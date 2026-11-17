#!/usr/bin/env python3
"""Ciclo de produção numa GitHub Action: gera, compila, publica e arquiva.

Diferente de `autopiloto.py`, este script não dorme. Cada execução faz um
pequeno bloco de trabalho e termina; o agendador do GitHub (cron) volta a
chamá-lo. É assim que a produção continua mesmo com o computador desligado.

O que guarda:
  - os JSON dos capítulos no ramo de dados, sem misturar com o código;
  - os módulos SQLite3 como artefato descarregável (retenção configurável);
  - um HTML por capítulo produzido (artifact + release `bee-previa`);
  - um resumo no resumo da execução do GitHub.
"""
from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import autopiloto
from bee.agenda import (
    Agendador, Diario, carregar_estado, escrever_atomico, livros_na_fila,
    proximo_trabalho, salvar_estado,
    _agora,
)
from bee.arquivos import DadosInvalidos, ler_todos
from bee.catalogo import POR_NUMERO
from bee.compilador import ErroCompilacao, compilar
from bee.fontes import ErroFonte, FontesOriginais
from bee.rede import ClienteHTTP, ErroRede
from bee.trava import EmExecucao, trava


ROTULO = 'BEE · nuvem'

# O GitHub envia SIGTERM quando o job chega ao timeout-minutes e só depois
# SIGKILL. Este sinal permite terminar o ciclo no ponto seguro, compilar,
# exportar e publicar o que já está no disco.
_PARAR = False


def _pedir_paragem(signum, frame) -> None:  # noqa: ARG001
    global _PARAR
    _PARAR = True
    print('Pedido de paragem recebido; a fechar o ciclo e a publicar o que existe.', flush=True)


def _instalar_sinais() -> None:
    for nome in ('SIGTERM', 'SIGINT'):
        sinal = getattr(signal, nome, None)
        if sinal is not None:
            try:
                signal.signal(sinal, _pedir_paragem)
            except (ValueError, OSError):
                pass


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
    referencia = f'refs/remotes/origin/{ramo}'
    anterior = _git('rev-parse', '--verify', referencia, verificar=False)
    if anterior.returncode != 0 or not anterior.stdout.strip():
        # No workflow o ramo é buscado para FETCH_HEAD, não para
        # refs/remotes/origin/…; sem esta busca a reparação seria um no-op
        # silencioso exactamente onde é precisa.
        try:
            _git('fetch', '--quiet', '--depth=1', 'origin', f'+refs/heads/{ramo}:{referencia}')
        except subprocess.CalledProcessError:
            return 'sem ramo de dados publicado', 0
        anterior = _git('rev-parse', '--verify', referencia, verificar=False)
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
    # Compila sempre que valha a pena, mesmo quando o ciclo terminou como
    # 'nada' ou 'parar': o ciclo pode ter gravado versículos antes de falhar.
    # Em 17/11 o ciclo 3 morreu com um JSON inválido e esta condição deitou
    # fora 9 capítulos completos que já estavam no disco.
    if resultado is not None and resultado.resumo_compilacao:
        return
    if _env('BEE_COMPILAR', '1') == '0':  # respeita BEE_COMPILAR=0
        return
    if not _modulos_desatualizados(dados, saida):
        return
    try:
        resumo = compilar(dados, saida)
    except Exception as exc:  # a compilação nunca deve estragar a produção
        diario.escrever(f'A compilação do fim do ciclo falhou; módulos anteriores preservados: {exc}', 'aviso')
        return None
    if resultado is not None:
        resultado.resumo_compilacao = resumo
    diario.escrever(
        f'Módulos recompilados no fim do ciclo: {resumo["capitulos"]}/1189 capítulos, '
        f'{resumo["versiculos"]} versículos.'
    )
    return resumo


def _mapa_capitulos(dados: Path) -> dict[tuple[int, int], int]:
    """{(book_number, capítulo): quantos versículos estão guardados}.

    Conta também os capítulos ainda em curso (`in_progress`): é o que a
    produção escreve antes de o capítulo fechar, e é precisamente o que se
    quer poder ler no telemóvel enquanto o capítulo não está inteiro.
    """
    mapa: dict[tuple[int, int], int] = {}
    for numero, livro in ler_todos(dados).items():
        for colecao in ('chapters', 'in_progress'):
            for cap, versos in livro.get(colecao, {}).items():
                mapa[(numero, int(cap))] = len(versos)
    return mapa


def _ficheiro_capitulo(nome: str, cap: int) -> str:
    texto = unicodedata.normalize('NFKD', nome)
    simples = ''.join(c for c in texto if not unicodedata.combining(c) and c.isalnum())
    return f'{simples}-{cap:03d}.html'


ESTILO_CAPITULO = (
    ':root{--tinta:#242019;--suave:#635c4e;--acento:#2e6b45;--fundo:#faf7f1;'\
    '--cartao:#f1ebe0;--borda:#ddd3c0}'\
    '@media(prefers-color-scheme:dark){:root{--tinta:#e7e2d6;--suave:#a59d8c;'\
    '--acento:#95cba4;--fundo:#171511;--cartao:#22201a;--borda:#3c382d}}'\
    '*{box-sizing:border-box}'\
    'html{-webkit-text-size-adjust:100%}'\
    'body{margin:0;background:var(--fundo);color:var(--tinta);'\
    "font-family:Georgia,'Times New Roman',serif;line-height:1.75;font-size:18px}"\
    'main{max-width:38em;margin:0 auto;padding:1.4em 1.2em 3.5em}'\
    'header{border-bottom:2px solid var(--borda);padding-bottom:.55em;margin-bottom:1.1em}'\
    'h1{margin:0;font-size:1.6em;line-height:1.25;font-weight:normal}'\
    '.rotulo{color:var(--suave);font-size:.78em;margin-top:.25em;'\
    "font-family:system-ui,sans-serif}"\
    '.aviso{background:var(--cartao);border:1px solid var(--borda);'\
    'border-radius:10px;padding:.6em .85em;font-size:.76em;color:var(--suave);'\
    'margin:0 0 1.6em;line-height:1.55;font-family:system-ui,sans-serif}'\
    '.v{margin:0 0 1em}'\
    '.v sup{color:var(--acento);font-weight:700;font-size:.7em;'\
    'margin-right:.45em;font-family:system-ui,sans-serif}'\
    'details{margin:-.5em 0 1.4em;border:1px solid var(--borda);'\
    'border-radius:10px;background:var(--cartao);overflow:hidden}'\
    'summary{cursor:pointer;padding:.55em .9em;color:var(--acento);'\
    "font-family:system-ui,sans-serif;font-size:.78em;font-weight:600;"\
    'letter-spacing:.02em}'\
    'summary::before{content:"▸ "}'\
    'details[open] summary::before{content:"▾ "}'\
    'details>div{padding:.2em 1em .75em;font-size:.88em;line-height:1.65;'\
    'border-top:1px solid var(--borda)}'\
    'details b{color:var(--acento)}'\
    'details p{margin:.45em 0}'\
    'i{font-style:italic}'\
)


def exportar_capitulos(
    dados: Path, destino: Path, antes: dict[tuple[int, int], int], diario,
) -> tuple[list[str], int]:
    """Um HTML legível por capítulo, todos os capítulos, em cada execução.

    O módulo MyBible só recebe capítulos completos e consecutivos; quem quer
    verificar no telemóvel um capítulo acabado (ou a meio) não tinha nada para
    abrir. Os ficheiros viajam como artifact da execução e como assets do
    release `bee-previa`, que fica com a coleção completa e atual.
    Devolve (ficheiros escritos, quantos capítulos mudaram nesta execução).
    """
    try:
        livros = ler_todos(dados)
    except DadosInvalidos as exc:
        diario.escrever(f'A exportação de capítulos falhou: {exc}', 'aviso')
        return [], 0
    exportados: list[str] = []
    novos = 0
    destino.mkdir(parents=True, exist_ok=True)
    for numero, livro_dados in sorted(livros.items()):
        livro = POR_NUMERO[numero]
        vistos: set[int] = set()
        for colecao, completo in (('chapters', True), ('in_progress', False)):
            for cap in sorted(livro_dados.get(colecao, {}), key=int):
                chave = (numero, int(cap))
                if chave in vistos:
                    continue
                vistos.add(chave)
                versos = livro_dados[colecao][cap]
                if len(versos) != antes.get(chave, -1):
                    novos += 1
                total = livro.versos_por_capitulo[int(cap) - 1]
                em_curso = not completo and len(versos) < total
                cabecalho = f'{escape(livro.nome)} {cap}'
                linhas = [
                    '<!DOCTYPE html>',
                    '<html lang="pt"><head><meta charset="utf-8">',
                    '<meta name="viewport" content="width=device-width, initial-scale=1">',
                    f'<title>{cabecalho} — BEE</title>',
                    f'<style>{ESTILO_CAPITULO}</style></head><body><main>',
                    f'<header><h1>{cabecalho}</h1>'
                    + (
                        f'<div class="rotulo">em curso: {len(versos)} de {total} versículos</div>'
                        if em_curso else ''
                    )
                    + '</header>',
                    '<div class="aviso">Bíblia de Estudo Epignósis — rascunho automático '
                    'gerado por IA e <b>NÃO revisto</b>. Autor: Martinho S. S. Madureira. '
                    f'Gerado em {_agora():%d/%m/%Y %H:%M}.</div>',
                ]
                for versiculo in sorted(versos, key=lambda v: v['verse']):
                    linhas.append(
                        f'<p class="v"><sup>{versiculo["verse"]}</sup>{versiculo["text"]}</p>'
                    )
                    if versiculo.get('commentary'):
                        linhas.append(
                            '<details><summary>Comentário — toque para abrir</summary><div>'
                            + versiculo['commentary'] + '</div></details>'
                        )
                linhas.append('</main></body></html>')
                caminho = destino / _ficheiro_capitulo(livro.nome, int(cap))
                try:
                    escrever_atomico(caminho, '\n'.join(linhas))
                except (OSError, ValueError) as exc:
                    diario.escrever(f'A exportação de {caminho.name} falhou: {exc}', 'aviso')
                    continue
                exportados.append(caminho.name)
    if exportados:
        diario.escrever(
            f'Capítulos exportados para leitura: {len(exportados)} '
            f'({novos} mudaram nesta execução).'
        )
    return exportados, novos


LEIA_ME = (
    'Bíblia de Estudo Epignósis (BEE) — Projeto Epignósis.\n'
    'Autor: Martinho S. S. Madureira.\n'
    'Publicado por Martinho S. S. Madureira Ministries.\n'
    '\n'
    'Rascunho automático: este conteúdo é gerado por IA sob direcção do autor\n'
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


def _escrever_relatorio(
    saida: Path, dados: Path, motores: list, resultado, publicado: str,
    ramo: str, exportados: list[str],
) -> Path:
    """Relatório sempre presente no artefacto, mesmo quando não há módulos.

    A execução #12 terminou sem artefacto de capítulos e com o de módulos
    vazio; quem ia buscar o resultado não tinha como saber o que aconteceu.
    Este ficheiro garante que existe algo para descarregar e para diagnosticar.
    """
    capitulos, versos = _progresso(dados)
    linhas = [
        'BEE — relatório da execução',
        f'Gerado em: {_agora():%Y-%m-%d %H:%M:%S} UTC',
        f'Execução GitHub: {_env("GITHUB_RUN_NUMBER", "local")}',
        f'Ramo de dados: {ramo}',
        f'Provedores ativos: {", ".join(m.provedor for m in motores) or "(nenhum)"}',
        f'Ação: {getattr(resultado, "acao", "interrompida")}',
        f'Detalhe: {getattr(resultado, "detalhe", "") or "(sem detalhe)"}',
        f'Capítulos completos: {capitulos}/1189',
        f'Versículos guardados: {versos}/31102',
        f'Capítulos exportados para leitura: {len(exportados)}',
        f'Dados: {publicado}',
    ]
    modulo = saida / 'BEE.SQLite3'
    if modulo.exists():
        try:
            import sqlite3
            with sqlite3.connect(modulo) as conexao:
                linhas.append(
                    'Módulo MyBible: '
                    f'{conexao.execute("SELECT COUNT(*) FROM verses").fetchone()[0]} versículos'
                )
        except Exception as exc:  # diagnóstico não pode falhar a execução
            linhas.append(f'Módulo MyBible: não foi possível ler ({type(exc).__name__})')
    else:
        linhas.append('Módulo MyBible: não gerado nesta execução')
    caminho = saida / 'RELATORIO.txt'
    escrever_atomico(caminho, '\n'.join(linhas) + '\n')
    return caminho


def main() -> int:
    _instalar_sinais()
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
    # 9 minutos por padrão: o job tem 12, e ainda é preciso compilar, exportar,
    # publicar e carregar artefactos. Antes o ciclo podia durar os 50 minutos e
    # ser morto com trabalho por publicar.
    config.max_tempo_ciclo = float(_env('BEE_TEMPO_MAXIMO', '540') or 0)
    # Tecto para o script inteiro (incluindo as repetições por falha
    # transitória). Sem isto, `BEE_TENTATIVAS_CICLO=8` podia somar 8 ciclos de
    # 9 min e continuar a estourar o timeout do job.
    inicio_execucao = time.monotonic()
    limite_total = float(_env('BEE_TEMPO_TOTAL', '660') or 0)
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
    antes_capitulos = _mapa_capitulos(dados)
    falha: str | None = None
    resultado = None
    exportados: list[str] = []
    motores: list = []
    publicado_cedo = ''

    try:
        with trava(dados):
            rede = ClienteHTTP(pausa=float(_env('BEE_PAUSA', '1') or 1),
                               tentativas=_env_int('BEE_TENTATIVAS', 3),
                               timeout=float(_env('BEE_TIMEOUT', '180') or 180))
            try:
                motores = autopiloto._motores(argumentos, rede)
            except SystemExit as exc:
                # Sem chaves não há fila. Transformar em ErroRede faz com que
                # o bloco de preservação escreva o resumo e o RELATORIO.txt,
                # em vez de o processo morrer sem deixar artefacto.
                raise ErroRede(str(exc)) from None
            print(f'{ROTULO}: {", ".join(m.provedor for m in motores)}', flush=True)
            fontes = FontesOriginais(cache, rede)
            agendador = Agendador(
                dados, saida, cache, estado, config, diario, fuso, motores, fontes, rede,
            )
            if limite_total > 0:
                restante = limite_total - (time.monotonic() - inicio_execucao)
                config.max_tempo_ciclo = max(0.0, min(config.max_tempo_ciclo, restante))
            resultado = agendador.ciclo(livros)
            salvar_estado(estado_caminho, estado)
            # Checkpoint imediato: se o job for morto a seguir (timeout,
            # cancelamento manual), os versículos já gerados ficam no ramo.
            if (
                _env('BEE_PUBLICAR', '1') != '0'
                and resultado.progresso is not None
                and resultado.progresso.versos
            ):
                try:
                    cap_checkpoint, _ = _progresso(dados)
                    publicado_cedo = _commit_dados(
                        ramo,
                        f'BEE: checkpoint de {resultado.progresso.versos} versículos '
                        f'({cap_checkpoint}/1189 capítulos completos)',
                        ['livros_json'],
                    )
                    print(f'Checkpoint publicado: {publicado_cedo}', flush=True)
                except Exception as exc:  # a publicação final ainda tenta
                    publicado_cedo = f'checkpoint falhou ({type(exc).__name__})'
                    print(f'Aviso: {publicado_cedo}', file=sys.stderr, flush=True)
            # O serviço de IA às vezes responde 5xx em rajada (foi o que
            # aconteceu na primeira execução real). Em vez de gastar uma
            # execução inteira do cron, tenta-se de novo aqui.
            extra = _env_int('BEE_TENTATIVAS_CICLO', 2) - 1
            while (
                resultado.acao == 'nada' and extra > 0 and not _PARAR
                and estado.falhas_seguidas < agendador.config.max_falhas_seguidas
                and _parece_transitorio(estado.ultimo_erro or '')
                and (limite_total <= 0 or time.monotonic() < inicio_execucao + limite_total)
            ):
                print('Falha transitória do serviço; nova tentativa no mesmo trabalho...', flush=True)
                diario.escrever('Falha transitória do serviço; nova tentativa no mesmo trabalho.', 'aviso')
                time.sleep(float(_env('BEE_ESPERA_ENTRE_TENTATIVAS', '45') or 45))
                extra -= 1
                if limite_total > 0:
                    restante = limite_total - (time.monotonic() - inicio_execucao)
                    config.max_tempo_ciclo = max(0.0, min(config.max_tempo_ciclo, restante))
                resultado = agendador.ciclo(livros)
                salvar_estado(estado_caminho, estado)
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
        # Uma falha a meio do ciclo não pode deitar fora o trabalho já feito.
        # Em 17/11 o ciclo 3 morreu com um JSON inválido em João 15 e os 10
        # capítulos gerados nessa execução nunca foram compilados nem
        # publicados: o artifact saiu vazio e o ramo de dados ficou atrasado.
        falha = f'{type(exc).__name__}: {exc}'
        print(f'AVISO: o ciclo falhou; o trabalho já gravado vai ser compilado e '
              f'publicado na mesma. Causa: {falha}', file=sys.stderr, flush=True)
        diario.escrever(f'Ciclo interrompido: {falha}', 'erro')

    # A partir daqui o trabalho feito é preservado mesmo com falha: compilar,
    # publicar e empacotar não dependem de o ciclo ter terminado bem.
    resumo_compilacao = _compilar_no_fim(resultado, dados, saida, diario)
    exportados, capitulos_novos = exportar_capitulos(
        dados, saida.parent / 'capitulos', antes_capitulos, diario,
    )
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
    relatorio = _escrever_relatorio(
        saida, dados, motores, resultado, publicado, ramo, exportados,
    )
    env = (saida / 'BEE.SQLite3')
    trabalho = proximo_trabalho(livros, dados)
    faltam_livro, faltam_fila = _passo_do_plano(dados, livros)
    transitorio = _parece_transitorio(estado.ultimo_erro or '')
    # Números pequenos e absolutos, sem percentagens que sugiram progresso que
    # não existe: o que conta é quantos capítulos estão completos e quantos
    # versículos já estão guardados (mesmo em capítulos ainda em curso).
    linhas = [f'### {ROTULO}', '']
    linhas.append(
        '- Provedores ativos: '
        + (', '.join(f'`{m.provedor}`' for m in motores) if motores else '**(nenhum)**')
    )
    if publicado_cedo:
        linhas.append(f'- Checkpoint publicado durante o ciclo: {publicado_cedo}.')
    if resultado is None:
        # O ciclo pode ter falhado antes de devolver um ResultadoCiclo.
        linhas.append(f'- Ação: **interrompida** — {falha}')
        linhas.append(
            '- **O trabalho feito antes da falha foi guardado** (compilado e '
            'publicado). O próximo ciclo continua a partir dele.'
        )
    elif resultado.acao == 'adormecer':
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
                      'agendado (20 min) volta a tentar sozinho; não precisa de fazer nada.')
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
    if resumo_compilacao:
        resumo = resumo_compilacao
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
    elif depois_cap:
        # Havia capítulos completos mas a compilação não aconteceu: dizê-lo
        # com o nome do próximo capítulo a fechar, em vez da frase fixa
        # "precisa de fechar João 5" que apareceu com 15 capítulos completos.
        proximo = (
            f'{trabalho[0].nome} {estado.lote_capitulo}'
            if trabalho and estado.lote_capitulo else 'o capítulo em curso'
        )
        linhas.append(
            f'- Módulos: **não recompilados nesta execução** (havia {depois_cap} '
            f'capítulos completos). Os módulos de antes continuam válidos; '
            f'este ciclo não conseguiu gerar. A seguir: {proximo}.'
        )
    else:
        linhas.append('- Módulos: ainda não há capítulos completos.')
    linhas.append(f'- Dados: {publicado} (ramo `{ramo}`)')
    if exportados:
        linhas.append(
            f'- **Capítulos para ler no telemóvel:** {len(exportados)} no total, '
            f'{capitulos_novos} mudado(s) nesta execução — em *Artifacts* → '
            '`BEE-capitulos` desta execução e acumulados no release `bee-previa` '
            '(Assets), um ficheiro HTML por capítulo.'
        )
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
    if falha:
        # A execução fica vermelha — o autor tem de saber — mas o resumo já
        # explicou que o trabalho ficou guardado.
        return 1
    if resultado is not None and resultado.acao == 'nada' and estado.falhas_seguidas:
        if _parece_transitorio(estado.ultimo_erro or ''):
            return 0
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
