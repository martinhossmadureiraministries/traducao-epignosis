"""Guarda anti-deriva: deteção de arcaísmos, hesitação e marcadores de Almeida."""
import importlib.util
from pathlib import Path
import unittest

CAMINHO = Path(__file__).resolve().parents[1] / 'scripts' / 'verificar_estilo.py'
spec = importlib.util.spec_from_file_location('verificar_estilo', CAMINHO)
ve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ve)


class AnalisarTextoTest(unittest.TestCase):
    def test_arcaismos_sao_falha_dura(self):
        res = ve.analisar_texto('Não vos deixeis abalar; vós sois atribulados.')
        for forma in ('vos', 'vós', 'sois'):
            self.assertIn(forma, res['duros'])

    def test_hesitacao_no_texto_e_falha_dura(self):
        res = ve.analisar_texto('A vós — ou seja, a vocês — graça e paz.')
        self.assertIn('ou seja', res['duros'])
        self.assertIn('hesitação com travessão', res['duros'])

    def test_hedge_com_acento_tambem_e_falha_dura(self):
        # «isto é,» tem acento: o texto é comparado sem acentos (_norm), por
        # isso as frases de hesitação também se comparam normalizadas.
        res = ve.analisar_texto('Ele veio, isto é, chegou ontem.')
        self.assertIn('isto é,', res['duros'])
        limpo = ve.analisar_texto('Isto é bom para todos.')
        self.assertNotIn('isto é,', limpo['duros'], 'sem vírgula não é glosa')

    def test_marcador_almeida_e_apenas_aviso(self):
        res = ve.analisar_texto('a fé cresce sobremaneira')
        self.assertEqual(res['duros'], [])
        self.assertIn('sobremaneira', res['avisos'])

    def test_texto_bee_limpo_passa(self):
        res = ve.analisar_texto('Graça e paz a vocês, da parte de Deus Pai.')
        self.assertEqual(res['duros'], [])
        self.assertEqual(res['avisos'], [])

    def test_expressoes_aprovadas_nao_sao_falsos_positivos(self):
        # «em verdade» e «Eis que» aparecem nos pilotos aprovados: não sinalizar.
        self.assertEqual(ve.analisar_texto('Eis que o Senhor vem')['avisos'], [])
        self.assertEqual(ve.analisar_texto('em verdade e amor')['avisos'], [])
        # «connosco» (pt) não é o arcaico «convosco».
        self.assertNotIn('convosco', ve.analisar_texto('estarão connosco')['duros'])


class AnalisarDadosTest(unittest.TestCase):
    DADOS = {'chapters': {'1': [
        {'verse': 1, 'text': 'Graça e paz a vocês.'},
        {'verse': 2, 'text': 'A vossa fé cresce sobremaneira.'},
    ]}}

    def test_percorre_e_localiza_o_verso_com_falha(self):
        achados = ve.analisar_dados(self.DADOS)
        self.assertEqual(len(achados), 1)
        capitulo, verso, _texto, res = achados[0]
        self.assertEqual((capitulo, verso), (1, 2))
        self.assertIn('vossa', res['duros'])
        self.assertIn('sobremaneira', res['avisos'])

    def test_formato_da_nota_so_com_incluir_comentario(self):
        # A linha legada usa outro formato de nota: por omissão a CLI não
        # chumba por ele; na edição nova o formato é falha dura.
        dados = {'chapters': {'3': [{
            'verse': 34, 'text': 'Ele não dá o Espírito por medida.',
            'commentary': '<p><b>Análise Léxica</b> — x</p>',
        }]}}
        self.assertEqual(ve.analisar_dados(dados), [])
        achados = ve.analisar_dados(dados, incluir_comentario=True)
        self.assertEqual(len(achados), 1)
        self.assertTrue(any('formato da casa' in d
                            for d in achados[0][3]['duros']))

    def test_formato_da_casa_so_nos_livros_da_migracao(self):
        # O formato de três secções é o da migração de 2026-11-20. Os lotes
        # aprovados depois usam notas em prosa e não podem chumbar por rótulos
        # que nunca tiveram: isso gerava centenas de alarmes falsos.
        raiz = ve.RAIZ
        nova = raiz / 'edicoes' / 'nova' / 'livros_json'
        self.assertTrue(ve._auditar_notas(nova, 600))
        self.assertTrue(ve._auditar_notas(nova, 720))
        self.assertFalse(ve._auditar_notas(nova, 460))
        self.assertFalse(ve._auditar_notas(raiz / 'livros_json', 640))

    def test_so_a_pasta_da_edicao_nova_liga_as_notas(self):
        raiz = ve.RAIZ
        self.assertTrue(
            ve._eh_edicao_nova(raiz / 'edicoes' / 'nova' / 'livros_json'))
        self.assertFalse(ve._eh_edicao_nova(raiz / 'livros_json'))


if __name__ == '__main__':
    unittest.main()
