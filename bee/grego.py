"""Convenção do grego nas notas: itálico (decisão D7 do plano de correção).

Cada palavra grega fora de explicação em itálico recebe <i>…</i>. A função só
mexe nas marcas <i>: o conteúdo das notas tem de ficar igual, o que se verifica
por `sem_marcas_i(antes) == sem_marcas_i(depois)`.

Não se aplica ao texto dos versículos (não tem grego) nem a rótulos <b>.
Transliterações latinas, como «(epýthleto)», não são grego e não são tocadas.
"""
from __future__ import annotations

import re

# Letras gregas (incluindo tónicos e espíritos), marcas combinadas, apóstrofo
# elidido (ʼ) e os sinais gregos ; e ·, que fazem parte da palavra.
_LETRA = r'[\u0370-\u03ff\u1f00-\u1fff\u0300-\u036f\u0345\u02bc]'
_RE_GREGO = re.compile(rf'{_LETRA}(?:(?:{_LETRA}|[ \u00a0])*{_LETRA})?')
_RE_ITALICO = re.compile(r'<i>.*?</i>', re.S)
_RE_TAG = re.compile(r'<[^>]+>')


def _segmentos_fora_de_italico(texto: str):
    """Pares (é_italico, pedaço) que cobrem o texto inteiro."""
    pos = 0
    for m in _RE_ITALICO.finditer(texto):
        if m.start() > pos:
            yield False, texto[pos:m.start()]
        yield True, m.group(0)
        pos = m.end()
    if pos < len(texto):
        yield False, texto[pos:]


def italico_grego(texto: str) -> str:
    """Devolve o texto com o grego fora de <i> posto em itálico."""
    if not texto:
        return texto
    saida = []
    for italico, pedaco in _segmentos_fora_de_italico(texto):
        if italico:
            saida.append(pedaco)
            continue
        # Não se toca no interior de etiquetas (<b>, <p>, …).
        partes = _RE_TAG.split(pedaco)
        marcas = _RE_TAG.findall(pedaco)
        for i, parte in enumerate(partes):
            saida.append(_RE_GREGO.sub(lambda m: f'<i>{m.group(0)}</i>', parte))
            if i < len(marcas):
                saida.append(marcas[i])
    return ''.join(saida)


def grego_fora_de_italico(texto: str) -> list[str]:
    """Pedaços de grego que não estão em itálico (para o verificador)."""
    achados = []
    for italico, pedaco in _segmentos_fora_de_italico(texto or ''):
        if italico:
            continue
        for parte in _RE_TAG.split(pedaco):
            for m in _RE_GREGO.finditer(parte):
                achados.append(m.group(0).strip(' \u00a0'))
    return [a for a in achados if a]


def sem_marcas_i(texto: str) -> str:
    """O texto sem <i> e </i>; serve para provar que só as marcas mudaram."""
    return re.sub(r'</?i>', '', texto or '')
