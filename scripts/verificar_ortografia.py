#!/usr/bin/env python3
"""Alerta ortográfico PT-PT sobre os versículos e notas gravados.

Os modelos inventam palavras («vendentem», «quej») e nenhum verificador
determinístico as apanhava: a memória de estilo pede «ZERO gralhas» ao
modelo, mas quem gera também é quem se fiscaliza. Este script é a rede
independente: corre o dicionário português sobre texto e nota e reporta
palavras desconhecidas QUE ESTÃO A UMA (ou, nas longas, duas) letras de
uma palavra real — a assinatura típica da gralha.

É ALERTA, não porta: o dicionário também desconhece formas legítimas
(«connosco» europeu, nomes bíblicos), por isso a lista da casa em
``modelos/ortografia_casa.txt`` e o modo de saída são conservadores.
Com ``--rigoroso`` os suspeitos fazem sair com código 1.

Sem ``pyspellchecker`` instalado, o script avisa e sai com 0 — um
verificador ausente nunca pode parar a produção.

Uso:
    python3 scripts/verificar_ortografia.py                 # edição nova
    python3 scripts/verificar_ortografia.py --rigoroso      # suspeitos chumbam
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_todos  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402

LISTA_CASA = RAIZ / 'modelos' / 'ortografia_casa.txt'

_ITALICO = re.compile(r'<i>.*?</i>', re.S)
_PARENTESES = re.compile(r'\([^)]*\)')
_ETIQUETAS = re.compile(r'<[^>]+>')
_PALAVRA = re.compile(r'[A-Za-zÀ-ÖØ-öø-ÿ]+(?:-[A-Za-zÀ-ÖØ-öø-ÿ]+)*')


def _distancia(a: str, b: str) -> int:
    """Levenshtein simples (as palavras são curtas)."""
    if abs(len(a) - len(b)) > 2:
        return 3
    anterior = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        atual = [i]
        for j, cb in enumerate(b, 1):
            atual.append(min(
                atual[-1] + 1, anterior[j] + 1,
                anterior[j - 1] + (0 if ca == cb else 1)))
        anterior = atual
    return anterior[-1]


def palavras_do_texto(texto: str) -> list[str]:
    """Palavras portuguesas verificáveis de um texto/nota.

    Fora ficam: o que está em <i> (grego e transliterações), o que está
    entre parênteses (transliterações e apartes), palavras com maiúscula
    inicial (nomes próprios: «Sicar» não é «ficar») e palavras curtas.
    """
    limpo = _ITALICO.sub(' ', texto or '')
    limpo = _PARENTESES.sub(' ', limpo)
    limpo = _ETIQUETAS.sub(' ', limpo)
    palavras = []
    for tok in _PALAVRA.findall(limpo):
        if len(tok) < 4 or tok[0].isupper():
            continue
        palavras.append(tok.casefold())
    return palavras


_CLITICOS = ('-lhes', '-los', '-las', '-lhe', '-nos', '-vos', '-se',
             '-te', '-me', '-lo', '-la', '-os', '-as', '-o', '-a')
_CACHE: dict[str, str | None] = {}


def _correcao(corretor, palavra: str) -> str | None:
    if palavra not in _CACHE:
        _CACHE[palavra] = corretor.correction(palavra)
    return _CACHE[palavra]


def _formas(palavra: str) -> list[str]:
    """A palavra e o seu radical sem clítico («ajudá-los» → «ajudá»)."""
    formas = [palavra]
    for clitico in _CLITICOS:
        if palavra.endswith(clitico) and len(palavra) > len(clitico) + 2:
            formas.append(palavra[: -len(clitico)])
            break
    return formas


def suspeitas(texto: str, corretor, conhecidas: set[str]) -> list[str]:
    """Palavras desconhecidas a 1–2 letras de uma palavra real."""
    achadas: list[str] = []
    for palavra in sorted(set(palavras_do_texto(texto))):
        formas = _formas(palavra)
        if any(f in conhecidas or f in corretor for f in formas):
            continue
        correcao = _correcao(corretor, formas[-1])
        if not correcao or correcao in formas:
            continue
        # O dicionário conhece «samaritano» mas não «samaritana»: a troca
        # a→o é concordância de género, não gralha.
        if formas[-1].endswith('a') and correcao == formas[-1][:-1] + 'o':
            continue
        limite = 2 if len(formas[-1]) >= 8 else 1
        if _distancia(formas[-1], correcao) <= limite:
            achadas.append(f'{palavra} → {correcao}?')
    return achadas


def _carregar_corretor():
    try:
        from spellchecker import SpellChecker
    except ImportError:
        return None
    return SpellChecker(language='pt')


def _conhecidas() -> set[str]:
    if not LISTA_CASA.exists():
        return set()
    return {linha.strip().casefold()
            for linha in LISTA_CASA.read_text(encoding='utf-8').splitlines()
            if linha.strip() and not linha.startswith('#')}


def relatorio(pasta: Path, rigoroso: bool) -> int:
    corretor = _carregar_corretor()
    if corretor is None:
        print('pyspellchecker não instalado; verificação ortográfica saltada.')
        return 0
    conhecidas = _conhecidas()
    total = 0
    for numero, dados in sorted(ler_todos(pasta).items()):
        livro = POR_NUMERO.get(numero)
        nome = livro.nome if livro else str(numero)
        for zona in ('chapters', 'in_progress'):
            for capitulo, versiculos in sorted(
                    dados.get(zona, {}).items(), key=lambda kv: int(kv[0])):
                for verso in versiculos:
                    achadas = suspeitas(
                        f"{verso.get('text', '')} {verso.get('commentary', '')}",
                        corretor, conhecidas)
                    if achadas:
                        total += 1
                        print(f'  {nome} {capitulo}:{verso.get("verse")}: '
                              + '; '.join(achadas))
    if total:
        print(f'\nOrtografia: {total} versículo(s) com palavras suspeitas '
              '(alerta — confirmar à mão).')
    else:
        print('\nOrtografia: nenhuma palavra suspeita.')
    return 1 if (rigoroso and total) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json')
    parser.add_argument('--rigoroso', action='store_true',
                        help='suspeitos fazem sair com código 1')
    args = parser.parse_args()
    if not args.dados.exists():
        print(f'Pasta de dados não encontrada: {args.dados}', file=sys.stderr)
        return 2
    return relatorio(args.dados, args.rigoroso)


if __name__ == '__main__':
    raise SystemExit(main())
