"""P3: métricas por provedor (recolha/confiança/cache) e crescimento da memória.

As CLIs entram por subprocesso (prova o argparse); as funções centrais em
chamada direta sobre pastas temporárias. A memória real nunca é tocada.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from bee import metricas, papeis
from bee.memoria_estilo import CAMINHO_PADRAO, carregar

RAIZ = Path(__file__).resolve().parents[1]


def _carregar_script(nome: str):
    caminho = RAIZ / 'scripts' / f'{nome}.py'
    spec = importlib.util.spec_from_file_location(nome, caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


aprovar = _carregar_script('aprovar_voz')


def _historia(provedor, capitulo, de_, ate_, modelo='m'):
    return {'chapter': capitulo, 'verse_from': de_, 'verse_to': ate_,
            'provider': provedor, 'model': modelo,
            'generated_at_utc': '2026-11-19T00:00:00+00:00'}


class RecolherMetricasTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='metricas_p3_'))
        livro = {
            'format_version': 1, 'book_number': 710, 'book_name': '3 João',
            'chapter_count': 1, 'chapters': {}, 'in_progress': {},
            'history': [
                _historia('groq', 1, 1, 10),
                _historia('gemini', 1, 11, 15),
                _historia('revisao:cerebras', 1, 1, 15),
                _historia('local', 1, 16, 16),   # marcadores não contam
            ],
        }
        (self.tmp / '710_3_Joao.json').write_text(json.dumps(livro), encoding='utf-8')
        abelha = self.tmp / '.bee'
        abelha.mkdir()
        (abelha / 'quarentena.json').write_text(json.dumps({'entries': [{
            'book': 710, 'chapter': 1, 'verse': 4,
            'provider': 'groq', 'providers_tried': ['groq', 'gemini'],
            'status': 'chumbado-estilo',
            'style_marks': {'4': ['vós'], '5': ['ou seja']},
        }, {
            'book': 710, 'chapter': 1, 'verse': 9, 'provider': 'ovh',
            'status': 'pendente',           # outro estado: não conta
        }]}), encoding='utf-8')
        (abelha / 'revisoes.json').write_text(json.dumps({'entries': [
            {'book': 710, 'chapter': 1, 'verse': 3, 'reviewer': 'cerebras'},
        ]}), encoding='utf-8')

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_contagens_por_provedor(self):
        m = metricas.recolher(self.tmp)
        self.assertEqual(m['groq'].versos_gerados, 10)
        self.assertEqual(m['gemini'].versos_gerados, 5)
        # chumbo com 2 marcas conta 2 para quem tentou o lote
        self.assertEqual(m['groq'].chumbos_estilo, 2)
        self.assertEqual(m['gemini'].chumbos_estilo, 2)
        self.assertNotIn('ovh', m, 'entrada pendente (sem deriva) não cria provedor')
        # ambos os autores do capítulo levam a emenda do revisor
        self.assertEqual(m['groq'].emendas_recebidas, 1)
        self.assertEqual(m['gemini'].emendas_recebidas, 1)
        self.assertEqual(m['cerebras'].revisoes_feitas, 1)
        self.assertEqual(m['cerebras'].versos_revistos, 15)
        self.assertNotIn('local', m)

    def test_taxa_e_ordem_de_confianca(self):
        m = metricas.recolher(self.tmp)
        self.assertEqual(m['groq'].chumbos_por_100, 20.0)     # 2/10*100
        self.assertEqual(m['gemini'].chumbos_por_100, 40.0)   # 2/5*100
        ordem = metricas.ordenar_confianca(m)
        self.assertEqual(ordem[:2], ['groq', 'gemini'], 'menos deriva vem primeiro')

    def test_cache_ida_e_volta(self):
        m = metricas.recolher(self.tmp)
        destino = metricas.guardar(self.tmp, m)
        self.assertTrue(destino.exists())
        pontos = metricas.carregar_pontuacoes(self.tmp)
        self.assertEqual(pontos['groq'], 20.0)
        self.assertIsNone(metricas.carregar_pontuacoes(self.tmp / 'nao_existe'))

    def test_pasta_vazia_da_tudo_vazio_sem_erros(self):
        vazia = self.tmp / 'vazia'
        vazia.mkdir()
        self.assertEqual(metricas.recolher(vazia), {})
        self.assertIn('ainda sem dados', metricas.tabela({}))

    def test_ficheiro_corrompido_nao_parte_o_relatorio(self):
        (self.tmp / 'lixo.json').write_text('{ inválido', encoding='utf-8')
        m = metricas.recolher(self.tmp)          # ignora o lixo, lê o resto
        self.assertIn('groq', m)


class PrioridadesComPontuacoesTest(unittest.TestCase):
    def test_menos_deriva_passa_a_frente(self):
        # Ordem estática daria cerebras primeiro; as méticas trocam para groq.
        ordem = papeis.ordenar_revisores(
            ['cerebras', 'groq'], pontuacoes={'cerebras': 12.0, 'groq': 2.0})
        self.assertEqual(ordem, ['groq', 'cerebras'])

    def test_sem_medicao_caem_na_ordem_estatica(self):
        ordem = papeis.ordenar_revisores(
            ['nvidia', 'cerebras'], pontuacoes={'nvidia': 1.0})
        # nvidia tem nota (vai à frente); cerebras sem nota fica na ordem estática
        self.assertEqual(ordem, ['nvidia', 'cerebras'])

    def test_autor_continua_excluido_com_metricas(self):
        revs = papeis.revisores_disponiveis(
            ['groq', 'cerebras'], autor='groq', pontuacoes={'groq': 0.0, 'cerebras': 9.0})
        self.assertEqual(revs, ['cerebras'], 'nota perfeita não anula a segunda IA')


class AprovarVozTest(unittest.TestCase):
    """As funções da CLI aplicadas a uma cópia temporária da memória real."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='aprovar_p3_'))
        self.caminho = self.tmp / 'estilo_bee.json'
        shutil.copy(CAMINHO_PADRAO, self.caminho)
        self.memoria = json.loads(self.caminho.read_text(encoding='utf-8'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_aprovar_capitulos_regista_e_e_idempotente_no_livro(self):
        entrada = aprovar.aprovar_capitulos(self.memoria, 600, [1, 2, 3], 'registo equilibrado')
        self.assertIn('2 Tessalonicenses (600)', entrada)
        self.assertIn('caps. 1, 2, 3', entrada)
        antes = len(self.memoria['aprovacoes'])
        aprovar.aprovar_capitulos(self.memoria, 600, [1], '')   # repetição do mesmo livro
        self.assertEqual(len(self.memoria['aprovacoes']), antes, 'não duplica o livro')

    def test_glossario_novo_e_atualizacao(self):
        novo = aprovar.fixar_glossario(
            self.memoria, 'μακροθυμία', None, '«paciência»',
            transliteracao='makrothymía', sentido='esperança ativa.')
        self.assertEqual(novo['usar'], '«paciência»')
        total = len(self.memoria['glossario'])
        # chave igual atualiza em vez de duplicar
        aprovar.fixar_glossario(self.memoria, 'μακροθυμία', None, '«perseverança»',
                                transliteracao='makrothymía')
        self.assertEqual(len(self.memoria['glossario']), total)
        self.assertEqual(novo['usar'], '«perseverança»')

    def test_glossario_invalido_e_recusado(self):
        with self.assertRaises(ValueError):
            aprovar.fixar_glossario(self.memoria, 'λόγος', None, '«palavra»')  # falta translit.
        with self.assertRaises(ValueError):
            aprovar.fixar_glossario(self.memoria, None, None, '«x»')           # sem chave

    def test_amostra_entra_no_genero_e_na_memoria_renderizada(self):
        aprovar.promover_amostra(self.memoria, '2 Tessalonicenses 1:3',
                                 'Devemos dar sempre graças a Deus por vocês…',
                                 'ação de graças coesa com os pilotos')
        self.assertIn('2 Tessalonicenses 1:3', self.memoria['ancoras']['por_genero']['carta'])
        # grava E recarrega: o schema continua válido e o renderer vê a amostra
        aprovar._guardar(self.caminho, self.memoria)
        dados = carregar(self.caminho)
        refs = [a['referencia'] for a in dados['ancoras']['amostras']]
        self.assertIn('2 Tessalonicenses 1:3', refs)

    def test_amostra_duplicada_e_erro(self):
        aprovar.promover_amostra(self.memoria, 'Nova Ref 1:1', 'texto', 'razão')
        with self.assertRaises(ValueError):
            aprovar.promover_amostra(self.memoria, 'Nova Ref 1:1', 'outro', 'outra')

    def test_guardar_recusa_schema_partido(self):
        partido = json.loads(json.dumps(self.memoria))
        del partido['registro']
        with self.assertRaises(ValueError):
            aprovar._guardar(self.caminho, partido)
        # e o ficheiro ficou intocado
        self.assertEqual(json.loads(self.caminho.read_text(encoding='utf-8'))['registro'],
                         self.memoria['registro'])


class CLIsEmSubprocessoTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='cli_p3_'))

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_aprovar_dry_run_nao_escreve(self):
        memoria = self.tmp / 'estilo.json'
        shutil.copy(CAMINHO_PADRAO, memoria)
        antes = memoria.read_bytes()
        resultado = subprocess.run(
            [sys.executable, str(RAIZ / 'scripts' / 'aprovar_voz.py'),
             '--memoria', str(memoria), '--dry-run', 'capitulos', '600', '1'],
            capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('2 Tessalonicenses (600)', resultado.stdout)
        self.assertEqual(memoria.read_bytes(), antes, 'dry-run não escreve')

    def test_metricas_cli_imprime_tabela(self):
        # pasta vazia: tabela com aviso, saída 0
        resultado = subprocess.run(
            [sys.executable, str(RAIZ / 'scripts' / 'metricas_provedores.py'),
             '--dados', str(self.tmp)], capture_output=True, text=True)
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('provedor', resultado.stdout)
        self.assertIn('ainda sem dados', resultado.stdout)


if __name__ == '__main__':
    unittest.main()
