"""Alerta ortográfico: gralhas a 1–2 letras de uma palavra real, sem ruído."""
import importlib.util
from pathlib import Path
import unittest

CAMINHO = (Path(__file__).resolve().parents[1]
           / 'scripts' / 'verificar_ortografia.py')
spec = importlib.util.spec_from_file_location('verificar_ortografia', CAMINHO)
vo = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vo)


class CorretorFalso:
    """Conhece umas palavras e corrige outras, como o dicionário real."""

    CONHECIDAS = {'vendem', 'connosco', 'palavra', 'samaritano', 'ajudar'}
    CORRECOES = {'vendetem': 'vendem', 'samaritana': 'samaritano'}

    def __contains__(self, palavra):
        return palavra in self.CONHECIDAS

    def correction(self, palavra):
        return self.CORRECOES.get(palavra)


class PalavrasDoTextoTest(unittest.TestCase):
    def test_ignora_italico_parenteses_e_nomes(self):
        texto = ('Os que vendem <i>λόγος</i> (palavra grega) em Sicar '
                 'e na Galileia connosco.')
        palavras = vo.palavras_do_texto(texto)
        self.assertIn('vendem', palavras)
        self.assertIn('connosco', palavras)
        self.assertNotIn('sicar', palavras)
        self.assertNotIn('grega', palavras)  # dentro de parênteses


class SuspeitasTest(unittest.TestCase):
    def test_gralha_perto_de_palavra_real_e_sinalizada(self):
        achadas = vo.suspeitas(
            'os que vendetem connosco', CorretorFalso(), {'connosco'})
        self.assertEqual(len(achadas), 1)
        self.assertIn('vendetem', achadas[0])

    def test_lista_da_casa_e_genero_nao_sao_ruido(self):
        # «connosco» está na lista da casa; «samaritana» só difere do
        # masculino do dicionário pela concordância.
        achadas = vo.suspeitas(
            'a mulher samaritana connosco', CorretorFalso(), {'connosco'})
        self.assertEqual(achadas, [])

    def test_formas_com_clitico_nao_explodem(self):
        # «ajudá-los»: verifica-se o radical; sem correção plausível,
        # não há alerta.
        achadas = vo.suspeitas('foi ajudá-los ontem', CorretorFalso(), set())
        self.assertEqual(achadas, [])


if __name__ == '__main__':
    unittest.main()
