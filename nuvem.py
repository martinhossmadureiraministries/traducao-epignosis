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
from datetime import timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import autopiloto
from bee.agenda import (
    Agendador, Diario, carregar_estado, escrever_atomico, livros_na_fila,
    proximo_trabalho, salvar_estado,
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
    'ServicoIndisponivel', 'HTTP 5', 'HTTP 408', 'HTTP 409', 'HTTP 425',
    'falha de rede', 'timed out', 'timeout',
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
    if _env('BEE_UNIR', '1') != '0' and remoto is not None and remoto.is_dir():
        mantidos = _unir_progresso(dados, remoto)
        if mantidos:
            print(f'Progresso recuperado sem sobrescrever {mantidos} versículo(s) já existentes localmente.')
        _apagar_recuperado(remoto)

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
    transitorio = _parece_transitorio(estado.ultimo_erro or '')
    # Números pequenos e absolutos, sem percentagens que sugiram progresso que
    # não existe: o que conta é quantos capítulos estão completos e quantos
    # versículos já estão guardados (mesmo em capítulos ainda em curso).
    linhas = [f'### {ROTULO}', '']
    if resultado.acao == 'gerado':
        linhas.append(f'- Ação: **{resultado.acao}** — {resultado.detalhe or "—"}')
        linhas.append(f'- Esta execução: +{resultado.progresso.versos} versículos, '
                      f'+{resultado.progresso.capitulos} capítulos')
    elif transitorio:
        linhas.append('- Ação: **nada gerado nesta execução** — o serviço de IA não respondeu.')
        linhas.append('- **Não é um erro do projeto nem da sua chave.** O próximo ciclo '
                      'agendado (15 min) volta a tentar sozinho; não precisa de fazer nada.')
    else:
        linhas.append(f'- Ação: **nada** — {resultado.detalhe or "—"}')
    linhas.append(f'- Progresso: **{depois_cap}/1189 capítulos completos**, '
                  f'{depois_versos}/31102 versículos guardados')
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
            '- **Causa provável:** serviço de IA instável (5xx) — não é a sua chave nem o '
            'projeto; o próximo ciclo tenta de novo.'
            if transitorio else
            '- **Causa provável:** configuração (chave, modelo ou quota). '
            'Corra `python autopiloto.py --testar` e veja a tabela em COMECAR_HOJE.md.'
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
