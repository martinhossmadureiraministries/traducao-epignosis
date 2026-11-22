"""Porta obrigatória (P1): o texto mau nunca é guardado; quem dériva é evitado.

Cobre:
  * inspeção de lotes (falhas duras chumbam; avisos não);
  * rotação automática do rodízio quando um provedor dériva no mesmo lote;
  * quarentena com proveniência (status/marcas) quando ninguém passa na porta;
  * exclusão do provedor chumbado na repetição do capítulo, SEM perder
    disponibilidade (se só resta ele, fica);
  * legado sem porta: comportamento exatamente igual ao anterior.
"""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from bee import porta
from bee.catalogo import POR_NUMERO
from bee.gerador import ConfigGeracao, Progresso, _gerar_capitulo
from bee.ia import DerivaEstilo, Rodizio
from bee.inspetor import analisar_texto

RAIZ = Path(__file__).resolve().parents[1]


def _verso(numero: int, texto: str) -> dict:
    return {
        'verse': numero,
        'text': texto,
        'commentary': ('<p><b>Análise Léxica:</b> x</p>'
                       '<p><b>Crítica Textual:</b> y</p>'
                       '<p><b>Síntese Exegética:</b> z</p>'),
    }


LIMPO = [_verso(1, 'Graça e paz a vocês, da parte de Deus, nosso Pai.')]
DERIVADO = [_verso(1, 'A vós — ou seja, a vocês — graça e paz.')]


class MotorFalso:
    """Devolve sequências fixas; a última repete-se quando esgotada."""

    def __init__(self, provedor: str, saidas):
        self.provedor = provedor
        self.modelo = f'modelo-{provedor}'
        self.log = None
        self._saidas = list(saidas)
        self.chamadas: list[tuple[int, int]] = []

    def gerar(self, livro, capitulo, fontes, estilo=None):
        self.chamadas.append((livro.numero, capitulo))
        saida = self._saidas[0] if len(self._saidas) == 1 else self._saidas.pop(0)
        if isinstance(saida, Exception):
            raise saida
        return saida


class InspecionarVersosTest(unittest.TestCase):
    def test_lote_limpo_passa(self):
        self.assertEqual(porta.inspecionar_versos(LIMPO), {})

    def test_falha_dura_chumba_com_o_numero_do_verso(self):
        marcas = porta.inspecionar_versos(DERIVADO)
        self.assertIn(1, marcas)
        self.assertIn('ou seja', marcas[1])
        self.assertTrue({'vós', 'vos'} & set(marcas[1]))

    def test_avisos_nao_chumbam_na_porta(self):
        # «sobremaneira» é aviso (revê-se), não bloqueia a produção.
        avisoso = [_verso(3, 'a fé cresce sobremaneira entre vocês.')]
        self.assertEqual(porta.inspecionar_versos(avisoso), {})

    def test_forma_eis_fora_da_lista_chumba(self):
        # Regressão 2026-11-20: «adorareis»/«conheceis» passaram porque a
        # lista de arcaísmos só tinha formas fixas.
        resultado = porta.inspecionar_versos(
            [_verso(21, 'Vocês adoram o que não conheceis.')])
        self.assertIn(21, resultado)
        self.assertTrue(any('-eis' in m for m in resultado[21]))

    def test_eis_acentuado_e_excecoes_nao_chumbam(self):
        texto = ('Os fiéis seguram os papéis difíceis; são seis leis '
                 'dos reis de antigamente.')
        self.assertEqual(porta.inspecionar_versos([_verso(1, texto)]), {})

    def test_estar_a_infinitivo_passa(self):
        # Decisão de 2026-11-22: «estar a + infinitivo» é a perífrase da casa
        # (Portugal e Angola); o gerúndio progressivo é variante aceite. Nenhum
        # dos dois chumba, e a ênclise continua a ser exigida.
        self.assertEqual(porta.inspecionar_versos(
            [_verso(1, 'Ele estava a fazer discípulos.')]), {})
        self.assertEqual(porta.inspecionar_versos(
            [_verso(2, 'Ele estava fazendo discípulos.')]), {})

    def test_ponto_fora_das_aspas_chumba(self):
        resultado = porta.inspecionar_versos(
            [_verso(7, '«Dá-me de beber».')])
        self.assertIn(7, resultado)

    def test_grego_misto_na_nota_chumba(self):
        # «ἄνδra» tem letras latinas dentro da palavra grega: gralha
        # mecânica que a produção real cometeu (João 4:16).
        verso = _verso(16, 'Ele disse-lhe: «Vai.»')
        verso['commentary'] = (
            '<p><b>Análise Léxica:</b> <b>ἄνδra</b> (andra): marido.</p>'
            '<p><b>Crítica Textual:</b> y</p>'
            '<p><b>Síntese Exegética:</b> z</p>')
        marcas = porta.inspecionar_versos([verso])
        self.assertIn(16, marcas)
        self.assertTrue(any('mista' in m for m in marcas[16]))

    def test_nota_fora_do_formato_chumba(self):
        # Regressão 2026-11-20: «<b>Análise Léxica</b> —» passou na porta e
        # só falhou nos testes depois do capítulo fechado.
        verso = _verso(34, 'Ele não dá o Espírito por medida.')
        verso['commentary'] = ('<p><b>Análise Léxica</b> — x</p>'
                               '<p><b>Crítica Textual</b> — y</p>'
                               '<p><b>Síntese Exegética</b> — z</p>')
        self.assertIn(34, porta.inspecionar_versos([verso]))

    def test_resumo_marcas_e_legivel(self):
        resumo = porta.resumo_marcas({2: ['vós'], 7: ['ou seja']})
        self.assertEqual(resumo, 'v.2: vós; v.7: ou seja')


class RodizioComPortaTest(unittest.TestCase):
    def test_deriva_roda_para_outro_provedor_no_mesmo_lote(self):
        maus = MotorFalso('maus', [DERIVADO])
        bons = MotorFalso('bons', [LIMPO])
        registos: list[str] = []
        rodizio = Rodizio([maus, bons], registar=registos.append,
                          inspetor=porta.inspecionar_versos)
        livro = POR_NUMERO[640]
        resultado = rodizio.gerar(livro, 1, [{'verse': 1}], None)
        self.assertEqual(resultado, LIMPO, 'o texto limpo é o que segue em frente')
        self.assertEqual(len(maus.chamadas), 1)
        self.assertEqual(len(bons.chamadas), 1)
        self.assertTrue(any('Deriva de estilo' in r for r in registos))

    def test_se_todos_derivam_levanta_deriva_estilo_com_proveniencia(self):
        maus = MotorFalso('maus', [DERIVADO])
        piores = MotorFalso('piores', [[_verso(1, 'Não vos deixeis abalar, porque vós sois fortes.')]])
        rodizio = Rodizio([maus, piores], inspetor=porta.inspecionar_versos)
        with self.assertRaises(DerivaEstilo) as ctx:
            rodizio.gerar(POR_NUMERO[640], 1, [{'verse': 1}], None)
        exc = ctx.exception
        self.assertEqual(exc.provedor, 'piores', 'o último a escrever leva a culpa')
        self.assertTrue(exc.marcas)

    def test_sem_inspetor_texto_deriva_passa_igual_ao_anterior(self):
        # O legado não liga a porta: o resultado volta tal como o modelo deu.
        maus = MotorFalso('maus', [DERIVADO])
        rodizio = Rodizio([maus])
        resultado = rodizio.gerar(POR_NUMERO[640], 1, [{'verse': 1}], None)
        self.assertEqual(resultado, DERIVADO)

    def test_filtro_evita_provedor_chumbado_no_capitulo(self):
        maus = MotorFalso('maus', [DERIVADO])     # também saberia responder…
        bons = MotorFalso('bons', [LIMPO])
        registos: list[str] = []
        livro = POR_NUMERO[640]
        rodizio = Rodizio(
            [maus, bons], registar=registos.append,
            inspetor=porta.inspecionar_versos,
            filtro_provedores=lambda liv, cap: {'maus'} if (liv.numero, cap) == (640, 1) else set(),
        )
        resultado = rodizio.gerar(livro, 1, [{'verse': 1}], None)
        self.assertEqual(resultado, LIMPO)
        self.assertEqual(maus.chamadas, [], 'o chumbado nem chega a ser chamado')
        self.assertTrue(any('a evitar maus' in r for r in registos))

    def test_disponibilidade_vem_antes_do_filtro(self):
        # Se o filtro excluir todos os motores ativos, ignora-se: antes produzir
        # com quem há do que ficar parado à espera de quota.
        sozinho = MotorFalso('sozinho', [LIMPO])
        rodizio = Rodizio(
            [sozinho], inspetor=porta.inspecionar_versos,
            filtro_provedores=lambda liv, cap: {'sozinho'},
        )
        resultado = rodizio.gerar(POR_NUMERO[640], 1, [{'verse': 1}], None)
        self.assertEqual(resultado, LIMPO)
        self.assertEqual(len(sozinho.chamadas), 1)


class QuarentenaComProvenienciaTest(unittest.TestCase):
    """Integração real: capítulo inteiro derivado → nada mau gravado + registo."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='porta_p1_'))
        origem = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '710_3_Joao.json'
        dados = json.loads(origem.read_text(encoding='utf-8'))
        dados['chapters'] = {}
        dados['in_progress'] = {}
        dados['history'] = []
        self.caminho = self.tmp / origem.name
        self.caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=2),
                                encoding='utf-8')
        self.dados = dados

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_capitulo_todo_derivado_vai_para_quarentena_sem_texto_mau(self):
        livro = POR_NUMERO[710]
        total = livro.versos_por_capitulo[0]
        maus = [MotorFalso(p, [[_verso(i, 'Irmãos, não vos perturbeis; vós sois idóneas.')
                                for i in range(1, total + 1)]])
                for p in ('alfa', 'beta')]
        rodizio = Rodizio(maus, inspetor=porta.inspecionar_versos)
        progresso = Progresso()
        config = ConfigGeracao(versos_por_pedido=8, tentativas_conteudo=2,
                               max_quarentena=total + 5)
        fontes = [{'verse': i} for i in range(1, total + 1)]
        _gerar_capitulo(livro, 1, self.caminho, self.dados, fontes,
                        rodizio, config, progresso)

        # Nada do que ficou gravado tem falhas duras (só marcadores pendentes).
        gravado = json.loads(self.caminho.read_text(encoding='utf-8'))
        textos = [v['text'] for cap in {**gravado.get('chapters', {}),
                                        **gravado.get('in_progress', {})}.values()
                  for v in cap]
        self.assertTrue(textos, 'alguma coisa ficou gravada')
        for texto in textos:
            self.assertEqual(analisar_texto(texto)['duros'], [], f'texto mau gravado: {texto}')
        self.assertGreaterEqual(progresso.quarentenados, 1)

        # A quarentena guarda o estado e as marcas para a repetição evitar autores.
        quarentena = json.loads((self.tmp / '.bee' / 'quarentena.json')
                                .read_text(encoding='utf-8'))
        entradas = [e for e in quarentena['entries'] if e['status'] == 'chumbado-estilo']
        self.assertTrue(entradas, 'esperadas entradas chumbado-estilo')
        primeira = entradas[0]
        self.assertEqual(primeira['book'], 710)
        self.assertEqual(primeira['chapter'], 1)
        self.assertIn(primeira['provider'], {'alfa', 'beta'})
        self.assertTrue(primeira['style_marks'])
        self.assertIn('deriva de estilo', primeira['error'])

        # E o mapa de exclusões devolve ambos os provedores para (710, 1).
        mapa = porta.exclusoes_de_estilo(self.tmp / '.bee' / 'quarentena.json')
        self.assertEqual(mapa.get((710, 1)), {'alfa', 'beta'})


class ExclusoesDeEstiloTest(unittest.TestCase):
    def test_ficheiro_ausente_da_mapa_vazio(self):
        self.assertEqual(porta.exclusoes_de_estilo(Path('/nao/existe/q.json')), {})

    def test_ficheiro_corrompido_nao_impede_producao(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / 'quarentena.json'
            caminho.write_text('{ inválido', encoding='utf-8')
            self.assertEqual(porta.exclusoes_de_estilo(caminho), {})

    def test_so_contam_chumbados_de_estilo_com_provedor(self):
        entradas = {
            'entries': [
                # providers_tried alarga a exclusão a todos os autores da deriva
                {'book': 710, 'chapter': 1, 'provider': 'groq',
                 'providers_tried': ['groq', 'gemini'], 'status': 'chumbado-estilo'},
                # status diferente de chumbado-estilo não conta
                {'book': 710, 'chapter': 1, 'provider': 'cerebras', 'status': 'pendente'},
                # sem provedor identificado não conta
                {'book': 710, 'chapter': 2, 'provider': None, 'status': 'chumbado-estilo'},
            ],
        }
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / 'quarentena.json'
            caminho.write_text(json.dumps(entradas), encoding='utf-8')
            mapa = porta.exclusoes_de_estilo(caminho)
        self.assertEqual(mapa, {(710, 1): {'groq', 'gemini'}})


if __name__ == '__main__':
    unittest.main()
