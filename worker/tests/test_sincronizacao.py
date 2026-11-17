"""Sincronização GitHub: baixar JSON, commit de árvore, release — tudo simulado."""
import pytest


class GitHubFalso:
    """Roteador mínimo dos endpoints usados por sincronizacao_github."""

    def __init__(self, arquivos: dict[str, bytes] | None = None):
        self.arquivos = dict(arquivos or {})
        self.refs = {'bee-dados': 'sha-base', 'main': 'sha-base'}
        self.commits = {'sha-base': {'sha': 'sha-base', 'tree': {'sha': 'tree-base'}}}
        self.arvores = {'tree-base': {'sha': 'tree-base'}}
        self.contador = 0
        self.releases: dict[str, dict] = {}
        self.assets_apagados: list[str] = []
        self.commits_criados: list[dict] = []

    def rotear(self, metodo: str, url: str, corpo=None, bruto=None,
               content_type='application/json', aceitar='application/vnd.github+json'):
        self.contador += 1
        caminho = url.split('github.com', 1)[-1] if 'github.com' in url else url
        assert url.startswith('https://api.github.com') or url.startswith('https://uploads.github.com')
        if 'api.github.com/repos/' in url:
            resto = url.split('api.github.com/repos/', 1)[1].split('?')[0]
        else:
            resto = url.split('uploads.github.com/repos/', 1)[1].split('?')[0]
        partes = resto.strip('/').split('/')

        if metodo == 'GET' and resto == 'martinhossmadureiraministries/traducao-epignosis':
            return {'default_branch': 'main'}
        if partes[:2] == ['martinhossmadureiraministries', 'traducao-epignosis']:
            r = partes[2:]
        else:
            raise AssertionError(f'URL inesperada: {url}')

        if metodo == 'GET' and r == ['contents', 'livros_json']:
            nomes = sorted(caminho.split('livros_json/', 1)[1] for caminho in self.arquivos
                           if caminho.startswith('livros_json/') and not caminho.split('/')[-1].startswith('.'))
            return [{'name': nome, 'type': 'file'} for nome in nomes]
        if metodo == 'GET' and len(r) == 3 and r[0] == 'contents' and r[1] == 'livros_json':
            if aceitar.endswith('raw+json'):
                return self.arquivos[f'livros_json/{r[2]}']
            import base64
            return {'encoding': 'base64', 'content': base64.b64encode(self.arquivos[f'livros_json/{r[2]}']).decode()}
        if metodo == 'GET' and r[:2] == ['git', 'ref']:
            chave = '/'.join(r[3:])
            if chave not in self.refs:
                from worker.sincronizacao_github import ErroGitHub
                raise ErroGitHub(f'GitHub GET {url}: HTTP 404: not found')
            return {'object': {'sha': self.refs[chave]}}
        if metodo == 'POST' and r == ['git', 'refs']:
            self.refs[corpo['ref'].split('heads/')[1]] = corpo['sha']
            return {'object': {'sha': corpo['sha']}}
        if metodo == 'GET' and r[:2] == ['git', 'commits']:
            return self.commits[r[2]]
        if metodo == 'POST' and r == ['git', 'blobs']:
            self.contador += 1000
            sha = f'blob-{self.contador}'
            return {'sha': sha}
        if metodo == 'POST' and r == ['git', 'trees']:
            self.contador += 1000
            sha = f'tree-{self.contador}'
            self.arvores[sha] = {'sha': sha}
            for no in corpo['tree']:
                self.arquivos[no['path']] = b'conteudo-novo'
            return {'sha': sha}
        if metodo == 'POST' and r == ['git', 'commits']:
            self.contador += 1000
            sha = f'commit-{self.contador}'
            self.commits[sha] = {'sha': sha, 'tree': {'sha': corpo['tree']}}
            self.commits_criados.append(corpo)
            return {'sha': sha}
        if metodo == 'PATCH' and r[:2] == ['git', 'refs']:
            self.refs[r[3]] = corpo['sha']
            return {'object': {'sha': corpo['sha']}}
        if metodo == 'GET' and r[:1] == ['releases'] and r[1] == 'tags':
            if corpo is None and r[2] not in self.releases:
                from worker.sincronizacao_github import ErroGitHub
                raise ErroGitHub(f'GitHub GET {url}: HTTP 404: not found')
            return self.releases[r[2]]
        if metodo == 'POST' and r == ['releases']:
            self.releases[corpo['tag_name']] = {
                'id': 111, 'html_url': f'https://github.com/x/releases/tags/{corpo["tag_name"]}',
                'assets': [], **{k: v for k, v in corpo.items() if k in ('tag_name', 'body')},
            }
            return self.releases[corpo['tag_name']]
        if metodo == 'PATCH' and r[0] == 'releases':
            self.releases[self._tag_por_id(r[1])]['body'] = corpo['body']
            return self.releases[self._tag_por_id(r[1])]
        if metodo == 'DELETE' and r[0] == 'releases' and r[1] == 'assets':
            self.assets_apagados.append(r[2])
            return None
        if metodo == 'POST' and r[0] == 'releases' and r[2] == 'assets':
            release = self.releases[self._tag_por_id(r[1])]
            release.setdefault('assets', []).append({'id': 222, 'name': url.split('name=')[1]})
            return {'id': 222}
        raise AssertionError(f'Endpoint não simulado: {metodo} {url}')

    def _tag_por_id(self, identificador: str) -> str:
        for tag, release in self.releases.items():
            if str(release['id']) == identificador:
                return tag
        raise AssertionError(f'Release {identificador} inexistente')


def instalar(monkeypatch, falso: GitHubFalso) -> None:
    import worker.sincronizacao_github as sinc

    monkeypatch.setenv('GITHUB_TOKEN', 'token-teste')
    monkeypatch.setattr(sinc, '_pedido', falso.rotear)


def test_baixar_dados(monkeypatch, tmp_path):
    falso = GitHubFalso({'livros_json/640_Filemom.json': b'{"book_number": 640}'})
    instalar(monkeypatch, falso)
    from worker.sincronizacao_github import baixar_dados

    destino = tmp_path / 'dados'
    baixados = baixar_dados('martinhossmadureiraministries/traducao-epignosis', 'bee-dados', destino)
    assert baixados == ['640_Filemom.json']
    assert (destino / '640_Filemom.json').read_bytes() == b'{"book_number": 640}'


def test_commit_arquivos_um_commit_so(monkeypatch, tmp_path):
    falso = GitHubFalso()
    instalar(monkeypatch, falso)
    from worker.sincronizacao_github import commit_arquivos

    sha = commit_arquivos(
        'martinhossmadureiraministries/traducao-epignosis', 'bee-dados',
        {'livros_json/640_Filemom.json': b'{}', 'entregas/BEE.SQLite3': b'x'},
        'BEE: teste',
    )
    assert sha.startswith('commit-')
    assert len(falso.commits_criados) == 1
    assert falso.refs['bee-dados'] == sha


def test_publicar_modulos_e_release(monkeypatch, tmp_path):
    falso = GitHubFalso()
    instalar(monkeypatch, falso)
    from worker.sincronizacao_github import publicar_release

    zip_path = tmp_path / 'BEE-modulos.zip'
    zip_path.write_bytes(b'PK\x03\x04')
    url = publicar_release(
        'martinhossmadureiraministries/traducao-epignosis', zip_path, 'prévia'
    )
    assert url.endswith('tags/bee-previa')
    url2 = publicar_release(
        'martinhossmadureiraministries/traducao-epignosis', zip_path, 'prévia 2'
    )
    assert url2 == url
    assert falso.releases['bee-previa']['body'] == 'prévia 2'
    assert falso.assets_apagados == ['222']


def test_sem_token_falha_clara(monkeypatch, tmp_path):
    import worker.sincronizacao_github as sinc
    from worker.sincronizacao_github import ErroGitHub

    monkeypatch.delenv('GITHUB_TOKEN', raising=False)
    with pytest.raises(ErroGitHub, match='GITHUB_TOKEN'):
        sinc.baixar_dados('r/x', 'bee-dados', tmp_path)
