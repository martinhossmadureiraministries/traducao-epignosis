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

_RE_ARCAICO = {
    termo: re.compile(r'(?<![a-zà-ÿ])' + re.escape(_norm(termo)) + r'(?![a-zà-ÿ])')
    for termo in ARCAISMOS
}


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
    avisos = [m for m in MARCADORES_ALMEIDA if m in baixo]
    return {'duros': sorted(set(duros)), 'avisos': sorted(set(avisos))}
