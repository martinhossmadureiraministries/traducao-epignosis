"""Workflow `bee-producao`: loop de fatias, paragens e resumo — Temporal simulado."""
import pytest

from mistralai.workflows.testing import create_test_worker
from worker import producao
from worker.workflows.bee_producao import BeeProducao, EntradaProducao, fatia_producao


def fatia_fake(chamadas: list[dict]):
    def executar(estado: dict) -> dict:
        chamadas.append(estado)
        if len(chamadas) < 2:
            return {
                'versos': 24, 'capitulos': 1, 'pedidos': 3, 'concluido': False,
                'alterado': True, 'livro': 'Filemom', 'capitulo_atual': 1,
                'motivos': [], 'commit': 'sha-1', 'modelo': 'Mistral AI · mistral-medium-latest',
            }
        return {
            'versos': 12, 'capitulos': 1, 'pedidos': 2, 'concluido': True,
            'alterado': True, 'livro': None, 'capitulo_atual': None,
            'motivos': [], 'commit': 'sha-2', 'modelo': 'Mistral AI · mistral-medium-latest',
        }
    return executar


async def test_corre_ate_concluir(temporal_env, monkeypatch):
    chamadas: list[dict] = []
    monkeypatch.setattr(producao, 'executar_fatia', fatia_fake(chamadas))
    async with create_test_worker(temporal_env, [BeeProducao], activities=[fatia_producao]):
        handle = await temporal_env.client.start_workflow(
            BeeProducao.run, EntradaProducao(fatias_maximas=5),
            id='bee-teste-concluir', task_queue='test-task-queue',
        )
        resumo = (await handle.result()).get('result', {})
    assert resumo['fatias'] == 2
    assert resumo['concluido'] is True
    assert resumo['versos'] == 36
    assert resumo['capitulos'] == 2
    assert len(chamadas) == 2


async def test_para_por_fatias_maximas(temporal_env, monkeypatch):
    chamadas: list[dict] = []

    def executar(estado: dict) -> dict:
        chamadas.append(estado)
        return {
            'versos': 24, 'capitulos': 1, 'pedidos': 3, 'concluido': False,
            'alterado': True, 'livro': 'Filemom', 'capitulo_atual': 1,
            'motivos': [], 'commit': 'sha', 'modelo': 'x',
        }

    monkeypatch.setattr(producao, 'executar_fatia', executar)
    async with create_test_worker(temporal_env, [BeeProducao], activities=[fatia_producao]):
        handle = await temporal_env.client.start_workflow(
            BeeProducao.run, EntradaProducao(fatias_maximas=3),
            id='bee-teste-maximo', task_queue='test-task-queue',
        )
        resumo = (await handle.result()).get('result', {})
    assert resumo['fatias'] == 3
    assert resumo['concluido'] is False
    assert len(chamadas) == 3


async def test_para_apos_falhas_consecutivas(temporal_env, monkeypatch):
    chamadas: list[dict] = []

    def executar(estado: dict) -> dict:
        chamadas.append(estado)
        return {
            'versos': 0, 'capitulos': 0, 'pedidos': 0, 'concluido': False,
            'alterado': False, 'livro': None, 'capitulo_atual': 1,
            'motivos': ['erro simulado'], 'commit': '', 'modelo': 'x',
        }

    monkeypatch.setattr(producao, 'executar_fatia', executar)
    async with create_test_worker(temporal_env, [BeeProducao], activities=[fatia_producao]):
        handle = await temporal_env.client.start_workflow(
            BeeProducao.run, EntradaProducao(fatias_maximas=10),
            id='bee-teste-falhas', task_queue='test-task-queue',
        )
        resumo = (await handle.result()).get('result', {})
    assert resumo.get('motivo_paragem') == 'fatias consecutivas sem produção'
    assert resumo['fatias'] == 3
