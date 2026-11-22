#!/usr/bin/env python3
"""Retira o histórico de correções das «Notas de redação» de livros em rascunho.

A secção «Nota de redação» é legítima (docs/CRITICA_TEXTUAL.md): explica uma
escolha de tradução. Mas, em várias redações, foi usada para contar a história
da versão anterior («A redação anterior dizia…», ««X» deu «Y»», «Duas
correções»). Isso é processo, não leitura, e não pertence ao comentário.

A ferramenta retira essas frases e mantém as restantes. Se uma nota ficar sem
frases, a secção desaparece. Não toca em nenhum livro que tenha um bloco de
revisão que não esteja em `rascunho`: texto aprovado não se altera por aqui.

Por defeito só mostra o que faria; `--aplicar` escreve.

Uso:
    python3 scripts/limpar_historico_notas.py --aplicar \
        edicoes/nova/livros_json/600_2_Tessalonicenses.json \
        edicoes/nova/livros_json/630_Tito.json
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

NOTA = re.compile(r'<p><b>Nota de redação:</b>(.*?)</p>', re.S)
HISTORICO = re.compile(
    r'\b(a|à|da|na|de) (versão|redação|tradução|formulação) anterior\b|'
    r'\bversão anterior\b|\bredação de \d{4}-\d{2}-\d{2}\b|'
    r'\bmesma correção de\b|\bcorreç(ão|ões)\b|\bdeu «|'
    r'\baprovada em \d{1,2}/\d{1,2}\b|\bsubstitui a formulação\b|'
    r'\b[Ff]oi corrigid[oa]\b|\b[Cc]orrigid[oa] para\b|\btraduzia\b', re.I)
# Cabeçalhos que ficam sem conteúdo depois da frase de histórico.
CABECALHO = re.compile(r'^(Duas|Três|Quatro) correções\.$')
# Divide em frases, sem partir no ponto de abreviaturas nem dentro de «…».
FRASES = re.compile(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÂÊÔÃÕÇ«“(<])')


def _equilibrado(texto: str) -> bool:
    return all(texto.count(f'<{t}>') == texto.count(f'</{t}>') for t in ('i', 'b'))


def _limpa_nota(conteudo: str) -> tuple[str | None, int]:
    """Devolve (novo conteúdo ou None se a nota desaparece, nº de frases retiradas)."""
    frases = FRASES.split(conteudo.strip())
    mantidas = [f for f in frases if not HISTORICO.search(f) and not CABECALHO.match(f)]
    retiradas = len(frases) - len(mantidas)
    if retiradas == 0:
        return conteudo, 0
    if not mantidas:
        return None, retiradas
    novo = ' '.join(mantidas)
    if not _equilibrado(novo):
        raise ValueError('a limpeza deixaria marcação desequilibrada')
    return novo, retiradas


def limpar(dados: dict) -> tuple[int, int, int]:
    """Altera `dados` no lugar. Devolve (notas tocadas, frases retiradas, notas removidas)."""
    for bloco in dados.get('review', {}).get('editorial_blocks', []):
        if bloco.get('status') != 'rascunho':
            raise PermissionError(f"bloco com estado «{bloco.get('status')}»: não se mexe")
    tocadas = frases_total = removidas = 0
    for lista in dados['chapters'].values():
        for verso in lista:
            com = verso.get('commentary') or ''

            def _sub(m: re.Match) -> str:
                nonlocal tocadas, frases_total, removidas
                novo, n = _limpa_nota(m.group(1))
                if n == 0:
                    return m.group(0)
                tocadas += 1
                frases_total += n
                if novo is None:
                    removidas += 1
                    return ''
                return f'<p><b>Nota de redação:</b> {novo}</p>'

            verso['commentary'] = NOTA.sub(_sub, com)
    return tocadas, frases_total, removidas


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('ficheiros', nargs='+', type=Path)
    ap.add_argument('--aplicar', action='store_true')
    args = ap.parse_args(argv)
    estado = 0
    for caminho in args.ficheiros:
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        try:
            tocadas, frases, removidas = limpar(dados)
        except (PermissionError, ValueError) as erro:
            print(f'{caminho.name}: NÃO ALTERADO — {erro}', file=sys.stderr)
            estado = 1
            continue
        print(f'{caminho.name}: notas tocadas {tocadas}, frases retiradas {frases}, '
              f'secções removidas {removidas}')
        if args.aplicar and tocadas:
            caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n',
                               encoding='utf-8')
    if not args.aplicar:
        print('(simulação: use --aplicar para escrever)')
    return estado


if __name__ == '__main__':
    sys.exit(main())
