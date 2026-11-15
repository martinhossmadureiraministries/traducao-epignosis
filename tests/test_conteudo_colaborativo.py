"""Protege a estrutura e as aprovações já registradas, não a exatidão filológica."""
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bee.arquivos import ler_todos
from bee.compilador import compilar


RAIZ = Path(__file__).resolve().parents[1]


class ConteudoColaborativoTest(unittest.TestCase):
    def test_filemom_aprovado_preservado_e_amostra_do_salmo(self):
        livros = ler_todos(RAIZ / 'livros_json')
        filemom = livros[640]
        amostra = json.loads((RAIZ / 'rascunhos/640_Filemom_1.json').read_text(encoding='utf-8'))
        salmo = json.loads((RAIZ / 'rascunhos/230_Salmos_23.json').read_text(encoding='utf-8'))
        atuais = filemom['chapters']['1'][:3]
        self.assertEqual(atuais[0], amostra['verses'][0])
        self.assertEqual(atuais[2], amostra['verses'][2])
        # O texto aprovado é idêntico sem a nova sinalização. A nota aprovada
        # permanece intacta; o adendo novo não herda automaticamente a aprovação.
        self.assertEqual(atuais[1]['text'].replace('[[', '').replace(']]', ''), amostra['verses'][1]['text'])
        self.assertTrue(atuais[1]['commentary'].startswith(amostra['verses'][1]['commentary']))
        self.assertIn('adendo', filemom['review']['editorial_blocks'][1]['status'])
        self.assertIn('pendentes', filemom['review']['editorial_blocks'][1]['status'])
        self.assertIn('aprovados pelo responsável', amostra['review']['editorial'])
        self.assertEqual(filemom['review']['editorial_blocks'][0]['status'], 'aprovado pelo responsável')
        self.assertEqual(filemom['review']['editorial_blocks'][2]['status'], 'aprovado pelo responsável')
        self.assertEqual(salmo['review']['editorial'], 'aprovado pelo responsável')

    def test_capitulos_concluidos_tem_as_tres_secoes_e_aspas_iniciais_equilibradas(self):
        livros = ler_todos(RAIZ / 'livros_json')
        for numero in (500, 640):
            for capitulo, versos in livros[numero]['chapters'].items():
                with self.subTest(livro=numero, capitulo=capitulo):
                    # Nestes trechos o discurso não continua para o capítulo seguinte.
                    if (numero, capitulo) in {(500, '1'), (500, '2'), (500, '3'), (500, '4'), (640, '1')}:
                        texto = ' '.join(v['text'] for v in versos)
                        self.assertEqual(texto.count('“'), texto.count('”'))
                        self.assertEqual(texto.count('‘'), texto.count('’'))
                    for verso in versos:
                        for secao in ('Análise léxica', 'Crítica textual', 'Síntese exegética'):
                            self.assertIn(secao, verso['commentary'])

    def test_variantes_selecionadas_identificam_leituras_e_suplementos(self):
        livros = ler_todos(RAIZ / 'livros_json')
        exemplos = {
            (500, '1', 18): ('[[o Único, que é Deus]]', 'P66'),
            (500, '1', 27): ('[[e passou à minha frente]]', 'suplemento'),
            (500, '1', 34): ('[[Escolhido de Deus]]', 'P75'),
            (500, '1', 51): ('[[de agora em diante]]', 'suplemento'),
            (500, '3', 13): ('[[que está no céu]]', 'não está nessa edição crítica'),
            (500, '3', 15): ('[[não pereça, mas]]', 'não traz'),
            (500, '3', 25): ('[[um judeu]]', 'primeira mão'),
            (500, '3', 31): ('[[está acima de todos]]', 'P75'),
            (500, '3', 34): ('[[Deus]]', 'não explicita o sujeito'),
            (500, '4', 1): ('[[Jesus]]', 'P66'),
            (500, '4', 9): ('[[Pois os judeus', 'Sinaítico'),
            (500, '4', 11): ('[[A mulher]]', 'P75'),
            (500, '4', 17): ('[[a ele]]', 'P66'),
            (500, '4', 42): ('[[o Salvador do mundo]]', 'Bezae'),
            (640, '1', 2): ('[[irmã]]', 'Alexandrino'),
            (640, '1', 6): ('[[em nós]]', 'P61'),
            (640, '1', 12): ('[[Receba-o.]]', 'suplemento'),
            (640, '1', 25): ('[[Amém.]]', 'suplemento'),
        }
        for (numero, capitulo, n), (marcador, evidencia) in exemplos.items():
            with self.subTest(livro=numero, capitulo=capitulo, versiculo=n):
                verso = livros[numero]['chapters'][capitulo][n - 1]
                self.assertIn(marcador, verso['text'])
                self.assertIn(evidencia, verso['commentary'])
        # Estes testes preservam decisões documentadas; não conferem sua exatidão histórica.

    def test_joao_4_ligacao_de_ja_e_estado_provisorio(self):
        joao = ler_todos(RAIZ / 'livros_json')[500]
        versos = joao['chapters']['4']
        self.assertEqual(len(versos), 54)
        self.assertNotIn('já', versos[34]['text'])
        self.assertIn('já recebe', versos[35]['text'])
        self.assertIn('ao fim de 4:35', versos[35]['commentary'])
        self.assertIn('<i>o menino</i>', versos[51]['text'])
        # Em 4:42 o texto segue a leitura curta; a alternativa fica só na nota.
        self.assertNotIn('Cristo', versos[41]['text'])
        self.assertIn('Scrivener acrescenta', versos[41]['commentary'])
        self.assertIn('pendente', joao['review']['editorial_blocks'][-1]['status'])
        self.assertEqual(joao['review']['specialist'][-1]['status'], 'não revisado')
        self.assertNotIn('4', joao['in_progress'])

    def test_preview_real_reproduz_json_e_estados_nos_dois_sqlite(self):
        livros = ler_todos(RAIZ / 'livros_json')
        esperados = {
            (num, int(cap), v['verse']): (v['text'], v['commentary'])
            for num, livro in livros.items()
            for cap, versos in livro['chapters'].items()
            for v in versos
        }
        self.assertEqual(len(esperados), 191)
        with tempfile.TemporaryDirectory() as tmp:
            saida = Path(tmp)
            resumo = compilar(RAIZ / 'livros_json', saida)
            self.assertFalse(resumo['completo'])
            with sqlite3.connect(saida / 'BEE.SQLite3') as biblia, \
                 sqlite3.connect(saida / 'BEE.commentaries.SQLite3') as notas:
                texto = {(b, c, v): t for b, c, v, t in biblia.execute(
                    'SELECT book_number, chapter, verse, text FROM verses')}
                comentarios = {(b, c, v): t for b, c, v, t in notas.execute(
                    'SELECT book_number, chapter_number_from, verse_number_from, text FROM commentaries')}
                self.assertEqual(texto, {k: v[0] for k, v in esperados.items()})
                self.assertEqual(comentarios, {k: v[1] for k, v in esperados.items()})
                self.assertEqual(biblia.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                self.assertEqual(notas.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
                bi, co = (dict(conn.execute('SELECT name,value FROM info')) for conn in (biblia, notas))
                self.assertEqual(bi['bee_build_id'], co['bee_build_id'])
                self.assertEqual(bi['bee_review_by_book'], co['bee_review_by_book'])
                revisoes = {b['book_number']: b for b in json.loads(bi['bee_review_by_book'])['books']}
                self.assertEqual(revisoes[500]['chapters_included'], [1, 2, 3, 4])
                self.assertIn('pendente', revisoes[500]['editorial_blocks'][-1]['status'])
                self.assertEqual(revisoes[500]['specialist_blocks'][-1]['status'], 'não revisado')
                self.assertIn('pendentes', revisoes[640]['editorial_blocks'][1]['status'])


if __name__ == '__main__':
    unittest.main()
