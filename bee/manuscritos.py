"""Manuscritologia: leitura de transcrições MES e colação verificável.

Este módulo existe para que a BEE possa falar de **manuscritos** com a mesma
disciplina com que fala de edições. Três regras o governam:

1. **Nada de testemunho inventado.** Só se afirma a leitura de um manuscrito a
   partir de uma transcrição efetivamente lida, com ficheiro e revisão fixados.
   Onde a transcrição tem lacuna, diz-se lacuna; onde o editor supriu, diz-se
   suprido; onde um corretor alterou, registam-se as duas camadas.
2. **Edição não é manuscrito.** O aparato do SBLGNT compara edições impressas
   (WH, Treg, NA28, RP, NIV); a transcrição CNTR dá a leitura de cada suporte.
   Os dois níveis nunca se misturam num mesmo enunciado.
3. **Contagem não é genealogia.** O número de testemunhas que leem o mesmo não
   mede o número de decisões independentes: cópias descendem de cópias. Por
   isso a colação devolve *quem* lê o quê, e a decisão fica em
   ``docs/CRITICA_TEXTUAL.md``, com o raciocínio por unidade de variação.

O formato lido é o **MES** (*Manuscript Encoding Specification*) do Center for
New Testament Restoration (Alan Bunning), cuja gramática ANTLR está em
``MES.g4`` no acervo. Símbolos relevantes::

    \\  quebra de página     |  quebra de coluna   /  quebra de linha
    &  resto de linha        *  resto de versículo
    %  letra danificada      ^  letra faltante     ~  palavra suprida
    =  nomen sacrum          $  valor numérico     ⋄  divisão alternativa
    x{…} camada do escriba original   {…} camada vigente   a{…} b{…} corretores

Quebras de linha podem cair **dentro** de uma palavra (``σιλουα/νοσ``); por
isso são removidas sem inserir espaço. As ``nomina sacra`` são expandidas só
quando a forma é conhecida (tabela construída a partir das formas atestadas no
próprio livro) e a expansão fica sempre marcada como tal.

Módulo puro: só biblioteca padrão, sem rede. O acervo descarregado vive em
``.bee-cache/`` (ignorada pelo Git) por causa da licença CC BY-SA 4.0 — ver
``docs/CRITICA_TEXTUAL.md``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import difflib
from pathlib import Path
import re
import unicodedata

# --------------------------------------------------------------------------
# Normalização
# --------------------------------------------------------------------------
# Sigla crítica das edições impressas (⸀ ⸁ ⸂ ⸃ …) e marcas MES que não são letra.
_SIGLA_CRITICA = re.compile(r'[\u2e00-\u2e7f]')
_MARCAS_MES = re.compile(r'[{}&*%^_⋄$~+¶·˚]')
_QUEBRAS = re.compile(r'[\\/|]\d*')
_PONTUACAO = re.compile(r'[,.;:!?\'ʼʾ᾿\u0313\u0314\u0342\u00af]+')
_REFERENCIA = re.compile(r'^(\d{2})(\d{3})(\d{3})\s(.*)$')
# Ligaduras do MES que VALEM uma palavra: o sinal KAI (ϗ) é a conjunção καί.
# Ignorá-la faria o escriba parecer omitir um «e» que ele escreveu por sinal.
_LIGADURAS = {'ϗ': 'και', '\u03d7': 'και', 'ϛ': 'ϛ', '\ufffd': ''}
_ILEGIVEL = '\ufffd'  # REPLACEMENT: letra desconhecida no suporte

# Nomina sacra: forma abreviada (sem '=') → forma expandida, já normalizada.
# Construída a partir das formas atestadas em 2 Tessalonicenses no acervo CNTR
# consultado; acrescentar uma forma sem a atestar é conjetura, não transcrição.
NOMINA_SACRA = {
    'θσ': 'θεοσ', 'θυ': 'θεου', 'θω': 'θεω', 'θν': 'θεον',
    'κσ': 'κυριοσ', 'κυ': 'κυριου', 'κω': 'κυριω', 'κν': 'κυριον',
    'ισ': 'ιησουσ', 'ιυ': 'ιησου', 'ιν': 'ιησουν',
    'ιησ': 'ιησουσ', 'ιηυ': 'ιησου', 'ιην': 'ιησουν',
    'χσ': 'χριστοσ', 'χυ': 'χριστου', 'χω': 'χριστω', 'χν': 'χριστον',
    'πρσ': 'πατηρ', 'πρι': 'πατρι', 'πηρ': 'πατηρ',
    'πνσ': 'πνεματοσ', 'πνι': 'πνευματι', 'πνα': 'πνευμα',
    'ανσ': 'ανθρωποσ', 'ανοσ': 'ανθρωποσ', 'ανυ': 'ανθρωπου',
    'ανω': 'ανθρωπω', 'ανν': 'ανθρωπον', 'ανων': 'ανθρωπον',
    'υσ': 'υιοσ', 'υυ': 'υιου', 'υω': 'υιω', 'υν': 'υιον',
    'ουνου': 'ουρανου', 'ουνω': 'ουρανω', 'ουνον': 'ουρανον',
    'ιηλ': 'ισραηλ', 'δαδ': 'δαυιδ',
}


# Famílias flexionais das nomina sacra. Uma abreviatura não indica o caso: o
# escriba escreve =θω e o contexto decide se é θεῷ ou θεοῦ. Comparar a forma
# expandida com a da base sem esta neutralização inventaria variantes de caso
# («πατρὸς → πατήρ») que não existem. Só se aplica a palavras marcadas como
# nomen sacrum na testemunha: fora delas, uma diferença de caso É variante.
FAMILIAS = (
    ('THEOS', frozenset({'θεοσ', 'θεου', 'θεω', 'θεον'})),
    ('KYRIOS', frozenset({'κυριοσ', 'κυριου', 'κυριω', 'κυριον'})),
    ('IESOUS', frozenset({'ιησουσ', 'ιησου', 'ιησουν'})),
    ('CHRISTOS', frozenset({'χριστοσ', 'χριστου', 'χριστω', 'χριστον'})),
    ('PATER', frozenset({'πατηρ', 'πατροσ', 'πατρι', 'πατερα'})),
    ('PNEUMA', frozenset({'πνευμα', 'πνεματοσ', 'πνευματι', 'πνευματων'})),
    ('ANTHROPOS', frozenset({'ανθρωποσ', 'ανθρωπου', 'ανθρωπω', 'ανθρωπον'})),
    ('HYIOS', frozenset({'υιοσ', 'υιου', 'υιω', 'υιον'})),
    ('OURANOS', frozenset({'ουρανοσ', 'ουρανου', 'ουρανω', 'ουρανον'})),
    ('ISRAEL', frozenset({'ισραηλ'})),
    ('DAUID', frozenset({'δαυιδ'})),
)
_FAMILIA_DE = {forma: chave for chave, formas in FAMILIAS for forma in formas}


def canonica(forma: str) -> str:
    """Chave da família flexional de uma forma, ou a própria forma."""
    return _FAMILIA_DE.get(forma, forma)


def sem_diacriticos(texto: str) -> str:
    """Minúsculas, sem acentos/espíritos e com ς harmonizado em σ."""
    sem = ''.join(
        c for c in unicodedata.normalize('NFD', texto) if not unicodedata.combining(c)
    )
    return sem.lower().replace('ς', 'σ')


def normalizar(texto: str) -> str:
    """Forma comparável de uma palavra: só letras gregas, sem marcas nem sigla."""
    limpo = _QUEBRAS.sub('', texto)
    for ligadura, palavra in _LIGADURAS.items():
        limpo = limpo.replace(ligadura, ' ' + palavra + ' ' if palavra else ' ')
    limpo = _SIGLA_CRITICA.sub('', _MARCAS_MES.sub('', limpo))
    limpo = _PONTUACAO.sub('', limpo)
    limpo = re.sub(r'[^α-ω]', '', sem_diacriticos(limpo))
    return limpo


def normalizar_texto(texto: str) -> list[str]:
    """Lista de palavras normalizadas de um versículo (quebras não separam)."""
    sem_quebras = _QUEBRAS.sub('', texto)
    return [p for p in (normalizar(t) for t in sem_quebras.split()) if p]


def _expandir_nomen(forma: str) -> tuple[str, bool, bool]:
    """Expande uma nomen sacrum. Devolve (forma, era_nomen, expansao_duvidosa)."""
    if not forma.startswith('='):
        return normalizar(forma), False, False
    abreviatura = normalizar(forma.lstrip('=~+'))
    expandida = NOMINA_SACRA.get(abreviatura)
    if expandida is None:
        # Sem expansão segura: conserva a forma abreviada e assinala a dúvida.
        return abreviatura, True, True
    return expandida, True, False


@dataclass(frozen=True)
class Palavra:
    """Uma palavra tal como uma testemunha a apresenta."""

    forma: str                 # normalizada, comparável
    crua: str                  # como está na transcrição
    suprida: bool = False      # ~ : restituída pelo editor numa lacuna
    danificada: bool = False   # % : letra danificada no suporte
    faltante: bool = False     # ^ : letra que falta no suporte
    nomen_sacrum: bool = False
    expansao_duvidosa: bool = False
    ilegivel: bool = False     # \ufffd : letra desconhecida no suporte
    abreviada: bool = False    # ¯ : barra de abreviatura; faltam letras finais
    versiculo_alternativo: int | None = None  # ⋄N : pertence a outro versículo


@dataclass(frozen=True)
class Correcao:
    """Camadas de um trecho corrigido no próprio suporte.

    Uma camada presente e VAZIA significa que o texto foi apagado: ``x{και} {}``
    diz que o escriba original escreveu καί e a mão vigente já não o tem. Por
    isso as camadas vivem num dicionário — a presença da chave é a informação,
    não o conteúdo — e nunca se confunde "camada vazia" com "camada inexistente".
    """

    camadas: dict[str, tuple[Palavra, ...]] = field(default_factory=dict)

    @property
    def original(self) -> tuple[Palavra, ...]:
        """Leitura do escriba original (x); se não houver, a vigente."""
        return self.camadas.get('x', self.vigente)

    @property
    def vigente(self) -> tuple[Palavra, ...]:
        """Leitura atual do suporte: a camada MAIS Tardia presente.

        Ordem MES ``c > b > a > editada > original``: quando um corretor voltou
        ao texto, é a mão dele que o códice apresenta hoje. Em 2Ts 2:4 o
        Sinaiticus recebeu ϗ ὑπεραμενος na camada editada (itacismo) e o
        corretor ``a`` escreveu ϗ ὑπεραιρομενος; a leitura vigente é a do
        corretor, e o itacismo fica registado como etapa, não como texto.
        """
        for camada in ('c', 'b', 'a', ''):
            if camada in self.camadas:
                return self.camadas[camada]
        return self.camadas.get('x', ())

    @property
    def corretores(self) -> dict[str, tuple[Palavra, ...]]:
        return {c: v for c, v in self.camadas.items() if c in ('a', 'b', 'c')}


@dataclass(frozen=True)
class VersiculoTestemunha:
    """Leitura de um versículo numa testemunha, com o estado físico do suporte."""

    referencia: str            # '2:13'
    testemunha: str            # 'P92', '01', 'WH', …
    presente: bool             # False só quando a transcrição marca o verso ausente
    palavras: tuple[Palavra, ...] = ()
    correcoes: tuple[Correcao, ...] = ()
    cru: str = ''
    lacuna: bool = False
    suprido: bool = False
    texto_duvidoso: bool = False
    dividido: bool = False     # ⋄ : a testemunha divide o versículo de outro modo
    _originais: tuple[Palavra, ...] = field(default=(), compare=False)

    @property
    def texto(self) -> str:
        return ' '.join(part for p in self.palavras for part in p.forma.split())

    @property
    def ilegivel_original(self) -> bool:
        """True quando a camada do escriba original tem letra não identificada."""
        return any(
            p.ilegivel for c in self.correcoes for p in c.camadas.get('x', ())
        )

    def camada(self, qual: str) -> str:
        """Leitura reconstruída de uma camada, preservando a ordem do versículo.

        ``'vigente'`` devolve o estado atual do suporte (o que as edições citam
        quando não distinguem mãos); ``'original'`` devolve a mão do primeiro
        escriba, que é o que um aparato cita como \* (por ex., א\*).
        """
        return ' '.join(
            p.forma for p in (self._originais if qual == 'original' else self.palavras)
        )

    @property
    def leitura_original(self) -> str:
        return self.camada('original')

    @property
    def corrigida(self) -> bool:
        """True quando alguma camada de correção alterou o texto vigente.

        É a única fonte desta informação: não há campo ``corrigido`` a poder
        divergir do que as camadas dizem."""
        return any(c.original != c.vigente for c in self.correcoes)


def _palavra(token: str) -> Palavra:
    alternativa = None
    busca = re.search(r'⋄(\d+)', token)
    if busca:
        alternativa = int(busca.group(1))
    forma, nomen, duvidosa = _expandir_nomen(token.strip())
    return Palavra(
        forma=forma,
        crua=token.strip(),
        suprida='~' in token,
        danificada='%' in token,
        faltante='^' in token,
        nomen_sacrum=nomen,
        expansao_duvidosa=duvidosa,
        ilegivel=_ILEGIVEL in token,
        abreviada='\u00af' in token,
        versiculo_alternativo=alternativa,
    )


_CORRECAO = re.compile(r'(?P<camada>[xabc])?\{(?P<conteudo>[^{}]*)\}')


# Um segmento de correção MES é uma sequência de edições ADJACENTES:
# ``(ORIGINAL edit SPACE)? edit (SPACE CORRECTOR edit)*`` (MES.g4). Por isso
# x{…} {} é UMA correção com duas camadas, nunca duas correções separadas.
_BLOCO_CORRECAO = re.compile(
    r'(?:[xabc])?\{[^{}]*\}(?:\s+(?:[xabc])?\{[^{}]*\})*'
)


def _segmentos(texto: str) -> list[object]:
    """Separa palavras livres de grupos de correção, NA ORDEM do manuscrito.

    Grupos contíguos (``x{και} {}``, ``x{…} {…} a{…}``) pertencem à mesma
    correção e formam uma única camada composta; palavras fora de chaves são
    texto corrente. A ordem é preservada porque uma correção no meio do
    versículo não pode migrar para o fim.
    """
    itens: list[object] = []
    posicao = 0
    for bloco in _BLOCO_CORRECAO.finditer(texto):
        anterior = texto[posicao:bloco.start()].strip()
        if anterior:
            itens.extend(_palavra(t) for t in anterior.split())
        camadas: dict[str, list[Palavra]] = {}
        for encontro in _CORRECAO.finditer(texto[bloco.start():bloco.end()]):
            camada = encontro.group('camada') or ''
            camadas.setdefault(camada, []).extend(
                _palavra(t) for t in encontro.group('conteudo').split()
            )
        itens.append(Correcao(camadas={c: tuple(v) for c, v in camadas.items()}))
        posicao = bloco.end()
    resto = texto[posicao:].strip()
    if resto:
        itens.extend(_palavra(t) for t in resto.split())
    return itens


def ler_testemunha(caminho: Path, livro: int | str) -> dict[str, VersiculoTestemunha]:
    """Lê uma transcrição MES do CNTR para um livro.

    ``livro`` é o número CNTR (40=Mateus … 53=2 Tessalonicenses … 66=Apocalipse).
    Serve tanto para manuscritos (``class 1``) como para os textos críticos do
    acervo (``critical texts``): ambos usam a mesma referência de 8 dígitos.
    """
    prefixo = f'{int(livro):02d}'
    resultado: dict[str, VersiculoTestemunha] = {}
    testemunha = caminho.stem
    for linha in caminho.read_text(encoding='utf-8').splitlines():
        if linha[:2] != prefixo or not linha[2:8].isdigit():
            continue
        encontro = _REFERENCIA.match(linha)
        if not encontro:
            continue
        _, capitulo, verso, corpo = encontro.groups()
        corpo = corpo.strip()
        referencia = f'{int(capitulo)}:{int(verso)}'
        # Um versículo marcado só com '-' está ausente no suporte.
        if re.fullmatch(r'-~?', corpo):
            resultado[referencia] = VersiculoTestemunha(
                referencia=referencia, testemunha=testemunha, presente=False, cru=corpo,
            )
            continue
        itens = _segmentos(corpo)
        vigentes: list[Palavra] = []
        originais: list[Palavra] = []
        correcoes: list[Correcao] = []
        for item in itens:
            if isinstance(item, Correcao):
                correcoes.append(item)
                vigentes.extend(item.vigente)
                originais.extend(item.original)
            else:
                vigentes.append(item)
                originais.append(item)
        resultado[referencia] = VersiculoTestemunha(
            referencia=referencia,
            testemunha=testemunha,
            presente=True,
            palavras=tuple(vigentes),
            _originais=tuple(originais),
            correcoes=tuple(correcoes),
            cru=corpo,
            lacuna=bool(re.search(r'[~&*%^]', corpo)),
            suprido='~' in corpo,
            texto_duvidoso='[' in corpo or ']' in corpo,
            dividido='⋄' in corpo,
        )
    return resultado


# --------------------------------------------------------------------------
# Colação
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Divergencia:
    """Diferença de uma testemunha face à leitura-base, com o seu motivo."""

    testemunha: str
    estado: str                # 'identica' | 'divergente' | 'ausente'
    diferenca: str = ''
    leitura: str = ''
    fisico: tuple[str, ...] = ()

    def linha(self) -> str:
        fisico = (' [' + ','.join(self.fisico) + ']') if self.fisico else ''
        return f'{self.testemunha:>11} {self.estado:<10}{fisico} {self.diferenca}'.rstrip()


def diferenca(base: list[str], leitura: list[str]) -> str:
    """Alinhamento sequencial (não conjuntos): ordem e repetição são variantes.

    Uma transposição (``αὐτοὺς ἡμᾶς`` / ``ἡμᾶς αὐτοὺς``) é variante real, e uma
    palavra repetida não pode anular outra. Por isso usa-se ``difflib`` sobre as
    sequências, nunca a diferença de conjuntos.
    """
    partes: list[str] = []
    comparador = difflib.SequenceMatcher(None, base, leitura, autojunk=False)
    for operacao, i1, i2, j1, j2 in comparador.get_opcodes():
        if operacao == 'equal':
            continue
        trecho_base = ' '.join(base[i1:i2])
        trecho_leitura = ' '.join(leitura[j1:j2])
        if operacao == 'delete':
            partes.append(f'-[{trecho_base}]')
        elif operacao == 'insert':
            partes.append(f'+[{trecho_leitura}]')
        else:
            partes.append(f'{trecho_base} → {trecho_leitura}')
    return '; '.join(partes) or 'ordem diferente'


def harmonizar(base: list[str], palavras: tuple[Palavra, ...]) -> tuple[list[str], list[str]]:
    """Neutraliza artefactos de transcrição antes de contar variantes.

    Duas passagens, ambas conservadoras — o que não puder ser resolvido com
    certeza continua a contar como divergência e é devolvido em ``notas`` para
    revisão humana:

    1. **Nomina sacra.** A abreviatura não fixa o caso; compara-se pela família
       flexional (``FAMILIAS``) e, coincidindo a família, adota-se a forma da
       base. Só para palavras marcadas como nomen sacrum na testemunha.
    2. **Abreviatura por barra (macron).** ``ημω̄`` por ἡμῶν não é variante:
       completa-se a palavra quando a forma base começa pela forma abreviada na
       posição alinhada.

    Devolve a leitura harmonizada e as notas do que foi resolvido ou ficou por
    resolver. Sem este passo a colação enche-se de falsas divergências que
    escondem as variantes reais — e uma nota cheia de ruído não serve ninguém.
    """
    leitura = [p.forma for p in palavras]
    notas: list[str] = []

    # Passagem 1: famílias flexionais das nomina sacra.
    base_canonica = [canonica(forma) for forma in base]
    leitura_canonica = [
        canonica(forma) if palavras[i].nomen_sacrum else forma
        for i, forma in enumerate(leitura)
    ]
    comparador = difflib.SequenceMatcher(None, base_canonica, leitura_canonica, autojunk=False)
    substituir: dict[int, str] = {}
    for operacao, i1, i2, j1, j2 in comparador.get_opcodes():
        if operacao != 'equal':
            continue
        for deslocamento in range(i2 - i1):
            indice = j1 + deslocamento
            if palavras[indice].nomen_sacrum and leitura[indice] != base[i1 + deslocamento]:
                substituir[indice] = base[i1 + deslocamento]
                notas.append(f'ns:{leitura[indice]}={base[i1 + deslocamento]}')
    leitura = [substituir.get(i, forma) for i, forma in enumerate(leitura)]

    # Passagem 2: abreviaturas por barra, alinhadas na leitura já harmonizada.
    comparador = difflib.SequenceMatcher(None, base, leitura, autojunk=False)
    substituir = {}
    for operacao, i1, i2, j1, j2 in comparador.get_opcodes():
        if operacao != 'replace' or (i2 - i1) != (j2 - j1):
            continue
        for deslocamento in range(i2 - i1):
            indice = j1 + deslocamento
            if not palavras[indice].abreviada:
                continue
            forma_base, curta = base[i1 + deslocamento], leitura[indice]
            if curta and forma_base.startswith(curta):
                substituir[indice] = forma_base
                notas.append(f'abrev:{curta}={forma_base}')
            else:
                notas.append(f'abrev_por_resolver:{curta}?{forma_base}')
    leitura = [substituir.get(i, forma) for i, forma in enumerate(leitura)]

    for palavra in palavras:
        if palavra.expansao_duvidosa:
            notas.append(f'expansao_duvidosa:{palavra.crua}')
        if palavra.ilegivel:
            notas.append(f'ilegivel:{palavra.crua}')
    return leitura, sorted(set(notas))


def colacionar(
    base: list[str], fontes: dict[str, VersiculoTestemunha | None]
) -> list[Divergencia]:
    """Compara uma leitura-base normalizada com cada testemunha do versículo."""
    achados: list[Divergencia] = []
    for nome, versiculo in fontes.items():
        if versiculo is None or not versiculo.presente:
            achados.append(Divergencia(nome, 'ausente'))
            continue
        leitura, abreviaturas = harmonizar(base, versiculo.palavras)
        fisico = tuple(
            rotulo for rotulo, ativo in (
                ('lacuna', versiculo.lacuna),
                ('suprido', versiculo.suprido),
                ('corrigido', versiculo.corrigida),
                ('texto_duvidoso', versiculo.texto_duvidoso),
                ('divisao_alternativa', versiculo.dividido),
                ('ilegivel_original', versiculo.ilegivel_original),
            ) if ativo
        )
        nota_abreviatura = (' ‹' + ','.join(abreviaturas) + '›') if abreviaturas else ''
        if leitura == base:
            achados.append(Divergencia(
                nome, 'identica', leitura=versiculo.texto, fisico=fisico,
                diferenca=nota_abreviatura.strip(),
            ))
        else:
            achados.append(Divergencia(
                nome, 'divergente',
                diferenca=(diferenca(base, leitura) + nota_abreviatura).strip(),
                leitura=' '.join(leitura), fisico=fisico,
            ))
    return achados


def unidades_de_variacao(
    referencias: list[str],
    base: dict[str, list[str]],
    testemunhas: dict[str, dict[str, VersiculoTestemunha]],
) -> dict[str, list[Divergencia]]:
    """Divergências por versículo, só onde há pelo menos uma testemunha."""
    resultado: dict[str, list[Divergencia]] = {}
    for referencia in referencias:
        fontes = {
            nome: dados.get(referencia) for nome, dados in testemunhas.items()
        }
        achados = colacionar(base.get(referencia, []), fontes)
        if any(a.estado == 'divergente' for a in achados):
            resultado[referencia] = achados
    return resultado
