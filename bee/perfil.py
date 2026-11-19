"""Perfis de edição: separam a voz da tradução sem tocar na infraestrutura.

O projeto convive com duas linhas editoriais:

* ``legado`` — a edição original. Reutiliza, byte a byte, os prompts e o
  glossário que já estavam em ``bee/ia.py`` e ``bee/gerador.py``. É o perfil
  ativo quando nada é configurado, para que corridas antigas, testes e a fila
  em curso (João 19:13) não mudem de comportamento.

* ``nova`` — a voz descrita em ``docs/ESTILO_BEE.md`` (v0.5). Só entra quando
  ``BEE_EDICAO=nova``. A infraestrutura (JSON, checkpoints, validação,
  compilação e agendamento) é a mesma; muda apenas o que pedimos ao modelo.
  As regras de estilo desta edição NÃO vivem mais neste ficheiro: vêm da
  memória única ``modelos/estilo_bee.json``, renderizada por
  ``bee/memoria_estilo.py`` — assim todos os provedores recebem exatamente a
  mesma voz (P0 do sistema de convergência multi-provedor).

Regra de ouro do guia de estilo: *recomeçar a tradução, não a infraestrutura*.
Por isso este módulo NÃO altera caminhos nem formato de saída — só o texto das
instruções e do glossário. Isolar diretório, checkpoints e artefactos faz-se
apontando ``--dados``/``BEE_DADOS`` para outra pasta (ver ``docs/EDICAO_NOVA.md``).
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
import os

from . import memoria_estilo as _memoria_estilo


# --------------------------------------------------------------------------
# Perfil legado: exatamente o que já existia antes deste módulo.
# Importamos as constantes reais para garantir identidade total. Qualquer
# ajuste futuro aos prompts herdados continua a valer para o perfil legado.
# --------------------------------------------------------------------------
from .ia import PROMPT_REVISAO as _REVISAO_LEGADO, SYSTEM_PROMPT as _SISTEMA_LEGADO
from .gerador import GLOSSARIO_PADRAO as _GLOSSARIO_LEGADO


@dataclass(frozen=True)
class PerfilEdicao:
    """Um conjunto coerente de instruções de voz para uma edição."""

    nome: str
    system_prompt: str          # instrução de sistema principal
    prompt_revisao: str         # acrescentada no modo rascunho automático
    glossario: str              # vocabulário fixo enviado em cada pedido
    # Âncoras few-shot: versículos já aprovados pelo responsável, enviados em
    # cada pedido para calibrar a voz. Vazio no legado => nenhuma mudança.
    amostras: str = ''
    # Renderizador dinâmico do glossário por pedido (recebe o book_number e
    # acrescenta o contexto de reuso aprovado nesse livro). None no legado =>
    # devolve o glossário fixo, byte-idêntico ao de sempre.
    render_glossario: Callable[[int | None], str] | None = None

    def sistema(self, aplicar_revisao: bool = True) -> str:
        return self.system_prompt + (self.prompt_revisao if aplicar_revisao else '')

    def glossario_pedido(self, livro_numero: int | None = None) -> str:
        """Glossário enviado num pedido concreto.

        No legado é o texto fixo herdado; na edição nova é a memória de estilo
        renderizada, que marca as decisões já aprovadas no livro em tradução
        (coesão intra-livro: repetir a mesma palavra escolhida)."""
        if self.render_glossario is not None:
            return self.render_glossario(livro_numero)
        return self.glossario


_PERFIL_LEGADO = PerfilEdicao(
    nome='legado',
    system_prompt=_SISTEMA_LEGADO,
    prompt_revisao=_REVISAO_LEGADO,
    glossario=_GLOSSARIO_LEGADO,
)


# --------------------------------------------------------------------------
# Perfil novo: operacionaliza docs/ESTILO_BEE.md (v0.5).
#
# Divisão de responsabilidades decidida no P0 da convergência multi-provedor:
#   * o CONTRATO OPERACIONAL (quem traduz, formato de saída JSON, HTML limpo,
#     rigor/prova, modo rascunho) fica aqui no código — é infraestrutura de
#     pedido, igual para qualquer voz;
#   * TUDO o que define a VOZ (identidade, método por unidade, registo e lista
#     negra de arcaísmos, regressões proibidas, aperto de calibração, glossário
#     de decisões com contextos de reuso, palavras rejeitadas, fórmulas
#     consolidadas, âncoras aprovadas e contrastes mau→bom) vive em
#     modelos/estilo_bee.json e chega aqui renderizado por bee/memoria_estilo.
#     Editar a voz = editar o JSON; nenhum provedor recebe regras diferentes.
# --------------------------------------------------------------------------
_SISTEMA_NOVO = (
    'Você é um tradutor e exegeta trabalhando na NOVA edição da Bíblia de Estudo '
    'Epignósis (BEE), sob a voz editorial do documento interno ESTILO_BEE (v0.5). '
    'Traduza somente os textos-base originais fornecidos na mensagem do usuário '
    '(Westminster Leningrad Codex para o AT; SBLGNT e edições comparadas fornecidas '
    'para o NT), respeitando o trecho e a versificação indicados. '
    '\n\nVOZ E REGISTO: '
    'Clareza para ler, cadência para proclamar, profundidade para estudar. O impacto '
    'vem do texto, não de frases que lhe acrescentamos. Escreva português contemporâneo '
    'com voz própria, sem adotar uma região como norma e sem arcaísmos nem calques do '
    'inglês. Prefira verbos concretos e ordem natural; leia mentalmente em voz alta. '
    'A Almeida (ARC/NVI/KJA) é referência comparativa, nunca norma de redação nem fonte: '
    'não copie nenhuma tradução portuguesa existente. Preserve imagens, contrastes, '
    'repetições intencionais e ambiguidades cuja explicação pertence à nota. Não '
    'acrescente grandiloquência, conclusão doutrinária ou aplicação devocional ao versículo. '
    'Palavras adicionadas apenas para clareza ficam entre <i>...</i>. '
    '\n\nMÉTODO POR UNIDADE: '
    'Antes de fechar versículos, identifique quem fala, a quem, em que situação e com que '
    'propósito; preserve conectores decisivos. Divida frases longas só quando isso não '
    'alterar a lógica. Coerência teológica é ler a passagem inteira, não isolar o versículo. '
    'Em eleição, conserve os verbos e relações do original («predestinou», «atrair», '
    '«endurece») sem inserir qualificações de nenhum sistema teológico. Em poesia e profecia, '
    'mantenha imagens e números. Em violência, lamento ou intimidade, não suavize as vítimas '
    'nem dramatize; distinga quem narra, ordena, lamenta ou impreca. '
    '\n\nCOMENTÁRIO EXEGÉTICO (HTML limpo): '
    'Separe tradução de nota. O versículo traduz; a nota explica. Cada commentary tem três '
    'secções, cada uma começando em <p>: (1) Análise Léxica — forma original, transliteração '
    'e significado corrente no contexto; Strong serve de índice, não de prova de sentido; '
    '(2) Crítica Textual — compare apenas as edições efetivamente fornecidas; marque com [[ ]] '
    'somente diferenças observadas entre elas; distingue variante textual de opção de sintaxe; '
    '(3) Síntese Exegética concisa. Não faça da nota oração, declaração nem aplicação. '
    '\n\nRIGOR E PROVA: '
    'Não afirme ter consultado Nestle-Aland, BDB, Thayer ou manuscritos específicos que não '
    'lhe tenham sido fornecidos; escreva "definição não verificada em léxico" ou "sem variante '
    'verificada" quando não puder sustentar. Não invente códigos Strong, testemunhos, variantes '
    'nem alternativas; registe pendência em vez de inventar. Distinga crítica textual (leituras '
    'e testemunhos), sintaxe/semântica (como traduzer a leitura adotada) e exegese (a escolha no '
    'argumento da passagem). WLC e SBLGNT são edições textuais, não manuscritos individuais. '
    'No OSHB, ketiv e qere são leituras alternativas: identifique a escolhida, não as concatene. '
    '\n\nSAÍDA: '
    'Retorne estritamente um objeto JSON válido com a lista de versículos (verse, text, commentary). '
    'No comentário use apenas <p>, <br>, <b>, <strong>, <i>, <em>, <ul>, <ol>, <li>, <sup> e <sub>, '
    'sem atributos, sem <div> e sem HTML dentro de valores; nos textos bíblicos use só <i></i> quando '
    'necessário. Não omita nem acrescente números, não devolva introduções.'
)

_REVISAO_NOVA = (
    '\n\nMODO RASCUNHO AUTOMÁTICO (edição nova): esta saída não passou por consulta de léxicos '
    'durante a geração e não está aprovada para publicação. Não mencione BDB, Thayer, Nestle-Aland '
    'nem manuscritos específicos como consultados. Na Análise Léxica indique forma, transliteração '
    'e significado corrente; escreva "definição não verificada em léxico" quando não puder sustentar. '
    'Na Crítica Textual limite-se às edições fornecidas (por ex., SBLGNT e Textus Receptus) e escreva '
    '"sem variante verificada" quando não houver diferença; marque [[ ]] apenas diferenças observadas.'
)

# A memória de estilo é carregada UMA vez no arranque e validada contra o
# schema: um JSON malformado falha alto aqui (e nos testes), nunca em corrida.
_MEMORIA_ESTILO = _memoria_estilo.carregar()

_PERFIL_NOVO = PerfilEdicao(
    nome='nova',
    system_prompt=_SISTEMA_NOVO + _memoria_estilo.system_fragment(_MEMORIA_ESTILO),
    prompt_revisao=_REVISAO_NOVA,
    glossario=_memoria_estilo.glossario_para_pedido(_MEMORIA_ESTILO),
    amostras=_memoria_estilo.bloco_amostras(_MEMORIA_ESTILO),
    render_glossario=lambda livro_numero=None: _memoria_estilo.glossario_para_pedido(
        _MEMORIA_ESTILO, livro_numero),
)


PERFIS: dict[str, PerfilEdicao] = {
    _PERFIL_LEGADO.nome: _PERFIL_LEGADO,
    _PERFIL_NOVO.nome: _PERFIL_NOVO,
}

PERFIL_PADRAO = _PERFIL_LEGADO.nome
VARIAVEL_AMBIENTE = 'BEE_EDICAO'


def resolver_perfil(nome: str | None = None) -> PerfilEdicao:
    """Escolhe o perfil ativo.

    Ordem de resolução: argumento explícito > variável de ambiente > padrão.
    Um nome desconhecido é um erro de configuração, não uma queda silenciosa
    para o legado: misturar vozes numa edição corrompe a calibração.
    """
    escolhido = (nome or os.environ.get(VARIAVEL_AMBIENTE) or PERFIL_PADRAO).strip().lower()
    perfil = PERFIS.get(escolhido)
    if perfil is None:
        raise ValueError(
            f'Perfil de edição desconhecido: {escolhido!r}. '
            f'Use um de: {", ".join(sorted(PERFIS))}.'
        )
    return perfil
