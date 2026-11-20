"""Manuscritologia: leitura de transcrições MES, camadas de correção e colação.

Cobre os defeitos reais que a primeira colação de 2 Tessalonicenses expôs, para
que nenhum deles volte silenciosamente:

  * a referência MES tem **8** dígitos (LLCCCVVV) — com 9, nenhuma linha de
    ``critical texts`` casava e as cinco edições pareciam «ausentes»;
  * as quebras de linha caem **dentro** de palavras (``σιλουα/νοσ``) — separar por
    ``/`` inventava variantes;
  * a ligadura KAI (``ϗ``) **vale uma palavra** (καί) — apagá-la fazia o escriba
    parecer omitir um «e»;
  * ``x{και} {}`` é UMA correção com duas camadas e a camada vazia significa
    «apagado»; juntar tudo no fim do versículo destruía a ordem;
  * a leitura vigente é a da camada mais tardia (``c > b > a > editada >
    original``), não a do escriba original;
  * nomina sacra não indicam caso, e abreviatura por barra só se completa quando
    a forma da base **começa** pela forma abreviada — o resto fica por resolver.

Tudo com ficheiros sintéticos em ``tempfile``: estes testes correm sem rede, sem
``.bee-cache/`` e sem o acervo CNTR (que é CC BY-SA e nunca é redistribuído).
"""
from pathlib import Path
import tempfile
import unittest

from bee.manuscritos import (
    Correcao,
    Divergencia,
    Palavra,
    VersiculoTestemunha,
    _expandir_nomen,
    _palavra,
    _segmentos,
    canonica,
    colacionar,
    diferenca,
    harmonizar,
    ler_testemunha,
    normalizar,
    normalizar_texto,
    sem_diacriticos,
    unidades_de_variacao,
)

MACRON = '\u00af'          # ¯ : barra de abreviatura do MES
ILEGIVEL = '\ufffd'        # letra não identificada no suporte


def escrever(linhas: list[str], nome: str = 'T') -> Path:
    """Ficheiro MES sintético (referência de 8 dígitos + espaço + texto)."""
    pasta = Path(tempfile.mkdtemp(prefix='bee-mes-'))
    caminho = pasta / f'{nome}.txt'
    caminho.write_text('\n'.join(linhas) + '\n', encoding='utf-8')
    return caminho


class NormalizacaoTest(unittest.TestCase):
    def test_diacriticos_e_sigma_final(self):
        self.assertEqual(sem_diacriticos('Θεοῦ'), 'θεου')
        self.assertEqual(sem_diacriticos('ἀδελφοί'), 'αδελφοι')
        self.assertEqual(sem_diacriticos('Ἰησοῦς'), 'ιησουσ')

    def test_marcas_mes_nao_sao_letra(self):
        self.assertEqual(normalizar('{και}'), 'και')
        self.assertEqual(normalizar('=θσ'), 'θσ')
        self.assertEqual(normalizar('~εν'), 'εν')
        self.assertEqual(normalizar('πα%τερ'), 'πατερ')

    def test_sigla_critica_das_edicoes_e_removida(self):
        # ⸀ (U+2E00) marca unidade no aparato de edições impressas, não no texto.
        self.assertEqual(normalizar_texto('⸀απαρχὴν ⸂ἔργῳ καὶ λόγῳ⸃'),
                         ['απαρχην', 'εργω', 'και', 'λογω'])

    def test_quebra_de_linha_dentro_da_palavra_nao_separa(self):
        self.assertEqual(normalizar_texto('σιλουα/νοσ'), ['σιλουανοσ'])
        self.assertEqual(normalizar_texto('εκκλη/σια \\1 θεου'), ['εκκλησια', 'θεου'])

    def test_ligadura_kai_vale_uma_palavra(self):
        # Apagar ϗ fazia o escriba parecer omitir καί (01 em 2Ts 2:4 e 2:16).
        self.assertEqual(normalizar_texto('ϗ ὑπεραιρομενοσ'), ['και', 'υπεραιρομενοσ'])
        self.assertEqual(normalizar('ϗ'), 'και')

    def test_pontuacao_e_elisao_nao_geram_variante(self):
        self.assertEqual(normalizar_texto('ἀπʼ ἀρχῆς'), ['απ', 'αρχησ'])
        self.assertEqual(normalizar('ὑμῶν·'), 'υμων')


class NominaSacraTest(unittest.TestCase):
    def test_formas_atestadas_expandem_se(self):
        self.assertEqual(_expandir_nomen('=θσ'), ('θεοσ', True, False))
        self.assertEqual(_expandir_nomen('=κσ'), ('κυριοσ', True, False))
        self.assertEqual(_expandir_nomen('=πνσ'), ('πνεματοσ', True, False))

    def test_abreviatura_desconhecida_nao_se_conjetura(self):
        forma, era_nomen, duvidosa = _expandir_nomen('=ξφ')
        self.assertTrue(era_nomen)
        self.assertTrue(duvidosa, 'sem forma atestada, a dúvida fica assinalada')
        self.assertEqual(forma, 'ξφ', 'a abreviatura conserva-se, não se inventa')

    def test_palavra_sem_nomen_nao_e_marcada(self):
        self.assertEqual(_expandir_nomen('θεοσ'), ('θεοσ', False, False))

    def test_familia_flexional_neutraliza_o_caso(self):
        for forma in ('πατηρ', 'πατροσ', 'πατρι', 'πατερα'):
            self.assertEqual(canonica(forma), 'PATER')
        self.assertEqual(canonica('κυριοσ'), 'KYRIOS')
        self.assertEqual(canonica('λογον'), 'λογον', 'fora das famílias, fica igual')


class PalavraTest(unittest.TestCase):
    def test_marcas_fisicas_ficam_na_palavra(self):
        self.assertTrue(_palavra('~εν').suprida)
        self.assertTrue(_palavra('πα%τερ').danificada)
        self.assertTrue(_palavra('πα^τερ').faltante)
        self.assertTrue(_palavra(f'εν{ILEGIVEL}').ilegivel)
        self.assertTrue(_palavra(f'ημω{MACRON}').abreviada)
        self.assertEqual(_palavra('⋄3').versiculo_alternativo, 3)
        self.assertTrue(_palavra('=θσ').nomen_sacrum)

    def test_forma_e_comparavel(self):
        palavra = _palavra(f'ημω{MACRON}')
        self.assertEqual(palavra.forma, 'ημω')
        self.assertEqual(palavra.crua, f'ημω{MACRON}')


class SegmentosTest(unittest.TestCase):
    def test_correcao_fica_na_posicao_do_versiculo(self):
        itens = _segmentos('εν =θω x{και} {} πατρι')
        self.assertEqual([type(i) for i in itens],
                         [Palavra, Palavra, Correcao, Palavra],
                         'o bloco corrigido fica onde o escriba o escreveu')
        self.assertEqual(itens[0].forma, 'εν')
        self.assertEqual(itens[1].forma, 'θεω', 'nomen sacrum expandida')
        self.assertTrue(itens[1].nomen_sacrum)
        self.assertEqual(itens[3].forma, 'πατρι')

    def test_camada_vazia_significa_apagado(self):
        correcao = _segmentos('x{και} {}')[0]
        self.assertEqual(tuple(p.forma for p in correcao.original), ('και',))
        self.assertEqual(correcao.vigente, (), 'o καί cancelado não reaparece')

    def test_camada_inexistente_nao_e_camada_vazia(self):
        correcao = _segmentos('x{και}')[0]
        self.assertEqual(tuple(p.forma for p in correcao.original), ('και',))
        self.assertEqual(tuple(p.forma for p in correcao.vigente), ('και',))

    def test_precedencia_dos_corretores(self):
        # MES: c > b > a > editada > original. 01 em 2Ts 2:4 tem ϗ ὑπεραμενος na
        # camada editada e ϗ ὑπεραιρομενοσ do corretor a: vigora a do corretor.
        correcao = _segmentos('{ϗ ὑπεραμενοσ} a{ϗ ὑπεραιρομενοσ}')[0]
        vigente = ' '.join(p.forma for p in correcao.vigente)
        self.assertEqual(vigente, 'και υπεραιρομενοσ', 'vigora a mão do corretor a')
        self.assertEqual(list(correcao.corretores), ['a'])
        editada = ' '.join(p.forma for p in correcao.camadas[''])
        self.assertIn('υπεραμενοσ', editada,
                      'a camada anterior fica registada, com o seu itacismo')

    def test_dois_grupos_vizinhos_sao_uma_so_correcao(self):
        itens = _segmentos('εν x{υμων} {ημων} θεω')
        self.assertEqual(len(itens), 3)
        self.assertIsInstance(itens[1], Correcao)
        self.assertEqual(tuple(p.forma for p in itens[1].original), ('υμων',))
        self.assertEqual(tuple(p.forma for p in itens[1].vigente), ('ημων',))


class HarmonizarTest(unittest.TestCase):
    def test_abreviatura_por_barra_completa_se_quando_a_base_comeca_por_ela(self):
        # ημω̄ por ἡμῶν (02 em 2Ts 1:9, 3:3, 3:16): não é variante.
        leitura, notas = harmonizar(['ημων'], (_palavra(f'ημω{MACRON}'),))
        self.assertEqual(leitura, ['ημων'])
        self.assertIn('abrev:ημω=ημων', notas)

    def test_abreviatura_que_nao_e_prefixo_fica_por_resolver(self):
        # 01 em 2Ts 2:13 escreve οφιλομε¯ e a base lê οφειλομεν: completar aqui
        # seria conjetura, por isso a divergência mantém-se e fica assinalada.
        leitura, notas = harmonizar(['οφειλομεν'], (_palavra(f'οφιλομε{MACRON}'),))
        self.assertEqual(leitura, ['οφιλομε'])
        self.assertIn('abrev_por_resolver:οφιλομε?οφειλομεν', notas)

    def test_nomen_sacrum_adopta_a_forma_da_base_dentro_da_familia(self):
        # =πατηρ comparado com πατρὸς inventava «πατροσ → πατηρ» (02 em 2Ts 1:2).
        leitura, notas = harmonizar(['πατροσ'], (_palavra('=πηρ'),))
        self.assertEqual(leitura, ['πατροσ'])
        self.assertIn('ns:πατηρ=πατροσ', notas)

    def test_diferenca_de_caso_fora_de_nomen_sacrum_e_variante(self):
        leitura, notas = harmonizar(['πατροσ'], (_palavra('πατηρ'),))
        self.assertEqual(leitura, ['πατηρ'], 'sem marca de nomen, o caso conta')
        self.assertEqual(notas, [])

    def test_expansao_duvidosa_e_ilegivel_sao_assinaladas(self):
        leitura, notas = harmonizar(
            ['θεου'], (_palavra('=ξφ'), _palavra(f'{ILEGIVEL}')))
        self.assertTrue(any(n.startswith('expansao_duvidosa:') for n in notas))
        self.assertTrue(any(n.startswith('ilegivel:') for n in notas))

    def test_harmonizacao_nao_apaga_variante_real(self):
        leitura, notas = harmonizar(
            ['απαρχην'], (_palavra('απ'), _palavra('αρχησ')))
        self.assertEqual(leitura, ['απ', 'αρχησ'])
        self.assertEqual(notas, [])


class LerTestemunhaTest(unittest.TestCase):
    def test_referencia_de_oito_digitos(self):
        caminho = escrever(['53001001 παυλοσ και σιλουανοσ και τιμοθεοσ'])
        versos = ler_testemunha(caminho, 53)
        self.assertIn('1:1', versos)
        self.assertEqual(versos['1:1'].texto, 'παυλοσ και σιλουανοσ και τιμοθεοσ')
        self.assertEqual(versos['1:1'].testemunha, caminho.stem)

    def test_nove_digitos_nao_casam(self):
        caminho = escrever(['530010012 παυλοσ'])
        self.assertEqual(ler_testemunha(caminho, 53), {})

    def test_outro_livro_e_ignorado(self):
        caminho = escrever(['53001001 παυλοσ', '49001001 ευλογητοσ'])
        self.assertEqual(list(ler_testemunha(caminho, 53)), ['1:1'])

    def test_versiculo_ausente_no_suporte(self):
        caminho = escrever(['53001001 παυλοσ', '53001005 -'])
        versos = ler_testemunha(caminho, 53)
        self.assertFalse(versos['1:5'].presente)
        self.assertEqual(versos['1:5'].texto, '')

    def test_estado_fisico_do_suporte(self):
        caminho = escrever([
            '53001002 ~εν ~θεω',            # lacuna com texto suprido
            '53001003 [εν] θεου',            # texto duvidoso
            '53001004 εν ⋄2 θεου',           # divisão alternativa do versículo
            '53001006 x{τοπω} {τροπω}',      # corrigido
        ])
        versos = ler_testemunha(caminho, 53)
        self.assertTrue(versos['1:2'].lacuna)
        self.assertTrue(versos['1:2'].suprido)
        self.assertTrue(versos['1:3'].texto_duvidoso)
        self.assertTrue(versos['1:4'].dividido)
        self.assertTrue(versos['1:6'].corrigida)
        self.assertEqual(versos['1:6'].camada('original'), 'τοπω')
        self.assertEqual(versos['1:6'].leitura_original, 'τοπω')
        self.assertEqual(versos['1:6'].texto, 'τροπω')

    def test_corrigida_e_a_unica_fonte(self):
        # Houve um campo `corrigido` e uma propriedade `corrigida` a poderem
        # divergir; ficou só a propriedade calculada pelas camadas.
        caminho = escrever(['53001001 x{τοπω} {τροπω}', '53001002 εν θεου'])
        versos = ler_testemunha(caminho, 53)
        self.assertTrue(versos['1:1'].corrigida)
        self.assertFalse(versos['1:2'].corrigida)
        self.assertFalse(hasattr(versos['1:1'], 'corrigido'))

    def test_ilegivel_na_mao_original(self):
        caminho = escrever([f'53002001 ν{ILEGIVEL} x{{ν{ILEGIVEL}}} {{ερωτωμεν}}'])
        versos = ler_testemunha(caminho, 53)
        self.assertTrue(versos['2:1'].ilegivel_original)
        self.assertTrue(versos['2:1'].corrigida)


class ColacionarTest(unittest.TestCase):
    def base(self, *palavras: str) -> list[str]:
        return list(palavras)

    def carregar(self, linhas: list[str]) -> dict[str, VersiculoTestemunha]:
        caminho = escrever(linhas, nome='W')
        return ler_testemunha(caminho, 53)

    def test_leitura_identica(self):
        fontes = self.carregar(['53001001 απ αρχησ'])
        achados = colacionar(self.base('απ', 'αρχησ'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'identica')
        self.assertIsInstance(achados[0], Divergencia)

    def test_testemunha_ausente(self):
        fontes = self.carregar(['53001001 -'])
        achados = colacionar(self.base('απ'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'ausente')

    def test_testemunha_que_nao_tem_o_versiculo(self):
        achados = colacionar(self.base('απ'), {'W': None})
        self.assertEqual(achados[0].estado, 'ausente')

    def test_omissao_e_acrescimo(self):
        fontes = self.carregar(['53001001 ο θεοσ ημων'])
        achados = colacionar(self.base('ο', 'κυριοσ', 'ημων'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'divergente')
        self.assertIn('κυριοσ → θεοσ', achados[0].diferenca)

    def test_transposicao_e_variante(self):
        # Conjuntos anulariam isto; a colação é sequencial.
        fontes = self.carregar(['53001001 ημασ αυτουσ'])
        achados = colacionar(self.base('αυτουσ', 'ημασ'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'divergente')
        self.assertIn('+[ημασ]', achados[0].diferenca)
        self.assertIn('-[ημασ]', achados[0].diferenca)

    def test_palavra_repetida_nao_se_anula(self):
        fontes = self.carregar(['53001001 και θεου'])
        achados = colacionar(self.base('και', 'και', 'θεου'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'divergente')
        self.assertIn('-[και]', achados[0].diferenca)

    def test_itacismo_aparece_como_divergencia_ortografica(self):
        # Não se esconde: quem decide se é só ortografia é a nota, não a colação.
        fontes = self.carregar(['53001001 σειλουανοσ'])
        achados = colacionar(self.base('σιλουανοσ'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'divergente')

    def test_estado_fisico_acompanha_a_divergencia(self):
        fontes = self.carregar(['53001001 x{τοπω} {τροπω} εν'])
        achados = colacionar(self.base('τροπω', 'εν'), {'W': fontes['1:1']})
        self.assertEqual(achados[0].estado, 'identica')
        self.assertIn('corrigido', achados[0].fisico)

    def test_diferenca_de_sequencia_vazia(self):
        self.assertEqual(diferenca([], []), 'ordem diferente')

    def test_unidades_de_variacao_so_onde_ha_divergencia(self):
        caminho = escrever(['53001001 απ αρχησ', '53001002 εν θεου'])
        testemunhas = {'W': ler_testemunha(caminho, 53)}
        base = {'1:1': ['απ', 'αρχησ'], '1:2': ['εν', 'κυριω']}
        unidades = unidades_de_variacao(['1:1', '1:2'], base, testemunhas)
        self.assertEqual(list(unidades), ['1:2'])


if __name__ == '__main__':
    unittest.main()
