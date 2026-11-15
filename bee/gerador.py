"""Orquestra geração em lotes e checkpoint imediatamente após cada lote válido."""
from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from pathlib import Path
import sys
from typing import Any, Callable

from .arquivos import DadosInvalidos, ler_livro, ler_todos, salvar_livro, validar_versiculos
from .catalogo import Livro
from .fontes import ALINHAMENTO_VERSAO, FontesOriginais, MORPH_COMMIT, SBL_COMMIT, TR_COMMIT
from .ia import MotorIA, RespostaInvalida


def _placeholder_ausente(verso: int) -> dict[str, Any]:
    return {
        'verse': verso,
        'text': '[Versículo sem texto correspondente no WLC consultado.]',
        'commentary': (
            '<p><b>Análise Léxica:</b> Não verificada: não há texto-base WLC para esta referência.</p>'
            '<p><b>Crítica Textual:</b> A numeração tradicional inclui este versículo, '
            'mas ele não consta no WLC utilizado. É necessária uma fonte suplementar.</p>'
            '<p><b>Síntese Exegética:</b> Pendente de estabelecimento e revisão do texto.</p>'
        ),
    }


def _registrar(dados: dict[str, Any], capitulo: int, inicio: int, fim: int, provedor: str, modelo: str) -> None:
    dados.setdefault('history', []).append({
        'chapter': capitulo, 'verse_from': inicio, 'verse_to': fim,
        'provider': provedor, 'model': modelo,
        'generated_at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    })


def _salvar_lote(
    caminho: Path, dados: dict[str, Any], livro: Livro, capitulo: int,
    parcial: list[dict[str, Any]], total: int,
) -> None:
    chave = str(capitulo)
    if len(parcial) == total:
        dados['chapters'][chave] = parcial
        dados.setdefault('in_progress', {}).pop(chave, None)
    else:
        dados.setdefault('in_progress', {})[chave] = parcial
    salvar_livro(caminho, dados, livro)


def gerar_livros(
    livros: list[Livro], diretorio: Path, fontes: FontesOriginais,
    obter_motor: Callable[[], MotorIA], versos_por_pedido: int,
    tentativas_conteudo: int, max_capitulos: int | None = None,
) -> int:
    # Detecte ficheiros inválidos/duplicados e evite criar um segundo ficheiro
    # para um livro que o utilizador tenha renomeado acidentalmente.
    existentes = ler_todos(diretorio)
    for livro in livros:
        caminho = diretorio / livro.nome_arquivo
        if livro.numero in existentes and not caminho.exists():
            raise DadosInvalidos(
                f'O livro {livro.numero} está noutro ficheiro. Renomeie-o para {livro.nome_arquivo} antes de gerar.'
            )

    gerados = 0
    motor: MotorIA | None = None
    for livro in livros:
        caminho = diretorio / livro.nome_arquivo
        dados = ler_livro(caminho, livro)
        for capitulo in range(1, livro.capitulos + 1):
            chave = str(capitulo)
            if chave in dados['chapters']:
                continue
            if max_capitulos is not None and gerados >= max_capitulos:
                print(f'Limite de {max_capitulos} capítulo(s) atingido; progresso preservado.', flush=True)
                return gerados
            # Uma chave ausente deve falhar antes de descarregar as fontes.
            if motor is None:
                motor = obter_motor()
            versoes = (
                {'versification': 'KJV/tradicional', 'alignment_version': ALINHAMENTO_VERSAO, 'wlc_oshb_commit': MORPH_COMMIT}
                if livro.antigo_testamento else
                {'versification': 'KJV/tradicional', 'alignment_version': ALINHAMENTO_VERSAO,
                 'sblgnt_commit': SBL_COMMIT, 'textus_receptus_commit': TR_COMMIT}
            )
            anterior = dados.get('sources')
            if anterior is not None and anterior != versoes:
                raise DadosInvalidos(f'{livro.nome}: as versões das fontes diferem do checkpoint; revise antes de misturar edições.')
            dados['sources'] = versoes
            fontes_capitulo = fontes.capitulo(livro, capitulo)
            total = livro.versos_por_capitulo[capitulo - 1]
            parcial = list(dados.get('in_progress', {}).get(chave, []))
            if parcial:
                print(f'A retomar {livro.nome} {capitulo} a partir do versículo {len(parcial) + 1}/{total}.', flush=True)
            else:
                print(f'A gerar {livro.nome} {capitulo} ({total} versículos)...', flush=True)
            limite_lote = versos_por_pedido
            while len(parcial) < total:
                inicio = len(parcial) + 1
                fonte_atual = fontes_capitulo[inicio - 1]
                if fonte_atual.get('ausente'):
                    parcial.append(_placeholder_ausente(inicio))
                    _registrar(dados, capitulo, inicio, inicio, 'local', 'sem-fonte-WLC')
                    _salvar_lote(caminho, dados, livro, capitulo, parcial, total)
                    print(f'  {livro.nome} {capitulo}:{inicio}: marcador de fonte ausente guardado.', flush=True)
                    continue
                tamanho = min(limite_lote, total - inicio + 1)
                # Nunca inclua o marcador de texto ausente no pedido à IA.
                for indice, item in enumerate(fontes_capitulo[inicio - 1:inicio - 1 + tamanho]):
                    if item.get('ausente'):
                        tamanho = indice
                        break
                falhas_unitarias = 0
                while True:
                    selecionadas = fontes_capitulo[inicio - 1:inicio - 1 + tamanho]
                    try:
                        versiculos = motor.gerar(livro, capitulo, selecionadas)
                        validar_versiculos(versiculos, range(inicio, inicio + tamanho), f'{livro.nome} {capitulo}')
                        break
                    except RespostaInvalida as exc:
                        if tamanho > 1:
                            tamanho = max(1, tamanho // 2)
                            limite_lote = min(limite_lote, tamanho)
                            print(
                                f'  Resposta inválida ou truncada ({exc}); a dividir o lote para {tamanho} versículo(s).',
                                file=sys.stderr, flush=True,
                            )
                        else:
                            falhas_unitarias += 1
                            if falhas_unitarias >= tentativas_conteudo:
                                raise RespostaInvalida(
                                    f'{livro.nome} {capitulo}:{inicio}: resposta inválida após '
                                    f'{falhas_unitarias} tentativa(s). Progresso anterior preservado. {exc}'
                                ) from exc
                            print(f'  A repetir {livro.nome} {capitulo}:{inicio}: {exc}', file=sys.stderr, flush=True)
                for versiculo, fonte in zip(versiculos, selecionadas):
                    if fonte.get('aviso'):
                        versiculo['commentary'] += (
                            '<p><b>Nota de fonte:</b> ' + escape(fonte['aviso']) + '</p>'
                        )
                parcial.extend(versiculos)
                _registrar(dados, capitulo, inicio, inicio + tamanho - 1, motor.provedor, motor.modelo)
                _salvar_lote(caminho, dados, livro, capitulo, parcial, total)
                print(f'  Guardados {livro.nome} {capitulo}:{inicio}-{inicio + tamanho - 1}.', flush=True)
            gerados += 1
            print(f'Capítulo concluído: {livro.nome} {capitulo}.', flush=True)
    if gerados == 0:
        print('Todos os capítulos selecionados já estavam concluídos; nenhuma chamada de IA foi feita.', flush=True)
    return gerados
