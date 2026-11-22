"""Convenção do grego nas notas (decisão D7): itálico, sem mexer no resto."""
import importlib.util
import json
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parents[1]

from bee.grego import (grego_fora_de_italico, italico_grego,  # noqa: E402
                       sem_marcas_i)
from bee.inspetor import grego_sem_italico  # noqa: E402


class ItalicoGregoTest(unittest.TestCase):
    def test_poe_em_italico_o_grego_fora_de_i(self):
        self.assertEqual(italico_grego('o verbo ἐκένωσεν aqui'),
                         'o verbo <i>ἐκένωσεν</i> aqui')

    def test_palavras_gregas_seguidas_formam_uma_so_expressao(self):
        self.assertEqual(italico_grego('ἐν ἀρχῇ ἦν'), '<i>ἐν ἀρχῇ ἦν</i>')

    def test_nao_duplica_o_que_ja_esta_em_i(self):
        s = '<i>Δεῦτε</i> (deûte) «venham»'
        self.assertEqual(italico_grego(s), s)

    def test_nao_mexe_em_etiquetas_nem_em_transliteracao(self):
        s = '<b>Análise Léxica:</b> (epýthleto) «ὁ»'
        o = italico_grego(s)
        self.assertIn('<b>Análise Léxica:</b>', o)
        self.assertIn('(epýthleto)', o)
        self.assertEqual(o, '<b>Análise Léxica:</b> (epýthleto) «<i>ὁ</i>»')

    def test_so_as_marcas_i_mudam(self):
        s = '<p><b>Crítica Textual:</b> Treg lê ἀπʼ ἀρχῆς e WH também.</p>'
        o = italico_grego(s)
        self.assertEqual(sem_marcas_i(o), sem_marcas_i(s))

    def test_idempotente(self):
        s = 'ἐν ἀρχῇ ἦν ὁ λόγος'
        uma = italico_grego(s)
        self.assertEqual(italico_grego(uma), uma)

    def test_nada_de_grego_sem_italico_depois(self):
        s = 'Λόγος e λογος; ἐκένωσεν, κένωσις.'
        self.assertEqual(grego_fora_de_italico(italico_grego(s)), [])


class FalhaDeAuditoriaTest(unittest.TestCase):
    def test_grego_fora_de_i_e_falha(self):
        self.assertTrue(grego_sem_italico('nota com ἐκένωσεν solto'))

    def test_grego_em_i_passa(self):
        self.assertEqual(grego_sem_italico('nota com <i>ἐκένωσεν</i>'), [])


class EdicaoNovaTest(unittest.TestCase):
    def test_edicao_nova_sem_grego_fora_de_italico(self):
        pasta = RAIZ / 'edicoes' / 'nova' / 'livros_json'
        restos = []
        for caminho in sorted(pasta.glob('*.json')):
            dados = json.loads(caminho.read_text(encoding='utf-8'))
            for zona in ('chapters', 'in_progress'):
                for versos in (dados.get(zona) or {}).values():
                    for v in versos:
                        if grego_fora_de_italico(v.get('commentary') or ''):
                            restos.append(f"{caminho.name} {v.get('verse')}")
        self.assertEqual(restos, [])


if __name__ == '__main__':
    unittest.main()
