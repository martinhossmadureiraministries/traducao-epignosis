#!/usr/bin/env python3
"""Lapidação automática (mecânica) de um capítulo já gravado.

A mesma lapidação que a agenda corre sozinha ao fechar um capítulo
(``bee/lapidador.py``), aqui à mão para qualquer capítulo — fechado ou
em curso — da edição nova. Normaliza a forma das notas, regenera a
Crítica Textual do relatório de colação e corrige a pontuação
mecânica; reporta o que exige juízo (secções em falta, grego misto).

Uso:
    python3 scripts/lapidar.py 500 4            # João 4 (aplica e guarda)
    python3 scripts/lapidar.py 500 4 --verificar
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.catalogo import POR_NUMERO  # noqa: E402
from bee.lapidador import lapidar_versos  # noqa: E402

DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('livro', type=int, help='book_number (ex.: 500)')
    ap.add_argument('capitulo', type=int)
    ap.add_argument('--verificar', action='store_true',
                    help='confere sem escrever')
    args = ap.parse_args()

    livro = POR_NUMERO.get(args.livro)
    caminho = next(DADOS.glob(f'{args.livro}_*.json'), None)
    if livro is None or caminho is None:
        print(f'Livro {args.livro} não encontrado.', file=sys.stderr)
        return 2
    dados = json.loads(caminho.read_text(encoding='utf-8'))
    zona = None
    for candidata in ('chapters', 'in_progress'):
        if str(args.capitulo) in dados.get(candidata, {}):
            zona = candidata
            break
    if zona is None:
        print(f'{livro.nome} {args.capitulo}: capítulo não encontrado.',
              file=sys.stderr)
        return 2

    colacao = None
    relatorio_col = RAIZ / 'docs' / 'colacao' / f'{livro.nome}.json'
    if relatorio_col.exists():
        colacao = json.loads(relatorio_col.read_text(encoding='utf-8'))

    versiculos = dados[zona][str(args.capitulo)]
    novos, relatorio, problemas = lapidar_versos(
        versiculos, args.capitulo, colacao)
    for linha in relatorio:
        print(' ', linha)
    for problema in problemas:
        print('  PROBLEMA:', problema)
    if problemas:
        return 1
    if novos == versiculos:
        print(f'\nOK: {livro.nome} {args.capitulo} já lapidado.')
        return 0
    if args.verificar:
        print(f'\n{livro.nome} {args.capitulo}: há normalizações por aplicar.')
        return 1
    dados[zona][str(args.capitulo)] = novos
    dados.setdefault('history', []).append({
        'chapter': args.capitulo, 'verse_from': 1,
        'verse_to': len(novos), 'provider': 'local',
        'model': 'editorial:lapidacao-automatica',
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
    })
    temporario = caminho.with_suffix('.tmp')
    with temporario.open('w', encoding='utf-8') as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    os.replace(temporario, caminho)
    print(f'\nOK: {len(relatorio)} normalizações aplicadas a '
          f'{livro.nome} {args.capitulo}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
