"""Etapa 2 do plano: os comandos por defeito leem a edição nova.

A linha legada (`livros_json/`) só se usa com `--dados livros_json` explícito.
O fluxo legado `bee-autopiloto.yml` passa esse argumento (linha 145).
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

    def test_gerar_bee_aceita_a_legada_explicitamente(self):
        gerar = _carregar(RAIZ / 'gerar_bee.py', 'gerar_bee')
        self.assertEqual(gerar.argumentos(['--compilar', '--dados', 'livros_json']).dados, Path('livros_json'))

    def test_verificar_dados_por_defeito_le_a_edicao_nova(self):
        resultado = subprocess.run(
            [sys.executable, 'scripts/verificar_dados.py', '--minimo', '0'],
            cwd=RAIZ, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('edicoes/nova/livros_json', resultado.stdout)

    def test_fluxo_legado_passa_a_pasta_explicita(self):
        # O ficheiro ativo em .github/workflows/ é verificado por
        # tests/test_workflow_sincronizado.py (copiado à mão pelo responsável).
        for caminho in ('docs/bee-autopiloto.yml', 'modelos/bee-autopiloto.yml'):
            texto = (RAIZ / caminho).read_text(encoding='utf-8')
            self.assertIn('verificar_dados.py --dados livros_json --minimo 18', texto, caminho)


if __name__ == '__main__':
    unittest.main()
