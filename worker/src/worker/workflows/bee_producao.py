"""Workflow durável `bee-producao`.

Cada iteração é uma fatia (atividade): sincroniza os JSON com o ramo de dados
no GitHub, gera um orçamento de versículos com modelos Mistral, valida, commita
e, quando um capítulo completa, recompila os módulos MyBible e atualiza a
release de prévia. O `continue-as-new` permite correr até aos 1.189 capítulos
sem estourar o histórico; os signals permitem novas diretrizes e paragem sem
interromper o que já foi feito.
"""
from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import mistralai.workflows as workflows
from pydantic import BaseModel

from worker import producao

REPOSITORIO_PADRAO = 'martinhossmadureiraministries/traducao-epignosis'
FALHAS_PARA_PARAR = 3


class EntradaProducao(BaseModel):
    repositorio: str = REPOSITORIO_PADRAO
    ramo_dados: str = 'bee-dados'
    modelo: str = 'mistral-medium-latest'
    versos_por_fatia: int = 24
    versos_por_pedido: int = 8
    fatias_maximas: int = 60
    compilar: bool = True
    publicar_release: bool = True
    orientacoes: str = ''
    ordem: list[int] | None = None


class EstadoProducao(EntradaProducao):
    fatias_feitas: int = 0
    falhas_consecutivas: int = 0


@workflows.activity(start_to_close_timeout=timedelta(minutes=40))
async def fatia_producao(estado: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(producao.executar_fatia, estado)


@workflows.workflow.define(
    name='bee-producao',
    workflow_display_name='BEE — produção contínua',
    workflow_description=(
        'Produz a Bíblia de Estudo Epignósis em fatias com modelos Mistral, '
        'commita o progresso no GitHub e publica os módulos MyBible.'
    ),
    execution_timeout=timedelta(hours=24),
)
class BeeProducao:
    def __init__(self) -> None:
        self.orientacoes_novas: str | None = None
        self.parar: bool = False

    @workflows.workflow.signal(name='orientacoes')
    async def receber_orientacoes(self, texto: str) -> None:
        self.orientacoes_novas = texto

    @workflows.workflow.signal(name='parar')
    async def parar_producao(self) -> None:
        self.parar = True

    @workflows.workflow.query(name='estado')
    def estado_atual(self) -> dict[str, Any]:
        return {'parar': self.parar, 'orientacoes_pendentes': self.orientacoes_novas is not None}

    @workflows.workflow.entrypoint
    async def run(self, estado: EstadoProducao) -> dict[str, Any]:
        resumo: dict[str, Any] = {
            'fatias': 0, 'versos': 0, 'capitulos': 0,
            'concluido': False, 'parado': False, 'ultima_fatia': None,
        }
        for _ in range(estado.fatias_maximas):
            if self.parar:
                resumo['parado'] = True
                break
            if self.orientacoes_novas is not None:
                estado.orientacoes = self.orientacoes_novas
                self.orientacoes_novas = None
            resultado = await fatia_producao(estado.model_dump())
            resumo['fatias'] += 1
            resumo['versos'] += resultado.get('versos', 0)
            resumo['capitulos'] += resultado.get('capitulos', 0)
            resumo['ultima_fatia'] = resultado
            if resultado.get('concluido'):
                resumo['concluido'] = True
                break
            if resultado.get('versos', 0) == 0:
                estado.falhas_consecutivas += 1
                if estado.falhas_consecutivas >= FALHAS_PARA_PARAR:
                    resumo['motivo_paragem'] = 'fatias consecutivas sem produção'
                    break
            else:
                estado.falhas_consecutivas = 0
            if workflows.workflow.should_continue_as_new():
                workflows.workflow.continue_as_new(estado)
        return resumo
