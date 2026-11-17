"""Motor BEE que fala com a API Mistral através do SDK do worker.

Reaproveita todo o pipeline do `bee.ia.MotorIA` (prompt, validação, saneamento)
e substitui apenas o transporte: a chamada usa `get_mistral_client()`, que no
deployment gerenciado autentica-se com o token rotativo da conta de serviço —
sem chave estática no repositório. Fora do deployment (desenvolvimento), o SDK
usa a variável `MISTRAL_API_KEY`.
"""
from __future__ import annotations

from bee.ia import MotorIA, RespostaInvalida, RespostaTruncada
from bee.rede import ClienteHTTP
from mistralai.workflows.plugins.mistralai import get_mistral_client
from mistralai.workflows.plugins.mistralai.connectors.run_as import RunAs

MODELO_PADRAO = 'mistral-medium-latest'


class MotorMistral(MotorIA):
    """Um modelo Mistral com as diretrizes editoriais do responsável."""

    def __init__(
        self, modelo: str = MODELO_PADRAO, max_tokens: int = 8192,
        aplicar_revisao: bool = True, orientacoes: str = '',
    ):
        super().__init__('mistral', (modelo,), ['via-sdk'], ClienteHTTP(), max_tokens, aplicar_revisao)
        self.orientacoes = orientacoes.strip()

    def _system(self) -> str:
        base = super()._system()
        if self.orientacoes:
            base += (
                '\n\nDIRETRIZES DO RESPONSÁVEL: obedeça com prioridade sobre o padrão, '
                'sem violar as regras de rigor: ' + self.orientacoes
            )
        return base

    def _requisicao(self, mensagem: str) -> str:
        cliente = get_mistral_client(RunAs.DEPLOYMENT)
        resposta = cliente.chat.complete(
            model=self.modelo,
            messages=[
                {'role': 'system', 'content': self._system()},
                {'role': 'user', 'content': mensagem},
            ],
            max_tokens=self.max_tokens,
            temperature=0.4,
            response_format={'type': 'json_object'},
        )
        escolhas = getattr(resposta, 'choices', None) or []
        if not escolhas:
            raise RespostaInvalida('Resposta Mistral sem escolhas.')
        if escolhas[0].finish_reason == 'length':
            raise RespostaTruncada('Resposta Mistral atingiu o limite de tokens.')
        texto = (escolhas[0].message.content or '') if escolhas[0].message else ''
        if not texto.strip():
            raise RespostaInvalida('Resposta Mistral vazia.')
        return texto
