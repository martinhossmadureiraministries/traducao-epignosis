import contextlib
from email.message import Message
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request

from bee.catalogo import POR_NUMERO
from bee.ia import MotorIA, RespostaInvalida, RespostaTruncada, SYSTEM_PROMPT
from bee.rede import ClienteHTTP, CotaExcedida, ErroRede


def retorno(versos):
    return {'verses': [
        {'verse': n, 'text': f'Verso {n}',
         'commentary': '<p>Análise Léxica: teste.</p><p>Crítica Textual: não verificado.</p><p>Síntese Exegética: teste.</p>'}
        for n in versos
    ]}


class HTTPFalso:
    def __init__(self, resposta):
        self.resposta = resposta
        self.requisicoes = []

    def obter(self, req, descricao, limite=None, log=None, provedor=None):
        self.requisicoes.append((req, descricao))
        return json.dumps(self.resposta, ensure_ascii=False).encode()


class IATest(unittest.TestCase):
    def test_groq_reserva_espaco_para_entrada_no_teto_de_8000(self):
        motor = MotorIA('groq', 'openai/gpt-oss-120b', 'CHAVE', HTTPFalso({}), 12000)
        _, curto, _ = motor._corpo('texto', 'CHAVE')
        _, longo, _ = motor._corpo('texto' * 300, 'CHAVE')
        self.assertLess(curto['max_tokens'], 8000)
        self.assertLess(longo['max_tokens'], curto['max_tokens'])
        with self.assertRaises(RespostaTruncada):
            motor._corpo('texto' * 5000, 'CHAVE')

    def test_openai_json_e_system_prompt_incluem_fontes_e_chave_em_header(self):
        response = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(retorno([1,2]))}}]}
        http = HTTPFalso(response)
        motor = MotorIA('openai', 'gpt-6-luna', 'SEGREDO', http, 8192, aplicar_revisao=False)
        fontes = [{'verse': 1, 'base': [{'texto': 'ἀρχή'}]}, {'verse': 2, 'base': [{'texto': 'λόγος'}]}]
        result = motor.gerar(POR_NUMERO[500], 1, fontes)
        self.assertEqual([r['verse'] for r in result], [1,2])
        req, _ = http.requisicoes[0]
        payload = json.loads(req.data)
        self.assertEqual(payload['messages'][0]['content'], SYSTEM_PROMPT)
        self.assertIn('ἀρχή', payload['messages'][1]['content'])
        self.assertEqual(payload['response_format']['type'], 'json_object')
        self.assertEqual(req.get_header('Authorization'), 'Bearer SEGREDO')
        self.assertNotIn('SEGREDO', req.full_url)
        self.assertNotIn('SEGREDO', json.dumps(payload))
    def test_modelo_retirado_410_passa_ao_seguinte(self):
        """HTTP 410 (modelo retirado) roda para o seguinte, como o 404.

        A NVIDIA respondeu 410 pelo llama-3.1-70b retirado do catálogo
        NIM em 2026-11-20 e o motor dava o provedor como perdido.
        """
        class Rede410:
            def obter(self, req, descricao, limite=None, log=None, provedor=None):
                if json.loads(req.data)['model'] == 'retirado':
                    raise ErroRede(
                        'nvidia: HTTP 410; verifique a configuração do serviço.')
                return json.dumps({'choices': [{
                    'finish_reason': 'stop',
                    'message': {'content': json.dumps(retorno([1]))},
                }]}).encode()

        motor = MotorIA('nvidia', ['retirado', 'atual'], 'CHAVE',
                        Rede410(), 8192, aplicar_revisao=False)
        resultado = motor.gerar(POR_NUMERO[500], 1, [{'verse': 1, 'base': []}])
        self.assertEqual(resultado[0]['verse'], 1)
        self.assertEqual(motor.modelo, 'atual')

    def test_descoberta_de_modelos_e_cacheada_por_execucao(self):
        from bee.ia import descobrir_modelo
        http = HTTPFalso({'data': [{'id': 'openai/gpt-oss-120b'}]})
        self.assertEqual(descobrir_modelo('groq', 'CHAVE', http), 'openai/gpt-oss-120b')
        self.assertEqual(descobrir_modelo('groq', 'CHAVE', http), 'openai/gpt-oss-120b')
        self.assertEqual(len(http.requisicoes), 1, 'só deve pedir /models uma vez')


    def test_gemini_json_config_e_chave_no_cabecalho(self):
        resp = {'candidates': [{'finishReason': 'STOP', 'content': {'parts': [{'text': json.dumps(retorno([1]))}]}}]}
        http = HTTPFalso(resp)
        motor = MotorIA('gemini', 'gemini-3.8-flash', 'CHAVE', http, 8192, aplicar_revisao=False)
        self.assertEqual(motor.gerar(POR_NUMERO[500], 1, [{'verse':1, 'base': []}])[0]['verse'], 1)
        req, _ = http.requisicoes[0]
        dados = json.loads(req.data)
        self.assertEqual(dados['systemInstruction']['parts'][0]['text'], SYSTEM_PROMPT)
        self.assertEqual(dados['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(req.get_header('X-goog-api-key'), 'CHAVE')
        self.assertNotIn('CHAVE', req.full_url)
        self.assertNotIn('CHAVE', json.dumps(dados))

    def test_corte_falha_e_lacunas_rejeitadas(self):
        http = HTTPFalso({'choices': [{'finish_reason': 'length'}]})
        motor = MotorIA('openai', 'gpt-6-luna', 'x', http, 8192)
        with self.assertRaises(RespostaTruncada):
            motor.gerar(POR_NUMERO[500], 1, [{'verse':1}])
        http.resposta = {'choices': [{'finish_reason':'stop', 'message': {'content':json.dumps(retorno([1,3]))}}]}
        with self.assertRaises(RespostaInvalida):
            motor.gerar(POR_NUMERO[500], 1, [{'verse':1}, {'verse':2}])
        http.resposta = {'choices': [{'finish_reason':'stop', 'message': {'content':'```json\n{}\n```'}}]}
        with self.assertRaises(RespostaInvalida):
            motor.gerar(POR_NUMERO[500], 1, [{'verse':1}])
        ruim = {'verses': [{'verse': 1, 'text': 'Texto', 'commentary': '<p>Só uma nota.</p>'}]}
        http.resposta = {'choices': [{'finish_reason':'stop', 'message': {'content':json.dumps(ruim)}}]}
        # Uma secção em falta não perde o lote: fica assinalada para revisão.
        versiculo = motor.gerar(POR_NUMERO[500], 1, [{'verse':1}])[0]
        for titulo in ('Análise Léxica', 'Crítica Textual', 'Síntese Exegética'):
            self.assertIn(titulo, versiculo['commentary'])
        self.assertIn('não devolvida pelo modelo', versiculo['commentary'])

    def test_json_corrompido_a_meio_salva_os_versiculos_anteriores(self):
        """17/11: João 18:1-10 voltou 3 vezes com JSON inválido a meio (aspas
        sem escape) e cada tentativa perdeu a resposta inteira."""
        corrompido = (
            '{"verses":['
            '{"verse":1,"text":"Verso 1","commentary":"<p>Análise Léxica: a.</p>'
            '<p>Crítica Textual: b.</p><p>Síntese Exegética: c.</p>"},'
            '{"verse":2,"text":"Verso "2","commentary":"<p>x</p>"}]}'
        )
        http = HTTPFalso({'choices': [{'finish_reason': 'stop', 'message': {'content': corrompido}}]})
        motor = MotorIA('openai', 'gpt-6-luna', 'x', http, 8192, aplicar_revisao=False)
        fontes = [{'verse': 1, 'base': []}, {'verse': 2, 'base': []}]
        resultado = motor.gerar(POR_NUMERO[500], 1, fontes)
        self.assertEqual([v['verse'] for v in resultado], [1])

    def test_numero_de_versiculo_como_texto_e_aceite(self):
        """17/11: o modelo devolveu "verse": "11" e o lote foi rejeitado."""
        resposta = retorno([1])
        resposta['verses'][0]['verse'] = '1'
        http = HTTPFalso({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(resposta)}}]})
        motor = MotorIA('openai', 'gpt-6-luna', 'x', http, 8192, aplicar_revisao=False)
        resultado = motor.gerar(POR_NUMERO[500], 1, [{'verse': 1, 'base': []}])
        self.assertEqual(resultado[0]['verse'], 1)

    def test_resposta_parcial_contigua_e_aceite(self):
        resposta = retorno([1, 2])
        http = HTTPFalso({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(resposta)}}]})
        motor = MotorIA('openai', 'gpt-6-luna', 'x', http, 8192, aplicar_revisao=False)
        fontes = [{'verse': n, 'base': []} for n in (1, 2, 3)]
        resultado = motor.gerar(POR_NUMERO[500], 1, fontes)
        self.assertEqual([v['verse'] for v in resultado], [1, 2])

    def test_resposta_com_lacuna_ou_excesso_continua_rejeitada(self):
        http = HTTPFalso({'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(retorno([1, 3]))}}]})
        motor = MotorIA('openai', 'gpt-6-luna', 'x', http, 8192, aplicar_revisao=False)
        fontes = [{'verse': n, 'base': []} for n in (1, 2, 3)]
        with self.assertRaises(RespostaInvalida):
            motor.gerar(POR_NUMERO[500], 1, fontes)
        http.resposta = {'choices': [{'finish_reason': 'stop', 'message': {'content': json.dumps(retorno([1, 2, 3, 4]))}}]}
        with self.assertRaises(RespostaInvalida):
            motor.gerar(POR_NUMERO[500], 1, fontes)

    def test_429_nao_dorme_e_passa_ao_provedor(self):
        """17/11: Retry-After de 523/1176/989/1542 s levou ao cancelamento aos 50 min."""
        headers = Message()
        headers['Retry-After'] = '1200'
        request = Request('https://example.com/api', headers={'Authorization': 'Bearer SEGREDO'})
        error = HTTPError(request.full_url, 429, 'Too many', headers, io.BytesIO(b'key SEGREDO'))
        cliente = ClienteHTTP(pausa=0, tentativas=3, timeout=1)
        stderr = io.StringIO()
        with patch('bee.rede.urllib.request.urlopen', side_effect=[error]) as urlopen, \
             patch('bee.rede.time.sleep') as sleep, contextlib.redirect_stderr(stderr):
            with self.assertRaises(CotaExcedida):
                cliente.obter(request, 'API', provedor='groq')
        self.assertEqual(urlopen.call_count, 1, 'não insiste no mesmo 429')
        sleep.assert_not_called()
        self.assertNotIn('SEGREDO', stderr.getvalue())
        self.assertEqual(cliente.pedidos_por_provedor(), {'groq': 1})

    def test_retry_after_longo_de_5xx_fica_limitado(self):
        """Um 503 com Retry-After de 20 min não pode bloquear o ciclo."""
        headers = Message()
        headers['Retry-After'] = '1200'
        request = Request('https://example.com/api')
        error = HTTPError(request.full_url, 503, 'Indisponível', headers, io.BytesIO(b''))
        cliente = ClienteHTTP(pausa=0, tentativas=2, timeout=1)
        with patch('bee.rede.urllib.request.urlopen', side_effect=[error, io.BytesIO(b'{}')]), \
             patch('bee.rede.time.sleep') as sleep:
            self.assertEqual(cliente.obter(request, 'API'), b'{}')
        self.assertLessEqual(sleep.call_args[0][0], 45.0)

    def test_contagem_de_tentativas_inclui_falhas(self):
        request = Request('https://example.com/api')
        headers = Message()
        headers['Retry-After'] = '1'
        error = HTTPError(request.full_url, 500, 'Erro', headers, io.BytesIO(b''))
        cliente = ClienteHTTP(pausa=0, tentativas=2, timeout=1)
        with patch('bee.rede.urllib.request.urlopen', side_effect=[error, io.BytesIO(b'{}')]), \
             patch('bee.rede.time.sleep'):
            cliente.obter(request, 'API', provedor='gemini')
        self.assertEqual(cliente.pedidos_por_provedor(), {'gemini': 2})

    def test_pausa_e_aplicada_depois_da_resposta_anterior(self):
        request = Request('https://example.com/api')
        cliente = ClienteHTTP(pausa=1, tentativas=1, timeout=1)
        with patch('bee.rede.urllib.request.urlopen', side_effect=[io.BytesIO(b'1'), io.BytesIO(b'2')]), \
             patch('bee.rede.time.monotonic', side_effect=[10.0, 10.2, 11.2]), \
             patch('bee.rede.time.sleep') as sleep:
            self.assertEqual(cliente.obter(request, 'API'), b'1')
            self.assertEqual(cliente.obter(request, 'API'), b'2')
        sleep.assert_called_once()
        self.assertAlmostEqual(sleep.call_args[0][0], 0.8)

    def test_limite_de_tokens_por_minuto_evita_429(self):
        """17/11: sem TPM, a Groq devolveu 10 respostas 429 seguidas.

        O plano gratuito do gpt-oss-120b dá 8.000 tokens/minuto. Quatro lotes
        de 2.000 caberam; o quinto tinha de esperar — não falhar.
        """
        cliente = ClienteHTTP(pausa=0, tentativas=1)
        cliente.tokens_por_minuto['groq'] = 8_000
        relogio = [100.0]

        def agora():
            return relogio[0]

        def dormir(segundos):
            relogio[0] += segundos

        with patch('bee.rede.time.monotonic', side_effect=agora), \
             patch('bee.rede.time.sleep', side_effect=dormir) as sleep:
            esperas = [cliente.reservar_tokens('groq', 2_000) for _ in range(5)]
        self.assertEqual(esperas[:4], [0.0, 0.0, 0.0, 0.0], 'os primeiros cabem no minuto')
        self.assertGreaterEqual(esperas[4], 59.0, 'o quinto tem de esperar pelo minuto seguinte')
        self.assertEqual(sleep.call_count, 1)
        self.assertAlmostEqual(cliente.esperas_por_provedor()['groq'], esperas[4], places=1)

    def test_sem_teto_de_tpm_nao_espera(self):
        cliente = ClienteHTTP(pausa=0, tentativas=1)
        self.assertEqual(cliente.reservar_tokens('gemini', 50_000), 0.0)
        self.assertEqual(cliente.esperas_por_provedor(), {})

    def test_provedores_declararam_tpm_e_groq_e_o_mais_apertado(self):
        from bee.ia import PROVEDORES
        self.assertGreater(PROVEDORES['gemini'].tokens_por_minuto, 0)
        self.assertEqual(PROVEDORES['groq'].tokens_por_minuto, 8_000,
                         'gpt-oss-120b tem 8.000 TPM no plano gratuito')
        self.assertLess(PROVEDORES['groq'].tokens_por_minuto,
                        PROVEDORES['gemini'].tokens_por_minuto)

    def test_pedidos_por_minuto_do_mistral_evita_429(self):
        """O Mistral dá ~2 pedidos/minuto: o terceiro tem de esperar."""
        cliente = ClienteHTTP(pausa=0, tentativas=1)
        cliente.pedidos_por_minuto['mistral'] = 2
        relogio = [0.0]

        def dormir(segundos):
            relogio[0] += segundos

        with patch('bee.rede.time.monotonic', side_effect=lambda: relogio[0]), \
             patch('bee.rede.time.sleep', side_effect=dormir) as sleep:
            esperas = [cliente.reservar_pedido('mistral') for _ in range(4)]
        self.assertEqual(esperas[:2], [0.0, 0.0], 'os dois primeiros cabem no minuto')
        self.assertGreaterEqual(esperas[2], 59.0, 'o terceiro espera pelo minuto seguinte')
        self.assertEqual(sleep.call_count, 1)

    def test_ovhcloud_funciona_sem_chave_nenhuma(self):
        """O nível anónimo não leva 'Authorization': um Bearer vazio é rejeitado."""
        from bee.ia import OVH_URL
        enviados = {}

        class RedeFalsa:
            def obter(self, requisicao, descricao, log=None, provedor=None):
                enviados['headers'] = dict(requisicao.headers)
                enviados['url'] = requisicao.full_url
                return b'{"choices":[{"message":{"content":"{\\"ok\\":1}"}}]}'

            def reservar_pedido(self, provedor):
                return 0.0

            def reservar_tokens(self, *a, **k):
                return 0.0

        motor = MotorIA('ovh', 'gpt-oss-120b', [], RedeFalsa(), 512)
        self.assertEqual(motor._requisicao('teste'), '{"ok":1}')
        self.assertEqual(enviados['url'], OVH_URL)
        self.assertNotIn('Authorization', enviados['headers'])
        self.assertEqual(enviados['headers']['Content-type'], 'application/json')

    def test_ovhcloud_com_chave_usa_bearer(self):
        from bee.ia import OVH_URL  # noqa: F401  (garante que a URL é o endpoint OVH)

        class RedeFalsa:
            def __init__(self):
                self.cabecalhos = {}

            def obter(self, requisicao, descricao, log=None, provedor=None):
                self.cabecalhos = dict(requisicao.headers)
                return b'{"choices":[{"message":{"content":"{\\"ok\\":1}"}}]}'

            def reservar_pedido(self, provedor):
                return 0.0

            def reservar_tokens(self, *a, **k):
                return 0.0

        rede = RedeFalsa()
        MotorIA('ovh', 'gpt-oss-120b', 'chave-abc', rede, 512)._requisicao('teste')
        self.assertEqual(rede.cabecalhos['Authorization'], 'Bearer chave-abc')

    def test_provedor_sem_chave_nao_divide_por_zero(self):
        """Nível anónimo tem lista de chaves vazia: rodar a chave rebentava."""
        from bee.rede import ErroRede

        class RedeFalsa:
            def obter(self, *a, **k):
                raise ErroRede('ovh: falha de rede (URLError); esgotadas 3 tentativas.')

            def reservar_pedido(self, provedor):
                return 0.0

            def reservar_tokens(self, *a, **k):
                return 0.0

        motor = MotorIA('ovh', 'gpt-oss-120b', [], RedeFalsa(), 512)
        with self.assertRaises(ErroRede):
            motor.testar_ligacao()
        with self.assertRaises(ErroRede):
            motor._requisicao('teste')

    def test_ovhcloud_respeita_o_ritmo_do_nivel_anonimo(self):
        from bee.ia import PROVEDORES
        ovh = PROVEDORES['ovh']
        self.assertTrue(ovh.sem_chave)
        self.assertEqual(ovh.pedidos_por_minuto, 2, '2 pedidos/minuto por IP e modelo')
        self.assertEqual(ovh.pedidos_por_minuto * 1440, ovh.pedidos_por_dia)
        self.assertGreater(ovh.pedidos_por_dia, PROVEDORES['groq'].tokens_por_dia // 3000,
                           'no fim do dia a OVHcloud produz mais do que a Groq')

    def test_chave_com_quebra_de_linha_e_rejeitada_sem_vazar(self):
        with self.assertRaises(ValueError) as erro:
            MotorIA('openai', 'gpt-6-luna', 'SEGREDO\nSECRET', HTTPFalso({}), 8192)
        self.assertIn('chave', str(erro.exception))
        self.assertNotIn('SEGREDO', str(erro.exception))
        self.assertNotIn('SECRET', str(erro.exception))

    def test_401_nao_faz_retry_ou_expoe_corpo(self):
        request = Request('https://example.com/api')
        error = HTTPError(request.full_url, 401, 'Unauthorized', Message(), io.BytesIO(b'SEGREDO'))
        with patch('bee.rede.urllib.request.urlopen', side_effect=error) as urlopen:
            with self.assertRaises(ErroRede) as exc:
                ClienteHTTP(0, 4, 1).obter(request, 'API')
        self.assertEqual(urlopen.call_count, 1)
        self.assertNotIn('SEGREDO', str(exc.exception))
        self.assertIn('chave', str(exc.exception))


if __name__ == '__main__':
    unittest.main()
