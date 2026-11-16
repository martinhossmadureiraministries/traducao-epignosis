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

import os
from pathlib import Path
import subprocess
import sys
from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import autopiloto
from bee.agenda import (
    Agendador, Diario, carregar_estado, livros_na_fila, proximo_trabalho, salvar_estado,
)
from bee.arquivos import DadosInvalidos, ler_todos
from bee.compilador import ErroCompilacao
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


def _progresso(dados: Path) -> tuple[int, int]:
    livros = ler_todos(dados)
    capitulos = sum(len(item['chapters']) for item in livros.values())
    versos = sum(len(v) for item in livros.values() for v in item['chapters'].values())
    return capitulos, versos


def _git(*comandos: str, verificar: bool = True, env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        ('git',) + comandos, check=verificar, text=True, env=env,
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
    comando = ['commit-tree', arvore, '-m', mensagem]
    if pai:
        comando[2:2] = ['-p', pai.splitlines()[0]]
    novo = _git(*comando, env=env).stdout.strip()
    _git('push', 'origin', f'{novo}:refs/heads/{ramo}')
    return 'JSON publicados' if pai else 'ramo de dados criado'


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

    estado_caminho = dados / '.bee' / 'estado.json'
    estado = carregar_estado(estado_caminho)
    diario = Diario(dados / '.bee' / 'diario.md')
    config = autopiloto._config(argumentos)
    config.fuso = fuso_nome
    config.intervalo_min = 0
    if _env('BEE_COMPILAR', '1') == '0':
        config.compilar = False

    livros = livros_na_fila(argumentos.livros, argumentos.ordem)
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
    except EmExecucao as exc:
        _resumo(f'### {ROTULO}\n\nOutra execução está a usar os dados: {exc}. Nada foi feito.')
        return 0
    except (DadosInvalidos, ErroCompilacao, ErroFonte, ErroRede, ValueError, OSError) as exc:
        _resumo(f'### {ROTULO}\n\nFalha: `{type(exc).__name__}` — {exc}')
        return 1

    depois_cap, depois_versos = _progresso(dados)
    ramo = _env('BEE_BRAMO_DADOS', 'bee-dados')
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

    pacote = _empacotar(saida)
    trabalho = proximo_trabalho(livros, dados)
    faltam_livro, faltam_fila = _passo_do_plano(dados, livros)
    linhas = [f'### {ROTULO}', '',
              f'- Ação: **{resultado.acao}** — {resultado.detalhe or "—"}']
    if resultado.progresso:
        linhas.append(f'- Esta execução: +{resultado.progresso.versos} versículos, '
                      f'+{resultado.progresso.capitulos} capítulos')
    linhas.append(f'- Progresso: **{depois_cap}/1189 capítulos**, {depois_versos}/31102 versículos')
    seguinte = f'{trabalho[0].nome} {trabalho[1]}' if trabalho else 'nada pendente'
    linhas.append('- A seguir: ' + seguinte)
    if faltam_livro:
        linhas.append(
            f'- Faltam {faltam_livro} versículos para concluir '
            f'**{trabalho[0].nome}**; {faltam_fila} em toda a fila'
        )
    if resultado.resumo_compilacao:
        resumo = resultado.resumo_compilacao
        linhas.append(f'- Módulos: {"completo" if resumo["completo"] else "PARCIAL"}, '
                      f'{resumo["versiculos"]} versículos')
    linhas.append(f'- Dados: {publicado} (ramo `{ramo}`)')
    if pacote:
        linhas.append(f'- Módulos: `{pacote}` (descarregue em Artifacts)')
    else:
        linhas.append('- Módulos: ainda não há capítulos completos')
    _resumo('\n'.join(linhas))
    # 'nada' com falhas deve deixar a execução vermelha no GitHub.
    return 1 if resultado.acao == 'nada' and estado.falhas_seguidas else 0


if __name__ == '__main__':
    raise SystemExit(main())
