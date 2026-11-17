"""MotorMistral: transporte via SDK Mistral, prompt e validação do MotorIA."""
import json

import pytest

import worker.motor_mistral as mm
from bee.catalogo import POR_NUMERO
from bee.ia import RespostaTruncada
from worker.motor_mistral import MotorMistral


class _Mensagem:
    def __init__(self, conteudo: str):
        self.content = conteudo


class _Escolha:
    def __init__(self, conteudo: str, motivo: str = 'stop'):
        self.message = _Mensagem(conteudo)
        self.finish_reason = motivo


class _Chat:
    def __init__(self, respostas: list[str]):
        self.respostas = list(respostas)
        self.pedidos: list[dict] = []

    def complete(self, **kwargs):
        self.pedidos.append(kwargs)
        return type('Resposta', (), {'choices': [_Escolha(self.respostas.pop(0))]})()


class _Cliente:
    def __init__(self, respostas: list[str]):
        self.chat = _Chat(respostas)


COMENTARIO = (
    '<p><b>Análise Léxica:</b> δέσμιος (désnios, G1198): prisioneiro.</p>'
    '<p><b>Crítica Textual:</b> sem variante verificada entre as edições fornecidas.</p>'
    '<p><b>Síntese Exegética:</b> Paulo apresenta-se como prisioneiro de Cristo.</p>'
)


def resposta_verses(versiculos: list[dict]) -> str:
    return json.dumps({'verses': versiculos}, ensure_ascii=False)


def test_gera_e_valida_versiculos(monkeypatch):
    fake = _Cliente([resposta_verses([
        {'verse': 1, 'text': 'De Paulo, prisioneiro de Cristo Jesus,', 'commentary': COMENTARIO},
        {'verse': 2, 'text': 'para Filemom, nosso amado colaborador,', 'commentary': COMENTARIO},
    ])])
    monkeypatch.setattr(mm, 'get_mistral_client', lambda run_as=None: fake)
    motor = MotorMistral(orientacoes='Manter SENHOR em maiúsculas.')
    livro = POR_NUMERO[640]
    fontes = [
        {'verse': 1, 'grego': 'Παῦλος δέσμιος Χριστοῦ Ἰησοῦ'},
        {'verse': 2, 'grego': 'καὶ Τιμοθέῳ ὁ ἀδελφός'},
    ]
    versiculos = motor.gerar(livro, 1, fontes)
    assert [v['verse'] for v in versiculos] == [1, 2]
    assert '<p>' in versiculos[0]['commentary']
    pedido = fake.chat.pedidos[0]
    system = pedido['messages'][0]['content']
    assert 'DIRETRIZES DO RESPONSÁVEL' in system
    assert 'Manter SENHOR em maiúsculas.' in system
    assert 'MODO RASCUNHO' in system
    assert pedido['model'] == 'mistral-medium-latest'
    assert pedido['response_format'] == {'type': 'json_object'}


def test_resposta_truncada(monkeypatch):
    fake = _Cliente(['{"verses": [{"verse": 1, "text": "De Pau'])
    fake.chat.pedidos = []

    def complete(**kwargs):
        return type('Resposta', (), {'choices': [_Escolha(fake.chat.respostas.pop(0), 'length')]})()

    fake.chat.complete = complete
    monkeypatch.setattr(mm, 'get_mistral_client', lambda run_as=None: fake)
    motor = MotorMistral()
    with pytest.raises(RespostaTruncada):
        motor.gerar(POR_NUMERO[640], 1, [{'verse': 1, 'grego': 'Παῦλος'}])


def test_provedor_mistral_registado():
    from bee.ia import PROVEDORES

    config = PROVEDORES['mistral']
    assert config.formato == 'openai'
    assert config.modelos[0] == 'mistral-medium-latest'
