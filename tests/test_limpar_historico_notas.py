"""A limpeza do histórico de correções só retira processo, nunca justificação."""
import importlib.util
from pathlib import Path
import unittest

CAMINHO = Path(__file__).resolve().parents[1] / 'scripts' / 'limpar_historico_notas.py'
spec = importlib.util.spec_from_file_location('limpar_historico_notas', CAMINHO)
lh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lh)


def _nota(texto):
    return f'<p><b>Nota de redação:</b> {texto}</p>'


def _livro(estado, texto_nota):
    return {
        'review': {'editorial_blocks': [{'chapter': 1, 'verse_from': 1,
                                         'verse_to': 1, 'status': estado}]},
        'chapters': {'1': [{'verse': 1, 'text': 'x',
                            'commentary': _nota(texto_nota)}]},
    }


class LimparHistoricoTest(unittest.TestCase):
    def test_retira_historico_e_mantem_justificacao(self):
        dados = _livro('rascunho',
                       'A versão anterior escrevia «toda iniquidade». '
                       '<i>πᾶν</i> é anártrico e distribui — cada obra, cada palavra.')
        tocadas, frases, removidas = lh.limpar(dados)
        self.assertEqual((tocadas, removidas), (1, 0))
        nota = dados['chapters']['1'][0]['commentary']
        self.assertIn('anártrico e distribui', nota)
        self.assertNotIn('versão anterior', nota)

    def test_remove_secao_que_so_tinha_historico(self):
        dados = _livro('rascunho', 'Foi corrigido para «como primícias».')
        tocadas, frases, removidas = lh.limpar(dados)
        self.assertEqual(removidas, 1)
        self.assertNotIn('Nota de redação', dados['chapters']['1'][0]['commentary'])

    def test_nota_sem_historico_nao_muda(self):
        texto = 'O possessivo não está na base fixada.'
        dados = _livro('rascunho', texto)
        antes = dados['chapters']['1'][0]['commentary']
        self.assertEqual(lh.limpar(dados), (0, 0, 0))
        self.assertEqual(dados['chapters']['1'][0]['commentary'], antes)

    def test_recusa_livro_com_bloco_aprovado(self):
        dados = _livro('aprovado editorialmente', 'A versão anterior escrevia «x».')
        with self.assertRaises(PermissionError):
            lh.limpar(dados)
        self.assertIn('versão anterior', dados['chapters']['1'][0]['commentary'])


if __name__ == '__main__':
    unittest.main()
