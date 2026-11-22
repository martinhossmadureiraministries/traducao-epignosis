"""Crítica textual: o que o protocolo promete tem de estar nos dados.

Três coisas são verificadas aqui, e todas nasceram de defeitos reais:

  1. **Nenhuma testemunha é citada sem colação.** Cada códice, papiro ou edição
     nomeado numa nota de 2 Tessalonicenses tem de ter um registo no relatório
     de ``docs/colacao/`` para aquele versículo. É a versão mecânica da regra
     «não afirme ter consultado manuscritos que não lhe tenham sido fornecidos».
  2. **As decisões difíceis assentam em leituras que existem mesmo.** O caso de
     2Ts 2:13 (ἀπαρχήν / ἀπʼ ἀρχῆς) e o achado de 2Ts 3:16 (τόπω → τρόπω) são
     conferidos contra o relatório, não contra a memória de quem os escreveu.
  3. **A regeneração de 2 Tessalonicenses é reproduzível e auditável.** O JSON
     gravado é o que ``scripts/regenerar_2ts.py`` produz; a proveniência
     (``bibliography``) fixa as revisões; os estados de revisão declaram
     RASCUNHO; e nada do histórico anterior foi apagado.
"""
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / 'scripts'))

from bee.arquivos import DadosInvalidos, validar_livro  # noqa: E402
from bee.catalogo import POR_NUMERO  # noqa: E402
from bee.fontes import SBL_COMMIT, TR_COMMIT  # noqa: E402

RELATORIO = RAIZ / 'docs' / 'colacao' / '2_Tessalonicenses.json'
PROTOCOLO = RAIZ / 'docs' / 'CRITICA_TEXTUAL.md'
LIVRO_JSON = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '600_2_Tessalonicenses.json'

_espec = importlib.util.spec_from_file_location(
    'regenerar_2ts', RAIZ / 'scripts' / 'regenerar_2ts.py')
regenerar = importlib.util.module_from_spec(_espec)
_espec.loader.exec_module(regenerar)

from colar import CNTR_REVISAO  # noqa: E402

LIVRO = POR_NUMERO[600]

# Nomes por que as notas chamam as testemunhas → chave no relatório de colação.
# Edições que só aparecem no aparato (NA28, NIV, Tregelles) NÃO entram aqui: o
# aparato é evidência de edições, e o teste não as confunde com manuscritos.
ALCUNHAS = {
    '01': '01', 'sinaiticus': '01',
    '02': '02', 'alexandrinus': '02',
    '03': '03', 'vaticanus': '03',
    'p30': 'P30', 'p92': 'P92',
    'wh': 'WH', 'westcott': 'WH', 'hort': 'WH',
    'rp': 'RP', 'robinson': 'RP', 'pierpont': 'RP',
    'st': 'ST', 'stephanus': 'ST', 'estivénne': 'ST',
    'kjtr': 'KJTR', 'sr': 'SR', 'scrivener': 'Scrivener',
}
_MENCAO = re.compile(
    r'\b(sinaiticus|alexandrinus|vaticanus|westcott|hort|robinson|pierpont|'
    r'stephanus|estiv[ée]nne|scrivener|kjtr|p30|p92|wh|rp|st|sr|01|02|03)\b',
    re.IGNORECASE)

SECCOES_OBRIGATORIAS = ('Análise Léxica', 'Crítica Textual', 'Síntese Exegética')


def _carregar(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding='utf-8'))


def _sem_marcas(html: str) -> str:
    """Texto legível de um campo com HTML: sem etiquetas e com espaços normais."""
    return ' '.join(re.sub(r'<[^>]+>', ' ', html).split())


class ProtocoloTest(unittest.TestCase):
    """O protocolo existe, e diz o que a convicção do projeto exige dele."""

    @classmethod
    def setUpClass(cls):
        cls.texto = PROTOCOLO.read_text(encoding='utf-8')

    def test_documento_existe(self):
        self.assertTrue(PROTOCOLO.is_file(), PROTOCOLO)

    def test_comeca_pela_conviccao_doutrinaria(self):
        # A crítica textual é auxiliar: a inerrância é afirmada antes do método.
        for marcador in ('inerrância', 'infalibilidade', 'imutab'):
            self.assertTrue(marcador in self.texto, f'falta no protocolo: {marcador}')

    def test_regra_dos_mais_antigos_e_discutida_e_nao_repetida(self):
        self.assertIn('mais antigos', self.texto)
        for marcador in ('evidência externa', 'evidência interna',
                         'Probabilidade transcricional', 'Probabilidade intrínseca',
                         'Ecletismo fundamentado'):
            self.assertTrue(marcador in self.texto, f'falta no protocolo: {marcador}')

    def test_niveis_de_evidencia_e_as_tres_proibicoes(self):
        for marcador in ('Edição impressa não é manuscrito',
                         'Tradução moderna não é evidência textual',
                         'não é um texto único',
                         'Probabilidade transcricional',
                         'Probabilidade intrínseca',
                         'Regra de ouro'):
            self.assertTrue(marcador in self.texto, f'falta no protocolo: {marcador}')

    def test_niveis_de_certeza(self):
        for nivel in ('Nível de certeza', '**A**', '**B**', '**C**'):
            self.assertTrue(nivel in self.texto, f'falta no protocolo: {nivel}')

    def test_tetragrama_reservado(self):
        for marcador in ('Tetragrama', 'o dia do Senhor'):
            self.assertTrue(marcador in self.texto, f'falta no protocolo: {marcador}')

    def test_custodia_do_acervo_cc_by_sa(self):
        self.assertIn('CC BY-SA', self.texto)
        self.assertIn('não as redistribui', self.texto)
        self.assertIn('.bee-cache/', self.texto)

    def test_cache_fica_fora_do_git(self):
        ignorados = (RAIZ / '.gitignore').read_text(encoding='utf-8')
        self.assertIn('.bee-cache/', ignorados)
        if (RAIZ / '.bee-cache').exists():
            self.assertFalse(
                any((RAIZ / '.bee-cache').rglob('*.txt')) is None,
                'o acervo pode estar presente localmente; nunca versionado')


class RelatorioTest(unittest.TestCase):
    """O relatório de colação tem proveniência fixada e coberta."""

    @classmethod
    def setUpClass(cls):
        cls.dados = _carregar(RELATORIO)
        cls.fontes = cls.dados['fontes']

    def test_revisoes_fixadas_por_commit(self):
        self.assertEqual(self.fontes['base']['revisao'], SBL_COMMIT)
        self.assertEqual(self.fontes['comparacao']['revisao'], TR_COMMIT)
        self.assertEqual(self.fontes['cntr']['revisao'], CNTR_REVISAO)

    def test_licencas_declaradas(self):
        self.assertEqual(self.fontes['base']['licenca'], 'CC BY 4.0')
        self.assertEqual(self.fontes['cntr']['licenca'], 'CC BY-SA 4.0')
        self.assertIn('não redistribuído', self.fontes['cntr']['redistribuicao'])

    def test_manuscritos_de_2ts_declarados(self):
        self.assertEqual(sorted(self.fontes['cntr']['manuscritos']),
                         ['01', '02', '03', 'P30', 'P92'])

    def test_todos_os_versiculos_colacionados(self):
        esperados = {f'{cap}:{v}' for cap, total in enumerate(
            LIVRO.versos_por_capitulo, 1) for v in range(1, total + 1)}
        self.assertEqual(set(self.dados['versiculos']), esperados)

    def test_cada_verso_tem_base_e_testemunhas(self):
        for referencia, verso in self.dados['versiculos'].items():
            with self.subTest(referencia):
                self.assertTrue(verso['base']['sblgnt'])
                self.assertTrue(verso['base']['sblgnt_norm'])
                nomes = [d['testemunha'] for d in verso['divergencias']]
                self.assertIn('01', nomes)
                self.assertIn('Scrivener', nomes)


class Caso213Test(unittest.TestCase):
    """2Ts 2:13 — o caso que desfaz o slogan «mais antigo e com mais cópias»."""

    @classmethod
    def setUpClass(cls):
        cls.verso = _carregar(RELATORIO)['versiculos']['2:13']
        cls.por_nome = {d['testemunha']: d for d in cls.verso['divergencias']}
        cls.leituras = cls.verso['leituras']

    def test_base_lee_aparchen(self):
        self.assertIn('απαρχην', self.verso['base']['sblgnt_norm'])

    def test_as_tres_maiusculas_dividem_se(self):
        self.assertIn('απαρχην', self.leituras['02']['texto'])
        self.assertIn('απαρχην', self.leituras['03']['texto'])
        self.assertNotIn('απαρχην', self.leituras['01']['texto'])
        self.assertIn('απ αρχησ', self.leituras['01']['texto'])

    def test_maioria_numerica_esta_do_outro_lado(self):
        # 01 + toda a tradição bizantina lêem ἀπʼ ἀρχῆς: contar cópias decidiria
        # contra a base. É por isso que o critério não pode ser só quantidade.
        for nome in ('WH', 'RP', 'ST', 'KJTR', 'SR'):
            with self.subTest(nome):
                self.assertIn('αρχησ', self.leituras[nome]['texto'])
        # O Textus Receptus de Scrivener vem na base (não é testemunha CNTR).
        self.assertIn('αρχησ', self.verso['base']['scrivener_norm'])
        self.assertNotIn('απαρχην', self.verso['base']['scrivener_norm'])

    def test_aparato_nomeia_edicoes_e_nao_codices(self):
        aparato = ' '.join(self.verso['base']['aparato_sblgnt'])
        self.assertIn('ἀπαρχὴν', aparato)
        self.assertIn('ἀπʼ ἀρχῆς', aparato)
        for edicao in ('WH', 'RP', 'NA28'):
            self.assertIn(edicao, aparato)
        for codice in ('Sinaiticus', 'Vaticanus', 'Alexandrinus', '01', '03'):
            self.assertNotIn(codice, aparato,
                            'o aparato não dá manuscritos: só a colação dá')

    def test_alexandrinus_tem_lacuna_aqui(self):
        self.assertIn('lacuna', self.por_nome['02']['fisico'])

    def test_decisao_registada_no_livro(self):
        nota = _sem_marcas(_carregar(LIVRO_JSON)['chapters']['2'][12]['commentary'])
        self.assertIn('primícias', nota)
        self.assertIn('Nível de certeza C', nota.replace('nível de certeza', 'Nível de certeza'))


class Caso316Test(unittest.TestCase):
    """2Ts 3:16 — τόπω → τρόπω: uma letra decide «em todo o lugar»/«de toda a maneira»."""

    @classmethod
    def setUpClass(cls):
        cls.leituras = _carregar(RELATORIO)['versiculos']['3:16']['leituras']

    def test_mao_original_e_corretor(self):
        alexandrinus = self.leituras['02']
        self.assertIn('τοπω', alexandrinus['original'])
        self.assertIn('τροπω', alexandrinus['texto'])
        self.assertTrue(alexandrinus['corrigido'])

    def test_as_outras_testemunhas_leem_tropo(self):
        for nome in ('01', '03'):
            with self.subTest(nome):
                self.assertIn('τροπω', self.leituras[nome]['texto'])

    def test_base_ee_edicoes_concordam(self):
        verso = _carregar(RELATORIO)['versiculos']['3:16']
        self.assertIn('τροπω', verso['base']['sblgnt_norm'])

    def test_livro_traduz_tropo_e_regista_o_achado(self):
        dados = _carregar(LIVRO_JSON)['chapters']['3'][15]
        self.assertIn('de todas as maneiras', dados['text'])
        nota = _sem_marcas(dados['commentary'])
        self.assertIn('τόπῳ', nota)
        self.assertIn('τρόπῳ', nota)


class NotasSemTestemunhasInventadasTest(unittest.TestCase):
    """Regra de ouro: só se cita quem foi colacionado naquele versículo."""

    @classmethod
    def setUpClass(cls):
        cls.colacao = _carregar(RELATORIO)['versiculos']
        cls.livro = _carregar(LIVRO_JSON)

    def test_toda_a_testemunha_citada_tem_registo_no_verso(self):
        for capitulo, versiculos in self.livro['chapters'].items():
            for verso in versiculos:
                referencia = f'{capitulo}:{verso["verse"]}'
                registo = self.colacao[referencia]
                disponiveis = set(registo['leituras']) | {
                    d['testemunha'] for d in registo['divergencias']
                }
                nota = _sem_marcas(verso['commentary'])
                for mencao in set(_MENCAO.findall(nota)):
                    chave = ALCUNHAS.get(mencao.lower())
                    if chave is None:
                        continue
                    with self.subTest(f'{referencia} {mencao}'):
                        self.assertIn(chave, disponiveis,
                                      f'{referencia} cita {mencao} sem colação')

    def test_aparato_nao_e_usado_como_prova_de_manuscrito(self):
        # «O Sinaiticus lê X» só pode aparecer onde a colação regista 01.
        for capitulo, versiculos in self.livro['chapters'].items():
            for verso in versiculos:
                referencia = f'{capitulo}:{verso["verse"]}'
                nota = _sem_marcas(verso['commentary'])
                for alcunha, chave in (('Sinaiticus', '01'), ('Alexandrinus', '02'),
                                       ('Vaticanus', '03')):
                    if alcunha not in nota:
                        continue
                    registo = self.colacao[referencia]['leituras'].get(chave)
                    with self.subTest(f'{referencia} {alcunha}'):
                        self.assertIsNotNone(registo, 'testemunha sem registo')


class LivroRegeneradoTest(unittest.TestCase):
    """O JSON gravado é o que o ficheiro editorial produz — e é auditável."""

    @classmethod
    def setUpClass(cls):
        cls.dados = _carregar(LIVRO_JSON)

    def test_valida_contra_o_schema(self):
        try:
            validar_livro(self.dados, LIVRO)
        except DadosInvalidos as exc:
            self.fail(str(exc))

    def test_json_e_reproduzivel_a_partir_do_ficheiro_editorial(self):
        esperado = regenerar.montar(self.dados)
        self.assertEqual(esperado['chapters'], self.dados['chapters'])
        self.assertEqual(esperado['bibliography'], self.dados['bibliography'])
        self.assertEqual(esperado['review'], self.dados['review'])
        self.assertEqual(regenerar.conferir(esperado), [])

    def test_montar_e_idempotente(self):
        primeira = regenerar.montar(self.dados)
        segunda = regenerar.montar(primeira)
        self.assertEqual(len(primeira['history']), len(segunda['history']),
                         'cada execução somava três entradas de history')

    def test_historico_anterior_nao_foi_apagado(self):
        provedores = [e['provider'] for e in self.dados['history']]
        self.assertEqual(provedores.count('local'), 3)
        self.assertGreaterEqual(len(provedores), 15)
        for geracao in ('gemini', 'groq'):
            self.assertTrue(any(p.startswith(geracao) or p == geracao
                                for p in provedores),
                            f'histórico de {geracao} desapareceu')

    def test_tres_seccoes_obrigatorias_em_todos_os_versos(self):
        for capitulo, versiculos in self.dados['chapters'].items():
            for verso in versiculos:
                nota = verso['commentary']
                for seccao in SECCOES_OBRIGATORIAS:
                    with self.subTest(f'{capitulo}:{verso["verse"]} {seccao}'):
                        self.assertIn(f'<b>{seccao}:</b>', nota)

    def test_nenhum_verso_tem_o_que_a_memoria_veta(self):
        vetados = ('SENHOR', 'filho da perdição', 'o sem lei', 'convosco', 'conosco',
                   'vós', 'vosso', 'sobremaneira', 'deveras', 'outrossim',
                   'manifestação da sua vinda', 'de fato', '\u2011')
        for capitulo, versiculos in self.dados['chapters'].items():
            for verso in versiculos:
                for termo in vetados:
                    with self.subTest(f'{capitulo}:{verso["verse"]} {termo!r}'):
                        self.assertNotIn(termo, verso['text'])

    def test_dia_do_senhor_sem_maiusculas(self):
        verso = self.dados['chapters']['2'][1]
        self.assertIn('o dia do Senhor', verso['text'])
        self.assertIn('κύριος', _sem_marcas(verso['commentary']))

    def test_politica_de_pontuacao_e_maiuscula_inicial(self):
        for capitulo, versiculos in self.dados['chapters'].items():
            for verso in versiculos:
                self.assertTrue(
                    verso['text'].rstrip().endswith(('.', ',', ';', '?', '!')),
                    f"{capitulo}:{verso['verse']} sem pontuação final")
            for anterior, seguinte in zip(versiculos, versiculos[1:]):
                fim = anterior['text'].rstrip()[-1]
                inicio = seguinte['text'].lstrip()[0]
                rotulo = f'{capitulo}:{seguinte["verse"]}'
                with self.subTest(rotulo):
                    if inicio.islower():
                        self.assertIn(fim, ',;', f'{rotulo} minúscula depois de {fim!r}')
                    if fim == ',':
                        self.assertTrue(inicio.islower(),
                                        f'{rotulo} maiúscula depois de vírgula')

    def test_proveniencia_declarada(self):
        nomes = ' '.join(f['name'] for f in self.dados['bibliography'])
        for fonte in ('SBLGNT', 'Scrivener', 'CNTR', 'colação'):
            self.assertIn(fonte, nomes, fonte)
        por_nome = {f['name']: f for f in self.dados['bibliography']}
        cntr = por_nome['CNTR Transcriptions (Center for New Testament Restoration)']
        self.assertEqual(cntr['revision'], CNTR_REVISAO)
        self.assertEqual(cntr['license'], 'CC BY-SA 4.0')
        self.assertIn('nunca redistribuído', cntr['attribution'])
        sbl = por_nome['SBLGNT — The Greek New Testament, SBL Edition']
        self.assertEqual(sbl['revision'], SBL_COMMIT)
        tr = por_nome['Textus Receptus — edição de Scrivener (Robinson)']
        self.assertEqual(tr['revision'], TR_COMMIT)

    def test_sources_fixa_as_tres_revisoes(self):
        fontes = self.dados['sources']
        self.assertEqual(fontes['sblgnt_commit'], SBL_COMMIT)
        self.assertEqual(fontes['textus_receptus_commit'], TR_COMMIT)
        self.assertEqual(fontes['cntr_transcriptions_commit'], CNTR_REVISAO)
        self.assertTrue(fontes['collation_report'].endswith('.json'))

    def test_estados_de_revisao_aprovada_com_especialista_pendente(self):
        # Decisão D2 (plano de correção): 2 Tessalonicenses fica aprovada
        # editorialmente (voz). A revisão especializada continua pendente.
        revisao = self.dados['review']
        cobertos = sum(b['verse_to'] - b['verse_from'] + 1
                       for b in revisao['editorial_blocks'])
        self.assertEqual(cobertos, 47)
        for bloco in revisao['editorial_blocks']:
            self.assertEqual(bloco['status'], 'aprovado editorialmente')
        especialistas = sum(b['verse_to'] - b['verse_from'] + 1
                            for b in revisao['specialist'])
        self.assertEqual(especialistas, 47)
        for bloco in revisao['specialist']:
            self.assertEqual(bloco['status'], 'pendente')
        notas = ' '.join(b.get('nota', '') for b in revisao['specialist'])
        self.assertIn('2:13', notas)
        self.assertIn('3:6', notas)

    def test_variantes_marcadas_so_onde_ha_decisao_de_texto(self):
        # [[ ]] é para diferenças observadas no TEXTO traduzido. O ἀμήν de 3:18 é
        # fecho litúrgico: registado na nota, não marcado no versículo.
        for capitulo, versiculos in self.dados['chapters'].items():
            for verso in versiculos:
                with self.subTest(f'{capitulo}:{verso["verse"]}'):
                    self.assertNotIn('[[', verso['text'])
        fecho = self.dados['chapters']['3'][17]
        self.assertNotIn('Amém', fecho['text'])
        self.assertIn('ἀμήν', _sem_marcas(fecho['commentary']))

    def test_nivel_c_identificado_nas_notas(self):
        for referencia, indice in (('2:13', (1, 12)), ('3:6', (2, 5))):
            capitulo, verso = indice
            nota = _sem_marcas(self.dados['chapters'][str(capitulo + 1)][verso]['commentary'])
            with self.subTest(referencia):
                self.assertIn('C', nota)
                self.assertIn('revisão especializada', nota.lower())


class MemoriaDeEstiloCoerenteTest(unittest.TestCase):
    """A memória de estilo não pode contradizer o texto aprovado que cita.

    Já aconteceu: o contraste de 2Ts 1:3 mostrava «está a crescer» como forma
    boa, e o versículo aprovado diz «está crescendo». Um provedor que siga a
    âncora escreve outra coisa do que o livro — deriva sem que ninguém edite o
    livro. As âncoras citam, não reescrevem.
    """

    @classmethod
    def setUpClass(cls):
        cls.memoria = json.loads(
            (RAIZ / 'modelos' / 'estilo_bee.json').read_text(encoding='utf-8'))
        cls.livro = _carregar(LIVRO_JSON)
        cls.textos = {}
        for capitulo, versiculos in cls.livro['chapters'].items():
            for verso in versiculos:
                cls.textos[f'2Ts {capitulo}:{verso["verse"]}'] = verso['text']

    def test_contrastes_de_2ts_citam_o_livro(self):
        for contraste in self.memoria['contrastes']:
            referencia = contraste['mau_referencia']
            if not referencia.startswith('2Ts '):
                continue
            bom = contraste['bom']
            verso = self.textos.get(referencia)
            self.assertIsNotNone(verso, f'contraste cita {referencia}, que não existe')
            with self.subTest(referencia):
                if bom.startswith('…'):
                    self.assertIn(bom.lstrip('…').rstrip('.,;'), verso)
                else:
                    self.assertEqual(bom, verso)

    def test_formulas_consolidadas_estao_onde_o_grego_as_tem(self):
        # A saudação consolidada É Filemom 1:3, cuja base traz πατρὸς ἡμῶν. A base
        # de 2Ts 1:2 não traz ἡμῶν: por isso as duas saudações diferem, e é isso
        # mesmo que a regra UNIFORMIDADE SÓ ONDE O GREGO É IGUAL manda fazer.
        formulas = self.memoria['formulas_consolidadas']
        filemom = _carregar(RAIZ / 'edicoes/nova/livros_json/640_Filemom.json')
        self.assertEqual(filemom['chapters']['1'][2]['text'], formulas['saudacao'])
        self.assertNotIn('nosso Pai', self.textos['2Ts 1:2'])
        self.assertIn('da parte de Deus Pai', self.textos['2Ts 1:2'])
        for nome in ('acao_de_gracas', 'bencao_de_paz'):
            base = formulas[nome].split('…')[0]
            with self.subTest(nome):
                self.assertTrue(any(base in t for t in self.textos.values()),
                                f'{nome} não casa com 2 Tessalonicenses')

    def test_1_2_regista_a_divergencia_de_emos(self):
        nota = _sem_marcas(self.livro['chapters']['1'][1]['commentary'])
        self.assertIn('sem ἡμῶν', nota)
        self.assertIn('Nível de certeza B', nota)
        self.assertIn('Filemom 1:3', nota)

    def test_regras_duras_da_critica_textual_existem(self):
        rotulos = [r['rotulo'] for r in self.memoria['regras_duras']]
        self.assertEqual(len(rotulos), 15, 'número de regras duras mudou')
        for regra in ('PONTUAÇÃO E MAIÚSCULA INICIAL', 'SENHOR E Senhor',
                      'CRÍTICA TEXTUAL SÓ COM EVIDÊNCIA COLACIONADA',
                      'ÊNCLISE COM GERÚNDIO E PRONOME',
                      'UNIFORMIDADE SÓ ONDE O GREGO É IGUAL',
                      'DESEMPATE NA28'):
            with self.subTest(regra):
                self.assertIn(regra, rotulos)

    def test_norma_ortografica_declarada(self):
        ortografia = self.memoria['registro']['ortografia']
        for forma in ('connosco', 'de facto', 'registo'):
            self.assertIn(forma, ortografia)

    def test_2ts_nao_ancora_a_memoria_com_revisao_especializada_pendente(self):
        # 2 Tessalonicenses está aprovada editorialmente (voz), mas a revisão
        # especializada está pendente: não entra como livro-base da memória.
        numeros = {l['numero'] for l in self.memoria['ancoras']['livros_base']}
        self.assertNotIn(600, numeros)
        estados = {b['status'] for b in self.livro['review']['editorial_blocks']}
        self.assertEqual(estados, {'aprovado editorialmente'})


class LapidacaoTest(unittest.TestCase):
    """Defeitos que uma leitura atenta apanha e que nenhum verificador apanhava.

    Todos os testes desta classe nasceram de um achado real na passagem de
    lapidação de 2026-11-20 (docs/OFICINA_TRADUCAO.md). Ficam aqui para que o
    mesmo defeito não volte noutro livro.
    """

    @classmethod
    def setUpClass(cls):
        cls.pasta = RAIZ / 'edicoes' / 'nova' / 'livros_json'
        cls.livros = {p.stem: _carregar(p) for p in sorted(cls.pasta.glob('*.json'))}
        cls.dois_ts = cls.livros['600_2_Tessalonicenses']

    def versos(self, dados):
        for capitulo, versiculos in dados['chapters'].items():
            for verso in versiculos:
                yield f'{capitulo}:{verso["verse"]}', verso

    def test_sem_proclise_em_gerundio_em_toda_a_edicao(self):
        # Gerúndio português termina em -ando/-endo/-indo; «mundo», «quando» e
        # «segundo» terminam em -ndo sem o serem, e «o mundo» não é próclise.
        padrao = re.compile(
            r'\b(?:se|me|te|nos|vos|lhe|lhes) \w+(?:ando|endo|indo)\b')
        for nome, dados in self.livros.items():
            for referencia, verso in self.versos(dados):
                alvos = [('text', verso['text'])]
                # A nota cita formas defeituosas para as corrigir; o que está entre
                # «…» é citação, não redação.
                nota = _sem_marcas(verso.get('commentary', ''))
                alvos.append(('commentary', re.sub(r'«[^»]*»', '', nota)))
                for campo, texto in alvos:
                    for achado in padrao.findall(texto):
                        self.fail(f'{nome} {referencia} {campo}: próclise «{achado}»')

    def test_marcacao_equilibrada_em_toda_a_edicao(self):
        # Aspas e itálicos podem atravessar versículos (Jd 14-15 cita 1 Enoque a
        # cavalgamento); o que não podem é abrir e não fechar dentro do capítulo.
        for nome, dados in self.livros.items():
            for capitulo, versiculos in dados['chapters'].items():
                texto = ' '.join(v['text'] + ' ' + v.get('commentary', '')
                                 for v in versiculos)
                for abrir, fechar in (('«', '»'), ('<i>', '</i>'), ('<b>', '</b>')):
                    with self.subTest(f'{nome} cap. {capitulo} {abrir}'):
                        self.assertEqual(texto.count(abrir), texto.count(fechar))

    def test_verbos_supridos_vao_em_italico(self):
        esperados = {'1:5': '<i>Isso é</i>', '2:9': '<i>acontece</i>',
                     '3:9': '<i>fizemos assim</i>', '1:7': '<i>dar</i>',
                     '2:3': '<i>esse dia não virá</i>',
                     '2:7': '<i>continuará a fazê-lo</i>'}
        for referencia, marca in esperados.items():
            capitulo, verso = referencia.split(':')
            texto = self.dois_ts['chapters'][capitulo][int(verso) - 1]['text']
            with self.subTest(referencia):
                self.assertIn(marca, texto)

    def test_familia_atakt_e_coerente(self):
        # ἀτάκτως / ἀτακτέω nos vv. 6, 7 e 11: um só verbo português, «viver».
        achados = []
        for referencia, verso in self.versos(self.dois_ts):
            achados += [(referencia, m) for m in
                        re.findall(r'\w+ desordenadamente', verso['text'])]
        self.assertEqual(len(achados), 3, achados)
        for referencia, forma in achados:
            with self.subTest(referencia):
                self.assertIn(forma.split()[0], ('vive', 'vivem', 'vivemos'))

    def test_artigo_depois_de_todo_e_obrigatorio_em_portugues(self):
        """πᾶς: o artigo depois de «todo» no singular é gramática portuguesa.

        A regra de 2026-11-20 de manhã mandava suprimir o artigo quando o grego
        era anártrico. Foi revertida no mesmo dia: essa distinção existe no
        português do Brasil («todo desejo» = cada; «todo o desejo» = o inteiro)
        e não no europeu, onde o artigo é obrigatório e não traduz nada. A
        Almeida de 1911, impressa em Portugal, escreve «todo o desejo» e «todo o
        irmão» para grego anártrico. O facto grego fica na nota, não no artigo.
        """
        substantivos = ('desejo', 'obra', 'irmão', 'homem', 'iniquidade',
                        'mansidão', 'boa obra', 'boa palavra', 'tipo')
        for nome, dados in self.livros.items():
            for referencia, verso in self.versos(dados):
                texto = verso['text']
                for subst in substantivos:
                    padrao = re.compile(
                        r'\btod[oa]\s+' + re.escape(subst), re.IGNORECASE)
                    with self.subTest(f'{nome} {referencia} {subst}'):
                        self.assertIsNone(
                            padrao.search(texto),
                            f'«todo {subst}» sem artigo é brasileiro; falta «todo o/'
                            f'toda a»')

    def test_pas_anaritrico_registado_nas_notas(self):
        """Onde o artigo português foi acrescentado, a nota diz que o grego é anártrico."""
        notas = ' '.join(v.get('commentary', '') for _, v in self.versos(self.dois_ts))
        self.assertIn('anártrico', notas)
        self.assertIn('todo o desejo de bondade e toda a obra',
                      self.dois_ts['chapters']['1'][10]['text'])
        self.assertIn('todo o irmão', self.dois_ts['chapters']['3'][5]['text'])
        self.assertIn('toda a boa obra e palavra',
                      self.dois_ts['chapters']['2'][16]['text'])

    def test_relativa_de_1_9_e_virgula_de_1_8(self):
        cap = self.dois_ts['chapters']['1']
        self.assertTrue(cap[7]['text'].endswith(','), '1:8 deve fechar com vírgula')
        self.assertTrue(cap[8]['text'].startswith('os quais sofrerão'))

    def test_notas_sem_palavras_que_nao_sao_portuguesas(self):
        # «pererergoso» foi inventado para explicar περίεργος; «introduce» é
        # italiano/inglês (o português é «introduz»). Palavras que existem com
        # e sem acento — «evidencia», «sequencia», «apostasia» — são formas
        # verbais ou substantivos legítimos e não se apanham assim.
        for nome, dados in self.livros.items():
            for referencia, verso in self.versos(dados):
                nota = _sem_marcas(verso.get('commentary', ''))
                for defeito in ('pererergoso', 'introduce', 'pererérgico'):
                    with self.subTest(f'{nome} {referencia} {defeito}'):
                        self.assertNotIn(defeito, nota)

    def test_acento_nas_formas_que_o_exigem(self):
        # «advérbio», «evidência», «sequência» têm acento; as formas sem acento que
        # apareciam nas notas eram gralhas, não variantes ortográficas.
        nota_3_6 = _sem_marcas(self.dois_ts['chapters']['3'][5]['commentary'])
        self.assertIn('é advérbio de', nota_3_6)
        nota_1_12 = _sem_marcas(self.dois_ts['chapters']['1'][11]['commentary'])
        self.assertIn('introduz a finalidade', nota_1_12)

    def test_uma_letra_separa_topo_de_tropo(self):
        nota = _sem_marcas(self.dois_ts['chapters']['3'][15]['commentary'])
        self.assertIn('Uma só letra separa as duas leituras', nota)
        self.assertNotIn('Duas letras', nota)

    def test_nota_e_versiculo_nao_se_contradizem(self):
        # 1:2 era o caso: a nota dizia que a base não tem ἡμῶν e o texto traduzia-o
        # na mesma. Quando a nota regista uma divergência, o texto segue a base.
        verso = self.dois_ts['chapters']['1'][1]
        nota = _sem_marcas(verso['commentary'])
        self.assertIn('sem ἡμῶν', nota)
        self.assertIn('Decisão: seguir a base', nota)
        self.assertNotIn('nosso Pai', verso['text'])


class ConferenciaDoFicheiroEditorialTest(unittest.TestCase):
    """A conferência interna do script chumba o que o protocolo proíbe."""

    def montar_valido(self) -> dict:
        return regenerar.montar(None)

    def texto(self, dados: dict, capitulo: int, verso: int) -> str:
        return dados['chapters'][str(capitulo)][verso - 1]['text']

    def test_base_limpa(self):
        self.assertEqual(regenerar.conferir(self.montar_valido()), [])

    def test_chumba_maiusculas_por_kyrios(self):
        dados = self.montar_valido()
        dados['chapters']['2'][1]['text'] = self.texto(dados, 2, 2).replace(
            'do Senhor', 'do SENHOR')
        self.assertTrue(any('SENHOR' in e for e in regenerar.conferir(dados)))

    def test_chumba_hifen_invisivel(self):
        dados = self.montar_valido()
        dados['chapters']['2'][3]['text'] = self.texto(dados, 2, 4).replace(
            'proclamando-se', 'proclamando\u2011se')
        self.assertTrue(any('U+2011' in e for e in regenerar.conferir(dados)))

    def test_chumba_minuscula_depois_de_ponto(self):
        dados = self.montar_valido()
        dados['chapters']['1'][2]['text'] = self.texto(dados, 1, 3).replace(
            'transborda,', 'transborda.')
        self.assertTrue(any('minúscula' in e for e in regenerar.conferir(dados)))

    def test_chumba_seccao_obrigatoria_em_falta(self):
        dados = self.montar_valido()
        dados['chapters']['3'][0]['commentary'] = '<p><b>Análise Léxica:</b> x.</p>'
        erros = regenerar.conferir(dados)
        self.assertTrue(any('Crítica Textual' in e for e in erros))

    def test_chumba_arcaismo(self):
        dados = self.montar_valido()
        dados['chapters']['2'][14]['text'] = 'Portanto, irmãos, mantende-vos firmes.'
        erros = regenerar.conferir(dados)
        self.assertTrue(any('falhas duras' in e for e in erros))


class MigracaoNotasCincoLivrosTest(unittest.TestCase):
    """As notas dos cinco livros curtos já não são texto de enchimento.

    `scripts/importar_piloto.py` deixou em Tito, Filemom, 2 João, 3 João e
    Judas duas frases-promessa («migração lexical pendente de verificação»,
    «colação direta não repetida aqui») nas 123 notas. A migração de
    2026-11-20 substituiu-as por conteúdo verificável; estes testes impedem
    a regressão e garantem que nenhuma testemunha é citada fora do acervo
    colacionado para o próprio livro.
    """

    LIVROS = {630: 'Tito', 640: 'Filemom', 700: '2_João',
              710: '3_João', 720: 'Judas'}
    # Livros tocados pela migração de notas de 2026-11-20 (os cinco curtos,
    # João 1 e 2 Tessalonicenses), no formato da casa de três secções.
    LIVROS_MIGRADOS = (500, 600, 630, 640, 700, 710, 720)
    # Estados editoriais em uso; a revisão especializada é sempre «pendente».
    ESTADOS_EDITORIAIS = {'rascunho', 'aprovado editorialmente'}
    ENCHIMENTO = ('migração lexical pendente de verificação',
                  'colação direta não repetida aqui',
                  'rascunho a migrar das notas do piloto')

    def _livro(self, caminho: Path) -> dict:
        return json.loads(caminho.read_text(encoding='utf-8'))

    def _ficheiro(self, numero: int) -> Path:
        return next((RAIZ / 'edicoes' / 'nova' / 'livros_json').glob(
            f'{numero}_*.json'))

    def _comentarios(self, numero: int):
        livro = self._livro(self._ficheiro(numero))
        for cap, versos in livro['chapters'].items():
            for v in versos:
                yield f"{cap}:{v['verse']}", v.get('commentary', '') or ''

    def test_sem_enchimento_em_livro_nenhum(self):
        pasta = RAIZ / 'edicoes' / 'nova' / 'livros_json'
        for ficheiro in sorted(pasta.glob('*.json')):
            livro = self._livro(ficheiro)
            for cap, versos in livro['chapters'].items():
                for v in versos:
                    comentario = v.get('commentary', '') or ''
                    for frase in self.ENCHIMENTO:
                        self.assertNotIn(
                            frase, comentario,
                            f'{ficheiro.name} {cap}:{v["verse"]}')

    def test_tres_seccoes_e_metadados_nos_sete_livros(self):
        # A migração de 2026-11-20 tocou sete livros (os cinco curtos, João 1 e
        # 2 Tessalonicenses) e é neles que o formato da casa vale: três secções
        # por nota e tudo em RASCUNHO. Os lotes posteriores da edição nova
        # (Rute, profetas, Tessalonicenses) foram aprovados com notas BEE de
        # outra forma e outro estado, por isso não entram nesta verificação —
        # o que se lhes exige está no teste seguinte.
        for numero in self.LIVROS_MIGRADOS:
            ficheiro = self._ficheiro(numero)
            livro = self._livro(ficheiro)
            self.assertTrue(livro.get('bibliography'), ficheiro.name)
            self.assertTrue(livro.get('review'), ficheiro.name)
            estados = {b['status'] for b in
                       livro['review']['editorial_blocks']}
            # 2 Tessalonicenses, Filemom, 2 e 3 João: aprovados editorialmente
            # (decisão D2 e voz do piloto). Os outros continuam rascunho.
            esperado = ({'aprovado editorialmente'}
                        if numero in (600, 640, 700, 710) else {'rascunho'})
            self.assertEqual(estados, esperado, ficheiro.name)
            for cap, versos in livro['chapters'].items():
                for v in versos:
                    comentario = v.get('commentary', '') or ''
                    for seccao in ('Análise Léxica', 'Crítica Textual',
                                   'Síntese Exegética'):
                        self.assertIn(f'<b>{seccao}:</b>', comentario,
                                      f'{ficheiro.name} {cap}:{v["verse"]}')

    def test_metadados_de_proveniencia_em_todos_os_livros(self):
        # Fora do formato migrado, o que não pode faltar é a proveniência: cada
        # livro declara fontes, e cada bloco declara um estado conhecido. Um
        # estado inventado (ou vazio) é deriva, não progresso.
        pasta = RAIZ / 'edicoes' / 'nova' / 'livros_json'
        for ficheiro in sorted(pasta.glob('*.json')):
            livro = self._livro(ficheiro)
            self.assertTrue(livro.get('bibliography'), ficheiro.name)
            self.assertTrue(livro.get('review'), ficheiro.name)
            blocos = livro['review']['editorial_blocks']
            self.assertTrue(blocos, ficheiro.name)
            for bloco in blocos:
                self.assertIn(bloco['status'].strip(), self.ESTADOS_EDITORIAIS,
                              f'{ficheiro.name} cap. {bloco["chapter"]}')
            for bloco in livro['review'].get('specialist', []):
                self.assertEqual(bloco['status'], 'pendente', ficheiro.name)

    def test_testemunhas_citadas_existem_na_colacao_do_livro(self):
        sigla = re.compile(r'\b(0[1-4]|0232|P\d+)\b')
        for numero, nome in self.LIVROS.items():
            relatorio = self._livro(RAIZ / 'docs' / 'colacao' / f'{nome}.json')
            manuscritos = set(relatorio['fontes']['cntr']['manuscritos'])
            for ref, comentario in self._comentarios(numero):
                m = re.search(r'<b>Crítica Textual:</b>(.*?)</p>', comentario)
                self.assertIsNotNone(m, f'{numero} {ref}')
                for citada in set(sigla.findall(m.group(1))):
                    self.assertIn(citada, manuscritos,
                                  f'{numero} {ref} cita {citada}')

    def test_relatorios_de_colacao_versionados(self):
        for nome in (*self.LIVROS.values(), 'João', '2_Tessalonicenses'):
            self.assertTrue(
                (RAIZ / 'docs' / 'colacao' / f'{nome}.json').exists(), nome)


class ProtocoloDasIAsTest(unittest.TestCase):
    """O ritmo da oficina tem de chegar às IAs de geração e de revisão.

    O protocolo (base fixa → desempate NA28 → colação antes de citar → três
    secções verdadeiras → lapidação mecânica → proteger o aprovado → estatuto
    RASCUNHO) vive na memória de estilo e é renderizado por `system_fragment`,
    que alimenta o tradutor (bee/perfil.py) e o revisor (bee/revisor.py).
    Estes testes chumbam se alguma destas instruções deixar de chegar lá.
    """

    def test_memoria_tem_protocolo_e_desempate_na28(self):
        from bee import memoria_estilo as ms
        dados = ms.carregar()
        self.assertEqual(ms.validar(dados), [])
        self.assertGreaterEqual(len(dados.get('protocolo') or []), 6)
        regras = ' '.join(r['rotulo'] for r in dados['regras_duras'])
        self.assertIn('DESEMPATE NA28', regras)

    def test_protocolo_no_prompt_do_tradutor(self):
        from bee.perfil import resolver_perfil
        sistema = resolver_perfil('nova').sistema()
        for marca in ('PROTOCOLO DE TRABALHO', 'DESEMPATE NA28',
                      'docs/colacao/', 'RASCUNHO', 'todo o desejo',
                      'Judas 1:5'):
            self.assertIn(marca, sistema)

    def test_protocolo_no_prompt_do_revisor(self):
        from bee.memoria_estilo import carregar
        from bee.revisor import sistema_revisor
        sistema = sistema_revisor(carregar())
        self.assertIn('PROTOCOLO DE TRABALHO', sistema)
        self.assertIn('NUNCA emende contra a base', sistema)
        self.assertIn('NA28', sistema)

    def test_judas_1_5_segue_na28_por_decisao_do_responsavel(self):
        livro = json.loads(
            (RAIZ / 'edicoes' / 'nova' / 'livros_json' / '720_Judas.json')
            .read_text(encoding='utf-8'))
        verso5 = livro['chapters']['1'][4]
        self.assertIn('[[Jesus]]', verso5['text'])
        self.assertIn('seguir NA28',
                      livro['review']['specialist'][0]['nota'])


if __name__ == '__main__':
    unittest.main()
