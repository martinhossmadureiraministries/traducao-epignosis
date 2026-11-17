import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
from unittest.mock import patch
import unittest
from zoneinfo import ZoneInfo

import autopiloto
from bee.agenda import (
    Agendador, ConfigAgenda, Diario, Estado, dentro_da_janela, livros_na_fila,
)
from bee.arquivos import carregar_json, novo_livro, salvar_livro
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

    def test_nuvem_5xx_persistente_nao_marca_falha(self):
        """Serviço em baixo com a reserva esgotada: sai limpo, o cron volta."""
        import nuvem

        class Sempre503(MotorFalso):
            def gerar(self, *a, **k):
                raise ServicoIndisponivel('gemini: HTTP 503; esgotadas 3 tentativas.')

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0',
            'BEE_TENTATIVAS_CICLO': '1', 'BEE_ESPERA_ENTRE_TENTATIVAS': '0',
            'BEE_PUBLICAR': '0', 'BEE_LIVROS': '640',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache),
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[Sempre503()]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn('próximo ciclo', saida.getvalue())
        diario = (self.dados / '.bee' / 'diario.md').read_text(encoding='utf-8')
        self.assertIn('indisponível', diario)

    def test_resumo_conta_versiculos_de_capitulos_em_curso(self):
        """Já aconteceu o resumo dizer '0 versículos' depois de guardar 6."""
        import nuvem
        motor = MotorFalso()
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0',
            'BEE_TENTATIVAS_CICLO': '1', 'BEE_PUBLICAR': '0', 'BEE_LIVROS': '640',
            'BEE_VERSOS_POR_CICLO': '6', 'BEE_LOTE': '6',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache),
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[motor]), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn('6/31102 versículos guardados', saida.getvalue())

    def test_servico_em_baixo_nao_faz_o_agendador_desistir(self):
        """6 falhas seguidas param a produção: um 5xx não pode contar para isso."""
        import nuvem

        class Sempre503(MotorFalso):
            def gerar(self, *a, **k):
                raise ServicoIndisponivel('gemini: HTTP 503; esgotadas 3 tentativas.')

        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0',
            'BEE_TENTATIVAS_CICLO': '1', 'BEE_PUBLICAR': '0', 'BEE_LIVROS': '640',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache),
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[Sempre503()]), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(nuvem.main(), 0)
        estado = json.loads((self.dados / '.bee' / 'estado.json').read_text(encoding='utf-8'))
        self.assertEqual(estado['falhas_seguidas'], 0)

    def test_fora_da_janela_o_resumo_diz_o_motivo(self):
        """Uma execução às 04:17 não pode ficar verde sem explicar que não produziu."""
        import nuvem
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0', 'BEE_PUBLICAR': '0',
            'BEE_LIVROS': '640', 'BEE_HORA_INICIO': '5', 'BEE_HORA_FIM': '23',
            'BEE_FUSO': 'Africa/Luanda',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache),
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[MotorFalso()]), \
             patch('bee.agenda._agora',
                   return_value=__import__('datetime').datetime(
                       2026, 11, 17, 3, 17, tzinfo=__import__('datetime').timezone.utc)), \
             patch('nuvem._agora_local',
                   return_value=__import__('datetime').datetime(2026, 11, 17, 4, 17)), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        # Sem fixar o relógio do agendador, este teste passava só quando corria
        # fora da janela: `bee.agenda._agora` lia a hora real.
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn('a aguardar a janela diária', saida.getvalue())
        self.assertIn('04:17', saida.getvalue())
        self.assertIn('05:00', saida.getvalue())

    def test_publicacao_recusa_perder_versiculos(self):
        """O caso real: recuperação falhou e a publicação apagou João 5:7-46."""
        import subprocess
        import nuvem
        repo = self.raiz / 'repo'
        repo.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 't@e'], check=True)
        subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 't'], check=True)
        dados = repo / 'livros_json'
        dados.mkdir()
        livro = LIVROS_POR_NUMERO[640]

        def escrever(quantidade: int) -> None:
            conteudo = {'chapters': {}, 'in_progress': {'1': [
                {'verse': n, 'text': f'T{n}.',
                 'commentary': '<p>Análise Léxica: a</p><p>Crítica Textual: b</p>'
                               '<p>Síntese Exegética: c</p>'}
                for n in range(1, quantidade + 1)]}}
            (dados / livro.nome_arquivo).write_text(json.dumps(conteudo), encoding='utf-8')

        escrever(10)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'inicial'], check=True)
        escrever(2)  # a árvore local perdeu 8 versículos

        pai = subprocess.run(['git', '-C', str(repo), 'rev-parse', 'HEAD'],
                             capture_output=True, text=True).stdout.strip()
        # Árvore que a execução tentaria publicar agora (2 versículos).
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        arvore_local = subprocess.run(['git', '-C', str(repo), 'write-tree'],
                                      capture_output=True, text=True).stdout.strip()
        with patch.dict(os.environ, {'BEE_REPO': str(repo)}, clear=False):
            self.assertEqual(
                nuvem._regressao(pai, arvore_local, ['livros_json']), 8,
                'a publicação tem de recusar perder 8 versículos já publicados',
            )

    def test_reparacao_recupera_versiculos_do_ramo(self):
        """17/11: arrancou sem o ramo de dados e 46 versículos ficaram de fora."""
        import subprocess
        import nuvem
        repo = self.raiz / 'repo2'
        repo.mkdir(parents=True)
        subprocess.run(['git', 'init', '-q', str(repo)], check=True)
        subprocess.run(['git', '-C', str(repo), 'config', 'user.email', 't@e'], check=True)
        subprocess.run(['git', '-C', str(repo), 'config', 'user.name', 't'], check=True)
        dados = self.raiz / 'locais'
        dados.mkdir()
        livro = LIVROS_POR_NUMERO[640]

        from bee.arquivos import novo_livro, salvar_livro

        def escrever(caminho: Path, quantidade: int) -> None:
            conteudo = novo_livro(livro)
            conteudo['in_progress']['1'] = [
                {'verse': n, 'text': f'T{n}.',
                 'commentary': '<p>Análise Léxica: a</p><p>Crítica Textual: b</p>'
                               '<p>Síntese Exegética: c</p>'}
                for n in range(1, quantidade + 1)]
            salvar_livro(caminho, conteudo, livro)

        no_ramo = repo / 'livros_json'
        no_ramo.mkdir()
        escrever(no_ramo / livro.nome_arquivo, 10)
        subprocess.run(['git', '-C', str(repo), 'add', '-A'], check=True)
        subprocess.run(['git', '-C', str(repo), 'commit', '-qm', 'ramo de dados'], check=True)
        subprocess.run(['git', '-C', str(repo), 'update-ref', 'refs/remotes/origin/bee-dados', 'HEAD'],
                       check=True)
        escrever(dados / livro.nome_arquivo, 3)  # o local perdeu 7

        with patch.dict(os.environ, {'BEE_REPO': str(repo), 'BEE_PUBLICAR': '0',
                                     'RUNNER_TEMP': str(self.raiz)}, clear=False):
            mensagem, recuperados = nuvem._reparar_dados(
                dados, 'bee-dados',
                type('D', (), {'escrever': staticmethod(lambda *a, **k: None)})(),
                publicar=False,
            )
        self.assertEqual(recuperados, 7, mensagem)
        self.assertIn('recuperados', mensagem)
        self.assertEqual(nuvem._progresso(dados)[1], 10)

    def test_compila_no_fim_mesmo_sem_fechar_capitulo(self):
        """João 5 tem 47 versículos: 8 ciclos não podem ficar sem módulos novos."""
        import nuvem
        from bee.arquivos import novo_livro, salvar_livro
        livro = LIVROS_POR_NUMERO[640]
        dados = novo_livro(livro)
        dados['chapters']['1'] = [
            {'verse': n, 'text': f'Texto {n}.',
             'commentary': '<p>Análise Léxica: a</p><p>Crítica Textual: b</p>'
                           '<p>Síntese Exegética: c</p>'}
            for n in range(1, 26)
        ]
        salvar_livro(self.dados / livro.nome_arquivo, dados, livro)

        class Resultado:
            acao = 'gerado'
            resumo_compilacao = None

        diario = type('D', (), {'escrever': staticmethod(lambda *a, **k: None)})()
        resultado = Resultado()
        nuvem._compilar_no_fim(resultado, self.dados, self.saida, diario)
        self.assertTrue((self.saida / 'BEE.SQLite3').exists())
        self.assertIsNotNone(resultado.resumo_compilacao)

    def test_compila_mesmo_quando_o_ciclo_termina_mal(self):
        """17/11: o ciclo 3 morreu e 9 capítulos completos não chegaram ao MyBible.

        A condição antiga (`acao != 'gerado'`) impedia a compilação quando o
        ciclo terminava como 'nada' — que é exactamente o que acontece depois
        de falhar, com versículos já gravados no disco.
        """
        import nuvem
        from bee.arquivos import novo_livro, salvar_livro
        livro = LIVROS_POR_NUMERO[640]
        dados = novo_livro(livro)
        dados['chapters']['1'] = [
            {'verse': n, 'text': f'Texto {n}.',
             'commentary': '<p>Análise Léxica: a</p><p>Crítica Textual: b</p>'
                           '<p>Síntese Exegética: c</p>'}
            for n in range(1, 26)
        ]
        salvar_livro(self.dados / livro.nome_arquivo, dados, livro)

        for acao in ('nada', 'parar'):
            for ficheiro in self.saida.glob('*.SQLite3'):
                ficheiro.unlink()

            class Resultado:
                resumo_compilacao = None

            resultado = Resultado()
            resultado.acao = acao
            diario = type('D', (), {'escrever': staticmethod(lambda *a, **k: None)})()
            resumo = nuvem._compilar_no_fim(resultado, self.dados, self.saida, diario)
            self.assertIsNotNone(resumo, f'compilação perdida com acao={acao!r}')
            self.assertTrue((self.saida / 'BEE.SQLite3').exists())

    def test_janela_desligada_produz_a_qualquer_hora(self):
        import nuvem
        with patch.dict(os.environ, {
            'GEMINI_API_KEY': 'chave-de-teste', 'BEE_PAUSA': '0', 'BEE_PUBLICAR': '0',
            'BEE_LIVROS': '640', 'BEE_HORA_INICIO': '5', 'BEE_HORA_FIM': '23',
            'BEE_JANELA': '0', 'BEE_VERSOS_POR_CICLO': '2', 'BEE_LOTE': '2',
            'BEE_FUSO': 'Africa/Luanda',
            'BEE_DADOS': str(self.dados), 'BEE_SAIDA': str(self.saida),
            'BEE_CACHE': str(self.cache),
        }, clear=True), \
             patch('autopiloto.ClienteHTTP'), \
             patch('nuvem.FontesOriginais', FontesFalsas), \
             patch('autopiloto._motores', return_value=[MotorFalso()]), \
             patch('nuvem._agora_local', return_value=__import__('datetime').datetime(2026, 11, 17, 4, 17)), \
             contextlib.redirect_stdout(io.StringIO()) as saida:
            codigo = nuvem.main()
        self.assertEqual(codigo, 0, saida.getvalue())
        self.assertIn('Ação: **gerado**', saida.getvalue())

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
        self.assertIn('chave', saida.getvalue())



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


class DescobertaDeModeloTest(unittest.TestCase):
    """Nomes fixos envelhecem: o modelo certo é o que o serviço disser que existe."""

    def test_modelos_retirados_da_groq_nao_sao_escolhidos(self):
        from bee.ia import PROVEDORES, RETIRADOS, _escolher_modelo
        groq = PROVEDORES['groq']
        self.assertNotIn(groq.modelos[0], RETIRADOS, 'o primeiro modelo não pode ser um retirado')
        disponiveis = ['openai/gpt-oss-120b', 'openai/gpt-oss-20b', 'llama-3.3-70b-versatile']
        self.assertEqual(_escolher_modelo(groq, disponiveis), 'openai/gpt-oss-120b')
        # Sem os GPT-OSS, sobra apenas um retirado: nada é escolhido.
        self.assertIsNone(_escolher_modelo(groq, ['llama-3.3-70b-versatile']))

    def test_gemini_prefere_flash_lite_e_ignora_modelos_sem_geracao(self):
        from bee.ia import PROVEDORES, _escolher_modelo, _ids_disponiveis
        config = PROVEDORES['gemini']
        resposta = {'models': [
            {'name': 'models/gemini-3.8-pro', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/gemini-3.5-flash-lite', 'supportedGenerationMethods': ['generateContent']},
            {'name': 'models/text-embedding-004', 'supportedGenerationMethods': ['embedContent']},
        ]}
        ids = _ids_disponiveis(config, resposta)
        self.assertNotIn('text-embedding-004', ids)
        self.assertEqual(_escolher_modelo(config, ids), 'gemini-3.5-flash-lite')

    def test_a_chave_do_gemini_nao_vai_na_url_da_listagem(self):
        from bee.ia import PROVEDORES, _pedido_listagem
        pedido = _pedido_listagem(PROVEDORES['gemini'], 'segredo-123')
        self.assertNotIn('segredo-123', pedido.full_url, 'chave nunca na URL (fica nos registos)')
        self.assertEqual(pedido.get_header('X-goog-api-key'), 'segredo-123')

    def test_sem_lista_usa_a_reserva_do_codigo(self):
        from bee.ia import resolver_modelos
        modelos = resolver_modelos('groq', ['chave'], HTTPFalso({}))
        self.assertEqual(modelos[0], 'openai/gpt-oss-120b')
        self.assertGreater(len(modelos), 1, 'deve haver suplentes para 404')

    def test_lista_real_e_usada_quando_existe(self):
        from bee.ia import resolver_modelos
        class ListaOK:
            def obter(self, requisicao, descricao, limite=None, log=None, provedor=None):
                return json.dumps({'data': [
                    {'id': 'llama-3.3-70b-versatile'},
                    {'id': 'openai/gpt-oss-20b'},
                    {'id': 'openai/gpt-oss-120b'},
                ]}).encode()
        modelos = resolver_modelos('groq', ['chave'], ListaOK())
        self.assertEqual(modelos, ['openai/gpt-oss-120b'])

    def test_gpt_oss_da_groq_pede_esforco_de_raciocinio_baixo(self):
        """Os GPT-OSS gastam max_tokens a pensar; sem isto os lotes truncam."""
        from bee.ia import MotorIA
        corpos = []

        class Guarda:
            def obter(self, requisicao, descricao, limite=None, log=None, provedor=None):
                corpos.append(json.loads(requisicao.data))
                return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps({'verses': [{
                        'verse': 1, 'text': 'Texto.',
                        'commentary': '<p>Análise Léxica; Crítica Textual; Síntese Exegética.</p>'}]})}}]}).encode()

        motor = MotorIA('groq', ['openai/gpt-oss-120b'], 'chave', Guarda(), 4096)
        motor.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(corpos[0]['reasoning_effort'], 'low')
        self.assertEqual(corpos[0]['model'], 'openai/gpt-oss-120b')

    def test_404_troca_de_modelo_e_continua(self):
        from bee.ia import MotorIA
        from bee.rede import ErroRede

        pedidos = []
        class HTTP404:
            def obter(self, requisicao, descricao, limite=None, log=None, provedor=None):
                pedidos.append(json.loads(requisicao.data)['model'])
                if len(pedidos) == 1:
                    raise ErroRede('groq: HTTP 404; verifique o endereço ou o nome do modelo.')
                return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps({'verses': [{
                        'verse': 1, 'text': 'Texto.',
                        'commentary': '<p>Análise Léxica: não verificada em léxico.</p>'
                                      '<p>Crítica Textual: sem variante verificada.</p>'
                                      '<p>Síntese Exegética: teste.</p>'}]})}}]}).encode()

        motor = MotorIA('groq', ['llama-3.3-70b-versatile', 'openai/gpt-oss-120b'],
                        'chave', HTTP404(), 4096)
        avisos = []
        motor.log = avisos.append
        versos = motor.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(versos[0]['verse'], 1)
        self.assertEqual(pedidos, ['llama-3.3-70b-versatile', 'openai/gpt-oss-120b'])
        self.assertEqual(motor.modelo, 'openai/gpt-oss-120b')
        self.assertTrue(any('404' in a for a in avisos))


class MotorDeLotes:
    """Motor mínimo com lotes registados (independente do MotorFalso local)."""

    provedor = 'gemini'
    modelo = 'modelo-teste'

    def __init__(self, tamanho_max=None, falhar=False):
        self.calls = []
        self.tamanho_max = tamanho_max
        self.falhar = falhar

    def gerar(self, livro, capitulo, fontes, estilo=None):
        from bee.ia import RespostaInvalida, RespostaTruncada
        nums = [f['verse'] for f in fontes]
        self.calls.append(nums)
        if self.falhar:
            raise RespostaInvalida('JSON incompleto')
        if self.tamanho_max is not None and len(nums) > self.tamanho_max:
            raise RespostaTruncada('limite')
        return [
            {'verse': n, 'text': f'Texto {n}.',
             'commentary': ('<p><b>Análise Léxica:</b> não verificada.</p>'
                            '<p><b>Crítica Textual:</b> sem variante.</p>'
                            '<p><b>Síntese Exegética:</b> rascunho.</p>')}
            for n in nums
        ]


class MarcacaoDoModeloTest(unittest.TestCase):
    """O que aconteceu em produção: `<div>` fazia o lote ser recusado e dividido."""

    def test_div_envolvente_e_aceite_e_convertido(self):
        from bee.arquivos import sanear_html as sanitizar_para_guardar, validar_html
        texto = ('<div><p><b>Análise Léxica</b><br>ἦν (ēn - era).</p>'
                 '<p><b>Crítica Textual</b><br>Sem variante.</p>'
                 '<p><b>Síntese Exegética</b><br>Rascunho.</p></div>')
        validar_html(texto, 'commentary', True)          # antes: erro, lote dividido
        limpo = sanitizar_para_guardar(texto, True)
        self.assertNotIn('<div>', limpo)
        self.assertEqual(limpo.count('<p>'), limpo.count('</p>'))
        self.assertIn('Análise Léxica', limpo)

    def test_script_e_conteudo_de_script_continuam_recusados(self):
        from bee.arquivos import DadosInvalidos, validar_html
        for perigoso in ('<script>alert(1)</script>', '<iframe src="x"></iframe>',
                         '<p onclick="x">oi</p>', '<p>a</p></p>', '<!-- nota --><p>a</p>'):
            with self.assertRaises(DadosInvalidos, msg=perigoso):
                validar_html(perigoso, 'commentary', True)

    def test_tag_sem_significado_e_atributo_sao_limpos_na_limpeza(self):
        from bee.arquivos import sanear_html as sanitizar_para_guardar
        self.assertEqual(sanitizar_para_guardar('a <b onclick="x">b</b>', True), 'a b')
        self.assertEqual(sanitizar_para_guardar('<p>a</p></p><b>solto', True),
                         '<p>a</p><b>solto</b>')

    def test_texto_biblico_so_pode_ter_italico(self):
        from bee.arquivos import DadosInvalidos, validar_html
        validar_html('palavra <i>acrescentada</i>', 'text')
        with self.assertRaises(DadosInvalidos):
            validar_html('palavra <b>negrito</b>', 'text')

    def test_resposta_com_div_e_guardada_sem_repetir_o_lote(self):
        """Antes: 3 tentativas, lote dividido até 1 versículo e produção parada."""
        from bee.ia import MotorIA
        from bee.arquivos import ler_livro
        pedidos = []

        class DivHTTP:
            def obter(self, requisicao, descricao, limite=None, log=None, provedor=None):
                corpo = json.loads(requisicao.data)
                fontes = json.loads(corpo['messages'][1]['content'].rsplit('\n\n', 1)[-1])
                pedidos.append(len(fontes))
                versos = [{'verse': f['verse'], 'text': 'Texto.',
                           'commentary': '<div><p>Análise Léxica: x</p>'
                                         '<p>Crítica Textual: y</p>'
                                         '<p>Síntese Exegética: z</p></div>'} for f in fontes]
                return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
                    'content': json.dumps({'verses': versos}, ensure_ascii=False)}}]},
                    ensure_ascii=False).encode()

        motor = MotorIA('groq', ['openai/gpt-oss-120b'], 'chave', DivHTTP(), 4096)
        versos = motor.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': n} for n in (1, 2, 3)])
        self.assertEqual(len(versos), 3)
        self.assertNotIn('<div>', versos[0]['commentary'])


class RetomadaDoLoteTest(unittest.TestCase):
    """A produção parava em João 5:7 e insistia nele em vez de avançar."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dados = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_lote_repetido_apos_falhas_vai_direto_a_1_versiculo(self):
        from bee.gerador import ConfigGeracao, gerar_fatia
        motor = MotorDeLotes(tamanho_max=1)
        config = ConfigGeracao(versos_por_pedido=8, max_versos=4,
                               falhas_anteriores=2, lote_retomar=1)
        gerar_fatia([LIVROS_POR_NUMERO[640]], self.dados, FontesFalsas(), motor, config)
        self.assertEqual(motor.calls[0], [1], 'devia pedir só o versículo em falta')

    def test_falhas_do_mesmo_lote_ficam_no_progresso(self):
        from bee.gerador import ConfigGeracao, gerar_fatia
        motor = MotorDeLotes(falhar=True)
        with self.assertRaises(Exception):
            gerar_fatia([LIVROS_POR_NUMERO[640]], self.dados, FontesFalsas(), motor,
                        ConfigGeracao(versos_por_pedido=1, tentativas_conteudo=2))

    def test_agendador_guarda_o_lote_em_falta_entre_ciclos(self):
        from bee.agenda import Agendador, ConfigAgenda, Estado
        from bee.gerador import Progresso
        agendador = Agendador.__new__(Agendador)
        agendador.estado = Estado()
        agendador.diario = type('D', (), {'escrever': staticmethod(lambda *a, **k: None)})()
        progresso = Progresso(livro=LIVROS_POR_NUMERO[500], capitulo=5, lote_inicio=7,
                              falhas_lote=1)
        agendador._registar_lote(progresso)
        self.assertEqual(
            (agendador.estado.lote_livro, agendador.estado.lote_capitulo,
             agendador.estado.lote_versiculo),
            (500, 5, 7),
        )
        self.assertEqual(agendador.estado.lote_falhas, 1)
        agendador._registar_lote(Progresso(livro=LIVROS_POR_NUMERO[500], capitulo=5, versos=3))
        self.assertIsNone(agendador.estado.lote_versiculo)


class RodizioTest(unittest.TestCase):
    def test_salta_para_o_seguinte_quando_a_quota_esgota(self):
        """Um 429 é limite por minuto: passa ao seguinte sem o dar por perdido."""
        notas = []
        primeiro = MotorFalso(falhar_em=1, erro=CotaExcedida('HTTP 429'))
        segundo = MotorFalso()
        rodizio = Rodizio([primeiro, segundo], registar=notas.append)
        versos = rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(versos[0]['verse'], 1)
        self.assertEqual(rodizio.provedor, segundo.provedor)
        self.assertEqual(rodizio.esgotados(), [], 'um 429 isolado não é quota do dia')
        self.assertTrue(any('Limite por minuto' in n for n in notas))

    def test_429_repetido_marca_o_provedor_como_esgotado(self):
        notas = []

        class Sempre429(MotorFalso):
            def gerar(self, *a, **k):
                raise CotaExcedida('HTTP 429; esgotadas 3 tentativas.')

        rodizio = Rodizio([Sempre429(), Sempre429()], registar=notas.append)
        for _ in range(Rodizio.QUOTA_PARA_DESISTIR):
            with self.assertRaises(ErroRede):
                rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(sorted(rodizio.esgotados()), ['gemini', 'gemini'])
        self.assertTrue(any('fica de fora' in n for n in notas))

    def test_todos_esgotados_levanta_erro_de_rede(self):
        class Sempre429(MotorFalso):
            def gerar(self, *a, **k):
                raise CotaExcedida('HTTP 429; esgotadas 3 tentativas.')

        rodizio = Rodizio([Sempre429(), Sempre429()])
        with self.assertRaises(ErroRede):
            rodizio.gerar(LIVROS_POR_NUMERO[640], 1, [{'verse': 1}])
        self.assertEqual(rodizio.esgotados(), [])


class ProvedoresTest(unittest.TestCase):
    def test_apenas_provedores_com_plano_gratuito_na_lista(self):
        gratuitos = [nome for nome, p in PROVEDORES.items() if p.pedidos_por_dia]
        self.assertIn('gemini', gratuitos)
        self.assertIn('groq', gratuitos)
        self.assertIn('ovh', gratuitos, 'a OVHcloud tem nível anónimo sem chave')
        self.assertNotIn('openai', gratuitos)
        for nome in gratuitos:
            self.assertIn(nome, VERSOS_POR_PEDIDO_PADRAO)
            self.assertTrue(PROVEDORES[nome].variavel.endswith('_API_KEY'))
        # Só um serviço pode dispensar chave; é o que garante que a produção
        # arranca numa instalação nova, sem contas nenhumas.
        sem_chave = [n for n, p in PROVEDORES.items() if p.sem_chave]
        self.assertEqual(sem_chave, ['ovh'])

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

    def obter(self, requisicao, descricao, limite=None, provedor=None):
        return json.dumps(self.resposta).encode()


class CapitulosExportadosTest(Base):
    def _livro(self, capitulo, versos, completo=True):
        livro = LIVROS_POR_NUMERO[230]
        caminho = self.dados / '230.json'
        if caminho.exists():
            dados = carregar_json(caminho.read_text(encoding='utf-8'))
        else:
            dados = novo_livro(livro)
        colecao = 'chapters' if completo else 'in_progress'
        dados.setdefault(colecao, {})[str(capitulo)] = versos
        if completo:
            dados.get('in_progress', {}).pop(str(capitulo), None)
        salvar_livro(caminho, dados, livro)
        return livro

    def _versos(self, numeros):
        return [
            {'verse': n, 'text': f'Texto {n}.',
             'commentary': '<p><b>Análise Léxica:</b> teste.</p>'}
            for n in numeros
        ]

    def test_capitulo_produzido_vira_html_legivel(self):
        from nuvem import exportar_capitulos
        livro = self._livro(23, self._versos([1, 2, 3, 4, 5, 6]))
        diario = Diario(self.dados / '.bee' / 'diario.md')
        destino = self.raiz / 'entregas' / 'capitulos'
        exportados, novos = exportar_capitulos(self.dados, destino, {}, diario)
        self.assertEqual(exportados, ['Salmos-023.html'])
        self.assertEqual(novos, 1)
        html = (destino / 'Salmos-023.html').read_text(encoding='utf-8')
        self.assertIn(f'<h1>{livro.nome} 23</h1>', html)
        self.assertIn('Texto 2.', html)
        self.assertIn('Análise Léxica', html)
        self.assertIn('NÃO revisto', html)
        self.assertNotIn('em curso', html)
        self.assertIn('<details><summary>Comentário', html)
        self.assertIn('prefers-color-scheme:dark', html)

    def test_capitulo_em_curso_e_exportado_com_aviso(self):
        from nuvem import _mapa_capitulos, exportar_capitulos
        self._livro(23, self._versos([1, 2]), completo=False)
        antes = _mapa_capitulos(self.dados)
        self.assertEqual(antes, {(230, 23): 2})
        self._livro(23, self._versos([1, 2, 3]), completo=False)
        diario = Diario(self.dados / '.bee' / 'diario.md')
        destino = self.raiz / 'entregas' / 'capitulos'
        exportados, novos = exportar_capitulos(self.dados, destino, antes, diario)
        self.assertEqual(exportados, ['Salmos-023.html'])
        self.assertEqual(novos, 1)
        html = (destino / 'Salmos-023.html').read_text(encoding='utf-8')
        self.assertIn('em curso: 3 de 6 versículos', html)

    def test_exporta_todos_e_conta_so_os_mudados(self):
        from nuvem import exportar_capitulos
        self._livro(23, self._versos([1, 2, 3, 4, 5, 6]))
        diario = Diario(self.dados / '.bee' / 'diario.md')
        destino = self.raiz / 'entregas' / 'capitulos'
        antes = {(230, 23): 6, (230, 24): 0}
        self._livro(24, self._versos([1, 2]), completo=False)
        exportados, novos = exportar_capitulos(self.dados, destino, antes, diario)
        self.assertEqual(sorted(exportados), ['Salmos-023.html', 'Salmos-024.html'])
        self.assertEqual(novos, 1)


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


class ControloDeTempoEOrcamentoTest(Base):
    """Regressões da execução #12, que ficou 50 min presa e perdeu trabalho."""

    def test_prazo_do_ciclo_para_e_preserva(self):
        agendador, _ = self.agendador(max_versos=1000, max_tempo_ciclo=0.0001)
        resultado = agendador.ciclo(livros_na_fila([640]))
        # Pode gravar um lote antes de o relógio passar; o que não pode é
        # continuar indefinidamente. O capítulo não fica completo.
        self.assertIn(resultado.acao, ('gerado', 'nada'))
        self.assertTrue(resultado.progresso.tempo_esgotado)
        self.assertLessEqual(resultado.progresso.versos, 8)
        caminho = self.dados / '640_Filemom.json'
        if caminho.exists():
            dados = json.loads(caminho.read_text(encoding='utf-8'))
            self.assertNotIn('1', dados.get('chapters', {}))
            self.assertLessEqual(len(dados.get('in_progress', {}).get('1', [])), 8)

    def test_gemini_sem_tecto_proprio_nao_para_o_dia(self):
        """Antes, all([]) era True e o dia parava com detalhe vazio."""
        agendador, _ = self.agendador(
            max_versos=5, pedidos_por_dia=100,
            tectos_por_provedor={'groq': 66},
        )
        self.assertEqual(agendador.ciclo(livros_na_fila([640])).acao, 'gerado')
        segundo = agendador.ciclo(livros_na_fila([640]))
        self.assertNotEqual(segundo.acao, 'parar', segundo.detalhe)

    def test_relatorio_existe_mesmo_sem_modulos(self):
        import nuvem
        destino = self.raiz / 'entregas' / 'auto'
        caminho = nuvem._escrever_relatorio(
            destino, self.dados, [], None, 'não configurado', 'bee-dados', [],
        )
        self.assertTrue(caminho.exists())
        texto = caminho.read_text(encoding='utf-8')
        self.assertIn('Provedores ativos: (nenhum)', texto)
        self.assertIn('Capítulos completos: 0/1189', texto)


class DadosNoMainTest(unittest.TestCase):
    """A Etapa 2 tirou os dados do ramo `bee-dados`."""

    def test_nuvem_usa_main_como_ramo_de_dados(self):
        import nuvem
        self.assertEqual(nuvem.RAMO_DADOS, 'main')

    def test_verificador_aceita_os_dados_do_main(self):
        raiz = Path(__file__).resolve().parents[1]
        resultado = subprocess.run(
            [sys.executable, str(raiz / 'scripts/verificar_dados.py'),
             '--dados', str(raiz / 'livros_json'), '--minimo', '18'],
            capture_output=True, text=True,
        )
        self.assertEqual(resultado.returncode, 0, resultado.stderr)
        self.assertIn('18 capítulos completos', resultado.stdout)


if __name__ == '__main__':
    unittest.main()
