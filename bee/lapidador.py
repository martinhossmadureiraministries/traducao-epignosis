"""Lapidação automática determinística — a parte mecânica da oficina.

Os scripts ``scripts/lapidar_*.py`` lapidaram à mão, livro a livro, o que
a produção na nuvem tinha derivado. Este módulo extrai a parte MECÂNICA
dessa lapidação para correr sozinha sempre que um capítulo fecha
(``bee/agenda.py`` chama-o antes da revisão por segunda IA):

1. títulos das três secções postos no formato da casa
   («<b>Análise Léxica:</b>»), aspas curvas viradas «», entidades HTML
   («&#x27;») e hífenes não-quebráveis normalizados, «[[ ]]» retirados;
2. secções que não são as três da casa (nem «Nota de redação») removidas;
3. Crítica Textual REGENERADA do aparato da SBLGNT e do relatório de
   colação do livro (quando existe em ``docs/colacao/``), com o nível
   de certeza da casa — a nota deixa de poder inventar variantes,
   testemunhas ou certezas, porque o texto é gerado da evidência;
4. ponto fora das aspas no texto («beber». → «beber.») corrigido;
5. palavras greco-latinas mistas («ἄνδra») detetadas e REPORTADAS —
   não são corrigidas à máquina, porque a correção exige juízo;
6. siglas de manuscritos citadas sem testemunha na colação do
   versículo reportadas (o apoio inventado não passa em silêncio), e
   o grego da nota fora da base agregado como alerta de amostragem.

O que este módulo NÃO faz, de propósito: mudar escolhas de tradução,
reescrever prosa ou corrigir erros de sentido. Isso continua a ser do
revisor (segunda IA, de outro provedor) e da amostragem humana. A
lapidação automática trata da forma; o sentido tem outra camada.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any

SECCOES_CASA = ('Análise Léxica', 'Crítica Textual', 'Síntese Exegética')
SECCOES_PERMITIDAS = SECCOES_CASA + ('Nota de redação',)

_CABECALHO_FORA = re.compile(
    r'<b>(Análise Léxica|Crítica Textual|Síntese Exegética)</b>\s*'
    r'(?:—|-|:)?\s*')
_PARAGRAFO = re.compile(r'<p><b>([^<]+):</b>.*?</p>', re.S)
_MISTO = re.compile(r'[Ͱ-Ͽἀ-῿]')
_PONTO_FORA = re.compile(r'»([.?!])')

_SIGLAS = {'WH', 'Treg', 'NA28', 'RP', 'NIV'}


def tokens_mistos(texto: str) -> list[str]:
    """Palavras com letras gregas E latinas misturadas («ἄνδra»)."""
    limpo = re.sub(r'<[^>]+>', ' ', texto or '')
    return [tok for tok in limpo.split()
            if _MISTO.search(tok) and re.search(r'[A-Za-z]', tok)]


def normalizar_nota(nota: str) -> str:
    """Forma da casa: cabeçalhos, aspas, hífenes, sem «[[ ]]» nem entidades."""
    nota = _CABECALHO_FORA.sub(r'<b>\1:</b> ', nota or '')
    nota = nota.replace('\u2011', '-')
    nota = nota.replace('&#x27;', 'ʼ').replace('&#39;', 'ʼ')
    nota = nota.replace('[[', '').replace(']]', '')
    estado = {'aberta': False}

    def aspas(_: re.Match[str]) -> str:
        estado['aberta'] = not estado['aberta']
        return '«' if estado['aberta'] else '»'

    return re.sub(r'&quot;|[“”]', aspas, nota)


def secoes(nota: str) -> list[tuple[str, str]]:
    """[(rótulo, parágrafo completo)] na ordem em que aparecem."""
    return [(m.group(1), m.group(0)) for m in _PARAGRAFO.finditer(nota or '')]


def _dividir_apoio(parte: str) -> tuple[str, list[str]]:
    """'ἀδελφῇ WH Treg NA28' -> ('ἀδελφῇ', ['WH','Treg','NA28'])."""
    tokens = parte.strip().split()
    apoio: list[str] = []
    while tokens and tokens[-1] in _SIGLAS:
        apoio.insert(0, tokens.pop())
    return ' '.join(tokens), apoio


def _render_apoio(siglas: list[str]) -> str:
    nomes = {'Treg': 'Tregelles'}
    return ', '.join(nomes.get(s, s) for s in siglas) or 'sem apoio nomeado'


def critica_textual(item_col: dict) -> str:
    """Crítica Textual gerada do aparato (edições) + nível de certeza.

    A fraseologia é a dos scripts de lapidação já provados (João 2–4):
    A quando a variante é só bizantina (RP) ou o aparato nada regista;
    B quando as edições críticas não são unânimes.
    """
    base = item_col['base']
    aparato = base.get('aparato_sblgnt') or []
    frases: list[str] = []
    if aparato:
        descricoes = []
        apoios_variantes: list[set[str]] = []
        for entrada in aparato:
            limpa = entrada.strip().lstrip('•').strip()
            limpa = re.sub(r'^[\d:–\-– ]+', '', limpa)
            if ']' not in limpa:
                continue
            esq, dir_ = limpa.split(']', 1)
            leitura_base, apoio_base = _dividir_apoio(esq)
            variantes = []
            for alt in dir_.split(';'):
                leitura_alt, apoio_alt = _dividir_apoio(alt)
                if leitura_alt in ('–', '-'):
                    leitura_alt = 'omissão desta leitura'
                elif leitura_alt.startswith('+'):
                    leitura_alt = 'acréscimo de ' + leitura_alt[1:].strip()
                variantes.append((leitura_alt, apoio_alt))
                apoios_variantes.append(set(apoio_alt))
            texto_var = '; '.join(
                f'«{l}» ({_render_apoio(a)})' for l, a in variantes)
            descricoes.append(
                f'«{leitura_base}» ({_render_apoio(apoio_base)}) '
                f'contra {texto_var}')
        frases.append(
            'O aparato da SBLGNT (que compara edições, não manuscritos) '
            'regista ' + '; '.join(descricoes) + '.')
        so_bizantina = all(a and a <= {'RP'} for a in apoios_variantes)
        if so_bizantina:
            nivel, razao = 'A', ('a variante é bizantina (RP) e as edições '
                                 'críticas apoiam a base')
        else:
            nivel, razao = 'B', 'as edições críticas não são unânimes'
        frases.append(
            f'O texto segue a base (nível de certeza {nivel}: {razao}).')
    else:
        igual_tr = base.get('sblgnt_norm') == base.get('scrivener_norm')
        frases.append(
            'Sem unidade de variação adotada por qualquer edição: o '
            'aparato da SBLGNT nada regista neste versículo. Nas '
            'testemunhas colacionadas (CNTR) as divergências são de '
            'ortografia, abreviaturas de nomes sagrados, ordem de palavras '
            'ou leituras que nenhuma edição imprime (relatório de colação '
            'do livro).')
        if igual_tr:
            frases.append('O Textus Receptus de Scrivener lê o mesmo texto.')
        else:
            frases.append(
                'O Textus Receptus de Scrivener diverge da base neste '
                'versículo; a divergência está registada no mesmo relatório.')
        frases.append(
            'O texto segue a base (nível de certeza A: o aparato não '
            'regista variante neste versículo).')
    return '<p><b>Crítica Textual:</b> ' + ' '.join(frases) + '</p>'


_SIGLA_MS = re.compile(r'\bP\d{1,3}\b|\b0\d{1,2}\b|\b0\d{3}\b')


def siglas_sem_evidencia(nota: str, item_col: dict) -> list[str]:
    """Siglas de manuscritos citadas na nota sem testemunha na colação.

    A evidência é o registo do versículo no relatório de colação
    (``leituras``: sigla → leitura presente) mais as siglas do aparato
    da SBLGNT. Uma sigla citada que não está em nenhum dos dois é o
    apoio inventado que a produção real cometeu: sai como problema
    (alerta forte) para o diário e para quem lapidar à mão.
    """
    leituras = item_col.get('leituras') or {}
    evidencia = {
        sigla for sigla, leitura in leituras.items()
        if leitura and (not isinstance(leitura, dict)
                        or leitura.get('presente', True))
    }
    aparato = ' '.join((item_col.get('base') or {}).get('aparato_sblgnt')
                       or [])
    evidencia |= set(_SIGLA_MS.findall(aparato))
    limpo = re.sub(r'<[^>]+>', ' ', nota or '')
    citadas = set(_SIGLA_MS.findall(limpo))
    if 'א' in limpo:  # o Sinaítico também se cita pela letra hebraica
        citadas.add('01')
    return sorted(c for c in citadas if c not in evidencia)


def lapidar_versos(
    versos: list[dict[str, Any]],
    capitulo: int,
    colacao: dict | None,
) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    """Lapida os versículos de um capítulo. Devolve (versos, relatório, problemas).

    ``colacao`` é o relatório de ``docs/colacao/<Livro>.json`` já lido, ou
    None (sem ele, a Crítica Textual não é regenerada — só a forma é
    normalizada). Os versículos são copiados, nunca alterados no sítio.
    """
    saida: list[dict[str, Any]] = []
    relatorio: list[str] = []
    problemas: list[str] = []
    for original in versos:
        v = dict(original)
        vv = v.get('verse')
        ref = f'{capitulo}:{vv}'

        texto = _PONTO_FORA.sub(r'\1»', str(v.get('text', '')))
        texto = texto.replace('\u2011', '-')
        if texto != v.get('text'):
            relatorio.append(f'{ref}: pontuação/hífen do texto normalizados')
        v['text'] = texto

        nota = normalizar_nota(str(v.get('commentary', '')))
        partes = secoes(nota)
        rotulos = [r for r, _ in partes]
        for seccao in SECCOES_CASA:
            if seccao not in rotulos:
                problemas.append(f'{ref}: falta a secção «{seccao}»')
        # Siglas: verificam-se na nota TAL COMO FOI GERADA, antes de a
        # regeneração substituir a Crítica Textual — o apoio inventado
        # fica registado mesmo quando a CT regenerada o corrige.
        if colacao is not None:
            item_col = (colacao.get('versiculos') or {}).get(ref)
            if item_col is not None:
                for sigla in siglas_sem_evidencia(nota, item_col):
                    problemas.append(
                        f'{ref}: sigla {sigla} citada sem evidência na '
                        'colação deste versículo')
        mantidas: list[str] = []
        for rotulo, paragrafo in partes:
            if rotulo == 'Crítica Textual' and colacao is not None:
                # Uma CT que cita a colação (CNTR/relatório) ou já traz o
                # nível de certeza da casa é CURADA: pode ter factos
                # editoriais que a regeneração apagaria (em João 3:25, a
                # leitura de 01 e P66). Só se regenera a CT da máquina,
                # que não cita a colação. A lapidação é avessa à perda:
                # nunca destrói informação curada.
                curada = ('CNTR' in paragrafo or 'colação' in paragrafo
                          or 'nível de certeza' in paragrafo)
                if not curada:
                    item = (colacao.get('versiculos') or {}).get(ref)
                    if item is not None:
                        paragrafo = critica_textual(item)
            if rotulo in SECCOES_PERMITIDAS:
                mantidas.append(paragrafo)
            else:
                relatorio.append(f'{ref}: secção «{rotulo}» removida')
        if mantidas:
            nota = ''.join(mantidas)
        mistos = tokens_mistos(nota) + tokens_mistos(texto)
        if mistos:
            problemas.append(
                f'{ref}: palavra(s) greco-latina(s) mista(s): '
                + ', '.join(sorted(set(mistos))))
        if nota != v.get('commentary'):
            relatorio.append(f'{ref}: nota normalizada')
        v['commentary'] = nota
        saida.append(v)
    return saida, relatorio, problemas


def _sem_acentos(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if not unicodedata.combining(c)).casefold()


_GREGO = re.compile(r'[Ͱ-Ͽἀ-῿]+')


def gregos_fora_da_base(
    nota: str,
    base_grego: str,
    vocabulario: set[str] | frozenset[str] = frozenset(),
) -> list[str]:
    """Formas gregas da nota que não estão na base nem no vocabulário.

    Serve de ALERTA (lemas de léxico são formas de dicionário e podem não
    estar na base flexionada): quem lê decide se é erro ou lema legítimo.
    A comparação é sem acentos nem maiúsculas.
    """
    permitidos = {_sem_acentos(t) for t in _GREGO.findall(base_grego or '')}
    permitidos |= {_sem_acentos(t) for t in vocabulario}
    achados = []
    for tok in _GREGO.findall(re.sub(r'<[^>]+>', ' ', nota or '')):
        if _sem_acentos(tok) not in permitidos:
            achados.append(tok)
    return sorted(set(achados))


def alertas_grego(
    versos: list[dict[str, Any]],
    capitulo: int,
    colacao: dict | None,
) -> dict[str, list[str]]:
    """{referência: [formas]} do grego da nota fora da base do versículo.

    Agregado para o diário: é alerta para amostragem humana, não falha —
    os lemas de léxico citados nas notas são formas de dicionário.
    """
    if not colacao:
        return {}
    itens = colacao.get('versiculos') or {}
    saida: dict[str, list[str]] = {}
    for v in versos:
        ref = f'{capitulo}:{v.get("verse")}'
        item = itens.get(ref)
        if not item:
            continue
        base_txt = (item.get('base') or {}).get('sblgnt') or ''
        if not base_txt:
            continue
        achados = gregos_fora_da_base(str(v.get('commentary', '')), base_txt)
        if achados:
            saida[ref] = achados
    return saida
