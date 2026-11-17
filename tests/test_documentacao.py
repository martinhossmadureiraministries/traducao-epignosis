import importlib.util
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parent.parent
espec = importlib.util.spec_from_file_location(
    'verificar_documentacao', RAIZ / 'scripts' / 'verificar_documentacao.py'
)
modulo = importlib.util.module_from_spec(espec)
espec.loader.exec_module(modulo)


class DocumentacaoTest(unittest.TestCase):
    def test_documentacao_principal_bate_certo_com_os_dados(self):
        self.assertEqual(modulo.verificar(), [])


if __name__ == '__main__':
    unittest.main()
