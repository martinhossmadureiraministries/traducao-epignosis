"""Textos originais fixados por versão, cache e versificação tradicional.

As correspondências parciais do WLC são deliberadamente marcadas para revisão;
nenhum limite de palavra é inventado para uma referência que o mapa não divida.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import Any
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from .catalogo import LIVROS, Livro
from .rede import ClienteHTTP


class ErroFonte(RuntimeError):
    pass


MORPH_COMMIT = 'db6c5c9b46b8f39346f10915ddb1a70dcd429901'
SBL_COMMIT = 'd7f35adca9ec410e1d1499c63b4dd989d76c8d4d'
TR_COMMIT = '6049a43b135ed870f843b83eb6a04764fc796678'
# Incremente quando o alinhamento/extração mudar de modo a alterar trechos.
ALINHAMENTO_VERSAO = 1
FONTES = {
    'wlc': (
        f'wlc-{MORPH_COMMIT[:8]}.zip',
        f'https://codeload.github.com/openscriptures/morphhb/zip/{MORPH_COMMIT}',
        '607f76d5def08654c2ef59ac1d318794cec7fcf6c9f3c6c445adfc9d35467c8a',
        'application/zip',
    ),
    'sbl': (
        f'sblgnt-{SBL_COMMIT[:8]}.zip',
        f'https://codeload.github.com/Faithlife/SBLGNT/zip/{SBL_COMMIT}',
        'bcb9cfd8678a863be77c01641aab14c31515e7057852b5abfe0920aac73cbf56',
        'application/zip',
    ),
    'tr': (
        f'textus-receptus-scrivener-{TR_COMMIT[:8]}.zip',
        f'https://codeload.github.com/byztxt/greektext-scrivener/zip/{TR_COMMIT}',
        '41d290083e20be0863cf274517d0f4a02fab2ed503b08dd9e16a024d7ed341f5',
        'application/zip',
    ),
}

AUTORIA = (
    'Obra: Bíblia de Estudo Epignósis (BEE) — Projeto Epignósis. '
    'Autor: Martinho S. S. Madureira. '
    'Publicado por Martinho S. S. Madureira Ministries. '
    'Texto bíblico e comentários gerados por IA sob direcção editorial do autor, '
    'sujeitos a revisão humana antes de qualquer edição final. '
)

ATRIBUICAO = (
    'AT: Original work of the Open Scriptures Hebrew Bible available at '
    'https://github.com/openscriptures/morphhb (CC BY 4.0), baseado no WLC; '
    'NT: Scripture quotations marked SBLGNT are from the SBL Greek New Testament. '
    'Copyright © 2010 Society of Biblical Literature and Logos Bible Software '
    '(https://github.com/Faithlife/SBLGNT; CC BY 4.0: '
    'https://creativecommons.org/licenses/by/4.0/). '
    'Comparação/suplemento: Textus Receptus de Scrivener 1894, digitalização '
    'de Maurice A. Robinson (domínio público segundo o fornecedor: '
    'https://github.com/byztxt/greektext-scrivener); convertido de ASCII para '
    'grego Unicode sem acentos, espíritos ou pontuação. Adaptações de versificação; '
    'textos e comentários gerados por IA, sujeitos a revisão humana.'
)

# Os 18 versículos tradicionais efetivamente ausentes no SBLGNT fixado.
# Outras diferenças de numeração são tratadas explicitamente em _grego().
_AUSENTES_SBL = {
    ('Matt', 17, 21), ('Matt', 18, 11), ('Matt', 23, 14),
    ('Mark', 7, 16), ('Mark', 9, 44), ('Mark', 9, 46), ('Mark', 11, 26), ('Mark', 15, 28),
    ('Luke', 17, 36), ('Luke', 23, 17), ('John', 5, 4),
    ('Acts', 8, 37), ('Acts', 15, 34), ('Acts', 24, 7), ('Acts', 28, 29),
    ('Rom', 16, 25), ('Rom', 16, 26), ('Rom', 16, 27),
}
# Nomes de ficheiro na transcrição ASCII de Robinson e seu alfabeto próprio.
_TR_ARQUIVOS = dict(zip(
    (livro.osis for livro in LIVROS[39:]),
    ('MT', 'MR', 'LU', 'JOH', 'AC', 'RO', '1CO', '2CO', 'GA', 'EPH', 'PHP',
     'COL', '1TH', '2TH', '1TI', '2TI', 'TIT', 'PHM', 'HEB', 'JAS', '1PE',
     '2PE', '1JO', '2JO', '3JO', 'JUDE', 'RE'),
))
_TR_UNICODE = str.maketrans('abgdezhyiklmnxoprsvtufcqw', 'αβγδεζηθικλμνξοπρσςτυφχψω')

# Limites explicitamente conferidos contra a numeração tradicional KJV.
# (capítulo, primeiro de dois versículos, origem do texto a dividir, início
# da segunda parte). A origem é o primeiro ou o segundo dos dois versículos.
# Não silencie estas adaptações: mantenha as referências originais e um aviso.
_SBL_LIMITES = {
    'Mark': [(3, 19, 20, 'καὶ συνέρχεται'), (12, 14, 14, 'δῶμεν ἢ μὴ δῶμεν')],
    'Luke': [(6, 17, 18, 'καὶ οἱ ⸂ἐνοχλούμενοι'), (7, 18, 18, 'καὶ προσκαλεσάμενος'),
             (22, 66, 67, 'Εἰ σὺ εἶ')],
    'Acts': [(2, 10, 11, 'Κρῆτες'), (3, 19, 20, 'καὶ ἀποστείλῃ'),
             (5, 39, 39, 'ἐπείσθησαν δὲ αὐτῷ'), (13, 38, 38, 'καὶ ἀπὸ πάντων'),
             (24, 18, 19, 'οὓς ⸀ἔδει')],
    'Rom': [(7, 9, 10, 'καὶ εὑρέθη'), (9, 11, 12, 'ἐρρέθη αὐτῇ')],
    '2Cor': [(8, 13, 13, 'ἀλλʼ ἐξ ἰσότητος'), (10, 4, 4, 'λογισμοὺς καθαιροῦντες')],
    'Gal': [(2, 19, 19, 'Χριστῷ συνεσταύρωμαι')],
    'Eph': [(2, 14, 14, 'τὴν ἔχθραν'), (5, 13, 14, 'διὸ λέγει')],
    'Phil': [(2, 7, 7, 'καὶ σχήματι')],
    'Col': [(1, 21, 22, 'ἐν τῷ σώματι')],
    '1Thess': [(1, 2, 2, 'ἀδιαλείπτως'), (2, 6, 7, 'ἀλλὰ ἐγενήθημεν'),
               (2, 11, 12, 'εἰς τὸ ⸀περιπατεῖν')],
    'Heb': [(3, 9, 10, 'διὸ προσώχθισα'), (12, 22, 22, 'πανηγύρει')],
    '1Pet': [(3, 15, 16, 'συνείδησιν ἔχοντες')],
    '1John': [(2, 13, 14, 'ἔγραψα ὑμῖν, πατέρες')],
    'Rev': [(2, 27, 28, 'καὶ δώσω'), (17, 9, 9, 'καὶ βασιλεῖς')],
}
_TR_LIMITES = {
    'Matt': [(15, 5, 5, 'και ου μη τιμηση'), (26, 60, 61, 'ειπον ουτος')],
    'Mark': [(6, 27, 28, 'και ηνεγκεν')],
    'Acts': [(13, 32, 32, 'οτι ταυτην')],
    '2Cor': [(1, 6, 6, 'και η ελπις ημων βεβαια'), (8, 13, 13, 'αλλ εξ ισοτητος')],
    'Eph': [(1, 10, 11, 'εν ω και'), (3, 17, 18, 'ινα εξισχυσητε')],
    '1Thess': [(2, 11, 12, 'εις το περιπατησαι')],
    'Phlm': [(1, 11, 11, 'ον ανεπεμψα')],
    'Heb': [(1, 1, 1, 'επ εσχατων')],
}


@dataclass(frozen=True)
class TrechoHebraico:
    referencia: str
    texto: str
    lemas: str
    parte: str = ''
    parcial: bool = False


def _ref(ref: str) -> tuple[str, int, int]:
    match = re.fullmatch(r'([A-Za-z0-9]+)\.(\d+)\.(\d+)', ref)
    if not match:
        raise ErroFonte(f'Referência de fonte inválida: {ref!r}.')
    return match[1], int(match[2]), int(match[3])


def _texto_hebraico(elemento: ET.Element) -> tuple[str, str]:
    texto: list[str] = []
    lemas: list[str] = []
    for filho in elemento:
        tag = filho.tag.rsplit('}', 1)[-1]
        if tag == 'w':
            palavra = (filho.text or '').replace('/', '')
            if palavra:
                if filho.get('type') == 'x-ketiv':
                    palavra = f'〔ketiv: {palavra}〕'
                texto.append(palavra)
                if filho.get('lemma'):
                    lemas.append(f"{palavra}:{filho.get('lemma')}")
        elif tag == 'seg':
            sinal = (filho.text or '').strip()
            if sinal:
                texto.append(sinal)
        elif tag == 'note' and filho.get('type') == 'variant':
            qere = [
                (w.text or '').replace('/', '')
                for w in filho.findall('.//{*}rdg/{*}w') if w.text
            ]
            if qere:
                texto.append('〔qere: ' + ' '.join(qere) + '〕')
    return ' '.join(texto), ' '.join(lemas)


def _mapa_hebraico(conteudo: bytes) -> dict[str, list[tuple[str, str, str, bool]]]:
    try:
        raiz = ET.fromstring(conteudo)
        resultado: dict[str, list[tuple[str, str, str, bool]]] = defaultdict(list)
        for elemento in raiz.findall('.//{*}verse'):
            origem = elemento.attrib['wlc']
            destino = elemento.attrib['kjv']
            fonte, _, parte_fonte = origem.partition('!')
            alvo, _, parte_destino = destino.partition('!')
            _ref(fonte)
            _ref(alvo)
            parcial = elemento.get('type') == 'partial'
            resultado[fonte].append((alvo, parte_fonte, parte_destino, parcial))
        return dict(resultado)
    except (ET.ParseError, KeyError) as exc:
        raise ErroFonte('Mapa de versificação WLC inválido.') from exc


def _hebraico(livro: Livro, xml: bytes, mapa: dict[str, list[tuple[str, str, str, bool]]]) -> dict[tuple[int, int], dict[str, Any]]:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ErroFonte(f'XML WLC inválido para {livro.nome}.') from exc
    alvos = {
        (capitulo, verso)
        for capitulo, total in enumerate(livro.versos_por_capitulo, 1)
        for verso in range(1, total + 1)
    }
    agrupados: dict[tuple[int, int], list[TrechoHebraico]] = defaultdict(list)
    referencias_vistas: set[str] = set()
    for elemento in raiz.findall('.//{*}verse'):
        referencia = elemento.get('osisID', '')
        osis, cap, verso = _ref(referencia)
        if osis != livro.osis or referencia in referencias_vistas:
            raise ErroFonte(f'Referência WLC duplicada ou inesperada: {referencia}.')
        referencias_vistas.add(referencia)
        texto, lemas = _texto_hebraico(elemento)
        if not texto:
            raise ErroFonte(f'Texto WLC vazio em {referencia}.')
        destinos = list(mapa.get(referencia, [(referencia, '', '', False)]))
        # Uma parte do versículo WLC pode pertencer a outro versículo. Nesse
        # caso o restante continua no destino de mesmo número, se ainda faltar.
        partes = [d[1] for d in destinos if d[3] and d[1] in ('a', 'b')]
        if len(partes) == 1 and not any(d[0] == referencia for d in destinos):
            restante = 'b' if partes[0] == 'a' else 'a'
            destinos.append((referencia, restante, '', True))
        for alvo, parte_fonte, parte_destino, parcial in destinos:
            osis_destino, cap_destino, verso_destino = _ref(alvo)
            if osis_destino != livro.osis or (cap_destino, verso_destino) not in alvos:
                raise ErroFonte(f'Mapeamento WLC fora da versificação: {referencia} -> {alvo}.')
            descricao = ''
            if parte_fonte:
                descricao += f'parte {parte_fonte} da referência WLC; limite exato requer revisão'
            if parte_destino:
                descricao += f' parte {parte_destino} do versículo de destino'
            agrupados[(cap_destino, verso_destino)].append(
                TrechoHebraico(referencia, texto, lemas, descricao.strip(), parcial)
            )

    resultado: dict[tuple[int, int], dict[str, Any]] = {}
    for capitulo, verso in sorted(alvos):
        trechos = agrupados.get((capitulo, verso), [])
        if livro.osis == 'Ps' and verso == 1 and len(trechos) > 1:
            # Superscrições WLC são versículos próprios, mas não fazem parte do
            # primeiro versículo na versificação escolhida. Preserve o último.
            maior = max(_ref(t.referencia)[2] for t in trechos)
            trechos = [t for t in trechos if _ref(t.referencia)[2] == maior]
        if not trechos:
            if (livro.osis, capitulo, verso) == ('Neh', 7, 68):
                resultado[(capitulo, verso)] = {
                    'verse': verso, 'ausente': True,
                    'aviso': 'Neemias 7:68 não tem correspondente no WLC usado; requer fonte suplementar e revisão.',
                }
                continue
            raise ErroFonte(f'Sem fonte WLC para {livro.nome} {capitulo}:{verso}.')
        base = []
        for trecho in trechos:
            item = {
                'edicao': 'WLC/OSHB', 'referencia': trecho.referencia,
                'texto': trecho.texto, 'lemas_oshb': trecho.lemas,
            }
            if trecho.parte:
                item['parte'] = trecho.parte
            base.append(item)
        item = {'verse': verso, 'base': base}
        if any(t.parcial for t in trechos):
            item['aviso'] = (
                'Correspondência WLC parcial: confira manualmente os limites entre versículos '
                'e a tradução; o mapa não fornece os pontos exatos de separação.'
            )
        resultado[(capitulo, verso)] = item
    return resultado


_SIGLAS_APARATO = frozenset({'WH', 'Treg', 'NA28', 'RP', 'NIV', 'ST', 'SR', 'KJTR', 'Scrivener'})


def _forma_comparavel(texto: str) -> str:
    """Minúsculas, sem acentos nem pontuação do aparato (⸀ ⸂ ⸃ · ‹ ›)."""
    import unicodedata
    decomposto = unicodedata.normalize('NFD', texto.casefold())
    sem_acentos = ''.join(c for c in decomposto if not unicodedata.combining(c))
    return re.sub(r'[^\w ]+', ' ', sem_acentos)


def _nota_pertence_ao_verso(nota: str, texto_verso: str) -> bool:
    """Uma nota do aparato pertence ao versículo BEE que contém a sua palavra-base.

    O aparato da SBLGNT é indexado pelo versículo SBLGNT. Quando a BEE junta o
    início de um versículo SBLGNT ao anterior (ex.: 1 Tessalonicenses 2:6–7),
    a nota do versículo seguinte chegava a ambos. A palavra-base é a primeira
    do lado esquerdo de «]» (o texto da base), sem número, sigla nem sinal.
    Sem palavra-base (adição «+» ou omissão «–») e nas notas de intervalo
    («16–17»), a nota mantém-se como antes.
    """
    limpa = nota.replace('\xa0', ' ')
    # Notas de intervalo («16–17 …») abrangem vários versículos: não se decide por lema.
    if re.match(r'^[\s•]*\d+\s*[–-]\s*\d+', limpa):
        return True
    corpo = re.sub(r'^[\s•]*\d*\s*', '', limpa)
    base = corpo.split(']', 1)[0]
    if corpo.lstrip().startswith(('+', '–', '-')):
        return True
    siglas = {x.casefold() for x in _SIGLAS_APARATO}
    palavras = [
        w for w in _forma_comparavel(base).split()
        if w not in siglas and not w.isdigit()
    ]
    if not palavras:
        return True
    contexto = ' ' + _forma_comparavel(texto_verso) + ' '
    return f' {palavras[0]} ' in contexto


def _filtrar_notas_do_verso(notas: list[str], texto_verso: str) -> list[str]:
    """Decide por grupo: uma nota numerada e as linhas «•» que se lhe seguem.

    Um grupo de intervalo («16–17») fica sempre como estava. Um grupo de um
    versículo só fica se a sua palavra-base estiver no versículo BEE.
    """
    grupos: list[list[str]] = []
    for nota in notas:
        if re.match(r'^\s*\d', nota.replace('\xa0', ' ')) or not grupos:
            grupos.append([nota])
        else:
            grupos[-1].append(nota)
    resultado: list[str] = []
    for grupo in grupos:
        cabeca = grupo[0].replace('\xa0', ' ')
        if re.match(r'^\s*\d+\s*[–-]\s*\d+', cabeca) or _nota_pertence_ao_verso(cabeca, texto_verso):
            resultado.extend(grupo)
    return resultado


def _aparato(xml: bytes) -> dict[tuple[int, int], list[str]]:
    try:
        raiz = ET.fromstring(xml)
    except ET.ParseError as exc:
        raise ErroFonte('Aparato SBLGNT inválido.') from exc
    resultado: dict[tuple[int, int], list[str]] = defaultdict(list)
    atual: tuple[int, int] | None = None
    for elemento in raiz:
        if elemento.tag == 'verse':
            match = re.search(r'(\d+):(\d+)$', ''.join(elemento.itertext()).strip())
            atual = (int(match[1]), int(match[2])) if match else None
        elif elemento.tag == 'note' and atual:
            texto = ''.join(elemento.itertext()).strip()
            if texto:
                resultado[atual].append(texto)
    return dict(resultado)


def _limites_ajustados(
    livro: Livro, originais: dict[tuple[int, int], str],
    regras: dict[str, list[tuple[int, int, int, str]]], edicao: str,
) -> dict[tuple[int, int], list[tuple[tuple[int, int], str]]]:
    """Reparte texto somente em pontos registrados, preservando a referência original."""
    resultado: dict[tuple[int, int], list[tuple[tuple[int, int], str]]] = {}
    for cap, primeiro, fonte, inicio_final in regras.get(livro.osis, []):
        # Livros reduzidos usados em testes podem não conter esta passagem.
        if cap > livro.capitulos or primeiro + 1 > livro.versos_por_capitulo[cap - 1]:
            continue
        anterior, seguinte, origem = (cap, primeiro), (cap, primeiro + 1), (cap, fonte)
        if anterior in resultado or seguinte in resultado or origem not in (anterior, seguinte):
            raise ErroFonte(f'Regras de versificação {edicao} inconsistentes: {livro.nome} {cap}:{primeiro}.')
        if anterior not in originais or seguinte not in originais:
            raise ErroFonte(f'Referência {edicao} ausente ao alinhar {livro.nome} {cap}:{primeiro}.')
        inteiro = originais[origem]
        if inteiro.count(inicio_final) != 1:
            raise ErroFonte(f'Limite {edicao} não encontrado de forma inequívoca: {livro.nome} {cap}:{fonte}.')
        inicio, _, final = inteiro.partition(inicio_final)
        inicio, final = inicio.strip(), (inicio_final + final).strip()
        if not inicio or not final:
            raise ErroFonte(f'Partição {edicao} vazia: {livro.nome} {cap}:{fonte}.')
        if origem == anterior:
            resultado[anterior] = [(origem, inicio)]
            resultado[seguinte] = [(origem, final), (seguinte, originais[seguinte])]
        else:
            resultado[anterior] = [(anterior, originais[anterior]), (origem, inicio)]
            resultado[seguinte] = [(origem, final)]
    return resultado


def _ler_scrivener(livro: Livro, texto: str) -> dict[str, Any]:
    """Lê os versículos de Robinson; converte somente letras, não inventa diacríticos."""
    # Títulos entre colchetes podem ocupar mais de uma linha e não fazem parte
    # dos versículos. Rejeite colchetes mal formados ou caracteres inesperados.
    texto = re.sub(r'\[[^\[\]]*\]', '', texto, flags=re.DOTALL)
    if '[' in texto or ']' in texto:
        raise ErroFonte(f'Título TR mal formado em {livro.nome}.')
    referencias: dict[tuple[int, int], list[str]] = {}
    atual: tuple[int, int] | None = None
    for linha in texto.splitlines():
        match = re.fullmatch(r'\s*(\d+):(\d+)\s*(.*)', linha)
        if match:
            atual = (int(match[1]), int(match[2]))
            if atual in referencias:
                raise ErroFonte(f'Versículo TR duplicado em {livro.nome} {atual}.')
            referencias[atual] = []
            linha = match[3]
        linha = linha.strip()
        if linha:
            if atual is None or not re.fullmatch(r'[a-z ]+', linha):
                raise ErroFonte(f'Texto TR inválido em {livro.nome} {atual}.')
            referencias[atual].append(linha)
    esperadas = {
        (c, v) for c, total in enumerate(livro.versos_por_capitulo, 1)
        for v in range(1, total + 1)
    }
    if set(referencias) != esperadas or any(not valor for valor in referencias.values()):
        raise ErroFonte(f'Contagem de versículos TR inválida: {livro.nome}.')
    originais = {chave: ' '.join(linhas).translate(_TR_UNICODE) for chave, linhas in referencias.items()}
    ajustes = _limites_ajustados(livro, originais, _TR_LIMITES, 'TR')
    capitulos = []
    for cap, total in enumerate(livro.versos_por_capitulo, 1):
        capitulos.append([
            ' '.join(trecho for _, trecho in ajustes.get((cap, verso), [((cap, verso), originais[(cap, verso)])]))
            for verso in range(1, total + 1)
        ])
    return {'chapters': capitulos, 'ajustados': ajustes}


def _grego(livro: Livro, texto: str, aparato: dict[tuple[int, int], list[str]], tr: dict[str, Any]) -> dict[tuple[int, int], dict[str, Any]]:
    base_sbl: dict[tuple[int, int], str] = {}
    padrao = re.compile(r'^' + re.escape(livro.osis) + r' (\d+):(\d+)\t(.+)$')
    for linha in texto.splitlines():
        match = padrao.match(linha)
        if match:
            chave = (int(match[1]), int(match[2]))
            if chave in base_sbl:
                raise ErroFonte(f'Referência SBLGNT duplicada: {livro.osis} {chave}.')
            base_sbl[chave] = match[3].strip()
    if not base_sbl:
        raise ErroFonte(f'Sem texto SBLGNT para {livro.nome}.')

    # Chave tradicional -> (referência SBLGNT, trecho). Algumas edições dividem
    # versículos de modo diferente. Só se dividem strings em limites explícitos.
    ajustes: dict[tuple[int, int], list[tuple[tuple[int, int], str]]] = {}
    if livro.osis == 'Acts':
        original = base_sbl.get((19, 40), '')
        inicio, separador, fim = original.partition('καὶ ταῦτα εἰπὼν')
        if not separador or not inicio.strip() or not fim.strip():
            raise ErroFonte('Não foi possível alinhar Atos 19:40-41.')
        ajustes[(19, 40)] = [((19, 40), inicio.strip())]
        ajustes[(19, 41)] = [((19, 40), (separador + fim).strip())]
    elif livro.osis == '2Cor':
        original = base_sbl.get((13, 12), '')
        inicio, separador, fim = original.partition('ἀσπάζονται')
        if not separador or not inicio.strip() or not fim.strip() or (13, 13) not in base_sbl:
            raise ErroFonte('Não foi possível alinhar 2 Coríntios 13:12-14.')
        ajustes[(13, 12)] = [((13, 12), inicio.strip())]
        ajustes[(13, 13)] = [((13, 12), (separador + fim).strip())]
        ajustes[(13, 14)] = [((13, 13), base_sbl[(13, 13)])]
    elif livro.osis == '3John':
        try:
            ajustes[(1, 14)] = [((1, 14), base_sbl[(1, 14)]), ((1, 15), base_sbl[(1, 15)])]
        except KeyError as exc:
            raise ErroFonte('Não foi possível alinhar 3 João 1:14.') from exc
    elif livro.osis == 'Rev':
        try:
            ajustes[(13, 1)] = [((12, 18), base_sbl[(12, 18)]), ((13, 1), base_sbl[(13, 1)])]
        except KeyError as exc:
            raise ErroFonte('Não foi possível alinhar Apocalipse 13:1.') from exc
    outros_ajustes = _limites_ajustados(livro, base_sbl, _SBL_LIMITES, 'SBLGNT')
    if ajustes.keys() & outros_ajustes.keys():
        raise ErroFonte(f'Regras SBLGNT sobrepostas: {livro.nome}.')
    ajustes.update(outros_ajustes)

    resultado: dict[tuple[int, int], dict[str, Any]] = {}
    for capitulo, total in enumerate(livro.versos_por_capitulo, 1):
        for verso in range(1, total + 1):
            chave = (capitulo, verso)
            comparacao = tr['chapters'][capitulo - 1][verso - 1]
            sbl = ajustes.get(chave)
            if sbl is None and chave in base_sbl:
                sbl = [(chave, base_sbl[chave])]
            item: dict[str, Any] = {'verse': verso}
            if not sbl:
                if (livro.osis, capitulo, verso) not in _AUSENTES_SBL:
                    raise ErroFonte(f'Sem fonte SBLGNT inesperadamente: {livro.nome} {capitulo}:{verso}.')
                item['base'] = [{'edicao': 'Textus Receptus', 'referencia': f'{livro.osis}.{capitulo}.{verso}', 'texto': comparacao}]
                item['aviso'] = (
                    'O SBLGNT fornecido não possui este versículo; a tradução usa o Textus Receptus '
                    'como fonte suplementar e deve ser revista.'
                )
            else:
                item['base'] = [
                    {'edicao': 'SBLGNT', 'referencia': f'{livro.osis}.{ref[0]}.{ref[1]}', 'texto': conteudo}
                    for ref, conteudo in sbl
                ]
                item['textus_receptus'] = comparacao
                notas = []
                texto_verso = ' '.join(conteudo for _, conteudo in sbl)
                for ref, _ in sbl:
                    notas.extend(_filtrar_notas_do_verso(aparato.get(ref, []), texto_verso))
                if notas:
                    item['aparato_sblgnt'] = notas
                avisos = []
                if chave in ajustes:
                    avisos.append(
                        'A numeração SBLGNT foi adaptada à versificação tradicional; '
                        'confira a separação ou junção e as variantes antes da publicação.'
                    )
                referencias_tr = tr.get('ajustados', {}).get(chave)
                if referencias_tr:
                    item['textus_receptus_referencias'] = [
                        f'{livro.osis}.{ref[0]}.{ref[1]}' for ref, _ in referencias_tr
                    ]
                    avisos.append('O Textus Receptus foi repartido entre referências para comparação; confira os limites.')
                if ((livro.osis == 'Mark' and capitulo == 16 and 9 <= verso <= 20) or
                        (livro.osis == 'John' and capitulo == 7 and verso == 53) or
                        (livro.osis == 'John' and capitulo == 8 and 1 <= verso <= 11)):
                    avisos.append(
                        'O SBLGNT assinala esta passagem entre colchetes críticos; '
                        'sua situação textual requer investigação e revisão especializada.'
                    )
                # Nestes casos a ordem de palavras ou frases muda entre edições;
                # não se deve apresentar uma simples repartição como fato certo.
                if (livro.osis, capitulo, verso) in {
                    ('Phil', 1, 16), ('Phil', 1, 17), ('Mark', 7, 21), ('Mark', 7, 22),
                }:
                    vizinho = verso + 1 if verso in (16, 21) else verso - 1
                    item['textus_receptus_versiculo_vizinho'] = {
                        'referencia': f'{livro.osis}.{capitulo}.{vizinho}',
                        'texto': tr['chapters'][capitulo - 1][vizinho - 1],
                    }
                    avisos.append(
                        'A ordem das leituras no SBLGNT e no TR atravessa versículos adjacentes; '
                        'confira o contexto e a crítica textual manualmente.'
                    )
                if avisos:
                    item['aviso'] = ' '.join(avisos)
            resultado[chave] = item
    return resultado


class FontesOriginais:
    def __init__(self, diretorio_cache: Path, rede: ClienteHTTP):
        self.cache = diretorio_cache
        self.rede = rede
        self._livros: dict[int, dict[tuple[int, int], dict[str, Any]]] = {}
        self._tr: dict[int, dict[str, Any]] = {}
        self._mapa: dict[str, list[tuple[str, str, str, bool]]] | None = None

    def _obter(self, tipo: str) -> Path:
        nome, url, checksum, accept = FONTES[tipo]
        self.cache.mkdir(parents=True, exist_ok=True)
        caminho = self.cache / nome
        if caminho.exists():
            resumo = hashlib.sha256()
            with caminho.open('rb') as arquivo:
                for bloco in iter(lambda: arquivo.read(1024 * 1024), b''):
                    resumo.update(bloco)
            if resumo.hexdigest() == checksum:
                return caminho
            print(f'Cache de {tipo} inválido; a descarregar novamente.')
        print(f'A descarregar fonte {tipo} para {self.cache} (uma vez por versão)...', flush=True)
        requisicao = urllib.request.Request(url, headers={'Accept': accept, 'User-Agent': 'gerar-bee/1.0'})
        dados = self.rede.obter(requisicao, f'Fonte {tipo}')
        if hashlib.sha256(dados).hexdigest() != checksum:
            raise ErroFonte(f'Integridade da fonte {tipo} falhou; ficheiro não utilizado.')
        fd, temporario = tempfile.mkstemp(prefix=f'.{nome}.', suffix='.bee-tmp', dir=self.cache)
        try:
            with os.fdopen(fd, 'wb') as arquivo:
                arquivo.write(dados)
                arquivo.flush()
                os.fsync(arquivo.fileno())
            os.replace(temporario, caminho)
        finally:
            try:
                os.unlink(temporario)
            except FileNotFoundError:
                pass
        return caminho

    @staticmethod
    def _ler_zip(caminho: Path, nome: str) -> bytes:
        try:
            with zipfile.ZipFile(caminho) as arquivo:
                info = arquivo.getinfo(nome)
                if info.file_size > 8 * 1024 * 1024:
                    raise ErroFonte(f'Ficheiro de fonte demasiado grande: {nome}.')
                return arquivo.read(info)
        except (OSError, KeyError, zipfile.BadZipFile) as exc:
            raise ErroFonte(f'Arquivo de fontes inválido: {nome}.') from exc

    def _textus_receptus(self, livro: Livro) -> dict[str, Any]:
        if livro.numero not in self._tr:
            nome = _TR_ARQUIVOS[livro.osis]
            pasta = f'greektext-scrivener-{TR_COMMIT}/textonly/'
            try:
                texto = self._ler_zip(self._obter('tr'), pasta + nome + '.SCV').decode('ascii')
            except UnicodeError as exc:
                raise ErroFonte(f'Codificação TR inválida para {livro.nome}.') from exc
            self._tr[livro.numero] = _ler_scrivener(livro, texto)
        return self._tr[livro.numero]

    def carregar_livro(self, livro: Livro) -> dict[tuple[int, int], dict[str, Any]]:
        if livro.numero in self._livros:
            return self._livros[livro.numero]
        if livro.antigo_testamento:
            caminho = self._obter('wlc')
            pasta = f'morphhb-{MORPH_COMMIT}/wlc/'
            if self._mapa is None:
                self._mapa = _mapa_hebraico(self._ler_zip(caminho, pasta + 'VerseMap.xml'))
            dados = _hebraico(livro, self._ler_zip(caminho, pasta + livro.osis + '.xml'), self._mapa)
        else:
            caminho = self._obter('sbl')
            pasta = f'SBLGNT-{SBL_COMMIT}/data/'
            try:
                texto = self._ler_zip(caminho, pasta + 'sblgnt/text/' + livro.osis + '.txt').decode('utf-8-sig')
            except UnicodeError as exc:
                raise ErroFonte(f'Codificação SBLGNT inválida para {livro.nome}.') from exc
            aparato = _aparato(self._ler_zip(caminho, pasta + 'sblgntapp/xml/' + livro.osis + '.xml'))
            tr = self._textus_receptus(livro)
            dados = _grego(livro, texto, aparato, tr)
        self._livros[livro.numero] = dados
        return dados

    def capitulo(self, livro: Livro, capitulo: int) -> list[dict[str, Any]]:
        if not 1 <= capitulo <= livro.capitulos:
            raise ErroFonte(f'Capítulo inválido: {livro.nome} {capitulo}.')
        dados = self.carregar_livro(livro)
        return [dados[(capitulo, verso)] for verso in range(1, livro.versos_por_capitulo[capitulo - 1] + 1)]
