import contextlib
import io
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

import gerar_bee
from test_workflow import FontesFalsas


class SimularHTTP:
    def __init__(self, *args, **kwargs):
        self.requests = []

    def obter(self, requisicao, descricao, limite=None, log=None):
        if requisicao.data is None:  # listagem de modelos (GET)
            return json.dumps({'data': []}).encode()
        self.requests.append(requisicao)
        payload = json.loads(requisicao.data)
        mensagem = payload['messages'][1]['content']
        fontes = json.loads(mensagem.rsplit('\n\n', 1)[-1])
        versiculos = [
            {'verse': f['verse'], 'text': f"Tradução {f['verse']}",
             'commentary': '<p>Análise Léxica; Crítica Textual; Síntese Exegética.</p>'}
            for f in fontes
        ]
        return json.dumps({'choices': [{'finish_reason': 'stop', 'message': {
            'content': json.dumps({'verses': versiculos}, ensure_ascii=False)
        }}]}, ensure_ascii=False).encode()


class CLITest(unittest.TestCase):
    def test_fluxo_completo_e_recompilacao_offline_sem_chave(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(io.StringIO()) as saida, \
             contextlib.redirect_stderr(io.StringIO()) as erros:
            raiz = Path(tmp)
            dados, modulos = raiz / 'json', raiz / 'modulos'
            argumentos = ['--livro', '640', '--provedor', 'openai', '--dados', str(dados),
                          '--saida', str(modulos), '--pausa', '0']
            fake_http = SimularHTTP()
            with patch.dict(os.environ, {'API_KEY':'nao-colocar-nos-ficheiros'}, clear=True), \
                 patch('gerar_bee.ClienteHTTP', return_value=fake_http), \
                 patch('gerar_bee.FontesOriginais', return_value=FontesFalsas()):
                self.assertEqual(gerar_bee.main(argumentos), 0)
            self.assertEqual(len(fake_http.requests), 4)
            caminho = dados / '640_Filemom.json'
            conteudo = caminho.read_text(encoding='utf-8')
            self.assertNotIn('nao-colocar-nos-ficheiros', conteudo)
            dados_livro = json.loads(conteudo)
            self.assertEqual(len(dados_livro['chapters']['1']), 25)
            self.assertIn('sblgnt_commit', dados_livro['sources'])
            # Uma edição manual persiste: a segunda execução não precisa da chave
            # e não faz nenhuma chamada, mas recompila o par de módulos.
            dados_livro['chapters']['1'][0]['text'] = 'Texto manual revisto.'
            caminho.write_text(json.dumps(dados_livro, ensure_ascii=False, indent=2), encoding='utf-8')
            with patch.dict(os.environ, {}, clear=True), patch('gerar_bee.FontesOriginais') as fonte:
                # FontesOriginais é construído, mas não deve procurar fontes quando tudo está completo.
                fonte.return_value.capitulo.side_effect = AssertionError('não deve descarregar fonte')
                self.assertEqual(gerar_bee.main(argumentos), 0)
                fonte.return_value.capitulo.assert_not_called()
                self.assertEqual(gerar_bee.main(['--compilar', '--dados', str(dados), '--saida', str(modulos)]), 0)
            with sqlite3.connect(modulos / 'BEE.SQLite3') as conn:
                self.assertEqual(conn.execute('SELECT text FROM verses WHERE book_number=640 AND chapter=1 AND verse=1').fetchone()[0], 'Texto manual revisto.')
            self.assertIn('PARCIAL', saida.getvalue())
            self.assertEqual(erros.getvalue(), '')

    def test_sem_chave_falha_antes_de_descarregar(self):
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stderr(io.StringIO()) as erros, \
             patch.dict(os.environ, {}, clear=True), patch('gerar_bee.FontesOriginais') as fonte:
            self.assertEqual(gerar_bee.main(['--livro','500','--dados', tmp]), 1)
            fonte.return_value.capitulo.assert_not_called()
            self.assertIn('GEMINI_API_KEY', erros.getvalue())
            self.assertFalse((Path(tmp) / '500_Joao.json').exists())

    def test_invalid_argumentos(self):
        with contextlib.redirect_stderr(io.StringIO()):
            for args in (['--livro', '999'], ['--livro','500','--pausa','nan'],
                         ['--compilar','--sem-compilar'], ['--todos','--max-tokens','10']):
                with self.assertRaises(SystemExit):
                    gerar_bee.argumentos(args)


if __name__ == '__main__':
    unittest.main()
