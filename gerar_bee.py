#!/usr/bin/env python3
"""Gere rascunhos revisáveis da BEE e módulos SQLite3 para o MyBible."""
from __future__ import annotations

import argparse
import math
import os
from pathlib import Path
import sys

from bee.arquivos import DadosInvalidos, ler_todos
from bee.catalogo import LIVROS, POR_NUMERO
from bee.compilador import ErroCompilacao, compilar
from bee.fontes import ErroFonte, FontesOriginais
from bee.gerador import gerar_livros
from bee.ia import MODELOS_PADRAO, MotorIA, RespostaInvalida
from bee.rede import ClienteHTTP, ErroRede
from bee.trava import EmExecucao, trava


def _positivo(valor: str) -> int:
    try:
        numero = int(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Informe um número inteiro positivo.') from exc
    if numero < 1:
        raise argparse.ArgumentTypeError('Informe um número inteiro positivo.')
    return numero


def _real(valor: str, zero: bool = False) -> float:
    try:
        numero = float(valor)
    except ValueError as exc:
        raise argparse.ArgumentTypeError('Informe um número válido.') from exc
    if not math.isfinite(numero) or numero < 0 or (numero == 0 and not zero):
        raise argparse.ArgumentTypeError('Informe um número finito ' + ('não negativo.' if zero else 'positivo.'))
    return numero


def argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='BEE: rascunhos em JSON e módulos MyBible, com checkpoint e revisão humana.',
        epilog='Exemplos: python gerar_bee.py --livro 500 | python gerar_bee.py --todos | python gerar_bee.py --compilar',
    )
    acao = parser.add_mutually_exclusive_group(required=True)
    acao.add_argument('--livro', type=_positivo, metavar='NÚMERO', help='gera um livro pelo book_number MyBible, por exemplo 500 (João)')
    acao.add_argument('--todos', action='store_true', help='gera os 66 livros; pode consumir muitos tokens e demorar dias')
    acao.add_argument('--compilar', action='store_true', help='compila apenas os JSON completos, sem IA e sem API_KEY')
    acao.add_argument('--listar-livros', action='store_true', help='lista os 66 números e totais de capítulos')
    acao.add_argument('--status', action='store_true', help='mostra o progresso local, sem chamadas de rede')
    parser.add_argument('--provedor', choices=tuple(MODELOS_PADRAO), default='gemini',
                        help='gemini (padrão, plano gratuito), groq, cerebras, openrouter ou openai')
    parser.add_argument('--modelo', help='modelo compatível com JSON do provedor (padrão depende do provedor)')
    parser.add_argument('--pausa', type=lambda v: _real(v, True), default=1.0, metavar='SEGUNDOS', help='pausa mínima após cada chamada (padrão: 1)')
    parser.add_argument('--tentativas', type=_positivo, default=4, help='tentativas em falha transitória ou resposta inválida (padrão: 4)')
    parser.add_argument('--timeout', type=_real, default=120.0, metavar='SEGUNDOS', help='tempo-limite de cada chamada (padrão: 120)')
    parser.add_argument('--versos-por-pedido', type=_positivo, default=8, metavar='N', help='lote máximo por requisição (padrão: 8; reduz automaticamente se necessário)')
    parser.add_argument('--max-tokens', type=_positivo, default=8192, metavar='N', help='limite de tokens de saída por chamada (padrão: 8192, mínimo: 256)')
    parser.add_argument('--max-capitulos', type=_positivo, metavar='N', help='limita os novos capítulos nesta execução; útil para controlar custos')
    parser.add_argument('--sem-compilar', action='store_true', help='não compila automaticamente após a geração')
    parser.add_argument('--dados', type=Path, default=Path('edicoes/nova/livros_json'), metavar='PASTA', help='pasta de JSON e checkpoints (padrão: edição nova, edicoes/nova/livros_json; a legada livros_json só com --dados explícito)')
    parser.add_argument('--saida', type=Path, default=Path('.'), metavar='PASTA', help='pasta dos módulos SQLite3 (padrão: atual)')
    parser.add_argument('--cache-fontes', type=Path, default=Path('.bee-cache'), metavar='PASTA', help='cache local das fontes originais')
    args = parser.parse_args(argv)
    if args.livro is not None and args.livro not in POR_NUMERO:
        parser.error(f'book_number {args.livro} não pertence aos 66 livros; use --listar-livros.')
    if args.max_tokens < 256:
        parser.error('--max-tokens deve ser pelo menos 256.')
    if args.versos_por_pedido > 176:
        parser.error('--versos-por-pedido deve ser no máximo 176.')
    if args.sem_compilar and (args.compilar or args.status or args.listar_livros):
        parser.error('--sem-compilar só pode ser usado com --livro ou --todos.')
    if args.max_capitulos is not None and not (args.todos or args.livro is not None):
        parser.error('--max-capitulos só pode ser usado com --livro ou --todos.')
    return args


def _listar() -> None:
    for livro in LIVROS:
        print(f'{livro.numero:03d}  {livro.nome:<22} {livro.capitulos:3d} capítulos  {livro.nome_arquivo}')
    print(f'Total: {len(LIVROS)} livros, {sum(l.capitulos for l in LIVROS)} capítulos.')


def _status(diretorio: Path) -> None:
    dados = ler_todos(diretorio)
    for livro in LIVROS:
        item = dados.get(livro.numero, {})
        completos = len(item.get('chapters', {}))
        parciais = len(item.get('in_progress', {}))
        sufixo = f' (+{parciais} em andamento)' if parciais else ''
        print(f'{livro.numero:03d}  {livro.nome:<22} {completos:3d}/{livro.capitulos:<3}{sufixo}')
    completo = sum(len(item['chapters']) for item in dados.values())
    print(f'Total: {completo}/1189 capítulos estruturalmente completos; a revisão editorial não é verificada.')


def _compilar(dados: Path, saida: Path) -> None:
    resumo = compilar(dados, saida)
    estado = 'completo' if resumo['completo'] else 'PARCIAL'
    print(
        f"Módulos {estado}: {resumo['livros']}/66 livros, {resumo['capitulos']}/1189 capítulos, "
        f"{resumo['versiculos']} versículos."
    )
    if resumo['parciais']:
        print(f"{resumo['parciais']} capítulo(s) em andamento não foram compilados.")
    if resumo['lacunas_fonte']:
        print(f"ATENÇÃO: {resumo['lacunas_fonte']} versículo(s) contêm marcadores de fonte ausente; verifique-os.")
    print(f"Ficheiros: {saida / 'BEE.SQLite3'} e {saida / 'BEE.commentaries.SQLite3'}")
    print('Os textos e comentários são rascunhos de IA: revise-os antes de publicar.')


def main(argv: list[str] | None = None) -> int:
    args = argumentos(argv)
    if args.listar_livros:
        _listar()
        return 0
    try:
        if args.status:
            _status(args.dados)
            return 0
        with trava(args.dados):
            if args.compilar:
                _compilar(args.dados, args.saida)
                return 0
            selecionados = list(LIVROS) if args.todos else [POR_NUMERO[args.livro]]
            if args.todos:
                print('AVISO: gerar 1.189 capítulos pode custar muitos tokens e levar bastante tempo.', flush=True)
            rede = ClienteHTTP(pausa=args.pausa, tentativas=args.tentativas, timeout=args.timeout)
            fontes = FontesOriginais(args.cache_fontes, rede)

            def obter_motor() -> MotorIA:
                from bee.ia import PROVEDORES
                nome = PROVEDORES[args.provedor].variavel
                chave = os.environ.get(nome, '') or os.environ.get('API_KEY', '')
                if not chave.strip():
                    raise ValueError(f'Defina a variável {nome} (ou API_KEY) para gerar novos capítulos; '
                                     'veja autopiloto.py para a produção automática.')
                from bee.ia import resolver_modelos
                from bee.perfil import resolver_perfil
                modelos = resolver_modelos(
                    args.provedor, [chave], rede, pedido=args.modelo,
                    log=lambda texto: print(f'  {texto}', flush=True),
                )
                # Voz da edição ativa (BEE_EDICAO); padrão legado = sem mudança.
                return MotorIA(args.provedor, modelos, chave, rede, args.max_tokens,
                               perfil=resolver_perfil())

            gerar_livros(
                selecionados, args.dados, fontes, obter_motor,
                args.versos_por_pedido, args.tentativas, args.max_capitulos,
            )
            if not args.sem_compilar:
                _compilar(args.dados, args.saida)
        return 0
    except KeyboardInterrupt:
        print('\nInterrompido. Os lotes já guardados podem ser retomados com o mesmo comando.', file=sys.stderr)
        return 130
    except (DadosInvalidos, ErroCompilacao, ErroFonte, ErroRede, RespostaInvalida, EmExecucao, ValueError, OSError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
