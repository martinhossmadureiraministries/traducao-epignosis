"""Importador de pilotos: análise do markdown e reconstrução do comentário."""
import importlib.util
from pathlib import Path
import unicodedata
import unittest

CAMINHO = Path(__file__).resolve().parents[1] / 'scripts' / 'importar_piloto.py'
spec = importlib.util.spec_from_file_location('importar_piloto', CAMINHO)
imp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(imp)


def _norm(texto: str) -> str:
    texto = ''.join(c for c in unicodedata.normalize('NFD', texto)
                    if not unicodedata.combining(c))
    return ' '.join(texto.casefold().split())


MD = """# Demo
## Texto
### Capítulo 1
**1.** primeira parte
continuação da primeira
**2.** segunda
### Capítulo 2
**1.** capítulo dois
## Notas exegéticas
### Capítulo 1
**1.** nota do primeiro [rótulo](http://exemplo.pt)
"""


class AnaliseTest(unittest.TestCase):
    def setUp(self):
        self.blocos = imp.analisar_fichiero(MD, livro_inicial=640)

    def test_versos_multilinha_e_capitulos(self):
        b1 = self.blocos[(640, 1)]
        self.assertEqual(b1['versos'][1], 'primeira parte continuação da primeira')
        self.assertEqual(b1['versos'][2], 'segunda')
        self.assertEqual(self.blocos[(640, 2)]['versos'][1], 'capítulo dois')

    def test_notas_mapeadas_por_capitulo_e_links_descartados(self):
        nota = self.blocos[(640, 1)]['notas'][1]
        self.assertIn('nota do primeiro rótulo', nota)   # link virou só o rótulo
        self.assertNotIn('http://', nota)
        self.assertNotIn((640, 2), {c for c in self.blocos if self.blocos[c]['notas']})

    def test_ficheiro_conjunto_troca_de_livro(self):
        md = ('# 2 e 3\n## 2 João\n### Texto\n**1.** dois\n## 3 João\n### Texto\n**1.** tres\n')
        blocos = imp.analisar_fichiero(md, livro_inicial=700)
        self.assertEqual(blocos[(700, 1)]['versos'][1], 'dois')
        self.assertEqual(blocos[(710, 1)]['versos'][1], 'tres')


class ComentarioTest(unittest.TestCase):
    def test_tres_seccoes_presentes_e_nota_escapada(self):
        c = imp.comentario('texto <b>com</b> & "aspas"')
        for secao in ('analise lexica', 'critica textual', 'sintese exegetica'):
            self.assertIn(secao, _norm(c))
        self.assertIn('&lt;b&gt;', c, 'HTML da nota deve ser escapado')
        self.assertNotIn('<b>com</b>', c)

    def test_sem_nota_fica_marcado_para_migrar(self):
        self.assertIn('migrar', imp.comentario(None))

    def test_limpar_links(self):
        self.assertEqual(imp._limpar_links_markdown('[a](http://b)'), 'a')


if __name__ == '__main__':
    unittest.main()
