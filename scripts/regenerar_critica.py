#!/usr/bin/env python3
"""Regenera a Crítica Textual de um livro a partir do aparato e da colação.

Para cada versículo, a parágrafo «Crítica Textual» é reescrito só com factos:

* as leituras do aparato da SBLGNT, com as edições que as sustentam (WH, Treg,
  NA28, RP, NIV…); a base é sempre o lado esquerdo de cada entrada;
* a comparação com o Textus Receptus de Scrivener, feita sobre a colação
  (`docs/colacao/<livro>.json`): coincide, ou diverge com a primeira diferença;
* a decisão (segue a base) e o nível de certeza, por regra fixa:
  - **A**: as três edições críticas (WH, Treg, NA28) estão de acordo em cada
    entrada, ou não há entrada; uma alternativa só aparece em RP/NIV;
  - **B**: alguma entrada tem WH, Treg ou NA28 divididos entre a base e a
    alternativa;
  - **C**: reservado para decisão manual (este script não o atribui).

Remove também resíduos de processo do comentário: blocos «Nota de redação»,
que descrevem a história da redação e não pertencem ao texto para leitura.
Os parágrafos Análise Léxica e Síntese Exegética não são tocados, exceto o
realce de palavras gregas (passa de negrito a itálico).

Por defeito só mostra o que faria; `--aplicar` escreve o JSON.

Uso:
    python3 scripts/regenerar_critica.py --dados edicoes/nova/livros_json/500_Joao.json \
        --colacao docs/colacao/João.json --capitulos 1-4 [--aplicar]
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bee.grego import italico_grego  # noqa: E402

SIGLAS_CRITICAS = ('WH', 'Treg', 'NA28')
SIGLAS = ('WH', 'Treg', 'NA28', 'RP', 'NIV', 'ST', 'SR', 'KJTR', 'Scrivener')
SEP = '\xa0]\xa0'
GREGO = re.compile(r'[\u0370-\u03ff\u1f00-\u1fff]')


def _siglas_e_texto(parte: str) -> tuple[str, list[str]]:
    """Separa «texto siglas…» em (texto, [siglas])."""
    toks = parte.replace('\xa0', ' ').split()
    sig: list[str] = []
    while toks and toks[-1].rstrip(';') in SIGLAS + ('Holmes', 'WHmarg'):
        sig.insert(0, toks.pop().rstrip(';'))
    return ' '.join(toks), sig


def _entradas(aparato: list[str]) -> list[dict]:
    """Converte as linhas do aparato em {base, alt[]} com siglas."""
    saida = []
    for linha in aparato:
        linha = linha.replace('•', ' ').replace('\xa0', ' ').strip()
        linha = re.sub(r'^\d+:\d+\s+|^\d+\s+', '', linha)  # número do versículo
        if ' ] ' not in linha:
            continue
        esq, dir_ = linha.split(' ] ', 1)
        texto_b, sig_b = _siglas_e_texto(esq)
        alternativas = []
        for parte in dir_.split(';'):
            txt, sig = _siglas_e_texto(parte.strip())
            if sig:
                alternativas.append((txt, sig))
        saida.append({'base': (texto_b, sig_b), 'alt': alternativas})
    return saida


def _descreve(txt: str, sig: list[str]) -> str:
    plural = len(sig) > 1
    nomes = ', '.join(sig[:-1]) + (' e ' + sig[-1] if plural else sig[0] if sig else '')
    if txt in ('–', '-', ''):
        return f"{nomes} {'omitem' if plural else 'omite'}"
    if txt.startswith('+'):
        return f"{nomes} {'acrescentam' if plural else 'acrescenta'} «{txt.lstrip('+ ').strip()}»"
    return f"{nomes} {'lêem' if plural else 'lê'} «{txt}»"


def _nivel(entradas: list[dict]) -> str:
    """A se WH, Treg e NA28 estão do mesmo lado de cada entrada; B se se dividem."""
    nivel = 'A'
    for e in entradas:
        lados = [(0, e['base'][1])] + [(1, s) for _, s in e['alt']]
        lado_de: dict[str, set[int]] = {}
        for indice, sig in lados:
            for s in sig:
                if s in SIGLAS_CRITICAS:
                    lado_de.setdefault(s, set()).add(indice)
        lados_usados = set().union(*lado_de.values()) if lado_de else set()
        if len(lados_usados) > 1:
            nivel = 'B'
    return nivel


def _frase_entrada(e: dict) -> str:
    partes = [_descreve(*e['base'])] + [_descreve(txt, sig) for txt, sig in e['alt']]
    return '; '.join(partes)


def _tr(base: dict) -> str:
    """Compara base e TR sobre as formas normalizadas da colação (sem acento)."""
    if base['sblgnt_norm'] == base['scrivener_norm']:
        return 'O Textus Receptus de Scrivener coincide com a base.'
    a, b = base['sblgnt_norm'], base['scrivener_norm']
    marcas = []
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b).get_opcodes():
        if op == 'equal':
            continue
        onde = ' '.join(a[i1:i2])
        tr = ' '.join(b[j1:j2])
        if not onde:
            marcas.append(f'TR acrescenta «{tr}»')
        elif not tr:
            marcas.append(f'TR omite «{onde}»')
        else:
            marcas.append(f'TR «{tr}» onde a base lê «{onde}»')
    total = len(marcas)
    resumo = '; '.join(marcas[:2]) + ('; …' if total > 2 else '')
    return (f'O Textus Receptus de Scrivener diverge da base em {total} ponto(s) '
            f'(formas sem acento, como na colação: {resumo}).')


def critica(verso_ref: str, colacao_base: dict) -> tuple[str, str]:
    base = colacao_base['base']
    entradas = _entradas(base.get('aparato_sblgnt') or [])
    if entradas:
        if len(entradas) == 1:
            partes = [f'Aparato SBLGNT: {_frase_entrada(entradas[0])}.']
        else:
            partes = ['Aparato SBLGNT: ' + ' '.join(f'({i}) {_frase_entrada(e)}.'
                                                    for i, e in enumerate(entradas, 1))]
        decisao = 'O texto segue a base SBLGNT.'
    else:
        partes = ['O aparato da SBLGNT não regista variante neste versículo.']
        decisao = 'O texto segue a base SBLGNT.'
    nivel = _nivel(entradas) if entradas else 'A'
    ct = ' '.join(partes + [_tr(base), decisao, f'Nível de certeza {nivel}.'])
    return ct, nivel


def _sem_residuos(com: str) -> str:
    com = re.sub(r'<p><b>Nota de redação:</b>.*?</p>', '', com, flags=re.S)
    com = re.sub(r'<b>(\s*)(' + GREGO.pattern + r'[^<]*?)(\s*)</b>',
                 lambda m: f'<i>{m.group(2)}</i>', com)
    return com


def _substituir_ct(com: str, nova: str) -> str:
    padrao = re.compile(r'<p><b>Crítica Textual:</b>.*?</p>', re.S)
    bloco = f'<p><b>Crítica Textual:</b> {nova}</p>'
    if padrao.search(com):
        return padrao.sub(lambda _m: bloco, com, count=1)
    return com + bloco


def _intervalo(texto: str) -> set[int]:
    if not texto:
        return set()
    a, _, b = texto.partition('-')
    return set(range(int(a), int(b or a) + 1))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dados', required=True, type=Path)
    ap.add_argument('--colacao', required=True, type=Path)
    ap.add_argument('--capitulos', default='', help='ex.: 1-4 (vazio = todos)')
    ap.add_argument('--aplicar', action='store_true')
    args = ap.parse_args(argv)
    dados = json.loads(args.dados.read_text(encoding='utf-8'))
    colacao = json.loads(args.colacao.read_text(encoding='utf-8'))['versiculos']
    caps = _intervalo(args.capitulos)
    alterados = 0
    for cap, lista in dados['chapters'].items():
        if caps and int(cap) not in caps:
            continue
        for verso in lista:
            ref = f"{cap}:{verso['verse']}"
            if ref not in colacao:
                raise SystemExit(f'{ref} sem registo na colação')
            com = _sem_residuos(verso.get('commentary') or '')
            ct, _nivel_ref = critica(ref, colacao[ref])
            novo = italico_grego(_substituir_ct(com, ct))
            if novo != verso.get('commentary'):
                alterados += 1
                verso['commentary'] = novo
    print(f'versículos com nota alterada: {alterados}')
    if args.aplicar:
        args.dados.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('escrito:', args.dados)
    else:
        print('(simulação: use --aplicar para escrever)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
