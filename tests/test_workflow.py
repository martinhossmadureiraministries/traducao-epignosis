import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from bee.arquivos import DadosInvalidos, ler_livro, novo_livro, salvar_livro, validar_versiculos
from bee.catalogo import LIVROS, POR_NUMERO
from bee.compilador import ErroCompilacao, compilar
from bee.gerador import gerar_livros
from bee.ia import RespostaInvalida, RespostaTruncada
from bee.trava import EmExecucao, trava


class FontesFalsas:
    def __init__(self, ausente=None, aviso=None):
        self.ausente = ausente
        self.aviso = aviso
        self.calls = []

    def capitulo(self, livro, capitulo):
        self.calls.append((livro.numero, capitulo))
        resultado = []
        for v in range(1, livro.versos_por_capitulo[capitulo - 1] + 1):
            d = {'verse': v, 'base': [{'edicao': 'teste', 'texto': f'original {v}'}]}
            if v == self.ausente:
                d['ausente'] = True
            if v == self.aviso:
                d['aviso'] = 'Fonte suplementar & revisão necessária.'
            resultado.append(d)
        return resultado


class MotorFalso:
    provedor = 'openai'
    modelo = 'modelo-teste'

    def __init__(self, interromper_na_chamada=None, tamanho_max=None, falhar=False):
        self.calls = []
        self.interromper_na_chamada = interromper_na_chamada
        self.tamanho_max = tamanho_max
        self.falhar = falhar

    def gerar(self, livro, capitulo, fontes, estilo=None):
        nums = [f['verse'] for f in fontes]
        self.calls.append(nums)
        if self.interromper_na_chamada == len(self.calls):
            raise KeyboardInterrupt()
        if self.falhar:
            raise RespostaInvalida('JSON incompleto')
        if self.tamanho_max is not None and len(nums) > self.tamanho_max:
            raise RespostaTruncada('limite')
        return [
            {'verse': n, 'text': f'Texto {n} <i>claro</i>.',
             'commentary': f'<p><b>Análise Léxica:</b> {n}.</p><p><b>Crítica Textual:</b> não verificada.</p><p><b>Síntese Exegética:</b> teste.</p>'}
            for n in nums
        ]


@contextlib.contextmanager
def silencioso():
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        yield


class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.dados = self.raiz / 'livros_json'
        self.saida = self.raiz / 'saida'
        self.livro = POR_NUMERO[640]  # Filemom, um capítulo de 25 versículos

    def gerar(self, motor, fontes=None, **kw):
        with silencioso():
            return gerar_livros(
                [self.livro], self.dados, fontes or FontesFalsas(), lambda: motor,
                versos_por_pedido=kw.get('lote', 8), tentativas_conteudo=kw.get('tentativas', 3),
                max_capitulos=kw.get('max_capitulos'),
            )

    def test_marcadores_de_variante_equilibrados_em_cada_versiculo(self):
        def validar(texto):
            validar_versiculos([{'verse': 1, 'text': texto, 'commentary': '<p>Nota.</p>'}], range(1, 2), 'teste')

        validar('Leitura [[disputada]], [[com <i>acréscimo</i>]].')
        for texto in ('[[aberto', 'fechado]]', '[[ ]]', '[[<i></i>]]', '[[um [[dois]]]]'):
            with self.subTest(texto=texto), self.assertRaisesRegex(DadosInvalidos, 'variante'):
                validar(texto)
        # Aceitar um par é só uma checagem sintática, não comprovação da variante.
        validar('[[palavras válidas]]')

    def test_catalogo_oficial_e_contagens(self):
        numeros = [
            10,20,30,40,50,60,70,80,90,100,110,120,130,140,150,160,190,220,230,240,250,260,
            290,300,310,330,340,350,360,370,380,390,400,410,420,430,440,450,460,
            470,480,490,500,510,520,530,540,550,560,570,580,590,600,610,620,630,640,650,
            660,670,680,690,700,710,720,730,
        ]
        self.assertEqual([l.numero for l in LIVROS], numeros)
        self.assertEqual(len(LIVROS), 66)
        self.assertEqual(sum(l.capitulos for l in LIVROS), 1189)
        self.assertEqual(sum(sum(l.versos_por_capitulo) for l in LIVROS), 31102)
        self.assertEqual(POR_NUMERO[10].nome_arquivo, '010_Genesis.json')
        self.assertEqual(POR_NUMERO[500].nome_arquivo, '500_Joao.json')
        self.assertEqual(POR_NUMERO[730].nome_arquivo, '730_Apocalipse.json')
        self.assertEqual(POR_NUMERO[230].capitulos, 150)
        self.assertEqual(POR_NUMERO[460].capitulos, 4)
        self.assertEqual(POR_NUMERO[500].versos_por_capitulo[:3], (51, 25, 36))

    def test_interrupcao_retomada_preserva_edicao_e_nao_rechama(self):
        primeiro = MotorFalso(interromper_na_chamada=2)
        with self.assertRaises(KeyboardInterrupt):
            self.gerar(primeiro)
        caminho = self.dados / self.livro.nome_arquivo
        dados = ler_livro(caminho, self.livro)
        self.assertEqual(len(dados['in_progress']['1']), 8)
        self.assertEqual(dados['chapters'], {})
        dados['in_progress']['1'][0]['text'] = 'Versículo revisto manualmente.'
        salvar_livro(caminho, dados, self.livro)
        segundo = MotorFalso()
        self.assertEqual(self.gerar(segundo), 1)
        self.assertEqual(segundo.calls[0][0], 9)
        dados = ler_livro(caminho, self.livro)
        self.assertEqual(dados['chapters']['1'][0]['text'], 'Versículo revisto manualmente.')
        self.assertEqual(len(dados['chapters']['1']), 25)
        self.assertEqual(dados['in_progress'], {})
        self.assertEqual(len(dados['history']), 4)
        with silencioso():
            self.assertEqual(gerar_livros([self.livro], self.dados, FontesFalsas(),
                                          lambda: self.fail('IA não deve ser inicializada'), 8, 2), 0)

    def test_alinhamento_divergente_nao_mistura_checkpoint(self):
        with self.assertRaises(KeyboardInterrupt):
            self.gerar(MotorFalso(interromper_na_chamada=2))
        motor = MotorFalso()
        with patch('bee.gerador.ALINHAMENTO_VERSAO', 999):
            with self.assertRaisesRegex(DadosInvalidos, 'versões das fontes diferem'):
                self.gerar(motor)
        self.assertEqual(motor.calls, [])

    def test_divide_saida_truncada_e_mantem_lotes_menores(self):
        motor = MotorFalso(tamanho_max=2)
        self.gerar(motor)
        self.assertEqual([len(c) for c in motor.calls[:4]], [8, 4, 2, 2])
        self.assertTrue(all(len(c) <= 2 for c in motor.calls[2:]))
        dados = ler_livro(self.dados / self.livro.nome_arquivo, self.livro)
        self.assertEqual(len(dados['chapters']['1']), 25)

    def test_sem_fonte_nao_e_enviada_ao_modelo_e_aviso_e_preservado(self):
        motor = MotorFalso()
        self.gerar(motor, FontesFalsas(ausente=3, aviso=5))
        self.assertNotIn(3, [v for chamada in motor.calls for v in chamada])
        dados = ler_livro(self.dados / self.livro.nome_arquivo, self.livro)
        versos = dados['chapters']['1']
        self.assertIn('sem texto correspondente', versos[2]['text'])
        self.assertIn('Fonte suplementar &amp; revisão necessária', versos[4]['commentary'])
        self.assertTrue(any(h['provider'] == 'local' for h in dados['history']))
        resultado = compilar(self.dados, self.saida)
        self.assertEqual(resultado['lacunas_fonte'], 1)
        with sqlite3.connect(self.saida / 'BEE.SQLite3') as conn:
            self.assertEqual(conn.execute("SELECT value FROM info WHERE name='bee_source_gaps'").fetchone()[0], '1')

    def test_falhas_do_modelo_nao_gravam_capitulo_incompleto(self):
        motor = MotorFalso(falhar=True)
        with self.assertRaises(RespostaInvalida):
            self.gerar(motor, lote=1, tentativas=2)
        self.assertEqual(len(motor.calls), 2)
        self.assertFalse((self.dados / self.livro.nome_arquivo).exists())

    def test_sqlite_mybible_parcial_com_metadados_indices_e_intervalos(self):
        self.gerar(MotorFalso())
        resumo = compilar(self.dados, self.saida)
        self.assertFalse(resumo['completo'])
        self.assertEqual((resumo['livros'], resumo['capitulos'], resumo['versiculos']), (1, 1, 25))
        with sqlite3.connect(self.saida / 'BEE.SQLite3') as biblia, sqlite3.connect(self.saida / 'BEE.commentaries.SQLite3') as comentarios:
            info_biblia = dict(biblia.execute('SELECT name,value FROM info'))
            info_comentarios = dict(comentarios.execute('SELECT name,value FROM info'))
            self.assertEqual(info_biblia['description'], 'Bíblia de Estudo Epignósis (BEE) — RASCUNHO PARCIAL')
            self.assertIn('RASCUNHO PARCIAL', info_comentarios['description'])
            self.assertEqual(info_biblia['bee_complete'], 'false')
            self.assertIn('Revisão especializada necessária', info_biblia['bee_review_status'])
            sem_revisao = json.loads(info_biblia['bee_review_by_book'])['books'][0]
            self.assertEqual(sem_revisao['editorial_unreported_verses'], 25)
            self.assertEqual(sem_revisao['specialist_unreported_verses'], 25)
            self.assertEqual(info_biblia['russian_numbering'], 'false')
            self.assertEqual(info_comentarios['is_footnotes'], 'false')
            self.assertEqual(dict(biblia.execute('SELECT name,value FROM info'))['bee_build_id'],
                             dict(comentarios.execute('SELECT name,value FROM info'))['bee_build_id'])
            self.assertEqual(biblia.execute('SELECT COUNT(*) FROM books').fetchone()[0], 1)
            self.assertEqual(biblia.execute('SELECT COUNT(*) FROM books_all').fetchone()[0], 66)
            self.assertEqual(biblia.execute('SELECT is_present FROM books_all WHERE book_number=640').fetchone()[0], 1)
            self.assertEqual(biblia.execute('SELECT is_present FROM books_all WHERE book_number=500').fetchone()[0], 0)
            self.assertEqual(biblia.execute('SELECT text FROM verses WHERE book_number=640 AND chapter=1 AND verse=1').fetchone()[0], 'Texto 1 <i>claro</i>.')
            item = comentarios.execute(
                'SELECT book_number,chapter_number_from,verse_number_from,book_number_to,chapter_number_to,verse_number_to,marker,text '
                'FROM commentaries WHERE book_number=640 AND chapter_number_from=1 AND verse_number_from=25'
            ).fetchone()
            self.assertEqual(item[:7], (640, 1, 25, 640, 1, 25, ''))
            self.assertIn('Síntese Exegética', item[7])
            self.assertEqual(biblia.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertEqual(comentarios.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
            self.assertIn('verses_index', [r[1] for r in biblia.execute("PRAGMA index_list('verses')")])
            self.assertIn('commentaries_index', [r[1] for r in comentarios.execute("PRAGMA index_list('commentaries')")])

    def test_bibliografia_do_capitulo_e_preservada_nos_dois_modulos(self):
        self.gerar(MotorFalso())
        caminho = self.dados / self.livro.nome_arquivo
        dados = ler_livro(caminho, self.livro)
        dados['bibliography'] = [{
            'name': 'Léxico <de teste>', 'revision': 'abc123',
            'url': 'https://example.org/lexico', 'license': 'Licença de teste',
            'attribution': 'Autor do léxico',
            'urls': ['https://example.org/entrada'],
        }]
        salvar_livro(caminho, dados, self.livro)
        compilar(self.dados, self.saida)
        for nome in ('BEE.SQLite3', 'BEE.commentaries.SQLite3'):
            with sqlite3.connect(self.saida / nome) as conn:
                fontes = dict(conn.execute('SELECT name,value FROM info'))['source']
                self.assertIn('Léxico <de teste>', fontes)
                self.assertIn('abc123', fontes)
                self.assertIn('https://example.org/entrada', fontes)
                self.assertIn('Licença de teste', fontes)
                self.assertIn('Autor do léxico', fontes)
        with sqlite3.connect(self.saida / 'BEE.SQLite3') as conn:
            intro = conn.execute('SELECT introduction FROM introductions WHERE book_number=0').fetchone()[0]
            self.assertIn('Léxico &lt;de teste&gt;', intro)
            self.assertIn('RASCUNHO PARCIAL', intro)

    def test_bibliografia_invalida_nao_passa_na_validacao(self):
        dados = novo_livro(self.livro)
        for bibliografia in ({'name': 'não é lista'}, [{'name': ''}],
                             [{'name': 'Teste', 'urls': 'não é lista'}],
                             [{'name': 'Teste', 'url': 123}]):
            dados['bibliography'] = bibliografia
            with self.subTest(bibliography=bibliografia):
                with self.assertRaises(DadosInvalidos):
                    salvar_livro(self.dados / self.livro.nome_arquivo, dados, self.livro)

    def test_revisoes_separadas_e_trechos_nao_informados_nos_dois_modulos(self):
        self.gerar(MotorFalso())
        caminho = self.dados / self.livro.nome_arquivo
        dados = ler_livro(caminho, self.livro)
        dados['review'] = {
            'editorial_blocks': [
                {'chapter': 1, 'verse_from': 1, 'verse_to': 3, 'status': 'aprovado pelo responsável'},
                {'chapter': 1, 'verse_from': 4, 'verse_to': 20, 'status': 'pendente'},
            ],
            'specialist': {'chapter': 1, 'verse_from': 1, 'verse_to': 25, 'status': 'não revisado'},
        }
        salvar_livro(caminho, dados, self.livro)
        compilar(self.dados, self.saida)
        metadados = []
        for nome in ('BEE.SQLite3', 'BEE.commentaries.SQLite3'):
            with sqlite3.connect(self.saida / nome) as conn:
                info = dict(conn.execute('SELECT name,value FROM info'))
                metadados.append(info['bee_review_by_book'])
                estado = json.loads(info['bee_review_by_book'])['books'][0]
                self.assertEqual(estado['editorial_blocks'][0]['status'], 'aprovado pelo responsável')
                self.assertEqual(estado['editorial_blocks'][1]['status'], 'pendente')
                self.assertEqual(estado['specialist_blocks'][0]['status'], 'não revisado')
                self.assertEqual(estado['editorial_unreported_verses'], 5)
                self.assertEqual(estado['specialist_unreported_verses'], 0)
                self.assertIn('não informado em 5 versículo(s)', info['detailed_info'])
                self.assertEqual(info['bee_complete'], 'false')
        self.assertEqual(metadados[0], metadados[1])

    def test_revisao_de_capitulo_incompleto_nao_entra_no_modulo(self):
        livro = POR_NUMERO[500]
        dados = novo_livro(livro)
        dados['chapters']['1'] = [
            {'verse': n, 'text': 'Texto.', 'commentary': '<p>Nota.</p>'} for n in range(1, 52)
        ]
        dados['in_progress']['2'] = [{'verse': 1, 'text': 'Texto.', 'commentary': '<p>Nota.</p>'}]
        dados['review'] = {
            'editorial_blocks': [
                {'chapter': 1, 'verse_from': 1, 'verse_to': 51, 'status': 'pendente'},
                {'chapter': 2, 'verse_from': 1, 'verse_to': 25, 'status': 'ainda não compilado'},
            ],
            'specialist': [
                {'chapter': 1, 'verse_from': 1, 'verse_to': 51, 'status': 'não revisado'},
                {'chapter': 2, 'verse_from': 1, 'verse_to': 25, 'status': 'não revisado'},
            ],
        }
        salvar_livro(self.dados / livro.nome_arquivo, dados, livro)
        resultado = compilar(self.dados, self.saida)
        self.assertEqual(resultado['parciais'], 1)
        with sqlite3.connect(self.saida / 'BEE.SQLite3') as conn:
            info = dict(conn.execute('SELECT name,value FROM info'))
            estado = json.loads(info['bee_review_by_book'])['books'][0]
            self.assertEqual(estado['chapters_included'], [1])
            self.assertEqual([b['chapter'] for b in estado['editorial_blocks']], [1])
            self.assertEqual([b['chapter'] for b in estado['specialist_blocks']], [1])
            self.assertNotIn('ainda não compilado', info['detailed_info'])
            self.assertEqual(conn.execute('SELECT count(*) FROM verses').fetchone()[0], 51)

    def test_revisao_invalida_ou_sobreposta_nao_passa_na_validacao(self):
        dados = novo_livro(self.livro)
        bloco = {'chapter': 1, 'verse_from': 1, 'verse_to': 3, 'status': 'pendente'}
        invalidas = [
            'pendente', {'editorial_blocks': {}}, {'specialist': 'não revisado'},
            {'editorial_blocks': [{**bloco, 'verse_to': 26}]},
            {'editorial_blocks': [{**bloco, 'chapter': True}]},
            {'editorial_blocks': [{**bloco, 'status': ''}]},
            {'editorial_blocks': [bloco, {**bloco, 'verse_from': 3, 'verse_to': 5}]},
            {'specialist': [bloco, {**bloco, 'verse_from': 2, 'verse_to': 5}]},
        ]
        for revisao in invalidas:
            dados['review'] = revisao
            with self.subTest(review=revisao):
                with self.assertRaises(DadosInvalidos):
                    salvar_livro(self.dados / self.livro.nome_arquivo, dados, self.livro)

    def test_json_truncado_nao_sobrescreve_modulos_existentes(self):
        self.gerar(MotorFalso())
        compilar(self.dados, self.saida)
        paths = [self.saida / 'BEE.SQLite3', self.saida / 'BEE.commentaries.SQLite3']
        anteriores = [p.read_bytes() for p in paths]
        caminho = self.dados / self.livro.nome_arquivo
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        dados['chapters']['1'].pop()  # falta o último; não basta checar numeração sequencial
        caminho.write_text(json.dumps(dados), encoding='utf-8')
        with self.assertRaises(DadosInvalidos):
            compilar(self.dados, self.saida)
        self.assertEqual([p.read_bytes() for p in paths], anteriores)

    def test_sem_capitulo_completo_nao_cria_arquivos(self):
        with self.assertRaises(KeyboardInterrupt):
            self.gerar(MotorFalso(interromper_na_chamada=2))
        with self.assertRaises(ErroCompilacao):
            compilar(self.dados, self.saida)
        self.assertFalse((self.saida / 'BEE.SQLite3').exists())

    def test_falha_ao_publicar_segundo_modulo_restaura_primeiro(self):
        self.gerar(MotorFalso())
        self.saida.mkdir()
        bible = self.saida / 'BEE.SQLite3'
        comm = self.saida / 'BEE.commentaries.SQLite3'
        bible.write_bytes(b'biblia anterior')
        comm.write_bytes(b'comentario anterior')
        replace = os.replace
        def falhar_no_segundo(origem, destino):
            if str(destino).endswith('BEE.commentaries.SQLite3'):
                raise OSError('falha simulada')
            return replace(origem, destino)
        with patch('bee.compilador.os.replace', side_effect=falhar_no_segundo):
            with self.assertRaises(ErroCompilacao):
                compilar(self.dados, self.saida)
        self.assertEqual(bible.read_bytes(), b'biblia anterior')
        self.assertEqual(comm.read_bytes(), b'comentario anterior')
        self.assertEqual(list(self.saida.glob('*.bee-tmp')), [])

    def test_json_duplicado_invalido_e_html_indevido(self):
        self.dados.mkdir()
        caminho = self.dados / self.livro.nome_arquivo
        caminho.write_text('{"book_number": 640, "book_number": 640}', encoding='utf-8')
        with self.assertRaisesRegex(DadosInvalidos, 'repetida'):
            ler_livro(caminho, self.livro)
        caminho.write_text('{"book_number": 640, "valor": NaN}', encoding='utf-8')
        with self.assertRaisesRegex(DadosInvalidos, 'Constante JSON'):
            ler_livro(caminho, self.livro)
        dados = novo_livro(self.livro)
        dados['chapters']['1'] = MotorFalso().gerar(self.livro, 1, [{'verse': n} for n in range(1, 26)])
        dados['chapters']['1'][2]['commentary'] = '<script>alert(1)</script>'
        with self.assertRaisesRegex(DadosInvalidos, 'não permitido'):
            salvar_livro(caminho, dados, self.livro)
        self.assertIn('book_number', caminho.read_text(encoding='utf-8'))

    def test_trava_impede_duas_execucoes_e_e_liberada(self):
        with trava(self.dados):
            with self.assertRaises(EmExecucao):
                with trava(self.dados):
                    pass
        with trava(self.dados):
            pass

    def test_trava_tambem_impede_compilacoes_na_mesma_saida(self):
        self.gerar(MotorFalso())
        with trava(self.saida, nome='.bee.compile.lock'):
            with self.assertRaises(EmExecucao):
                compilar(self.dados, self.saida)
        self.assertEqual(compilar(self.dados, self.saida)['versiculos'], 25)

    def test_lacuna_de_capitulos_impede_compilacao(self):
        livro = POR_NUMERO[500]
        dados = novo_livro(livro)
        dados['chapters']['2'] = MotorFalso().gerar(livro, 2, [{'verse': n} for n in range(1, 26)])
        salvar_livro(self.dados / livro.nome_arquivo, dados, livro)
        with self.assertRaisesRegex(DadosInvalidos, 'lacunas'):
            compilar(self.dados, self.saida)


if __name__ == '__main__':
    unittest.main()
