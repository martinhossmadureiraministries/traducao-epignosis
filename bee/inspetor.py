"""Núcleo determinístico da guarda anti-deriva da voz BEE.

Vive na biblioteca (e não apenas em ``scripts/``) para que o próprio motor de
geração o possa usar como PORTA OBRIGATÓRIA (P1 da convergência multi-provedor):
o ``Rodizio`` inspeciona cada lote antes de o devolver e roda para outro
provedor quando o texto dériva para arcaísmos ou hesitação. O script
``scripts/verificar_estilo.py`` é a CLI de auditoria sobre dados gravados e
importa tudo daqui — uma só fonte para as listas de proibição.

Procura três categorias:
  * ARCAÍSMOS (falha dura) — «vós/vos/convosco», «sois/sejais/sabeis/padeceis…»;
    a voz BEE usa sempre «vocês».
  * HESITAÇÃO NO TEXTO (falha dura) — «ou seja», «ou melhor», parênteses/travessões
    com alternativa; as nuances pertencem à nota, não ao versículo.
  * MARCADORES DE ALMEIDA (aviso) — léxico eclesiástico/antigo («sobremaneira»,
    «porventura», «outrossim», «o sem lei»…) a merecer reescrita.
"""
from __future__ import annotations

import re
import unicodedata


def _norm(texto: str) -> str:
    """Minúsculas e sem acentos, para casar formas independentemente do acento."""
    sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto) if not unicodedata.combining(c)
    )
    return sem_acentos.casefold()


# Falhas duras: nunca podem aparecer no texto aprovado. Espelho exato da lista
# negra de modelos/estilo_bee.json (um teste de coerência garante a igualdade).
ARCAISMOS = (
    'vós', 'vos', 'vosso', 'vossa', 'vossos', 'vossas', 'convosco',
    'sois', 'sejais', 'estais', 'estejais', 'tendes', 'tenhais', 'sabeis',
    'sabíeis', 'padeceis', 'quereis', 'deveis', 'fazeis', 'dizeis', 'vedes',
    'rogamos-vos', 'tornai-vos', 'lembrai-vos',
)

# Hesitação/glosa dentro do versículo (frases e padrões).
HEDGE_FRASES = ('ou seja', 'ou melhor', 'isto é,', 'dito de outro modo', 'em outras palavras')
# O texto é comparado sem acentos (_norm), logo as frases também têm de ser
# comparadas normalizadas — senão «isto é,» (com acento) nunca casaria. O
# rótulo acrescentado aos achados continua a ser a forma original legível.
_HEDGE_FRASES_NORM = tuple(_norm(f) for f in HEDGE_FRASES)
# Cada entrada é (rótulo legível, padrão) para o relatório não mostrar regex cru.
HEDGE_PADROES = (
    ('hesitação em parênteses', re.compile(r'\([^)]*\bou\b[^)]*\)')),
    ('hesitação com travessão', re.compile(r'—\s*ou\s', re.IGNORECASE)),
    ('metalinguagem "grego:"', re.compile(r'\bgrego:\b', re.IGNORECASE)),
    ('"literalmente:" no texto', re.compile(r'\bliteralmente[: ]', re.IGNORECASE)),
)

# Avisos: cheiram a Almeida; reescrever salvo razão contextual forte. Ficam de
# fora expressões que os pilotos aprovados mantiveram legitimamente («em verdade»,
# «Eis que» numa citação profética), para não sinalizar o padrão-ouro.
MARCADORES_ALMEIDA = (
    'sobremaneira', 'deveras', 'porventura', 'outrossim', 'dar-se-á', 'sucedeu que',
    'aconteceu que', 'o sem lei', 'para com os outros', 'glória da sua força',
    'manifestação da sua vinda', 'filho da perdição',
)
# O texto é comparado sem acentos (_norm), logo os marcadores também têm de ser
# comparados normalizados — sem isto, «filho da perdição», «glória da sua força»,
# «manifestação da sua vinda» e «dar-se-á» nunca casavam (tinham acento) e a
# auditoria devolvia «Estilo limpo» a livros que os contêm. Foi o falso negativo
# que deixou passar as regressões de 2 Tessalonicenses 2:3 e 2:8.
_MARCADORES_ALMEIDA_NORM = tuple((_norm(m), m) for m in MARCADORES_ALMEIDA)

_RE_ARCAICO = {
    termo: re.compile(r'(?<![a-zà-ÿ])' + re.escape(_norm(termo)) + r'(?![a-zà-ÿ])')
    for termo in ARCAISMOS
}

# Falhas duras POR FORMA, que a lista de palavras não consegue enumerar
# (qualquer verbo pode ser conjugado na 2.ª pessoa do plural de «vós»).
# A produção de 2026-11-20 deixou passar «adorareis» e «conheceis»
# misturados com «vocês» porque a lista só tinha algumas formas fixas.
#
# «-eis» sem acento: as formas verbais (conheceis, adorareis, sabeis) não
# têm acento; os nomes/adjetivos legítimos em -eis ou o têm (fiéis,
# papéis, difíceis, anéis) ou estão na lista de excepções (seis, leis,
# reis). O padrão corre sobre o texto dobrado (casefold) mas SEM tirar
# acentos, e exige fronteira de palavra dos dois lados.
_EXCECOES_EIS = frozenset({'seis', 'leis', 'reis'})
_RE_EIS = re.compile(r'(?<![a-zà-ÿ])[a-z]+eis(?![a-zà-ÿ])')
# «estar/andar a» + infinitivo NÃO é falha. A regra que a proibia partia de
# uma premissa que o corpus desmentiu (Rute 2:9, Rute 4:3, Habacuque 1:5, todos
# aprovados) e contradizia a norma europeia que a casa segue na ortografia e na
# colocação dos pronomes: «está a fazer» é a perífrase de Portugal e de Angola,
# «está fazendo» é a do Brasil. Decisão do responsável de 2026-11-22: a
# perífrase é a forma da casa para o progressivo; o gerúndio progressivo fica
# como variante aceite e o gerúndio continua a verter o particípio grego.
# Pontuação dentro das aspas é a forma da casa («Segue-me.»): «beber». é
# a pontuação de Almeida que a produção nova usou em João 4.
_RE_PONTO_FORA = re.compile(r'»(?=[.?!])')

# Formato único das notas (decisão do responsável, 2026-11-23): um parágrafo de
# comentário em prosa por versículo, sem rótulos de secção e sem níveis de
# certeza (A, B, C). A Crítica Textual vai num parágrafo próprio, «Crítica
# Textual:», só quando o aparato da SBLGNT ou a colação registam variante.
# Os livros e capítulos antigos foram todos convertidos; não há exceções.
_RE_ROTULO_ANTIGO = re.compile(
    r'<b>\s*(Análise Léxica|Síntese Exegética)\s*:?\s*</b>', re.I)
# Níveis só com maiúscula (A, B, C) e a expressão «nível de certeza».
_RE_NIVEL = re.compile(
    r'[Nn]ível de certeza|\b[Nn]ível [ABC]\b|\*\*[ABC]\*\*')


def analisar_texto(texto: str) -> dict[str, list[str]]:
    """Classifica um texto de versículo. Devolve {'duros': […], 'avisos': […]}."""
    baixo = _norm(texto)
    orig_baixo = texto.casefold()
    duros: list[str] = []
    for termo, padrao in _RE_ARCAICO.items():
        if padrao.search(baixo):
            duros.append(termo)
    for frase, norma in zip(HEDGE_FRASES, _HEDGE_FRASES_NORM):
        if norma in baixo:
            duros.append(frase)
    for rotulo, padrao in HEDGE_PADROES:
        if padrao.search(orig_baixo):
            duros.append(rotulo)
    if any(tok not in _EXCECOES_EIS for tok in _RE_EIS.findall(orig_baixo)):
        duros.append('forma verbal de «vós» (-eis)')
    if _RE_PONTO_FORA.search(texto):
        duros.append('ponto fora das aspas')
    avisos = [rotulo for norma, rotulo in _MARCADORES_ALMEIDA_NORM if norma in baixo]
    return {'duros': sorted(set(duros)), 'avisos': sorted(set(avisos))}


_GREGO = re.compile(r'[Ͱ-Ͽἀ-῿]')


def grego_sem_italico(comentario: str) -> list[str]:
    """Falha da auditoria (D7): grego numa nota fora de itálico.

    Fica só no verificador de estilo (scripts/verificar_estilo.py) e não na
    porta do gerador (`analisar_comentario`), para não chumbar a produção
    enquanto a instrução do modelo não pedir o itálico.
    """
    from .grego import grego_fora_de_italico
    return ['grego fora de itálico na nota (convenção D7)'] \
        if grego_fora_de_italico(comentario or '') else []


def analisar_comentario(comentario: str) -> list[str]:
    """Falhas duras da NOTA: rótulos e níveis antigos, grego misto.

    A nota é prosa. Não pode trazer as antigas secções «Análise Léxica» e
    «Síntese Exegética», nem níveis de certeza A/B/C, nem «nota de redação».
    As palavras greco-latinas mistas («ἄνδra», com letras latinas dentro da
    palavra grega) são gralha mecânica inequívoca: também chumbam.
    """
    nota = comentario or ''
    falhas: list[str] = []
    if _RE_ROTULO_ANTIGO.search(nota):
        falhas.append('rótulo de formato antigo na nota (Análise Léxica / Síntese Exegética)')
    if _RE_NIVEL.search(nota):
        falhas.append('nível de certeza (A/B/C) na nota: retirar')
    limpo = re.sub(r'<[^>]+>', ' ', nota)
    if any(_GREGO.search(tok) and re.search(r'[A-Za-z]', tok)
           for tok in limpo.split()):
        falhas.append('palavra greco-latina mista na nota')
    return falhas
