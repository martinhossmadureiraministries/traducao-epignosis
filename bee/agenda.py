"""Agendador da produção automática: ritmo, janela diária, orçamento e diário.

O estado vive ao lado dos dados (`livros_json/.bee/`), nunca no Git, e é escrito
de forma atómica. Um ciclo é: gerar uma fatia com orçamento → compilar → registar.
Se algo falhar, o ciclo seguinte tenta de novo; nada é apagado.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import date, datetime, time, timedelta, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import Any

from .arquivos import ler_todos
from .catalogo import LIVROS
from .compilador import ErroCompilacao, compilar
from .gerador import ConfigGeracao, Progresso, gerar_fatia
from .ia import Rodizio, VERSOS_POR_PEDIDO_PADRAO
from .fontes import FontesOriginais
from .rede import ClienteHTTP


FUSO_PADRAO = 'UTC'


# --------------------------------------------------------------------------
# Estado persistente


def _agora() -> datetime:
    return datetime.now(timezone.utc)


def _iso(momento: datetime) -> str:
    return momento.astimezone(timezone.utc).isoformat(timespec='seconds')


def escrever_atomico(caminho: Path, texto: str) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(prefix=f'.{caminho.name}.', suffix='.bee-tmp', dir=caminho.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as arquivo:
            arquivo.write(texto)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, caminho)
    finally:
        try:
            os.unlink(temporario)
        except FileNotFoundError:
            pass


@dataclass
class Estado:
    """Tudo o que o agendador precisa de recordar entre ciclos."""

    criado_utc: str = field(default_factory=lambda: _iso(_agora()))
    ciclos: int = 0
    versos_total: int = 0
    dias: dict[str, dict[str, Any]] = field(default_factory=dict)
    ultimo_ciclo_utc: str | None = None
    ultima_compilacao_utc: str | None = None
    ultima_compilacao_build: str | None = None
    falhas_seguidas: int = 0
    ultimo_erro: str | None = None
    # Provedores que o rodízio já marcou como esgotados hoje.
    exaustos_em: str | None = None
    exaustos: list[str] = field(default_factory=list)
    # Onde a produção parou (livro/capítulo/versículo) e quantas vezes o mesmo
    # lote já falhou. Permite repetir só o lote em falta no ciclo seguinte, em
    # vez de recomeçar o capítulo e gastar quota nos versículos já guardados.
    lote_livro: int | None = None
    lote_capitulo: int | None = None
    lote_versiculo: int | None = None
    lote_falhas: int = 0

    def dia(self, chave: str) -> dict[str, Any]:
        registo = self.dias.setdefault(chave, {
            'pedidos': 0, 'pedidos_ok': 0, 'versos': 0, 'capitulos': 0, 'falhas': 0,
            'aberto': True, 'fechado_em_utc': None,
            # Pedidos e versículos por provedor. Sem isto, esgotar a Groq
            # calava o dia inteiro e o Gemini — que ainda tinha quota — nunca
            # era usado. Cada serviço tem o seu próprio tecto.
            'por_provedor': {},
        })
        # Estados antigos não têm o contador de tentativas bem-sucedidas.
        registo.setdefault('pedidos_ok', 0)
        return registo

    def orcamento(self, chave: str, provedor: str) -> dict[str, int]:
        """Contadores do dia para um provedor (criados à primeira utilização)."""
        return self.dia(chave).setdefault('por_provedor', {}).setdefault(
            provedor, {'pedidos': 0, 'versos': 0},
        )

    def gastou(self, chave: str, provedor: str, pedidos: int, versos: int) -> None:
        registo = self.orcamento(chave, provedor)
        registo['pedidos'] += pedidos
        registo['versos'] += versos

    def para_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def de_json(cls, dados: Any) -> 'Estado':
        if not isinstance(dados, dict):
            return cls()
        conhecidos = {campo for campo in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in dados.items() if k in conhecidos})


def carregar_estado(caminho: Path) -> Estado:
    if not caminho.exists():
        return Estado()
    try:
        return Estado.de_json(json.loads(caminho.read_text(encoding='utf-8')))
    except (OSError, ValueError):
        # Um estado ilegível nunca deve impedir a produção: começa-se de novo,
        # mas os JSON dos capítulos permanecem intactos.
        return Estado()


def salvar_estado(caminho: Path, estado: Estado) -> None:
    escrever_atomico(caminho, json.dumps(estado.para_json(), ensure_ascii=False, indent=2, sort_keys=True) + '\n')


# --------------------------------------------------------------------------
# Diário legível


class Diario:
    """Linha por acontecimento em Markdown, adequada para ler no telefone."""

    def __init__(self, caminho: Path):
        self.caminho = caminho

    LIMITE_BYTES = 300_000

    def escrever(self, texto: str, nivel: str = 'info') -> None:
        marca = {'info': '', 'aviso': '**AVISO** ', 'erro': '**ERRO** '}.get(nivel, '')
        self._rodar()
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        with self.caminho.open('a', encoding='utf-8', newline='\n') as arquivo:
            arquivo.write(f'- {_iso(_agora())} — {marca}{texto}\n')

    def _rodar(self) -> None:
        """Mantém o diário legível: guarda as últimas linhas quando fica grande."""
        try:
            if self.caminho.stat().st_size <= self.LIMITE_BYTES:
                return
            linhas = self.caminho.read_text(encoding='utf-8').splitlines()
        except OSError:
            return
        escrever_atomico(
            self.caminho,
            '# Diário da produção automática da BEE (continuação)\n\n'
            + '\n'.join(linhas[-1000:]) + '\n',
        )

    def resumo(self, texto: str) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        if not self.caminho.exists():
            escrever_atomico(
                self.caminho,
                '# Diário da produção automática da BEE\n\n'
                'Este ficheiro é escrito pelo agendador. O progresso real está nos JSON e nos módulos.\n\n',
            )
        with self.caminho.open('a', encoding='utf-8', newline='\n') as arquivo:
            arquivo.write(f'\n## {_iso(_agora())}\n\n{texto}\n')


# --------------------------------------------------------------------------
# Janela diária e ritmo


def _data_local(momento: datetime, fuso: Any) -> date:
    return momento.astimezone(fuso).date()


def dentro_da_janela(momento: datetime, fuso: Any, inicio: int, fim: int) -> bool:
    """Horas locais inteiras; `inicio == fim` significa 24 horas por dia."""
    if inicio == fim:
        return True
    hora = momento.astimezone(fuso).hour
    if inicio < fim:
        return inicio <= hora < fim
    return hora >= inicio or hora < fim


def segundos_ate_abrir(momento: datetime, fuso: Any, inicio: int) -> float:
    local = momento.astimezone(fuso)
    alvo = datetime.combine(local.date(), time(hour=inicio), tzinfo=local.tzinfo)
    if alvo <= local:
        alvo += timedelta(days=1)
    return max(30.0, (alvo - local).total_seconds())


@dataclass
class ConfigAgenda:
    """Parâmetros de um ciclo de produção automática."""

    intervalo_min: float = 5.0
    max_versos: int = 6
    max_pedidos: int = 3
    pedidos_por_dia: int = 400
    versos_por_dia: int = 0            # 0: sem teto próprio
    # Tecto de pedidos de cada provedor, por dia. Vazio: usa pedidos_por_dia
    # para todos (comportamento antigo).
    tectos_por_provedor: dict[str, int] = field(default_factory=dict)
    hora_inicio: int = 0
    hora_fim: int = 24
    fuso: str = FUSO_PADRAO
    lote_global: int | None = None
    versos_por_pedido: dict[str, int] = field(default_factory=dict)
    tentativas_conteudo: int = 3
    estilo: bool = True
    compilar: bool = True
    pausa_rede: float = 1.0
    tentativas_rede: int = 3
    timeout: float = 180.0
    max_tokens: int = 4096
    revisao: bool = True
    max_falhas_seguidas: int = 6
    # Prazo interno do ciclo, em segundos (0 = sem limite). O nuvem.py usa isto
    # para parar a geração antes de o GitHub matar o job; o trabalho guardado é
    # então compilado e publicado.
    max_tempo_ciclo: float = 0.0

    def lote(self, provedor: str) -> int:
        return (
            self.versos_por_pedido.get(provedor)
            or self.lote_global
            or VERSOS_POR_PEDIDO_PADRAO.get(provedor, 8)
        )


# --------------------------------------------------------------------------
# Fila de trabalho


# As oito fases do docs/EDITORIAL.md, na ordem editorial aprovada.
FASES = [
    [640, 500],
    [480, 470, 490, 510],
    [10, 20],
    [230, 240, 220, 250, 260],
    [520, 530, 540, 550, 560, 570, 580, 590, 600, 610, 620, 630, 650, 660, 670, 680, 690, 700, 710, 720],
    [30, 40, 50, 60, 70, 80, 90, 100, 110, 120, 130, 140, 150, 160, 190],
    [290, 300, 310, 330, 340, 350, 360, 370, 380, 390, 400, 410, 420, 430, 440, 450, 460],
    [730],
]


_ORDEM_PLANO = [numero for fase in FASES for numero in fase]
_RANK_PLANO = {numero: i for i, numero in enumerate(_ORDEM_PLANO)}
POR_NUMERO = {livro.numero: livro for livro in LIVROS}


def livros_na_fila(apenas: list[int] | None = None, ordem: str = 'plano') -> list[Any]:
    """Ordem de produção.

    - 'plano': as oito fases do docs/EDITORIAL.md (Filemom primeiro).
    - 'canonica': Génesis a Apocalipse.
    - 'curtos': livros com menos capítulos primeiro (empate pela ordem do plano).
    - `apenas`: mantém a ordem pedida pelo utilizador.
    """
    if apenas:
        vistos: list[Any] = []
        for numero in apenas:
            livro = POR_NUMERO.get(numero)
            if livro is not None and livro not in vistos:
                vistos.append(livro)
        return vistos
    if ordem == 'canonica':
        return list(LIVROS)
    if ordem == 'curtos':
        return sorted(LIVROS, key=lambda l: (l.capitulos, _RANK_PLANO.get(l.numero, 999)))
    return sorted(LIVROS, key=lambda l: (_RANK_PLANO.get(l.numero, 999), l.numero))


def proximo_trabalho(livros: list[Any], diretorio: Path) -> tuple[Any, int] | None:
    """Primeiro capítulo ainda incompleto, para mostrar no diário."""
    dados = ler_todos(diretorio)
    for livro in livros:
        completos = dados.get(livro.numero, {}).get('chapters', {})
        for capitulo in range(1, livro.capitulos + 1):
            if str(capitulo) not in completos:
                return livro, capitulo
    return None


# --------------------------------------------------------------------------
# Ciclo


@dataclass
class QuotaDeTodosEsgotada(RuntimeError):
    pass


@dataclass
class ResultadoCiclo:
    acao: str                    # 'gerado', 'nada', 'adormecer', 'parar'
    detalhe: str = ''
    progresso: Progresso | None = None
    espera: float | None = None
    resumo_compilacao: dict[str, Any] | None = None


class Agendador:
    def __init__(
        self, dados: Path, saida: Path, cache: Path, estado: Estado,
        config: ConfigAgenda, diario: Diario, fuso: Any, motores: list[Any],
        fontes: FontesOriginais, rede: ClienteHTTP,
    ):
        self.dados = dados
        self.saida = saida
        self.cache = cache
        self.estado = estado
        self.config = config
        self.diario = diario
        self.fuso = fuso
        self.motores = motores
        self.fontes = fontes
        self.rede = rede
        self._rodizio: Rodizio | None = None

    # -- rodízio de provedores ------------------------------------------------
    def _obter_rodizio(self) -> Rodizio:
        if self._rodizio is not None:
            return self._rodizio
        hoje = _data_local(_agora(), self.fuso).isoformat()
        if self.estado.exaustos_em != hoje:
            self.estado.exaustos_em = hoje
            self.estado.exaustos = []
        exaustos = set(self.estado.exaustos)
        ativos = [m for m in self.motores if m.provedor not in exaustos]
        if not ativos:
            raise QuotaDeTodosEsgotada('todos os provedores configurados já esgotaram a quota hoje')
        for motor in ativos:
            # Avisos de rede (novas tentativas, 503, 429) ficam no diário com data.
            motor.log = lambda texto: self.diario.escrever(texto, 'aviso')
        rodizio = Rodizio(ativos, registar=self.diario.escrever)
        # Porta obrigatória (P1): na edição nova, cada lote é inspecionado antes
        # de ser aceite (deriva → outro provedor no mesmo lote) e os provedores
        # já chumbados num capítulo ficam evitados na repetição. O legado não
        # liga nada disto — comportamento exatamente igual ao anterior.
        from .perfil import resolver_perfil
        if resolver_perfil().nome == 'nova':
            from . import porta
            rodizio.inspetor = porta.inspecionar_versos
            mapa = porta.exclusoes_de_estilo(self.dados / '.bee' / 'quarentena.json')
            if mapa:
                rodizio.filtro_provedores = (
                    lambda livro, capitulo: mapa.get((livro.numero, capitulo), frozenset())
                )
                self.diario.escrever(
                    f'Porta de estilo ativa; {len(mapa)} capítulo(s) com provedores '
                    'evitados por deriva anterior.'
                )
        self._rodizio = rodizio
        return self._rodizio

    def _registar_lote(self, progresso: Progresso | None) -> None:
        """Guarda onde a produção parou para o próximo ciclo continuar daí."""
        if progresso is not None and progresso.lote_inicio is not None:
            livro = progresso.livro
            # `progresso.capitulo` fica preenchido durante a fatia; se a falha
            # aconteceu no fim de um livro, mantém-se o último capítulo válido.
            if livro is not None and progresso.capitulo:
                self.estado.lote_livro = livro.numero
                self.estado.lote_capitulo = progresso.capitulo
                self.estado.lote_versiculo = progresso.lote_inicio
                # `falhas_lote` já inclui as falhas dos ciclos anteriores.
                self.estado.lote_falhas = progresso.falhas_lote or (self.estado.lote_falhas + 1)
                if self.estado.lote_falhas > 6:
                    self.diario.escrever(
                        f'O lote {livro.nome} {progresso.capitulo}:{progresso.lote_inicio} falhou '
                        f'{self.estado.lote_falhas} vezes; a saltar para o versículo seguinte.',
                        'aviso',
                    )
                    self.estado.lote_versiculo = None
                    self.estado.lote_falhas = 0
        elif progresso is not None and progresso.versos:
            self.estado.lote_livro = None
            self.estado.lote_capitulo = None
            self.estado.lote_versiculo = None
            self.estado.lote_falhas = 0

    def _registar_exaustos(self) -> None:
        if self._rodizio is None:
            return
        for nome in self._rodizio.esgotados():
            if nome not in self.estado.exaustos:
                self.estado.exaustos.append(nome)

    def _contagem_rede(self) -> dict[str, int]:
        """Tentativas HTTP acumuladas no cliente, se ele as souber contar."""
        contar = getattr(self.rede, 'pedidos_por_provedor', None)
        if contar is None:
            return {}
        try:
            return dict(contar())
        except Exception:  # um contador extra nunca deve parar a produção
            return {}

    def _registar_consumo(
        self, chave: str, antes: dict[str, int], progresso: Progresso | None,
    ) -> None:
        """Regista no orçamento o que foi realmente tentado, não só o que passou.

        Em 17/11 o estado dizia zero pedidos enquanto a Groq devolvia 429 em
        série: só os lotes guardados contavam. O tecto diário era, por isso,
        uma ficção. O contador do ClienteHTTP inclui as tentativas falhadas.
        """
        depois = self._contagem_rede()
        deltas = {
            nome: depois.get(nome, 0) - antes.get(nome, 0)
            for nome in set(antes) | set(depois)
        }
        total = sum(max(0, delta) for delta in deltas.values())
        dia = self.estado.dia(chave)
        if total:
            dia['pedidos'] += total
            for nome, delta in deltas.items():
                if delta > 0:
                    self.estado.orcamento(chave, nome)['pedidos'] += delta
        else:
            # Sem contador de rede (motores falsos nos testes), usa os pedidos
            # que o gerador conseguiu completar.
            sucesso = progresso.pedidos if progresso else 0
            dia['pedidos'] += sucesso
            usado = (progresso.provedor if progresso else None) or (
                getattr(self.motores[0], 'provedor', None) if self.motores else None
            )
            if sucesso and usado:
                self.estado.orcamento(chave, usado)['pedidos'] += sucesso
        if progresso is not None:
            dia['pedidos_ok'] += progresso.pedidos
            usado = progresso.provedor or (
                getattr(self.motores[0], 'provedor', None) if self.motores else None
            )
            if usado:
                self.estado.orcamento(chave, usado)['versos'] += progresso.versos

    # -- decisões de calendário ----------------------------------------------
    def decidir(self, momento: datetime) -> ResultadoCiclo | None:
        """Devolve None quando é hora de gerar, ou o motivo para esperar."""
        chave = _data_local(momento, self.fuso).isoformat()
        dia = self.estado.dia(chave)
        if not dentro_da_janela(momento, self.fuso, self.config.hora_inicio, self.config.hora_fim):
            if dia['aberto']:
                dia['aberto'] = False
                dia['fechado_em_utc'] = _iso(momento)
                self.diario.escrever(f'Janela diária encerrada; retoma às {self.config.hora_inicio:02d}:00 ({self.config.fuso}).')
            espera = segundos_ate_abrir(momento, self.fuso, self.config.hora_inicio)
            return ResultadoCiclo('adormecer', 'fora da janela diária', espera=espera)
        if not dia['aberto']:
            dia['aberto'] = True
            self.diario.escrever('Janela diária reaberta.')
        if dia['pedidos'] >= self.config.pedidos_por_dia:
            return ResultadoCiclo(
                'parar', f"orçamento diário de {self.config.pedidos_por_dia} pedidos atingido", espera=None,
            )
        # Cada provedor tem o seu tecto: esgotar a Groq não deve calar o
        # Gemini, que ainda tem quota. Antes, o primeiro a esgotar-se parava o
        # dia inteiro e os restantes ficavam por usar.
        if self.config.tectos_por_provedor:
            usados = dia.setdefault('por_provedor', {})
            # Só contam os provedores que têm tecto próprio E já foram usados.
            # Antes, se o único provedor usado fosse o Gemini (sem tecto de
            # tokens/dia), `all([])` era True e o dia parava com a mensagem
            # vazia “orçamento diário de cada provedor atingido ()”.
            com_tecto = [
                (nome, tecto) for nome, tecto in self.config.tectos_por_provedor.items()
                if nome in usados
            ]
            todos_esgotados = bool(com_tecto) and all(
                usados[nome].get('pedidos', 0) >= tecto for nome, tecto in com_tecto
            )
            if todos_esgotados:
                detalhe = ', '.join(
                    f'{nome}: {usados[nome]["pedidos"]}/{tecto}'
                    for nome, tecto in self.config.tectos_por_provedor.items()
                    if nome in usados
                )
                return ResultadoCiclo(
                    'parar', f'orçamento diário de cada provedor atingido ({detalhe})',
                    espera=None,
                )
        if self.config.versos_por_dia and dia['versos'] >= self.config.versos_por_dia:
            return ResultadoCiclo(
                'parar', f"orçamento diário de {self.config.versos_por_dia} versículos atingido",
            )
        if self.estado.falhas_seguidas >= self.config.max_falhas_seguidas:
            return ResultadoCiclo(
                'parar',
                f"{self.estado.falhas_seguidas} falhas seguidas; última: {self.estado.ultimo_erro}",
            )
        return None

    # -- um ciclo -------------------------------------------------------------
    def ciclo(self, livros: list[Any]) -> ResultadoCiclo:
        momento = _agora()
        decisao = self.decidir(momento)
        if decisao is not None:
            return decisao
        chave = _data_local(momento, self.fuso).isoformat()
        dia = self.estado.dia(chave)
        antes_rede = self._contagem_rede()
        self.estado.ciclos += 1
        self.estado.ultimo_ciclo_utc = _iso(momento)

        try:
            motor = self._obter_rodizio()
        except QuotaDeTodosEsgotada as exc:
            self.diario.escrever(f'{exc}; a aguardar a reabertura da janela diária.', 'aviso')
            return ResultadoCiclo(
                'adormecer', str(exc),
                espera=segundos_ate_abrir(momento, self.fuso, self.config.hora_inicio),
            )
        config = ConfigGeracao(
            versos_por_pedido=self.config.lote(motor.provedor),
            tentativas_conteudo=self.config.tentativas_conteudo,
            max_versos=self.config.max_versos,
            estilo=self.config.estilo,
            falhas_anteriores=self.estado.lote_falhas,
            lote_retomar=self.estado.lote_versiculo,
            max_segundos=self.config.max_tempo_ciclo or None,
        )
        try:
            progresso = gerar_fatia(livros, self.dados, self.fontes, motor, config)
        except Exception as exc:  # qualquer falha é registada e o ciclo seguinte tenta de novo
            dia['falhas'] += 1
            self.estado.falhas_seguidas += 1
            self.estado.ultimo_erro = f'{type(exc).__name__}: {exc}'
            self._registar_lote(getattr(exc, 'progresso', None))
            self._registar_consumo(chave, antes_rede, getattr(exc, 'progresso', None))
            self._registar_exaustos()
            self.diario.escrever(f'Ciclo {self.estado.ciclos} falhou: {exc}', 'erro')
            return ResultadoCiclo('nada', f'falha: {exc}', progresso=None)
        self.estado.falhas_seguidas = 0
        self._registar_lote(progresso)
        dia['versos'] += progresso.versos
        dia['capitulos'] += progresso.capitulos
        # Consumo por provedor: inclui tentativas falhadas e é isto que permite
        # trocar de serviço quando um esgota, em vez de parar o dia inteiro.
        self._registar_consumo(chave, antes_rede, progresso)
        self.estado.versos_total += progresso.versos
        self._registar_exaustos()
        self._lapidar_fechados(progresso)
        self._rever_fechados(progresso, dia)

        alvo = 'livro completo'
        if progresso.livro:
            alvo = f'{progresso.livro.nome} {progresso.capitulo or ""}'.strip()
        if progresso.concluido and progresso.versos == 0:
            self.diario.escrever(
                f'Nada pendente nesta fila de {len(livros)} livro(s). '
                'Se quiser continuar, acrescente mais livros à fila.'
            )
            return ResultadoCiclo('parar', f'nada pendente nesta fila de {len(livros)} livro(s)')
        if progresso.versos == 0 and progresso.capitulos == 0:
            return ResultadoCiclo(
                'nada', '; '.join(progresso.motivos) or 'nenhum progresso', progresso=progresso,
            )

        resumo = None
        if self.config.compilar and progresso.capitulos:
            resumo = self._compilar(chave)
        seguinte = proximo_trabalho(livros, self.dados)
        onde = f' A seguir: {seguinte[0].nome} {seguinte[1]}.' if seguinte else ''
        self.diario.escrever(
            f'Ciclo {self.estado.ciclos}: +{progresso.versos} versículos, '
            f'+{progresso.capitulos} capítulos em {alvo} '
            f'({motor.provedor}/{motor.modelo}; {self.config.lote(motor.provedor)} versículos/pedido). '
            f'Hoje: {dia["versos"]} versículos, {dia["pedidos"]} pedidos.{onde}'
        )
        salvar_estado(self.dados / '.bee' / 'estado.json', self.estado)
        return ResultadoCiclo('gerado', alvo, progresso=progresso, resumo_compilacao=resumo)

    def _lapidar_fechados(self, progresso: Progresso) -> None:
        """Lapidação automática (mecânica) dos capítulos fechados nesta fatia.

        Corre na edição nova, antes da revisão por segunda IA: normaliza a
        forma das notas, regenera a Crítica Textual do aparato e da
        colação e corrige a pontuação mecânica (`bee/lapidador.py`). Uma
        falha aqui NUNCA perde produção: regista-se o aviso e o capítulo
        segue para a revisão tal como foi gerado.
        """
        if not progresso.capitulos_fechados:
            return
        from .perfil import resolver_perfil
        if resolver_perfil().nome != 'nova':
            return
        from . import lapidador
        from .arquivos import salvar_livro
        raiz = Path(__file__).resolve().parent.parent
        for numero, capitulo in progresso.capitulos_fechados:
            livro = next((l for l in LIVROS if l.numero == numero), None)
            caminho = next(self.dados.glob(f'{numero}_*.json'), None)
            if livro is None or caminho is None or not caminho.exists():
                continue
            try:
                dados = json.loads(caminho.read_text(encoding='utf-8'))
                versiculos = dados.get('chapters', {}).get(str(capitulo))
                if not versiculos:
                    continue
                colacao = None
                relatorio_col = raiz / 'docs' / 'colacao' / f'{livro.nome}.json'
                if relatorio_col.exists():
                    colacao = json.loads(relatorio_col.read_text(encoding='utf-8'))
                novos, relatorio, problemas = lapidador.lapidar_versos(
                    versiculos, capitulo, colacao)
                if colacao is not None:
                    alertas = lapidador.alertas_grego(novos, capitulo, colacao)
                    if alertas:
                        self.diario.escrever(
                            f'Lapidação automática de {livro.nome} {capitulo}: '
                            f'{sum(len(f) for f in alertas.values())} forma(s) '
                            f'grega(s) fora da base em {len(alertas)} '
                            'versículo(s) — alerta de amostragem (lemas de '
                            'léxico são legítimos).', 'aviso')
                if novos != versiculos:
                    dados['chapters'][str(capitulo)] = novos
                    dados.setdefault('history', []).append({
                        'chapter': capitulo, 'verse_from': 1,
                        'verse_to': len(novos), 'provider': 'local',
                        'model': 'editorial:lapidacao-automatica',
                        'generated_at_utc': _iso(_agora()),
                    })
                    salvar_livro(caminho, dados, livro)
                    self.diario.escrever(
                        f'Lapidação automática de {livro.nome} {capitulo}: '
                        f'{len(relatorio)} normalização(ões).')
                for problema in problemas:
                    self.diario.escrever(
                        f'Lapidação automática de {livro.nome}: {problema}',
                        'aviso')
            except Exception as exc:  # a lapidação nunca pode parar a produção
                self.diario.escrever(
                    f'Lapidação automática de {livro.nome if livro else numero} '
                    f'{capitulo} falhou; original preservado: {exc}', 'aviso')

    def _rever_fechados(self, progresso: Progresso, dia: dict[str, Any]) -> None:
        """P2: revisão por segunda IA dos capítulos fechados nesta fatia.

        Só na edição nova e sempre ligada (desliga-se com BEE_REVISAO=desligado).
        Uma falha da revisão NUNCA toca no que foi traduzido: regista-se o aviso
        e segue — perder produção por causa do revisor seria pior do que não rever.
        """
        if not progresso.capitulos_fechados:
            return
        if os.environ.get('BEE_REVISAO', 'sempre').strip().lower() == 'desligado':
            self.diario.escrever('Revisão por segunda IA desligada (BEE_REVISAO=desligado).')
            return
        from .perfil import resolver_perfil
        if resolver_perfil().nome != 'nova':
            return  # o legado não tem revisão de voz
        from . import revisor
        # P3 opcional: com métricas gravadas, os provedores com menos deriva
        # revista primeiro (o cache vem de scripts/metricas_provedores.py, que
        # o workflow corre em cada produção).
        pontos = None
        if os.environ.get('BEE_PRIORIDADES', '').strip().lower() == 'metricas':
            from . import metricas
            pontos = metricas.carregar_pontuacoes(self.dados)
            if pontos is None:
                self.diario.escrever(
                    'BEE_PRIORIDADES=metricas mas sem cache .bee/metricas.json; '
                    'a usar a prioridade padrão dos papéis.')
        try:
            resumo = revisor.rever_capitulos_fechados(
                self.dados, progresso.capitulos_fechados, self.motores,
                diario=self.diario.escrever, pontuacoes=pontos,
            )
        except Exception as exc:
            self.diario.escrever(
                f'Revisão por segunda IA falhou; original preservado: {exc}', 'aviso')
            return
        dia['emendas_revisao'] = dia.get('emendas_revisao', 0) + resumo['emendas']
        self.diario.escrever(
            f'Revisão de voz: {resumo["capitulos_revistos"]} capítulo(s) revistos, '
            f'{resumo["emendas"]} emenda(s) aplicada(s).'
            + (f' Saltados: {"; ".join(resumo["saltados"])}.' if resumo['saltados'] else '')
        )

    def _compilar(self, chave: str) -> dict[str, Any] | None:
        existentes = ler_todos(self.dados)
        if not any(dados['chapters'] for dados in existentes.values()):
            # Ainda não há um capítulo completo; nada a publicar.
            return None
        try:
            resumo = compilar(self.dados, self.saida)
        except (ErroCompilacao, ValueError, OSError) as exc:
            self.diario.escrever(f'A compilação falhou; os módulos anteriores foram preservados: {exc}', 'aviso')
            return None
        self.estado.ultima_compilacao_utc = _iso(_agora())
        self.estado.ultima_compilacao_build = str(resumo['build_id'])
        estado = 'completo' if resumo['completo'] else 'PARCIAL'
        self.diario.escrever(
            f'Módulos recompilados ({estado}): {resumo["capitulos"]}/1189 capítulos, '
            f'{resumo["versiculos"]} versículos.'
        )
        return resumo
