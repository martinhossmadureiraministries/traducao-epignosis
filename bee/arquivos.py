"""Leitura validada e checkpoints atômicos, próprios para revisão no GitHub."""
from __future__ import annotations

import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
import tempfile
from typing import Any

from .catalogo import Livro, POR_NUMERO


class DadosInvalidos(ValueError):
    """Um ficheiro ou resposta precisa ser corrigido antes de prosseguir."""


def _sem_chaves_repetidas(pares: list[tuple[str, Any]]) -> dict[str, Any]:
    resultado: dict[str, Any] = {}
    for chave, valor in pares:
        if chave in resultado:
            raise DadosInvalidos(f'Chave JSON repetida: {chave!r}.')
        resultado[chave] = valor
    return resultado


def _constante_invalida(valor: str) -> None:
    raise DadosInvalidos(f'Constante JSON não permitida: {valor}.')


def carregar_json(texto: str) -> Any:
    try:
        return json.loads(texto, object_pairs_hook=_sem_chaves_repetidas, parse_constant=_constante_invalida)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise DadosInvalidos(f'JSON inválido: {exc}') from exc


class _HTMLSeguro(HTMLParser):
    def __init__(self, permitidas: set[str]):
        super().__init__(convert_charrefs=True)
        self.permitidas = permitidas
        self.pilha: list[str] = []
        self.texto: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.permitidas or attrs:
            raise DadosInvalidos(f'Tag HTML ou atributo não permitido: <{tag}>.')
        if tag != 'br':
            self.pilha.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag != 'br' or tag not in self.permitidas or attrs:
            raise DadosInvalidos(f'Tag HTML não permitida: <{tag}/>.')

    def handle_endtag(self, tag: str) -> None:
        if tag == 'br' or not self.pilha or self.pilha[-1] != tag:
            raise DadosInvalidos(f'Tag HTML mal fechada: </{tag}>.')
        self.pilha.pop()

    def handle_data(self, data: str) -> None:
        self.texto.append(data)

    def handle_comment(self, data: str) -> None:
        raise DadosInvalidos('Comentários HTML não são permitidos.')

    def handle_decl(self, decl: str) -> None:
        raise DadosInvalidos('Declarações HTML não são permitidas.')

    def unknown_decl(self, data: str) -> None:
        raise DadosInvalidos('Declarações HTML não são permitidas.')

    def handle_pi(self, data: str) -> None:
        raise DadosInvalidos('Instruções de processamento HTML não são permitidas.')


def validar_html(valor: Any, campo: str, comentario: bool = False) -> None:
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidos(f'{campo} deve ser texto não vazio.')
    permitidas = {'i'} if not comentario else {
        'p', 'br', 'b', 'strong', 'i', 'em', 'ul', 'ol', 'li', 'sup', 'sub'
    }
    parser = _HTMLSeguro(permitidas)
    try:
        parser.feed(valor)
        parser.close()
    except (ValueError, AssertionError) as exc:
        if isinstance(exc, DadosInvalidos):
            raise
        raise DadosInvalidos(f'HTML inválido em {campo}: {exc}') from exc
    if parser.pilha:
        raise DadosInvalidos(f'Tag HTML não fechada em {campo}: <{parser.pilha[-1]}>.')
    if not ''.join(parser.texto).strip():
        raise DadosInvalidos(f'{campo} não pode conter apenas marcação.')


def validar_colchetes_variantes(valor: str, campo: str) -> None:
    """Verifica a forma dos marcadores, não a existência ou a evidência da variante.

    Cada versículo é fechado independentemente, inclusive em passagens que
    atravessam capítulos; o comentário identifica a leitura e a fonte utilizadas.
    """
    inicio: int | None = None
    for sinal in re.finditer(r'\[\[|\]\]', valor):
        if sinal.group() == '[[':
            if inicio is not None:
                raise DadosInvalidos(f'{campo}: marcadores de variante aninhados.')
            inicio = sinal.end()
        else:
            if inicio is None:
                raise DadosInvalidos(f'{campo}: fechamento de variante sem abertura.')
            conteudo = re.sub(r'<[^>]*>', '', valor[inicio:sinal.start()]).strip()
            if not conteudo:
                raise DadosInvalidos(f'{campo}: trecho de variante vazio.')
            inicio = None
    if inicio is not None:
        raise DadosInvalidos(f'{campo}: marcador de variante sem fechamento.')


def validar_versiculos(versiculos: Any, esperados: range, contexto: str) -> None:
    if not isinstance(versiculos, list):
        raise DadosInvalidos(f'{contexto}: esperava uma lista de versículos.')
    numeros = list(esperados)
    if len(versiculos) != len(numeros):
        raise DadosInvalidos(
            f'{contexto}: esperados {len(numeros)} versículos; encontrados {len(versiculos)}.'
        )
    for item, numero in zip(versiculos, numeros):
        if not isinstance(item, dict):
            raise DadosInvalidos(f'{contexto}: versículo {numero} deve ser um objeto.')
        n = item.get('verse')
        if type(n) is not int or n != numero:
            raise DadosInvalidos(f'{contexto}: esperava o versículo {numero}, recebi {n!r}.')
        try:
            validar_html(item.get('text'), f'text de {contexto}:{numero}')
            validar_colchetes_variantes(item['text'], f'text de {contexto}:{numero}')
            validar_html(item.get('commentary'), f'commentary de {contexto}:{numero}', True)
        except DadosInvalidos as exc:
            raise DadosInvalidos(f'{contexto}:{numero}: {exc}') from exc


def novo_livro(livro: Livro) -> dict[str, Any]:
    return {
        'format_version': 1,
        'book_number': livro.numero,
        'book_name': livro.nome,
        'chapter_count': livro.capitulos,
        'chapters': {},
        'in_progress': {},
        'history': [],
    }


def _validar_revisao(revisao: Any, livro: Livro) -> None:
    """Valida trechos declarados sem inferir que qualquer texto foi aprovado."""
    if not isinstance(revisao, dict):
        raise DadosInvalidos(f'{livro.nome}: review deve ser um objeto.')
    editoriais = revisao.get('editorial_blocks', [])
    especialistas = revisao.get('specialist', [])
    if not isinstance(editoriais, list):
        raise DadosInvalidos(f'{livro.nome}: editorial_blocks deve ser uma lista.')
    if isinstance(especialistas, dict):
        especialistas = [especialistas]
    if not isinstance(especialistas, list):
        raise DadosInvalidos(f'{livro.nome}: specialist deve ser um objeto ou uma lista.')
    for nome, blocos in (('editorial_blocks', editoriais), ('specialist', especialistas)):
        intervalos: dict[int, list[tuple[int, int]]] = {}
        for bloco in blocos:
            if not isinstance(bloco, dict):
                raise DadosInvalidos(f'{livro.nome}: bloco de {nome} deve ser um objeto.')
            capitulo, inicio, fim = (bloco.get(k) for k in ('chapter', 'verse_from', 'verse_to'))
            if any(type(valor) is not int for valor in (capitulo, inicio, fim)):
                raise DadosInvalidos(f'{livro.nome}: limites de {nome} devem ser inteiros.')
            if not 1 <= capitulo <= livro.capitulos or not 1 <= inicio <= fim <= livro.versos_por_capitulo[capitulo - 1]:
                raise DadosInvalidos(f'{livro.nome}: intervalo de {nome} fora dos limites.')
            if not isinstance(bloco.get('status'), str) or not bloco['status'].strip():
                raise DadosInvalidos(f'{livro.nome}: bloco de {nome} precisa de status não vazio.')
            intervalos.setdefault(capitulo, []).append((inicio, fim))
        for trechos in intervalos.values():
            trechos.sort()
            if any(a[1] >= b[0] for a, b in zip(trechos, trechos[1:])):
                raise DadosInvalidos(f'{livro.nome}: blocos de {nome} sobrepostos.')


def validar_livro(dados: Any, livro: Livro) -> None:
    if not isinstance(dados, dict):
        raise DadosInvalidos(f'{livro.nome}: o ficheiro deve conter um objeto JSON.')
    if type(dados.get('format_version')) is not int or dados['format_version'] != 1:
        raise DadosInvalidos(f'{livro.nome}: format_version deve ser 1.')
    if type(dados.get('book_number')) is not int or dados['book_number'] != livro.numero:
        raise DadosInvalidos(f'{livro.nome}: book_number inconsistente.')
    if type(dados.get('chapter_count')) is not int or dados['chapter_count'] != livro.capitulos:
        raise DadosInvalidos(f'{livro.nome}: chapter_count deve ser {livro.capitulos}.')
    if not isinstance(dados.get('book_name'), str) or not dados['book_name'].strip():
        raise DadosInvalidos(f'{livro.nome}: book_name ausente ou inválido.')
    completos = dados.get('chapters')
    parciais = dados.get('in_progress', {})
    if not isinstance(completos, dict) or not isinstance(parciais, dict):
        raise DadosInvalidos(f'{livro.nome}: chapters e in_progress devem ser objetos.')
    if 'history' in dados and not isinstance(dados['history'], list):
        raise DadosInvalidos(f'{livro.nome}: history deve ser uma lista.')
    if 'review' in dados:
        _validar_revisao(dados['review'], livro)
    if 'bibliography' in dados:
        bibliografia = dados['bibliography']
        if not isinstance(bibliografia, list):
            raise DadosInvalidos(f'{livro.nome}: bibliography deve ser uma lista.')
        for fonte in bibliografia:
            if not isinstance(fonte, dict) or not isinstance(fonte.get('name'), str) or not fonte['name'].strip():
                raise DadosInvalidos(f'{livro.nome}: cada referência precisa de um nome.')
            for campo in ('revision', 'url', 'text_url', 'apparatus_url', 'license', 'attribution'):
                if campo in fonte and (not isinstance(fonte[campo], str) or not fonte[campo].strip()):
                    raise DadosInvalidos(f'{livro.nome}: {campo} da referência deve ser texto não vazio.')
            if 'urls' in fonte and (
                not isinstance(fonte['urls'], list)
                or any(not isinstance(url, str) or not url.strip() for url in fonte['urls'])
            ):
                raise DadosInvalidos(f'{livro.nome}: urls da referência deve ser uma lista de textos não vazios.')
    for colecao, parcial in ((completos, False), (parciais, True)):
        for chave, versiculos in colecao.items():
            if not isinstance(chave, str) or not chave.isascii() or not chave.isdecimal():
                raise DadosInvalidos(f'{livro.nome}: capítulo inválido {chave!r}.')
            capitulo = int(chave)
            if chave != str(capitulo) or not 1 <= capitulo <= livro.capitulos:
                raise DadosInvalidos(f'{livro.nome}: capítulo fora do intervalo: {chave!r}.')
            if parcial and chave in completos:
                raise DadosInvalidos(f'{livro.nome} {chave}: capítulo completo e parcial ao mesmo tempo.')
            total = livro.versos_por_capitulo[capitulo - 1]
            if parcial:
                if not isinstance(versiculos, list) or not 0 < len(versiculos) < total:
                    raise DadosInvalidos(f'{livro.nome} {chave}: progresso parcial inválido.')
                fim = len(versiculos)
            else:
                fim = total
            validar_versiculos(versiculos, range(1, fim + 1), f'{livro.nome} {chave}')


def ler_livro(caminho: Path, livro: Livro) -> dict[str, Any]:
    if not caminho.exists():
        return novo_livro(livro)
    try:
        dados = carregar_json(caminho.read_text(encoding='utf-8'))
        validar_livro(dados, livro)
        return dados
    except (OSError, UnicodeError, DadosInvalidos) as exc:
        raise DadosInvalidos(f'{caminho}: {exc}') from exc


def ler_todos(diretorio: Path) -> dict[int, dict[str, Any]]:
    livros: dict[int, dict[str, Any]] = {}
    origens: dict[int, Path] = {}
    if not diretorio.exists():
        return livros
    if not diretorio.is_dir():
        raise DadosInvalidos(f'{diretorio} não é uma pasta.')
    for caminho in sorted(diretorio.glob('*.json')):
        try:
            dados = carregar_json(caminho.read_text(encoding='utf-8'))
            numero = dados.get('book_number') if isinstance(dados, dict) else None
            if type(numero) is not int or numero not in POR_NUMERO:
                raise DadosInvalidos(f'book_number desconhecido: {numero!r}.')
            if numero in livros:
                raise DadosInvalidos(f'livro {numero} duplicado em {origens[numero]} e {caminho}.')
            validar_livro(dados, POR_NUMERO[numero])
            livros[numero] = dados
            origens[numero] = caminho
        except (OSError, UnicodeError, DadosInvalidos) as exc:
            raise DadosInvalidos(f'{caminho}: {exc}') from exc
    return livros


def salvar_livro(caminho: Path, dados: dict[str, Any], livro: Livro) -> None:
    validar_livro(dados, livro)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(prefix=f'.{caminho.name}.', suffix='.bee-tmp', dir=caminho.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as arquivo:
            json.dump(dados, arquivo, ensure_ascii=False, indent=2, allow_nan=False)
            arquivo.write('\n')
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        try:
            os.unlink(temporario)
        except FileNotFoundError:
            pass
