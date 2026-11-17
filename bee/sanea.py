"""HTML simples: validar sem rejeitar o que o modelo escreve de boa-fé.

Duas coisas aprendidas em produção:

(a) modelos envolvem os parágrafos num `<div>`, e o validador rejeitava o lote
    inteiro por causa de uma tag sem significado — com o serviço instável, o
    lote era dividido até 1 versículo e a produção parava;
(b) o conteúdo de `<script>` era analisado como HTML, e um `x < y` dentro do
    script podia "fechar" tags verdadeiras.

A política tem dois níveis:

* `estrito=True` (porta de entrada, ao ler uma resposta): recusa tudo o que não
  seja explicitamente permitido — scripts, iframes, comentários, atributos e
  tags desconhecidas. Contentores neutros (`div`, `span`) são aceites porque não
  mudam o texto e são convertidos em `<p>` ao guardar.
* `estrito=False` (limpeza ao guardar): converte o que se puder converter e
  remove o resto, para que um ficheiro antigo ou escrito à mão não fique preso.
"""
from __future__ import annotations

from html import escape, unescape
import re

TEXTO = frozenset({'i'})
COMENTARIO = frozenset({'p', 'br', 'b', 'strong', 'i', 'em', 'ul', 'ol', 'li', 'sup', 'sub'})

# Contentores sem significado nos módulos do MyBible: o conteúdo fica.
NEUTROS = frozenset({'div', 'span', 'section', 'article', 'center', 'blockquote', 'figure', 'figcaption'})
VAZIAS = frozenset({'br', 'img', 'hr', 'input', 'meta', 'link', 'source', 'wbr'})
PROIBIDAS = frozenset({'script', 'style', 'iframe', 'object', 'embed', 'svg', 'math', 'template', 'noscript'})
_ELEMENTO = re.compile(r'<(/?)([A-Za-z][A-Za-z0-9]*)((?:[^>"\']|"[^"]*"|\'[^\']*\')*)>', re.S)


class ErroHTML(ValueError):
    """Marcação que a porta estrita recusa."""


def _recusar(estrito: bool, mensagem: str, texto: str, inicio: int, fim: int) -> str | None:
    """Devolve o texto a emitir ou levanta ErroHTML, conforme o nível."""
    if estrito:
        raise ErroHTML(mensagem)
    return escape(unescape(texto[inicio:fim]))


def _normalizar(texto: str, permitidas: frozenset[str], estrito: bool) -> str:
    if not isinstance(texto, str):
        raise ErroHTML('o texto não é uma cadeia de caracteres.')
    # Comentários, declarações e instruções nunca têm lugar num comentário BEE.
    for padrao, mensagem in (
        (r'<!--.*?-->', 'Comentários HTML não são permitidos.'),
        (r'<!(?:DOCTYPE[^>]*|\[CDATA\[.*?\]\])>', 'Declarações HTML não são permitidas.'),
        (r'<\?.*?\?>', 'Instruções de processamento HTML não são permitidas.'),
    ):
        achado = re.search(padrao, texto, re.S | re.I)
        if achado:
            if estrito:
                raise ErroHTML(mensagem)
            texto = texto[:achado.start()] + texto[achado.end():]

    saida: list[str] = []
    pilha: list[str] = []
    pos = 0
    while True:
        achado = _ELEMENTO.search(texto, pos)
        if achado is None:
            saida.append(escape(unescape(texto[pos:])))
            break
        antes = texto[pos:achado.start()]
        if antes:
            saida.append(escape(unescape(antes)))
        pos = achado.end()
        fecho, nome, attrs = achado.group(1) == '/', achado.group(2).lower(), achado.group(3).strip()

        if nome in PROIBIDAS:
            if fecho:
                continue
            if estrito:
                raise ErroHTML(f'Tag HTML ou atributo não permitido: <{nome}>.')
            fim = re.search(rf'</\s*{nome}\s*>', texto[pos:], re.I)
            pos = pos + (fim.end() if fim else len(texto) - pos)
            continue
        if attrs and not (nome in NEUTROS and re.fullmatch(r'class\s*=\s*("[^"]*"|\'[^\']*\')', attrs)):
            texto_bruto = _recusar(estrito, f'Tag HTML ou atributo não permitido: <{nome}>.',
                                   texto, achado.start(), achado.end())
            if texto_bruto is not None:
                # No modo tolerante o atributo desaparece e a tag fica sem ele,
                # mas só se for permitida; caso contrário o texto é escapado.
                if nome not in permitidas and nome not in NEUTROS:
                    saida.append(escape(unescape(achado.group(0))))
                    continue
            continue
        if nome in NEUTROS:
            continue  # sai a marcação, fica o conteúdo
        if nome not in permitidas:
            texto_bruto = _recusar(estrito, f'Tag HTML ou atributo não permitido: <{nome}>.',
                                   texto, achado.start(), achado.end())
            if texto_bruto is not None:
                saida.append(texto_bruto)
            continue
        if fecho:
            if nome in VAZIAS:
                continue
            if nome not in pilha:
                if estrito:
                    raise ErroHTML(f'Tag HTML mal fechada: </{nome}>.')
                continue
            while pilha and pilha[-1] != nome:
                fechada = pilha.pop()
                saida.append(f'</{fechada}>')
            pilha.pop()
            saida.append(f'</{nome}>')
            continue
        if nome in VAZIAS:
            if nome == 'br':
                saida.append('<br>')
            continue
        if nome == 'p' and 'p' in pilha:
            continue  # <p> dentro de <p>: o HTML não permite; ignora-se o interno
        pilha.append(nome)
        saida.append(f'<{nome}>')
    while pilha:
        saida.append(f'</{pilha.pop()}>')
    return ''.join(saida)


def limpar(texto: str, comentario: bool, estrito: bool = False) -> str:
    """Devolve o HTML com apenas tags permitidas, todas fechadas."""
    limpo = _normalizar(texto, COMENTARIO if comentario else TEXTO, estrito)
    if comentario:
        # Linhas soltas separadas por <br> continuam a ser parágrafos legíveis.
        limpo = re.sub(r'(?:<br>\s*){2,}', '</p><p>', limpo)
    return limpo
