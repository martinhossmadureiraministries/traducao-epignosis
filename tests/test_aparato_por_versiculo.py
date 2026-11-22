"""Regressão: uma nota do aparato da SBLGNT só vai ao versículo BEE que a contém.

Caso real: 1 Tessalonicenses 2:6–7. A BEE junta o início do v. 7 SBLGNT ao v. 6
(KJV). A nota «ἤπιοι» (v. 7) chegava também ao v. 6, e a CT gerada dizia que
havia variante onde não havia. Ver bee/fontes.py (_nota_pertence_ao_verso).
"""
import unittest

from bee.fontes import _nota_pertence_ao_verso

V6 = ('οὔτε ζητοῦντες ἐξ ἀνθρώπων δόξαν, οὔτε ἀφʼ ὑμῶν οὔτε ἀπʼ ἄλλων, '
      'δυνάμενοι ἐν βάρει εἶναι ὡς Χριστοῦ ἀπόστολοι·')
V7 = 'ἀλλὰ ἐγενήθημεν ἤπιοι ἐν μέσῳ ὑμῶν, ὡς ἐὰν τροφὸς θάλπῃ τὰ ἑαυτῆς τέκνα·'


class NotaPertenceAoVersoTest(unittest.TestCase):
    def test_nota_do_verso_seguinte_nao_chega_ao_anterior(self):
        nota = '7 ἤπιοι Treg NIV RP\xa0]\xa0νήπιοι WH NA28'
        self.assertFalse(_nota_pertence_ao_verso(nota, V6))
        self.assertTrue(_nota_pertence_ao_verso(nota, V7))

    def test_nota_com_bullet_e_alternativa_em_linha_propria(self):
        nota = '•\xa0ἐὰν WH Treg NA28\xa0]\xa0ἂν RP'
        self.assertFalse(_nota_pertence_ao_verso(nota, V6))
        self.assertTrue(_nota_pertence_ao_verso(nota, V7))

    def test_adicao_sem_palavra_base_mantem_se(self):
        # Entrada «+» (a base não tem a palavra): não há lema para decidir; fica como antes.
        self.assertTrue(_nota_pertence_ao_verso('3 + ὑμῶν RP', V6))
        self.assertTrue(_nota_pertence_ao_verso('14 – WH Treg NA28', V6))


if __name__ == '__main__':
    unittest.main()


class NotaDeIntervaloTest(unittest.TestCase):
    def test_nota_de_intervalo_nao_e_filtrada(self):
        # Filipenses 1:16–17: a nota de intervalo tem de continuar a ir ao versículo
        # (perdê-la foi a regressão que este teste guarda).
        nota = '16–17 ἀγάπης … κεῖμαι WH Treg NA28\xa0]\xa0ἐριθείας RP'
        self.assertTrue(_nota_pertence_ao_verso(nota, V6))


class GrupoDeNotasTest(unittest.TestCase):
    def test_grupo_com_linha_bullet_segue_a_nota_numerada(self):
        from bee.fontes import _filtrar_notas_do_verso
        grupo = ['7 ἤπιοι Treg NIV RP\xa0]\xa0νήπιοι WH NA28',
                 '•\xa0ἐὰν WH Treg NA28\xa0]\xa0ἂν RP']
        self.assertEqual(_filtrar_notas_do_verso(grupo, V6), [])
        self.assertEqual(_filtrar_notas_do_verso(grupo, V7), grupo)

    def test_grupo_de_intervalo_fica_inteiro(self):
        from bee.fontes import _filtrar_notas_do_verso
        grupo = ['16–17 ἀγάπης … κεῖμαι WH Treg NA28\xa0]\xa0ἐριθείας RP',
                 '•\xa0ἐριθείας … δεσμοῖς μου WH Treg NA28\xa0]\xa0ἀγάπης']
        self.assertEqual(_filtrar_notas_do_verso(grupo, V6), grupo)
