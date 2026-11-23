#!/usr/bin/env python3
"""Guarda anti-deriva da voz BEE: deteta nos versículos gerados aquilo que o
perfil proíbe, ANTES de chegar ao leitor.

É uma rede de segurança independente do modelo: mesmo que um provedor "escorregue"
para a Almeida ou misture registos, este verificador sinaliza. Corre offline, sem
rede nem chaves, sobre os JSON de qualquer edição.

O núcleo de análise vive em ``bee/inspetor.py`` (usado também como porta
obrigatória dentro do próprio motor de geração — P1); este script é a CLI de
auditoria sobre dados gravados e reexporta os mesmos símbolos.

Procura três categorias:
  * ARCAÍSMOS (falha dura) — «vós/vos/convosco», «sois/sejais/sabeis/padeceis…»;
    a voz BEE usa sempre «vocês».
  * HESITAÇÃO NO TEXTO (falha dura) — «ou seja», «ou melhor», parênteses/travessões
    com alternativa; as nuances pertencem à nota, não ao versículo.
  * MARCADORES DE ALMEIDA (aviso) — léxico eclesiástico/antigo («sobremaneira»,
    «porventura», «outrossim», «o sem lei»…) a merecer reescrita.
  * NOTAS FORA DO FORMATO (falha dura, só na edição nova) — nos livros da
    prosa, sem rótulos «Análise Léxica» / «Síntese Exegética» e sem níveis de
    certeza A/B/C (decisão de 2026-11-23). Notas com esses rótulos são falha.

Código de saída: 1 se houver FALHAS duras (ou também avisos com --rigoroso);
0 caso contrário. Serve tanto para leitura manual como para um passo de CI.

Uso:
    python3 scripts/verificar_estilo.py                     # edição nova
    python3 scripts/verificar_estilo.py --dados livros_json # linha legada
    python3 scripts/verificar_estilo.py 600                 # só 2 Tessalonicenses
    python3 scripts/verificar_estilo.py --rigoroso          # avisos também chumbam
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import ler_todos  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402
# Núcleo único das listas de proibição (o motor de geração usa o mesmo).
from bee.inspetor import (  # noqa: E402,F401  (reexportados para testes/CLI)
    ARCAISMOS,
    HEDGE_FRASES,
    HEDGE_PADROES,
    MARCADORES_ALMEIDA,
    _HEDGE_FRASES_NORM,
    _norm,
    analisar_comentario,
    analisar_texto,
    grego_sem_italico,
)


def analisar_dados(dados: dict,
                   incluir_comentario: bool = False,
                   ) -> list[tuple[int, int, str, dict]]:
    """Percorre capítulos completos e em curso; devolve achados por versículo.

    ``incluir_comentario`` liga a verificação do formato das notas, que só
    se aplica à edição nova: a linha legada usa outro formato de nota e
    não pode chumbar por ele.
    """
    achados: list[tuple[int, int, str, dict]] = []
    for capitulo, versiculos in sorted({**dados.get('chapters', {}),
                                        **dados.get('in_progress', {})}.items(),
                                       key=lambda kv: int(kv[0])):
        for verso in versiculos:
            resultado = analisar_texto(str(verso.get('text', '')))
            if incluir_comentario:
                resultado['duros'] = sorted(set(
                    resultado['duros']
                    + analisar_comentario(str(verso.get('commentary') or ''))
                    + grego_sem_italico(str(verso.get('commentary') or ''))))
            if resultado['duros'] or resultado['avisos']:
                achados.append((int(capitulo), int(verso.get('verse', 0)),
                                str(verso.get('text', '')), resultado))
    return achados


def _eh_edicao_nova(pasta: Path) -> bool:
    """A verificação das notas só se aplica à pasta da edição nova."""
    try:
        return pasta.resolve() == (
            RAIZ / 'edicoes' / 'nova' / 'livros_json').resolve()
    except OSError:
        return False


def relatorio(pasta: Path, livros_filtro: set[int] | None, rigoroso: bool) -> int:
    todos = ler_todos(pasta)
    falhas = avisos_total = 0
    for numero in sorted(todos):
        if livros_filtro and numero not in livros_filtro:
            continue
        livro = POR_NUMERO.get(numero)
        nome = livro.nome if livro else str(numero)
        achados = analisar_dados(todos[numero],
                                 incluir_comentario=_eh_edicao_nova(pasta))
        if not achados:
            continue
        print(f'\n## {nome} ({numero})')
        for capitulo, verso, texto, res in achados:
            etiqueta = []
            if res['duros']:
                etiqueta.append('FALHA: ' + ', '.join(res['duros']))
            if res['avisos']:
                etiqueta.append('aviso: ' + ', '.join(res['avisos']))
            falhas += 1 if res['duros'] else 0
            avisos_total += len(res['avisos'])
            excerto = (texto[:90] + '…') if len(texto) > 90 else texto
            print(f'  {capitulo}:{verso} [{"; ".join(etiqueta)}] {excerto}')
    if falhas == 0 and avisos_total == 0:
        print('\nEstilo limpo: nenhum arcaísmo, hesitação ou marcador de Almeida.')
    else:
        print(f'\nResumo: {falhas} versículo(s) com falhas duras, {avisos_total} aviso(s).')
    if falhas:
        return 1
    if rigoroso and avisos_total:
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('livros', nargs='*', type=int,
                        help='book_number a filtrar (vazio = todos)')
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json',
                        help='pasta dos JSON (padrão: edição nova)')
    parser.add_argument('--rigoroso', action='store_true',
                        help='avisos (marcadores de Almeida) também fazem chumbar')
    args = parser.parse_args()
    if not args.dados.exists():
        print(f'Pasta de dados não encontrada: {args.dados}', file=sys.stderr)
        return 2
    return relatorio(args.dados, set(args.livros) or None, args.rigoroso)


if __name__ == '__main__':
    raise SystemExit(main())
