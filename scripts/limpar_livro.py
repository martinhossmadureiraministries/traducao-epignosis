#!/usr/bin/env python3
"""Repõe um livro na fila de produção, apagando o que estava guardado.

Serve dois propósitos:

* Regenerar um livro cujo rascunho ficou aquém da voz BEE (o motor NÃO refaz
  capítulos completos; é preciso limpá-lo primeiro — foi o caso de 2 Tessalonicenses).
* Alimentar o ciclo de calibração «correr → guarda de estilo → repetir»: quando
  `scripts/verificar_estilo.py` chumba um livro, limpa-se esse livro e volta-se a
  correr até o guarda dar limpo.

O ficheiro é reescrito como um livro novo (metadados do catálogo, sem capítulos),
ficando «por fazer»; o agendador volta a pegá-lo desde o versículo 1. O texto
anterior não se perde — fica na história do Git. Corra depois
`scripts/verificar_dados.py --dados <pasta>` para confirmar a integridade.

Uso:
    python3 scripts/limpar_livro.py 600            # limpa 2 Tessalonicenses
    python3 scripts/limpar_livro.py 600 --dry-run  # mostra sem escrever
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_livro, novo_livro, salvar_livro  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402


def contar(dados: dict) -> tuple[int, int]:
    completos = sum(len(v) for v in dados.get('chapters', {}).values())
    em_curso = sum(len(v) for v in dados.get('in_progress', {}).values())
    return completos, em_curso


def limpar(numero: int, pasta: Path, dry_run: bool) -> int:
    livro = POR_NUMERO.get(numero)
    if livro is None:
        print(f'Book_number desconhecido: {numero}', file=sys.stderr)
        return 2
    caminho = pasta / livro.nome_arquivo
    if caminho.exists():
        antigos = ler_livro(caminho, livro)
        completos, em_curso = contar(antigos)
        antes = f'{completos} completos + {em_curso} em curso'
    else:
        antes = 'ficheiro inexistente (livro ainda por começar)'
    if dry_run:
        print(f'DRY-RUN {livro.nome} ({livro.nome_arquivo}): limparia [{antes}].')
        return 0
    pasta.mkdir(parents=True, exist_ok=True)
    salvar_livro(caminho, novo_livro(livro), livro)
    print(f'{livro.nome} ({livro.nome_arquivo}) reposto na fila — tinha [{antes}].')
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('livros', nargs='+', type=int, help='book_number a limpar')
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json',
                        help='pasta dos JSON (padrão: edição nova)')
    parser.add_argument('--dry-run', action='store_true', help='mostra sem escrever')
    args = parser.parse_args()
    codigos = [limpar(n, args.dados, args.dry_run) for n in args.livros]
    if not args.dry_run and any(c == 0 for c in codigos):
        print('\nConfira a integridade: '
              f'python3 scripts/verificar_dados.py --dados {args.dados}')
    return max(codigos) if codigos else 0


if __name__ == '__main__':
    raise SystemExit(main())
