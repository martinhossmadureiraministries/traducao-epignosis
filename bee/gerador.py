"""Orquestra geração em lotes e checkpoint imediatamente após cada lote válido.

`gerar_livros` é o percurso histórico (um livro inteiro por chamada). A produção
automática usa `gerar_fatia`, que trabalha com um orçamento de versículos e pode
parar a meio de um capítulo sem perder o que já foi guardado.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Callable, Protocol

from .arquivos import DadosInvalidos, ler_livro, ler_todos, salvar_livro, validar_versiculos
from .catalogo import Livro
from .fontes import ALINHAMENTO_VERSAO, FontesOriginais, MORPH_COMMIT, SBL_COMMIT, TR_COMMIT
from .ia import DerivaEstilo, RespostaInvalida, RespostaTruncada


# Vocabulário fixo pedido em todos os pedidos: evita que a mesma palavra grega
# apareça traduzida de formas diferentes em capítulos distantes.
GLOSSARIO_PADRAO = (
    'SENHOR (maiúsculas) para o Tetragrama; Senhor para Adonai; Cristo para Χριστός; '
    'graça para χάρις; fé para πίστις; arrependimento para μετάνοια; igreja para ἐκκλησία; '
    'evangelho para εὐαγγέλιον; Espírito Santo para τὸ πνεῦμα τὸ ἅγιον; '
    'manter “vocês” no plural e “tu” apenas em oração direta.'
)


class Motor(Protocol):
    provedor: str
    modelo: str

    def gerar(
        self, livro: Livro, capitulo: int, fontes: list[dict[str, Any]],
        estilo: dict[str, str] | None = None,
    ) -> list[dict[str, Any]]: ...


@dataclass
class Progresso:
    """O que uma fatia produziu; permite ao agendador decidir quando parar."""

    versos: int = 0
    capitulos: int = 0
    pedidos: int = 0
    # Capítulos (livro, capítulo) concluídos nesta fatia: a revisão por segunda
    # IA (P2) percorre exatamente esta lista depois da produção.
    capitulos_fechados: list[tuple[int, int]] = field(default_factory=list)
    livro: Livro | None = None
    capitulo: int | None = None
    concluido: bool = False        # não há mais trabalho em nenhum livro da fila
    alterado: bool = False
    motivos: list[str] = field(default_factory=list)
    # Provedor que respondeu nesta fatia: o agendador precisa de saber a quem
    # imputar os pedidos para respeitar o tecto diário de cada serviço.
    provedor: str | None = None
    # Lote onde a produção parou e quantas vezes já falhou: a repetição no mesmo
    # trabalho continua a partir daqui, em vez de recomeçar o capítulo.
    lote_inicio: int | None = None
    falhas_lote: int = 0
    # O modelo devolveu os versículos, mas o lote foi recusado na validação
    # (marcação inválida). Repetir com o mesmo pedido não resolve: o lote é
    # dividido de imediato em vez de gastar tentativas.
    lote_defeituoso: bool = False
    # O prazo interno do ciclo foi atingido: o que está gravado é válido e o
    # ciclo termina para o nuvem.py poder publicar antes de o job ser morto.
    tempo_esgotado: bool = False
    # Versículos que ficaram em quarentena nesta fatia (marcador gravado).
    quarentenados: int = 0
    # A fatia deve terminar de forma limpa depois de gravar o que tem (por
    # exemplo, atingiu o limite de versículos em quarentena).
    parar: bool = False

    def somar(self, outro: 'Progresso') -> None:
        self.versos += outro.versos
        self.capitulos += outro.capitulos
        self.pedidos += outro.pedidos
        self.capitulos_fechados.extend(outro.capitulos_fechados)
        self.concluido = outro.concluido
        self.alterado = self.alterado or outro.alterado
        self.tempo_esgotado = self.tempo_esgotado or outro.tempo_esgotado
        self.quarentenados += outro.quarentenados
        self.parar = self.parar or outro.parar
        self.livro, self.capitulo = outro.livro, outro.capitulo
        self.motivos.extend(outro.motivos)


@dataclass
class ConfigGeracao:
    versos_por_pedido: int = 8
    tentativas_conteudo: int = 3
    max_versos: int | None = None       # orçamento desta fatia
    estilo: bool = True                 # enviar contexto e glossário
    max_capitulos: int | None = None
    # Falhas já acumuladas no mesmo lote em execuções anteriores.
    falhas_anteriores: int = 0
    lote_retomar: int | None = None
    # Prazo em segundos para esta fatia (None = sem prazo). Ver nuvem.py.
    max_segundos: float | None = None
    # Depois de N versículos em quarentena, a fatia para: evita encher o livro
    # de marcadores quando o problema é do serviço inteiro, não de um versículo.
    max_quarentena: int = 3


PENDENTE_PREFIXO = '[Versículo pendente:'


def _placeholder_pendente(verso: int, motivo: str) -> dict[str, Any]:
    """Marcador explícito para um versículo que nenhum provedor conseguiu produzir.

    Não é texto bíblico: fica assim para o leitor saber que a tradução daquele
    versículo ainda falta, e para a quarentena poder ser revista depois.
    """
    return {
        'verse': verso,
        'text': f'{PENDENTE_PREFIXO} tradução ainda não produzida — {motivo}.]',
        'commentary': (
            '<p><b>Análise Léxica:</b> Pendente: o provedor devolveu conteúdo inválido '
            'para este versículo.</p>'
            '<p><b>Crítica Textual:</b> O texto-base existe; falta a tradução e o '
            'comentário. Versículo registado em quarentena para revisão.</p>'
            '<p><b>Síntese Exegética:</b> Pendente de nova tentativa ou revisão humana.</p>'
        ),
    }


def _registar_quarentena(
    caminho: Path, livro: Livro, capitulo: int, verso: int,
    motor: Motor, erro: str, status: str = 'pendente',
    marcas: dict[str, list[str]] | None = None,
    tentados: list[str] | None = None,
) -> None:
    """Acrescenta uma entrada a `livros_json/.bee/quarentena.json` de forma atómica.

    ``status='chumbado-estilo'`` + ``marcas`` identificam os versos que a porta
    de estilo recusou; o agendador usa isto para evitar repetir o provedor no
    mesmo capítulo (P1 da convergência multi-provedor)."""
    pasta = caminho.parent / '.bee'
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / 'quarentena.json'
    dados: dict[str, Any] = {'entries': []}
    if destino.exists():
        try:
            lido = json.loads(destino.read_text(encoding='utf-8'))
            if isinstance(lido, dict) and isinstance(lido.get('entries'), list):
                dados = lido
            elif isinstance(lido, list):
                dados = {'entries': lido}
        except (OSError, UnicodeError, ValueError):
            # Não apagar um ficheiro que não percebemos: guarda-o ao lado.
            try:
                os.replace(destino, destino.with_suffix('.json.invalido'))
            except OSError:
                pass
    entrada = {
        'reference': f'{livro.nome} {capitulo}:{verso}',
        'book': livro.numero,
        'chapter': capitulo,
        'verse': verso,
        'provider': getattr(motor, 'provedor', None),
        'model': getattr(motor, 'modelo', None),
        'error': erro,
        'at_utc': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'status': status,
    }
    if marcas:
        entrada['style_marks'] = marcas
    if tentados:
        # Todos os provedores que escreveram texto chumbado (não só o último):
        # é esta lista que a repetição do capítulo usa para os evitar a todos.
        entrada['providers_tried'] = list(tentados)
    dados['entries'].append(entrada)
    dados['updated_at_utc'] = datetime.now(timezone.utc).isoformat(timespec='seconds')
    temporario = destino.with_suffix('.json.tmp')
    temporario.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporario, destino)


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


def versoes_fonte(livro: Livro) -> dict[str, Any]:
    if livro.antigo_testamento:
        return {'versification': 'KJV/tradicional', 'alignment_version': ALINHAMENTO_VERSAO,
                'wlc_oshb_commit': MORPH_COMMIT}
    return {'versification': 'KJV/tradicional', 'alignment_version': ALINHAMENTO_VERSAO,
            'sblgnt_commit': SBL_COMMIT, 'textus_receptus_commit': TR_COMMIT}


def _trecho(versiculos: list[dict[str, Any]], limite: int = 420) -> str:
    texto = ' '.join(v['text'] for v in versiculos)
    return texto[-limite:]


def _contexto_estilo(
    dados: dict[str, Any], capitulo: int, parcial: list[dict[str, Any]],
) -> dict[str, str]:
    """Memória curta: últimos versículos já escritos, para coerência de vocabulário."""
    # O glossário vem do perfil de edição ativo. Sem BEE_EDICAO definido, o
    # perfil é o legado e devolve exatamente GLOSSARIO_PADRAO (sem mudança).
    # Importado aqui dentro para não fechar o ciclo gerador -> perfil -> gerador.
    from .perfil import resolver_perfil
    perfil = resolver_perfil()
    # Glossário por pedido: no legado é o texto fixo herdado (sem mudança); na
    # edição nova vem da memória de estilo e assinala as decisões já aprovadas
    # NO livro em tradução, para o provedor repetir a mesma palavra escolhida.
    numero = dados.get('book_number')
    estilo: dict[str, str] = {
        'glossario': perfil.glossario_pedido(int(numero) if numero is not None else None)
    }
    # Âncoras few-shot só existem no perfil novo; no legado a chave fica de fora
    # e o pedido enviado é exatamente o antigo.
    if perfil.amostras:
        estilo['amostras'] = perfil.amostras
    anteriores = parcial[-3:] if parcial else []
    if not anteriores:
        for anterior in range(capitulo - 1, 0, -1):
            if str(anterior) in dados.get('chapters', {}):
                anteriores = dados['chapters'][str(anterior)][-3:]
                break
    if anteriores:
        estilo['anterior'] = _trecho(anteriores)
    return estilo


def _gerar_capitulo(
    livro: Livro, capitulo: int, caminho: Path, dados: dict[str, Any],
    fontes_capitulo: list[dict[str, Any]], motor: Motor, config: ConfigGeracao,
    progresso: Progresso, prazo: float | None = None,
) -> None:
    def sem_tempo() -> bool:
        if prazo is None or time.monotonic() < prazo:
            return False
        progresso.tempo_esgotado = True
        progresso.motivos.append('prazo do ciclo atingido')
        return True

    chave = str(capitulo)
    total = livro.versos_por_capitulo[capitulo - 1]
    parcial = list(dados.get('in_progress', {}).get(chave, []))
    if parcial:
        print(f'A retomar {livro.nome} {capitulo} a partir do versículo {len(parcial) + 1}/{total}.', flush=True)
    else:
        print(f'A gerar {livro.nome} {capitulo} ({total} versículos)...', flush=True)
    limite_lote = min(config.versos_por_pedido, total)
    # Derivas de estilo vistas nas rondas deste capítulo: alimentam o motivo e o
    # registo de quarentena quando nenhum provedor passa na porta.
    acumulo_deriva: dict[int, set[str]] = {}
    autores_deriva: set[str] = set()   # provedores que escreveram texto chumbado
    while len(parcial) < total:
        if sem_tempo():
            return
        if config.max_versos is not None and progresso.versos >= config.max_versos:
            progresso.motivos.append('orçamento de versículos desta fatia atingido')
            return
        inicio = len(parcial) + 1
        fonte_atual = fontes_capitulo[inicio - 1]
        if fonte_atual.get('ausente'):
            parcial.append(_placeholder_ausente(inicio))
            _registrar(dados, capitulo, inicio, inicio, 'local', 'sem-fonte-WLC')
            _salvar_lote(caminho, dados, livro, capitulo, parcial, total)
            progresso.alterado = True
            print(f'  {livro.nome} {capitulo}:{inicio}: marcador de fonte ausente guardado.', flush=True)
            continue
        tamanho = min(limite_lote, total - inicio + 1)
        if config.max_versos is not None:
            restante = config.max_versos - progresso.versos
            if restante <= 0:
                return
            tamanho = min(tamanho, restante)
        # Nunca inclua o marcador de texto ausente no pedido à IA.
        for indice, item in enumerate(fontes_capitulo[inicio - 1:inicio - 1 + tamanho]):
            if item.get('ausente'):
                tamanho = indice
                break
        # Se o lote já vinha a falhar de ciclos anteriores, começa mais pequeno.
        if config.lote_retomar == inicio and config.falhas_anteriores and tamanho > 1:
            tamanho = 1
        falhas_unitarias = 0
        quarentena_feita = False
        while True:
            if sem_tempo():
                return
            selecionadas = fontes_capitulo[inicio - 1:inicio - 1 + tamanho]
            try:
                estilo = _contexto_estilo(dados, capitulo, parcial) if config.estilo else None
                versiculos = motor.gerar(livro, capitulo, selecionadas, estilo)
                # Uma resposta cortada no fim pode trazer menos versículos do
                # que os pedidos; os que vieram completos são válidos. Guardar
                # o que veio e continuar do seguinte evita repetir (e pagar)
                # o mesmo trecho até esgotar as tentativas.
                numeros = sorted({v['verse'] for v in versiculos})
                if numeros and numeros[0] == inicio:
                    esperados = list(range(inicio, inicio + len(numeros)))
                    if numeros != esperados:
                        raise RespostaInvalida('versículos fora de ordem')
                    if len(numeros) < tamanho:
                        print(
                            f'  Resposta parcial: {len(numeros)} de {tamanho} versículos; '
                            'a guardar os que vieram e a continuar do seguinte.',
                            file=sys.stderr, flush=True,
                        )
                    tamanho = len(numeros)
                    validar_versiculos(versiculos, range(inicio, inicio + tamanho), f'{livro.nome} {capitulo}')
                    break
                validar_versiculos(versiculos, range(inicio, inicio + tamanho), f'{livro.nome} {capitulo}')
                break
            except RespostaInvalida as exc:
                # Deriva de estilo NÃO se resolve dividindo o lote — a voz está
                # errada, o tamanho certo. Registam-se as marcas para a quarentena
                # guardar proveniência; o rodízio já rodou os provedores todos
                # internamente antes de isto chegar aqui.
                marcas_estilo = getattr(exc, 'marcas', None)
                if marcas_estilo:
                    for numero, marcas in marcas_estilo.items():
                        acumulo_deriva.setdefault(numero, set()).update(marcas)
                    tentados = getattr(exc, 'tentados', None) or []
                    ultimo = getattr(exc, 'provedor', None)
                    autores_deriva.update(p for p in list(tentados) + [ultimo] if p)
                # Resposta cortada por limite de tokens: dividir sempre resolve.
                # Conteúdo inválido (marcação, números): dividir uma vez e, se
                # voltar a falhar, não repetir o mesmo pedido.
                dividir = not marcas_estilo and tamanho > 1 and (
                    isinstance(exc, RespostaTruncada) or not progresso.lote_defeituoso
                )
                if dividir:
                    progresso.lote_defeituoso = True
                    tamanho = max(1, tamanho // 2)
                    limite_lote = min(limite_lote, tamanho)
                    print(
                        f'  Resposta inválida ou truncada ({exc}); a dividir o lote para {tamanho} versículo(s).',
                        file=sys.stderr, flush=True,
                    )
                else:
                    falhas_unitarias += 1
                    progresso.lote_inicio = inicio
                    progresso.falhas_lote = config.falhas_anteriores + falhas_unitarias
                    if falhas_unitarias >= config.tentativas_conteudo:
                        # Nenhum provedor/modelo produziu este versículo. Em vez de
                        # bloquear o capítulo inteiro (e a fila), grava um marcador
                        # explícito, regista a quarentena e segue para o seguinte.
                        if acumulo_deriva:
                            # O registo completo (versos e marcas) fica na
                            # quarentena; o marcador gravado no livro NÃO cita as
                            # formas proibidas, senão a guarda sinalizava o próprio
                            # marcador e chumbava para sempre.
                            resumo = '; '.join(
                                f'v.{n}: ' + ', '.join(sorted(marca))
                                for n, marca in sorted(acumulo_deriva.items())
                            )
                            erro_completo = (
                                f'deriva de estilo após {falhas_unitarias} ronda(s) '
                                f'pelos provedores ({resumo})'
                            )
                            motivo = (
                                f'deriva de estilo após {falhas_unitarias} ronda(s) '
                                'pelos provedores — versos e marcas em '
                                '.bee/quarentena.json (status chumbado-estilo)'
                            )
                            estado_quarentena = 'chumbado-estilo'
                            marcas_quarentena = {
                                str(n): sorted(marca) for n, marca in acumulo_deriva.items()
                            }
                        else:
                            erro_completo = motivo = (
                                f'resposta inválida após {falhas_unitarias} tentativa(s): {exc}'
                            )
                            estado_quarentena = 'pendente'
                            marcas_quarentena = None
                        parcial.append(_placeholder_pendente(inicio, motivo))
                        _registrar(dados, capitulo, inicio, inicio, 'local', 'quarentena')
                        _registar_quarentena(caminho, livro, capitulo, inicio, motor,
                                             erro_completo, status=estado_quarentena,
                                             marcas=marcas_quarentena,
                                             tentados=sorted(autores_deriva) or None)
                        _salvar_lote(caminho, dados, livro, capitulo, parcial, total)
                        progresso.alterado = True
                        progresso.quarentenados += 1
                        progresso.lote_inicio = None
                        progresso.falhas_lote = 0
                        quarentena_feita = True
                        print(
                            f'  {livro.nome} {capitulo}:{inicio}: em quarentena; '
                            'a continuar com o versículo seguinte.',
                            file=sys.stderr, flush=True,
                        )
                        if progresso.quarentenados >= config.max_quarentena:
                            progresso.motivos.append(
                                'limite de versículos em quarentena atingido'
                            )
                            progresso.parar = True
                        break
                    print(f'  A repetir {livro.nome} {capitulo}:{inicio}: {exc}', file=sys.stderr, flush=True)
        if quarentena_feita:
            if progresso.parar:
                return
            continue
        for versiculo, fonte in zip(versiculos, selecionadas):
            if fonte.get('aviso'):
                versiculo['commentary'] += (
                    '<p><b>Nota de fonte:</b> ' + escape(fonte['aviso']) + '</p>'
                )
        progresso.lote_inicio = None
        progresso.falhas_lote = 0
        parcial.extend(versiculos)
        progresso.versos += len(versiculos)
        progresso.pedidos += 1
        progresso.alterado = True
        progresso.provedor = motor.provedor
        _registrar(dados, capitulo, inicio, inicio + tamanho - 1, motor.provedor, motor.modelo)
        _salvar_lote(caminho, dados, livro, capitulo, parcial, total)
        print(f'  Guardados {livro.nome} {capitulo}:{inicio}-{inicio + tamanho - 1}.', flush=True)
    progresso.capitulos += 1
    progresso.capitulos_fechados.append((livro.numero, capitulo))
    print(f'Capítulo concluído: {livro.nome} {capitulo}.', flush=True)


def gerar_fatia(
    livros: list[Livro], diretorio: Path, fontes: FontesOriginais, motor: Motor,
    config: ConfigGeracao | None = None,
) -> Progresso:
    """Gera até `config.max_versos` versículos, em ordem, e devolve o que fez.

    Nada é enviado ao modelo se todos os capítulos da fila já estiverem completos.
    """
    config = config or ConfigGeracao()
    diretorio.mkdir(parents=True, exist_ok=True)
    existentes = ler_todos(diretorio)
    progresso = Progresso()
    try:
        return _percorrer(livros, diretorio, fontes, motor, config, existentes, progresso)
    except Exception as exc:
        # Quem chama precisa de saber onde a produção parou (lote em falta),
        # mesmo quando o gerador não devolve nada.
        exc.progresso = progresso
        raise


def _percorrer(
    livros: list[Livro], diretorio: Path, fontes: FontesOriginais, motor: Motor,
    config: ConfigGeracao, existentes: dict[int, Any], progresso: Progresso,
) -> Progresso:
    prazo = (
        time.monotonic() + config.max_segundos
        if config.max_segundos and config.max_segundos > 0
        else None
    )
    for livro in livros:
        caminho = diretorio / livro.nome_arquivo
        if livro.numero in existentes and not caminho.exists():
            raise DadosInvalidos(
                f'O livro {livro.numero} está noutro ficheiro. Renomeie-o para {livro.nome_arquivo} antes de gerar.'
            )
        dados = ler_livro(caminho, livro)
        pendentes = [c for c in range(1, livro.capitulos + 1) if str(c) not in dados['chapters']]
        if not pendentes:
            continue
        versoes = versoes_fonte(livro)
        anterior = dados.get('sources')
        # A guarda compara só as chaves canónicas de `versoes_fonte`. Os
        # dados podem trazer proveniência extra registada por outras
        # ferramentas (a migração das notas acrescenta a revisão CNTR e o
        # relatório de colação a `sources`), e isso não é «misturar
        # edições». A igualdade estrita do dicionário parou a produção em
        # 2026-11-20: nenhum livro gerava, com este mesmo erro.
        if anterior is not None and any(
            anterior.get(chave) != valor for chave, valor in versoes.items()
        ):
            raise DadosInvalidos(f'{livro.nome}: as versões das fontes diferem do checkpoint; revise antes de misturar edições.')
        dados['sources'] = {**(anterior or {}), **versoes}
        progresso.livro = livro
        for capitulo in pendentes:
            if prazo is not None and time.monotonic() >= prazo:
                progresso.tempo_esgotado = True
                progresso.motivos.append('prazo do ciclo atingido')
                progresso.concluido = False
                return progresso
            if config.max_versos is not None and progresso.versos >= config.max_versos:
                progresso.motivos.append('orçamento de versículos desta fatia atingido')
                progresso.concluido = False
                return progresso
            if config.max_capitulos is not None and progresso.capitulos >= config.max_capitulos:
                progresso.motivos.append('limite de capítulos atingido')
                progresso.concluido = False
                return progresso
            progresso.capitulo = capitulo
            fontes_capitulo = fontes.capitulo(livro, capitulo)
            _gerar_capitulo(
                livro, capitulo, caminho, dados, fontes_capitulo, motor, config,
                progresso, prazo,
            )
            if progresso.parar:
                progresso.concluido = False
                return progresso
            if progresso.tempo_esgotado:
                progresso.concluido = False
                return progresso
        progresso.capitulo = None
    progresso.concluido = True
    return progresso


def gerar_livros(
    livros: list[Livro], diretorio: Path, fontes: FontesOriginais,
    obter_motor: Callable[[], Motor], versos_por_pedido: int,
    tentativas_conteudo: int, max_capitulos: int | None = None,
) -> int:
    """Percurso histórico: um ou mais livros inteiros, criando o motor só se preciso."""
    existentes = ler_todos(diretorio)
    for livro in livros:
        caminho = diretorio / livro.nome_arquivo
        if livro.numero in existentes and not caminho.exists():
            raise DadosInvalidos(
                f'O livro {livro.numero} está noutro ficheiro. Renomeie-o para {livro.nome_arquivo} antes de gerar.'
            )
    gerados = 0
    motor: Motor | None = None
    for livro in livros:
        dados = ler_livro(diretorio / livro.nome_arquivo, livro)
        pendentes = [c for c in range(1, livro.capitulos + 1) if str(c) not in dados['chapters']]
        if not pendentes:
            continue
        if max_capitulos is not None and gerados >= max_capitulos:
            print(f'Limite de {max_capitulos} capítulo(s) atingido; progresso preservado.', flush=True)
            return gerados
        # Uma chave ausente deve falhar antes de descarregar as fontes.
        if motor is None:
            motor = obter_motor()
        config = ConfigGeracao(
            versos_por_pedido=versos_por_pedido, tentativas_conteudo=tentativas_conteudo,
            max_capitulos=None if max_capitulos is None else max_capitulos - gerados,
        )
        progresso = gerar_fatia([livro], diretorio, fontes, motor, config)
        gerados += progresso.capitulos
        if progresso.concluido:
            continue
        if progresso.motivos and 'limite de capítulos' in ' '.join(progresso.motivos):
            print(f'Limite de {max_capitulos} capítulo(s) atingido; progresso preservado.', flush=True)
            return gerados
    if gerados == 0:
        print('Todos os capítulos selecionados já estavam concluídos; nenhuma chamada de IA foi feita.', flush=True)
    return gerados
