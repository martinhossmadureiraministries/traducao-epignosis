"""Revisão por segunda IA (P2): outro provedor aplica a memória, com proteções.

Cobre papéis/ordem de revisores, validação de emendas (incluindo rejeição de
"correções" que derivam), integração real num livro temporário (autor excluído,
caderno e history escritos), falhas preservam o original, e o método MotorIA.rever
que transporta o system prompt do revisor.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bee import papeis, revisor
from bee.catalogo import POR_NUMERO
from bee.memoria_estilo import carregar as carregar_memoria
from bee.rede import CotaExcedida

RAIZ = Path(__file__).resolve().parents[1]


class RevisorFalso:
    def __init__(self, provedor, resposta=None, erro=None):
        self.provedor = provedor
        self.modelo = f'modelo-{provedor}'
        self._resposta = resposta
        self._erro = erro
        self.chamadas: list[str] = []

    def rever(self, sistema, mensagem):
        self.chamadas.append(mensagem)
        assert 'REVISOR DE VOZ' in sistema, 'o revisor recebe a identidade própria'
        if self._erro is not None:
            raise self._erro
        if isinstance(self._resposta, (dict, list)):
            return json.dumps(self._resposta, ensure_ascii=False)
        return self._resposta


class PapeisTest(unittest.TestCase):
    def test_ordem_prefere_a_lista_e_desconhecidos_vao_ao_fim(self):
        ordem = papeis.ordenar_revisores(['groq', 'nvidia', 'cerebras'])
        self.assertEqual(ordem, ['cerebras', 'groq', 'nvidia'])

    def test_autor_excluido_quando_ha_alternativa(self):
        revs = papeis.revisores_disponiveis(['gemini', 'groq', 'cerebras'], autor='groq')
        self.assertNotIn('groq', revs)
        self.assertEqual(revs[0], 'cerebras')

    def test_autor_unico_fica_para_nao_ficar_sem_revisao(self):
        self.assertEqual(papeis.revisores_disponiveis(['groq'], autor='groq'), ['groq'])

    def test_sem_ativos_lista_vazia(self):
        self.assertEqual(papeis.revisores_disponiveis([]), [])


class ValidarEmendasTest(unittest.TestCase):
    VERSOS = [{'verse': 1, 'text': 'A vós graça.'}, {'verse': 2, 'text': 'Texto limpo para vocês.'}]

    def test_emenda_valida_e_aceite_com_razao(self):
        bruto = {'emendas': [{'verse': 1, 'texto': 'Graça a vocês.', 'razao': 'arcaísmo «vós»'}]}
        aceites, problemas = revisor.validar_emendas(self.VERSOS, bruto)
        self.assertEqual(len(aceites), 1)
        self.assertEqual(aceites[0]['texto'], 'Graça a vocês.')
        self.assertEqual(problemas, [])

    def test_correcao_que_deriva_e_rejeitada_pela_porta(self):
        # O revisor "corrige" introduzindo «vosso»: a porta chumba a emenda.
        bruto = {'emendas': [{'verse': 2, 'texto': 'O vosso texto.', 'razao': '?'}]}
        aceites, problemas = revisor.validar_emendas(self.VERSOS, bruto)
        self.assertEqual(aceites, [])
        self.assertTrue(any('porta' in p for p in problemas))

    def test_emenda_igual_ao_texto_e_silenciada(self):
        bruto = {'emendas': [{'verse': 2, 'texto': 'Texto limpo para vocês.', 'razao': 'x'}]}
        aceites, problemas = revisor.validar_emendas(self.VERSOS, bruto)
        self.assertEqual((aceites, problemas), ([], []))

    def test_verso_desconhecido_e_problema(self):
        bruto = {'emendas': [{'verse': 99, 'texto': 'Novo.', 'razao': 'x'}]}
        aceites, problemas = revisor.validar_emendas(self.VERSOS, bruto)
        self.assertEqual(aceites, [])
        self.assertTrue(any('não existe' in p for p in problemas))

    def test_resposta_sem_lista_e_problema(self):
        aceites, problemas = revisor.validar_emendas(self.VERSOS, {'nada': 1})
        self.assertEqual(aceites, [])
        self.assertTrue(problemas)

    def test_aplicar_troca_so_o_texto_e_preserva_o_resto(self):
        novos = revisor.aplicar_emendas(
            [{'verse': 1, 'text': 'Antigo.', 'commentary': '<p>nota</p>'}],
            [{'verse': 1, 'texto': 'Novo.', 'razao': 'r'}])
        self.assertEqual(novos[0]['text'], 'Novo.')
        self.assertEqual(novos[0]['commentary'], '<p>nota</p>')


class SistemaEIntegracaoMotorTest(unittest.TestCase):
    def test_sistema_do_revisor_traz_identidade_memoria_e_contrato(self):
        texto = revisor.sistema_revisor(carregar_memoria())
        for marca in ('REVISOR DE VOZ', 'NÃO retraduz', '"emendas"',
                      'NADA DE ARCAÍSMOS', 'FÓRMULAS CONSOLIDADAS'):
            self.assertIn(marca, texto)

    def test_motor_rever_usa_o_system_override(self):
        from bee.ia import MotorIA

        class HTTPFalso:
            def __init__(self, corpo: bytes):
                self.corpo = corpo
                self.requisicoes = []

            def obter(self, req, descricao, limite=None, log=None, provedor=None):
                self.requisicoes.append(req)
                return self.corpo

        resposta = json.dumps({'choices': [{'finish_reason': 'stop',
                            'message': {'content': '{"emendas": []}'}}]}).encode()
        http = HTTPFalso(resposta)
        motor = MotorIA('openai', 'gpt-6-luna', 'CHAVE', http, 4096, aplicar_revisao=False)
        texto = motor.rever('SISTEMA_DO_REVISOR', 'corpo do pedido')
        self.assertEqual(texto, '{"emendas": []}')
        payload = json.loads(http.requisicoes[0].data)
        self.assertEqual(payload['messages'][0], {'role': 'system', 'content': 'SISTEMA_DO_REVISOR'})
        self.assertEqual(payload['messages'][1]['content'], 'corpo do pedido')


class ReverCapitulosTest(unittest.TestCase):
    """Integração num livro temporário, como faria o agendador."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='revisor_p2_'))
        origem = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '710_3_Joao.json'
        self.dados = json.loads(origem.read_text(encoding='utf-8'))
        comentario = ('<p>Análise Léxica x</p><p>Crítica Textual y</p>'
                      '<p>Síntese Exegética z</p>')
        total = POR_NUMERO[710].versos_por_capitulo[0]   # capítulo inteiro (validação)
        versos = [{'verse': i, 'text': f'Meu querido, verso {i} para vocês.',
                   'commentary': comentario} for i in range(1, total + 1)]
        versos[1]['text'] = 'Não vos escrevo nada de novo.'   # arcaísmo propositado no v.2
        self.dados['chapters'] = {'1': versos}
        # Proveniência: foi o groq que escreveu o capítulo.
        self.dados['history'] = [{
            'chapter': 1, 'verse_from': 1, 'verse_to': total,
            'provider': 'groq', 'model': 'm-groq', 'generated_at_utc': '2026-11-19T00:00:00+00:00',
        }]
        self.caminho = self.tmp / origem.name
        self.caminho.write_text(json.dumps(self.dados, ensure_ascii=False, indent=2),
                                encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ler(self):
        return json.loads(self.caminho.read_text(encoding='utf-8'))

    def test_autor_excluido_e_outro_provedor_revista_com_registos(self):
        autor = RevisorFalso('groq')          # escreveu; não deve rever
        bom = RevisorFalso('cerebras', resposta={'emendas': [
            {'verse': 2, 'texto': 'Não lhes escrevo nada de novo.', 'razao': 'arcaísmo «vos»'},
        ]})
        resumo = revisor.rever_capitulos_fechados(
            self.tmp, [(710, 1)], [autor, bom], memoria=carregar_memoria())
        self.assertEqual(autor.chamadas, [], 'o autor do capítulo não se revê a si próprio')
        self.assertEqual(len(bom.chamadas), 1)
        self.assertEqual(resumo['emendas'], 1)
        gravado = self._ler()
        self.assertEqual(gravado['chapters']['1'][1]['text'], 'Não lhes escrevo nada de novo.')
        self.assertTrue(any(str(e.get('provider')) == 'revisao:cerebras'
                            for e in gravado['history']))
        caderno = json.loads((self.tmp / '.bee' / 'revisoes.json').read_text(encoding='utf-8'))
        self.assertEqual(caderno['entries'][0]['reviewer'], 'cerebras')
        self.assertEqual(caderno['entries'][0]['verse'], 2)

    def test_primeiro_revisor_falha_segundo_conclui(self):
        quebrado = RevisorFalso('cerebras', erro=CotaExcedida('quota'))
        reserva = RevisorFalso('gemini', resposta={'emendas': []})
        registos: list[str] = []
        resumo = revisor.rever_capitulos_fechados(
            self.tmp, [(710, 1)], [quebrado, reserva],
            diario=lambda texto, *resto: registos.append(texto), memoria=carregar_memoria())
        self.assertEqual(len(quebrado.chamadas), 1)
        self.assertEqual(len(reserva.chamadas), 1)
        self.assertEqual(resumo['capitulos_revistos'], 1)
        self.assertEqual(resumo['emendas'], 0)
        self.assertTrue(any('aprovado sem emendas' in r for r in registos))

    def test_todos_os_revisores_falham_original_preservado(self):
        antes = self._ler()['chapters']['1']
        falha1 = RevisorFalso('cerebras', erro=CotaExcedida('quota'))
        falha2 = RevisorFalso('gemini', erro=CotaExcedida('quota'))
        resumo = revisor.rever_capitulos_fechados(
            self.tmp, [(710, 1)], [falha1, falha2], memoria=carregar_memoria())
        self.assertEqual(self._ler()['chapters']['1'], antes, 'nada muda quando ninguém revê')
        self.assertTrue(resumo['saltados'])

    def test_sem_provedores_ativos_salta_sem_erros(self):
        resumo = revisor.rever_capitulos_fechados(
            self.tmp, [(710, 1)], [], memoria=carregar_memoria())
        self.assertEqual(resumo['capitulos_revistos'], 0)
        self.assertTrue(any('nenhum revisor' in s for s in resumo['saltados']))

    def test_capitulo_longo_parte_se_em_lotes_de_40(self):
        versos = [{'verse': i, 'text': f'Texto {i} para vocês.',
                   'commentary': '<p>a</p>'} for i in range(1, 46)]
        dados = self._ler()
        dados['chapters']['1'] = versos
        self.caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')
        contador = RevisorFalso('cerebras', resposta={'emendas': []})
        revisor.rever_capitulos_fechados(self.tmp, [(710, 1)], [contador],
                                         memoria=carregar_memoria())
        self.assertEqual(len(contador.chamadas), 2, '45 versículos = 2 pedidos de revisão')


if __name__ == '__main__':
    unittest.main()
