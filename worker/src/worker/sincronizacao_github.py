"""Sincronização dos dados BEE com o GitHub via API REST.

Sem git local: cada sincronização baixa os JSON do ramo de dados e sobe as
mudanças como um commit de árvore (blobs → tree → commit → ref). O token vem
do ambiente (`GITHUB_TOKEN`, secret do workspace vinculado ao deployment) e
nunca é escrito em ficheiros nem em registos.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

API = 'https://api.github.com'
UPLOADS = 'https://uploads.github.com'
PASTA_DADOS = 'livros_json'
PASTA_ENTREGAS = 'entregas'
MODULOS = ('BEE.SQLite3', 'BEE.commentaries.SQLite3')
TAG_PREVIA = 'bee-previa'
LEIA_ME = (
    'Bíblia de Estudo Epignósis (BEE) — prévia de produção automática.\n'
    'Copie os dois ficheiros .SQLite3 para a pasta de módulos do MyBible.\n'
    'Rascunho gerado por IA sob direção editorial; sujeito a revisão humana.\n'
)


class ErroGitHub(RuntimeError):
    pass


def _token() -> str:
    token = os.environ.get('GITHUB_TOKEN', '').strip()
    if not token:
        raise ErroGitHub(
            'GITHUB_TOKEN ausente: crie o secret no Mistral Studio e vincule-o ao deployment.'
        )
    return token


def _pedido(
    metodo: str, url: str, corpo: dict[str, Any] | None = None,
    bruto: bytes | None = None, content_type: str = 'application/json',
    aceitar: str = 'application/vnd.github+json',
) -> Any:
    dados = bruto if bruto is not None else (
        json.dumps(corpo).encode('utf-8') if corpo is not None else None
    )
    requisicao = urllib.request.Request(url, data=dados, method=metodo, headers={
        'Authorization': f'Bearer {_token()}',
        'Accept': aceitar,
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': content_type,
        'User-Agent': 'bee-workflow-mistral',
    })
    try:
        with urllib.request.urlopen(requisicao, timeout=120) as resposta:
            conteudo = resposta.read()
    except urllib.error.HTTPError as exc:
        detalhe = exc.read().decode('utf-8', 'replace')[:300]
        raise ErroGitHub(f'GitHub {metodo} {url}: HTTP {exc.code}: {detalhe}') from exc
    if not conteudo:
        return None
    texto = conteudo.decode('utf-8', 'replace')
    if texto.lstrip().startswith(('{', '[')):
        return json.loads(texto)
    return conteudo


def baixar_dados(
    repositorio: str, ramo: str, diretorio: Path, ramo_base: str = 'main',
) -> list[str]:
    """Copia os JSON de `livros_json` do ramo de dados (ou do ramo base) para `diretorio`."""
    diretorio.mkdir(parents=True, exist_ok=True)
    try:
        listagem = _pedido('GET', f'{API}/repos/{repositorio}/contents/{PASTA_DADOS}?ref={ramo}')
    except ErroGitHub:
        listagem = _pedido('GET', f'{API}/repos/{repositorio}/contents/{PASTA_DADOS}?ref={ramo_base}')
    baixados = []
    for item in listagem:
        nome = item['name']
        if not nome.endswith('.json') or nome.startswith('.'):
            continue
        conteudo = _pedido(
            'GET', f'{API}/repos/{repositorio}/contents/{PASTA_DADOS}/{nome}?ref={ramo}',
            aceitar='application/vnd.github.raw+json',
        )
        if isinstance(conteudo, dict) and conteudo.get('encoding') == 'base64':
            bruto = base64.b64decode(conteudo['content'])
        elif isinstance(conteudo, bytes):
            bruto = conteudo
        else:
            bruto = json.dumps(conteudo, ensure_ascii=False).encode('utf-8')
        (diretorio / nome).write_bytes(bruto)
        baixados.append(nome)
    return baixados


def _sha_do_ramo(repositorio: str, ramo: str) -> str | None:
    try:
        referencia = _pedido('GET', f'{API}/repos/{repositorio}/git/ref/heads/{ramo}')
    except ErroGitHub as exc:
        if 'HTTP 404' in str(exc):
            return None
        raise
    return referencia['object']['sha']


def commit_arquivos(
    repositorio: str, ramo: str, arquivos: dict[str, bytes], mensagem: str,
) -> str:
    """Sobe `arquivos` (caminho → conteúdo) num único commit no ramo indicado."""
    if not arquivos:
        return ''
    base = _sha_do_ramo(repositorio, ramo)
    if base is None:
        padrao = _pedido('GET', f'{API}/repos/{repositorio}')['default_branch']
        pai = _sha_do_ramo(repositorio, padrao)
        if pai is None:
            raise ErroGitHub(f'Ramo {ramo!r} e ramo base {padrao!r} inexistentes.')
        criado = _pedido(
            'POST', f'{API}/repos/{repositorio}/git/refs',
            {'ref': f'refs/heads/{ramo}', 'sha': pai},
        )
        base = criado['object']['sha']
    pai = _pedido('GET', f'{API}/repos/{repositorio}/git/commits/{base}')
    nos = []
    for caminho, conteudo in sorted(arquivos.items()):
        blob = _pedido(
            'POST', f'{API}/repos/{repositorio}/git/blobs',
            {'content': base64.b64encode(conteudo).decode('ascii'), 'encoding': 'base64'},
        )
        nos.append({'path': caminho, 'mode': '100644', 'type': 'blob', 'sha': blob['sha']})
    arvore = _pedido(
        'POST', f'{API}/repos/{repositorio}/git/trees',
        {'base_tree': pai['tree']['sha'], 'tree': nos},
    )
    commit = _pedido(
        'POST', f'{API}/repos/{repositorio}/git/commits',
        {'message': mensagem, 'tree': arvore['sha'], 'parents': [base]},
    )
    _pedido(
        'PATCH', f'{API}/repos/{repositorio}/git/refs/heads/{ramo}',
        {'sha': commit['sha'], 'force': False},
    )
    return commit['sha']


def empacotar_modulos(diretorio_saida: Path, destino: Path) -> Path | None:
    """ZIP com os dois módulos MyBible, pronto para copiar ao telefone."""
    modulos = [diretorio_saida / nome for nome in MODULOS]
    if not all(caminho.exists() for caminho in modulos):
        return None
    destino.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destino, 'w', zipfile.ZIP_DEFLATED) as pacote:
        for caminho in modulos:
            pacote.write(caminho, caminho.name)
        pacote.writestr('LEIA-ME.txt', LEIA_ME)
    return destino


def publicar_release(repositorio: str, zip_path: Path, descricao: str) -> str:
    """Cria ou atualiza a release `bee-previa` com o ZIP dos módulos como asset."""
    existente = None
    try:
        existente = _pedido('GET', f'{API}/repos/{repositorio}/releases/tags/{TAG_PREVIA}')
    except ErroGitHub as exc:
        if 'HTTP 404' not in str(exc):
            raise
    if existente is None:
        existente = _pedido(
            'POST', f'{API}/repos/{repositorio}/releases',
            {
                'tag_name': TAG_PREVIA, 'target_commitish': 'main',
                'name': 'BEE — prévia para MyBible', 'body': descricao,
                'prerelease': True,
            },
        )
    else:
        _pedido(
            'PATCH', f'{API}/repos/{repositorio}/releases/{existente["id"]}',
            {'body': descricao},
        )
        for asset in existente.get('assets', []):
            if asset['name'] == zip_path.name:
                _pedido('DELETE', f'{API}/repos/{repositorio}/releases/assets/{asset["id"]}')
    _pedido(
        'POST',
        f'{UPLOADS}/repos/{repositorio}/releases/{existente["id"]}/assets?name={zip_path.name}',
        bruto=zip_path.read_bytes(), content_type='application/zip',
    )
    return existente.get('html_url', '')


def publicar_modulos(
    repositorio: str, ramo: str, diretorio_dados: Path, diretorio_saida: Path,
    publicar_release: bool, descricao: str,
) -> dict[str, Any]:
    """Compila os módulos MyBible, commita-os no ramo de dados e publica a release."""
    from bee.compilador import compilar

    resumo: dict[str, Any] = {'compilado': False}
    try:
        contagens = compilar(diretorio_dados, diretorio_saida)
    except Exception as exc:
        resumo['erro_compilacao'] = str(exc)[:300]
        return resumo
    resumo['compilado'] = True
    resumo['contagens'] = {chave: str(valor) for chave, valor in contagens.items()}
    arquivos = {
        f'{PASTA_ENTREGAS}/{nome}': (diretorio_saida / nome).read_bytes() for nome in MODULOS
    }
    pacote = empacotar_modulos(diretorio_saida, diretorio_saida / 'BEE-modulos.zip')
    if pacote is not None:
        arquivos[f'{PASTA_ENTREGAS}/{pacote.name}'] = pacote.read_bytes()
    resumo['commit_modulos'] = commit_arquivos(
        repositorio, ramo, arquivos, f'Módulos MyBible compilados: {descricao}'[:250]
    )
    if publicar_release and pacote is not None:
        resumo['release'] = publicar_release(repositorio, pacote, descricao)
    return resumo
