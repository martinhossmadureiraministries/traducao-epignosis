"""A fila de provedores: Mistral, Gemini, Groq, OpenRouter.

O Gemini deu 503 em rajada durante horas. A Groq respondia sempre que tinha
tokens, mas a quota dela é pequena (200.000 tokens/dia). O Mistral entrou
como principal porque dá 1.000 milhões de tokens/mês sem cartão — vinte vezes
a Groq. A fila só é segura porque cada serviço tem o seu próprio orçamento:
esgotar um não cala os outros.
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
        valores = {'GROQ_API_KEY': 'k1', 'GEMINI_API_KEY': 'k2', 'MISTRAL_API_KEY': 'k3'}
        if variavel is not None:
            valores['BEE_PROVEDOR_PRINCIPAL'] = variavel
        args = autopiloto.argumentos([])
        with patch.dict(os.environ, valores, clear=True), \
             patch('autopiloto.resolver_modelos', return_value=['modelo']):
            return [m.provedor for m in autopiloto._motores(args, object())]

    def test_mistral_responde_primeiro(self):
        self.assertEqual(self._ordem()[0], 'mistral', 'o Mistral tem a maior quota gratuita')

    def test_fila_por_quota_decrescente(self):
        """Mistral (1e9 tokens/mês) -> Gemini (480 ped) -> Groq (66 ped)."""
        self.assertEqual(self._ordem()[:3], ['mistral', 'gemini', 'groq'])

    def test_sem_mistral_a_fila_comeca_no_gemini(self):
        args = autopiloto.argumentos([])
        with patch.dict(os.environ, {'GROQ_API_KEY': 'k1', 'GEMINI_API_KEY': 'k2'}, clear=True), \
             patch('autopiloto.resolver_modelos', return_value=['modelo']):
            ordem = [m.provedor for m in autopiloto._motores(args, object())]
        self.assertEqual(ordem[:2], ['gemini', 'groq'])

    def test_variavel_permite_inverter_sem_tocar_no_codigo(self):
        self.assertEqual(self._ordem('gemini')[0], 'gemini')
        self.assertEqual(self._ordem('groq')[0], 'groq')

    def test_variavel_desconhecida_e_ignorada(self):
        self.assertEqual(self._ordem('inventado')[0], 'mistral')


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
