#!/usr/bin/env python3
"""Convenções de nota fixadas na revisão de João 1–15 (docs/ESTILO_BEE.md, «Convenções de notas»).

Verifica, em todos os JSON da edição nova, o que se pode conferir sem ler o grego:

  * FALHA — «Crítica Textual:» repetida no mesmo versículo;
  * FALHA — «Crítica Textual:» colada ao parágrafo principal (tem de abrir um <p> próprio);
  * FALHA — sinais de aparato (⸀ ⸁ ⸂ ⸃) dentro da nota;
  * FALHA — «lêm» (português europeu: «leem»);
  * AVISO — a NIV citada numa Crítica Textual sem «por escolha de tradução»
    (a NIV é tradução, não testemunha);
  * AVISO — «A base» com maiúscula depois dos dois pontos do aparato (usa-se «a base»;
    com maiúscula só no início de frase);
  * AVISO — «Huios» com maiúscula na transliteração (é «huios»).

Código de saída 1 se houver FALHAS; avisos só saem com código 1 com --rigoroso.

Uso:
    python3 scripts/verificar_convencoes_notas.py
    python3 scripts/verificar_convencoes_notas.py --rigoroso
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / "edicoes" / "nova" / "livros_json"
CT = "Crítica Textual:"


def _texto(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def verificar_nota(html: str) -> tuple[list[str], list[str]]:
    falhas: list[str] = []
    avisos: list[str] = []
    if html.count(CT) > 1:
        falhas.append("Crítica Textual repetida")
    if any(not html[:m.start()].endswith("<p><b>") for m in re.finditer(re.escape(CT), html)):
        falhas.append("Crítica Textual colada ao parágrafo principal")
    if re.search(r"[⸀⸁⸂⸃]", html):
        falhas.append("sinal de aparato na nota")
    texto = _texto(html)
    if re.search(r"\blêm\b", texto):
        falhas.append("«lêm» (usar «leem»)")
    if re.search(r"SBLGNT, [\d:–]+: A base", texto):
        avisos.append("«A base» com maiúscula depois dos dois pontos do aparato")
    if re.search(r"\bHuios\b", texto):
        avisos.append("«Huios» (usar «huios»)")
    m = re.search(rf"{re.escape(CT)}(.*)$", texto)
    if m:
        for frase in re.split(r"(?<=\.)\s", m.group(1)):
            if "NIV" in frase and "escolha de tradução" not in frase:
                avisos.append("NIV em Crítica Textual sem «por escolha de tradução»")
                break
    return falhas, avisos


def verificar_edicao(pasta: Path) -> tuple[list[str], list[str]]:
    falhas: list[str] = []
    avisos: list[str] = []
    for ficheiro in sorted(glob.glob(str(pasta / "*.json"))):
        dados = json.loads(Path(ficheiro).read_text(encoding="utf-8"))
        nome = Path(ficheiro).name
        for cap, versos in dados.get("chapters", {}).items():
            for v in versos:
                f, a = verificar_nota(v.get("commentary", ""))
                for item in f:
                    falhas.append(f"{nome} {cap}:{v['verse']}: {item}")
                for item in a:
                    avisos.append(f"{nome} {cap}:{v['verse']}: {item}")
    return falhas, avisos


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dados", type=Path, default=DADOS)
    ap.add_argument("--rigoroso", action="store_true")
    args = ap.parse_args(argv)
    falhas, avisos = verificar_edicao(args.dados)
    for item in falhas:
        print(f"FALHA  {item}")
    for item in avisos:
        print(f"aviso  {item}")
    print(f"Convenções: {len(falhas)} falha(s), {len(avisos)} aviso(s).")
    if falhas or (avisos and args.rigoroso):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
