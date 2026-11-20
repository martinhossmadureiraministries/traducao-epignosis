#!/usr/bin/env python3
"""Corrige as palavras greco-latinas mistas que a porta nova apanhou.

Cinco casos reais nos dados gravados — a mesma classe de gralha de
João 4:16 («ἄνδra») que motivou a deteção em ``bee/inspetor.py``:

- João 1:21 e 1:25: «Ἠλ + ías latino» dentro da forma grega;
- João 1:24: transliteração «(pharisa + ίων grego)» meio a meio;
- João 1:30: a Nota de redação CITAVA a forma defeituosa — passa a
  descrevê-la sem a reproduzir (a porta lê a nota inteira);
- 3 João 1:14: falta de espaço («direto.κατ’») colava latim a grego.

As cadeias gregas constroem-se por codepoints (U+…) para não trocar
letras latinas e gregas visualmente idênticas. O script verifica no
fim que não resta nenhum token misto nos dois livros.

Uso:
    python3 scripts/lapidar_mistos.py              # aplica e guarda
    python3 scripts/lapidar_mistos.py --verificar  # só confere
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.lapidador import tokens_mistos  # noqa: E402

DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json'

_ILIAS_MISTO = '\u1f28\u03bb\u00edas'
_ILIAS_GREGO = '\u1f28\u03bb\u03af\u03b1\u03c2'
_PHAR_MISTO = '(pharisa\u03af\u03c9\u03bd)'
_PHAR_LIMPO = '(pharisai\u014dn)'

# (livro, capítulo, verso, antes, depois)
FRAGMENTOS = [
    ('500_Joao.json', 1, 21, _ILIAS_MISTO, _ILIAS_GREGO),
    ('500_Joao.json', 1, 25, _ILIAS_MISTO, _ILIAS_GREGO),
    ('500_Joao.json', 1, 24, _PHAR_MISTO, _PHAR_LIMPO),
    ('500_Joao.json', 1, 30,
     'trazia «' + 'γέγον' + 'en' + '», com letras latinas dentro da '
     'forma grega',
     'trazia a forma de ' + 'γέγονεν' + ' com as duas últimas letras '
     'em caracteres latinos'),
]
# 3 João 1:14: espaço em falta depois do ponto, antes do grego.
_REGEX_3JOAO = re.compile(r'direto\.(?=[\u0370-\u03ff\u1f00-\u1fff])')


def _versos(dados: dict, capitulo: int):
    for zona in ('chapters', 'in_progress'):
        if str(capitulo) in dados.get(zona, {}):
            return dados[zona][str(capitulo)]
    raise KeyError(capitulo)


def corrigir(verificar: bool) -> int:
    problemas = 0
    alterados: dict[str, dict] = {}
    caminhos: dict[str, Path] = {}
    for nome, capitulo, verso, antes, depois in FRAGMENTOS:
        caminho = DADOS / nome
        dados = alterados.get(nome) or json.loads(
            caminho.read_text(encoding='utf-8'))
        alterados[nome] = dados
        caminhos[nome] = caminho
        alvo = next(v for v in _versos(dados, capitulo)
                    if v['verse'] == verso)
        nota = alvo['commentary']
        if antes in nota:
            alvo['commentary'] = nota.replace(antes, depois)
            print(f'  {nome} {capitulo}:{verso}: fragmento corrigido')
        elif depois not in nota:
            print(f'  FALHA {nome} {capitulo}:{verso}: fragmento ausente',
                  file=sys.stderr)
            problemas += 1

    caminho = DADOS / '710_3_Joao.json'
    dados = alterados.get('710_3_Joao.json') or json.loads(
        caminho.read_text(encoding='utf-8'))
    alterados['710_3_Joao.json'] = dados
    caminhos['710_3_Joao.json'] = caminho
    alvo = next(v for v in _versos(dados, 1) if v['verse'] == 14)
    nova, n = _REGEX_3JOAO.subn('direto. ', alvo['commentary'])
    if n:
        alvo['commentary'] = nova
        print('  710_3_Joao.json 1:14: espaço reposto')

    for nome, dados in alterados.items():
        for zona in ('chapters', 'in_progress'):
            for versiculos in dados.get(zona, {}).values():
                for v in versiculos:
                    mistos = tokens_mistos(v.get('commentary', ''))
                    if mistos:
                        print(f'  FALHA {nome}: restam mistos {mistos}',
                              file=sys.stderr)
                        problemas += 1
        if verificar or problemas:
            continue
        temporario = caminhos[nome].with_suffix('.tmp')
        with temporario.open('w', encoding='utf-8') as fh:
            json.dump(dados, fh, ensure_ascii=False, indent=2)
            fh.write('\n')
        os.replace(temporario, caminhos[nome])
    return 1 if problemas else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--verificar', action='store_true')
    args = ap.parse_args()
    codigo = corrigir(args.verificar)
    print('\nOK: sem palavras greco-latinas mistas.'
          if codigo == 0 else '\nHá problemas por corrigir.')
    return codigo


if __name__ == '__main__':
    raise SystemExit(main())
