"""A nota é opcional; é obrigatória só onde o texto marca algo a explicar.

Regra (decisão de 2026-11-24): versículo sem chave `commentary` é válido, salvo se
o texto tiver acréscimo em itálico (`<i>`) ou colchetes simples (`[ ]`). Uma
chave `commentary` presente tem de ser nota não vazia.
"""
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from bee import arquivos
from bee.arquivos import DadosInvalidos, exige_nota, validar_versiculos

RAIZ = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verificar_dados', RAIZ / 'scripts' / 'verificar_dados.py')
vd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vd)

NOTA = '<p>Nota em prosa sobre a palavra <i>ἀγάπη</i>.</p>'
ACRESCIMO = 'Estava doente um homem <i>chamado</i> Lázaro.'
VARIANTE = 'Disse-lhe [Jesus] que viesse.'


class ExigeNotaTest(unittest.TestCase):
    def test_texto_simples_nao_pede_nota(self):
        self.assertIsNone(exige_nota('Graça e paz a vocês.'))

    def test_acrescimo_em_italico_pede_nota(self):
        self.assertIn('itálico', exige_nota(ACRESCIMO))

    def test_colchetes_simples_pedem_nota(self):
        self.assertIn('colchetes', exige_nota(VARIANTE))

    def test_marcador_de_producao_nao_pede_nota(self):
        self.assertIsNone(exige_nota('[Versículo pendente: tradução ainda não produzida.]'))


class ValidarVersiculosTest(unittest.TestCase):
    def test_sem_nota_e_aceite(self):
        validar_versiculos([{'verse': 1, 'text': 'Graça e paz.'}], range(1, 2), 'Livro 1')

    def test_com_nota_e_aceite(self):
        validar_versiculos([{'verse': 1, 'text': 'Graça e paz.', 'commentary': NOTA}],
                           range(1, 2), 'Livro 1')

    def test_chave_presente_mas_vazia_chumba(self):
        with self.assertRaises(DadosInvalidos):
            validar_versiculos([{'verse': 1, 'text': 'Graça e paz.', 'commentary': ''}],
                               range(1, 2), 'Livro 1')

    def test_acrescimo_sem_nota_chumba(self):
        with self.assertRaises(DadosInvalidos) as ctx:
            validar_versiculos([{'verse': 1, 'text': ACRESCIMO}], range(1, 2), 'Livro 1')
        self.assertIn('sem nota', str(ctx.exception))

    def test_colchetes_sem_nota_chumba(self):
        with self.assertRaises(DadosInvalidos):
            validar_versiculos([{'verse': 1, 'text': VARIANTE}], range(1, 2), 'Livro 1')

    def test_colchetes_duplos_chumbam(self):
        with self.assertRaises(DadosInvalidos) as ctx:
            validar_versiculos([{'verse': 1, 'text': 'Disse-lhe [[Jesus]].', 'commentary': NOTA}],
                               range(1, 2), 'Livro 1')
        self.assertIn('colchetes simples', str(ctx.exception))

    def test_colchetes_desequilibrados_chumbam(self):
        with self.assertRaises(DadosInvalidos):
            validar_versiculos([{'verse': 1, 'text': 'Disse-lhe [Jesus que viesse.',
                                 'commentary': NOTA}], range(1, 2), 'Livro 1')


class VerificarDadosTest(unittest.TestCase):
    def _pasta(self, versiculos):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        livro = {'chapters': {'1': versiculos}}
        Path(tmp.name, '500_Joao.json').write_text(json.dumps(livro), encoding='utf-8')
        return Path(tmp.name)

    def _problemas(self, versiculos):
        _, _, problemas = vd.verificar(self._pasta(versiculos))
        return problemas

    def test_sem_nota_em_texto_simples_passa(self):
        self.assertEqual(self._problemas([{'verse': 1, 'text': 'Graça e paz.'}]), [])

    def test_acrescimo_sem_nota_falha(self):
        problemas = self._problemas([{'verse': 1, 'text': ACRESCIMO}])
        self.assertEqual(len(problemas), 1)
        self.assertIn('sem nota', problemas[0])

    def test_colchetes_duplos_no_texto_falham(self):
        problemas = self._problemas([{'verse': 1, 'text': 'Disse-lhe [[Jesus]].',
                                      'commentary': NOTA}])
        self.assertEqual(len(problemas), 1)
        self.assertIn('colchetes simples', problemas[0])

    def test_chave_vazia_falha(self):
        problemas = self._problemas([{'verse': 1, 'text': 'Graça e paz.', 'commentary': '  '}])
        self.assertEqual(len(problemas), 1)
        self.assertIn('comentário vazio', problemas[0])


class CompiladorTest(unittest.TestCase):
    def test_so_entram_os_versiculos_com_nota(self):
        from bee import compilador
        livros = {500: {
            'chapters': {'1': [
                {'verse': 1, 'text': 'Graça e paz.', 'commentary': NOTA},
                {'verse': 2, 'text': 'Sem nota aqui.'},
                {'verse': 3, 'text': 'Outra nota.', 'commentary': NOTA},
            ]},
        }}
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / 'BEE.commentaries.SQLite3'
            compilador._criar_comentarios(caminho, livros, 'build', False, 0, 0)
            conexao = sqlite3.connect(caminho)
            try:
                versos = [r[0] for r in conexao.execute(
                    'SELECT verse_number_from FROM commentaries ORDER BY verse_number_from')]
            finally:
                conexao.close()
        self.assertEqual(versos, [1, 3])


if __name__ == '__main__':
    unittest.main()
