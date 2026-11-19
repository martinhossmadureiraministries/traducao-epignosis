#!/usr/bin/env python3
"""Semeia a NOVA edição com os livros que o responsável JÁ APROVOU como piloto.

Motivo: uma execução automática reproduziu Filemom abaixo da qualidade do piloto
aprovado («Apfia», «a tua amor», «entranhas», vv. 8–9 achatados). Os pilotos em
`edicoes/piloto/` são o padrão; este script copia-lhes o TEXTO aprovado para os
JSON da edição nova, garantindo que esses livros ficam exatamente ao nível
aprovado e que a produção automática NÃO os volta a gerar por cima.

Honestidade: o texto vem do piloto aprovado. O comentário é reconstruído com as
três secções obrigatórias (Análise Léxica / Crítica Textual / Síntese Exegética)
usando as notas exegéticas do piloto quando existem; onde faltam, fica marcado
como rascunho a migrar. Continua a ser RASCUNHO até revisão especializada.

Capítulo só vira `chapters` (completo) se o número de versículos igualar o
esperado pelo catálogo; caso contrário vai para `in_progress` com aviso — nunca
marcamos como completo um capítulo com lacunas.

Uso:
    python3 scripts/importar_piloto.py --dry-run            # mostra contagens
    python3 scripts/importar_piloto.py                      # escreve nos JSON
    python3 scripts/importar_piloto.py --dados outra/pasta
"""
from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from html import escape
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.arquivos import novo_livro, salvar_livro, validar_versiculos  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402


# (ficheiro do piloto, livro inicial). Para o ficheiro conjunto 2 e 3 João, o
# detetor de cabeçalhos troca de livro ao encontrar "## 3 João".
PILOTOS = [
    ('FILEMOM.md', 640),
    ('TITO.md', 630),
    ('JUDAS.md', 720),
    ('2_E_3_JOAO.md', 700),
]

_NUM_LIVRO_POR_NOME = {'2 joao': 700, '3 joao': 710}

RE_TITULO = re.compile(r'^(#{1,6})\s+(.*)$')
RE_VERSO = re.compile(r'^\*\*(\d+)\.\*\*\s*(.*)$')


def _norm(texto: str) -> str:
    sem_acentos = ''.join(
        c for c in unicodedata.normalize('NFD', texto) if not unicodedata.combining(c)
    )
    return ' '.join(sem_acentos.casefold().split())


def _limpar_links_markdown(texto: str) -> str:
    """[rótulo](url) -> rótulo; evita HTML inválido no comentário."""
    return re.sub(r'\[([^\]]+)\]\([^)]*\)', r'\1', texto)


def analisar_fichiero(texto_md: str, livro_inicial: int):
    """Devolve {(numero_livro, capitulo): {'versos': {n: texto}, 'notas': {n: nota}}}."""
    blocos: dict[tuple[int, int], dict] = {}
    livro = livro_inicial
    capitulo = 1
    secao = 'texto'          # 'texto' | 'notas'
    aberto = None            # ('verso'|'nota', numero)

    def bloco() -> dict:
        chave = (livro, capitulo)
        return blocos.setdefault(chave, {'versos': {}, 'notas': {}})

    def fechar():
        nonlocal aberto
        if aberto is None:
            return
        tipo, numero = aberto
        alvo = 'versos' if tipo == 'verso' else 'notas'
        atual = bloco()[alvo].get(numero, [])
        limpo = ' '.join(' '.join(atual).split())
        bloco()[alvo][numero] = limpo
        aberto = None

    for linha in texto_md.splitlines():
        titulo = RE_TITULO.match(linha)
        if titulo:
            fechar()
            nome = titulo.group(2).strip()
            baixo = _norm(nome)
            if baixo in _NUM_LIVRO_POR_NOME:           # "## 2 João"/"## 3 João"
                livro = _NUM_LIVRO_POR_NOME[baixo]
                capitulo = 1
                secao = 'texto'
                continue
            m_cap = re.search(r'cap[íi]tulo\s+(\d+)', baixo)
            if m_cap:
                capitulo = int(m_cap.group(1))
                continue
            if 'nota' in baixo:
                secao = 'notas'
            elif 'texto' in baixo:
                secao = 'texto'
            continue
        verso = RE_VERSO.match(linha.strip())
        if verso:
            fechar()
            numero = int(verso.group(1))
            resto = verso.group(2).strip()
            tipo = 'verso' if secao == 'texto' else 'nota'
            alvo = 'versos' if tipo == 'verso' else 'notas'
            bloco()[alvo].setdefault(numero, [])
            if resto:
                bloco()[alvo][numero].append(_limpar_links_markdown(resto))
            aberto = (tipo, numero)
            continue
        if aberto is not None and linha.strip():
            tipo, numero = aberto
            alvo = 'versos' if tipo == 'verso' else 'notas'
            bloco()[alvo][numero].append(_limpar_links_markdown(linha.strip()))
    fechar()
    return blocos


def comentario(nota: str | None) -> str:
    analise = ('<p><b>Análise Léxica:</b> termos no original registados nas notas do '
               'piloto aprovado; migração lexical pendente de verificação.</p>')
    critica = ('<p><b>Crítica Textual:</b> aparato de edições comparado no piloto '
               'aprovado; colação direta não repetida aqui.</p>')
    if nota:
        sintese = '<p><b>Síntese Exegética:</b> ' + escape(nota) + '</p>'
    else:
        sintese = ('<p><b>Síntese Exegética:</b> rascunho a migrar das notas do piloto '
                   'aprovado.</p>')
    return analise + critica + sintese


def importar(pilotos_dir: Path, dados_dir: Path, dry_run: bool) -> int:
    problemas: list[str] = []
    resumo: list[str] = []
    for ficheiro, livro_inicial in PILOTOS:
        caminho = pilotos_dir / ficheiro
        if not caminho.exists():
            problemas.append(f'piloto em falta: {caminho}')
            continue
        blocos = analisar_fichiero(caminho.read_text(encoding='utf-8'), livro_inicial)
        livros_vistos = sorted({numero for numero, _ in blocos})
        for numero in livros_vistos:
            livro = POR_NUMERO.get(numero)
            if livro is None:
                problemas.append(f'{ficheiro}: livro {numero} desconhecido no catálogo')
                continue
            caps = sorted(cap for n, cap in blocos if n == numero)
            destino = dados_dir / livro.nome_arquivo
            estrutura = novo_livro(livro)
            completos, parciais = 0, 0
            for cap in caps:
                esperado = livro.versos_por_capitulo[cap - 1]
                versos = blocos[(numero, cap)]['versos']
                notas = blocos[(numero, cap)]['notas']
                ordenados = sorted(versos)
                lista = [
                    {'verse': n, 'text': versos[n],
                     'commentary': comentario(notas.get(n))}
                    for n in ordenados
                ]
                contexto = f'{livro.nome} {cap} (piloto)'
                try:
                    validar_versiculos(lista, range(1, len(lista) + 1), contexto)
                except Exception as exc:  # noqa: BLE001 - reportar e continuar
                    problemas.append(f'{contexto}: validação falhou ({exc})')
                    continue
                chave = str(cap)
                if len(lista) == esperado and ordenados == list(range(1, esperado + 1)):
                    estrutura['chapters'][chave] = lista
                    completos += 1
                else:
                    estrutura['in_progress'][chave] = lista
                    parciais += 1
                    problemas.append(
                        f'{livro.nome} {cap}: {len(lista)} versículos no piloto, '
                        f'esperava {esperado}; guardado em in_progress (não completo).'
                    )
            resumo.append(
                f'{livro.nome} ({livro.nome_arquivo}): {completos} capítulo(s) completo(s), '
                f'{parciais} parcial(is).'
            )
            if not dry_run and completos + parciais:
                dados_dir.mkdir(parents=True, exist_ok=True)
                salvar_livro(destino, estrutura, livro)
    for linha in resumo:
        print(('DRY-RUN ' if dry_run else '') + linha)
    if problemas:
        print('\nAvisos:')
        for p in problemas:
            print('  - ' + p)
    if not dry_run:
        print('\nVerifique a integridade: '
              f'python3 scripts/verificar_dados.py --dados {dados_dir} --minimo 0')
    return 1 if problemas and not any('completo' in r for r in resumo) else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--pilotos', type=Path, default=RAIZ / 'edicoes' / 'piloto')
    parser.add_argument('--dados', type=Path,
                        default=RAIZ / 'edicoes' / 'nova' / 'livros_json')
    parser.add_argument('--dry-run', action='store_true',
                        help='mostra as contagens sem escrever nada')
    args = parser.parse_args()
    return importar(args.pilotos, args.dados, args.dry_run)


if __name__ == '__main__':
    raise SystemExit(main())
