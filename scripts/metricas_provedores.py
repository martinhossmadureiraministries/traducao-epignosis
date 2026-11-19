#!/usr/bin/env python3
"""Métricas de qualidade por provedor (P3): deriva, revisões e confiança.

Resume, a partir do que está gravado na pasta de dados, o desempenho de cada
provedor: versículos gerados, chumbos da porta de estilo, emendas recebidas do
revisor de voz e capítulos que reviu. A taxa «chumbos/100» é o número que
compara a confiança entre serviços — serve para o relatório e, com
`BEE_PRIORIDADES=metricas`, para ordenar os revisores.

Corre offline; nunca escreve fora da pasta `.bee` (ignorada pelo Git), exceto
com `--json CAMINHO`.

Uso:
    python3 scripts/metricas_provedores.py                     # edição nova
    python3 scripts/metricas_provedores.py --dados livros_json # linha legada
    python3 scripts/metricas_provedores.py --sem-cache         # só imprime
    python3 scripts/metricas_provedores.py --json /tmp/m.json  # exporta
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.metricas import (  # noqa: E402
    guardar, recolher, tabela, ordenar_confianca, pontuacoes,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json',
                        help='pasta dos JSON (padrão: edição nova)')
    parser.add_argument('--sem-cache', action='store_true',
                        help='não escrever .bee/metricas.json')
    parser.add_argument('--json', type=Path, metavar='CAMINHO',
                        help='exportar as métricas completas para este ficheiro')
    args = parser.parse_args()
    if not args.dados.exists():
        print(f'Pasta de dados não encontrada: {args.dados}', file=sys.stderr)
        return 2
    metricas = recolher(args.dados)
    print(tabela(metricas))
    confianca = ordenar_confianca(metricas)
    if confianca:
        print('\nOrdem de confiança (menos deriva primeiro): ' + ' > '.join(confianca))
    if not args.sem_cache and metricas:
        destino = guardar(args.dados, metricas)
        print(f'\nCache para prioridades escrito em {destino.relative_to(RAIZ)}.')
    if args.json:
        exportacao = {'pontuacoes': pontuacoes(metricas), 'confianca': confianca,
                      'detalhe': {n: m.__dict__ for n, m in sorted(metricas.items())}}
        args.json.write_text(json.dumps(exportacao, ensure_ascii=False, indent=2) + '\n',
                             encoding='utf-8')
        print(f'Métricas exportadas para {args.json}.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
