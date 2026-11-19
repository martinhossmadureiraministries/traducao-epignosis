"""Memória de estilo da edição nova: única fonte de verdade em JSON.

Vários provedores (Gemini, Groq, Cerebras…) só convergem na mesma voz se todos
receberem EXATAMENTE as mesmas regras de estilo. Este módulo torna isso
mecânico: o ficheiro ``modelos/estilo_bee.json`` guarda a memória (registo,
lista negra de arcaísmos, glossário com contextos de reuso, palavras
rejeitadas, fórmulas consolidadas, âncoras aprovadas e contrastes mau→bom) e os
renderizadores abaixo transformam-na nos fragmentos que ``bee/perfil.py`` cola
nos prompts da edição nova.

O módulo é deliberadamente puro (só biblioteca padrão, nenhuma dependência do
resto do pacote): pode ser importado e testado sem rede, sem chaves e sem o
catálogo, e valida o schema ao carregar para que um JSON malformado falhe alto
nos testes em vez de corromper silenciosamente uma corrida de tradução.

O perfil legado NÃO usa nada daqui — continua byte-idêntico.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO = RAIZ / 'modelos' / 'estilo_bee.json'

_CHAVES_OBRIGATORIAS = (
    'identidade', 'metodo', 'registro', 'regras_duras', 'aperto',
    'proibicoes_globais', 'glossario', 'rejeitados', 'formulas_consolidadas',
    'ancoras', 'contrastes', 'aprovacoes',
)


# --------------------------------------------------------------------------
# Carregamento e validação do schema
# --------------------------------------------------------------------------
def validar(dados: Any) -> list[str]:
    """Valida a estrutura da memória de estilo; devolve a lista de erros."""
    erros: list[str] = []
    if not isinstance(dados, dict):
        return ['a raiz deve ser um objeto JSON']
    for chave in _CHAVES_OBRIGATORIAS:
        if chave not in dados:
            erros.append(f'falta a chave obrigatória {chave!r}')
    if erros:
        return erros  # sem as chaves, as verificações seguintes não fazem sentido

    if not isinstance(dados['identidade'], str) or not dados['identidade'].strip():
        erros.append('identidade deve ser texto não vazio')
    if not isinstance(dados['metodo'], list) or not dados['metodo']:
        erros.append('metodo deve ser uma lista não vazia')
    elif any(not isinstance(item, str) or not item.strip() for item in dados['metodo']):
        erros.append('cada ponto de metodo deve ser texto não vazio')

    registro = dados['registro']
    if not isinstance(registro, dict):
        erros.append('registro deve ser um objeto')
    else:
        for campo in ('tratamento_plural', 'tu_oracao_direta'):
            if not isinstance(registro.get(campo), str) or not registro[campo].strip():
                erros.append(f'registro.{campo} deve ser texto não vazio')
        proibidos = registro.get('arcaismos_proibidos')
        if not isinstance(proibidos, list) or not proibidos:
            erros.append('registro.arcaismos_proibidos deve ser lista não vazia')
        elif any(not isinstance(t, str) or not t.strip() for t in proibidos):
            erros.append('cada arcaísmo proibido deve ser texto não vazio')

    for i, regra in enumerate(dados['regras_duras']):
        if not isinstance(regra, dict) or not regra.get('rotulo') or not regra.get('texto'):
            erros.append(f'regras_duras[{i}] exige rotulo e texto não vazios')
    for i, item in enumerate(dados['aperto']):
        if not isinstance(item, dict) or not item.get('rotulo') or not item.get('texto'):
            erros.append(f'aperto[{i}] exige rotulo e texto não vazios')

    for i, entrada in enumerate(dados['glossario']):
        if not isinstance(entrada, dict):
            erros.append(f'glossario[{i}] deve ser um objeto')
            continue
        if not entrada.get('usar'):
            erros.append(f'glossario[{i}] exige o campo usar')
        if not entrada.get('grego') and not entrada.get('termo'):
            erros.append(f'glossario[{i}] exige grego ou termo')
        if entrada.get('grego') and not entrada.get('transliteracao'):
            erros.append(f'glossario[{i}] com grego exige transliteracao')

    for i, item in enumerate(dados['rejeitados']):
        for campo in ('item', 'motivo', 'alternativa'):
            if not isinstance(item, dict) or not item.get(campo):
                erros.append(f'rejeitados[{i}] exige {campo}')

    formulas = dados['formulas_consolidadas']
    if not isinstance(formulas, dict):
        erros.append('formulas_consolidadas deve ser um objeto')
    else:
        for campo in ('saudacao', 'acao_de_gracas', 'bencao_de_paz'):
            if not isinstance(formulas.get(campo), str) or not formulas[campo].strip():
                erros.append(f'formulas_consolidadas.{campo} deve ser texto não vazio')

    ancoras = dados['ancoras']
    if not isinstance(ancoras, dict):
        erros.append('ancoras deve ser um objeto')
    else:
        base = ancoras.get('livros_base')
        if not isinstance(base, list) or not base:
            erros.append('ancoras.livros_base deve ser lista não vazia')
        elif any(not isinstance(l, dict) or not l.get('numero') or not l.get('nome')
                 for l in base):
            erros.append('cada livro-base exige numero e nome')
        amostras = ancoras.get('amostras')
        if not isinstance(amostras, list) or not amostras:
            erros.append('ancoras.amostras deve ser lista não vazia')
        else:
            for i, amostra in enumerate(amostras):
                if not isinstance(amostra, dict) or not amostra.get('referencia') \
                        or not amostra.get('texto') or not amostra.get('porque'):
                    erros.append(f'ancoras.amostras[{i}] exige referencia, texto e porque')
        por_genero = ancoras.get('por_genero')
        if not isinstance(por_genero, dict) or not all(
            isinstance(refs, list) for refs in por_genero.values()
        ):
            erros.append('ancoras.por_genero deve mapear género → lista de referências')

    for i, par in enumerate(dados['contrastes']):
        if not isinstance(par, dict) or not par.get('mau') or not par.get('bom'):
            erros.append(f'contrastes[{i}] exige mau e bom')

    if not isinstance(dados['aprovacoes'], list) or not dados['aprovacoes']:
        erros.append('aprovacoes deve ser lista não vazia')

    return erros


@lru_cache(maxsize=8)
def carregar(caminho: str | Path | None = None) -> dict:
    """Carrega e valida a memória de estilo. Falha alto se o schema for inválido.

    O resultado fica em cache por caminho: renderizar em cada pedido não
    reparseia o ficheiro. Passe um caminho explícito em testes.
    """
    arquivo = Path(caminho or CAMINHO_PADRAO)
    dados = json.loads(arquivo.read_text(encoding='utf-8'))
    erros = validar(dados)
    if erros:
        raise ValueError(
            f'Memória de estilo inválida em {arquivo}:\n- ' + '\n- '.join(erros)
        )
    return dados


# --------------------------------------------------------------------------
# Renderizadores: memória → fragmentos de prompt (determinísticos)
# --------------------------------------------------------------------------
def system_fragment(dados: dict) -> str:
    """Bloco de voz+regras para o system prompt da edição nova.

    Todos os provedores recebem este bloco igual, colado após o contrato
    operacional (formato de saída, rigor, comentário) que vive no código.
    """
    partes: list[str] = ['\n\nMEMÓRIA DE ESTILO (fonte única: modelos/estilo_bee.json). ']
    partes.append(dados['identidade'])
    partes.append('\n\nMÉTODO POR UNIDADE: ' + ' '.join(dados['metodo']))
    registro = dados['registro']
    partes.append(
        '\n\nVOZ E REGISTO: ' + registro['tratamento_plural'] + ' '
        + registro['tu_oracao_direta'] + ' ' + registro.get('nota_connosco', '')
    )
    regras = ' '.join(
        f'({i}) {regra["rotulo"]}: {regra["texto"]}'
        for i, regra in enumerate(dados['regras_duras'], start=1)
    )
    partes.append('\n\nREGRESSÕES PROIBIDAS (erros já observados; não repetir): ' + regras)
    aperto = ' '.join(
        f'({item["letra"]}) {item["rotulo"]}: {item["texto"]}'
        for item in dados['aperto']
    )
    partes.append('\n\nAPERTO ADICIONAL (calibração fina): ' + aperto)
    proibições = ' '.join(
        f'({chr(ord("a") + i)}) {texto}'
        for i, texto in enumerate(dados['proibicoes_globais'])
    )
    partes.append('\n\nPROIBIÇÕES GLOBAIS: ' + proibições)
    aprovacoes = '; '.join(dados['aprovacoes']) + '.'
    partes.append('\nAPROVAÇÕES EM QUE ESTA VOZ SE BASEIA: ' + aprovacoes)
    return ''.join(partes)


def _linha_glossario(entrada: dict, livro_numero: int | None) -> str:
    cabeca = (
        f'{entrada["grego"]} ({entrada["transliteracao"]})'
        if entrada.get('grego') else str(entrada['termo'])
    )
    linha = [f'- {cabeca} → usar {entrada["usar"]}']
    if entrada.get('sentido'):
        linha[0] += '. ' + entrada['sentido'].rstrip('. ')
    if entrada.get('nao_estender_a'):
        linha[0] += f'. A regra NÃO se estende automaticamente a {entrada["nao_estender_a"]}'
    reuso = entrada.get('contexto_reuso')
    livros_reuso = entrada.get('livros_reuso') or []
    if reuso:
        linha[0] += '. Reuso: ' + reuso.rstrip(';., ')
    if livro_numero is not None and livro_numero in livros_reuso:
        linha[0] += ' — palavra JÁ APROVADA neste livro; manter exatamente a mesma'
    if entrada.get('rejeitar'):
        linha[0] += f'. {entrada["rejeitar"].rstrip(".")}'
    if entrada.get('exemplo_aprovado'):
        linha[0] += f'. Exemplo aprovado: {entrada["exemplo_aprovado"]}'
    return linha[0] + '.'


def glossario_para_pedido(dados: dict, livro_numero: int | None = None) -> str:
    """Glossário + rejeitados enviados em cada pedido.

    Com ``livro_numero``, as entradas cuja decisão já foi aprovada nesse livro
    ganham a indicação «JÁ APROVADA neste livro», para o provedor repetir a
    mesma palavra (coesão intra-livro, como Filemom vv. 7/12/20).
    """
    linhas = ['GLOSSÁRIO DE DECISÕES DA MEMÓRIA DE ESTILO (minúsculas no corpo do texto):']
    linhas += [_linha_glossario(e, livro_numero) for e in dados['glossario']]
    linhas.append('PALAVRAS E FORMULAÇÕES REJEITADAS:')
    for item in dados['rejeitados']:
        linhas.append(
            f'- {item["item"]} — motivo: {item["motivo"].rstrip(".")} → '
            f'alternativa: {item["alternativa"].rstrip(".")}'
        )
    return '\n'.join(linhas)


def amostras_para_genero(dados: dict, genero: str = 'carta') -> str:
    """Âncoras few-shot aprovadas, filtradas por género literário.

    Se o género não existir em ``ancoras.por_genero``, entram todas as amostras
    (antes poucas âncoras certas do que nenhumas). Mantém-se curto de propósito:
    entra em todos os pedidos e as quotas gratuitas são apertadas.
    """
    ancoras = dados['ancoras']
    selecao = ancoras.get('por_genero', {}).get(genero)
    linhas = [
        'AMOSTRAS DE VOZ APROVADAS — referência de estilo. NÃO as copie nem as devolva; '
        'use-as só para calibrar registo, cadência e a separação entre versículo e nota:'
    ]
    for amostra in ancoras['amostras']:
        if selecao is not None and amostra['referencia'] not in selecao:
            continue
        linhas.append(
            f'- {amostra["referencia"]} «{amostra["texto"]}» — {amostra["porque"].rstrip(".")}.'
        )
    nomes = ', '.join(l['nome'] for l in ancoras['livros_base'])
    linhas.append(
        f'LIVROS-BASE desta voz: {nomes} (pilotos aprovados; edicoes/nova/livros_json).'
    )
    evitar = ', '.join(ancoras.get('evitar', []))
    linhas.append(
        f'EVITAR (regressões vistas): {evitar}; achatar cláusulas subordinadas em frases simples.'
    )
    linhas.append(
        'Mantenha este nível de naturalidade e cadência nos versículos pedidos; uma imagem '
        'clara vale mais do que uma explicação embutida no versículo.'
    )
    return '\n'.join(linhas)


def contrastes(dados: dict) -> str:
    """Pares mau→bom nascidos de regressões reais: o sinal anti-Almeida mais forte."""
    linhas = ['CONTRASTES (mau → bom; calibrar por eles, NÃO os copiar):']
    for par in dados['contrastes']:
        ref = par.get('mau_referencia', '')
        cabeca = f'- MAU {ref} ' if ref else '- MAU '
        linhas.append(f'{cabeca}«{par["mau"]}» → BOM «{par["bom"]}» ({par.get("licao", "")}).')
    return '\n'.join(linhas)


def formulas(dados: dict) -> str:
    """Fórmulas consolidadas: repeti-las iguais em todos os livros coesiona a edição."""
    f = dados['formulas_consolidadas']
    return (
        'FÓRMULAS CONSOLIDADAS (repetir estas formas iguais em todos os livros, pela '
        'coerência com os pilotos aprovados):\n'
        f'- Saudação: «{f["saudacao"]}»\n'
        f'- Ação de graças paulina: «{f["acao_de_gracas"]}»\n'
        f'- Bênção de paz: «{f["bencao_de_paz"]}»'
    )


def bloco_amostras(dados: dict, genero: str = 'carta') -> str:
    """Composição completa enviada no campo `amostras` do pedido."""
    return (
        amostras_para_genero(dados, genero)
        + '\n\n' + contrastes(dados)
        + '\n' + formulas(dados)
    )
