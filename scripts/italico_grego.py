#!/usr/bin/env python3
"""Põe em itálico o grego fora de <i> nas notas (decisão D7 do plano).

Só altera o campo `commentary`. Confirma que, sem as marcas <i>, cada nota
fica igual. Sem `--aplicar` só mostra quantos trechos mudariam.

Uso:
    python3 scripts/italico_grego.py                  # conta, não escreve
    python3 scripts/italico_grego.py --aplicar        # escreve
    python3 scripts/italico_grego.py --dados PASTA --aplicar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.grego import grego_fora_de_italico, italico_grego, sem_marcas_i  # noqa: E402


def processar(pasta: Path, aplicar: bool) -> int:
    trechos = 0
    ficheiros = 0
    for caminho in sorted(pasta.glob('*.json')):
        texto_original = caminho.read_text(encoding='utf-8')
        dados = json.loads(texto_original)
        if json.dumps(dados, ensure_ascii=False, indent=2) + '\n' != texto_original:
            print(f'  {caminho.name}: formatação não é a canónica; ignorado')
            continue
        alterado = False
        for zona in ('chapters', 'in_progress'):
            for versos in (dados.get(zona) or {}).values():
                for verso in versos:
                    nota = verso.get('commentary')
                    if not nota:
                        continue
                    novo = italico_grego(nota)
                    if novo == nota:
                        continue
                    assert sem_marcas_i(novo) == sem_marcas_i(nota), caminho.name
                    trechos += len(grego_fora_de_italico(nota))
                    verso['commentary'] = novo
                    alterado = True
        if alterado:
            ficheiros += 1
            if aplicar:
                caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n',
                                   encoding='utf-8')
    modo = 'escritos' if aplicar else 'a alterar (sem --aplicar)'
    print(f'{ficheiros} ficheiro(s) {modo}; {trechos} trecho(s) de grego posto(s) em itálico.')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--dados', type=Path, default=RAIZ / 'edicoes' / 'nova' / 'livros_json')
    ap.add_argument('--aplicar', action='store_true')
    args = ap.parse_args()
    return processar(args.dados, args.aplicar)


if __name__ == '__main__':
    sys.exit(main())
