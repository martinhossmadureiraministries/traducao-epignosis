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
from bee.rede import ClienteHTTP, ErroRede


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

    def obter(self, req, descricao, limite=None, log=None):
        self.requisicoes.append((req, descricao))
        return json.dumps(self.resposta, ensure_ascii=False).encode()


class IATest(unittest.TestCase):
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

    def test_retry_429_respeita_retry_after_e_nao_expoe_chave(self):
        headers = Message()
        headers['Retry-After'] = '3'
        request = Request('https://example.com/api', headers={'Authorization': 'Bearer SEGREDO'})
        error = HTTPError(request.full_url, 429, 'Too many', headers, io.BytesIO(b'key SEGREDO'))
        cliente = ClienteHTTP(pausa=0, tentativas=2, timeout=1)
        stderr = io.StringIO()
        with patch('bee.rede.urllib.request.urlopen', side_effect=[error, io.BytesIO(b'{}')]) as urlopen, \
             patch('bee.rede.time.sleep') as sleep, contextlib.redirect_stderr(stderr):
            self.assertEqual(cliente.obter(request, 'API'), b'{}')
        self.assertEqual(urlopen.call_count, 2)
        self.assertGreaterEqual(sleep.call_args[0][0], 3)
        self.assertNotIn('SEGREDO', stderr.getvalue())

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
