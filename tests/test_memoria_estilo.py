"""Memória de estilo (P0): um único JSON alimenta os prompts de todos os provedores.

Garante que:
  * o schema de modelos/estilo_bee.json é validado e falha alto quando violado;
  * os renderizadores produzem fragmentos determinísticos com as marcas da voz
    (lista negra, regras duras, aperto, glossário, fórmulas, contrastes);
  * o contexto de reuso marca as decisões já aprovadas no livro em tradução;
  * a edição nova recebe tudo isto e o legado fica byte-idêntico;
  * a lista negra da memória está coberta pela guarda anti-deriva (coerência P1).
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from bee import memoria_estilo as ms
from bee.perfil import PERFIS

RAIZ = Path(__file__).resolve().parents[1]

# Importa a guarda tal como tests/test_verificar_estilo.py (scripts não é pacote).
_spec = importlib.util.spec_from_file_location(
    'verificar_estilo', RAIZ / 'scripts' / 'verificar_estilo.py')
ve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ve)


class SchemaTest(unittest.TestCase):
    def test_ficheiro_padrao_carrega_e_valida(self):
        dados = ms.carregar()
        self.assertEqual(ms.validar(dados), [])
        self.assertEqual(ms.CAMINHO_PADRAO.name, 'estilo_bee.json')

    def test_cada_chave_obrigatoria_e_verificada(self):
        base = ms.carregar()
        for chave in ms._CHAVES_OBRIGATORIAS:
            mutado = copy.deepcopy(base)
            del mutado[chave]
            erros = ms.validar(mutado)
            self.assertTrue(any(chave in erro for erro in erros),
                            f'{chave} sem erro: {erros}')

    def test_entrada_de_glossario_incompleta_e_erro(self):
        dados = copy.deepcopy(ms.carregar())
        dados['glossario'][0].pop('usar')
        self.assertTrue(any('usar' in e for e in ms.validar(dados)))
        dados = copy.deepcopy(ms.carregar())
        dados['glossario'][0].pop('grego')      # fica sem grego E sem termo
        self.assertTrue(any('grego ou termo' in e for e in ms.validar(dados)))

    def test_lista_negra_vazia_e_erro_e_falha_alto_no_carregar(self):
        dados = copy.deepcopy(ms.carregar())
        dados['registro']['arcaismos_proibidos'] = []
        self.assertTrue(any('arcaismos_proibidos' in e for e in ms.validar(dados)))
        with tempfile.TemporaryDirectory() as tmp:
            caminho = Path(tmp) / 'estilo.json'
            caminho.write_text(json.dumps(dados, ensure_ascii=False), encoding='utf-8')
            with self.assertRaises(ValueError) as ctx:
                ms.carregar(caminho)
        self.assertIn('arcaismos_proibidos', str(ctx.exception))

    def test_formulas_todas_presentes_e_nao_vazias(self):
        dados = copy.deepcopy(ms.carregar())
        dados['formulas_consolidadas']['bencao_de_paz'] = ''
        self.assertTrue(any('bencao_de_paz' in e for e in ms.validar(dados)))


class CoerenciaComAGuardaTest(unittest.TestCase):
    """A memória promete proibir; a guarda tem mesmo de detetar."""

    def test_lista_negra_coberta_pelos_arcaismos_da_guarda(self):
        memoria = set(t.lower() for t in ms.carregar()['registro']['arcaismos_proibidos'])
        guarda = set(ve.ARCAISMOS)
        self.assertEqual(memoria - guarda, set(),
                         'arcaísmos na memória que a guarda não deteta')

    def test_hedges_rejeitados_sao_falha_dura_na_guarda(self):
        for hedge in ve.HEDGE_FRASES:
            res = ve.analisar_texto(f'Texto qualquer, {hedge}, continuação.')
            self.assertIn(hedge, res['duros'])
        # «ou seja» e «isto é» estão nos rejeitados da memória
        itens = ' '.join(r['item'].lower() for r in ms.carregar()['rejeitados'])
        self.assertIn('ou seja', itens)
        self.assertIn('isto é', itens)

    def test_marcadores_de_almeida_rejeitados_dao_aviso(self):
        rejeitados = ' '.join(r['item'].lower() for r in ms.carregar()['rejeitados'])
        for marcador in ('sobremaneira', 'o sem lei'):
            self.assertIn(marcador, rejeitados)
            self.assertIn(marcador, ve.MARCADORES_ALMEIDA)


class RenderizacaoTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dados = ms.carregar()

    def test_system_fragment_traz_toda_a_estruturada_voz(self):
        texto = ms.system_fragment(self.dados)
        for marca in ('MEMÓRIA DE ESTILO', 'ESTILO_BEE', 'MÉTODO POR UNIDADE',
                      'VOZ E REGISTO', 'REGRESSÕES PROIBIDAS',
                      'APERTO ADICIONAL', 'PROIBIÇÕES GLOBAIS', 'APROVAÇÕES'):
            self.assertIn(marca, texto)
        # todas as regras duras e apertos numerados, pelos rótulos do JSON
        for regra in self.dados['regras_duras']:
            self.assertIn(regra['rotulo'], texto)
        for item in self.dados['aperto']:
            self.assertIn(item['rotulo'], texto)
        self.assertIn('vós/vos/vosso/vossa/convosco', texto)

    def test_glossario_marca_reuso_apenas_no_livro_certo(self):
        nenhum = ms.glossario_para_pedido(self.dados)
        self.assertNotIn('JÁ APROVADA', nenhum)
        filemom = ms.glossario_para_pedido(self.dados, livro_numero=640)
        # σπλάγχνα, κοινωνία, συστρατιώτης e ἐπίγνωσις têm Filemom aprovado
        self.assertGreaterEqual(filemom.count('JÁ APROVADA'), 4)
        tito = ms.glossario_para_pedido(self.dados, livro_numero=630)
        # Tito só tem ἐπίγνωσις aprovada
        self.assertEqual(tito.count('JÁ APROVADA'), 1)
        self.assertIn('NUNCA traduzir literalmente por «entranhas»', filemom)
        self.assertIn('epignōsis', filemom)
        self.assertIn('PALAVRAS E FORMULAÇÕES REJEITADAS', filemom)

    def test_amostras_por_genero_com_queda_para_todas(self):
        carta = ms.amostras_para_genero(self.dados, 'carta')
        for amostra in self.dados['ancoras']['amostras']:
            self.assertIn(amostra['referencia'], carta, 'género carta cobre tudo hoje')
        self.assertIn('LIVROS-BASE desta voz: Filemom, Tito, Judas, 2 João, 3 João', carta)
        self.assertIn('EVITAR', carta)
        # género desconhecido => todas as amostras (antes âncoras do que nenhuma)
        desconhecido = ms.amostras_para_genero(self.dados, 'poesia')
        self.assertIn('Filemom 1:7', desconhecido)

    def test_contrastes_nascem_de_regressoes_reais(self):
        texto = ms.contrastes(self.dados)
        self.assertIn('CONTRASTES (mau → bom', texto)
        for par in self.dados['contrastes']:
            self.assertIn(par['mau'], texto)
            self.assertIn(par['bom'], texto)
        self.assertIn('MAU 2Ts 1:2', texto)

    def test_formulas_exatas_incluindo_a_saudacao_do_piloto(self):
        texto = ms.formulas(self.dados)
        formulas = self.dados['formulas_consolidadas']
        for valor in formulas.values():
            self.assertIn(valor, texto)
        # a saudação consolidada É o texto aprovado de Filemom 1:3, letra a letra
        # (a pontuação final pode diferir: a fórmula fecha a frase com ponto)
        piloto = json.loads((RAIZ / 'edicoes/nova/livros_json/640_Filemom.json')
                            .read_text(encoding='utf-8'))
        verso3 = next(v for v in piloto['chapters']['1'] if v['verse'] == 3)
        self.assertEqual(formulas['saudacao'].rstrip('.'), verso3['text'].rstrip('.'))

    def test_bloco_amostras_compoe_as_tres_partes(self):
        bloco = ms.bloco_amostras(self.dados)
        self.assertIn('AMOSTRAS DE VOZ APROVADAS', bloco)
        self.assertIn('CONTRASTES', bloco)
        self.assertIn('FÓRMULAS CONSOLIDADAS', bloco)


class PerfilNovaVemDaMemoriaTest(unittest.TestCase):
    def test_o_perfil_nova_usa_os_renderizadores(self):
        dados = ms.carregar()
        nova = PERFIS['nova']
        self.assertEqual(nova.glossario, ms.glossario_para_pedido(dados))
        self.assertEqual(nova.amostras, ms.bloco_amostras(dados))
        self.assertTrue(nova.system_prompt.endswith(ms.system_fragment(dados)))
        self.assertIsNotNone(nova.render_glossario)

    def test_glossario_pedido_por_livro_no_perfil(self):
        nova = PERFIS['nova']
        self.assertIn('JÁ APROVADA', nova.glossario_pedido(640))
        self.assertNotIn('JÁ APROVADA', nova.glossario_pedido(None))

    def test_legado_byte_identico_sem_renderizador(self):
        from bee.gerador import GLOSSARIO_PADRAO
        legado = PERFIS['legado']
        self.assertIsNone(legado.render_glossario)
        self.assertEqual(legado.glossario_pedido(640), GLOSSARIO_PADRAO)
        self.assertEqual(legado.glossario_pedido(None), GLOSSARIO_PADRAO)
        self.assertNotIn('JÁ APROVADA', legado.glossario_pedido(640))


if __name__ == '__main__':
    unittest.main()
