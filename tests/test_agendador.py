"""O verificador do agendador tem de distinguir "manual" de "agendado"."""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import sys
import tempfile
import unittest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))

import verificar_agendador as va  # noqa: E402


AGORA = datetime(2026, 11, 17, 21, 25, tzinfo=timezone.utc)


def corrida(inicio: datetime, evento: str) -> dict:
    return {
        'id': int(inicio.timestamp()),
        'event': evento,
        'status': 'completed',
        'conclusion': 'success',
        'created_at': inicio.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }


class AnalisarTest(unittest.TestCase):
    def test_sem_execucoes(self):
        resumo = va.analisar([], AGORA)
        self.assertEqual(resumo['veredicto'], 'sem-execucoes')
        self.assertEqual(resumo['total'], 0)

    def test_um_manual_nao_e_autonomia(self):
        """O caso real de 17/11: um run manual, zero agendados em 5 h."""
        resumo = va.analisar([corrida(AGORA - timedelta(hours=5, minutes=28), 'workflow_dispatch')], AGORA)
        self.assertEqual(resumo['veredicto'], 'nunca-agendado')
        self.assertEqual(resumo['por_evento'], {'workflow_dispatch': 1})
        self.assertIsNone(resumo['horas_sem_agendado'])

    def test_agendado_recente(self):
        resumo = va.analisar(
            [corrida(AGORA - timedelta(minutes=40), 'schedule'),
             corrida(AGORA - timedelta(hours=6), 'workflow_dispatch')],
            AGORA,
        )
        self.assertEqual(resumo['veredicto'], 'a-funcionar')
        self.assertEqual(resumo['por_evento'], {'schedule': 1, 'workflow_dispatch': 1})
        self.assertAlmostEqual(resumo['horas_sem_agendado'], 0.7, places=1)

    def test_agendado_antigo_esta_parado(self):
        resumo = va.analisar([corrida(AGORA - timedelta(hours=9), 'schedule')], AGORA)
        self.assertEqual(resumo['veredicto'], 'parado')

    def test_ignora_registos_sem_data(self):
        resumo = va.analisar([{'id': 1, 'event': 'schedule', 'created_at': ''}], AGORA)
        self.assertEqual(resumo['veredicto'], 'sem-execucoes')

    def test_conta_ultimas_24_horas(self):
        resumo = va.analisar(
            [corrida(AGORA - timedelta(hours=1), 'schedule'),
             corrida(AGORA - timedelta(hours=30), 'schedule')],
            AGORA,
        )
        self.assertEqual(resumo['total'], 2)
        self.assertEqual(resumo['ultimas_24h'], 1)


class FicheiroTest(unittest.TestCase):
    def test_aceita_resposta_da_api_em_ficheiro(self):
        dados = {'workflow_runs': [corrida(AGORA, 'schedule')]}
        with tempfile.TemporaryDirectory() as pasta:
            ficheiro = Path(pasta) / 'runs.json'
            ficheiro.write_text(json.dumps(dados), encoding='utf-8')
            with open('/dev/null', 'w') as nada:
                antigo, sys.stdout = sys.stdout, nada
                try:
                    codigo = va.main(['--json', str(ficheiro)])
                finally:
                    sys.stdout = antigo
        self.assertEqual(codigo, 0)

    def test_saida_1_quando_nao_ha_agendadas(self):
        dados = [corrida(AGORA - timedelta(hours=2), 'workflow_dispatch')]
        with tempfile.TemporaryDirectory() as pasta:
            ficheiro = Path(pasta) / 'runs.json'
            ficheiro.write_text(json.dumps(dados), encoding='utf-8')
            with open('/dev/null', 'w') as nada:
                antigo, sys.stdout = sys.stdout, nada
                try:
                    codigo = va.main(['--json', str(ficheiro)])
                finally:
                    sys.stdout = antigo
        self.assertEqual(codigo, 1)


if __name__ == '__main__':
    unittest.main()
