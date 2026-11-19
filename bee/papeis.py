"""Papéis dos provedores na convergência multi-provedor (P2).

Todos os provedores configurados podem traduzir; a revisão de voz prefere uma
ORDEM própria e, sobretudo, um modelo DIFERENTE do autor do capítulo — é isso
que faz da revisão uma "segunda IA" e não uma confirmação do mesmo vício. A
disponibilidade vem sempre primeiro: se só resta o autor, revisa ele mesmo
(antes revista por quem há do que não revista).

A ordem de revisão favorece modelos de instrução forte em português e planos
gratuitos folgados; ajusta-se aqui sem tocar no motor.
"""
from __future__ import annotations

from typing import Iterable

# Prioridade para REVISÃO DE VOZ (o autor do capítulo é excluído quando há
# alternativa). Proveedores fora desta lista entram a seguir, pela ordem dada.
ORDEM_REVISORES = (
    'cerebras',     # rápido e folgado no plano gratuito
    'gemini',       # forte em português; só evita rever o que ele próprio escreveu
    'groq',
    'openrouter',   # dá acesso a famílias de modelos distintas das internas
    'cohere',
    'mistral',
    'nvidia',
    'openai',
    'ovh',
)


def ordenar_revisores(provedores: Iterable[str],
                      pontuacoes: dict[str, float] | None = None) -> list[str]:
    """Ordena pela prioridade de revisão; desconhecidos vão no fim, estáveis.

    Com ``pontuacoes`` (taxa de chumbo por provedor vinda das métricas P3),
    menos deriva passa à frente; quem não tem dados medidos fica na ordem
    estática de reserva. O resultado é sempre determinístico.
    """
    unicos = sorted(set(p for p in provedores if p))

    def chave(nome: str) -> tuple[int | float, int | str, str]:
        if pontuacoes and nome in pontuacoes:
            empate_estatico = ORDEM_REVISORES.index(nome) if nome in ORDEM_REVISORES else 99
            return (pontuacoes[nome], empate_estatico, nome)
        indice = ORDEM_REVISORES.index(nome) if nome in ORDEM_REVISORES else None
        if indice is not None:
            return (float('inf'), indice, nome)
        return (float('inf'), 100, nome)

    if pontuacoes:
        return sorted(unicos, key=chave)

    def chave_estatica(nome: str) -> tuple[int, int | str]:
        if nome in ORDEM_REVISORES:
            return (0, ORDEM_REVISORES.index(nome))
        return (1, nome)

    return sorted(unicos, key=chave_estatica)


def revisores_disponiveis(provedores_ativos: Iterable[str],
                          autor: str | None = None,
                          pontuacoes: dict[str, float] | None = None) -> list[str]:
    """Revisores para um capítulo, por prioridade, excluindo o autor.

    Se excluir o autor deixar a lista vazia, ele volta: produção revista vale
    mais do que produção sem revisão. Sem provedores ativos, lista vazia.
    """
    ativos = [p for p in provedores_ativos if p]
    ordenados = ordenar_revisores(ativos, pontuacoes=pontuacoes)
    if autor and len(ordenados) > 1:
        return [p for p in ordenados if p != autor] or ordenados
    return ordenados
