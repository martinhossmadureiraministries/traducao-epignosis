#!/usr/bin/env python3
"""Confere as notas de Crítica Textual contra a colação de um livro.

Cada versículo com nota tem a sua Crítica Textual (CT) comparada com os factos
que a colação regista (`docs/colacao/<livro>.json`):

* resíduos de processo não podem estar no comentário publicado: marcadores
  `[[ … ]]` soltos, texto de quarentena, e o histórico de correções dentro das
  «Notas de redação» (a nota em si é legítima);
* a CT tem de trazer, em ordem, as três secções da casa;
* se o aparato da SBLGNT regista leituras, a CT tem de as citar pelas siglas
  (WH, Treg, NA28, RP…) e não pode dizer que não há variante;
* se o aparato não regista nada, a CT não pode atribuir a uma edição uma
  variante que ela não imprime;
* quando a CT diz que o Textus Receptus coincide ou diverge da base, a
  comparação tem de bater com as sequências normalizadas da colação.

Não corrige nada: sai com código 1 se encontrar um problema.

Uso:
    python3 scripts/verificar_notas_colacao.py --dados edicoes/nova/livros_json/500_Joao.json \
        --colacao docs/colacao/João.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ_REPO))
from bee.inspetor import LIVROS_FORMATO_CASA  # noqa: E402

SECCOES = ('Análise Léxica:', 'Crítica Textual:', 'Síntese Exegética:')
# Resíduos de processo: o histórico de correções e a produção automática não
# pertencem ao comentário publicado. A secção «Nota de redação» em si é legítima
# (docs/CRITICA_TEXTUAL.md): só é resíduo quando conta a história da redação.
RESIDUOS = (
    (re.compile(r'(?<!<i>)\[\[(?!\s*\]\]</i>)|(?<!<i>)\[\[\s*\]\](?!</i>)'), 'marcador «[[ ]]» solto, fora de explicação em itálico'),
    (re.compile(r'Versículo pendente|quarentena|lapidaç', re.I), 'texto de produção automática (quarentena/lapidação)'),
    (re.compile(r'(redação|nota|texto|tradução|Crítica Textual) anterior\b|\bdeu «|Três correções|Duas correções', re.I),
     'história de correções no comentário (resíduo de processo)'),
    (re.compile(r'<b>Nota de redação:</b>[^<]*(?:anterior|correç|dizia|\blia\b)', re.I),
     'nota de redação que conta uma versão anterior'),
)
SIGLAS = ('WH', 'Treg', 'NA28', 'RP', 'NIV')
# Nomes por extenso que as CT usam no lugar da sigla («Tregelles» não é «Treg»).
ALIAS = {
    'WH': ('WH', 'Westcott-Hort', 'Westcott e Hort', 'Westcott', 'Hort'),
    'Treg': ('Treg', 'Tregelles'),
    'NA28': ('NA28', 'Nestle-Aland', 'Nestle–Aland'),
    'RP': ('RP', 'Robinson-Pierpont', 'Robinson'),
    'NIV': ('NIV',),
}


def _cita(sigla: str, texto: str) -> bool:
    """A CT cita a sigla, pela sigla ou por extenso."""
    return any(re.search(rf'(?<!\w){re.escape(a)}(?!\w)', texto)
               for a in ALIAS[sigla])
TEM_SEM_VARIANTE = re.compile(
    r'sem variante|nada regista|sem unidade de variação|não regista variante|'
    r'não há variante|sem variação', re.I)
TR_COINCIDE = re.compile(r'Textus Receptus[^.;]*?(coincide|idêntic)', re.I)
TR_DIVERGE = re.compile(r'Textus Receptus[^.;]*?(diverge|difere)', re.I)


def _ct(comentario: str) -> str | None:
    m = re.search(r'<b>Crítica Textual:</b>(.*?)</p>', comentario, re.S)
    return m.group(1) if m else None


def _lados(entrada: str) -> tuple[set[str], set[str]]:
    """Siglas da leitura da base (antes de «]») e das leituras alternativas."""
    base, _, alternativas = entrada.partition(']')
    siglas = lambda s: {x for x in SIGLAS if _cita(x, s)}
    return siglas(base), siglas(alternativas)


def verificar(dados: dict, colacao: dict) -> list[str]:
    problemas: list[str] = []
    versiculos = colacao.get('versiculos', {})
    livro = colacao.get('livro_bee')
    formato_casa = True if livro is None else livro in LIVROS_FORMATO_CASA
    for cap, lista in sorted(dados.get('chapters', {}).items(), key=lambda kv: int(kv[0])):
        for verso in lista:
            ref = f"{cap}:{verso.get('verse')}"
            com = verso.get('commentary') or ''
            texto = verso.get('text') or ''
            # O «[[ ]]» é marca legítima no texto (leitura assinalada); as
            # regras de resíduo aplicam-se só ao comentário. No texto, só
            # se procura marcador de produção (pendente/quarentena).
            for regex, nome in RESIDUOS:
                if regex.search(com):
                    problemas.append(f'{ref}: {nome}')
            if RESIDUOS[1][0].search(texto):
                problemas.append(f'{ref}: {RESIDUOS[1][1]} (no texto do versículo)')
            if '<b>' in com and not com.count('<b>'):
                problemas.append(f'{ref}: comentário sem rótulos')
            if re.search(r'<b>[^<]*[\u0370-\u03ff\u1f00-\u1fff][^<]*</b>', com):
                problemas.append(f'{ref}: palavra grega em negrito (use itálico)')
            rotulos = [r for r in re.findall(r'<b>([^<]+)</b>', com)]
            pedidos = [r for r in rotulos if r in SECCOES]
            if formato_casa and pedidos != list(SECCOES):
                problemas.append(f'{ref}: secções da casa em falta ou fora de ordem ({pedidos})')
            ct = _ct(com)
            if ct is None:
                # Nota em prosa (livros fora do formato da casa): a CT só aparece
                # quando há variante, mas toda a variante do aparato tem de ter CT.
                if not formato_casa and (versiculos.get(ref, {}).get('base', {})
                                         .get('aparato_sblgnt') or []):
                    problemas.append(f'{ref}: variante do aparato sem Crítica Textual')
                continue
            facto = versiculos.get(ref)
            if facto is None:
                problemas.append(f'{ref}: sem registo na colação')
                continue
            base = facto.get('base', {})
            aparato = base.get('aparato_sblgnt') or []
            if aparato:
                if TEM_SEM_VARIANTE.search(ct):
                    problemas.append(f'{ref}: CT nega variante que o aparato regista')
                for entrada in aparato:
                    # Basta uma sigla de cada lado: a CT não tem de repetir a lista.
                    for lado in _lados(entrada):
                        if lado and not any(_cita(s, ct) for s in lado):
                            problemas.append(f'{ref}: CT não cita {sorted(lado)} do aparato')
            else:
                # O aparato é o da SBLGNT, só de edições. Variantes de testemunhas
                # (manuscritos) constam das divergências da colação: não são falta.
                tem_divergencia = any(d.get('estado') == 'divergente'
                                      for d in facto.get('divergencias') or [])
                if not tem_divergencia and not TEM_SEM_VARIANTE.search(ct) \
                        and re.search(r'omite|acrescenta|diverg|variante', ct, re.I) \
                        and not TR_DIVERGE.search(ct) and not re.search(r'Textus', ct):
                    problemas.append(f'{ref}: CT fala de variante sem entrada no aparato')
            iguais = base.get('sblgnt_norm') == base.get('scrivener_norm')
            if TR_COINCIDE.search(ct) and not iguais:
                problemas.append(f'{ref}: CT diz que o TR coincide, mas a colação mostra diferença')
            if TR_DIVERGE.search(ct) and iguais and not re.search(r'diverge[^.]*variante', ct, re.I):
                problemas.append(f'{ref}: CT diz que o TR diverge, mas a colação mostra coincidência')
    return problemas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--dados', required=True, type=Path)
    ap.add_argument('--colacao', required=True, type=Path)
    args = ap.parse_args(argv)
    dados = json.loads(args.dados.read_text(encoding='utf-8'))
    colacao = json.loads(args.colacao.read_text(encoding='utf-8'))
    problemas = verificar(dados, colacao)
    if problemas:
        print(f'{len(problemas)} problema(s) nas notas de {args.dados.name}:')
        for p in problemas:
            print(f'  - {p}')
        return 1
    print(f'Notas de {args.dados.name} conferem com a colação.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
