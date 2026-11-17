#!/usr/bin/env python3
"""Verifica a integridade dos dados versionados em `livros_json/`.

Corre sem rede e sem chaves. Sai com código 1 se encontrar um problema que
possa fazer desaparecer versículos já produzidos (a causa da execução #12).

Uso:
    python3 scripts/verificar_dados.py
    python3 scripts/verificar_dados.py --minimo 18
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _numeros(versiculos: list[dict]) -> list[int]:
    return [v.get('verse') for v in versiculos if isinstance(v, dict)]


def verificar(dados: Path) -> tuple[int, int, list[str]]:
    problemas: list[str] = []
    capitulos = versiculos = 0
    for caminho in sorted(dados.glob('*.json')):
        try:
            livro = json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, ValueError) as exc:
            problemas.append(f'{caminho.name}: JSON ilegível ({exc})')
            continue
        if not isinstance(livro, dict):
            problemas.append(f'{caminho.name}: o topo não é um objeto')
            continue
        for secao in ('chapters', 'in_progress'):
            bloco = livro.get(secao, {})
            if not isinstance(bloco, dict):
                problemas.append(f'{caminho.name}: {secao} não é um objeto')
                continue
            for chave, lista in bloco.items():
                if not chave.isdigit():
                    problemas.append(f'{caminho.name}: capítulo inválido {chave!r}')
                    continue
                if not isinstance(lista, list) or not lista:
                    problemas.append(f'{caminho.name} {chave}: lista vazia')
                    continue
                numeros = _numeros(lista)
                esperado = list(range(1, len(numeros) + 1))
                if numeros != esperado:
                    problemas.append(
                        f'{caminho.name} {chave}: versículos fora de sequência '
                        f'({numeros[:6]}…, {len(numeros)} no total)'
                    )
                for versiculo in lista:
                    if not isinstance(versiculo, dict):
                        problemas.append(f'{caminho.name} {chave}: versículo não é objeto')
                        continue
                    if not str(versiculo.get('text') or '').strip():
                        problemas.append(
                            f'{caminho.name} {chave}:{versiculo.get("verse")}: texto vazio'
                        )
                    if not str(versiculo.get('commentary') or '').strip():
                        problemas.append(
                            f'{caminho.name} {chave}:{versiculo.get("verse")}: comentário vazio'
                        )
                if secao == 'chapters':
                    capitulos += 1
                    versiculos += len(lista)
    return capitulos, versiculos, problemas


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados', default='livros_json')
    parser.add_argument('--minimo', type=int, default=0,
                        help='mínimo de capítulos completos (protege contra regressões)')
    args = parser.parse_args(argv)
    dados = Path(args.dados)
    if not dados.is_dir():
        print(f'ERRO: {dados} não existe', file=sys.stderr)
        return 1
    capitulos, versiculos, problemas = verificar(dados)
    print(f'{dados}: {capitulos} capítulos completos, {versiculos} versículos')
    if capitulos < args.minimo:
        problemas.append(
            f'regressão: {capitulos} capítulos, abaixo do mínimo de {args.minimo}'
        )
    if problemas:
        for problema in problemas:
            print(f'ERRO: {problema}', file=sys.stderr)
        return 1
    print('Dados íntegros.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
