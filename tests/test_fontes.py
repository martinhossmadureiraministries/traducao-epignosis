import unittest

from bee.catalogo import Livro
from bee.fontes import ErroFonte, _aparato, _grego, _hebraico, _ler_scrivener, _mapa_hebraico


def livro_teste(numero, osis, contagens):
    return Livro(numero, osis, osis, osis, osis, '#ffffff', tuple(contagens))


def texto_sbl(osis, contagens, ignorar=(), extras=None, substituicoes=None):
    ignorar = set(ignorar)
    substituicoes = substituicoes or {}
    linhas = []
    for c, total in enumerate(contagens, 1):
        for v in range(1, total + 1):
            if (c, v) not in ignorar:
                valor = substituicoes.get((c, v), f'grego_{c}_{v}')
                linhas.append(f'{osis} {c}:{v}\t{valor}')
    for c, v, texto in extras or []:
        linhas.append(f'{osis} {c}:{v}\t{texto}')
    return '\n'.join(linhas)


def tr_para(contagens):
    return {'chapters': [[f'TR_{c}_{v}' for v in range(1, n + 1)] for c, n in enumerate(contagens, 1)]}


class FontesTest(unittest.TestCase):
    def test_sobrescricoes_salmos_nao_viram_versiculo_um(self):
        livro = livro_teste(230, 'Ps', [1])
        xml = b'''<osis><verse osisID="Ps.1.1"><w lemma="1">TITULO</w></verse>
          <verse osisID="Ps.1.2"><w lemma="2">VERSICULO</w></verse></osis>'''
        mapa = _mapa_hebraico(b'<verseMap><verse wlc="Ps.1.2" kjv="Ps.1.1" type="full"/></verseMap>')
        result = _hebraico(livro, xml, mapa)
        self.assertEqual(result[(1, 1)]['base'][0]['texto'], 'VERSICULO')
        self.assertIn('2', result[(1, 1)]['base'][0]['lemas_oshb'])

    def test_divisao_parcial_wlc_sempre_marca_ambos_os_destinos(self):
        livro = livro_teste(110, '1Kgs', [2])
        xml = b'''<osis><verse osisID="1Kgs.1.1"><w>ABC</w></verse>
          <verse osisID="1Kgs.1.2"><w>DEF</w></verse></osis>'''
        mapa = _mapa_hebraico(b'<verseMap><verse wlc="1Kgs.1.2!a" kjv="1Kgs.1.1!b" type="partial"/></verseMap>')
        result = _hebraico(livro, xml, mapa)
        self.assertEqual(len(result[(1, 1)]['base']), 2)
        self.assertIn('parte a', result[(1, 1)]['base'][1]['parte'])
        self.assertIn('parte b', result[(1, 2)]['base'][0]['parte'])
        self.assertIn('manualmente', result[(1, 2)]['aviso'])

    def test_fonte_ausente_nunca_e_preenchida_por_suposição(self):
        contagens = [1] * 6 + [69]
        livro = livro_teste(160, 'Neh', contagens)
        versiculos = []
        for c, total in enumerate(contagens, 1):
            for v in range(1, (68 if c == 7 else total) + 1):
                versiculos.append(f'<verse osisID="Neh.{c}.{v}"><w>heb{c}_{v}</w></verse>')
        xml = ('<osis>' + ''.join(versiculos) + '</osis>').encode()
        mapa = _mapa_hebraico(b'<verseMap><verse wlc="Neh.7.68" kjv="Neh.7.69" type="full"/></verseMap>')
        result = _hebraico(livro, xml, mapa)
        self.assertTrue(result[(7, 68)]['ausente'])
        self.assertEqual(result[(7, 69)]['base'][0]['referencia'], 'Neh.7.68')

    def test_doxologia_de_romanos_usa_tr_e_nao_finge_ser_sbl(self):
        contagens = [1] * 15 + [27]
        livro = livro_teste(520, 'Rom', contagens)
        texto = texto_sbl('Rom', contagens, ignorar={(16,25), (16,26), (16,27)})
        result = _grego(livro, texto, {}, tr_para(contagens))
        for v in (25, 26, 27):
            self.assertEqual(result[(16, v)]['base'][0]['edicao'], 'Textus Receptus')
            self.assertIn('não possui', result[(16, v)]['aviso'])
        self.assertEqual(result[(16, 24)]['base'][0]['edicao'], 'SBLGNT')
        with self.assertRaisesRegex(ErroFonte, 'inesperadamente'):
            _grego(livro, texto_sbl('Rom', contagens, ignorar={(1, 1), (16,25), (16,26), (16,27)}), {}, tr_para(contagens))

    def test_atos_e_corintios_alinhamento_por_trecho_nao_por_numero_igual(self):
        contagens = [1] * 18 + [41]
        livro = livro_teste(510, 'Acts', contagens)
        texto = texto_sbl('Acts', contagens, ignorar={(19,41)},
                          substituicoes={(19,40): 'primeira parte. καὶ ταῦτα εἰπὼν última parte.'})
        result = _grego(livro, texto, {}, tr_para(contagens))
        self.assertEqual(result[(19,40)]['base'][0]['texto'], 'primeira parte.')
        self.assertEqual(result[(19,41)]['base'][0]['texto'], 'καὶ ταῦτα εἰπὼν última parte.')
        self.assertIn('adaptada', result[(19,41)]['aviso'])
        contagens = [1] * 12 + [14]
        livro = livro_teste(540, '2Cor', contagens)
        texto = texto_sbl('2Cor', contagens, ignorar={(13,14)},
                          substituicoes={(13,12): 'beijo santo. ἀσπάζονται os santos.', (13,13): 'a graça.'})
        result = _grego(livro, texto, {}, tr_para(contagens))
        self.assertEqual(result[(13,12)]['base'][0]['texto'], 'beijo santo.')
        self.assertEqual(result[(13,13)]['base'][0]['texto'], 'ἀσπάζονται os santos.')
        self.assertEqual(result[(13,14)]['base'][0]['texto'], 'a graça.')
        self.assertEqual(result[(13,14)]['base'][0]['referencia'], '2Cor.13.13')

    def test_juncao_terceira_epistola_e_apocalipse(self):
        livro = livro_teste(710, '3John', [14])
        texto = texto_sbl('3John', [14], extras=[(1,15,'saudações adicionais')])
        result = _grego(livro, texto, {}, tr_para([14]))
        self.assertEqual([x['referencia'] for x in result[(1,14)]['base']], ['3John.1.14', '3John.1.15'])
        contagens = [1] * 11 + [17, 1]
        livro = livro_teste(730, 'Rev', contagens)
        texto = texto_sbl('Rev', contagens, extras=[(12,18,'sobre a areia')])
        result = _grego(livro, texto, {}, tr_para(contagens))
        self.assertEqual([x['referencia'] for x in result[(13,1)]['base']], ['Rev.12.18', 'Rev.13.1'])

    def test_scrivener_conversao_e_limite_hebreus(self):
        livro = livro_teste(650, 'Heb', [2])
        texto = ''' 1:1 [TITULO EM
                         DUAS LINHAS]
              polumerwv profhtaiv ep escatwn twn hmerwn
            1:2 on eyhken'''
        tr = _ler_scrivener(livro, texto)
        self.assertEqual(tr['chapters'][0][0], 'πολυμερως προφηταις')
        self.assertEqual(tr['chapters'][0][1], 'επ εσχατων των ημερων ον εθηκεν')
        self.assertEqual([ref for ref, _ in tr['ajustados'][(1, 2)]], [(1, 1), (1, 2)])
        with self.assertRaisesRegex(ErroFonte, 'inválido'):
            _ler_scrivener(livro, texto.replace('profhtaiv', 'profhtaiv@'))
        with self.assertRaisesRegex(ErroFonte, 'duplicado'):
            _ler_scrivener(livro, texto + '\n1:2 on eyhken')
        with self.assertRaisesRegex(ErroFonte, 'não encontrado'):
            _ler_scrivener(livro, texto.replace('ep escatwn', 'kata escatwn'))

    def test_limite_de_lucas_separa_e_mantem_referencias(self):
        contagens = [1] * 5 + [18]
        livro = livro_teste(490, 'Luke', contagens)
        texto = texto_sbl('Luke', contagens, substituicoes={
            (6, 17): 'texto do primeiro',
            (6, 18): 'οἳ ἦλθον ἀκοῦσαι· καὶ οἱ ⸂ἐνοχλούμενοι ἀπὸ⸃ πνευμάτων',
        })
        resultado = _grego(livro, texto, {}, tr_para(contagens))
        v17, v18 = resultado[(6, 17)], resultado[(6, 18)]
        self.assertEqual([x['referencia'] for x in v17['base']], ['Luke.6.17', 'Luke.6.18'])
        self.assertEqual(v17['base'][1]['texto'], 'οἳ ἦλθον ἀκοῦσαι·')
        self.assertTrue(v18['base'][0]['texto'].startswith('καὶ οἱ'))
        self.assertIn('adaptada', v17['aviso'])
        self.assertIn('adaptada', v18['aviso'])
        with self.assertRaisesRegex(ErroFonte, 'Limite SBLGNT'):
            _grego(livro, texto.replace('καὶ οἱ ⸂ἐνοχλούμενοι', 'outro'), {}, tr_para(contagens))

    def test_ordem_variavel_expoe_contexto_do_tr(self):
        contagens = [1] * 6 + [22]
        livro = livro_teste(480, 'Mark', contagens)
        resultado = _grego(livro, texto_sbl('Mark', contagens), {}, tr_para(contagens))
        self.assertIn('ordem das leituras', resultado[(7, 21)]['aviso'])
        self.assertEqual(resultado[(7, 21)]['textus_receptus_versiculo_vizinho']['referencia'], 'Mark.7.22')
        self.assertEqual(resultado[(7, 22)]['textus_receptus_versiculo_vizinho']['referencia'], 'Mark.7.21')

    def test_aparato_nao_inventa_notas(self):
        xml = b'<book><verse>John 1:15</verse><note>variante A</note><note>variante B</note><verse>John 1:18</verse><note>outra</note></book>'
        result = _aparato(xml)
        self.assertEqual(result[(1,15)], ['variante A','variante B'])
        self.assertNotIn((1,16), result)


if __name__ == '__main__':
    unittest.main()
