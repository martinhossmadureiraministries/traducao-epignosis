"""Lapidação automática: a forma mecânica corrige-se sozinha ao fechar o capítulo."""
import unittest

from bee import lapidador
from bee.lapidador import (
    alertas_grego,
    critica_textual,
    gregos_fora_da_base,
    lapidar_versos,
    normalizar_nota,
    siglas_sem_evidencia,
    tokens_mistos,
)

NOTA_SUJA = (
    '<p><b>Análise Léxica</b> — <i>δίδωσιν</i> (dídōsin): dá.</p>'
    '<p><b>Crítica Textual</b> — Sem variante. Certeza: A segura.</p>'
    '<p><b>Síntese Exegética</b> — Deus dá o Espírito sem medida.</p>'
    '<p><b>Geografia e História</b> — Enchimento.</p>'
)

COLACAO = {
    'versiculos': {
        '1:1': {'base': {
            'aparato_sblgnt': ['1 δίδωσιν WH NA28 ] + ὁ θεὸς Treg RP'],
            'sblgnt_norm': ['διδωσιν'], 'scrivener_norm': ['διδωσιν', 'θεος'],
        }},
        '1:2': {'base': {
            'aparato_sblgnt': [],
            'sblgnt_norm': ['λογος'], 'scrivener_norm': ['λογος'],
        }},
    },
}


def _verso(numero, texto='Ele dá o Espírito.', nota=NOTA_SUJA):
    return {'verse': numero, 'text': texto, 'commentary': nota}


class NormalizarNotaTest(unittest.TestCase):
    def test_cabecalhos_aspas_e_entidades(self):
        nota = normalizar_nota(
            '<p><b>Análise Léxica</b> — “x” &#x27; [[y]]</p>')
        self.assertIn('<b>Análise Léxica:</b>', nota)
        self.assertIn('«x»', nota)
        self.assertNotIn('[[', nota)
        self.assertNotIn('&#', nota)


class CriticaTextualTest(unittest.TestCase):
    def test_nivel_b_quando_as_edicoes_se_dividem(self):
        ct = critica_textual(COLACAO['versiculos']['1:1'])
        self.assertIn('nível de certeza B', ct)
        self.assertIn('Tregelles, RP', ct)

    def test_nivel_a_sem_aparato(self):
        ct = critica_textual(COLACAO['versiculos']['1:2'])
        self.assertIn('nível de certeza A', ct)
        self.assertIn('Scrivener lê o mesmo texto', ct)


class LapidarVersosTest(unittest.TestCase):
    def test_lapida_forma_e_regenera_ct(self):
        novos, relatorio, problemas = lapidar_versos(
            [_verso(1)], 1, COLACAO)
        nota = novos[0]['commentary']
        self.assertIn('<b>Análise Léxica:</b>', nota)
        self.assertIn('<b>Crítica Textual:</b>', nota)
        self.assertIn('nível de certeza B', nota)
        self.assertIn('<b>Síntese Exegética:</b>', nota)
        self.assertNotIn('Geografia e História', nota)
        self.assertEqual(problemas, [])
        self.assertTrue(relatorio)

    def test_idempotente(self):
        uma_vez, _, _ = lapidar_versos([_verso(1), _verso(2)], 1, COLACAO)
        outra_vez, relatorio, problemas = lapidar_versos(uma_vez, 1, COLACAO)
        self.assertEqual(outra_vez, uma_vez)
        self.assertEqual(relatorio, [])
        self.assertEqual(problemas, [])

    def test_ponto_fora_das_aspas_corrigido_no_texto(self):
        novos, _, _ = lapidar_versos(
            [_verso(1, '«Dá-me de beber».')], 1, COLACAO)
        self.assertEqual(novos[0]['text'], '«Dá-me de beber.»')

    def test_nota_de_redacao_preservada(self):
        nota = NOTA_SUJA + '<p><b>Nota de redação:</b> decisão.</p>'
        novos, _, _ = lapidar_versos([_verso(1, nota=nota)], 1, COLACAO)
        self.assertIn('<b>Nota de redação:</b>', novos[0]['commentary'])

    def test_grego_misto_e_problema_reportado(self):
        nota = NOTA_SUJA.replace('δίδωσιν', 'ἄνδra')
        novos, _, problemas = lapidar_versos(
            [_verso(1, nota=nota)], 1, COLACAO)
        self.assertTrue(any('mista' in p for p in problemas))

    def test_ct_curada_com_facto_editorial_e_intocavel(self):
        # João 3:25 real: a CT cita a colação e traz um facto editorial
        # (01 e P66 leem o plural). A regeneração apagá-lo-ia: proibido.
        nota = NOTA_SUJA.replace(
            'Sem variante. Certeza: A segura.',
            'Sem unidade de variação. Nas testemunhas colacionadas (CNTR), '
            '01 e P66 leem o plural, com o Textus Receptus; P75 lê o '
            'singular com a base.')
        novos, _, _ = lapidar_versos([_verso(1, nota=nota)], 1, COLACAO)
        self.assertIn('01 e P66 leem o plural', novos[0]['commentary'])

    def test_sem_colacao_so_normaliza_a_forma(self):
        novos, _, problemas = lapidar_versos([_verso(1)], 1, None)
        self.assertIn('<b>Análise Léxica:</b>', novos[0]['commentary'])
        self.assertEqual(problemas, [])


class SiglasTest(unittest.TestCase):
    ITEM = {
        'base': {'aparato_sblgnt': ['1 δίδωσιν WH NA28 ] + ὁ θεὸς Treg RP']},
        'leituras': {
            '01': {'texto': 'x', 'presente': True},
            'P75': {'texto': 'x', 'presente': True},
            'P66': None,  # ausente neste versículo: não é evidência
        },
    }

    def test_sigla_com_testemunha_passa(self):
        self.assertEqual(
            siglas_sem_evidencia('01 e P75 leem com a base.', self.ITEM), [])

    def test_sigla_inventada_e_reportada(self):
        # O apoio inventado não passa em silêncio.
        self.assertEqual(
            siglas_sem_evidencia('P45 e 02 apoiam a variante.', self.ITEM),
            ['02', 'P45'])

    def test_sigla_ausente_na_colacao_nao_e_evidencia(self):
        self.assertEqual(
            siglas_sem_evidencia('P66 lê o plural.', self.ITEM), ['P66'])

    def test_sinaitico_pela_letra_hebraica(self):
        self.assertEqual(
            siglas_sem_evidencia('א lê com a base.', self.ITEM), [])

    def test_lapidar_reporta_sigla_inventada(self):
        colacao = {'versiculos': {'1:1': dict(
            self.ITEM,
            base={**self.ITEM['base'],
                  'sblgnt_norm': ['διδωσιν'], 'scrivener_norm': ['διδωσιν']},
        )}}
        nota = NOTA_SUJA.replace(
            'Sem variante. Certeza: A segura.',
            'A variante lê-se em P45 e P75.')
        _, _, problemas = lapidar_versos([_verso(1, nota=nota)], 1, colacao)
        self.assertTrue(any('P45' in p for p in problemas))
        self.assertFalse(any('P75' in p for p in problemas))


class GregoTest(unittest.TestCase):
    def test_tokens_mistos(self):
        self.assertEqual(tokens_mistos('o ἄνδra e o λόγος'), ['ἄνδra'])

    def test_grego_fora_da_base_e_alerta(self):
        # A forma da base não é sinalizada; o lema (forma de dicionário)
        # é, porque este controlo é um alerta e não uma porta.
        nota = '<p>ἀπέστειλεν, de ἀποστέλλω, enviou.</p>'
        achados = gregos_fora_da_base(nota, 'ὃν ἀπέστειλεν ὁ θεός')
        self.assertEqual(achados, ['ἀποστέλλω'])
        self.assertEqual(
            gregos_fora_da_base(nota, 'x', {'ἀποστέλλω'}), ['ἀπέστειλεν'])

    def test_alertas_grego_agrega_por_versiculo(self):
        colacao = {'versiculos': {'1:1': {'base': {
            'sblgnt': 'ὃν ἀπέστειλεν ὁ θεός'}}}}
        versos = [_verso(1, nota='<p>de ἀποστέλλω, enviou.</p>')]
        self.assertEqual(
            alertas_grego(versos, 1, colacao), {'1:1': ['ἀποστέλλω']})
        self.assertEqual(alertas_grego(versos, 1, None), {})


if __name__ == '__main__':
    unittest.main()
