"""Higiene do repositório: nada de segredos ou binários gerados versionados."""
import subprocess
from pathlib import Path
import unittest


class RepositorioTest(unittest.TestCase):
    def test_sem_env_ou_modulos_sqlite_versionados(self):
        saida = subprocess.run(
            ['git', 'ls-files', '-z'], check=True, capture_output=True, text=True,
        ).stdout
        ficheiros = [Path(nome) for nome in saida.split('\0') if nome]
        proibidos = [
            str(caminho) for caminho in ficheiros
            if caminho.name.startswith('.env') and caminho.name != '.env.example'
            or caminho.suffix in ('.SQLite3', '.SQLite3-journal', '.SQLite3-wal')
            or caminho.name in ('BEE-modulos.zip', 'BEE-capitulos.zip', 'BEE-diagnostico.zip')
        ]
        self.assertEqual(proibidos, [], f'Não versione segredos/binários gerados: {proibidos}')
