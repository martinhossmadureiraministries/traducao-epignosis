"""Porta obrigatória da voz BEE (P1 da convergência multi-provedor).

Dois serviços, ambos determinísticos e sem rede:

* ``inspecionar_versos`` — o ``Rodizio`` chama-o sobre cada lote ANTES de o
  devolver ao gerador. Falhas duras (arcaísmos/hesitação) levantam
  ``DerivaEstilo`` dentro do rodízio, que roda automaticamente para outro
  provedor no mesmo lote: o texto mau nunca chega a ser guardado, e quem o
  escreveu não volta a escrevê-lo se outro provedor estiver disponível.

* ``exclusoes_de_estilo`` — lê ``.bee/quarentena.json`` e devolve, por
  (livro, capítulo), os provedores cujo texto já foi chumbado. O agendador
  passa isto ao rodízio como filtro: a repetição de um capítulo chumbado faz-se
  com provedores diferentes. A disponibilidade vem sempre primeiro — se o
  filtro excluir todos os motores, ignora-se nesse pedido (ver ``Rodizio``).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .inspetor import analisar_texto


def inspecionar_versos(versiculos: list[dict[str, Any]]) -> dict[int, list[str]]:
    """Devolve {número do versículo: [falhas duras]} só para os versos chumbados.

    Resultado vazio = lote limpo de falhas duras. Os avisos (marcadores de
    Almeida) NÃO chumbam na porta: são sinal para revisão, tal como na CLI,
    para não travar a produção por léxico discutível.
    """
    chumbados: dict[int, list[str]] = {}
    for verso in versiculos:
        resultado = analisar_texto(str(verso.get('text', '')))
        if resultado['duros']:
            try:
                numero = int(verso.get('verse', 0))
            except (TypeError, ValueError):
                numero = 0
            chumbados[numero] = resultado['duros']
    return chumbados


def resumo_marcas(marcas: dict[int, list[str]]) -> str:
    """Texto curto para diários/motivos: «vv. 2-3: vós; vv. 7: ou seja»."""
    if not marcas:
        return 'sem marcas'
    partes: list[str] = []
    for numero in sorted(marcas):
        partes.append(f'v.{numero}: ' + ', '.join(marcas[numero]))
    return '; '.join(partes)


def exclusoes_de_estilo(quarentena: Path) -> dict[tuple[int, int], set[str]]:
    """Provedores a evitar por (book_number, capítulo), vindos da quarentena.

    Só contam entradas com ``status == 'chumbado-estilo'`` e provedor
    identificado. Ficheiros ausentes/ilegíveis devolvem mapa vazio: uma memória
    de deriva corrompida nunca pode impedir a produção.
    """
    if not quarentena.exists():
        return {}
    try:
        lido = json.loads(quarentena.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return {}
    entradas = lido.get('entries') if isinstance(lido, dict) else None
    if not isinstance(entradas, list):
        return {}
    mapa: dict[tuple[int, int], set[str]] = {}
    for entrada in entradas:
        if not isinstance(entrada, dict) or entrada.get('status') != 'chumbado-estilo':
            continue
        livro, capitulo = entrada.get('book'), entrada.get('chapter')
        if not isinstance(livro, int) or not isinstance(capitulo, int):
            continue
        autores = {str(a) for a in entrada.get('providers_tried') or [] if a}
        if entrada.get('provider'):
            autores.add(str(entrada['provider']))
        if autores:
            mapa.setdefault((livro, capitulo), set()).update(autores)
    return mapa
