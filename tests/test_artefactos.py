import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import nuvem


class PacotesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.saida = self.raiz / 'entregas' / 'auto'
        self.saida.mkdir(parents=True)
        self.dados = self.raiz / 'livros_json'
        (self.dados / '.bee').mkdir(parents=True)

    def test_pacotes_tem_nomes_da_execucao_e_conteudo(self):
        (self.saida / 'BEE.SQLite3').write_bytes(b'SQLite format 3\x00')
        (self.saida / 'BEE.commentaries.SQLite3').write_bytes(b'SQLite format 3\x00')
        capitulos = self.saida.parent / 'capitulos'
        capitulos.mkdir()
        (capitulos / 'Joao-018.html').write_text('<p>18</p>', encoding='utf-8')
        (self.saida / 'RELATORIO.txt').write_text('relatório', encoding='utf-8')
        (self.dados / '.bee' / 'estado.json').write_text('{}', encoding='utf-8')
        (self.dados / '.bee' / 'diario.md').write_text('diário', encoding='utf-8')
        (self.dados / '.bee' / 'quarentena.json').write_text('{"entries": []}', encoding='utf-8')
        with patch.dict(os.environ, {'GITHUB_RUN_NUMBER': '42'}):
            pacotes = nuvem._empacotar_tudo(self.saida, self.dados)
        self.assertTrue(pacotes['modulos'].endswith('BEE-modulos-42.zip'))
        self.assertTrue(pacotes['capitulos'].endswith('BEE-capitulos-42.zip'))
        self.assertTrue(pacotes['diagnostico'].endswith('BEE-diagnostico-42.zip'))
        with ZipFile(pacotes['modulos']) as pacote:
            self.assertEqual(
                sorted(pacote.namelist()),
                ['BEE.SQLite3', 'BEE.commentaries.SQLite3', 'LEIA-ME.txt'],
            )
        with ZipFile(pacotes['capitulos']) as pacote:
            self.assertEqual(pacote.namelist(), ['Joao-018.html'])
        with ZipFile(pacotes['diagnostico']) as pacote:
            self.assertEqual(
                sorted(pacote.namelist()),
                ['RELATORIO.txt', 'diario.md', 'estado.json', 'quarentena.json'],
            )

    def test_sem_modulos_nao_cria_pacote_vazio(self):
        self.assertIsNone(nuvem._empacotar(self.saida))
        self.assertIsNone(nuvem._empacotar_capitulos(self.saida))
        self.assertIsNone(nuvem._empacotar_diagnostico(self.saida, self.dados))
