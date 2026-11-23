"""CLI de gerar_bee.py depois da retirada da produção por IA.

Só restam --listar-livros, --status e --compilar. Nenhum destes modos usa rede
nem chaves de API; os testes garantem que a CLI não as pede.
"""
import contextlib
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import gerar_bee


class CLITest(unittest.TestCase):
    def test_listar_livros_mostra_66_livros(self):
        saida = io.StringIO()
        with contextlib.redirect_stdout(saida):
            self.assertEqual(gerar_bee.main(['--listar-livros']), 0)
        self.assertIn('Total: 66 livros', saida.getvalue())

    def test_status_sobre_pasta_vazia_nao_chama_rede(self):
        with tempfile.TemporaryDirectory() as tmp, \
             patch.dict(os.environ, {}, clear=True), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            self.assertEqual(gerar_bee.main(['--status', '--dados', tmp]), 0)
        self.assertIn('0/1189', saida.getvalue())

    def test_compilar_pasta_vazia_falha_sem_criar_modulos(self):
        with tempfile.TemporaryDirectory() as tmp, tempfile.TemporaryDirectory() as saida_dir, \
             patch.dict(os.environ, {}, clear=True), \
             contextlib.redirect_stderr(io.StringIO()):
            codigo = gerar_bee.main(['--compilar', '--dados', tmp, '--saida', saida_dir])
            modulos = list(Path(saida_dir).glob('BEE*.SQLite3'))
        self.assertIn(codigo, (0, 1))
        if codigo == 1:
            self.assertEqual(modulos, [])

    def test_sem_acao_ou_com_acoes_juntas_e_erro(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            gerar_bee.argumentos([])
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            gerar_bee.argumentos(['--compilar', '--status'])

    def test_modos_de_geracao_foram_retirados(self):
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            gerar_bee.argumentos(['--livro', '500'])


if __name__ == '__main__':
    unittest.main()
