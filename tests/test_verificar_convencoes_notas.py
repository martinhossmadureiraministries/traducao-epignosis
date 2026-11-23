import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import verificar_convencoes_notas as vc  # noqa: E402


def p(texto):
    return f"<p>{texto}</p>"


class ConvencoesNotas(unittest.TestCase):
    def test_nota_limpa_passa(self):
        html = p("<i>λόγος</i> (logos), «palavra».") + p(
            "<b>Crítica Textual:</b> Aparato de edições SBLGNT, 1:1: a base lê «<i>ὁ</i>», "
            "com WH; a NIV omite a palavra, por escolha de tradução.")
        self.assertEqual(vc.verificar_nota(html), ([], []))

    def test_ct_repetida_e_colada_sao_falhas(self):
        html = "<p>texto <b>Crítica Textual:</b> um</p><p><b>Crítica Textual:</b> dois</p>"
        falhas, _ = vc.verificar_nota(html)
        self.assertIn("Crítica Textual repetida", falhas)
        self.assertIn("Crítica Textual colada ao parágrafo principal", falhas)

    def test_sinal_de_aparato_e_lêm_sao_falhas(self):
        falhas, _ = vc.verificar_nota(p("Os discípulos lêm ⸀ὁ texto."))
        self.assertIn("sinal de aparato na nota", falhas)
        self.assertIn("«lêm» (usar «leem»)", falhas)

    def test_niv_como_testemunha_e_aviso(self):
        html = p("<b>Crítica Textual:</b> Aparato de edições SBLGNT, 2:2: a base lê «a», com WH e NIV.")
        _, avisos = vc.verificar_nota(html)
        self.assertTrue(any("NIV" in a for a in avisos))

    def test_a_base_maiuscula_so_depois_dos_dois_pontos(self):
        html = p("<b>Crítica Textual:</b> Aparato de edições SBLGNT, 3:3: a base lê «a». A base lê «b».")
        _, avisos = vc.verificar_nota(html)
        self.assertEqual(avisos, [])
        html = p("<b>Crítica Textual:</b> Aparato de edições SBLGNT, 3:3: A base lê «a».")
        _, avisos = vc.verificar_nota(html)
        self.assertTrue(any("maiúscula" in a for a in avisos))


if __name__ == "__main__":
    unittest.main()
