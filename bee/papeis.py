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


def ordenar_revisores(provedores: Iterable[str]) -> list[str]:
    """Ordena pela prioridade de revisão; desconhecidos vão no fim, estáveis."""
    unicos = sorted(set(provedores))  # dedup determinístico
    def chave(nome: str) -> tuple[int, int | str]:
        if nome in ORDEM_REVISORES:
            return (0, ORDEM_REVISORES.index(nome))
        return (1, nome)
    return sorted(unicos, key=chave)


def revisores_disponiveis(provedores_ativos: Iterable[str],
                          autor: str | None = None) -> list[str]:
    """Revisores para um capítulo, por prioridade, excluindo o autor.

    Se excluir o autor deixar a lista vazia, ele volta: produção revista vale
    mais do que produção sem revisão. Sem provedores ativos, lista vazia.
    """
    ativos = [p for p in provedores_ativos if p]
    ordenados = ordenar_revisores(ativos)
    if autor and len(ordenados) > 1:
        return [p for p in ordenados if p != autor] or ordenados
    return ordenados
