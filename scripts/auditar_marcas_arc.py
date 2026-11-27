#!/usr/bin/env python3
"""Mede as marcas de «cara de ARC» nos JSON da edição nova.

Não compara com a ARC nem com nenhuma outra versão: conta construções que
caracterizam a sintaxe e o ritmo da Almeida (fórmulas, aberturas com «e»,
«eis que», «em verdade, em verdade», cadeias de «e», «o qual»…). Serve para
decidir onde a revisão de estilo deve começar. Um número alto não é erro: é
um sinal para ler com atenção, porque algumas marcas são legítimas
(«em verdade», por exemplo, é a fórmula do Evangelho segundo João).

Uso:
    python3 scripts/auditar_marcas_arc.py                 # tabela no terminal
    python3 scripts/auditar_marcas_arc.py --saida docs/revisao/MARCAS_ARC.md
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json'

# Cada marca: rótulo legível, expressão regular aplicada ao texto em minúsculas.
MARCAS = {
    'Bendito seja (fórmula de bênção)': r'\bbendito[s]? seja',
    'Em verdade, em verdade': r'em verdade, em verdade',
    'Eis / eis que': r'\beis\b',
    'Sucedeu / aconteceu': r'\b(sucedeu|aconteceu)\b',
    'Havia entre / havia (abertura)': r'^havia\b|\bhavia entre\b',
    'o qual / os quais (relativo)': r'\b(o|a|os|as) (qual|quais)\b',
    # «sede» fica de fora: é também substantivo (sede de água, João 4:13).
    'Tende (imperativo antigo)': r'\btende\b',
    'Porventura / outrossim / deveras': r'\b(porventura|outrossim|sobremaneira|deveras)\b',
    'Versículo começa com «E»': r'^e\b',
    'Versículo começa com «Pois»': r'^pois\b',
    'Versículo começa com «Porque»': r'^porque\b',
}
# Cadeia de quatro ou mais conjunções «e» (polissíndeto) numa só frase do versículo.
RE_E_CONJUNCAO = re.compile(r'(?:^|[ ,;])e (?=[a-zàáâãéêíóôõúç])')


def contar(dados_dir: Path = DADOS):
    total = 0
    por_marca: collections.Counter = collections.Counter()
    por_livro: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    exemplos: dict[str, list[str]] = collections.defaultdict(list)
    compilados = {rotulo: re.compile(padrao) for rotulo, padrao in MARCAS.items()}
    for ficheiro in sorted(glob.glob(str(dados_dir / '*.json'))):
        d = json.loads(Path(ficheiro).read_text(encoding='utf-8'))
        nome = d['book_name']
        for capitulo, versiculos in d['chapters'].items():
            for v in versiculos:
                total += 1
                texto = v['text'].lower()
                referencia = f"{nome} {capitulo}:{v['verse']}"
                achados = [r for r, rx in compilados.items() if rx.search(texto)]
                if len(RE_E_CONJUNCAO.findall(texto)) >= 4:
                    achados.append('Quatro ou mais «e» no versículo')
                for rotulo in achados:
                    por_marca[rotulo] += 1
                    por_livro[nome][rotulo] += 1
                    if len(exemplos[rotulo]) < 3:
                        exemplos[rotulo].append(referencia)
    return total, por_marca, por_livro, exemplos


def relatorio(total, por_marca, por_livro, exemplos) -> str:
    linhas = [
        '# Marcas de estilo ARC na edição nova',
        '',
        f'Gerado por `scripts/auditar_marcas_arc.py` sobre {total} versículos. '
        'Mede construções, não erros: um número alto pede leitura, não correção automática.',
        '',
        '## Totais por marca',
        '',
        '| Marca | Versículos | Exemplos |',
        '|---|---:|---|',
    ]
    for rotulo, n in por_marca.most_common():
        linhas.append(f"| {rotulo} | {n} | {', '.join(exemplos[rotulo])} |")
    linhas += ['', '## Livros com mais marcas', '', '| Livro | Marcas (ocorrências) |', '|---|---|']
    ordenados = sorted(por_livro.items(), key=lambda kv: -sum(kv[1].values()))
    for nome, c in ordenados:
        resumo = ', '.join(f'{r}: {n}' for r, n in c.most_common())
        linhas.append(f'| {nome} | {resumo} |')
    return '\n'.join(linhas) + '\n'


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[1])
    ap.add_argument('--dados', type=Path, default=DADOS)
    ap.add_argument('--saida', type=Path, help='escreve o relatório Markdown neste ficheiro')
    args = ap.parse_args()
    texto = relatorio(*contar(args.dados))
    if args.saida:
        args.saida.parent.mkdir(parents=True, exist_ok=True)
        args.saida.write_text(texto, encoding='utf-8')
        print(f'Relatório gravado em {args.saida}')
    else:
        sys.stdout.write(texto)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
