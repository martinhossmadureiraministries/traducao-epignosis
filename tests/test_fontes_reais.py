"""Auditoria opcional das fontes fixadas; requer rede somente se o cache estiver vazio."""
import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bee.catalogo import LIVROS, POR_NUMERO
from bee.fontes import FontesOriginais
from bee.rede import ClienteHTTP


@unittest.skipUnless(os.environ.get('BEE_TEST_FONTES_REAIS') == '1', 'defina BEE_TEST_FONTES_REAIS=1 para auditar as fontes reais')
class FontesReaisTest(unittest.TestCase):
    def test_cobertura_e_versificacao_de_todos_os_livros(self):
        diretorio = Path(os.environ.get('BEE_CACHE_FONTES', '.bee-cache'))
        fontes = FontesOriginais(diretorio, ClienteHTTP(pausa=0, tentativas=2, timeout=120))
        total = 0
        for livro in LIVROS:
            dados = fontes.carregar_livro(livro)
            self.assertEqual(len(dados), sum(livro.versos_por_capitulo), livro.nome)
            for capitulo, quantidade in enumerate(livro.versos_por_capitulo, 1):
                self.assertEqual([v['verse'] for v in fontes.capitulo(livro, capitulo)], list(range(1, quantidade + 1)))
            total += len(dados)
        self.assertEqual(total, 31102)
        self.assertEqual(fontes.capitulo(POR_NUMERO[230], 51)[0]['base'][0]['referencia'], 'Ps.51.3')
        self.assertEqual(fontes.capitulo(POR_NUMERO[460], 4)[0]['base'][0]['referencia'], 'Mal.3.19')
        self.assertTrue(fontes.capitulo(POR_NUMERO[160], 7)[67]['ausente'])
        self.assertEqual(fontes.capitulo(POR_NUMERO[160], 7)[68]['base'][0]['referencia'], 'Neh.7.68')
        self.assertEqual(fontes.capitulo(POR_NUMERO[520], 16)[24]['base'][0]['edicao'], 'Textus Receptus')
        self.assertTrue(fontes.capitulo(POR_NUMERO[520], 16)[24]['base'][0]['texto'].startswith('τω δε δυναμενω'))
        self.assertIn('colchetes críticos', fontes.capitulo(POR_NUMERO[480], 16)[11]['aviso'])
        self.assertIn('colchetes críticos', fontes.capitulo(POR_NUMERO[500], 8)[4]['aviso'])
        lucas = fontes.capitulo(POR_NUMERO[490], 6)
        self.assertEqual([x['referencia'] for x in lucas[16]['base']], ['Luke.6.17', 'Luke.6.18'])
        self.assertIn('οἳ ἦλθον', lucas[16]['base'][1]['texto'])
        self.assertTrue(lucas[17]['base'][0]['texto'].startswith('καὶ οἱ'))
        hebreus = fontes.capitulo(POR_NUMERO[650], 1)
        self.assertNotIn('εσχατων', hebreus[0]['textus_receptus'])
        self.assertIn('εσχατων', hebreus[1]['textus_receptus'])
        self.assertEqual(hebreus[1]['textus_receptus_referencias'], ['Heb.1.1', 'Heb.1.2'])
        self.assertEqual(fontes.capitulo(POR_NUMERO[510], 19)[40]['base'][0]['referencia'], 'Acts.19.40')
        self.assertEqual(fontes.capitulo(POR_NUMERO[540], 13)[13]['base'][0]['referencia'], '2Cor.13.13')
        self.assertEqual([v['referencia'] for v in fontes.capitulo(POR_NUMERO[730], 13)[0]['base']], ['Rev.12.18', 'Rev.13.1'])

if __name__ == '__main__':
    unittest.main()
