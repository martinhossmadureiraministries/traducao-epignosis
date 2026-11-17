#!/usr/bin/env python3
"""Ciclo de produção numa GitHub Action: gera, compila, publica e arquiva.

Diferente de `autopiloto.py`, este script não dorme. Cada execução faz um
pequeno bloco de trabalho e termina; o agendador do GitHub (cron) volta a
chamá-lo. É assim que a produção continua mesmo com o computador desligado.

O que guarda:
  - os JSON dos capítulos no ramo de dados, sem misturar com o código;
  - os módulos SQLite3 como artefato descarregável (retenção configurável);
  - um resumo no resumo da execução do GitHub.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import autopiloto
from bee.agenda import (
    Agendador, Diario, carregar_estado, escrever_atomico, livros_na_fila,
    proximo_trabalho, salvar_estado,
)
from bee.arquivos import DadosInvalidos, ler_todos
from bee.catalogo import POR_NUMERO
from bee.compilador import ErroCompilacao, compilar
from bee.fontes import ErroFonte, FontesOriginais
from bee.rede import ClienteHTTP, ErroRede
from bee.trava import EmExecucao, trava


ROTULO = 'BEE · nuvem'


def _env(nome: str, padrao: str = '') -> str:
    return os.environ.get(nome, padrao).strip()


def _env_int(nome: str, padrao: int) -> int:
    try:
        return int(_env(nome) or padrao)
    except ValueError:
        return padrao


def _resumo(markdown: str) -> None:
    """Escreve o resumo da execução, visível no GitHub."""
    destino = os.environ.get('GITHUB_STEP_SUMMARY')
    if destino:
        with open(destino, 'a', encoding='utf-8') as arquivo:
            arquivo.write(markdown + '\n')
    print(markdown)


def _agora_local(fuso: str) -> datetime:
    try:
        return datetime.now(ZoneInfo(fuso))
    except (ZoneInfoNotFoundError, ValueError):
        return datetime.now(timezone.utc)


def _progresso(dados: Path) -> tuple[int, int]:
    """Capítulos completos e versículos guardados (incluindo os de capítulos em curso).

    Contar só os `chapters` fazia o resumo dizer "0 versículos guardados" logo
    depois de guardar 6 — parecia que nada acontecia.
    """
    livros = ler_todos(dados)
    capitulos = sum(len(item['chapters']) for item in livros.values())
    versos = sum(
        len(valores)
        for item in livros.values()
        for lado in ('chapters', 'in_progress')
        for valores in item.get(lado, {}).values()
    )
    return capitulos, versos


def _repo() -> Path:
    """Repositório onde os ramos de dados são lidos/publicados.

    Em produção é a raiz do checkout (cwd). Nos testes é possível apontar para
    outro repositório com BEE_REPO, sem mexer no diretório de trabalho.
    """
    return Path(_env('BEE_REPO', '') or '.').resolve()


def _git(*comandos: str, verificar: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ('git', '-C', str(_repo())) + comandos, check=verificar, text=True, env=env,
        capture_output=True,
    )


def _commit_dados(ramo: str, mensagem: str, pastas: list[str]) -> str:
    """Publica os JSON num ramo próprio, sem tocar no ramo do código.

    Usa o índice em memória (`commit-tree`), por isso a história do ramo de
    dados contém apenas os dados, sem os commits do código.
    """
    _git('config', 'user.name', 'BEE autopiloto')
    _git('config', 'user.email', 'autopiloto@users.noreply.github.com')
    anterior = _git('rev-parse', '--verify', f'refs/remotes/origin/{ramo}', verificar=False)
    pai = anterior.stdout.strip() if anterior.returncode == 0 else ''
    indice = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'bee-indice'
    indice.unlink(missing_ok=True)
    env = {**os.environ, 'GIT_INDEX_FILE': str(indice)}
    if pai:
        _git('read-tree', pai.splitlines()[0], env=env)
    else:
        _git('read-tree', '--empty', env=env)
    # O estado do autopiloto (.bee) é ignorado pelo .gitignore do código, mas
    # precisa de viajar com os dados: por isso é adicionado à força.
    for pasta in pastas:
        _git('add', '-A', '-f', pasta, env=env)
    # A trava é um descritor do sistema operativo, não um dado do projeto.
    _git('update-index', '--force-remove', 'livros_json/.bee.lock', env=env, verificar=False)
    arvore = _git('write-tree', env=env).stdout.strip()
    if pai:
        arvore_anterior = _git('rev-parse', f'{pai.splitlines()[0]}^{{tree}}').stdout.strip()
        if arvore == arvore_anterior:
            return 'sem alterações nos JSON'
        perdidos = _regressao(pai.splitlines()[0], arvore, pastas)
        if perdidos:
            raise ValueError(
                f'a publicação foi cancelada para não perder {perdidos} versículo(s) que já '
                'estavam publicados; os dados locais não substituíram os do ramo'
            )
    comando = ['commit-tree', arvore, '-m', mensagem]
    if pai:
        comando[2:2] = ['-p', pai.splitlines()[0]]
    novo = _git(*comando, env=env).stdout.strip()
    _git('push', 'origin', f'{novo}:refs/heads/{ramo}')
    return 'JSON publicados' if pai else 'ramo de dados criado'


def _versiculos_de_arvore(arvore: str, pastas: list[str]) -> dict[str, int]:
    """Quantos versículos cada ficheiro de dados tem numa árvore do git."""
    contagem: dict[str, int] = {}
    listagem = _git('ls-tree', '-r', '--name-only', arvore, *pastas, verificar=False)
    for nome in listagem.stdout.splitlines():
        if not nome.endswith('.json'):
            continue
        try:
            texto = _git('show', f'{arvore}:{nome}').stdout
            dados = json.loads(texto)
        except (ValueError, subprocess.CalledProcessError):
            continue
        if not isinstance(dados, dict):
            continue
        contagem[nome] = sum(
            len(v) for lado in ('chapters', 'in_progress') for v in dados.get(lado, {}).values()
        )
    return contagem


def _regressao(pai: str, arvore: str, pastas: list[str]) -> int:
    """Versículos que existiam no ramo e desapareceriam com esta publicação.

    Aconteceu depois de o utilizador ter copiado o workflow para `.github/`:
    esse commit em `main` não trouxe o ramo de dados, a recuperação falhou em
    silêncio e a execução publicou uma árvore sem João 5:7-46 — trabalho pago em
    quota, perdido, com o resumo a dizer "versículos guardados".
    """
    antes = _versiculos_de_arvore(pai, pastas)
    depois = _versiculos_de_arvore(arvore, pastas)
    return sum(max(0, quantidade - depois.get(nome, 0)) for nome, quantidade in antes.items())


def _json_local(caminho: Path) -> dict | None:
    try:
        return json.loads(caminho.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return None


def _unir_progresso(local: Path, remoto: Path) -> int:
    """Mantém, para cada versículo, a versão que já existia localmente.

    A nuvem só deve acrescentar texto novo. Se você editou ou reviu versículos
    no seu computador, recuperar o ramo de dados não pode sobrescrever esse
    trabalho. Devolve quantos versículos ficaram com a versão local.
    """
    mantidos = 0
    if not remoto.is_dir():
        return mantidos
    for origem in sorted(remoto.glob('*.json')):
        destino = local / origem.name
        if not destino.exists():
            shutil.copy2(origem, destino)
            continue
        novos, antigos = _json_local(origem), _json_local(destino)
        if not isinstance(novos, dict) or not isinstance(antigos, dict):
            shutil.copy2(origem, destino)
            continue
        for secao in ('chapters', 'in_progress'):
            recebidos = novos.get(secao)
            if not isinstance(recebidos, dict):
                continue
            guardados = antigos.get(secao)
            if not isinstance(guardados, dict):
                guardados = antigos[secao] = {}
            for capitulo, versiculos in recebidos.items():
                existentes = guardados.get(capitulo) or []
                numeros = {v.get('verse') for v in existentes if isinstance(v, dict)}
                for versiculo in versiculos:
                    if versiculo.get('verse') in numeros:
                        mantidos += 1
                        continue
                    existentes.append(versiculo)
                    numeros.add(versiculo.get('verse'))
                guardados[capitulo] = existentes
        escrever_atomico(destino, json.dumps(antigos, ensure_ascii=False, indent=2) + '\n')
    return mantidos


_SINAIS_TRANSITORIOS = (
    'ServicoIndisponivel', 'HTTP 5', 'HTTP 408', 'HTTP 409', 'HTTP 425', 'HTTP 429',
    'falha de rede', 'timed out', 'timeout', 'CotaExcedida',
)


def _caminho_remoto(valor: str) -> Path | None:
    """Só aceita uma pasta de recuperação explícita e descartável.

    Uma variável vazia virava ``Path('.')`` e podia apagar o próprio projeto;
    por isso o caminho tem de ser indicado e não pode ser a raiz nem a pasta atual.
    """
    if not valor.strip():
        return None
    caminho = Path(valor).expanduser()
    try:
        absoluto = caminho.resolve()
    except OSError:
        return None
    if absoluto in (Path('/'), Path.home(), Path.cwd().resolve()):
        return None
    if '.git' in absoluto.parts:
        return None
    return absoluto


def _apagar_recuperado(caminho: Path) -> None:
    """Remove apenas diretórios temporários criados para a recuperação."""
    if caminho.name.startswith('bee-remoto') or 'bee-remoto' in caminho.parts:
        shutil.rmtree(caminho, ignore_errors=True)
    else:
        print(f'A pasta de recuperação {caminho} não foi apagada (não é temporária).', flush=True)


def _parece_transitorio(erro: str) -> bool:
    """Distingue indisponibilidade passageira do serviço de erro de configuração."""
    return any(sinal in erro for sinal in _SINAIS_TRANSITORIOS)


def _passo_do_plano(dados: Path, livros: list) -> tuple[int, int]:
    """Quantos versículos ainda faltam no livro atual e em toda a fila."""
    existentes = ler_todos(dados)
    atual = restante_fila = 0
    primeiro = True
    for livro in livros:
        completos = existentes.get(livro.numero, {}).get('chapters', {})
        pendentes = [c for c in range(1, livro.capitulos + 1) if str(c) not in completos]
        faltam = sum(
            livro.versos_por_capitulo[c - 1]
            - len(existentes.get(livro.numero, {}).get('in_progress', {}).get(str(c), []))
            for c in pendentes
        )
        restante_fila += faltam
        if pendentes and primeiro:
            atual = faltam
            primeiro = False
    return atual, restante_fila


def _modulos_desatualizados(dados: Path, saida: Path) -> bool:
    """Os módulos existem e são mais recentes do que todos os JSON de dados?"""
    env = saida / 'BEE.SQLite3'
    comentarios = saida / 'BEE.commentaries.SQLite3'
    try:
        mais_recente = max(c.stat().st_mtime for c in dados.glob('*.json'))
        modulos = min(env.stat().st_mtime, comentarios.stat().st_mtime)
    except (OSError, ValueError):
        return True
    return modulos < mais_recente


def _reparar_dados(dados: Path, ramo: str, diario, publicar: bool) -> tuple[str, int]:
    """Recupera do ramo de dados os versículos que faltam localmente.

    Foi o que aconteceu em 17/11: a execução arrancou sem o ramo de dados (o
    commit do workflow em `main` não o trouxe), o agendador achou João 5 em
    curso a partir do versículo 1 e 46 versículos já pagos em quota ficaram
    fora do ficheiro. Devolve (mensagem, versículos acrescentados).
    """
    anterior = _git('rev-parse', '--verify', f'refs/remotes/origin/{ramo}', verificar=False)
    if anterior.returncode != 0 or not anterior.stdout.strip():
        return 'sem ramo de dados publicado', 0
    revisao = anterior.stdout.strip()
    alvo = Path(os.environ.get('RUNNER_TEMP', '/tmp')) / 'bee-reparo'
    shutil.rmtree(alvo, ignore_errors=True)
    alvo.mkdir(parents=True)
    encontrados = 0
    listagem = _git('ls-tree', '-r', '--name-only', revisao, 'livros_json', verificar=False)
    for nome in listagem.stdout.splitlines():
        # Só ficheiros de livros: `livros_json/.bee/estado.json` e o diário
        # viajam no ramo mas não são livros.
        if not nome.endswith('.json') or '/.' in nome:
            continue
        destino = alvo / Path(nome).name
        try:
            destino.write_bytes(_git('show', f'{revisao}:{nome}').stdout.encode('utf-8'))
            encontrados += 1
        except subprocess.CalledProcessError:
            continue
    if not encontrados:
        shutil.rmtree(alvo, ignore_errors=True)
        return 'sem dados no ramo', 0
    antes = _progresso(dados)[1]
    mantidos = _unir_progresso(dados, alvo)
    shutil.rmtree(alvo, ignore_errors=True)
    acrescentados = max(0, _progresso(dados)[1] - antes)
    if not acrescentados:
        return 'nada a recuperar', 0
    diario.escrever(
        f'Recuperados {acrescentados} versículo(s) do ramo `{ramo}` que faltavam localmente.',
        'aviso',
    )
    if publicar and _env('BEE_PUBLICAR', '1') != '0':
        try:
            _commit_dados(
                ramo,
                f'BEE: reparação de {acrescentados} versículos recuperados do ramo',
                ['livros_json'],
            )
        except (ValueError, subprocess.CalledProcessError):
            pass
    return f'{acrescentados} versículo(s) recuperados do ramo `{ramo}`', acrescentados


def _compilar_no_fim(resultado, dados: Path, saida: Path, diario) -> None:
    """Compila quando há capítulos completos novos, mesmo em fim de ciclo parcial.

    O agendador só compila quando fecha um capítulo inteiro. Com lotes de 6
    versículos, um capítulo de 47 (João 5) levava 8 ciclos: o resumo repetia
    'ainda não há capítulos completos' e o MyBible não recebia nada durante
    horas. Aqui compila-se sempre que apareceu, desde a última compilação,
    pelo menos um capítulo completo novo.
    """
    if resultado.acao != 'gerado' or resultado.resumo_compilacao:
        return
    if _env('BEE_COMPILAR', '1') == '0':  # respeita BEE_COMPILAR=0
        return
    if not _modulos_desatualizados(dados, saida):
        return
    try:
        resumo = compilar(dados, saida)
    except Exception as exc:  # a compilação nunca deve estragar a produção
        diario.escrever(f'A compilação do fim do ciclo falhou; módulos anteriores preservados: {exc}', 'aviso')
        return
    resultado.resumo_compilacao = resumo
    diario.escrever(
        f'Módulos recompilados no fim do ciclo: {resumo["capitulos"]}/1189 capítulos, '
        f'{resumo["versiculos"]} versículos.'
    )


LEIA_ME = (
    'Rascunho automático da Bíblia de Estudo Epignósis (BEE).\n'
    'Copie os dois ficheiros .SQLite3 para a pasta do MyBible no Android e\n'
    'reinicie o aplicativo. Conteúdo gerado por IA e NÃO revisto: use para\n'
    'estudo e revisão, não como edição final.\n'
)


def _empacotar(saida: Path) -> str | None:
    """ZIP com os dois módulos e um LEIA-ME curto, pronto para copiar ao telefone."""
    from zipfile import ZIP_DEFLATED, ZipFile
    modulos = [saida / nome for nome in ('BEE.SQLite3', 'BEE.commentaries.SQLite3')]
    if not all(caminho.exists() for caminho in modulos):
        return None
    destino = saida / 'BEE-modulos.zip'
    temporario = destino.with_name(f'.{destino.name}.bee-tmp')
    try:
        with ZipFile(temporario, 'w', ZIP_DEFLATED) as pacote:
            for caminho in modulos:
                pacote.write(caminho, caminho.name)
            pacote.writestr('LEIA-ME.txt', LEIA_ME)
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)
    return str(destino)


def main() -> int:
    dados = Path(_env('BEE_DADOS', 'livros_json'))
    saida = Path(_env('BEE_SAIDA', 'entregas/auto'))
    cache = Path(_env('BEE_CACHE', '.bee-cache'))
    fuso_nome = _env('BEE_FUSO', 'UTC')

    lista = ['--doctor', '--fuso', fuso_nome,
        '--provedor', _env('BEE_PROVEDOR', 'auto'),
        '--max-verso-por-ciclo', _env('BEE_VERSOS_POR_CICLO', '40'),
        '--lote', _env('BEE_LOTE', '8'),
        '--pedidos-por-dia', _env('BEE_PEDIDOS_POR_DIA', '400'),
        '--versos-por-dia', _env('BEE_VERSOS_POR_DIA', '0'),
        '--hora-inicio', _env('BEE_HORA_INICIO', '0'),
        '--hora-fim', _env('BEE_HORA_FIM', '24')]
    if _env('BEE_LIVROS'):
        lista += ['--livros', _env('BEE_LIVROS')]
    if _env('BEE_MODELO'):
        lista += ['--modelo', _env('BEE_MODELO')]
    argumentos = autopiloto.argumentos(lista)
    try:
        fuso = ZoneInfo(fuso_nome)
    except (ZoneInfoNotFoundError, ValueError):
        fuso, fuso_nome = timezone.utc, 'UTC'
        print(f'Aviso: fuso {fuso_nome!r} desconhecido; a usar UTC.', file=sys.stderr)

    remoto = _caminho_remoto(_env('BEE_REMOTO', ''))
    recuperado = False
    if _env('BEE_UNIR', '1') != '0' and remoto is not None and remoto.is_dir():
        recuperado = any(remoto.glob('*.json'))
        mantidos = _unir_progresso(dados, remoto)
        if mantidos:
            print(f'Progresso recuperado sem sobrescrever {mantidos} versículo(s) já existentes localmente.')
    if remoto is not None and not recuperado:
        print(
            'AVISO: não foi possível recuperar o ramo de dados; esta execução começou '
            'do zero e só pode publicar versículos que produzir agora.',
            file=sys.stderr, flush=True,
        )
        _apagar_recuperado(remoto)

    estado_caminho = dados / '.bee' / 'estado.json'
    estado = carregar_estado(estado_caminho)
    diario = Diario(dados / '.bee' / 'diario.md')
    config = autopiloto._config(argumentos)
    config.fuso = fuso_nome
    config.intervalo_min = 0
    if _env('BEE_COMPILAR', '1') == '0':
        config.compilar = False
    # `BEE_JANELA=0` desliga a janela horária interna quando é o próprio
    # agendador (cron) que decide quando correr. Sem isto, uma execução manual
    # lançada de madrugada terminava verde sem produzir nada.
    if _env('BEE_JANELA', '1') == '0':
        config.hora_inicio, config.hora_fim = 0, 24

    livros = livros_na_fila(argumentos.livros, argumentos.ordem)
    ramo = _env('BEE_BRAMO_DADOS', 'bee-dados')
    reparacao, reparados = '', 0
    try:
        reparacao, reparados = _reparar_dados(
            dados, ramo, diario, publicar=_env('BEE_PUBLICAR', '1') != '0',
        )
    except Exception as exc:  # nunca impedir a produção por causa da reparação
        reparacao = f'não foi possível reparar ({type(exc).__name__})'
        print(f'Aviso: {reparacao}', file=sys.stderr, flush=True)
    antes_cap, antes_versos = _progresso(dados)

    try:
        with trava(dados):
            rede = ClienteHTTP(pausa=float(_env('BEE_PAUSA', '1') or 1),
                               tentativas=_env_int('BEE_TENTATIVAS', 3),
                               timeout=float(_env('BEE_TIMEOUT', '180') or 180))
            motores = autopiloto._motores(argumentos, rede)
            print(f'{ROTULO}: {", ".join(m.provedor for m in motores)}', flush=True)
            fontes = FontesOriginais(cache, rede)
            agendador = Agendador(
                dados, saida, cache, estado, config, diario, fuso, motores, fontes, rede,
            )
            resultado = agendador.ciclo(livros)
            salvar_estado(estado_caminho, estado)
            # O serviço de IA às vezes responde 5xx em rajada (foi o que
            # aconteceu na primeira execução real). Em vez de gastar uma
            # execução inteira do cron, tenta-se de novo aqui.
            extra = _env_int('BEE_TENTATIVAS_CICLO', 2) - 1
            while (
                resultado.acao == 'nada' and extra > 0
                and estado.falhas_seguidas < agendador.config.max_falhas_seguidas
                and _parece_transitorio(estado.ultimo_erro or '')
            ):
                print('Falha transitória do serviço; nova tentativa no mesmo trabalho...', flush=True)
                diario.escrever('Falha transitória do serviço; nova tentativa no mesmo trabalho.', 'aviso')
                time.sleep(float(_env('BEE_ESPERA_ENTRE_TENTATIVAS', '45') or 45))
                extra -= 1
                resultado = agendador.ciclo(livros)
                salvar_estado(estado_caminho, estado)
            # Depois de todas as tentativas: compilar uma única vez, com tudo o
            # que ficou guardado (dentro e depois das repetições).
            _compilar_no_fim(resultado, dados, saida, diario)
            # Uma falha passageira (5xx, rede) não deve contar como "código
            # avariado": se o serviço estiver em baixo 6 ciclos seguidos, o
            # agendador desistia e a produção só voltava quando alguém corresse
            # o programa à mão. Nestes casos encerra-se o contador.
            if (
                resultado.acao == 'nada' and not resultado.progresso
                and _parece_transitorio(estado.ultimo_erro or '')
            ):
                if estado.falhas_seguidas:
                    estado.falhas_seguidas = 0
                    salvar_estado(estado_caminho, estado)
                print('Serviço de IA indisponível neste momento; o próximo ciclo agendado volta a tentar.',
                      flush=True)
                diario.escrever(
                    'Serviço de IA indisponível (5xx) e reserva esgotada; o próximo ciclo volta a tentar.',
                    'aviso',
                )
    except EmExecucao as exc:
        _resumo(f'### {ROTULO}\n\nOutra execução está a usar os dados: {exc}. Nada foi feito.')
        return 0
    except (DadosInvalidos, ErroCompilacao, ErroFonte, ErroRede, ValueError, OSError) as exc:
        _resumo(f'### {ROTULO}\n\nFalha: `{type(exc).__name__}` — {exc}')
        return 1

    depois_cap, depois_versos = _progresso(dados)
    if recuperado or reparados:
        origem = (
            f'recuperados do ramo `{ramo}`'
            if recuperado else f'reparados a partir do ramo `{ramo}`'
        )
        linhas_recuperacao = (
            f'- Dados de partida: {origem} '
            f'({antes_cap} capítulos completos, {antes_versos} versículos).'
        )
    else:
        linhas_recuperacao = (
            f'- **Dados de partida: nenhum** — o ramo `{ramo}` não pôde ser recuperado nesta '
            'execução. Se já havia versículos publicados, esta é a razão pela qual não aparecem.'
        )
    publicado = 'não configurado'
    if _env('BEE_PUBLICAR', '1') != '0':
        try:
            produzidos = resultado.progresso.versos if resultado.progresso else 0
            publicado = _commit_dados(
                ramo,
                f'BEE: +{produzidos} versículos ({depois_cap}/1189 capítulos completos)',
                ['livros_json'],
            )
        except subprocess.CalledProcessError as exc:
            publicado = f'falha ao publicar ({exc})'
            print(f'Aviso: {publicado}', file=sys.stderr)
        except ValueError as exc:
            publicado = f'publicação recusada: {exc}'
            diario.escrever(publicado, 'erro')
            print(f'AVISO: {publicado}', file=sys.stderr)

    pacote = _empacotar(saida)
    env = (saida / 'BEE.SQLite3')
    trabalho = proximo_trabalho(livros, dados)
    faltam_livro, faltam_fila = _passo_do_plano(dados, livros)
    transitorio = _parece_transitorio(estado.ultimo_erro or '')
    # Números pequenos e absolutos, sem percentagens que sugiram progresso que
    # não existe: o que conta é quantos capítulos estão completos e quantos
    # versículos já estão guardados (mesmo em capítulos ainda em curso).
    linhas = [f'### {ROTULO}', '']
    if resultado.acao == 'adormecer':
        espera = resultado.espera or 0
        horas, minutos = int(espera // 3600), int((espera % 3600) // 60)
        linhas.append(
            f'- Ação: **a aguardar a janela diária** — agora são '
            f'{_agora_local(config.fuso):%H:%M} em {config.fuso}, fora de '
            f'{config.hora_inicio:02d}:00–{config.hora_fim:02d}:00. '
            f'A produção retoma às {config.hora_inicio:02d}:00, daqui a {horas}h{minutos:02d}.'
        )
        linhas.append(
            '- Isto é normal e não é uma falha: o horário está nas variáveis '
            '`BEE_HORA_INICIO` e `BEE_HORA_FIM` do workflow.'
        )
    elif resultado.acao == 'parar':
        linhas.append(f'- Ação: **parado até amanhã** — {resultado.detalhe or "orçamento diário atingido"}.')
        if 'orçamento' in (resultado.detalhe or ''):
            linhas.append('- O limite está em `BEE_PEDIDOS_POR_DIA`; a reposição é à meia-noite local.')
    elif resultado.acao == 'gerado':
        linhas.append(f'- Ação: **{resultado.acao}** — {resultado.detalhe or "—"}')
        versos = resultado.progresso.versos
        capitulos = resultado.progresso.capitulos
        linhas.append(
            f'- Esta execução: +{versos} {"versículo" if versos == 1 else "versículos"}, '
            f'+{capitulos} {"capítulo" if capitulos == 1 else "capítulos"}'
        )
    elif transitorio:
        linhas.append('- Ação: **nada gerado nesta execução** — o serviço de IA não respondeu.')
        linhas.append('- **Não é um erro do projeto nem da sua chave.** O próximo ciclo '
                      'agendado (15 min) volta a tentar sozinho; não precisa de fazer nada.')
    else:
        linhas.append(f'- Ação: **nada** — {resultado.detalhe or "—"}')
    linhas.append(linhas_recuperacao)
    if reparados:
        linhas.append(f'- **Trabalho recuperado:** {reparacao}.')
    linhas.append(f'- Progresso nesta execução: **{depois_cap}/1189 capítulos completos**, '
                  f'{depois_versos}/31102 versículos guardados')
    if (
        estado.lote_capitulo and estado.lote_versiculo
        and estado.lote_livro == (trabalho[0].numero if trabalho else None)
        and estado.lote_capitulo == (trabalho[1] if trabalho else None)
    ):
        livro = POR_NUMERO.get(estado.lote_livro or 0)
        if livro is not None:
            linhas.append(
                f'- A próxima execução continua em **{livro.nome} '
                f'{estado.lote_capitulo}:{estado.lote_versiculo}** '
                '(não recomeça o capítulo).'
            )
    seguinte = f'{trabalho[0].nome} {trabalho[1]}' if trabalho else 'nada pendente'
    linhas.append('- A seguir: ' + seguinte)
    if faltam_livro:
        linhas.append(
            f'- Faltam {faltam_livro} versículos para concluir '
            f'**{trabalho[0].nome}**; {faltam_fila} em toda a fila'
        )
    if resultado.acao == 'nada' and estado.ultimo_erro:
        linhas.append(f'- Último erro: `{estado.ultimo_erro}`')
        linhas.append(
            '- **Causa provável:** serviço de IA instável (5xx) ou limite de pedidos por minuto — '
            'não é a sua chave nem o projeto; o próximo ciclo tenta de novo.'
            if transitorio else
            '- **Causa provável:** os provedores gratuitos estão sem quota (a reposição é '
            'diária) ou recusaram a chave. O próximo ciclo tenta de novo; se durar mais de '
            'um dia, corra `python autopiloto.py --testar` (configuração da chave).'
        )
    if resultado.resumo_compilacao:
        resumo = resultado.resumo_compilacao
        em_curso = max(0, depois_versos - resumo['versiculos'])
        extra = (
            f' Mais {em_curso} versículos num capítulo ainda em curso, que o MyBible '
            'só mostra quando o capítulo fechar.'
            if em_curso else ''
        )
        linhas.append(
            f'- Módulos: {"Bíblia completa" if resumo["completo"] else "parciais"}, '
            f'{resumo["capitulos"]} capítulos completos e {resumo["versiculos"]} versículos '
            f'visíveis no MyBible (recompilados nesta execução).{extra}'
        )
    elif env.exists():
        # Não houve capítulo novo, mas os módulos de antes continuam válidos.
        linhas.append(
            '- Módulos: sem capítulos novos nesta execução; os de antes continuam válidos.'
        )
    else:
        linhas.append('- Módulos: ainda não há capítulos completos (precisa de fechar João 5)')
    linhas.append(f'- Dados: {publicado} (ramo `{ramo}`)')
    if pacote:
        linhas.append(
            f'- **Descarregue para o MyBible:** Abaixo, em *Artifacts* → '
            f'`BEE-modulos.zip` com os dois ficheiros .SQLite3.'
        )
    _resumo('\n'.join(linhas))
    # 'nada' com falhas deve deixar a execução vermelha no GitHub — exceto
    # quando a causa é o serviço estar em baixo (5xx): isso não é um defeito do
    # projeto e o próximo ciclo agendado volta a tentar. Falhas de configuração
    # continuam a marcar a execução como falhada, para não passarem em claro.
    if resultado.acao == 'nada' and estado.falhas_seguidas:
        if _parece_transitorio(estado.ultimo_erro or ''):
            return 0
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
