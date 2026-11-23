#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compila os módulos MyBible a partir da edição nova e mostra o estado dos JSON.

Sem IA, sem chaves de API e sem rede. A produção por IA foi retirada do repositório
(decisão de 2026-11-23); o texto novo é escrito e revisado à mão, livro a livro.

Uso:
    python3 gerar_bee.py --listar-livros
    python3 gerar_bee.py --status --dados edicoes/nova/livros_json
    python3 gerar_bee.py --compilar --dados edicoes/nova/livros_json --saida entregas/nova
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

from bee.arquivos import DadosInvalidos, ler_todos
from bee.catalogo import LIVROS
from bee.compilador import ErroCompilacao, compilar


def argumentos(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Compila os módulos MyBible e mostra o estado da edição nova.')
    acao = parser.add_mutually_exclusive_group(required=True)
    acao.add_argument('--compilar', action='store_true', help='compila os JSON completos em módulos SQLite3')
    acao.add_argument('--listar-livros', action='store_true', help='lista os 66 números e totais de capítulos')
    acao.add_argument('--status', action='store_true', help='mostra o progresso local dos JSON')
    parser.add_argument('--dados', type=Path, default=Path('edicoes/nova/livros_json'), metavar='PASTA',
                        help='pasta dos JSON (padrão: edicoes/nova/livros_json)')
    parser.add_argument('--saida', type=Path, default=Path('.'), metavar='PASTA',
                        help='pasta dos módulos SQLite3 (padrão: atual)')
    return parser.parse_args(argv)


def _listar() -> None:
    for livro in LIVROS:
        print(f'{livro.numero:03d}  {livro.nome:<22} {livro.capitulos:3d} capítulos  {livro.nome_arquivo}')
    print(f'Total: {len(LIVROS)} livros, {sum(l.capitulos for l in LIVROS)} capítulos.')


def _status(diretorio: Path) -> None:
    dados = ler_todos(diretorio)
    for livro in LIVROS:
        item = dados.get(livro.numero, {})
        completos = len(item.get('chapters', {}))
        parciais = len(item.get('in_progress', {}))
        sufixo = f' (+{parciais} em andamento)' if parciais else ''
        print(f'{livro.numero:03d}  {livro.nome:<22} {completos:3d}/{livro.capitulos:<3}{sufixo}')
    completo = sum(len(item['chapters']) for item in dados.values())
    print(f'Total: {completo}/1189 capítulos estruturalmente completos; a revisão editorial não é verificada.')


def _compilar(dados: Path, saida: Path) -> None:
    resumo = compilar(dados, saida)
    estado = 'completo' if resumo['completo'] else 'PARCIAL'
    print(
        f"Módulos {estado}: {resumo['livros']}/66 livros, {resumo['capitulos']}/1189 capítulos, "
        f"{resumo['versiculos']} versículos."
    )
    if resumo['parciais']:
        print(f"{resumo['parciais']} capítulo(s) em andamento não foram compilados.")
    if resumo['lacunas_fonte']:
        print(f"ATENÇÃO: {resumo['lacunas_fonte']} versículo(s) contêm marcadores de fonte ausente; verifique-os.")
    print(f"Ficheiros: {saida / 'BEE.SQLite3'} e {saida / 'BEE.commentaries.SQLite3'}")


def main(argv: list[str] | None = None) -> int:
    args = argumentos(argv)
    try:
        if args.listar_livros:
            _listar()
        elif args.status:
            _status(args.dados)
        else:
            _compilar(args.dados, args.saida)
        return 0
    except (DadosInvalidos, ErroCompilacao, OSError) as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
