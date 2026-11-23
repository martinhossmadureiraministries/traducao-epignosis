#!/usr/bin/env python3
"""Verifica a integridade dos dados versionados em `edicoes/nova/livros_json/`.

Corre sem rede e sem chaves. Sai com código 1 se encontrar um problema que
possa fazer desaparecer versículos já produzidos (a causa da execução #12).

Além das regressões, relata os versículos ainda marcados como pendentes: um
capítulo com marcadores conta como fechado para não se perder o que já existe,
mas não é texto para ler — e a contagem não deve fazer esquecer isso.

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


PENDENTE_PREFIXO = '[Versículo pendente:'


def _intervalos(numeros: list[int]) -> str:
    """«29-54», «2, 5-7»: as sequências aparecem comprimidas no relatório."""
    partes: list[str] = []
    inicio = anterior = None
    for numero in numeros:
        if inicio is None:
            inicio = anterior = numero
        elif numero == anterior + 1:
            anterior = numero
        else:
            partes.append(f'{inicio}-{anterior}' if anterior != inicio else str(inicio))
            inicio = anterior = numero
    if inicio is not None:
        partes.append(f'{inicio}-{anterior}' if anterior != inicio else str(inicio))
    return ', '.join(partes)


def pendentes(dados: Path) -> list[tuple[str, str, str]]:
    """Versículos por traduzir em capítulos dados como fechados."""
    achados: list[tuple[str, str, str]] = []
    for caminho in sorted(dados.glob('*.json')):
        try:
            livro = json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        for chave, lista in (livro.get('chapters') or {}).items():
            if not isinstance(lista, list):
                continue
            marcados = [v.get('verse') for v in lista
                        if isinstance(v, dict)
                        and str(v.get('text') or '').startswith(PENDENTE_PREFIXO)]
            marcados = [n for n in marcados if isinstance(n, int)]
            if marcados:
                achados.append((caminho.name, str(chave), _intervalos(sorted(marcados))))
    return achados


def pendentes_em_aprovados(dados: Path) -> list[str]:
    """Versículos pendentes dentro de um bloco de revisão já aprovado.

    Um rascunho pode ter pendentes e só é relatado. Um bloco «aprovado…» com
    versículos por traduzir é um erro: a aprovação foi dada sobre texto que
    não existe. Este caso chumba.
    """
    erros: list[str] = []
    for caminho in sorted(dados.glob('*.json')):
        try:
            livro = json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        blocos = [b for b in (livro.get('review') or {}).get('editorial_blocks') or []
                  if isinstance(b, dict) and str(b.get('status') or '').startswith('aprovado')]
        if not blocos:
            continue
        for chave, lista in (livro.get('chapters') or {}).items():
            if not isinstance(lista, list):
                continue
            for verso in lista:
                if not isinstance(verso, dict):
                    continue
                if not str(verso.get('text') or '').startswith(PENDENTE_PREFIXO):
                    continue
                n = verso.get('verse')
                for b in blocos:
                    if (str(b.get('chapter')) == str(chave)
                            and isinstance(n, int)
                            and b.get('verse_from', 0) <= n <= b.get('verse_to', -1)):
                        erros.append(f'{caminho.name} {chave}:{n} pendente dentro de bloco aprovado')
                        break
    return erros

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dados', default='edicoes/nova/livros_json')
    parser.add_argument('--minimo', type=int, default=0,
                        help='mínimo de capítulos completos (protege contra regressões)')
    args = parser.parse_args(argv)
    dados = Path(args.dados)
    if not dados.is_dir():
        print(f'ERRO: {dados} não existe', file=sys.stderr)
        return 1
    capitulos, versiculos, problemas = verificar(dados)
    print(f'{dados}: {capitulos} capítulos completos, {versiculos} versículos')
    marcados = pendentes(dados)
    for ficheiro, capitulo, intervalos in marcados:
        print(f'  pendente: {ficheiro} {capitulo}:{intervalos}')
    if marcados:
        quantos = len(marcados)
        print(f'{quantos} bloco{"s" if quantos > 1 else ""} de versículos pendentes: '
              'o capítulo conta como fechado, mas não é texto final.')
    problemas.extend(pendentes_em_aprovados(dados))
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
