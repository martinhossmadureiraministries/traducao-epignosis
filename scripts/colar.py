#!/usr/bin/env python3
"""Colacionar um livro da BEE contra as testemunhas realmente consultadas.

Produz a matéria-prima verificável da crítica textual da edição nova: para cada
versículo, o que leem a base fixada (SBLGNT), o Textus Receptus de Scrivener, as
testemunhas manuscritas transcritas pelo CNTR e os textos críticos do mesmo
acervo — com o estado físico do suporte (lacuna, texto suprido, mão corrigida).

    python3 scripts/colar.py --livro 600            # relatório JSON + resumo
    python3 scripts/colar.py --livro 600 --verso 2:13
    python3 scripts/colar.py --livro 600 --markdown # tabela legível

O acervo CNTR vive em ``.bee-cache/`` (ignorada pelo Git): é CC BY-SA 4.0, por
isso é consultado e citado, nunca redistribuído. Ver ``docs/CRITICA_TEXTUAL.md``.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.catalogo import LIVROS  # noqa: E402
from bee.fontes import SBL_COMMIT, TR_COMMIT, FontesOriginais  # noqa: E402
from bee.manuscritos import (  # noqa: E402
    colacionar,
    ler_testemunha,
    normalizar_texto,
)
from bee.rede import ClienteHTTP  # noqa: E402

CACHE = RAIZ / '.bee-cache'
CNTR = CACHE / 'cntr'
CNTR_REVISAO = '4e743a41a4b2ca010ece53229cd272aa59b1efe6'
CNTR_URL = (
    'https://github.com/Center-for-New-Testament-Restoration/transcriptions'
)
SAIDA_PADRAO = RAIZ / 'docs' / 'colacao'


def livro_cntr(numero_bee: int) -> int:
    """Número CNTR (ordem canónica 1–66) a partir do número interno da BEE."""
    for indice, livro in enumerate(LIVROS, start=1):
        if livro.numero == numero_bee:
            return indice
    raise SystemExit(f'Livro BEE desconhecido: {numero_bee}')


def testemunhas_disponiveis(numero: int) -> tuple[list[str], list[str]]:
    """Testemunhas e edições do acervo CNTR que efetivamente contêm o livro."""
    if not CNTR.exists():
        raise SystemExit(
            f'Acervo CNTR ausente em {CNTR}. Descarregue e registe a revisão:\n'
            f'  curl -sL -o .bee-cache/cntr.tar.gz '
            f'{CNTR_URL.replace("github.com", "codeload.github.com")}'
            f'/tar.gz/{CNTR_REVISAO}\n'
            '  mkdir -p .bee-cache/cntr && tar xzf .bee-cache/cntr.tar.gz '
            '-C .bee-cache/cntr --strip-components=1'
        )
    manuscritos, edicoes = [], []
    for caminho in sorted((CNTR / 'class 1').glob('*.txt')):
        if any(l[:2] == f'{numero:02d}' and l[2:8].isdigit()
               for l in caminho.read_text(encoding='utf-8').splitlines()):
            manuscritos.append(caminho.stem)
    for caminho in sorted((CNTR / 'critical texts').glob('*.txt')):
        if any(l[:2] == f'{numero:02d}' and l[2:8].isdigit()
               for l in caminho.read_text(encoding='utf-8').splitlines()):
            edicoes.append(caminho.stem)
    return manuscritos, edicoes


def base_do_projeto(numero_bee: int) -> dict[str, dict[str, object]]:
    livro = next(l for l in LIVROS if l.numero == numero_bee)
    fontes = FontesOriginais(CACHE, ClienteHTTP())
    dados = fontes.carregar_livro(livro)
    resultado: dict[str, dict[str, object]] = {}
    for (capitulo, verso), item in sorted(dados.items()):
        sbl = ' '.join(b['texto'] for b in item['base'])
        resultado[f'{capitulo}:{verso}'] = {
            'sblgnt': sbl,
            'sblgnt_norm': normalizar_texto(sbl),
            'scrivener': item.get('textus_receptus', ''),
            'scrivener_norm': normalizar_texto(str(item.get('textus_receptus', ''))),
            'aparato_sblgnt': item.get('aparato_sblgnt', []),
            'aviso': item.get('aviso', ''),
        }
    return resultado


def _estado(versiculo) -> dict[str, object] | None:
    """Estado completo de uma testemunha num versículo (ou None se não o tem)."""
    if versiculo is None:
        return None
    return {
        'texto': versiculo.texto,
        'original': versiculo.leitura_original,
        'cru': versiculo.cru,
        'presente': versiculo.presente,
        'lacuna': versiculo.lacuna,
        'suprido': versiculo.suprido,
        'corrigido': versiculo.corrigida,
        'ilegivel_original': versiculo.ilegivel_original,
        'divisao_alternativa': versiculo.dividido,
        'nomina_sacra': [p.crua for p in versiculo.palavras if p.nomen_sacrum],
        'expansao_duvidosa': [p.crua for p in versiculo.palavras if p.expansao_duvidosa],
    }


def colacionar_livro(numero_bee: int) -> dict[str, object]:
    numero = livro_cntr(numero_bee)
    livro = next(l for l in LIVROS if l.numero == numero_bee)
    nomes_ms, nomes_ed = testemunhas_disponiveis(numero)
    manuscritos = {
        n: ler_testemunha(CNTR / 'class 1' / f'{n}.txt', numero) for n in nomes_ms
    }
    edicoes = {
        n: ler_testemunha(CNTR / 'critical texts' / f'{n}.txt', numero)
        for n in nomes_ed
    }
    base = base_do_projeto(numero_bee)

    versiculos: dict[str, object] = {}
    for referencia, dados_base in base.items():
        fontes = {
            **{n: m.get(referencia) for n, m in manuscritos.items()},
            **{n: e.get(referencia) for n, e in edicoes.items()},
            'Scrivener': _scrivener_como_testemunha(dados_base),
        }
        achados = colacionar(list(dados_base['sblgnt_norm']), fontes)
        versiculos[referencia] = {
            'base': dados_base,
            'divergencias': [
                {
                    'testemunha': a.testemunha, 'estado': a.estado,
                    'diferenca': a.diferenca, 'leitura': a.leitura,
                    'fisico': list(a.fisico),
                } for a in achados
            ],
            'leituras': {
                nome: _estado(dados.get(referencia))
                for nome, dados in list(manuscritos.items()) + list(edicoes.items())
            },
        }
    return {
        'livro': livro.nome,
        'livro_bee': numero_bee,
        'livro_cntr': numero,
        'gerado_por': 'scripts/colar.py',
        'fontes': {
            'base': {
                'nome': 'SBL Greek New Testament (base fixada do projeto)',
                'revisao': SBL_COMMIT, 'licenca': 'CC BY 4.0',
                'papel': 'texto traduzido; o aparato compara EDIÇÕES',
            },
            'comparacao': {
                'nome': 'Textus Receptus de Scrivener 1894 (M. A. Robinson)',
                'revisao': TR_COMMIT,
                'licenca': 'domínio público segundo o fornecedor',
                'papel': 'comparação/suplemento identificado',
            },
            'cntr': {
                'nome': 'CNTR Electronic Transcriptions (Alan Bunning)',
                'url': CNTR_URL, 'revisao': CNTR_REVISAO, 'licenca': 'CC BY-SA 4.0',
                'papel': 'testemunhas manuscritas e textos críticos',
                'redistribuicao': 'não redistribuído; cópia local em .bee-cache/ (ignorada)',
                'manuscritos': nomes_ms,
                'edicoes': nomes_ed,
            },
        },
        'versiculos': versiculos,
    }


def _scrivener_como_testemunha(dados_base: dict[str, object]):
    """Adapta o TR de Scrivener à interface de testemunha (sem estado físico)."""
    from bee.manuscritos import Palavra, VersiculoTestemunha

    return VersiculoTestemunha(
        referencia='', testemunha='Scrivener', presente=True,
        palavras=tuple(
            Palavra(forma=p, crua=p) for p in dados_base['scrivener_norm']
        ),
        cru=str(dados_base['scrivener']),
    )


def resumo(colacao: dict[str, object]) -> str:
    linhas = [
        f"COLAÇÃO — {colacao['livro']} (livro CNTR {colacao['livro_cntr']})",
        'Base: SBLGNT ' + str(colacao['fontes']['base']['revisao'])[:8]
        + ' · Comparação: Scrivener TR ' + str(colacao['fontes']['comparacao']['revisao'])[:8],
        'Testemunhas CNTR: ' + ', '.join(colacao['fontes']['cntr']['manuscritos']),
        'Edições CNTR: ' + ', '.join(colacao['fontes']['cntr']['edicoes']) + ', Scrivener TR',
        '',
    ]
    for referencia, entrada in colacao['versiculos'].items():
        divergentes = [
            d for d in entrada['divergencias'] if d['estado'] == 'divergente'
        ]
        ausentes = [d for d in entrada['divergencias'] if d['estado'] == 'ausente']
        if not divergentes:
            continue
        linhas.append(f'--- {referencia} ---')
        linhas.append(f"  SBL: {entrada['base']['sblgnt']}")
        for nota in entrada['base']['aparato_sblgnt']:
            linhas.append(f'  APP: {nota}')
        for achado in divergentes:
            fisico = (' [' + ','.join(achado['fisico']) + ']') if achado['fisico'] else ''
            linhas.append(
                f"  {achado['testemunha']:>11} divergente{fisico} {achado['diferenca']}"
            )
        if ausentes:
            linhas.append(
                '  ausentes: ' + ', '.join(a['testemunha'] for a in ausentes)
            )
        linhas.append('')
    return '\n'.join(linhas)


def markdown(colacao: dict[str, object]) -> str:
    """Tabela por versículo: quem diverge da base e como."""
    linhas = [
        f"# Colação — {colacao['livro']}",
        '',
        f"Base traduzida: **SBLGNT** (revisão `{colacao['fontes']['base']['revisao'][:8]}`, CC BY 4.0).",
        f"Comparação: **Scrivener TR** (`{colacao['fontes']['comparacao']['revisao'][:8]}`).",
        f"Testemunhas manuscritas (CNTR, revisão `{colacao['fontes']['cntr']['revisao'][:8]}`, CC BY-SA 4.0): "
        + ', '.join(colacao['fontes']['cntr']['manuscritos']) + '.',
        'Edições críticas CNTR: ' + ', '.join(colacao['fontes']['cntr']['edicoes']) + '.',
        '',
        'Uma testemunha «ausente» não conservou o versículo; «suprido» significa que',
        'o editor do CNTR restituiu texto numa lacuna do suporte.',
        '',
        '| Versículo | Divergências face ao SBLGNT |',
        '|---|---|',
    ]
    for referencia, entrada in colacao['versiculos'].items():
        divergentes = [
            d for d in entrada['divergencias'] if d['estado'] == 'divergente'
        ]
        if not divergentes:
            continue
        celulas = []
        for achado in divergentes:
            fisico = (' ‹' + ', '.join(achado['fisico']) + '›') if achado['fisico'] else ''
            celulas.append(f"**{achado['testemunha']}**{fisico}: {achado['diferenca']}")
        linhas.append(f'| {referencia} | ' + '<br>'.join(celulas) + ' |')
    linhas.append('')
    return '\n'.join(linhas)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--livro', type=int, default=600, help='número interno BEE')
    parser.add_argument('--verso', help='detalhe de um versículo (ex.: 2:13)')
    parser.add_argument('--markdown', action='store_true', help='imprime a tabela')
    parser.add_argument('--saida', type=Path, default=None, help='pasta de saída')
    argumentos = parser.parse_args()

    colacao = colacionar_livro(argumentos.livro)
    pasta = argumentos.saida or SAIDA_PADRAO
    pasta.mkdir(parents=True, exist_ok=True)
    arquivo = colacao['livro'].replace(' ', '_')
    (pasta / f'{arquivo}.json').write_text(
        json.dumps(colacao, ensure_ascii=False, indent=1) + '\n', encoding='utf-8'
    )
    (pasta / f'{arquivo}.md').write_text(markdown(colacao), encoding='utf-8')

    if argumentos.verso:
        entrada = colacao['versiculos'].get(argumentos.verso)
        if entrada is None:
            raise SystemExit(f'Versículo não colacionado: {argumentos.verso}')
        print(json.dumps(entrada, ensure_ascii=False, indent=1))
        return 0
    if argumentos.markdown:
        print(markdown(colacao))
        return 0
    print(f'Relatório em {pasta}/{arquivo}.json e .md')
    print(resumo(colacao))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
