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
import unicodedata
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


def _cabecalho_estado(dados: dict) -> str:
    blocos = (dados.get('review') or {}).get('editorial_blocks') or []
    if blocos and all(str(b.get('status') or '').startswith('aprovado') for b in blocos):
        editorial = ('**Estado editorial:** aprovado pelo responsável em todos os capítulos. ')
    else:
        editorial = ('**Estado editorial (a aprovar por bloco):** cada capítulo está em `rascunho` '
                     'até aprovação do responsável. ')
    return (editorial + '**Revisão especializada: pendente para todos os capítulos.** '
            'O texto segue a base grega SBLGNT; a crítica textual vem do aparato e da colação CNTR.')


def _sem_acentos_nome(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', texto)
                   if not unicodedata.combining(c)).lower()


def _colacao(nome: str) -> Path | None:
    """Ficheiro de colação do livro em docs/colacao/, se existir."""
    alvo = _sem_acentos_nome(nome.replace(' ', '_')) + '.json'
    for caminho in sorted((RAIZ / 'docs' / 'colacao').glob('*.json')):
        if _sem_acentos_nome(caminho.name) == alvo:
            return caminho
    return None


def _rodape(dados: dict, livro) -> str:
    """Fontes do livro, só as que estão nos dados ou nos ficheiros."""
    partes = []
    if livro.numero >= 470:
        revisao = (dados.get('sources') or {}).get('sblgnt_commit')
        ref = f' (revisão `{revisao[:8]}`)' if revisao else ''
        partes.append(f'Base grega: [SBLGNT](../../docs/SBLGNT.md){ref}, CC BY 4.0. '
                      'Textus Receptus de Scrivener só como comparação, quando a colação o regista.')
    else:
        partes.append('Base hebraica: WLC, Open Scriptures Hebrew Bible (CC BY 4.0).')
    caminho = _colacao(livro.nome)
    if caminho:
        partes.append(f'Colação: `docs/colacao/{caminho.name}` (livro inteiro, gerada por '
                      f'`scripts/colar.py --livro {livro.numero}`).')
    else:
        partes.append('Colação de manuscritos: ainda não gerada para este livro.')
    ministerio = str(((dados.get('review') or {}).get('ministerio') or {}).get('status') or 'pendente')
    partes.append('Tradução e notas: revisão editorial pelo responsável; revisão especializada pendente; '
                  + ('revisão aprovada pelo ministério.' if ministerio.startswith('aprovado')
                     else 'revisão aprovada pelo ministério pendente.'))
    return ' '.join(partes)


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
        _cabecalho_estado(dados),
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
            linhas.append(f'**{v["verse"]}** {_md(v["text"])}')
            linhas.append('')

    linhas += ['## Notas', '']
    for c in capitulos:
        linhas += [f'### Notas do capítulo {c}', '']
        for v in dados['chapters'][str(c)]:
            if not v.get('commentary'):
                continue  # versículo sem nota: só aparece no texto
            linhas.append(f'**{c}:{v["verse"]}**')
            linhas.append('')
            for rotulo, texto in _notas(v['commentary']):
                if rotulo:
                    linhas.append(f'- **{rotulo}.** {texto}')
                else:
                    linhas.append(f'- {texto}')
            linhas.append('')

    linhas += ['---', '', _rodape(dados, livro), '']
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
