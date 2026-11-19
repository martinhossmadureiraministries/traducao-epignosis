"""Perfis de edição: a linha legada fica byte-idêntica; a nova só entra por opção."""
import json
import os
import unittest
from unittest import mock

from bee.catalogo import POR_NUMERO
from bee.gerador import GLOSSARIO_PADRAO, _contexto_estilo
from bee.ia import PROMPT_REVISAO, SYSTEM_PROMPT, MotorIA
from bee.perfil import PERFIL_PADRAO, PERFIS, VARIAVEL_AMBIENTE, resolver_perfil


class PerfilTest(unittest.TestCase):
    def test_padrao_e_legado(self):
        self.assertEqual(PERFIL_PADRAO, 'legado')
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertIs(resolver_perfil(), PERFIS['legado'])

    def test_legado_reutiliza_constantes_herdadas_sem_mudanca(self):
        legado = PERFIS['legado']
        self.assertEqual(legado.system_prompt, SYSTEM_PROMPT)
        self.assertEqual(legado.prompt_revisao, PROMPT_REVISAO)
        self.assertEqual(legado.glossario, GLOSSARIO_PADRAO)
        self.assertEqual(legado.amostras, '', 'o legado não envia âncoras de voz')
        self.assertEqual(legado.sistema(True), SYSTEM_PROMPT + PROMPT_REVISAO)
        self.assertEqual(legado.sistema(False), SYSTEM_PROMPT)

    def test_nova_tem_voz_propria_e_glossario_de_epignosis(self):
        novo = PERFIS['nova']
        self.assertNotEqual(novo.system_prompt, SYSTEM_PROMPT)
        self.assertIn('ESTILO_BEE', novo.system_prompt)
        self.assertIn('epignōsis', novo.glossario)
        self.assertIn('pleno conhecimento', novo.glossario)

    def test_nova_traz_ancoras_das_cartas_aprovadas(self):
        amostras = PERFIS['nova'].amostras
        self.assertTrue(amostras)
        # Âncoras fiéis aos pilotos já aprovados (não apenas Filemom).
        for carta in ('Filemom', 'Tito', 'Judas', '2 João'):
            self.assertIn(carta, amostras)
        self.assertIn('pleno conhecimento', amostras)

    def test_nova_proibe_hesitacao_arcaismos_e_copia_da_almeida(self):
        sp = PERFIS['nova'].system_prompt
        for marca in ('SEM HESITAÇÃO', 'NADA DE ARCAÍSMOS', 'VOZ PRÓPRIA', 'REVISÃO FINAL'):
            self.assertIn(marca, sp)
        # formas arcaicas explicitamente vedadas no texto da instrução
        self.assertIn('vós/vos/vosso/vossa/convosco', sp)

    def test_nova_traz_contrastes_e_formulas_consolidadas(self):
        amostras = PERFIS['nova'].amostras
        self.assertIn('CONTRASTES', amostras)
        self.assertIn('FÓRMULAS CONSOLIDADAS', amostras)
        self.assertIn('Graça e paz a vocês', amostras)   # saudação igual aos pilotos
        self.assertIn('→', amostras)                      # pares mau→bom

    def test_nova_tem_aperto_de_calibracao_fina(self):
        sp = PERFIS['nova'].system_prompt
        for marca in ('CONSISTÊNCIA DE TRATAMENTO', 'CORRENTES DE GENITIVOS',
                      'CONCISÃO CONCRETA', 'COERÊNCIA ENTRE LIVROS', 'SEM METALINGUAGEM'):
            self.assertIn(marca, sp)

    def test_ambiente_seleciona_perfil(self):
        with mock.patch.dict(os.environ, {VARIAVEL_AMBIENTE: 'nova'}):
            self.assertEqual(resolver_perfil().nome, 'nova')
        with mock.patch.dict(os.environ, {VARIAVEL_AMBIENTE: 'LEGADO'}):
            self.assertEqual(resolver_perfil().nome, 'legado', 'maiúsculas são aceites')

    def test_argumento_explícito_sobrepoe_ambiente(self):
        with mock.patch.dict(os.environ, {VARIAVEL_AMBIENTE: 'nova'}):
            self.assertEqual(resolver_perfil('legado').nome, 'legado')

    def test_perfil_desconhecido_e_erro_de_configuracao(self):
        with self.assertRaises(ValueError):
            resolver_perfil('inexistente')
        with mock.patch.dict(os.environ, {VARIAVEL_AMBIENTE: 'inexistente'}):
            with self.assertRaises(ValueError):
                resolver_perfil()


class MotorPerfilTest(unittest.TestCase):
    def _motor(self, perfil=None):
        return MotorIA('openai', 'gpt-6-luna', 'CHAVE', None, 4096,
                       aplicar_revisao=False, perfil=perfil)

    def test_sem_perfil_mantem_system_legado(self):
        self.assertEqual(self._motor()._system(), SYSTEM_PROMPT)

    def test_com_perfil_novo_muda_o_system(self):
        motor = self._motor(perfil=PERFIS['nova'])
        texto = motor._system()
        self.assertIn('ESTILO_BEE', texto)
        self.assertNotIn(SYSTEM_PROMPT[:40], texto)


class ContextoEstiloTest(unittest.TestCase):
    def test_glossario_padrao_sem_ambiente(self):
        with mock.patch.dict(os.environ, {}, clear=True):
            estilo = _contexto_estilo({}, 1, [])
        self.assertEqual(estilo['glossario'], GLOSSARIO_PADRAO)
        self.assertNotIn('amostras', estilo, 'o legado não pode ganhar a chave')

    def test_glossario_e_ancoras_novas_com_ambiente(self):
        with mock.patch.dict(os.environ, {VARIAVEL_AMBIENTE: 'nova'}):
            estilo = _contexto_estilo({}, 1, [])
        self.assertIn('epignōsis', estilo['glossario'])
        self.assertIn('Filemom', estilo['amostras'])


class HTTPFalso:
    def __init__(self, resposta: dict):
        self.resposta = resposta
        self.requisicoes = []

    def obter(self, req, descricao, limite=None, log=None, provedor=None):
        self.requisicoes.append((req, descricao))
        return json.dumps(self.resposta, ensure_ascii=False).encode()


def _resposta_ok(numero: int) -> dict:
    conteudo = {'verses': [{
        'verse': numero, 'text': 'Texto de exemplo.',
        'commentary': '<p>Análise Léxica x</p><p>Crítica Textual y</p><p>Síntese Exegética z</p>',
    }]}
    return {'choices': [{'finish_reason': 'stop',
                         'message': {'content': json.dumps(conteudo, ensure_ascii=False)}}]}


class AncorasNaMensagemTest(unittest.TestCase):
    """As âncoras de voz têm de viajar na mensagem do utilizador, antes das fontes."""

    def _gerar(self, estilo):
        http = HTTPFalso(_resposta_ok(1))
        motor = MotorIA('openai', 'gpt-6-luna', 'CHAVE', http, 4096,
                        aplicar_revisao=False, perfil=PERFIS['nova'])
        fontes = [{'verse': 1, 'base': [{'texto': 'ἀρχή'}]}]
        resultado = motor.gerar(POR_NUMERO[500], 1, fontes, estilo=estilo)
        self.assertEqual([v['verse'] for v in resultado], [1])
        req, _ = http.requisicoes[0]
        payload = json.loads(req.data)
        return payload['messages'][1]['content']

    def test_ancoras_presentes_quando_fornecidas(self):
        corpo = self._gerar({'amostras': 'AMOSTRA_UNICA_DE_TESTE'})
        self.assertIn('AMOSTRA_UNICA_DE_TESTE', corpo)
        self.assertIn('referências de estilo', corpo)

    def test_sem_ancoras_a_mensagem_nao_muda_para_o_legado(self):
        corpo = self._gerar({'glossario': GLOSSARIO_PADRAO})
        self.assertNotIn('referências de estilo', corpo)


if __name__ == '__main__':
    unittest.main()
