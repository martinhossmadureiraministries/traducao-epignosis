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


class EntregaSemJsonTest(unittest.TestCase):
    """Etapa 7: um livro só MD não pode ser declarado «entregue»."""

    def _raiz_falsa(self, registo: str) -> Path:
        import tempfile
        raiz = Path(tempfile.mkdtemp())
        (raiz / 'edicoes' / 'nova' / 'livros_json').mkdir(parents=True)
        (raiz / 'docs').mkdir()
        (raiz / 'edicoes' / 'nova' / 'livros_json' / '400_Miqueias.json').write_text('{}', encoding='utf-8')
        (raiz / 'edicoes' / 'nova' / 'AMOS.md').write_text('# Amós\n', encoding='utf-8')
        (raiz / 'edicoes' / 'nova' / 'MIQUEIAS.md').write_text('# Miqueias\n', encoding='utf-8')
        (raiz / 'edicoes' / 'nova' / 'LOTE_04.md').write_text(registo, encoding='utf-8')
        (raiz / 'docs' / 'ESTADO.md').write_text('', encoding='utf-8')
        (raiz / 'docs' / 'EDICAO_NOVA.md').write_text('', encoding='utf-8')
        return raiz

    def test_declarar_entregue_livro_sem_json_falha(self):
        raiz = self._raiz_falsa('Amós, 9 capítulos. Entregues para leitura.\n')
        original = modulo.RAIZ
        modulo.RAIZ = raiz
        try:
            problemas = modulo.entregas_sem_json()
        finally:
            modulo.RAIZ = original
        self.assertEqual(len(problemas), 1, problemas)
        self.assertIn('amos', problemas[0])

    def test_livro_com_json_e_lido_sem_json_passam(self):
        raiz = self._raiz_falsa('Miqueias entregue em JSON.\nAmós lido para revisão, sem JSON. Zacarias terá entrega própria.\n')
        original = modulo.RAIZ
        modulo.RAIZ = raiz
        try:
            problemas = modulo.entregas_sem_json()
        finally:
            modulo.RAIZ = original
        self.assertEqual(problemas, [])

    def test_repositorio_atual_nao_declara_entregas_sem_json(self):
        self.assertEqual(modulo.entregas_sem_json(), [])


if __name__ == '__main__':
    unittest.main()
