"""Leitura validada e checkpoints atômicos, próprios para revisão no GitHub."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
import tempfile
from typing import Any

from . import sanea
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


def _fechar_json(texto: str) -> str:
    """Fecha aspas, chaves e parênteses que o modelo deixou abertos."""
    em_texto = False
    escape = False
    pilha: list[str] = []
    for caracter in texto:
        if em_texto:
            if escape:
                escape = False
            elif caracter == '\\':
                escape = True
            elif caracter == '"':
                em_texto = False
            continue
        if caracter == '"':
            em_texto = True
        elif caracter in '{[':
            pilha.append('}' if caracter == '{' else ']')
        elif caracter in '}]' and pilha:
            pilha.pop()
    partes = [texto]
    if em_texto:
        partes.append('"')
    partes.append(''.join(reversed(pilha)))
    return ''.join(partes)


def _corte_valido(texto: str) -> Any:
    """Recupera os elementos completos de uma resposta cortada no fim.

    Tenta fechar o JSON tal como está; se o último objecto ficou a meio (sem
    `text` ou `commentary`), recua até ao último `}` e tenta de novo. Assim
    recuperam-se os versículos inteiros e descarta-se só o que ficou cortado.
    """
    candidatos = [_fechar_json(texto)]
    for posicao in range(len(texto) - 1, max(len(texto) - 4000, 0), -1):
        if texto[posicao] == '}':
            candidatos.append(_fechar_json(texto[:posicao + 1]))
    for candidato in candidatos:
        try:
            raiz = json.loads(
                candidato,
                object_pairs_hook=_sem_chaves_repetidas,
                parse_constant=_constante_invalida,
            )
        except (json.JSONDecodeError, UnicodeError):
            continue
        if isinstance(raiz, dict) and isinstance(raiz.get('verses'), list) and raiz['verses']:
            completos = [
                v for v in raiz['verses']
                if isinstance(v, dict) and v.get('text')
                and ('commentary' not in v or v.get('commentary'))
            ]
            if completos:
                raiz['verses'] = completos
                return raiz
    return None


def carregar_json(texto: str) -> Any:
    try:
        return json.loads(texto, object_pairs_hook=_sem_chaves_repetidas, parse_constant=_constante_invalida)
    except (json.JSONDecodeError, UnicodeError) as exc:
        # Uma resposta cortada no fim ainda contém versículos completos: em
        # 17/11 o Gemini cortou um lote a meio de uma chave e o ciclo morreu,
        # deitando fora 10 capítulos já gerados nessa execução.
        recuperado = _corte_valido(texto.strip())
        if recuperado is not None:
            return recuperado
        # A corrupção também surge a meio (aspas sem escape, vírgula em falta):
        # em 17/11 o João 18:1-10 falhou 3 vezes seguidas assim e cada tentativa
        # perdeu a resposta inteira. O erro indica o primeiro caractere
        # impossível de interpretar; os versículos anteriores a esse ponto
        # continuam válidos e podem ser guardados.
        if isinstance(exc, json.JSONDecodeError) and exc.pos:
            recuperado = _corte_valido(texto[:exc.pos].strip())
            if recuperado is not None:
                return recuperado
        raise DadosInvalidos(f'JSON inválido: {exc}') from exc


def validar_html(valor: Any, campo: str, comentario: bool = False) -> None:
    """Aceita HTML simples e tolera contentores neutros (`<div>`).

    Antes, um `<div>` a envolver os parágrafos fazia a **resposta inteira** ser
    rejeitada: o lote era dividido até 1 versículo e, com o serviço instável, a
    produção parava por causa de uma tag sem significado. `<div>`, `<span>` e
    afins passam a ser aceites e convertidos em `<p>` ao guardar. As regras de
    segurança mantêm-se: scripts, iframes, comentários, atributos e tags
    desconhecidas continuam a ser recusados nesta porta.
    """
    if not isinstance(valor, str) or not valor.strip():
        raise DadosInvalidos(f'{campo} deve ser texto não vazio.')
    try:
        limpo = sanea.limpar(valor, comentario, estrito=True)
    except sanea.ErroHTML as exc:
        raise DadosInvalidos(str(exc)) from exc
    if not re.sub(r'<[^>]*>', '', limpo).strip():
        raise DadosInvalidos(f'{campo} não pode conter apenas marcação.')


def sanear_html(valor: Any, comentario: bool = False) -> Any:
    """Devolve o HTML limpo (usada antes de guardar um lote)."""
    if not isinstance(valor, str):
        return valor
    try:
        return sanea.limpar(valor, comentario)
    except sanea.ErroHTML:
        return valor


def validar_colchetes_variantes(valor: str, campo: str) -> None:
    """Colchetes simples: `[ ]` para variante ou evidência de manuscritos.

    Convenção (2026-11-24): só colchetes simples, nunca `[[ ]]`. Verifica-se a
    forma, não a existência nem a evidência da variante; a evidência fica na nota.
    """
    if '[[' in valor or ']]' in valor:
        raise DadosInvalidos(f'{campo}: use colchetes simples, não duplos.')
    if valor.count('[') != valor.count(']'):
        raise DadosInvalidos(f'{campo}: colchetes desequilibrados.')


_RE_ACRESCIMO = re.compile(r'<i[\s>]')


def exige_nota(texto: Any) -> str | None:
    """Motivo pelo qual o versículo tem de ter nota, ou `None` se a nota é opcional.

    Regra (decisão de 2026-11-24): a nota é opcional. Fica obrigatória onde há
    algo a explicar e que a máquina consegue ver no texto: um acréscimo em
    itálico (palavra sem correspondência no grego) ou colchetes simples (variante
    ou evidência de manuscritos). A variante do aparato da SBLGNT sem nota é
    apanhada pelo `verificar_notas_colacao` (variante sem Crítica Textual). Os
    marcadores de produção (`[Versículo …`) não são texto e não pedem nota.
    """
    if not isinstance(texto, str) or texto.startswith('[Versículo'):
        return None
    if _RE_ACRESCIMO.search(texto):
        return 'o texto tem um acréscimo em itálico'
    if '[' in texto:
        return 'o texto tem colchetes (variante ou evidência de manuscritos)'
    return None


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
            if 'commentary' in item:
                # Chave presente: tem de ser nota não vazia. Chave ausente: versículo sem nota.
                validar_html(item.get('commentary'), f'commentary de {contexto}:{numero}', True)
            else:
                motivo = exige_nota(item.get('text'))
                if motivo:
                    raise DadosInvalidos(f'sem nota, porque {motivo}.')
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
