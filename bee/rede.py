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

    def _esperar_pausa(self) -> None:
        if self._ultima_requisicao is not None:
            restante = self.pausa - (time.monotonic() - self._ultima_requisicao)
            if restante > 0:
                time.sleep(restante)

    def obter(
        self, requisicao: urllib.request.Request, descricao: str,
        limite: int = 64 * 1024 * 1024, log: Callable[[str], None] | None = None,
    ) -> bytes:
        """Nunca imprime a chave, o corpo da resposta ou o texto enviado à API."""
        for tentativa in range(1, self.tentativas + 1):
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
                transitorio = codigo in (408, 409, 425, 429) or 500 <= codigo <= 599
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
                if motivo == 'HTTP 429':
                    classe = CotaExcedida
                elif motivo.startswith('HTTP 5'):
                    classe = ServicoIndisponivel
                else:
                    classe = ErroRede
                texto = f'{descricao}: {motivo}; esgotadas {self.tentativas} tentativas.'
                if log:
                    log(texto)
                raise classe(texto) from None
            atraso = max(retry_after, min(60.0, 2 ** (tentativa - 1) + random.random()))
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
