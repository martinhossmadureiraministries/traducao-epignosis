"""Revisão de voz por segunda IA (P2 da convergência multi-provedor).

Cada capítulo FECHADO na edição nova é revisto por um provedor DIFERENTE do
autor (ver ``bee/papeis.py``), SEMPRE — a escolha do utilizador foi revisão
automática em tudo, com estas proteções de quota:

* só os TEXTOS viajam no pedido (sem comentários) e em lotes de 40 versículos;
* o revisor responde apenas com EMENDAS pontuais — nada de reescrever por gosto;
* cada emenda proposta passa pela porta de estilo ANTES de ser aplicada (uma
  "correção" que introduzisse «vós» seria rejeitada);
* falha de rede/quota/JSON num revisor passa ao seguinte; se todos falharem, o
  original fica intacto (a revisão nunca perde uma tradução).

Tudo fica auditável em ``livros_json/.bee/revisoes.json`` e na ``history`` do
livro (entradas ``revisao:<provedor>``). Legado não usa nada disto.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from . import papeis
from .arquivos import carregar_json, salvar_livro
from .catalogo import POR_NUMERO
from .inspetor import analisar_texto
from .memoria_estilo import carregar as carregar_memoria
from .memoria_estilo import system_fragment

# Tamanho do lote de revisão: capítulos grandes (p.ex. Salmo 119) partem-se.
VERSO_POR_REVISAO = 40

Diario = Callable[[str], None] | Callable[[str, str], None]


def sistema_revisor(memoria: dict[str, Any]) -> str:
    """Identidade do REVISOR DE VOZ: aplica a memória, não reescreve por gosto."""
    return (
        'Você é o REVISOR DE VOZ da edição nova da Bíblia de Estudo Epignósis (BEE). '
        'Outro provedor traduziu; você NÃO retraduz. O seu único trabalho é fazer o '
        'texto aprovado cumprir a memória de estilo abaixo, com emendas MÍNIMAS.\n\n'
        + system_fragment(memoria) + '\n\n'
        'CONTRATO DA REVISÃO:\n'
        '(1) Emende APENAS o que violar a memória: arcaísmos/lista negra, hesitação '
        'dentro do verso («ou seja»), fórmulas consolidadas diferentes das aprovadas, '
        'correntes de genitivos tipo Almeida, erros de concordância/gralhas.\n'
        '(2) Se o verso já cumpre, NÃO o devolva — preferência de estilo não é defeito. '
        'Preserve imagens, ambiguidades deliberadas e a estrutura do argumento; nunca '
        'acrescente sentido, grandiloquência ou aplicação.\n'
        '(3) Mantenha o tratamento decidido no capítulo («vocês» ou «tu») e repita as '
        'FÓRMULAS CONSOLIDADAS exatamente como estão na memória.\n'
        '(4) Responda ESTRITAMENTE {"emendas":[{"verse":N,"texto":"...","razao":"curta"}]} '
        'com os mesmos números recebidos, ou {"emendas":[]} quando nada há a mudar. '
        'Sem introduções, sem versículos extra, sem tocar nos comentários.'
    )


def pedido_capitulo(livro_nome: str, capitulo: int, versos: list[dict[str, Any]]) -> str:
    """Mensagem do pedido: só referências e textos — mínimo de tokens."""
    compacto = [{'verse': v['verse'], 'text': v.get('text', '')} for v in versos]
    inicio, fim = compacto[0]['verse'], compacto[-1]['verse']
    return (
        f'Reveja {livro_nome} {capitulo}:{inicio}-{fim} contra a memória de estilo. '
        'Devolva só as emendas necessárias no formato combinado.\n'
        + json.dumps(compacto, ensure_ascii=False, separators=(',', ':'))
    )


def validar_emendas(versiculos: list[dict[str, Any]], bruto: Any) -> tuple[list[dict], list[str]]:
    """Filtra a resposta do revisor: só entra emenda válida E limpa na porta.

    Devolve (emendas aceites, problemas descartados). Uma emenda que introduza
    uma falha dura («vós», «ou seja»…) é rejeitada — a correção não pode dérivar.
    """
    aceites: list[dict] = []
    problemas: list[str] = []
    itens = bruto.get('emendas') if isinstance(bruto, dict) else bruto
    if not isinstance(itens, list):
        return [], ['resposta do revisor sem lista de emendas']
    por_numero = {int(v['verse']): v for v in versiculos if isinstance(v.get('verse'), int)
                  or (isinstance(v.get('verse'), str) and str(v['verse']).isdigit())}
    for item in itens:
        if not isinstance(item, dict):
            problemas.append('emenda não é um objeto')
            continue
        try:
            numero = int(item.get('verse'))
        except (TypeError, ValueError):
            problemas.append(f'emenda sem número de versículo: {item!r}')
            continue
        novo = str(item.get('texto') or '').strip()
        razao = str(item.get('razao') or 'sem razão indicada')
        atual = por_numero.get(numero)
        if atual is None:
            problemas.append(f'v.{numero}: versículo não existe no capítulo')
            continue
        if novo == str(atual.get('text', '')).strip():
            continue  # "emenda" igual ao texto: silêncio, não problema
        if not novo:
            problemas.append(f'v.{numero}: emenda vazia')
            continue
        duros = analisar_texto(novo)['duros']
        if duros:
            problemas.append(f'v.{numero}: emenda rejeitada pela porta ({", ".join(duros)})')
            continue
        aceites.append({'verse': numero, 'texto': novo, 'razao': razao})
    return aceites, problemas


def aplicar_emendas(versiculos: list[dict[str, Any]], emendas: list[dict]) -> list[dict]:
    """Nova lista de versículos com os textos emendados; comentários intocados."""
    novos = [dict(v) for v in versiculos]
    por_numero = {v['verse']: v for v in novos}
    for emenda in emendas:
        alvo = por_numero.get(emenda['verse'])
        if alvo is not None:
            alvo['text'] = emenda['texto']
    return novos


def _agora_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def registar_caderno(dados_dir: Path, entradas: list[dict]) -> None:
    """Acrescenta emendas aplicadas a `.bee/revisoes.json` (auditoria da 2.ª IA)."""
    if not entradas:
        return
    pasta = dados_dir / '.bee'
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / 'revisoes.json'
    caderno: dict[str, Any] = {'entries': []}
    if destino.exists():
        try:
            lido = json.loads(destino.read_text(encoding='utf-8'))
            if isinstance(lido, dict) and isinstance(lido.get('entries'), list):
                caderno = lido
        except (OSError, UnicodeError, ValueError):
            pass
    caderno['entries'].extend(entradas)
    caderno['updated_at_utc'] = _agora_iso()
    temporario = destino.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(caderno, ensure_ascii=False, indent=2) + '\n',
                          encoding='utf-8')
    temporario.replace(destino)


def _autores_do_capitulo(history: list[dict], capitulo: int) -> set[str]:
    """Provedores que GERARAM este capítulo (entradas locais/de revisão não contam)."""
    autores: set[str] = set()
    for entrada in history:
        if not isinstance(entrada, dict) or entrada.get('chapter') != capitulo:
            continue
        provedor = str(entrada.get('provider') or '')
        if provedor and provedor != 'local' and not provedor.startswith('revisao:'):
            autores.add(provedor)
    return autores


def rever_capitulos_fechados(
    dados_dir: Path,
    capitulos: list[tuple[int, int]],
    motores: list[Any],
    diario: Diario | None = None,
    memoria: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Revê cada (livro, capítulo) fechado com uma segunda IA. Nunca perde texto.

    ``motores`` são objetos com ``provedor``, ``modelo`` e ``rever(sistema, msg)``
    (o ``MotorIA`` cumpre; testes passam falsos). Devolve um resumo para o diário.
    """
    def escrever(texto: str, nivel: str = 'info') -> None:
        if diario is None:
            return
        try:
            diario(texto, nivel)          # Diário do agendador aceita nível
        except TypeError:
            diario(texto)                 # callbacks simples aceitam só o texto

    memoria = memoria if memoria is not None else carregar_memoria()
    sistema = sistema_revisor(memoria)
    por_livro: dict[int, list[int]] = {}
    for livro_numero, capitulo in capitulos:
        por_livro.setdefault(livro_numero, []).append(capitulo)

    saltados: list[str] = []
    resumo: dict[str, Any] = {'capitulos_revistos': 0, 'emendas': 0, 'saltados': saltados}
    for livro_numero, caps in sorted(por_livro.items()):
        livro = POR_NUMERO.get(livro_numero)
        caminho = next(dados_dir.glob(f'{livro_numero}_*.json'), None)
        if livro is None or caminho is None or not caminho.exists():
            continue
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        historia = dados.get('history') or []
        alterado = False
        for capitulo in caps:
            versiculos = dados.get('chapters', {}).get(str(capitulo))
            if not versiculos:
                continue
            autores = _autores_do_capitulo(historia, capitulo)
            autor_unico = next(iter(autores)) if len(autores) == 1 else None
            ativos = [m.provedor for m in motores if getattr(m, 'provedor', None)]
            ordem = papeis.revisores_disponiveis(ativos, autor_unico)
            candidatos: list[Any] = []
            vistos: set[str] = set()
            for nome in ordem:
                for motor_candidato in motores:
                    if getattr(motor_candidato, 'provedor', None) == nome and nome not in vistos:
                        candidatos.append(motor_candidato)
                        vistos.add(nome)
                        break
            if not candidatos:
                resumo['saltados'].append(f'{livro.nome} {capitulo}: nenhum revisor disponível')
                escrever(f'Revisão de {livro.nome} {capitulo} saltada: nenhum provedor ativo.', 'aviso')
                continue
            emendas_cap: list[dict] = []
            problemas_cap: list[str] = []
            revisor_usado = None
            for motor in candidatos:
                try:
                    pedacos = [versiculos[i:i + VERSO_POR_REVISAO]
                               for i in range(0, len(versiculos), VERSO_POR_REVISAO)]
                    todas: list[dict] = []
                    problemas: list[str] = []
                    for pedaco in pedacos:
                        bruto = carregar_json(motor.rever(
                            sistema, pedido_capitulo(livro.nome, capitulo, pedaco)))
                        aceites, descartes = validar_emendas(pedaco, bruto)
                        todas.extend(aceites)
                        problemas.extend(descartes)
                    emendas_cap, problemas_cap, revisor_usado = todas, problemas, motor
                    break  # primeiro revisor que responde fecha a revisão
                except Exception as exc:  # quota/rede/JSON → próximo revisor
                    escrever(f'Revisor {getattr(motor, "provedor", "?")} falhou em '
                             f'{livro.nome} {capitulo} ({type(exc).__name__}); a tentar outro.', 'aviso')
                    continue
            if revisor_usado is None:
                resumo['saltados'].append(f'{livro.nome} {capitulo}: todos os revisores falharam')
                escrever(f'{livro.nome} {capitulo} ficou sem revisão (original preservado).', 'aviso')
                continue
            resumo['capitulos_revistos'] += 1
            rotulo = f'{revisor_usado.provedor}/{getattr(revisor_usado, "modelo", "?")}'
            if emendas_cap:
                dados['chapters'][str(capitulo)] = aplicar_emendas(versiculos, emendas_cap)
                historia.append({
                    'chapter': capitulo, 'verse_from': emendas_cap[0]['verse'],
                    'verse_to': emendas_cap[-1]['verse'],
                    'provider': f'revisao:{revisor_usado.provedor}',
                    'model': getattr(revisor_usado, 'modelo', ''),
                    'generated_at_utc': _agora_iso(),
                })
                registar_caderno(dados_dir, [{
                    'book': livro_numero, 'chapter': capitulo,
                    'verse': e['verse'], 'texto': e['texto'], 'razao': e['razao'],
                    'reviewer': revisor_usado.provedor, 'at_utc': _agora_iso(),
                } for e in emendas_cap])
                alterado = True
                resumo['emendas'] += len(emendas_cap)
                escrever(f'Revisão de {livro.nome} {capitulo} por {rotulo}: '
                         f'{len(emendas_cap)} emenda(s) aplicada(s).'
                         + (f' Descartes: {"; ".join(problemas_cap)}.' if problemas_cap else ''))
            else:
                escrever(f'Revisão de {livro.nome} {capitulo} por {rotulo}: '
                         'capítulo aprovado sem emendas.')
        if alterado:
            salvar_livro(caminho, dados, livro)
    return resumo
