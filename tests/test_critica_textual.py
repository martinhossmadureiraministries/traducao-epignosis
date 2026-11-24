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
     gravado é o que o script de conversão de 2026-11-20 produziu; a proveniência
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
        # Decisão de 2026-11-20: os níveis A/B/C de certeza não aparecem nas notas
        # nem na documentação. O protocolo diz isso; nenhum marcador A/B/C fica impresso.
        self.assertIn('sem notação de nível', self.texto)
        for marca in ('**A**', '**B**', '**C**', '| A |', '| B |', '| C |'):
            self.assertNotIn(marca, self.texto, f'nível de certeza impresso: {marca}')

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
        # A leitura alternativa (ἀπʼ ἀρχῆς, «desde o princípio») fica registada na nota.
        self.assertIn('desde o princípio', nota)
        self.assertIn('seguir a base', nota)


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
        self.assertIn('Decisão: seguir a base', nota)
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

    def test_2ts_entra_como_livro_base_com_aprovacao_editorial(self):
        # 2 Tessalonicenses está aprovado editorialmente pelo responsável, que o
        # indicou como livro-base. A revisão especializada (especialista externo)
        # continua pendente e não é feita pelo agente nem pelo responsável.
        numeros = {l['numero'] for l in self.memoria['ancoras']['livros_base']}
        self.assertIn(600, numeros)
        estados = {b['status'] for b in self.livro['review']['editorial_blocks']}
        self.assertEqual(estados, {'aprovado editorialmente'})
        self.assertTrue(self.livro['review']['specialist'])
        self.assertTrue(all(b['status'] == 'pendente'
                            for b in self.livro['review']['specialist']))


class LapidacaoTest(unittest.TestCase):
    """Defeitos que uma leitura atenta apanha e que nenhum verificador apanhava.

    Todos os testes desta classe nasceram de um achado real na passagem de
    lapidação de 2026-11-20 (a oficina de tradução não está no repositório). Ficam aqui para que o
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
