#!/usr/bin/env python3
"""Autopiloto da BEE: produz capítulos aos poucos, compila e regista o progresso.

Feito para ser chamado por um agendador (GitHub Actions, cron, Agendador de
Tarefas do Windows) e para poder ser interrompido a qualquer momento: cada lote
é guardado atomicamente e o ciclo seguinte continua de onde parou.

Exemplos:
    python autopiloto.py --uma-vez            # um ciclo (bom para testar e para cron)
    python autopiloto.py                      # ciclos sem fim, com pausa entre eles
    python autopiloto.py --horas 6            # ciclos durante 6 horas
    python autopiloto.py --uma-vez --sem-compilar --lote 4
    python autopiloto.py --doctor             # o que está configurado, sem gerar nada
"""
from __future__ import annotations

import argparse
import contextlib
import math
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
import signal
import sys
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from bee.agenda import (
    Agendador, ConfigAgenda, Diario, Estado, ResultadoCiclo, carregar_estado,
    livros_na_fila, proximo_trabalho, salvar_estado,
)
from bee.arquivos import DadosInvalidos, ler_todos
from bee.catalogo import LIVROS, POR_NUMERO
from bee.compilador import ErroCompilacao
from bee.fontes import ErroFonte, FontesOriginais
from bee.ia import PROVEDORES, VERSOS_POR_PEDIDO_PADRAO, MotorIA, resolver_modelos
from bee.rede import ClienteHTTP, ErroRede, ler_chaves
from bee.trava import EmExecucao, trava


ROTULO = 'BEE · autopiloto'


def _positivo(valor: str) -> int:
    valor = valor.strip()
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Informe um número inteiro positivo.') from exc
    if numero < 1:
        raise argparse.ArgumentTypeError('Informe um número inteiro positivo.')
    return numero


def _nao_negativo(valor: str) -> float:
    try:
        numero = float(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Informe um número válido.') from exc
    if not math.isfinite(numero) or numero < 0:
        raise argparse.ArgumentTypeError('Informe um número finito não negativo.')
    return numero


def _hora(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Informe uma hora inteira (0 a 24).') from exc
    if not 0 <= numero <= 24:
        raise argparse.ArgumentTypeError('A hora deve estar entre 0 e 24.')
    return numero


def _lista_livros(valor: str) -> list[int]:
    numeros = []
    for parte in valor.replace(' ', ',').split(','):
        if not parte:
            continue
        if not parte.isdigit():
            raise argparse.ArgumentTypeError(f'Número de livro inválido: {parte!r}.')
        numero = int(parte)
        if numero not in POR_NUMERO:
            raise argparse.ArgumentTypeError(f'book_number {numero} não pertence aos 66 livros.')
        numeros.append(numero)
    if not numeros:
        raise argparse.ArgumentTypeError('Indique pelo menos um livro.')
    return numeros


def argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Produção automática da BEE: gera, compila e registra o progresso.',
        epilog='Exemplos: python autopiloto.py --uma-vez | python autopiloto.py --horas 6 | python autopiloto.py --doctor',
    )
    ritmo = parser.add_argument_group('ritmo')
    ritmo.add_argument('--intervalo-min', type=_nao_negativo, default=5.0, metavar='MIN',
                       help='pausa entre ciclos (padrão: 5)')
    ritmo.add_argument('--horas', type=_nao_negativo, default=None, metavar='H',
                       help='para ao fim de H horas (padrão: sem limite, útil para encerrar um job)')
    ritmo.add_argument('--uma-vez', action='store_true', help='faz um único ciclo e termina')
    ritmo.add_argument('--max-verso-por-ciclo', '--max-versos', dest='max_versos', type=_positivo,
                       default=6, metavar='N', help='versículos gerados por ciclo (padrão: 6)')
    ritmo.add_argument('--lote', type=_positivo, metavar='N',
                       help='versículos por pedido à IA (padrão depende do provedor)')

    orcamento = parser.add_argument_group('quota diária')
    orcamento.add_argument('--pedidos-por-dia', type=_positivo, default=400, metavar='N',
                           help='teto de pedidos à IA por dia local (padrão: 400)')
    orcamento.add_argument('--versos-por-dia', type=_nao_negativo, default=0, metavar='N',
                           help='teto de versículos por dia (0: sem teto próprio)')
    orcamento.add_argument('--hora-inicio', type=_hora, default=0, metavar='H',
                           help='hora local de início (padrão: 0)')
    orcamento.add_argument('--hora-fim', type=_hora, default=24, metavar='H',
                           help='hora local de fim, exclusiva (padrão: 24)')
    orcamento.add_argument('--fuso', default='UTC', metavar='ZONA',
                           help='fuso da janela diária, por exemplo Africa/Luanda (padrão: UTC)')

    fonte = parser.add_argument_group('IA (só planos gratuitos)')
    fonte.add_argument('--provedor', default='auto', metavar='NOME',
                       help='gemini, groq, cerebras, openrouter ou auto (padrão: auto pelas chaves existentes)')
    fonte.add_argument('--modelo', help='modelo do provedor; omita para usar o modelo gratuito padrão')
    fonte.add_argument('--chaves', metavar='LISTA',
                       help='chaves separadas por vírgula (alternativa às variáveis de ambiente)')
    fonte.add_argument('--versos-por-pedido', metavar='PROVEDOR=N',
                       help='lote por provedor, por exemplo groq=4,gemini=8')
    fonte.add_argument('--max-tokens', type=_positivo, default=4096, metavar='N',
                       help='limite de tokens de saída por pedido (padrão: 4096)')
    fonte.add_argument('--pausa', type=_nao_negativo, default=1.0, metavar='SEGUNDOS',
                       help='intervalo mínimo entre pedidos HTTP (padrão: 1)')
    fonte.add_argument('--tentativas', type=_positivo, default=3, metavar='N',
                       help='novas tentativas de rede por pedido (padrão: 3)')
    fonte.add_argument('--timeout', type=_nao_negativo, default=180.0, metavar='SEGUNDOS',
                       help='tempo-limite por pedido HTTP (padrão: 180)')
    fonte.add_argument('--sem-estilo', action='store_true',
                       help='não enviar glossário nem contexto do versículo anterior')
    fonte.add_argument('--sem-revisao-prompt', action='store_true',
                       help='não acrescentar as regras de rigor do modo automático')

    fila = parser.add_argument_group('o que produzir')
    fila.add_argument('--livros', type=_lista_livros, metavar='N,...',
                      help='só estes book_number, por exemplo 640,500')
    fila.add_argument('--ordem', choices=('plano', 'canonica', 'curtos'), default='plano',
                      help='ordem de produção (padrão: plano das oito fases)')

    saida = parser.add_argument_group('ficheiros')
    saida.add_argument('--dados', type=Path, default=Path('livros_json'), metavar='PASTA',
                       help='pasta dos JSON (padrão: livros_json)')
    saida.add_argument('--saida', type=Path, default=Path('.'), metavar='PASTA',
                       help='pasta dos módulos SQLite3 (padrão: pasta atual)')
    saida.add_argument('--cache-fontes', type=Path, default=Path('.bee-cache'), metavar='PASTA',
                       help='cache das fontes originais (padrão: .bee-cache)')
    saida.add_argument('--sem-compilar', action='store_true', help='não recompilar os módulos')
    saida.add_argument('--env', type=Path, default=Path('.env'), metavar='FICHEIRO',
                       help='ficheiro de chaves KEY=VALOR, ignorado pelo Git (padrão: .env)')
    saida.add_argument('--zip', type=Path, metavar='FICHEIRO',
                       help='depois de compilar, criar um ZIP com os dois módulos')
    saida.add_argument('--zip-sempre', action='store_true',
                       help='criar o ZIP em todos os ciclos, mesmo sem versículos novos')

    outros = parser.add_argument_group('diagnóstico')
    outros.add_argument('--doctor', action='store_true', help='mostra a configuração e sai, sem gerar')
    outros.add_argument('--testar', action='store_true',
                        help='testa a chave com um pedido mínimo (gasta 1 pedido) e sai')
    outros.add_argument('--status', action='store_true', help='mostra o progresso e sai')
    outros.add_argument('--verbose', action='store_true', help='mostra os pedidos HTTP em detalhe')
    args = parser.parse_args(argv)

    if args.hora_inicio == 24:
        parser.error('--hora-inicio deve estar entre 0 e 23.')
    if args.versos_por_pedido:
        try:
            args.lotes = {
                nome: _positivo(valor)
                for nome, valor in (par.split('=', 1) for par in args.versos_por_pedido.split(','))
            }
            for nome in args.lotes:
                if nome not in PROVEDORES:
                    parser.error(f'--versos-por-pedido: provedor desconhecido {nome!r}.')
        except ValueError as exc:
            raise SystemExit('--versos-por-pedido deve ter a forma provedor=N,provedor=N.') from exc
    else:
        args.lotes = {}
    if args.zip and args.sem_compilar:
        parser.error('--zip precisa de compilação; remova --sem-compilar.')
    return args


def carregar_env(caminho: Path = Path('.env')) -> list[str]:
    """Lê chaves de um ficheiro .env local (ignorado pelo Git).

    Variáveis já definidas no ambiente têm precedência. Devolve só os nomes
    carregados, nunca os valores.
    """
    if not caminho.exists():
        return []
    carregados: list[str] = []
    for linha in caminho.read_text(encoding='utf-8').splitlines():
        linha = linha.strip()
        if not linha or linha.startswith('#') or '=' not in linha:
            continue
        nome, valor = linha.split('=', 1)
        nome, valor = nome.strip(), valor.strip().strip('"\'')
        if not nome or not valor or nome in os.environ:
            continue
        os.environ[nome] = valor
        carregados.append(nome)
    return carregados


def _fuso(nome: str):
    try:
        return ZoneInfo(nome)
    except (ZoneInfoNotFoundError, ValueError):
        print(f'Aviso: fuso {nome!r} desconhecido neste sistema; a usar UTC.', file=sys.stderr)
        return timezone.utc


def _motores(args: argparse.Namespace, rede: ClienteHTTP) -> list[MotorIA]:
    """Monta os motores a partir das chaves disponíveis, sem imprimir segredos.

    O modelo é **descoberto** no próprio serviço: nomes fixos no código
    envelhecem (a Groq retirou os Llama 3.x e passou a devolver 404).
    """
    configurados: list[tuple[str, str]] = []
    if args.chaves:
        if args.provedor in ('auto', None):
            raise SystemExit('Com --chaves indique também --provedor.')
        configurados.append((args.provedor, args.chaves))
    else:
        for nome, config in PROVEDORES.items():
            valor = os.environ.get(config.variavel)
            if valor and ler_chaves(valor):
                configurados.append((nome, valor))
    if args.provedor not in ('auto', None):
        configurados = [(n, c) for n, c in configurados if n == args.provedor]
        if not configurados:
            config = PROVEDORES[args.provedor]
            raise SystemExit(
                f'Nenhuma chave para {config.rotulo}. Defina {config.variavel} ou use --chaves.'
            )
    if not configurados:
        disponiveis = ', '.join(f'{p.variavel} ({p.rotulo})' for p in PROVEDORES.values() if p.pedidos_por_dia)
        raise SystemExit(
            'Nenhum provedor configurado. Defina uma destas variáveis de ambiente: ' + disponiveis + '.'
        )
    # Provedores gratuitos primeiro; os pagos só entram se o utilizador os configurar.
    ordem = {nome: i for i, nome in enumerate(['gemini', 'groq', 'cerebras', 'openrouter', 'openai'])}
    configurados.sort(key=lambda par: ordem.get(par[0], 99))
    if args.modelo and len(configurados) > 1:
        print('  Aviso: --modelo só se aplica quando há um provedor; aqui o modelo é descoberto '
              'em cada serviço.', flush=True)
    motores = []
    for nome, valor in configurados:
        chaves = ler_chaves(valor)
        modelos = resolver_modelos(
            nome, chaves, rede,
            pedido=args.modelo if (args.modelo and len(configurados) == 1) else None,
            log=lambda texto: print(f'  {texto}', flush=True),
        )
        motores.append(MotorIA(
            nome, modelos, chaves, rede, args.max_tokens,
            aplicar_revisao=not args.sem_revisao_prompt,
        ))
    return motores


def _config(args: argparse.Namespace) -> ConfigAgenda:
    return ConfigAgenda(
        intervalo_min=args.intervalo_min,
        max_versos=args.max_versos,
        pedidos_por_dia=args.pedidos_por_dia,
        versos_por_dia=int(args.versos_por_dia),
        hora_inicio=args.hora_inicio,
        hora_fim=args.hora_fim,
        fuso=args.fuso,
        lote_global=args.lote,
        versos_por_pedido=args.lotes,
        tentativas_conteudo=3,
        estilo=not args.sem_estilo,
        compilar=not args.sem_compilar,
        pausa_rede=args.pausa,
        tentativas_rede=args.tentativas,
        timeout=args.timeout or 1.0,
        max_tokens=args.max_tokens,
        revisao=not args.sem_revisao_prompt,
    )


def _descrever_motores(motores: list[MotorIA], args: argparse.Namespace) -> None:
    for motor in motores:
        config = PROVEDORES.get(motor.provedor)
        rotulo = config.rotulo if config else motor.provedor
        teto = (
            f'{config.pedidos_por_dia} pedidos/dia (referência do plano gratuito)'
            if config and config.pedidos_por_dia else 'sem plano gratuito'
        )
        lote = args.lotes.get(motor.provedor) or args.lote or VERSOS_POR_PEDIDO_PADRAO.get(motor.provedor, 8)
        print(f'  - {rotulo} · {motor.modelo}: {teto}; {lote} versículos/pedido')
        chaves = getattr(motor, '_chaves', None)
        if chaves:
            print(f'    chaves configuradas: {len(chaves)}')


def _doctor(args: argparse.Namespace, estado: Estado, dados: Path) -> int:
    print(f'{ROTULO} — diagnóstico\n')
    print('Ficheiros:')
    print(f'  dados: {dados.resolve()}')
    print(f'  módulos: {args.saida.resolve()}')
    print(f'  cache de fontes: {args.cache_fontes.resolve()}')
    print(f'  estado: {(dados / ".bee" / "estado.json").resolve()}')
    print('\nProvedores configurados (só planos gratuitos):')
    try:
        rede = ClienteHTTP(pausa=args.pausa, tentativas=args.tentativas, timeout=args.timeout or 1.0)
        motores = _motores(args, rede)
    except SystemExit as exc:
        print(f'  Nenhum. {exc}')
        return 1
    _descrever_motores(motores, args)
    if len(motores) > 1:
        print(f'  Reserva ativa: se {motores[0].provedor} falhar (5xx) ou esgotar a quota, '
              f'{motores[1].provedor} assume automaticamente.')
        reservas = [m for m in motores if PROVEDORES[m.provedor].pedidos_por_dia]
        if len(reservas) > 1:
            print(f'  Capacidade de referência: '
                  f'{sum(PROVEDORES[m.provedor].pedidos_por_dia or 0 for m in reservas)} pedidos/dia '
                  f'entre {len(reservas)} provedores gratuitos.')
    livros = livros_na_fila(args.livros, args.ordem)
    trabalho = proximo_trabalho(livros, dados)
    print('\nFila:')
    print(f'  {len(livros)} livro(s), {sum(l.capitulos for l in livros)} capítulo(s)')
    if trabalho:
        print(f'  próximo: {trabalho[0].nome} {trabalho[1]}')
    else:
        print('  nada pendente nesta fila')
    print('\nEstado do agendador:')
    print(f'  ciclos: {estado.ciclos}; versículos acumulados: {estado.versos_total}')
    print(f'  falhas seguidas: {estado.falhas_seguidas}')
    if estado.ultimo_erro:
        print(f'  último erro: {estado.ultimo_erro}')
    if estado.exaustos:
        print(f'  provedores esgotados hoje: {", ".join(estado.exaustos)}')
    return 0


def _status(args: argparse.Namespace, dados: Path) -> int:
    dados_livros = ler_todos(dados)
    feitos = sum(len(item['chapters']) for item in dados_livros.values())
    versos = sum(len(v) for item in dados_livros.values() for v in item['chapters'].values())
    print(f'{ROTULO} — progresso')
    print(f'Capítulos estruturalmente completos: {feitos}/1189')
    print(f'Versículos nos capítulos completos: {versos}/31102')
    if feitos:
        print(f'Falta: {1189 - feitos} capítulos e {31102 - versos} versículos.')
    for livro in LIVROS:
        item = dados_livros.get(livro.numero, {})
        completos = len(item.get('chapters', {}))
        if completos:
            print(f'  {livro.numero:03d}  {livro.nome:<22} {completos:3d}/{livro.capitulos}')
    estado = carregar_estado(dados / '.bee' / 'estado.json')
    if estado.ciclos:
        print(f'Autopiloto: {estado.ciclos} ciclos; {estado.versos_total} versículos gerados; '
              f'último ciclo {estado.ultimo_ciclo_utc or "—"}')
    return 0


def _zip(args: argparse.Namespace) -> None:
    if not args.zip:
        return
    from zipfile import ZIP_DEFLATED, ZipFile
    args.zip.parent.mkdir(parents=True, exist_ok=True)
    temporario = args.zip.with_name(f'.{args.zip.name}.bee-tmp')
    modulos = [args.saida / nome for nome in ('BEE.SQLite3', 'BEE.commentaries.SQLite3')]
    if not all(caminho.exists() for caminho in modulos):
        print('Pacote não criado: ainda não existem os dois módulos compilados.', flush=True)
        return
    try:
        with ZipFile(temporario, 'w', ZIP_DEFLATED) as pacote:
            for caminho in modulos:
                pacote.write(caminho, caminho.name)
        os.replace(temporario, args.zip)
    finally:
        temporario.unlink(missing_ok=True)
    print(f'Pacote atualizado: {args.zip}', flush=True)


def main(argv: list[str] | None = None) -> int:
    args = argumentos(argv)
    carregadas = carregar_env(args.env)
    if carregadas:
        print(f'Chaves carregadas de .env: {", ".join(carregadas)} (valores não impressos).')
    dados: Path = args.dados
    estado_caminho = dados / '.bee' / 'estado.json'
    if args.status:
        return _status(args, dados)
    estado = carregar_estado(estado_caminho)
    if args.doctor:
        return _doctor(args, estado, dados)

    if args.testar:
        rede = ClienteHTTP(pausa=args.pausa, tentativas=args.tentativas, timeout=args.timeout or 1.0)
        motores = _motores(args, rede)
        falhou = False
        for motor in motores:
            try:
                resposta = motor.testar_ligacao()
            except (ErroRede, ValueError) as exc:
                print(f'FALHOU · {motor.provedor}/{motor.modelo}: {exc}')
                falhou = True
            else:
                print(f'OK · {motor.provedor}/{motor.modelo}: respondeu {resposta.strip()[:60]!r}')
        return 1 if falhou else 0

    fuso = _fuso(args.fuso)
    config = _config(args)
    try:
        with trava(dados):
            diario = Diario(dados / '.bee' / 'diario.md')
            if estado.ciclos == 0:
                diario.escrever(
                    f'{ROTULO} iniciado. Intervalo {config.intervalo_min:g} min; '
                    f'{config.max_versos} versículos por ciclo; janela {config.hora_inicio:02d}–{config.hora_fim:02d}h ({config.fuso}).'
                )
            rede = ClienteHTTP(pausa=config.pausa_rede, tentativas=config.tentativas_rede, timeout=config.timeout)
            motores = _motores(args, rede)
            print(f'{ROTULO}: {len(motores)} provedor(es) configurado(s).', flush=True)
            _descrever_motores(motores, args)
            livros = livros_na_fila(args.livros, args.ordem)
            fontes = FontesOriginais(args.cache_fontes, rede)
            agendador = Agendador(
                dados, args.saida, args.cache_fontes, estado, config, diario, fuso,
                motores, fontes, rede,
            )
            codigo = _loop(args, agendador, estado, estado_caminho, livros)
            _zip(args)
        return codigo
    except KeyboardInterrupt:
        print('\nInterrompido. Tudo o que já foi gerado está guardado; corra novamente para continuar.', file=sys.stderr)
        return 130
    except (DadosInvalidos, ErroCompilacao, ErroFonte, ErroRede, EmExecucao, ValueError, OSError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1


def _esperar(segundos: float) -> None:
    if segundos <= 0:
        return
    # Dormir em passos curtos mantém Ctrl+C responsivo em todos os sistemas.
    fim = time.monotonic() + segundos
    while True:
        restante = fim - time.monotonic()
        if restante <= 0:
            return
        time.sleep(min(restante, 30.0))
        if _PARAR.is_set():
            return


class _Parar:
    def __init__(self) -> None:
        self._pedido = False

    def set(self) -> None:
        self._pedido = True

    def is_set(self) -> bool:
        return self._pedido


_PARAR = _Parar()


def _instalar_sinais() -> None:
    def tratar(signum, frame):  # noqa: ARG001
        _PARAR.set()

    for nome in ('SIGTERM', 'SIGINT'):
        sinal = getattr(signal, nome, None)
        if sinal is not None:
            with contextlib.suppress(ValueError, OSError):
                signal.signal(sinal, tratar)


def _loop(args: argparse.Namespace, agendador: Agendador, estado: Estado,
          estado_caminho: Path, livros: list) -> int:
    """Corre ciclos até parar. Devolve o código de saída (1 se houve falha)."""
    _instalar_sinais()
    limite = None if args.horas is None else datetime.now(timezone.utc) + timedelta(hours=args.horas)
    while not _PARAR.is_set():
        resultado: ResultadoCiclo = agendador.ciclo(livros)
        salvar_estado(estado_caminho, estado)
        if resultado.acao == 'gerado':
            if resultado.resumo_compilacao and args.zip and args.zip_sempre:
                _zip(args)
            if args.uma_vez:
                return 0
            espera = agendador.config.intervalo_min * 60
        elif resultado.acao == 'nada':
            print(f'Ciclo sem progresso: {resultado.detalhe}', file=sys.stderr, flush=True)
            if args.uma_vez:
                # Uma execução única sem trabalho é uma falha para quem agendou
                # (GitHub Actions, cron): o erro fica visível em vez de silencioso.
                return 1
            espera = max(agendador.config.intervalo_min * 60, 300.0)
        elif resultado.acao == 'adormecer':
            espera = resultado.espera or 600.0
            print(f'Em pausa: {resultado.detalhe}. Retoma em {espera / 60:.0f} min.', flush=True)
        else:  # 'parar'
            print(f'Paragem: {resultado.detalhe}.', flush=True)
            return 0
        if limite is not None:
            restante = (limite - datetime.now(timezone.utc)).total_seconds()
            if restante <= 0:
                print('Limite de horas atingido.', flush=True)
                return 0
            espera = min(espera, restante)
        _esperar(espera)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
