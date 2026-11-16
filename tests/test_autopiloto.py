import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
import unittest
from zoneinfo import ZoneInfo

import autopiloto
from bee.agenda import (
    Agendador, ConfigAgenda, Diario, Estado, dentro_da_janela, livros_na_fila,
)
from bee.catalogo import POR_NUMERO as LIVROS_POR_NUMERO
from bee.gerador import ConfigGeracao, gerar_fatia
from bee.ia import MotorIA, PROVEDORES, Rodizio, VERSOS_POR_PEDIDO_PADRAO
from bee.rede import CotaExcedida, ErroRede, ServicoIndisponivel


class FontesFalsas:
    def __init__(self, *args, **kwargs):
        self.calls = []

    def capitulo(self, livro, capitulo):
        self.calls.append((livro.numero, capitulo))
        return [{'verse': v, 'base': [{'edicao': 'SBLGNT', 'texto': 'λόγος'}]}
                for v in range(1, livro.versos_por_capitulo[capitulo - 1] + 1)]


class MotorFalso:
    """Produz versículos com a forma exigida pela validação do projeto."""

    provedor = 'gemini'
    modelo = 'modelo-teste'

    def __init__(self, falhar_em=None, erro=None):
        self.lotes = []
        self.estilos = []
        self.falhar_em = falhar_em
        self.erro = erro or ErroRede('falha simulada')

    def gerar(self, livro, capitulo, fontes, estilo=None):
        self.lotes.append([f['verse'] for f in fontes])
        self.estilos.append(estilo)
        if self.falhar_em is not None and len(self.lotes) == self.falhar_em:
            raise self.erro
        return [
            {'verse': f['verse'], 'text': f'Texto {f["verse"]}.',
             'commentary': (
                 '<p><b>Análise Léxica:</b> não verificada em léxico.</p>'
                 '<p><b>Crítica Textual:</b> sem variante verificada.</p>'
                 '<p><b>Síntese Exegética:</b> teste automático.</p>'
             )}
            for f in fontes
        ]


class TestadorFalso(MotorFalso):
    """Finge a resposta mínima usada por --testar."""

    def testar_ligacao(self):
        raise ErroRede('gemini: falha de rede (URLError); esgotadas 1 tentativas.')


class Base(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.raiz = Path(self.temp.name)
        self.dados = self.raiz / 'livros_json'
        self.saida = self.raiz / 'modulos'
        self.cache = self.raiz / 'cache'
        self.fuso = ZoneInfo('Africa/Luanda')

    def agendador(self, estado=None, **config):
        parametros = dict(
            intervalo_min=0, max_versos=10, pedidos_por_dia=1000, fuso='Africa/Luanda',
            compilar=True, pausa_rede=0, tentativas_rede=1, timeout=30,
        )
        parametros.update(config)
        motor = parametros.pop('motor', None) or MotorFalso()
        cfg = ConfigAgenda(**parametros)
        diario = Diario(self.dados / '.bee' / 'diario.md')
        return Agendador(
            self.dados, self.saida, self.cache, estado or Estado(), cfg, diario,
            self.fuso, [motor], FontesFalsas(), None,
        ), motor


class FatiaTest(Base):
    def test_uma_fatia_respeita_orcamento_e_retoma_no_versiculo_seguinte(self):
        livro = LIVROS_POR_NUMERO[640]
        motor = MotorFalso()
        progresso = gerar_fatia(
            [livro], self.dados, FontesFalsas(), motor,
            ConfigGeracao(versos_por_pedido=8, max_versos=10),
        )
        self.assertEqual(progresso.versos, 10)
        self.assertEqual(motor.lotes, [[1, 2, 3, 4, 5, 6, 7, 8], [9, 10]])
        dados = json.loads((self.dados / '640_Filemom.json').read_text(encoding='utf-8'))
        self.assertEqual(len(dados['in_progress']['1']), 10)
        self.assertEqual(dados['chapters'], {})

        segundo = MotorFalso()
        progresso = gerar_fatia(
            [livro], self.dados, FontesFalsas(), segundo,
            ConfigGeracao(versos_por_pedido=8, max_versos=100),
        )
        self.assertEqual(segundo.lotes[0], [11, 12, 13, 14, 15, 16, 17, 18])
        self.assertEqual(progresso.capitulos, 1)
        dados = json.loads((self.dados / '640_Filemom.json').read_text(encoding='utf-8'))
        self.assertEqual(len(dados['chapters']['1']), 25)
        self.assertEqual(dados['in_progress'], {})

    def test_estilo_envia_glossario_e_ultimo_versiculo_anterior(self):
        livro = LIVROS_POR_NUMERO[640]
        motor = MotorFalso()
        gerar_fatia([livro], self.dados, FontesFalsas(), motor,
                    ConfigGeracao(versos_por_pedido=3, max_versos=6))
        self.assertIn('SENHOR', motor.estilos[0]['glossario'])
        self.assertNotIn('anterior', motor.estilos[0])
        self.assertIn('Texto 3.', motor.estilos[1]['anterior'])

    def test_sem_capitulos_pendentes_nao_chama_o_motor(self):
        livros = [LIVROS_POR_NUMERO[640]]
        gerar_fatia(livros, self.dados, FontesFalsas(), MotorFalso(), ConfigGeracao())
        motor = MotorFalso()
        progresso = gerar_fatia(livros, self.dados, FontesFalsas(), motor, ConfigGeracao())
        self.assertEqual(motor.lotes, [])
        self.assertTrue(progresso.concluido)
        self.assertEqual(progresso.versos, 0)


class AgendaTest(Base):
    def test_janela_diaria_e_espera_ate_abrir(self):
        from datetime import datetime, timezone
        noite = datetime(2026, 11, 16, 23, 30, tzinfo=timezone.utc)  # 00:30 em Luanda
        self.assertFalse(dentro_da_janela(noite, self.fuso, 5, 23))
        self.assertTrue(dentro_da_janela(noite, self.fuso, 0, 24))
        manha = datetime(2026, 11, 16, 5, 0, tzinfo=timezone.utc)     # 06:00 em Luanda
        self.assertTrue(dentro_da_janela(manha, self.fuso, 5, 23))

    def test_ciclo_grava_estado_diario_e_diario_legivel(self):
        agendador, motor = self.agendador()
        resultado = agendador.ciclo(livros_na_fila([640]))
        self.assertEqual(resultado.acao, 'gerado')
        self.assertEqual(resultado.progresso.versos, 10)
        estado = agendador.estado
        dia = next(iter(estado.dias.values()))
        self.assertEqual(dia['versos'], 10)
        self.assertEqual(dia['pedidos'], 2)
        self.assertGreaterEqual(dia['capitulos'], 0)
        diario = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('Ciclo 1: +10 versículos', diario)

    def test_orcamento_diario_de_pedidos_para_o_trabalho(self):
        agendador, _ = self.agendador(pedidos_por_dia=2)
        self.assertEqual(agendador.ciclo(livros_na_fila([640])).acao, 'gerado')
        segundo = agendador.ciclo(livros_na_fila([640]))
        self.assertEqual(segundo.acao, 'parar')
        self.assertIn('orçamento diário', segundo.detalhe)

    def test_falha_nao_apaga_progresso_e_conta_falhas_seguidas(self):
        motor = MotorFalso(falhar_em=2)
        agendador, _ = self.agendador(motor=motor)
        resultado = agendador.ciclo(livros_na_fila([640]))
        self.assertEqual(resultado.acao, 'nada')
        self.assertEqual(agendador.estado.falhas_seguidas, 1)
        dados = json.loads((self.dados / '640_Filemom.json').read_text(encoding='utf-8'))
        self.assertEqual(len(dados['in_progress']['1']), 8)
        diario = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('ERRO', diario)

    def test_compila_quando_ha_capitulo_completo_e_publica_zip(self):
        agendador, _ = self.agendador(max_versos=40)
        agendador.ciclo(livros_na_fila([640]))
        self.assertTrue((self.saida / 'BEE.SQLite3').exists())
        with sqlite3.connect(self.saida / 'BEE.SQLite3') as conexao:
            self.assertEqual(conexao.execute('SELECT COUNT(*) FROM verses').fetchone()[0], 25)
        self.assertIsNotNone(agendador.estado.ultima_compilacao_build)


class FilaTest(Base):
    def test_ordem_do_plano_comeca_por_filemom_e_joao(self):
        fila = livros_na_fila()
        self.assertEqual([l.numero for l in fila[:3]], [640, 500, 480])
        self.assertEqual(len(fila), 66)
        self.assertEqual(livros_na_fila(ordem='canonica')[0].numero, 10)
        self.assertEqual(livros_na_fila(ordem='curtos')[0].numero, 640)

    def test_livros_restritos_mantem_a_ordem_pedida(self):
        self.assertEqual([l.numero for l in livros_na_fila([500, 640])], [500, 640])
        self.assertEqual([l.numero for l in livros_na_fila([640, 500])], [640, 500])
        self.assertEqual([l.numero for l in livros_na_fila([640, 640, 999])], [640])


class DiarioTest(Base):
    def test_diario_roda_quando_fica_grande(self):
        diario = Diario(self.dados / '.bee' / 'diario.md')
        diario.escrever('primeira linha')
        diario.LIMITE_BYTES = 10
        diario.escrever('depois da rotação')
        texto = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('continuação', texto)
        self.assertIn('depois da rotação', texto)


class ArranqueTest(Base):
    """O que é preciso para começar hoje, num ambiente real."""

    def test_env_carrega_chaves_sem_imprimir_valores(self):
        ficheiro = self.raiz / '.env'
        ficheiro.write_text(
            '# comentário\nGEMINI_API_KEY="segredo-123"\nGROQ_API_KEY=outro\n',
            encoding='utf-8',
        )
        ambiente = {}
        with patch.dict(os.environ, ambiente, clear=True), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            nomes = autopiloto.carregar_env(ficheiro)
            self.assertEqual(nomes, ['GEMINI_API_KEY', 'GROQ_API_KEY'])
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'segredo-123')
        self.assertNotIn('segredo-123', saida.getvalue())

    def test_ambiente_tem_precedencia_sobre_o_ficheiro(self):
        ficheiro = self.raiz / '.env'
        ficheiro.write_text('GEMINI_API_KEY=do-ficheiro\n', encoding='utf-8')
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'do-ambiente'}, clear=True):
            autopiloto.carregar_env(ficheiro)
            self.assertEqual(os.environ['GEMINI_API_KEY'], 'do-ambiente')

    def test_testar_chave_nao_grava_conteudo_e_devolve_erro_em_falha(self):
        with patch.dict(os.environ, {'GEMINI_API_KEY': 'chave-de-teste'}, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('autopiloto._motores', return_value=[TestadorFalso()]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = autopiloto.main(['--testar', '--dados', str(self.dados)])
        self.assertEqual(codigo, 1)
        self.assertIn('FALHOU', saida.getvalue())
        self.assertFalse((self.dados / '640_Filemom.json').exists())

    def test_uniao_de_progresso_preserva_revisao_local(self):
        import nuvem
        local, remoto = self.raiz / 'local', self.raiz / 'remoto'
        local.mkdir()
        remoto.mkdir()
        base = {'format_version': 1, 'book_number': 640, 'book_name': 'Filemom',
                'chapter_count': 1, 'chapters': {}, 'history': []}
        revisado = {'verse': 1, 'text': 'VERSÃO REVISTA À MÃO', 'commentary': '<p>Análise Léxica</p>'}
        da_ia = {'verse': 1, 'text': 'versão da IA', 'commentary': '<p>x</p>'}
        novo = {'verse': 2, 'text': 'novo da IA', 'commentary': '<p>y</p>'}
        (local / '640_Filemom.json').write_text(
            json.dumps({**base, 'in_progress': {'1': [revisado]}}), encoding='utf-8')
        (remoto / '640_Filemom.json').write_text(
            json.dumps({**base, 'in_progress': {'1': [da_ia, novo]}}), encoding='utf-8')
        mantidos = nuvem._unir_progresso(local, remoto)
        dados = json.loads((local / '640_Filemom.json').read_text(encoding='utf-8'))
        self.assertEqual(mantidos, 1)
        self.assertEqual([v['text'] for v in dados['in_progress']['1']],
                         ['VERSÃO REVISTA À MÃO', 'novo da IA'])


class IndisponibilidadeTest(Base):
    """O caso real de 16/11: o Gemini respondeu 503 e a produção parou."""

    def test_503_no_gemini_passa_para_o_groq_e_continua(self):
        notas = []
        gemini = MotorFalso(falhar_em=1, erro=ServicoIndisponivel('gemini: HTTP 503; esgotadas 3 tentativas.'))
        groq = MotorFalso()
        groq.provedor = 'groq'
        rodizio = Rodizio([gemini, groq], registar=notas.append)
        versos = rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(versos[0]['verse'], 1)
        self.assertEqual(rodizio.provedor, 'groq')
        self.assertEqual(rodizio.esgotados(), [], 'um 5xx não deve marcar o provedor como esgotado')
        # O rodízio registou a passagem ao provedor seguinte, sem tratar o 5xx como quota.
        self.assertTrue(any('outro provedor' in n for n in notas), notas)

    def test_reconhece_erro_passageiro_e_de_configuracao(self):
        import nuvem
        for erro in ('gemini: HTTP 503; esgotadas 3 tentativas.',
                     'ServicoIndisponivel: HTTP 500',
                     'gemini: falha de rede (URLError)',
                     'gemini: timed out'):
            self.assertTrue(nuvem._parece_transitorio(erro), erro)
        for erro in ('gemini: HTTP 401; verifique a chave do provedor.',
                     'RespostaInvalida: falta a seção', ''):
            self.assertFalse(nuvem._parece_transitorio(erro), erro)

    def test_avisos_de_rede_vao_para_o_diario(self):
        motor = MotorFalso()
        agendador, _ = self.agendador(motor=motor)
        agendador._obter_rodizio()
        self.assertTrue(callable(motor.log))
        motor.log('gemini: HTTP 503; nova tentativa em 1.6s (1/3).')
        diario = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('HTTP 503', diario)
        self.assertIn('AVISO', diario)

    def test_nuvem_repete_quando_o_erro_e_passageiro(self):
        import nuvem
        motor = MotorFalso(falhar_em=1, erro=ServicoIndisponivel('gemini: HTTP 503; esgotadas 3 tentativas.'))
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0',
            'BEE_TENTATIVAS_CICLO': '2', 'BEE_ESPERA_ENTRE_TENTATIVAS': '0',
            'BEE_PUBLICAR': '0', 'BEE_VERSOS_POR_CICLO': '4', 'BEE_LOTE': '4',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache), 'BEE_FUSO': 'Africa/Luanda',
            'BEE_LIVROS': '640',
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[motor]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn('Ação: **gerado**', saida.getvalue())
        dados = json.loads((self.dados / '640_Filemom.json').read_text(encoding='utf-8'))
        self.assertEqual(len(dados['in_progress']['1']), 4)

    def test_nuvem_nao_repete_erro_de_configuracao(self):
        import nuvem
        chamadas = []

        class SemPermissao(MotorFalso):
            def gerar(self, *a, **k):
                chamadas.append(1)
                raise ErroRede('gemini: HTTP 401; verifique a chave do provedor.')

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0',
            'BEE_TENTATIVAS_CICLO': '3', 'BEE_ESPERA_ENTRE_TENTATIVAS': '0',
            'BEE_PUBLICAR': '0', 'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache), 'BEE_LIVROS': '640',
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[SemPermissao()]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        self.assertEqual(codigo, 1)
        self.assertEqual(len(chamadas), 1, 'erro de configuração não deve ser repetido')
        self.assertIn('configuração', saida.getvalue())



class RecuperacaoSeguraTest(Base):
    """Regressão: uma variável vazia não pode apontar para a pasta atual."""

    def test_sem_caminho_remoto_nao_apaga_nada(self):
        import nuvem
        self.assertIsNone(nuvem._caminho_remoto(''))
        self.assertIsNone(nuvem._caminho_remoto('   '))
        self.assertIsNone(nuvem._caminho_remoto('.'))
        self.assertEqual(nuvem._caminho_remoto('/tmp/bee-remoto/livros_json'),
                         __import__('pathlib').Path('/tmp/bee-remoto/livros_json'))

    def test_nuvem_sem_remoto_preserva_o_projeto(self):
        import nuvem
        marca = self.raiz / 'nao_apagar.txt'
        marca.write_text('ok', encoding='utf-8')
        motor = MotorFalso()
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0', 'BEE_PUBLICAR': '0',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache), 'BEE_LIVROS': '640',
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[motor]), \
             contextlib.redirect_stdout(io.StringIO()):
            nuvem.main()
        self.assertTrue(marca.exists(), 'a pasta atual não pode ser apagada')
        self.assertTrue(self.dados.exists())

class GroqTest(unittest.TestCase):
    """A Groq é a reserva configurada pelo responsável: tem de falar JSON."""

    def _corpo(self, provedor, modelo='llama-3.3-70b-versatile'):
        from bee.ia import MotorIA
        motor = MotorIA(provedor, modelo, 'chave-segura', HTTPFalso({}), 4096)
        return motor._corpo('mensagem', 'chave-segura')

    def test_groq_cerebras_e_openai_forcam_json(self):
        for provedor in ('groq', 'cerebras', 'openai'):
            with self.subTest(provedor=provedor):
                _, payload, _ = self._corpo(provedor)
                self.assertEqual(payload['response_format'], {'type': 'json_object'})

    def test_groq_usa_token_do_formato_antigo(self):
        _, payload, headers = self._corpo('groq')
        self.assertIn('max_tokens', payload)
        self.assertNotIn('max_completion_tokens', payload)
        self.assertEqual(headers['Authorization'], 'Bearer chave-segura')
        self.assertNotIn('chave-segura', str(payload))

    def test_gemini_continua_com_json_nativo(self):
        _, payload, headers = self._corpo('gemini', 'gemini-3.5-flash-lite')
        self.assertEqual(payload['generationConfig']['responseMimeType'], 'application/json')
        self.assertEqual(headers['x-goog-api-key'], 'chave-segura')


class RodizioTest(unittest.TestCase):
    def test_salta_para_o_seguinte_quando_a_quota_esgota(self):
        notas = []
        primeiro = MotorFalso(falhar_em=1, erro=CotaExcedida('HTTP 429'))
        segundo = MotorFalso()
        rodizio = Rodizio([primeiro, segundo], registar=notas.append)
        versos = rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(versos[0]['verse'], 1)
        self.assertEqual(rodizio.provedor, segundo.provedor)
        self.assertIn(primeiro.provedor, rodizio.esgotados())
        self.assertTrue(any('Quota esgotada' in n for n in notas))

    def test_todos_esgotados_levanta_erro_de_rede(self):
        rodizio = Rodizio([
            MotorFalso(falhar_em=1, erro=CotaExcedida('HTTP 429')),
            MotorFalso(falhar_em=1, erro=CotaExcedida('HTTP 429')),
        ])
        with self.assertRaises(ErroRede):
            rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(len(rodizio.esgotados()), 2)


class ProvedoresTest(unittest.TestCase):
    def test_apenas_provedores_com_plano_gratuito_na_lista(self):
        gratuitos = [nome for nome, p in PROVEDORES.items() if p.pedidos_por_dia]
        self.assertIn('gemini', gratuitos)
        self.assertIn('groq', gratuitos)
        self.assertNotIn('openai', gratuitos)
        for nome in gratuitos:
            self.assertIn(nome, VERSOS_POR_PEDIDO_PADRAO)
            self.assertTrue(PROVEDORES[nome].variavel.endswith('_API_KEY'))

    def test_prompt_de_rascunho_acrescenta_regras_sem_tocar_no_original(self):
        from bee.ia import PROMPT_REVISAO, SYSTEM_PROMPT
        motor = MotorIA('gemini', 'gemini-3.5-flash-lite', 'chave-segura', HTTPFalso({}), 512)
        self.assertIn(PROMPT_REVISAO.strip().split()[0], motor._system())
        self.assertTrue(motor._system().startswith(SYSTEM_PROMPT))
        motor.aplicar_revisao = False
        self.assertEqual(motor._system(), SYSTEM_PROMPT)

    def test_varias_chaves_mascaradas_e_sem_vazamento(self):
        from bee.rede import ler_chaves, mascarar
        self.assertEqual(ler_chaves('a,b;c'), ['a', 'b', 'c'])
        self.assertEqual(ler_chaves(''), [])
        self.assertEqual(mascarar('abcdefgh1234'), '…1234')
        self.assertNotIn('abcd', mascarar('abcdefgh1234'))


class HTTPFalso:
    def __init__(self, resposta):
        self.resposta = resposta

    def obter(self, requisicao, descricao, limite=None):
        return json.dumps(self.resposta).encode()


class CLIautopilotoTest(Base):
    def _correr(self, extra):
        ambiente = {'GEMINI_API_KEY': 'chave-de-teste'}
        base = ['--dados', str(self.dados), '--saida', str(self.saida), '--pausa', '0',
                '--fuso', 'Africa/Luanda', '--livros', '640', '--cache-fontes', str(self.cache)]
        with patch.dict(os.environ, ambiente, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('autopiloto.FontesOriginais', FontesFalsas), \
             patch('bee.gerador.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[MotorFalso()]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = autopiloto.main(base + extra)
        return codigo, saida.getvalue()

    def test_uma_vez_gera_compila_e_cria_zip(self):
        codigo, texto = self._correr(['--uma-vez', '--max-versos', '40', '--lote', '10',
                                      '--zip', str(self.raiz / 'BEE.zip')])
        self.assertEqual(codigo, 0, texto)
        self.assertTrue((self.raiz / 'BEE.zip').exists())
        self.assertTrue((self.dados / '.bee' / 'estado.json').exists())

    def test_segunda_corrida_nao_duplica_trabalho_e_para(self):
        self._correr(['--uma-vez', '--max-versos', '40', '--lote', '25'])
        codigo, texto = self._correr(['--uma-vez'])
        self.assertEqual(codigo, 0)
        self.assertIn('Paragem', texto)

    def test_falha_de_rede_devolve_codigo_de_erro(self):
        motor = MotorFalso(falhar_em=1)
        ambiente = {'GEMINI_API_KEY': 'chave-de-teste'}
        base = ['--dados', str(self.dados), '--saida', str(self.saida), '--pausa', '0',
                '--fuso', 'Africa/Luanda', '--livros', '640', '--cache-fontes', str(self.cache)]
        with patch.dict(os.environ, ambiente, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('autopiloto.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[motor]), \
             contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            codigo = autopiloto.main(base + ['--uma-vez'])
        self.assertEqual(codigo, 1)
        diario = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('Ciclo 1 falhou', diario)

    def test_doctor_nao_gera_nem_compila(self):
        codigo, texto = self._correr(['--doctor'])
        self.assertEqual(codigo, 0)
        self.assertIn('Google Gemini', texto)
        self.assertFalse((self.dados / '640_Filemom.json').exists())


if __name__ == '__main__':
    unittest.main()
