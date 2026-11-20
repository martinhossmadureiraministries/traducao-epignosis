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
    return re.sub(r'<[^>]+>', ' ', html)


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

    def test_estados_de_revisao_declarados_como_rascunho(self):
        revisao = self.dados['review']
        cobertos = sum(b['verse_to'] - b['verse_from'] + 1
                       for b in revisao['editorial_blocks'])
        self.assertEqual(cobertos, 47)
        for bloco in revisao['editorial_blocks']:
            self.assertEqual(bloco['status'], 'rascunho')
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

    def test_formulas_consolidadas_estao_no_livro(self):
        for nome, formula in self.memoria['formulas_consolidadas'].items():
            base = formula.split('…')[0]
            with self.subTest(nome):
                self.assertTrue(
                    any(t.startswith(base) or base in t for t in self.textos.values()),
                    f'{nome} não casa com nenhum versículo de 2 Tessalonicenses')

    def test_regras_duras_da_critica_textual_existem(self):
        rotulos = [r['rotulo'] for r in self.memoria['regras_duras']]
        self.assertEqual(len(rotulos), 12, 'número de regras duras mudou')
        for regra in ('PONTUAÇÃO E MAIÚSCULA INICIAL', 'SENHOR E Senhor',
                      'CRÍTICA TEXTUAL SÓ COM EVIDÊNCIA COLACIONADA'):
            with self.subTest(regra):
                self.assertIn(regra, rotulos)

    def test_norma_ortografica_declarada(self):
        ortografia = self.memoria['registro']['ortografia']
        for forma in ('connosco', 'de facto', 'registo'):
            self.assertIn(forma, ortografia)

    def test_2ts_nao_e_livro_base_enquanto_for_rascunho(self):
        # Os livros-base são os aprovados pelo responsável. 2 Tessalonicenses foi
        # regenerado por mão editorial e continua RASCUNHO: não ancora ninguém.
        numeros = {l['numero'] for l in self.memoria['ancoras']['livros_base']}
        self.assertNotIn(600, numeros)
        estados = {b['status'] for b in self.livro['review']['editorial_blocks']}
        self.assertEqual(estados, {'rascunho'})


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


if __name__ == '__main__':
    unittest.main()
