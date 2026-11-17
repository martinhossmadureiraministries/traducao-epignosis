"""Execução de uma fatia de produção, fora do SDK (chamada pela atividade).

Funções síncronas: baixam os JSON do ramo de dados, geram um orçamento de
versículos com o gerador existente (fontes WLC/SBLGNT/TR fixadas por commit),
validam, commitam as mudanças no GitHub e, quando um capítulo completa,
recompilam os módulos MyBible e atualizam a release de prévia.
"""
from __future__ import annotations

import os
from pathlib import Path
import tempfile
from typing import Any

from bee.agenda import livros_na_fila
from bee.fontes import FontesOriginais
from bee.gerador import ConfigGeracao, gerar_fatia
from bee.rede import ClienteHTTP

from worker import sincronizacao_github as github
from worker.motor_mistral import MODELO_PADRAO, MotorMistral

CACHE_FONTES = Path(os.environ.get('BEE_CACHE_FONTES', '/tmp/bee-fontes'))


def executar_fatia(estado: dict[str, Any]) -> dict[str, Any]:
    repositorio = estado['repositorio']
    ramo = estado['ramo_dados']
    with tempfile.TemporaryDirectory(prefix='bee-fatia-') as temporario:
        raiz = Path(temporario)
        dados_dir = raiz / 'dados'
        saida = raiz / 'saida'
        baixados = github.baixar_dados(repositorio, ramo, dados_dir)
        antes = {nome: (dados_dir / nome).read_bytes() for nome in baixados}
        motor = MotorMistral(
            modelo=estado.get('modelo', MODELO_PADRAO),
            orientacoes=estado.get('orientacoes', ''),
        )
        fontes = FontesOriginais(CACHE_FONTES, ClienteHTTP())
        livros = livros_na_fila(estado.get('ordem') or None, 'plano')
        config = ConfigGeracao(
            versos_por_pedido=estado.get('versos_por_pedido', 8),
            max_versos=estado.get('versos_por_fatia', 24),
        )
        progresso = gerar_fatia(livros, dados_dir, fontes, motor, config)
        arquivos = {
            f'livros_json/{livro.nome_arquivo}': conteudo
            for livro in livros
            if (dados_dir / livro.nome_arquivo).exists()
            and (conteudo := (dados_dir / livro.nome_arquivo).read_bytes()) != antes.get(livro.nome_arquivo)
        }
        commit = ''
        if arquivos:
            commit = github.commit_arquivos(
                repositorio, ramo, arquivos,
                f'BEE: {progresso.versos} versículo(s) de {motor.rotulo}',
            )
        resumo: dict[str, Any] = {
            'versos': progresso.versos,
            'capitulos': progresso.capitulos,
            'pedidos': progresso.pedidos,
            'concluido': progresso.concluido,
            'alterado': progresso.alterado,
            'livro': progresso.livro.nome if progresso.livro else None,
            'capitulo_atual': progresso.capitulo,
            'motivos': progresso.motivos,
            'commit': commit,
            'modelo': motor.rotulo,
        }
        if estado.get('compilar', True) and (progresso.capitulos > 0 or progresso.concluido):
            resumo['modulos'] = github.publicar_modulos(
                repositorio, ramo, dados_dir, saida,
                estado.get('publicar_release', True),
                f'{progresso.versos} versículo(s) nesta fatia ({motor.rotulo})',
            )
        return resumo
