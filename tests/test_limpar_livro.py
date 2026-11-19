"""limpar_livro repõe um livro na fila sem perder metadados."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parents[1]
CAMINHO = RAIZ / 'scripts' / 'limpar_livro.py'
spec = importlib.util.spec_from_file_location('limpar_livro', CAMINHO)
ll = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ll)

from bee.arquivos import ler_livro, novo_livro, salvar_livro  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402


class LimparTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pasta = Path(self.tmp.name)
        self.livro = POR_NUMERO[640]   # Filemom, 1 capítulo de 25 versículos
        dados = novo_livro(self.livro)
        dados['chapters']['1'] = [
            {'verse': n, 'text': f'T{n}.', 'commentary': '<p>x</p>'} for n in range(1, 26)
        ]
        salvar_livro(self.pasta / self.livro.nome_arquivo, dados, self.livro)

    def tearDown(self):
        self.tmp.cleanup()

    def test_dry_run_nao_escreve(self):
        self.assertEqual(ll.limpar(640, self.pasta, dry_run=True), 0)
        relido = ler_livro(self.pasta / self.livro.nome_arquivo, self.livro)
        self.assertEqual(ll.contar(relido), (25, 0))

    def test_limpar_repoe_na_fila(self):
        self.assertEqual(ll.limpar(640, self.pasta, dry_run=False), 0)
        relido = ler_livro(self.pasta / self.livro.nome_arquivo, self.livro)
        self.assertEqual(ll.contar(relido), (0, 0))
        self.assertEqual(relido.get('chapters', {}), {})
        self.assertEqual(relido.get('in_progress', {}), {})

    def test_numero_desconhecido_devolve_2(self):
        self.assertEqual(ll.limpar(99999, self.pasta, dry_run=False), 2)


if __name__ == '__main__':
    unittest.main()
