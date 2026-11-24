"""O documento de apresentação é gerado a partir dos JSON e não pode voltar a
descrever processos que já não existem (revisão por IA, rótulos antigos)."""
import importlib.util
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / 'scripts'))

try:
    import docx  # noqa: F401
    TEM_DOCX = True
except ImportError:
    TEM_DOCX = False


@unittest.skipUnless(TEM_DOCX, 'python-docx não instalado (opcional, ver requirements-dev.txt)')
class ApresentacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gerar_apresentacao as g
        cls.g = g
        cls.livros = g.carregar_livros()
        cls.doc = g.construir(cls.livros)

    def _textos(self):
        saida = [p.text for p in self.doc.paragraphs]
        for t in self.doc.tables:
            for linha in t.rows:
                saida.append(' | '.join(c.text for c in linha.cells))
        return '\n'.join(saida)

    def test_tabela_tem_um_livro_por_json(self):
        tabela = self.doc.tables[0]
        self.assertEqual(len(tabela.rows) - 1, len(self.livros))

    def test_revisoes_separadas_e_ministerio_nos_livros(self):
        texto = self._textos()
        for titulo in ('Revisão editorial', 'Revisão especializada', 'Revisão do ministério'):
            self.assertIn(titulo, texto)
        self.assertTrue(all(r['ministerio'] == 'pendente' or r['ministerio'].startswith('aprovado')
                            for r in self.livros))

    def test_sem_revisao_por_ia_nem_rotulos_antigos(self):
        texto = self._textos()
        for proibido in ('segunda IA', 'segundo modelo', 'Análise Léxica', 'Síntese Exegética',
                         'lapidação', 'GitHub Actions'):
            with self.subTest(proibido):
                self.assertNotIn(proibido, texto)

    def test_numeros_batem_com_os_json(self):
        texto = self._textos()
        capitulos = sum(r['capitulos'] for r in self.livros)
        versiculos = sum(r['versiculos'] for r in self.livros)
        self.assertIn(f'{len(self.livros)} livros', texto)
        self.assertIn(f'{capitulos} capítulos', texto)
        self.assertIn(f'{versiculos} versículos', texto)
        self.assertIsNotNone(re.search(r'1\.189 capítulos', texto))


if __name__ == '__main__':
    unittest.main()
