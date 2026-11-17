"""A fila de provedores: OVHcloud, Gemini, Groq, OpenRouter.

Ordem por quanto cada um pode produzir e por quanto pede em troca. A OVHcloud
vai primeiro porque é o único que **não pede chave nenhuma** (2 pedidos por
minuto, sem conta, sem cartão). O Gemini dá a maior quota mas respondeu 503 em
rajada durante horas; a Groq é pequena mas fiável.

O Mistral saiu do rodízio gratuito em 17/11/2026 (o plano Free deixou de
activar chaves de API) e voltou depois como API paga do workflow durável —
só entra na fila do autopiloto se MISTRAL_API_KEY estiver definida.
Ver `test_mistral_so_entra_com_chave_e_e_pago`.
"""
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

import autopiloto
from bee.agenda import ConfigAgenda, Estado
from bee.ia import PROVEDORES


class OrdemDosProvedoresTest(unittest.TestCase):
    def _ordem(self, variavel=None) -> list[str]:
        valores = {'GROQ_API_KEY': 'k1', 'GEMINI_API_KEY': 'k2'}
        if variavel is not None:
            valores['BEE_PROVEDOR_PRINCIPAL'] = variavel
        args = autopiloto.argumentos([])
        with patch.dict(os.environ, valores, clear=True), \
             patch('autopiloto.resolver_modelos', return_value=['modelo']):
            return [m.provedor for m in autopiloto._motores(args, object())]

    def test_ovhcloud_responde_primeiro(self):
        self.assertEqual(self._ordem()[0], 'ovh', 'a OVHcloud não pede chave nenhuma')

    def test_fila_por_utilidade(self):
        """OVHcloud (sem chave) -> Gemini (480 ped) -> Groq (66 ped)."""
        self.assertEqual(self._ordem()[:3], ['ovh', 'gemini', 'groq'])

    def test_ovhcloud_entra_mesmo_sem_chave_nenhuma(self):
        """O ponto da OVHcloud: funciona com o ambiente vazio."""
        args = autopiloto.argumentos([])
        with patch.dict(os.environ, {}, clear=True), \
             patch('autopiloto.resolver_modelos', return_value=['modelo']):
            ordem = [m.provedor for m in autopiloto._motores(args, object())]
        self.assertEqual(ordem, ['ovh'])

    def test_ovhcloud_desliga_se_sem_variables(self):
        """Basta OVH_API_KEY_ATIVO=0 para a tirar da fila sem tocar no código."""
        args = autopiloto.argumentos([])
        ambiente = {'OVH_API_KEY_ATIVO': '0', 'GROQ_API_KEY': 'k'}
        with patch.dict(os.environ, ambiente, clear=True), \
             patch('autopiloto.resolver_modelos', return_value=['modelo']):
            ordem = [m.provedor for m in autopiloto._motores(args, object())]
        self.assertEqual(ordem, ['groq'])

    def test_mistral_so_entra_com_chave_e_e_pago(self):
        """17/11/2026 saiu do rodízio gratuito; voltou como API paga do workflow durável.

        No autopiloto gratuito só entra quem tem chave definida; sem
        MISTRAL_API_KEY definida, o rodízio não o considera.
        """
        config = PROVEDORES['mistral']
        self.assertIsNone(config.pedidos_por_dia)
        self.assertEqual(config.variavel, 'MISTRAL_API_KEY')
        self.assertFalse(config.sem_chave)

    def test_variavel_permite_inverter_sem_tocar_no_codigo(self):
        self.assertEqual(self._ordem('gemini')[0], 'gemini')
        self.assertEqual(self._ordem('groq')[0], 'groq')

    def test_variavel_desconhecida_e_ignorada(self):
        self.assertEqual(self._ordem('inventado')[0], 'ovh')


class OrcamentoPorProvedorTest(unittest.TestCase):
    def test_esgotar_um_provedor_nao_cala_o_outro(self):
        estado = Estado()
        chave = '2026-11-17'
        # A Groq esgota os 66 pedidos do dia.
        estado.gastou(chave, 'groq', 66, 396)
        self.assertEqual(estado.orcamento(chave, 'groq')['pedidos'], 66)
        # O Gemini continua com o seu próprio contador, a zero.
        self.assertEqual(estado.orcamento(chave, 'gemini')['pedidos'], 0)

    def test_contadores_por_provedor_sao_independentes(self):
        estado = Estado()
        estado.gastou('2026-11-17', 'groq', 5, 30)
        estado.gastou('2026-11-17', 'gemini', 7, 42)
        self.assertEqual(estado.orcamento('2026-11-17', 'groq'), {'pedidos': 5, 'versos': 30})
        self.assertEqual(estado.orcamento('2026-11-17', 'gemini'), {'pedidos': 7, 'versos': 42})

    def test_estado_antigo_sem_por_provedor_continua_a_funcionar(self):
        """O estado no ramo de dados foi escrito antes desta mudança."""
        antigo = {'dias': {'2026-11-17': {'pedidos': 10, 'versos': 60}}}
        estado = Estado.de_json(antigo)
        self.assertEqual(estado.orcamento('2026-11-17', 'groq')['pedidos'], 0)

    def test_tecto_da_groq_vem_do_limite_de_tokens_por_dia(self):
        tectos = autopiloto._tectos_por_provedor(6)
        self.assertIn('groq', tectos)
        # 200.000 tokens/dia ÷ (6 versículos × 500 tokens) ≈ 66 pedidos.
        self.assertEqual(tectos['groq'], 66)
        self.assertEqual(PROVEDORES['groq'].tokens_por_dia, 200_000)

    def test_gemini_nao_tem_tecto_de_tokens_por_dia_apertado(self):
        """O Gemini tem mais quota: é por isso que fica como reserva útil."""
        self.assertEqual(PROVEDORES['gemini'].tokens_por_dia, 0)
        self.assertGreater(PROVEDORES['gemini'].tokens_por_minuto,
                           PROVEDORES['groq'].tokens_por_minuto)


if __name__ == '__main__':
    unittest.main()
