#!/usr/bin/env python3
"""Guarda anti-deriva da voz BEE: deteta nos versículos gerados aquilo que o
perfil proíbe, ANTES de chegar ao leitor.

É uma rede de segurança independente do modelo: mesmo que um provedor "escorregue"
para a Almeida ou misture registos, este verificador sinaliza. Corre offline, sem
rede nem chaves, sobre os JSON de qualquer edição.

Procura três categorias:
  * ARCAÍSMOS (falha dura) — «vós/vos/convosco», «sois/sejais/sabeis/padeceis…»;
    a voz BEE usa sempre «vocês».
  * HESITAÇÃO NO TEXTO (falha dura) — «ou seja», «ou melhor», parênteses/travessões
    com alternativa; as nuances pertencem à nota, não ao versículo.
  * MARCADORES DE ALMEIDA (aviso) — léxico eclesiástico/antigo («sobremaneira»,
    «porventura», «outrossim», «o sem lei»…) a merecer reescrita.

Código de saída: 1 se houver FALHAS duras (ou também avisos com --rigoroso);
0 caso contrário. Serve tanto para leitura manual como para um passo de CI.

Uso:
    python3 scripts/verificar_estilo.py                     # edição nova
    python3 scripts/verificar_estilo.py --dados livros_json # linha legada
    python3 scripts/verificar_estilo.py 600                 # só 2 Tessalonicenses
    python3 scripts/verificar_estilo.py --rigoroso          # avisos também chumbam
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_todos  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402


def _norm(texto: str) -> str:
    """Minúsculas e sem acentos, para casar formas independentemente do acento."""
    sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto) if not unicodedata.combining(c)
    )
    return sem_acentos.casefold()


# Falhas duras: nunca podem aparecer no texto aprovado.
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


def analisar_dados(dados: dict) -> list[tuple[int, int, str, dict]]:
    """Percorre capítulos completos e em curso; devolve achados por versículo."""
    achados: list[tuple[int, int, str, dict]] = []
    for capitulo, versiculos in sorted({**dados.get('chapters', {}),
                                        **dados.get('in_progress', {})}.items(),
                                       key=lambda kv: int(kv[0])):
        for verso in versiculos:
            resultado = analisar_texto(str(verso.get('text', '')))
            if resultado['duros'] or resultado['avisos']:
                achados.append((int(capitulo), int(verso.get('verse', 0)),
                                str(verso.get('text', '')), resultado))
    return achados


def relatorio(pasta: Path, livros_filtro: set[int] | None, rigoroso: bool) -> int:
    todos = ler_todos(pasta)
    falhas = avisos_total = 0
    for numero in sorted(todos):
        if livros_filtro and numero not in livros_filtro:
            continue
        livro = POR_NUMERO.get(numero)
        nome = livro.nome if livro else str(numero)
        achados = analisar_dados(todos[numero])
        if not achados:
            continue
        print(f'\n## {nome} ({numero})')
        for capitulo, verso, texto, res in achados:
            etiqueta = []
            if res['duros']:
                etiqueta.append('FALHA: ' + ', '.join(res['duros']))
            if res['avisos']:
                etiqueta.append('aviso: ' + ', '.join(res['avisos']))
            falhas += 1 if res['duros'] else 0
            avisos_total += len(res['avisos'])
            excerto = (texto[:90] + '…') if len(texto) > 90 else texto
            print(f'  {capitulo}:{verso} [{"; ".join(etiqueta)}] {excerto}')
    if falhas == 0 and avisos_total == 0:
        print('\nEstilo limpo: nenhum arcaísmo, hesitação ou marcador de Almeida.')
    else:
        print(f'\nResumo: {falhas} versículo(s) com falhas duras, {avisos_total} aviso(s).')
    if falhas:
        return 1
    if rigoroso and avisos_total:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('livros', nargs='*', type=int,
                        help='book_number a filtrar (vazio = todos)')
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json',
                        help='pasta dos JSON (padrão: edição nova)')
    parser.add_argument('--rigoroso', action='store_true',
                        help='avisos (marcadores de Almeida) também fazem chumbar')
    args = parser.parse_args()
    if not args.dados.exists():
        print(f'Pasta de dados não encontrada: {args.dados}', file=sys.stderr)
        return 2
    return relatorio(args.dados, set(args.livros) or None, args.rigoroso)


if __name__ == '__main__':
    raise SystemExit(main())
