#!/usr/bin/env python3
"""Verifica que a documentação principal não contradiz os dados versionados.

Corre sem rede e sem chaves. É usado no CI proposto em `docs/ci.yml`.
"""
from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_todos  # noqa: E402  (precisa da raiz no sys.path)


def numeros_reais() -> tuple[int, int, int, int]:
    livros = ler_todos(RAIZ / 'livros_json')
    capitulos = sum(len(item['chapters']) for item in livros.values())
    completos = sum(len(v) for item in livros.values() for v in item['chapters'].values())
    em_curso = sum(len(v) for item in livros.values() for v in item.get('in_progress', {}).values())
    return capitulos, completos, em_curso, completos + em_curso


def verificar() -> list[str]:
    problemas: list[str] = []
    capitulos, completos, em_curso, guardados = numeros_reais()
    if (capitulos, completos) != (18, 766):
        problemas.append(
            f'dados: esperava 18 capítulos e 766 versículos completos; '
            f'encontrei {capitulos} e {completos}.'
        )
    readme = (RAIZ / 'README.md').read_text(encoding='utf-8')
    for texto in (f'{capitulos} capítulos', f'{guardados} versículos guardados', '1.189', '31.102'):
        if texto not in readme:
            problemas.append(f'README.md: falta a referência actual {texto!r}.')
    # Números de versões antigas que já induziram o utilizador em erro.
    proibidos = ('5/1189', '5/1.189', '71 testes', '91 testes', 'repositório privado')
    for nome in ('README.md', 'docs/ESTADO.md', 'docs/OPERACAO.md', 'docs/ARQUITETURA.md', 'docs/EDITORIAL.md'):
        texto = (RAIZ / nome).read_text(encoding='utf-8')
        for velho in proibidos:
            if velho in texto:
                problemas.append(f'{nome}: ainda contém {velho!r}.')
    if em_curso and f'{guardados}' not in readme:
        problemas.append('README.md: não distingue versículos completos dos que estão em curso.')
    return problemas


def main() -> int:
    problemas = verificar()
    if problemas:
        for problema in problemas:
            print(f'ERRO: {problema}', file=sys.stderr)
        return 1
    capitulos, completos, em_curso, guardados = numeros_reais()
    print(
        f'Documentação coerente: {capitulos} capítulos completos, '
        f'{completos} versículos completos, {em_curso} em curso, {guardados} guardados.'
    )
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
