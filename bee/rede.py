"""HTTPS com limite de ritmo e retry para falhas transitórias."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import math
import random
import re
import sys
import time
from typing import Callable
import urllib.error
import urllib.request


class ErroRede(RuntimeError):
    pass


# Nenhuma espera de rede pode bloquear um ciclo por mais do que isto. Em 17/11
# a Groq devolveu Retry-After de 523 s, 1176 s, 989 s e 1542 s; o programa
# dormiu esses valores e a execução do GitHub foi cancelada aos 50 minutos.
# Um 429 passa imediatamente ao provedor seguinte; a espera longa é decisão do
# agendador, não de uma única chamada HTTP.
ESPERA_MAXIMA = 45.0


class CotaExcedida(ErroRede):
    """HTTP 429 persistente: a quota do serviço (ou da chave) está esgotada por agora."""


class ServicoIndisponivel(ErroRede):
    """HTTP 5xx persistente: o serviço está instável, não é a configuração do projeto."""


def _retry_after(valor: str | None) -> float:
    if not valor:
        return 0.0
    try:
        segundos = float(valor)
        return max(0.0, segundos) if math.isfinite(segundos) else 0.0
    except ValueError:
        try:
            data = parsedate_to_datetime(valor)
            if data.tzinfo is None:
                data = data.replace(tzinfo=timezone.utc)
            return max(0.0, (data - datetime.now(timezone.utc)).total_seconds())
        except (ValueError, TypeError, OverflowError):
            return 0.0


class ClienteHTTP:
    def __init__(self, pausa: float = 1.0, tentativas: int = 4, timeout: float = 120.0):
        if pausa < 0 or tentativas < 1 or timeout <= 0:
            raise ValueError('Configuração de rede inválida.')
        self.pausa = pausa
        self.tentativas = tentativas
        self.timeout = timeout
        self._ultima_requisicao: float | None = None
        # Orçamento de tokens por minuto, por provedor. Sem isto, um lote atrás
        # do outro esgota o TPM da Groq (8.000 tokens/minuto no plano gratuito)
        # e o serviço responde 429 em rajada — foi o que aconteceu em 17/11:
        # dez 429 seguidos e um único lote guardado em quatro minutos.
        self.tokens_por_minuto: dict[str, int] = {}
        # Pedidos por minuto: o Mistral dá ~2 e a Groq 30. Sem este limite o
        # ciclo pedia lotes em sequência e recebia 429 a cada segundo pedido.
        self.pedidos_por_minuto: dict[str, int] = {}
        self._gasto: dict[str, list[tuple[float, int]]] = {}
        self._pedidos: dict[str, list[float]] = {}
        self._esperas: dict[str, float] = {}
        # Contagem de tentativas HTTP por provedor, incluindo as que falharam.
        # O orçamento diário tem de contar o que foi realmente gasto, não só
        # os lotes que produziram versículos.
        self.contagem_pedidos: dict[str, int] = {}

    def pedidos_por_provedor(self) -> dict[str, int]:
        """Tentativas HTTP feitas nesta execução, por provedor."""
        return dict(self.contagem_pedidos)

    def reservar_pedido(self, provedor: str) -> float:
        """Espera o necessário para não exceder os pedidos/minuto do serviço."""
        teto = self.pedidos_por_minuto.get(provedor)
        if not teto:
            return 0.0
        agora = time.monotonic()
        marcas = self._pedidos.setdefault(provedor, [])
        limite = agora - 60.0
        while marcas and marcas[0] <= limite:
            marcas.pop(0)
        espera = 0.0
        if len(marcas) >= teto:
            espera = max(0.0, (marcas[0] + 60.0) - agora) + 0.05
            time.sleep(espera)
            agora = time.monotonic()
            while marcas and marcas[0] <= agora - 60.0:
                marcas.pop(0)
        marcas.append(agora)
        if espera:
            self._esperas[provedor] = self._esperas.get(provedor, 0.0) + espera
        return espera

    def reservar_tokens(self, provedor: str, tokens: int) -> float:
        """Espera o necessário para caber no TPM do provedor; devolve os segundos.

        A espera é devolvida para que o chamador a possa mostrar no diário e no
        resumo: uma pausa de 40 s tem de ser visível, não silenciosa.
        """
        teto = self.tokens_por_minuto.get(provedor)
        if not teto or tokens <= 0:
            return 0.0
        agora = time.monotonic()
        marcas = self._gasto.setdefault(provedor, [])
        limite = agora - 60.0
        while marcas and marcas[0][0] <= limite:
            marcas.pop(0)
        usado = sum(quantidade for _, quantidade in marcas)
        espera = 0.0
        if usado + tokens > teto and marcas:
            espera = max(0.0, (marcas[0][0] + 60.0) - agora) + 0.05
            if espera > 0:
                time.sleep(espera)
                agora = time.monotonic()
                while marcas and marcas[0][0] <= agora - 60.0:
                    marcas.pop(0)
        marcas.append((agora, min(tokens, teto)))
        if espera:
            self._esperas[provedor] = self._esperas.get(provedor, 0.0) + espera
        return espera

    def esperas_por_provedor(self) -> dict[str, float]:
        """Segundos totais passados à espera de TPM, por provedor."""
        return dict(self._esperas)

    def _esperar_pausa(self) -> None:
        if self._ultima_requisicao is not None:
            restante = self.pausa - (time.monotonic() - self._ultima_requisicao)
            if restante > 0:
                time.sleep(restante)

    def obter(
        self, requisicao: urllib.request.Request, descricao: str,
        limite: int = 64 * 1024 * 1024, log: Callable[[str], None] | None = None,
        provedor: str | None = None,
    ) -> bytes:
        """Nunca imprime a chave, o corpo da resposta ou o texto enviado à API."""
        for tentativa in range(1, self.tentativas + 1):
            if provedor:
                self.contagem_pedidos[provedor] = self.contagem_pedidos.get(provedor, 0) + 1
            self._esperar_pausa()
            retry_after = 0.0
            try:
                with urllib.request.urlopen(requisicao, timeout=self.timeout) as resposta:
                    corpo = resposta.read(limite + 1)
                if len(corpo) > limite:
                    raise ErroRede(f'{descricao}: resposta maior que o limite de segurança.')
                return corpo
            except urllib.error.HTTPError as exc:
                codigo = exc.code
                retry_after = _retry_after(exc.headers.get('Retry-After')) if exc.headers else 0.0
                exc.close()
                if codigo == 429:
                    # Não dormir: o rodízio passa ao provedor seguinte. Uma
                    # espera de 20 minutos é pior do que perder este lote e
                    # voltar no ciclo seguinte.
                    espera = f' (Retry-After {retry_after:.0f}s)' if retry_after else ''
                    raise CotaExcedida(
                        f'{descricao}: HTTP 429{espera}; limite de ritmo/quota atingido, '
                        'a tentar outro provedor.'
                    ) from None
                transitorio = codigo in (408, 409, 425) or 500 <= codigo <= 599
                if not transitorio:
                    dica = {
                        400: 'verifique os parâmetros e a compatibilidade do modelo',
                        401: 'verifique a chave do provedor',
                        403: 'verifique permissões, faturação e a chave',
                        404: 'verifique o endereço ou o nome do modelo',
                    }.get(codigo, 'verifique a configuração do serviço')
                    raise ErroRede(f'{descricao}: HTTP {codigo}; {dica}.') from None
                motivo = f'HTTP {codigo}'
            except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as exc:
                # URLError.reason pode conter dados sensíveis; mostre apenas a categoria.
                motivo = f'falha de rede ({type(exc).__name__})'
            finally:
                # A pausa é medida após o fim da chamada, não apenas entre inícios.
                self._ultima_requisicao = time.monotonic()
            if tentativa == self.tentativas:
                if motivo.startswith('HTTP 5'):
                    classe = ServicoIndisponivel
                else:
                    classe = ErroRede
                texto = f'{descricao}: {motivo}; esgotadas {self.tentativas} tentativas.'
                if log:
                    log(texto)
                raise classe(texto) from None
            atraso = min(ESPERA_MAXIMA, max(retry_after, min(60.0, 2 ** (tentativa - 1) + random.random())))
            aviso = f'{descricao}: {motivo}; nova tentativa em {atraso:.1f}s ({tentativa}/{self.tentativas}).'
            print(aviso, file=sys.stderr)
            if log:
                log(aviso)
            time.sleep(atraso)
        raise AssertionError('inalcançável')


def mascarar(chave: str) -> str:
    """Identifica uma chave nos registos sem revelar o segredo."""
    chave = chave.strip()
    return f'…{chave[-4:]}' if len(chave) > 8 else '(chave curta)'


def ler_chaves(valor: str | None) -> list[str]:
    """Aceita uma chave ou várias separadas por vírgula/ponto e vírgula."""
    if not valor:
        return []
    return [parte.strip() for parte in re.split(r'[,;\s]+', valor) if parte.strip()]
