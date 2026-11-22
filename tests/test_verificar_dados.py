"""O verificador de dados relata o que falta, sem esconder o que existe."""
import importlib.util
import json
import tempfile
from pathlib import Path
import unittest

CAMINHO = Path(__file__).resolve().parents[1] / 'scripts' / 'verificar_dados.py'
spec = importlib.util.spec_from_file_location('verificar_dados', CAMINHO)
vd = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vd)


def _livro(versiculos):
    return {'chapters': {'4': [{'verse': n, 'text': texto, 'commentary': '<p>x</p>'}
                               for n, texto in versiculos]}}


class PendentesTest(unittest.TestCase):
    def _pasta(self, conteudo):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        Path(tmp.name, '500_Joao.json').write_text(
            json.dumps(conteudo), encoding='utf-8')
        return Path(tmp.name)

    def test_marcadores_pendentes_sao_relatados_em_intervalos(self):
        # Um capítulo com marcadores conta como fechado para não se perder o que
        # já existe, mas o relatório tem de dizer o que ainda não é texto.
        pendente = '[Versículo pendente: tradução ainda não produzida.]'
        pasta = self._pasta(_livro([
            (28, 'A mulher deixou o cântaro.'),
            (29, pendente), (30, pendente), (31, pendente),
            (32, 'Muitos creram.'),
            (33, pendente),
        ]))
        self.assertEqual(vd.pendentes(pasta), [('500_Joao.json', '4', '29-31, 33')])

    def test_livro_sem_marcadores_nao_aparece(self):
        pasta = self._pasta(_livro([(1, 'Graça e paz a vocês.')]))
        self.assertEqual(vd.pendentes(pasta), [])

    def test_marcadores_nao_contam_como_corrupcao(self):
        # O compilador é quem impede uma edição final com pendentes; o
        # verificador avisa mas não chumba, para não parar a produção em curso.
        pendente = '[Versículo pendente: tradução ainda não produzida.]'
        pasta = self._pasta(_livro([(1, pendente)]))
        self.assertEqual(vd.main(['--dados', str(pasta)]), 0)


    def test_pendente_em_bloco_aprovado_chumba(self):
        # Aprovar um intervalo com versículos por traduzir é dar a aprovação
        # sobre texto que não existe: isto tem de falhar, não só ser relatado.
        pendente = '[Versículo pendente: tradução ainda não produzida.]'
        conteudo = _livro([(28, 'A mulher deixou o cântaro.'), (29, pendente)])
        conteudo['review'] = {'editorial_blocks': [
            {'chapter': 4, 'verse_from': 28, 'verse_to': 29,
             'status': 'aprovado editorialmente'}]}
        pasta = self._pasta(conteudo)
        self.assertEqual(len(vd.pendentes_em_aprovados(pasta)), 1)

    def test_pendente_em_rascunho_nao_chumba(self):
        pendente = '[Versículo pendente: tradução ainda não produzida.]'
        conteudo = _livro([(28, 'A mulher deixou o cântaro.'), (29, pendente)])
        conteudo['review'] = {'editorial_blocks': [
            {'chapter': 4, 'verse_from': 28, 'verse_to': 29, 'status': 'rascunho'}]}
        pasta = self._pasta(conteudo)
        # Só a regra de bloco aprovado é testada aqui; a sequência de versículos
        # da fixture não começa em 1 e não é o objeto deste teste.
        self.assertEqual(vd.pendentes_em_aprovados(pasta), [])


class IntervalosTest(unittest.TestCase):
    def test_comprime_sequencias(self):
        self.assertEqual(vd._intervalos([2, 3, 4, 7, 9, 10]), '2-4, 7, 9-10')
        self.assertEqual(vd._intervalos([5]), '5')
        self.assertEqual(vd._intervalos([]), '')


if __name__ == '__main__':
    unittest.main()
