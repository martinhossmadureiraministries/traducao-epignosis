#!/usr/bin/env python3
"""Verifica que a documentação principal não contradiz os dados versionados.

Corre sem rede e sem chaves. Não há CI ativa no repositório; corre-se à mão.
"""
from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_todos  # noqa: E402  (precisa da raiz no sys.path)


def numeros_reais() -> tuple[int, int, int, int]:
    livros = ler_todos(RAIZ / 'edicoes' / 'nova' / 'livros_json')
    capitulos = sum(len(item['chapters']) for item in livros.values())
    completos = sum(len(v) for item in livros.values() for v in item['chapters'].values())
    em_curso = sum(len(v) for item in livros.values() for v in item.get('in_progress', {}).values())
    return capitulos, completos, em_curso, completos + em_curso


def _sem_acentos(texto: str) -> str:
    return ''.join(c for c in unicodedata.normalize('NFKD', texto)
                   if not unicodedata.combining(c)).lower()


def livros_sem_json() -> list[str]:
    """Chaves (sem acentos) dos livros com MD na edição nova mas sem JSON."""
    nova = RAIZ / 'edicoes' / 'nova'
    com_json = {_sem_acentos(p.stem.split('_', 1)[1])
                for p in (nova / 'livros_json').glob('*.json')}
    sem = []
    for md in sorted(nova.glob('*.md')):
        if md.stem.upper().startswith(('LOTE_', 'CALIBRACAO')):
            continue
        chave = _sem_acentos(md.stem)
        if chave not in com_json:
            sem.append(chave)
    return sem


def entregas_sem_json() -> list[str]:
    """Um livro sem JSON não pode ser declarado «entregue» nos registos.

    Só se apanha o particípio («entregue», «entregues»): a palavra «entrega»
    como plano futuro ou processo não é uma declaração. A entrega de um livro
    pressupõe o JSON, de onde sai o módulo; os MD sem JSON podem ser lidos e
    revistos, mas não entregues.
    """
    sem = livros_sem_json()
    if not sem:
        return []
    alvos = [RAIZ / 'docs' / 'ESTADO.md', RAIZ / 'docs' / 'EDICAO_NOVA.md']
    alvos += sorted((RAIZ / 'edicoes' / 'nova').glob('LOTE_*.md'))
    problemas = []
    for ficheiro in alvos:
        for numero, linha in enumerate(ficheiro.read_text(encoding='utf-8').splitlines(), 1):
            n = _sem_acentos(linha)
            if not re.search(r'\bentregues?\b', n):
                continue
            for chave in sem:
                if re.search(rf'\b{re.escape(chave)}\b', n):
                    problemas.append(
                        f'{ficheiro.relative_to(RAIZ)}:{numero}: «entregue» para '
                        f'{chave} sem JSON (ver docs/arquivo/PLANO_CORRECAO.md, Etapa 7).')
                    break
    return problemas


def verificar() -> list[str]:
    problemas: list[str] = []
    capitulos, completos, em_curso, guardados = numeros_reais()
    # O progresso só cresce; estes mínimos detectam uma perda de dados sem
    # obrigar a editar o teste a cada capítulo novo.
    if (capitulos, completos) < (18, 766):
        problemas.append(
            f'dados: regressão — esperava pelo menos 18 capítulos e 766 '
            f'versículos completos; encontrei {capitulos} e {completos}.'
        )
    readme = (RAIZ / 'README.md').read_text(encoding='utf-8')
    for texto in (f'{capitulos} capítulos', f'{guardados} versículos guardados', '1.189', '31.102'):
        if texto not in readme:
            problemas.append(f'README.md: falta a referência actual {texto!r}.')
    # Números de versões antigas que já induziram o utilizador em erro.
    proibidos = ('5/1189', '5/1.189', '71 testes', '91 testes', 'repositório privado')
    for nome in ('README.md', 'docs/ESTADO.md', 'docs/ARQUITETURA.md', 'docs/EDITORIAL.md'):
        texto = (RAIZ / nome).read_text(encoding='utf-8')
        for velho in proibidos:
            if velho in texto:
                problemas.append(f'{nome}: ainda contém {velho!r}.')
    if em_curso and f'{guardados}' not in readme:
        problemas.append('README.md: não distingue versículos completos dos que estão em curso.')

    problemas += entregas_sem_json()
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
