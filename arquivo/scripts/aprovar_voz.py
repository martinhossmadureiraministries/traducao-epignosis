#!/usr/bin/env python3
"""Faz crescer a memória de estilo com as aprovações do responsável (P3).

A memória (`modelos/estilo_bee.json`) é viva: o glossário e as âncoras devem
aumentar à medida que mais texto é aprovado. Este script aplica essas decisões
de forma mecânica E validada — qualquer alteração que viole o schema é recusada
antes de tocar no ficheiro (nunca parte a fonte única da voz).

Subcomandos:
    capitulos   regista uma aprovação humana (entra em `aprovacoes`)
    glossario   acrescenta/fixa uma decisão lexical (ex.: palavra nova aprovada)
    amostra     promove um versículo aprovado a âncora de voz do género

Uso:
    python3 scripts/aprovar_voz.py capitulos 600 1 2 3 --nota "registo equilibrado"
    python3 scripts/aprovar_voz.py glossario --grego μακροθυμία --transliteracao makrothymía \
        --usar "«paciência»" --sentido "esperança ativa, não passividade."
    python3 scripts/aprovar_voz.py amostra --referencia "2 Tessalonicenses 1:3" \
        --texto "Devemos dar sempre graças a Deus por vocês…" --porque "ação de graças coesa"
    (acrescente --dry-run a qualquer um para ver sem escrever;
     --memoria CAMINHO usa outro ficheiro, p.ex. em testes.)
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from bee.catalogo import POR_NUMERO  # noqa: E402
from bee.memoria_estilo import validar  # noqa: E402


def _carregar(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding='utf-8'))


def _guardar(caminho: Path, dados: dict) -> None:
    erros = validar(dados)
    if erros:
        raise ValueError('alteração recusada pela validação do schema:\n- ' + '\n- '.join(erros))
    temporario = caminho.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8')
    os.replace(temporario, caminho)


def aprovar_capitulos(memoria: dict, numero: int, capitulos: list[int], nota: str) -> str:
    """Regista a aprovação em `aprovacoes`; devolve a entrada acrescentada."""
    livro = POR_NUMERO.get(numero)
    nome = livro.nome if livro else str(numero)
    unicos = sorted(set(capitulos))
    trechos = ', '.join(str(c) for c in unicos)
    sufixo = f' — {nota}' if nota.strip() else ''
    entrada = f'{nome} ({numero}), caps. {trechos}, aprovado pelo responsável em {date.today().isoformat()}{sufixo}'
    aprovacoes = memoria.setdefault('aprovacoes', [])
    if not any(e.startswith(f'{nome} ({numero})') for e in aprovacoes):
        aprovacoes.append(entrada)
    return entrada


def fixar_glossario(memoria: dict, grego: str | None, termo: str | None, usar: str,
                    sentido: str | None = None, rejeitar: str | None = None,
                    nao_estender: str | None = None, exemplo: str | None = None,
                    transliteracao: str | None = None) -> dict:
    """Acrescenta uma entrada ao glossário (ou atualiza a existente pela chave)."""
    chave = grego or termo
    if not chave:
        raise ValueError('indique --grego (com --transliteracao) ou --termo')
    if grego and not transliteracao:
        raise ValueError('--grego exige --transliteracao')
    entradas = memoria.setdefault('glossario', [])
    alvo = next((e for e in entradas
                 if e.get('grego') == grego or (grego is None and e.get('termo') == termo)), None)
    if alvo is None:
        alvo = {}
        entradas.append(alvo)
    if grego:
        alvo['grego'] = grego
        alvo['transliteracao'] = transliteracao
        alvo.pop('termo', None)
    else:
        alvo['termo'] = termo
        alvo.pop('grego', None)
        alvo.pop('transliteracao', None)
    alvo['usar'] = usar
    for campo, valor in (('sentido', sentido), ('rejeitar', rejeitar),
                         ('nao_estender_a', nao_estender), ('exemplo_aprovado', exemplo)):
        if valor:
            alvo[campo] = valor
    return alvo


def promover_amostra(memoria: dict, referencia: str, texto: str, porque: str,
                     genero: str = 'carta') -> dict:
    """Promove um versículo aprovado a âncora de voz do género indicado."""
    ancoras = memoria.setdefault('ancoras', {})
    amostras = ancoras.setdefault('amostras', [])
    if any(a.get('referencia') == referencia for a in amostras):
        raise ValueError(f'já existe amostra com a referência {referencia!r}; edite o JSON')
    amostra = {'referencia': referencia, 'genero': genero, 'texto': texto, 'porque': porque}
    amostras.append(amostra)
    por_genero = ancoras.setdefault('por_genero', {})
    por_genero.setdefault(genero, []).append(referencia)
    return amostra


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--memoria', type=Path, default=RAIZ / 'modelos' / 'estilo_bee.json',
                        help='ficheiro da memória de estilo (padrão: modelos/estilo_bee.json)')
    parser.add_argument('--dry-run', action='store_true', help='mostra sem escrever')
    sub = parser.add_subparsers(dest='comando', required=True)

    p_cap = sub.add_parser('capitulos', help='registar aprovação de capítulos')
    p_cap.add_argument('numero', type=int, help='book_number (ex.: 600)')
    p_cap.add_argument('capitulos', type=int, nargs='+', help='capítulos aprovados')
    p_cap.add_argument('--nota', default='', help='observação curta da aprovação')

    p_glo = sub.add_parser('glossario', help='acrescentar/fixar decisão lexical')
    p_glo.add_argument('--grego', help='forma grega (ex.: σπλάγχνα)')
    p_glo.add_argument('--transliteracao', help='transliteração (ex.: splanchna)')
    p_glo.add_argument('--termo', help='assunto sem grego (ex.: «Tetragrama e títulos»)')
    p_glo.add_argument('--usar', required=True, help='palavra/forma a usar (entre «…»)')
    p_glo.add_argument('--sentido', help='alcance no contexto')
    p_glo.add_argument('--rejeitar', help='o que NÃO usar e porquê')
    p_glo.add_argument('--nao-estender', help='onde a regra NÃO se aplica')
    p_glo.add_argument('--exemplo', help='exemplo aprovado (referência + texto)')

    p_amo = sub.add_parser('amostra', help='promover versículo aprovado a âncora')
    p_amo.add_argument('--referencia', required=True, help='ex.: «Filemom 1:7»')
    p_amo.add_argument('--texto', required=True, help='texto aprovado, sem aspas')
    p_amo.add_argument('--porque', required=True, help='razão editorial curta')
    p_amo.add_argument('--genero', default='carta', help='género literário (padrão: carta)')

    args = parser.parse_args()
    if not args.memoria.exists():
        print(f'Memória de estilo não encontrada: {args.memoria}', file=sys.stderr)
        return 2
    memoria = _carregar(args.memoria)
    try:
        if args.comando == 'capitulos':
            resultado = aprovar_capitulos(memoria, args.numero, args.capitulos, args.nota)
        elif args.comando == 'glossario':
            resultado = fixar_glossario(
                memoria, args.grego, args.termo, args.usar, sentido=args.sentido,
                rejeitar=args.rejeitar, nao_estender=args.nao_estender,
                exemplo=args.exemplo, transliteracao=args.transliteracao)
        else:
            resultado = promover_amostra(memoria, args.referencia, args.texto,
                                         args.porque, args.genero)
    except ValueError as exc:
        print(f'Erro: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(resultado, ensure_ascii=False, indent=2))
    if args.dry_run:
        print('(dry-run: nada foi escrito)', file=sys.stderr)
        return 0
    try:
        _guardar(args.memoria, memoria)
    except ValueError as exc:
        print(f'Gravação recusada: {exc}', file=sys.stderr)
        return 2
    print(f'\nMemória atualizada: {args.memoria}', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
