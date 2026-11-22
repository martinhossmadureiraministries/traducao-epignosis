"""Regressões do verificador de notas contra a colação (Etapa 2 do plano).

Três defeitos corrigidos:
* o marcador «[[ ]]» é legítimo no texto do versículo e não se aplica a ele;
* a CT pode citar a edição por extenso («Tregelles») e conta como citação;
* a verificação ortográfica sem a dependência falha, não sai com 0.
"""
import importlib.util
from pathlib import Path
import unittest

RAIZ = Path(__file__).resolve().parents[1]


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / 'scripts' / f'{nome}.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


vnc = _carregar('verificar_notas_colacao')
vo = _carregar('verificar_ortografia')

SECCOES_OK = ('<p><b>Análise Léxica:</b> a.</p>'
              '<p><b>Crítica Textual:</b> {ct}</p>'
              '<p><b>Síntese Exegética:</b> b.</p>')


def _dados(texto, ct):
    return {'chapters': {'1': [{'verse': 8, 'text': texto,
                                'commentary': SECCOES_OK.format(ct=ct)}]}}


def _colacao(entradas):
    base = {'sblgnt_norm': ['a'], 'scrivener_norm': ['b'],
            'aparato_sblgnt': entradas}
    return {'versiculos': {'1:8': {'base': base}}}


class MarcadorDeTextoTest(unittest.TestCase):
    def test_colchetes_duplos_no_texto_nao_sao_problema(self):
        # Leitura assinalada no texto (nível de colação), não resíduo.
        dados = _dados('nossa [[irmã]] querida', 'Treg e WH registam variante.')
        colacao = _colacao(['φλογὶ Treg ] πυρὶ WH NA28'])
        problemas = vnc.verificar(dados, colacao)
        self.assertFalse([p for p in problemas if '[[' in p or 'texto do versículo' in p],
                         problemas)

    def test_colchetes_duplos_soltos_na_nota_continuam_a_ser_problema(self):
        dados = _dados('texto simples', 'Treg e WH [[ficou]] aqui.')
        colacao = _colacao(['φλογὶ Treg ] πυρὶ WH'])
        problemas = vnc.verificar(dados, colacao)
        self.assertTrue(any('[[ ]]' in p for p in problemas), problemas)

    def test_marcador_de_quarentena_no_texto_continua_a_ser_problema(self):
        dados = _dados('[Versículo pendente: tradução ainda não produzida.]',
                       'Treg e WH registam variante.')
        colacao = _colacao(['φλογὶ Treg ] πυρὶ WH'])
        problemas = vnc.verificar(dados, colacao)
        self.assertTrue(any('texto do versículo' in p for p in problemas), problemas)


class NomeCompletoTest(unittest.TestCase):
    def test_tregelles_por_extenso_conta_como_treg(self):
        dados = _dados('texto', 'Tregelles lê diferente; WH também.')
        colacao = _colacao(['φλογὶ Treg ] πυρὶ WH'])
        problemas = vnc.verificar(dados, colacao)
        self.assertFalse([p for p in problemas if "não cita ['Treg']" in p], problemas)

    def test_sigla_em_falta_continua_a_ser_apanhada(self):
        dados = _dados('texto', 'Só WH regista isto.')
        colacao = _colacao(['φλογὶ Treg ] πυρὶ WH'])
        problemas = vnc.verificar(dados, colacao)
        self.assertTrue(any("não cita ['Treg']" in p for p in problemas), problemas)


class DependenciaOrtograficaTest(unittest.TestCase):
    def test_sem_pyspellchecker_o_relatorio_falha(self):
        original = vo._carregar_corretor
        vo._carregar_corretor = lambda: None
        self.addCleanup(setattr, vo, '_carregar_corretor', original)
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(vo.relatorio(Path(tmp), False), 2)


class RegressoesDaEtapa5(unittest.TestCase):
    """Duas regras que davam falsos avisos em 2 Tessalonicenses (M1, Etapa 5)."""

    def _verificar(self, comentario, colacao):
        dados = {'chapters': {'1': [{'verse': 8, 'text': 'x',
                                     'commentary': comentario}]}}
        return vnc.verificar(dados, colacao)

    def test_variante_de_testemunha_registada_nao_e_falta(self):
        # O aparato é só de edições: uma variante de manuscrito consta das
        # divergências da colação e a CT pode descrevê-la.
        base = {'sblgnt_norm': ['a'], 'scrivener_norm': ['a'], 'aparato_sblgnt': [],
                'aviso': ''}
        colacao = {'versiculos': {'1:8': {
            'base': base,
            'divergencias': [{'testemunha': '02', 'estado': 'divergente'}]}}}
        comentario = SECCOES_OK.format(ct='O Alexandrinus (02) omite o artigo.')
        self.assertEqual(self._verificar(comentario, colacao), [])

    def test_sem_divergencia_nem_aparato_a_falta_continua(self):
        base = {'sblgnt_norm': ['a'], 'scrivener_norm': ['a'], 'aparato_sblgnt': [],
                'aviso': ''}
        colacao = {'versiculos': {'1:8': {'base': base, 'divergencias': []}}}
        comentario = SECCOES_OK.format(ct='O Alexandrinus (02) omite o artigo.')
        problemas = self._verificar(comentario, colacao)
        self.assertTrue(any('sem entrada no aparato' in p for p in problemas))

    def test_familia_nao_e_historia_de_redacao(self):
        # «família» termina em «lia»: a regex de resíduo exige fronteira de palavra.
        base = {'sblgnt_norm': ['a'], 'scrivener_norm': ['a'], 'aparato_sblgnt': [],
                'aviso': ''}
        colacao = {'versiculos': {'1:8': {'base': base, 'divergencias': []}}}
        comentario = ('<p><b>Nota de redação:</b> A família ἀτακτ- fica com o mesmo verbo.</p>'
                      + SECCOES_OK.format(ct='Sem variante.'))
        problemas = self._verificar(comentario, colacao)
        self.assertFalse(any('versão anterior' in p for p in problemas))
        self.assertFalse(any('nota de redação' in p.lower() for p in problemas))


if __name__ == '__main__':
    unittest.main()
