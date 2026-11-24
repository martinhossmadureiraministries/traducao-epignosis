"""A leitura em Markdown gerada a partir do JSON não pode perder versículos
nem deixar de marcar a revisão especializada como pendente."""
import json
import re
import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))
sys.path.insert(0, str(RAIZ))

import gerar_leitura_livro  # noqa: E402


class LeituraLivroTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        caminho = RAIZ / 'edicoes/nova/livros_json/500_Joao.json'
        cls.dados = json.loads(caminho.read_text(encoding='utf-8'))
        cls.md = gerar_leitura_livro.gerar(cls.dados)

    def test_todos_os_versiculos_aparecem_no_texto(self):
        for capitulo, versos in self.dados['chapters'].items():
            for v in versos:
                marca = f'**{v["verse"]}** {gerar_leitura_livro._md(v["text"])}'
                self.assertIn(marca, self.md, f'{capitulo}:{v["verse"]} em falta')

    def test_cada_capitulo_tem_notas_e_contagem(self):
        for capitulo, versos in self.dados['chapters'].items():
            self.assertIn(f'### Notas do capítulo {capitulo}', self.md)
            self.assertEqual(
                len(re.findall(rf'^\*\*{capitulo}:\d+\*\*$', self.md, re.M)), len(versos))

    def test_revisao_especializada_fica_pendente(self):
        self.assertIn('Revisão especializada: pendente', self.md)

    def test_sem_marcas_html_no_markdown(self):
        self.assertNotRegex(self.md, r'<(/?)(p|b|i)>')

    def test_estado_vem_do_json(self):
        for bloco in self.dados['review']['editorial_blocks']:
            self.assertIn(f'| {bloco["chapter"]} | {bloco["status"]} |', self.md)


if __name__ == '__main__':
    unittest.main()
