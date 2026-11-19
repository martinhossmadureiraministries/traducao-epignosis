"""Métricas de qualidade por provedor (P3 da convergência multi-provedor).

Recolhe o que já está gravado — a ``history`` de cada livro (quem gerou o quê),
a quarentena de estilo (quem foi chumbado) e o caderno de revisões (quem teve
versos emendados pela segunda IA e quem fez revisões) — e transforma em números
por provedor. Dois usos:

* relatório humano/CI (``scripts/metricas_provedores.py`` e resumo do workflow);
* prioridade opcional dos revisores: com ``BEE_PRIORIDADES=metricas``, o
  agendador ordena os revisores pela taxa de chumbo (menos deriva = primeiro).

Tudo derivado de dados, sem rede; diretórios vazios ou ficheiros corrompidos
dão métricas parciais/zeradas, nunca erros — um relatório não pode parar nada.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass
class MetricaProvedor:
    nome: str
    versos_gerados: int = 0        # versículos escritos como tradutor
    lotes: int = 0                 # pedidos de geração concluídos
    chumbos_estilo: int = 0        # versos seus recusados pela porta de estilo
    emendas_recebidas: int = 0     # versos seus corrigidos pelo revisor de voz
    revisoes_feitas: int = 0       # capítulos que reviu como segunda IA
    versos_revistos: int = 0

    @property
    def chumbos_por_100(self) -> float:
        """Taxa de deriva dura; o número que compara a confiança entre provedores."""
        if not self.versos_gerados:
            return 0.0
        return round(100.0 * self.chumbos_estilo / self.versos_gerados, 2)


def _versos_da_entrada(entrada: dict) -> int:
    try:
        return max(0, int(entrada['verse_to']) - int(entrada['verse_from']) + 1)
    except (KeyError, TypeError, ValueError):
        return 0


def recolher(dados_dir: Path) -> dict[str, MetricaProvedor]:
    """Varre uma pasta ``livros_json`` e devolve métricas por provedor."""
    metricas: dict[str, MetricaProvedor] = {}

    def conta(nome: str) -> MetricaProvedor:
        return metricas.setdefault(nome, MetricaProvedor(nome))

    # Quem escreveu cada capítulo (para atribuir emendas do revisor ao autor).
    autores_por_capitulo: dict[tuple[int, int], set[str]] = {}
    for caminho in sorted(dados_dir.glob('*.json')):
        try:
            dados = json.loads(caminho.read_text(encoding='utf-8'))
        except (OSError, UnicodeError, ValueError):
            continue
        livro_numero = dados.get('book_number')
        if not isinstance(livro_numero, int):
            continue
        for entrada in dados.get('history') or []:
            if not isinstance(entrada, dict):
                continue
            provedor = str(entrada.get('provider') or '')
            capitulo = entrada.get('chapter')
            if not provedor or not isinstance(capitulo, int):
                continue
            versos = _versos_da_entrada(entrada)
            if provedor.startswith('revisao:'):
                revisor = provedor[len('revisao:'):]
                conta(revisor).revisoes_feitas += 1
                conta(revisor).versos_revistos += versos
                continue
            if provedor == 'local':
                continue
            conta(provedor).lotes += 1
            conta(provedor).versos_gerados += versos
            autores_por_capitulo.setdefault((livro_numero, capitulo), set()).add(provedor)

    # Emendas do caderno de revisões → contabilidade para o AUTOR emendado.
    caderno = dados_dir / '.bee' / 'revisoes.json'
    for entrada in _entradas(caderno):
        chave = (entrada.get('book'), entrada.get('chapter'))
        for autor in autores_por_capitulo.get(chave, ()):  # type: ignore[arg-type]
            conta(autor).emendas_recebidas += 1

    # Chumbos da porta de estilo → todos os provedores que tentaram o lote.
    quarentena = dados_dir / '.bee' / 'quarentena.json'
    for entrada in _entradas(quarentena):
        if entrada.get('status') != 'chumbado-estilo':
            continue
        marcas = entrada.get('style_marks')
        peso = len(marcas) if isinstance(marcas, dict) and marcas else 1
        autores = {str(a) for a in (entrada.get('providers_tried') or []) if a}
        if entrada.get('provider'):
            autores.add(str(entrada['provider']))
        for autor in autores:
            conta(autor).chumbos_estilo += peso

    return metricas


def _entradas(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    try:
        lido = json.loads(caminho.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return []
    entradas = lido.get('entries') if isinstance(lido, dict) else None
    if not isinstance(entradas, list):
        return []
    return [e for e in entradas if isinstance(e, dict)]


def pontuacoes(metricas: dict[str, MetricaProvedor]) -> dict[str, float]:
    """Nome → taxa de chumbo (menor = mais confiável); só quem já gerou texto."""
    return {nome: m.chumbos_por_100 for nome, m in metricas.items() if m.versos_gerados}


def ordenar_confianca(metricas: dict[str, MetricaProvedor]) -> list[str]:
    """Melhores primeiro: menos deriva por 100 versos; empate → mais volume."""
    com_dados = [m for m in metricas.values() if m.versos_gerados]
    com_dados.sort(key=lambda m: (m.chumbos_por_100, -m.versos_gerados, m.nome))
    return [m.nome for m in com_dados]


def tabela(metricas: dict[str, MetricaProvedor]) -> str:
    """Relatório legível, pior deriva primeiro (é o que interessa investigar)."""
    linhas = ['provedor      versos  lotes  chumbos  chumbos/100  emendas  revisões']
    ordenados = sorted(metricas.values(),
                       key=lambda m: (-m.chumbos_por_100, -m.versos_gerados, m.nome))
    for m in ordenados:
        linhas.append(
            f'{m.nome:<13} {m.versos_gerados:>6}  {m.lotes:>5}  {m.chumbos_estilo:>7}'
            f'  {m.chumbos_por_100:>11}  {m.emendas_recebidas:>7}  {m.revisoes_feitas:>8}')
    if len(linhas) == 1:
        linhas.append('(ainda sem dados de produção nesta pasta)')
    return '\n'.join(linhas)


def guardar(dados_dir: Path, metricas: dict[str, MetricaProvedor]) -> Path:
    """Cache em ``.bee/metricas.json`` para o agendador usar como prioridade."""
    pasta = dados_dir / '.bee'
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / 'metricas.json'
    payload = {'pontuacoes': pontuacoes(metricas),
               'confianca': ordenar_confianca(metricas),
               'detalhe': {nome: asdict(m) for nome, m in sorted(metricas.items())}}
    temporario = destino.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8')
    temporario.replace(destino)
    return destino


def carregar_pontuacoes(dados_dir: Path) -> dict[str, float] | None:
    """Lê o cache das pontuações; None se não existir (prioridades ficam padrão)."""
    caminho = dados_dir / '.bee' / 'metricas.json'
    if not caminho.exists():
        return None
    try:
        lido = json.loads(caminho.read_text(encoding='utf-8'))
    except (OSError, UnicodeError, ValueError):
        return None
    pontos = lido.get('pontuacoes') if isinstance(lido, dict) else None
    if not isinstance(pontos, dict):
        return None
    return {str(k): float(v) for k, v in pontos.items()
            if isinstance(v, (int, float))}
