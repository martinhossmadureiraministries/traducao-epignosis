"""Etapa 2 do plano: os comandos por defeito leem a edição nova.

"""
import importlib.util
from pathlib import Path
import subprocess
import sys
import unittest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))


def _carregar(caminho: Path, nome: str):
    espec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(espec)
    espec.loader.exec_module(modulo)
    return modulo


class DefaultsEdicaoNovaTest(unittest.TestCase):
    def test_gerar_bee_por_defeito_e_a_edicao_nova(self):
        gerar = _carregar(RAIZ / 'gerar_bee.py', 'gerar_bee')
        self.assertEqual(gerar.argumentos(['--compilar']).dados, Path('edicoes/nova/livros_json'))

    def test_verificar_dados_por_defeito_le_a_edicao_nova(self):
        resultado = subprocess.run(
            [sys.executable, 'scripts/verificar_dados.py', '--minimo', '0'],
            cwd=RAIZ, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('edicoes/nova/livros_json', resultado.stdout)


if __name__ == '__main__':
    unittest.main()
