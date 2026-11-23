#!/usr/bin/env python3
"""Gera a leitura em Markdown de um livro a partir do seu JSON (edição nova).

O texto e as notas são lidos do JSON; o Markdown nunca é editado à mão. Por
isso o ficheiro mantém-se sincronizado com os dados. O ficheiro cresce capítulo
a capítulo: gera-se sempre o livro inteiro, com os capítulos que já existem.

    python3 scripts/gerar_leitura_livro.py --livro 500 \\
        --dados edicoes/nova/livros_json --saida edicoes/nova/JOAO.md

Não aprova nada: o estado de cada capítulo é o que está em
``review.editorial_blocks`` do JSON. A revisão especializada fica sempre
registada como pendente.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.catalogo import POR_NUMERO  # noqa: E402

# Formato único: prosa por versículo; só a Crítica Textual tem rótulo.
PARAGRAFO = re.compile(r'<p>(.*?)</p>', re.S)
ROTULO = re.compile(r'^<b>(Crítica Textual):</b>\s*(.*)$', re.S)


def _md(trecho: str) -> str:
    """HTML simples da BEE (b, i) para Markdown; o resto é texto."""
    t = re.sub(r'<i>(.*?)</i>', r'*\1*', trecho, flags=re.S)
    t = re.sub(r'<b>(.*?)</b>', r'**\1**', t, flags=re.S)
    t = re.sub(r'<[^>]+>', '', t)
    return html.unescape(t).strip()


def _notas(comentario: str) -> list[tuple[str, str]]:
    """Devolve [(rótulo, texto)] na ordem em que aparecem no JSON."""
    saida = []
    for par in PARAGRAFO.findall(comentario):
        m = ROTULO.match(par.strip())
        if m:
            saida.append((m.group(1), _md(m.group(2))))
        else:
            saida.append(('', _md(par)))
    return saida


def _estado(dados: dict, capitulo: int) -> str:
    for bloco in dados['review']['editorial_blocks']:
        if bloco['chapter'] == capitulo:
            return bloco['status']
    return 'sem estado'


def _intervalo(capitulos: list[int]) -> str:
    return ', '.join(str(c) for c in capitulos)


def gerar(dados: dict) -> str:
    livro = POR_NUMERO[dados['book_number']]
    nome = dados['book_name']
    capitulos = sorted(int(c) for c in dados['chapters'])
    total_versos = sum(len(dados['chapters'][str(c)]) for c in capitulos)

    linhas = [
        f'# {nome} · Bíblia de Estudo Epignósis',
        '',
        f'Leitura em Markdown gerada a partir de `edicoes/nova/livros_json/` '
        f'({dados["book_number"]}). Capítulos disponíveis: {_intervalo(capitulos)}, '
        f'{total_versos} versículos.',
        '',
        '**Estado editorial (a aprovar por bloco):** cada capítulo está em `rascunho` '
        'até aprovação do responsável. **Revisão especializada: pendente para todos os capítulos.** '
        'O texto segue a base grega SBLGNT; a crítica textual vem do aparato e da colação CNTR.',
        '',
        '| Capítulo | Estado | Versículos |',
        '|---|---|---|',
    ]
    for c in capitulos:
        linhas.append(f'| {c} | {_estado(dados, c)} | {len(dados["chapters"][str(c)])} |')
    linhas += ['', '## Texto', '']

    for c in capitulos:
        linhas += [f'### Capítulo {c}', '']
        for v in dados['chapters'][str(c)]:
            linhas.append(f'**{v["verse"]}** {v["text"]}')
            linhas.append('')

    linhas += ['## Notas', '']
    for c in capitulos:
        linhas += [f'### Notas do capítulo {c}', '']
        for v in dados['chapters'][str(c)]:
            linhas.append(f'**{c}:{v["verse"]}**')
            linhas.append('')
            for rotulo, texto in _notas(v['commentary']):
                if rotulo:
                    linhas.append(f'- **{rotulo}.** {texto}')
                else:
                    linhas.append(f'- {texto}')
            linhas.append('')

    linhas += [
        '---',
        '',
        f'Base grega: [SBLGNT]({"../../docs/SBLGNT.md"}) (revisão `{dados["sources"]["sblgnt_commit"][:8]}`, CC BY 4.0). '
        'Textus Receptus de Scrivener só como comparação, quando a colação o regista. '
        'Colação: `docs/colacao/João.json` (livro inteiro, gerada por `scripts/colar.py --livro 500`). '
        'Tradução e notas: revisão editorial pelo responsável; revisão especializada pendente.',
        '',
    ]
    return '\n'.join(linhas)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--livro', type=int, required=True, help='número BEE do livro (ex.: 500)')
    ap.add_argument('--dados', type=Path, default=RAIZ / 'edicoes/nova/livros_json')
    ap.add_argument('--saida', type=Path, required=True)
    args = ap.parse_args()
    ficheiros = sorted(args.dados.glob(f'{args.livro:03d}_*.json'))
    if len(ficheiros) != 1:
        raise SystemExit(f'Esperado um JSON para o livro {args.livro}; encontrados {len(ficheiros)}.')
    dados = json.loads(ficheiros[0].read_text(encoding='utf-8'))
    args.saida.write_text(gerar(dados), encoding='utf-8')
    print(f'escrito: {args.saida}')


if __name__ == '__main__':
    main()
