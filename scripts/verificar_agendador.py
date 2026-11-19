#!/usr/bin/env python3
"""Diz, sem adivinhar, se o agendador está a produzir sozinho.

A pergunta que este script responde é só uma: **já houve alguma execução
disparada pelo cron?** Um `workflow_dispatch` (o botão "Run workflow") prova que
o pipeline funciona, mas não prova autonomia: quem carregou no botão foi uma
pessoa. Entre 16/11/2026 e 17/11/2026 o projeto teve exactamente um run, manual,
e zero agendados, durante mais de cinco horas — e isso não se vê na lista de
execuções sem filtrar por `event`.

Uso:

    python3 scripts/verificar_agendador.py            # vai buscar os dados com `gh`
    python3 scripts/verificar_agendador.py --json f.json   # analisa um ficheiro
    python3 scripts/verificar_agendador.py --repo dono/nome

Devolve 0 quando existe uma execução agendada recente e 1 quando não existe —
serve tanto para ler à mão como para correr num check.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

WORKFLOW = 'bee-autopiloto.yml'
REPO_PADRAO = 'martinhossmadureiraministries/traducao-epignosis'
# Uma produção horária deve aparecer dentro desta margem. Acima disto o
# agendador está parado, não só atrasado.
TOLERANCIA = timedelta(hours=3)


def _data(texto: str) -> datetime | None:
    if not texto:
        return None
    try:
        return datetime.strptime(texto, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def analisar(execucoes: Iterable[dict], agora: datetime | None = None) -> dict:
    """Resume uma lista de execuções (formato da API do GitHub).

    Função pura de propósito: os testes correm-na com dados inventados, sem
    rede e sem `gh`.
    """
    agora = agora or datetime.now(timezone.utc)
    if agora.tzinfo is None:
        agora = agora.replace(tzinfo=timezone.utc)

    corridas = []
    for item in execucoes:
        inicio = _data(item.get('created_at', ''))
        if inicio is None:
            continue
        corridas.append(
            {
                'id': item.get('id'),
                'evento': item.get('event') or '?',
                'inicio': inicio,
                'conclusao': item.get('conclusion') or item.get('status') or '?',
            }
        )
    corridas.sort(key=lambda r: r['inicio'])

    por_evento: dict[str, int] = {}
    for r in corridas:
        por_evento[r['evento']] = por_evento.get(r['evento'], 0) + 1

    agendadas = [r for r in corridas if r['evento'] == 'schedule']
    ultima = corridas[-1] if corridas else None
    ultima_agendada = agendadas[-1] if agendadas else None
    recentes = [r for r in corridas if agora - r['inicio'] <= timedelta(hours=24)]

    if not corridas:
        veredicto = 'sem-execucoes'
    elif ultima_agendada is None:
        veredicto = 'nunca-agendado'
    elif agora - ultima_agendada['inicio'] > TOLERANCIA:
        veredicto = 'parado'
    else:
        veredicto = 'a-funcionar'

    horas_sem_agendado = (
        round((agora - ultima_agendada['inicio']).total_seconds() / 3600, 1)
        if ultima_agendada
        else None
    )

    return {
        'veredicto': veredicto,
        'total': len(corridas),
        'por_evento': por_evento,
        'ultima': ultima,
        'ultima_agendada': ultima_agendada,
        'horas_sem_agendado': horas_sem_agendado,
        'ultimas_24h': len(recentes),
        'agora': agora,
    }


CONSELHOS = {
    'sem-execucoes': (
        'O workflow nunca correu. Abra Actions → BEE — produção automática e '
        'use "Run workflow" uma vez, para o GitHub registar o ficheiro.'
    ),
    'nunca-agendado': (
        'Só existem execuções manuais: o cron nunca disparou. Faça o passo 2 de '
        'docs/AGENDADOR.md (desativar e reativar o workflow na UI) e instale o '
        'relógio de segurança; se em 1 h continuar a zero, use o pinger externo.'
    ),
    'parado': (
        'Já houve execuções agendadas, mas nenhuma nas últimas 3 h. Veja o '
        'relógio de segurança (bee-relogio.yml) e o estado dos provedores.'
    ),
    'a-funcionar': (
        'O cron está a disparar: a produção continua com o computador desligado.'
    ),
}


def imprimir(resumo: dict) -> None:
    print(f"Execuções analisadas: {resumo['total']} (últimas 24 h: {resumo['ultimas_24h']})")
    if resumo['por_evento']:
        detalhe = ', '.join(f'{nome}={n}' for nome, n in sorted(resumo['por_evento'].items()))
        print(f'Por evento: {detalhe}')
    ultima = resumo['ultima']
    if ultima:
        print(f"Última execução: {ultima['inicio']:%Y-%m-%d %H:%M} UTC ({ultima['evento']}, {ultima['conclusao']})")
    agendada = resumo['ultima_agendada']
    if agendada:
        print(
            f"Última agendada: {agendada['inicio']:%Y-%m-%d %H:%M} UTC "
            f"({resumo['horas_sem_agendado']} h atrás)"
        )
    else:
        print('Última agendada: NENHUMA')
    print(f"Veredicto: {resumo['veredicto']} — {CONSELHOS[resumo['veredicto']]}")


def ler_da_api(repo: str) -> list[dict]:
    if shutil.which('gh') is None:
        raise SystemExit(
            'Não encontrei o `gh`. Instale-o (https://cli.github.com) ou passe '
            '--json com a resposta de:\n'
            f'  curl -H "Authorization: Bearer $TOKEN" \\\n    https://api.github.com/repos/{repo}/actions/workflows/{WORKFLOW}/runs'
        )
    saida = subprocess.run(
        [
            'gh',
            'api',
            f'repos/{repo}/actions/workflows/{WORKFLOW}/runs?per_page=100',
            '--jq',
            '{workflow_runs: [.workflow_runs[] | {id, event, status, conclusion, created_at}]}',
        ],
        capture_output=True,
        text=True,
    )
    if saida.returncode != 0:
        raise SystemExit(f'O `gh api` falhou:\n{saida.stderr.strip()}')
    return json.loads(saida.stdout).get('workflow_runs', [])


def main(argv: list[str] | None = None, agora: datetime | None = None) -> int:
    # `agora` só existe para os testes poderem fixar o relógio; em produção é
    # sempre None e vale o instante atual (comportamento inalterado).
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--repo', default=REPO_PADRAO)
    parser.add_argument('--json', type=Path, help='ficheiro com a resposta da API (para uso offline)')
    args = parser.parse_args(argv)

    if args.json:
        dados = json.loads(args.json.read_text(encoding='utf-8'))
        if isinstance(dados, list):
            execucoes = dados
        else:
            execucoes = dados.get('workflow_runs', [])
    else:
        execucoes = ler_da_api(args.repo)

    resumo = analisar(execucoes, agora)
    imprimir(resumo)
    return 0 if resumo['veredicto'] == 'a-funcionar' else 1


if __name__ == '__main__':
    raise SystemExit(main())
