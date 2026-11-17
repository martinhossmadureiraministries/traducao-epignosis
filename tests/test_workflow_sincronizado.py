"""O workflow que corre tem de ser igual ao modelo documentado.

Custou horas de produção: entre 16/11 e 17/11 o cron em `.github/workflows/`
esteve sempre em `*/15`, enquanto `modelos/` foi alterado para `*/60` e `*/45`.
As contas de minutos estavam certas no papel e erradas no GitHub.
"""
from pathlib import Path
import unittest


RAIZ = Path(__file__).resolve().parent.parent
MODELO = RAIZ / 'modelos' / 'bee-autopiloto.yml'
ATIVO = RAIZ / '.github' / 'workflows' / 'bee-autopiloto.yml'
REL_MODELO = RAIZ / 'modelos' / 'bee-relogio.yml'
REL_DOC = RAIZ / 'docs' / 'bee-relogio.yml'
REL_ATIVO = RAIZ / '.github' / 'workflows' / 'bee-relogio.yml'


class WorkflowSincronizadoTest(unittest.TestCase):
    def test_modelo_e_workflow_ativo_sao_iguais(self):
        """Falha enquanto o workflow activo não receber o modelo.

        O agente que prepara as alterações não tem permissão para escrever em
        `.github/workflows/` (o GitHub recusa o push). O modelo é actualizado
        aqui e o responsável copia-o; até lá este teste fica vermelho e diz
        exactamente o que fazer. É preferível um teste vermelho a uma produção
        parada sem ninguém saber porquê.
        """
        self.assertTrue(MODELO.is_file(), 'o modelo tem de existir')
        self.assertTrue(ATIVO.is_file(), 'o workflow ativo tem de existir')
        if MODELO.read_text(encoding='utf-8') == ATIVO.read_text(encoding='utf-8'):
            return
        atual = ATIVO.read_text(encoding='utf-8')
        esperado = MODELO.read_text(encoding='utf-8')
        pistas = []
        for marca in ('cron:', 'BEE_HORA_INICIO', 'BEE_VERSOS_POR_CICLO',
                      'BEE_LOTE', 'BEE_PEDIDOS_POR_DIA', 'timeout-minutes'):
            def valor(texto):
                for linha in texto.splitlines():
                    if marca in linha and '#' not in linha.split(marca)[0]:
                        return linha.strip()
                return '(ausente)'
            if valor(atual) != valor(esperado):
                pistas.append(f'  {marca}: activo={valor(atual)} | modelo={valor(esperado)}')
        self.fail(
            'O workflow activo está diferente do modelo. Copie '
            'modelos/bee-autopiloto.yml para .github/workflows/bee-autopiloto.yml '
            '(no site do GitHub: abrir o ficheiro, Edit, colar, Commit).\n'
            + '\n'.join(pistas)
        )

    def test_cron_fora_da_hora_cheia(self):
        """O minuto 0 é o mais congestionado do GitHub Actions."""
        texto = MODELO.read_text(encoding='utf-8')
        linha = [l for l in texto.splitlines() if 'cron:' in l]
        self.assertEqual(len(linha), 1, 'deve haver exactamente um cron')
        expressao = linha[0].split("'")[1]
        minutos = expressao.split()[0]
        self.assertNotIn('0,', minutos)
        self.assertNotEqual(minutos, '0', 'a hora cheia é o pior minuto para agendar')
        self.assertNotRegex(expressao, r'^\*/[1-9]\b',
                            'passos de */N perdem o alinhamento quando o GitHub atrasa')

    def test_cron_horario(self):
        """24 disparos por dia: a alta frequência é travada em silêncio.

        O cron '7,27,47' esteve no `main` desde 16/11 e produziu zero execuções
        agendadas; 20 em 20 minutos é frequência de filtro anti-abuso.
        """
        texto = MODELO.read_text(encoding='utf-8')
        linha = [l for l in texto.splitlines() if 'cron:' in l][0]
        expressao = linha.split("'")[1].strip()
        self.assertEqual(expressao, '23 * * * *')


class RelogioSincronizadoTest(unittest.TestCase):
    """O segundo relógio é opcional no GitHub, mas as cópias não divergem."""

    def test_docs_e_modelo_sao_iguais(self):
        self.assertTrue(REL_DOC.is_file(), 'falta docs/bee-relogio.yml')
        self.assertEqual(REL_DOC.read_text(encoding='utf-8'),
                         REL_MODELO.read_text(encoding='utf-8'))

    def test_cron_do_relogio_depois_da_producao(self):
        texto = REL_MODELO.read_text(encoding='utf-8')
        linha = [l for l in texto.splitlines() if 'cron:' in l][0]
        self.assertEqual(linha.split("'")[1].strip(), '41 * * * *')

    def test_workflow_ativo_igual_se_existir(self):
        """Enquanto não for colado na UI, o relógio não corre — e o teste diz isso."""
        if not REL_ATIVO.is_file():
            self.skipTest('bee-relogio.yml ainda não foi colado na UI (ver docs/AGENDADOR.md)')
        self.assertEqual(REL_ATIVO.read_text(encoding='utf-8'),
                         REL_MODELO.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
