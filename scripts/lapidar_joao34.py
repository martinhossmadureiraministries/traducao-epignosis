#!/usr/bin/env python3
"""Lapidação de João 3:34–36 e João 4:1–28 — 2026-11-20.

Os últimos três versículos de João 3 (Cerebras) e os primeiros 28 de
João 4 (Gemini) foram produzidos na nuvem depois da lapidação de João
2–3 e guardam os vícios dessa geração:

* os títulos das notas não estão no formato da casa em nenhum dos 31
  versículos («<b>Análise Léxica</b> —» em vez de «<b>Análise
  Léxica:</b>»); João 3:35–36 têm ainda secções de enchimento
  («Hermenêutica e Contexto», «Geografia e História») e põem a leitura
  inteira do Textus Receptus entre «[[ ]]»;
* a Crítica Textual inventa apoio manuscrito («forte apoio nos
  principais manuscritos alexandrinos», 4:1 — a colação mostra 02, 03,
  032, 04, P66 e P75 a lerem «ὁ κύριος»), inverte a leitura de 4:11
  (é WH que omite «ἡ γυνή», não a base) e usa níveis de certeza fora
  do formato («A segura», «grau de certeza»);
* há erros de gramática grega nas secções lexicais (δίδωσιν dado como
  3.ª pessoa do plural, quando é singular; δέδωκεν dado como aoristo,
  quando é perfeito) e gralhas greco-latinas («ἄνδra», «hallomenου»,
  «Σαmarίτιδος»);
* o texto tem o paradigma proibido de «vós» («adorareis», 4:21;
  «conheceis», 4:22), «estar a» + infinitivo (4:1, 4:27), o ponto
  fora das aspas (4:7, 4:10, 4:14–4:18) e inverte o sentido de 3:34
  («não dão o Espírito segundo medida», com sujeito plural fantasma).

Este script, e só isto:

1. normaliza registo, maiúsculas e pontuação dos 31 textos;
2. regenera a Crítica Textual dos 31 versículos a partir do aparato
   da SBLGNT e do relatório de colação CNTR aparado aos capítulos
   1–4 (``docs/colacao/João.json``), com o nível de certeza da casa
   (A: variante só bizantina, RP; B: edições críticas divididas —
   ``docs/CRITICA_TEXTUAL.md`` §10). Os únicos manuscritos citados
   são os dos factos de colação lidos verso a verso (``CT_EXTRA``);
3. corrige os erros lexicais e apaga as secções de enchimento;
4. regista cada decisão de fundo em Nota de redação, atualiza o bloco
   de revisão do capítulo 3 (agora fechado, 36 versículos), abre o
   bloco do capítulo 4 e estende a bibliografia à colação 1–4. Nada
   se aprova: João continua RASCUNHO e o capítulo 4 continua
   ``in_progress``.

Uso::

    python3 scripts/lapidar_joao34.py             # aplica e guarda
    python3 scripts/lapidar_joao34.py --verificar # confere sem escrever
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))

import lapidar_seis as lapidar          # normalização mecânica da casa
import migrar_notas_cinco as mig        # parsing do aparato (só edições)

DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '500_Joao.json'
COLACAO = RAIZ / 'docs' / 'colacao' / 'João.json'

MODELO_EDITORIAL = 'editorial:lapidacao-joao-3-4'
CARIMBO = '2026-11-20T13:00:00+00:00'

ALVOS: list[tuple[str, int, range]] = [
    ('chapters', 3, range(34, 37)),
    ('in_progress', 4, range(1, 29)),
]

# ---------------------------------------------------------------------------
# 1. Textos — (capítulo, verso, trecho antigo, trecho novo)
# ---------------------------------------------------------------------------

TEXTOS: list[tuple[int, int, str, str]] = [
    # δίδωσιν é singular e o sujeito implícito é Deus: «não dão» tinha um
    # sujeito plural fantasma e invertia o sentido.
    (3, 34, 'Pois aquele que Deus enviou fala as palavras de Deus, '
            'pois não dão o Espírito segundo medida.',
            'Pois aquele que Deus enviou fala as palavras de Deus, '
            'porque Deus não dá o Espírito por medida.'),
    # Pai/Filho com maiúscula (Deus/Jesus); δέδωκεν ἐν τῇ χειρί não é
    # «deu tudo na sua mão» (calque com a mão no singular).
    (3, 35, 'O pai ama o filho, e deu tudo na sua mão.',
            'O Pai ama o Filho e entregou-lhe tudo nas mãos.'),
    # ἀπειθῶν é «quem desobedece», sem o rodeio «se recusa a obedecer».
    (3, 36, 'Quem crê no filho tem vida eterna; mas quem se recusa a '
            'obedecer ao filho não verá a vida,',
            'Quem crê no Filho tem vida eterna; quem desobedece ao '
            'Filho não verá a vida,'),
    # A casa usa o imperfeito («fazia e batizava»), não «estar a» +
    # infinitivo; οὖν não precisa de «portanto» a abrir a frase.
    (4, 1, 'Quando, portanto, Jesus soube', 'Quando Jesus soube'),
    (4, 1, 'Jesus estava a fazer e a batizar mais discípulos do que João—',
           'Jesus fazia e batizava mais discípulos do que João —'),
    # τῷ Ἰωσήφ tem artigo: «ao seu filho José»; o ponto fecha o versículo
    # e 4:6 abre frase nova com maiúscula.
    (4, 5, 'que Jacó deu a seu filho José;', 'que Jacó deu ao seu filho José.'),
    (4, 6, 'estava ali a fonte de Jacó.', 'Estava ali a fonte de Jacó.'),
    (4, 6, 'assentava-se assim junto à fonte', 'sentou-se junto à fonte'),
    # Ponto dentro das aspas, a forma da casa (cf. 1:43, 1:45–1:48).
    (4, 7, '«Dá-me de beber».', '«Dá-me de beber.»'),
    (4, 10, 'e ele te daria água viva».', 'e ele te daria água viva.»'),
    (4, 14, 'para a vida eterna».', 'para a vida eterna.»'),
    # διέρχωμαι ἐνθάδε ἀντλεῖν é «vir aqui tirar água», sem «tencionar».
    (4, 15, '«Senhor, dá-me dessa água, para que eu não tenha sede nem '
            'venha aqui a tencionar tirar água».',
            '«Senhor, dá-me dessa água, para que eu não tenha sede nem '
            'venha aqui para tirar água.»'),
    (4, 16, '«Vai, chama o teu marido e vem cá».',
            '«Vai, chama o teu marido e vem cá.»'),
    (4, 17, '«Não tenho marido».', '«Não tenho marido.»'),
    (4, 18, 'nisso disseste a verdade».', 'nisso disseste a verdade.»'),
    # προσκυνήσετε é 2.ª pessoa do plural: a forma da casa é «vocês».
    (4, 21, 'nem em Jerusalém adorareis o Pai.',
            'nem em Jerusalém vocês adorarão o Pai.'),
    (4, 22, 'Vocês adoram o que não conheceis;',
            'Vocês adoram o que não conhecem;'),
    # ἀναγγελεῖ ἡμῖν ἅπαντα: «nos anunciará tudo», não «anunciará tudo
    # a nós».
    (4, 25, 'Quando ele vier, anunciará tudo a nós.',
            'Quando ele vier, nos anunciará tudo.'),
    # A casa usa o gerúndio («estava falando»), não «estar a» + infinitivo.
    (4, 27, 'estivesse a falar com uma mulher', 'estivesse falando com uma mulher'),
]

# ---------------------------------------------------------------------------
# 2. Notas — Análise Léxica refeita onde a máquina errou a gramática
# ---------------------------------------------------------------------------

LEX_REFEITA: dict[tuple[int, int], str] = {
    (3, 34): (
        '<p><b>Análise Léxica:</b> <i>ὃν</i> (hón) — aquele que; '
        '<i>ἀπέστειλεν</i> (apésteilen) — enviou (aoristo de '
        '<i>ἀποστέλλω</i>); <i>λαλεῖ</i> (laleî) — fala; <i>ἐκ '
        'μέτρου</i> (ek métrou) — por medida, com limite; '
        '<i>δίδωσιν</i> (dídōsin) — dá (presente, 3.ª pessoa do '
        'singular; o sujeito implícito é Deus); <i>τὸ πνεῦμα</i> '
        '(tò pneûma) — o Espírito.</p>'),
    (3, 35): (
        '<p><b>Análise Léxica:</b> <i>ὁ πατήρ</i> (ho patḗr) — o Pai; '
        '<i>ἀγαπᾷ</i> (agapâi) — ama (presente); <i>τὸν υἱόν</i> '
        '(tòn hyión) — o Filho; <i>πάντα</i> (pánta) — tudo, todas as '
        'coisas; <i>δέδωκεν</i> (dédōken) — entregou (perfeito de '
        '<i>δίδωμι</i>: a entrega está feita e os seus efeitos '
        'permanecem); <i>ἐν τῇ χειρὶ αὐτοῦ</i> (en têi cheirì '
        'autoû) — na mão dele (o texto usa a expressão corrente '
        '«nas mãos»).</p>'),
}

# Fragmentos lexicais e de síntese — (capítulo, verso, antigo, novo).
FRAGMENTOS: list[tuple[int, int, str, str]] = [
    # A síntese dizia que o Espírito é dado «segundo medida»: é o contrário.
    (3, 34, 'e que o Espírito não é distribuído arbitrariamente, mas '
            'segundo medida, sublinhando a autoridade divina da '
            'mensagem e a limitação da distribuição do Espírito.',
            'e que Deus dá o Espírito sem medida ao seu enviado, '
            'sublinhando a autoridade plena da sua mensagem.'),
    (3, 36, 'ὁδὲ ἡ ὀργὴ (hē orgē) – “mas a ira”',
            '<i>ἡ ὀργή</i> (hē orgḗ) — a ira'),
    (3, 36, 'ἐπʼ αὐτόν (ep&#x27; auton) – “sobre ele”',
            "<i>ἐπʼ αὐτόν</i> (ep' autón) — sobre ele"),
    (4, 2, 'ἀλλʼ (all&#x27;)', "<i>ἀλλʼ</i> (all')"),
    (3, 36, 'ὁ δὲ ἀπειθῶν (ho de apeithōn) – «mas o que se recusa»',
            'ὁ δὲ ἀπειθῶν (ho de apeithōn) – «mas o que desobedece»'),
    (4, 1, 'ποιεῖ (poiei): faz, está a fazer', 'ποιεῖ (poiei): faz'),
    (4, 2, 'καίτοιγε (kaitoisge): embora, com tudo, apesar de',
           'καίτοιγε (kaitoige): embora, apesar de'),
    (4, 3, 'para a região galileia', 'para a região da Galileia'),
    (4, 9, 'Σαmarίτιδος', 'Σαμαρίτιδος'),
    (4, 10, 'ᾔδεις (ēdeis): imperfeito com sentido de mais-que-perfeito, '
            '«conhecesses»',
            'ᾔδεις (ḗideis): «conhecesses» (mais-que-perfeito de '
            '<i>οἶδα</i>, com valor contrafactual na condição)'),
    (4, 13, 'com a insipidez das soluções materiais',
            'com a insuficiência das soluções materiais'),
    (4, 21, '«adorareis o Pai» (dativo)', '«vocês adorarão o Pai» (dativo)'),
    (4, 22, '«vocês adoram o que não conheceis»',
            '«vocês adoram o que não conhecem»'),
    (4, 14, '(hallomenου)', '(hallomenou)'),
    (4, 16, '<b>ἀνδρα</b> (andra)', '<b>ἄνδρα</b> (ándra)'),
]

# ---------------------------------------------------------------------------
# 3. Crítica Textual — factos de colação lidos no relatório (só CNTR de João)
# ---------------------------------------------------------------------------

CT_EXTRA: dict[tuple[int, int], str] = {
    (3, 34): 'Na colação, 02 e 05 acrescentam «ὁ θεὸς», com Tregelles '
             'e RP; 03 e 04 leem com a base.',
    (4, 1): 'Na colação, 01 e 05 leem «ὁ Ἰησοῦς» com a base; 02, 03, '
            '032, 04, P66 e P75 leem «ὁ κύριος».',
    (4, 3): 'Na colação, 02 omite «πάλιν», com RP; 01, 03, 032, 04, '
            'P66 e P75 leem com a base.',
    (4, 11): 'Na colação, 02, 032, 04, 05 e P66 leem «ἡ γυνή» com a '
             'base; 03 e P75 omitem a expressão, com WH.',
    (4, 25): 'Na colação, 03 e 04 leem «ἅπαντα» com a base; 02 lê '
             '«πάντα», com RP.',
    (4, 27): 'Na colação, 01, 02, 03, 032, 04, 05, P66 e P75 leem o '
             'imperfeito «ἐθαύμαζον»; o aoristo «ἐθαύμασαν» está em '
             'KJTR, RP e ST e no Textus Receptus de Scrivener.',
}


def critica_textual(cap: int, verso: int, item_col: dict) -> str:
    """Crítica Textual gerada do aparato (edições) + nível de certeza.

    A fraseologia é a de ``scripts/lapidar_joao23.py``; nos versículos
    sem aparato junta-se a frase do nível A, que a geração anterior
    omitia («Nível de certeza: A.» sem formato, ou nada).
    """
    base = item_col['base']
    aparato = base.get('aparato_sblgnt') or []
    frases: list[str] = []
    if aparato:
        descricoes = []
        apoios_variantes: list[set[str]] = []
        for entrada in aparato:
            limpa = entrada.strip().lstrip('•').strip()
            limpa = re.sub(r'^[\d:–\-– ]+', '', limpa)  # referência inicial
            if ']' not in limpa:
                continue
            esq, dir_ = limpa.split(']', 1)
            leitura_base, apoio_base = mig._dividir_apoio(esq)
            variantes = []
            for alt in dir_.split(';'):
                leitura_alt, apoio_alt = mig._dividir_apoio(alt)
                if leitura_alt in ('–', '-'):
                    leitura_alt = 'omissão desta leitura'
                elif leitura_alt.startswith('+'):
                    leitura_alt = 'acréscimo de ' + leitura_alt[1:].strip()
                variantes.append((leitura_alt, apoio_alt))
                apoios_variantes.append(set(apoio_alt))
            texto_var = '; '.join(
                f'«{l}» ({mig._render_apoio(a)})' for l, a in variantes)
            descricoes.append(
                f'«{leitura_base}» ({mig._render_apoio(apoio_base)}) '
                f'contra {texto_var}')
        frases.append(
            'O aparato da SBLGNT (que compara edições, não manuscritos) '
            'regista ' + '; '.join(descricoes) + '.')
        so_bizantina = all(a and a <= {'RP'} for a in apoios_variantes)
        if so_bizantina:
            nivel, razao = 'A', ('a variante é bizantina (RP) e as edições '
                                 'críticas apoiam a base')
        else:
            nivel, razao = 'B', 'as edições críticas não são unânimes'
        frases.append(
            f'O texto segue a base (nível de certeza {nivel}: {razao}).')
    else:
        igual_tr = base.get('sblgnt_norm') == base.get('scrivener_norm')
        frases.append(
            'Sem unidade de variação adotada por qualquer edição: o '
            'aparato da SBLGNT nada regista neste versículo. Nas '
            'testemunhas colacionadas (CNTR) as divergências são de '
            'ortografia, abreviaturas de nomes sagrados, ordem de palavras '
            'ou leituras que nenhuma edição imprime (relatório de colação '
            'do livro).')
        if igual_tr:
            frases.append('O Textus Receptus de Scrivener lê o mesmo texto.')
        else:
            frases.append(
                'O Textus Receptus de Scrivener diverge da base neste '
                'versículo; a divergência está registada no mesmo relatório.')
        frases.append(
            'O texto segue a base (nível de certeza A: o aparato não '
            'regista variante neste versículo).')
    extra = CT_EXTRA.get((cap, verso))
    if extra:
        frases.append(extra)
    return '<p><b>Crítica Textual:</b> ' + ' '.join(frases) + '</p>'


# ---------------------------------------------------------------------------
# 4. Notas de redação — uma por decisão de fundo
# ---------------------------------------------------------------------------

NOTAS_REDACAO: dict[tuple[int, int], str] = {
    (3, 34): '<p><b>Nota de redação:</b> O texto anterior lia «não dão '
             'o Espírito segundo medida», com sujeito plural fantasma: '
             '<i>δίδωσιν</i> é singular e o sujeito implícito é Deus — '
             'Deus não dá o Espírito por medida ao seu enviado. A '
             'Análise Léxica anterior dava a forma como «3.ª pessoa do '
             'plural» e a Crítica Textual como certeza A; Tregelles e '
             'RP acrescentam «ὁ θεὸς», por isso o nível é B.</p>',
    (3, 35): '<p><b>Nota de redação:</b> «O pai ama o filho» deu «O Pai '
             'ama o Filho» (maiúsculas de Deus e de Jesus, como no '
             'resto da edição) e «deu tudo na sua mão» deu «entregou-lhe '
             'tudo nas mãos»: <i>δέδωκεν</i> é perfeito, não aoristo '
             'como dizia a nota. As secções extra de contexto e de '
             'geografia eram enchimento e saíram; a leitura do Textus '
             'Receptus já não vai citada entre parênteses duplos.</p>',
    (3, 36): '<p><b>Nota de redação:</b> «quem se recusa a obedecer ao '
             'filho» deu «quem desobedece ao Filho»: é o que '
             '<i>ἀπειθῶν</i> diz, sem rodeio, e «Filho» leva maiúscula '
             'como em 3:16–18. As secções de enchimento saíram como em '
             '3:35.</p>',
    (4, 1): '<p><b>Nota de redação:</b> «estava a fazer e a batizar» '
            'deu «fazia e batizava»: a construção «estar a» + '
            'infinitivo não é a da casa (cf. 1:28). A nota anterior '
            'afirmava forte apoio manuscrito para '
            '«ὁ Ἰησοῦς», sem colação que o mostrasse; a colação '
            'mostra o contrário (ver Crítica Textual) e a afirmação '
            'saiu.</p>',
    (4, 11): '<p><b>Nota de redação:</b> A Crítica Textual anterior '
             'invertia a variante: dizia que a base omite «ἡ γυνή», '
             'quando a base a traz (Tregelles, NA28, RP) e é WH que a '
             'omite. A nota foi refeita do aparato.</p>',
    (4, 15): '<p><b>Nota de redação:</b> «nem venha aqui a tencionar '
             'tirar água» deu «nem venha aqui para tirar água»: '
             '<i>διέρχωμαι … ἀντλεῖν</i> é vir aqui tirar água; '
             '«tencionar» não está no grego.</p>',
    (4, 21): '<p><b>Nota de redação:</b> «adorareis» deu «vocês '
             'adorarão»: <i>προσκυνήσετε</i> é 2.ª pessoa do plural e '
             'o tratamento plural da casa é «vocês» (memória de '
             'estilo), como já em 4:20 e 4:22.</p>',
    (4, 22): '<p><b>Nota de redação:</b> «não conheceis» deu «não '
             'conhecem»: a mesma forma de «vós» de 4:21, no mesmo '
             'fôlego em que o texto já dizia «Vocês adoram».</p>',
    (4, 25): '<p><b>Nota de redação:</b> A Crítica Textual anterior '
             'apoiava «ἅπαντα» em testemunhas antigas que ninguém '
             'colacionou; o aparato só regista a divergência de RP '
             '(«πάντα») e o nível fica A. «anunciará tudo a nós» deu '
             '«nos anunciará tudo».</p>',
    (4, 27): '<p><b>Nota de redação:</b> «estivesse a falar» deu '
             '«estivesse falando» (gerúndio, cf. 1:28). A Crítica '
             'Textual anterior atribuía o aoristo «ἐθαύμασαν» ao '
             '«Textus Receptus e RP» com certeza B; o aparato só '
             'regista RP, por isso o nível é A e a atribuição foi '
             'corrigida com a colação.</p>',
}

BLOCO_CAP3 = {
    'chapter': 3, 'verse_from': 1, 'verse_to': 36, 'status': 'rascunho',
    'nota': 'Capítulo 3 fechado: os versículos 1–33 foram lapidados em '
            '2026-11-20 por scripts/lapidar_joao23.py e os versículos '
            '34–36, produzidos na nuvem já depois dessa lapidação, por '
            'scripts/lapidar_joao34.py (Crítica Textual refeita do '
            'aparato e da colação CNTR, capítulos 1–4; registo e '
            'pontuação normalizados). Continua RASCUNHO.'}

BLOCO_CAP4 = {
    'chapter': 4, 'verse_from': 1, 'verse_to': 28, 'status': 'rascunho',
    'nota': 'Capítulo em curso: os 28 versículos já produzidos foram '
            'lapidados em 2026-11-20 por scripts/lapidar_joao34.py '
            '(Crítica Textual refeita do aparato da SBLGNT e da '
            'colação CNTR, capítulos 1–4, com níveis de certeza; '
            'registo «vocês», gerúndio e pontuação normalizados). Os '
            'versículos seguintes continuam por produzir. Continua '
            'RASCUNHO.'}

HISTORICO = [
    {'chapter': 3, 'verse_from': 34, 'verse_to': 36, 'provider': 'local',
     'model': MODELO_EDITORIAL, 'generated_at_utc': CARIMBO},
    {'chapter': 4, 'verse_from': 1, 'verse_to': 28, 'provider': 'local',
     'model': MODELO_EDITORIAL, 'generated_at_utc': CARIMBO},
]

# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------

CABECALHO_FORA = re.compile(
    r'<b>(Análise Léxica|Crítica Textual|Síntese Exegética)</b>\s*'
    r'(?:—|-|:)?\s*')
SECCOES_CASA = ('Análise Léxica', 'Crítica Textual', 'Síntese Exegética')


def _alvos(dados: dict) -> list[tuple[int, dict]]:
    saida: list[tuple[int, dict]] = []
    for zona, cap, versos in ALVOS:
        por_numero = {v['verse']: v for v in dados[zona][str(cap)]}
        for vv in versos:
            saida.append(((cap, vv), por_numero[vv]))
    return saida


def _secoes(nota: str) -> dict[str, str]:
    return dict(mig.secoes(nota))


def aplicar(dados: dict, colacao: dict, relatorio: list[str]) -> None:
    for (cap, vv), v in _alvos(dados):
        ref = f'{cap}:{vv}'
        item_col = colacao['versiculos'][ref]
        ct = critica_textual(cap, vv, item_col)

        # --- texto ---
        for c, v2, velho, novo in TEXTOS:
            if (c, v2) != (cap, vv):
                continue
            if velho in v['text']:
                v['text'] = v['text'].replace(velho, novo, 1)
                relatorio.append(f'500 {ref} texto: «{velho[:40]}…» '
                                 f'→ «{novo[:40]}…»')
            elif novo not in v['text']:
                raise SystemExit(f'{ref}: trecho de texto não '
                                 f'encontrado: {velho!r}')

        # --- nota ---
        nota = CABECALHO_FORA.sub(r'<b>\1:</b> ', v['commentary'])
        secoes = _secoes(nota)
        for seccao in SECCOES_CASA:
            if seccao not in secoes:
                raise SystemExit(f'{ref}: falta a secção {seccao}')
        nota = (LEX_REFEITA.get((cap, vv), secoes['Análise Léxica'])
                + ct + secoes['Síntese Exegética'])
        # As secções que não são as três da casa (enchimento de 3:35–36)
        # não entram na nota refeita.
        if any(r not in SECCOES_CASA for r in _secoes(
                CABECALHO_FORA.sub(r'<b>\1:</b> ', v['commentary']))):
            relatorio.append(f'500 {ref} secções fora da casa removidas')
        relatorio.append(f'500 {ref} Crítica Textual regenerada')
        for c, v2, velho, novo in FRAGMENTOS:
            if (c, v2) != (cap, vv):
                continue
            if velho in nota:
                nota = nota.replace(velho, novo, 1)
                relatorio.append(f'500 {ref} nota: fragmento corrigido')
            elif novo not in nota:
                raise SystemExit(f'{ref}: fragmento de nota não '
                                 f'encontrado: {velho!r}')
        nota_red = NOTAS_REDACAO.get((cap, vv))
        if nota_red and nota_red not in nota:
            nota += nota_red
            relatorio.append(f'500 {ref} Nota de redação acrescentada')
        v['commentary'] = lapidar.normalizar_nota(nota)
        v['text'] = lapidar.normalizar_texto(v['text'])

    blocos = dados['review']['editorial_blocks']
    for i, bloco in enumerate(blocos):
        if bloco['chapter'] == 3:
            blocos[i] = BLOCO_CAP3
    if not any(b['chapter'] == 4 for b in blocos):
        blocos.append(BLOCO_CAP4)
    for item in dados.get('bibliography', []):
        if item.get('papel') == 'evidência' and 'capítulos 1–3' in (
                item.get('attribution') or ''):
            item['attribution'] = item['attribution'].replace(
                'capítulos 1–3', 'capítulos 1–4')
        if item.get('name', '').startswith('CNTR') and 'P45' not in (
                item.get('attribution') or ''):
            item['attribution'] = item['attribution'].replace(
                'P120, P134, P5,', 'P120, P134, P45, P5,')
    historico = dados.setdefault('history', [])
    for entrada in HISTORICO:
        if entrada not in historico:
            historico.append(entrada)


# ---------------------------------------------------------------------------
# Conferência
# ---------------------------------------------------------------------------

_MISTO = re.compile(r'[Ͱ-Ͽἀ-῿]')


def _token_misto(texto: str) -> list[str]:
    limpo = re.sub(r'<[^>]+>', ' ', texto)
    maus = []
    for tok in limpo.split():
        if _MISTO.search(tok) and re.search(r'[A-Za-z]', tok):
            maus.append(tok)
    return maus


def conferir(dados: dict, colacao: dict) -> list[str]:
    falhas: list[str] = []
    if len(dados['chapters'].get('3', [])) != 36:
        falhas.append('500 cap. 3: não tem 36 versículos')
    if '3' in dados.get('in_progress', {}):
        falhas.append('500: o capítulo 3 devia estar fechado em chapters')
    if len(dados.get('in_progress', {}).get('4', [])) != 28:
        falhas.append('500 cap. 4: não tem 28 versículos em curso')
    for (cap, vv), v in _alvos(dados):
        ref = f'{cap}:{vv}'
        t, n = v['text'], v['commentary']
        for proibido in ('[[', ']]', '&#', '<strong>', '“', '”', '‘', '’',
                         '\u2011', 'Hermenêutica e Contexto',
                         'Geografia e História', 'Textus Receptus (RP)',
                         'testemunhas alexandrinas',
                         'principais manuscritos alexandrinos',
                         'A segura', 'grau de certeza'):
            if proibido in n:
                falhas.append(f'500 {ref}: nota ainda tem «{proibido}»')
        for proibido in ('\u2011', 'adorareis', 'conheceis',
                         'estava a fazer', 'estivesse a falar',
                         'O pai ama o filho', 'tencionar tirar'):
            if proibido in t:
                falhas.append(f'500 {ref}: texto ainda tem «{proibido}»')
        if re.search(r'»[.?!]', t):
            falhas.append(f'500 {ref}: ponto fora das aspas no texto')
        for seccao in SECCOES_CASA:
            if f'<b>{seccao}:</b>' not in n:
                falhas.append(f'500 {ref}: falta a secção {seccao}')
        ct = critica_textual(cap, vv, colacao['versiculos'][ref])
        if ct not in n:
            falhas.append(f'500 {ref}: Crítica Textual não é a gerada')
        nota_red = NOTAS_REDACAO.get((cap, vv))
        if nota_red and nota_red not in n:
            falhas.append(f'500 {ref}: falta a Nota de redação')
        for c, v2, velho, novo in TEXTOS:
            if (c, v2) == (cap, vv) and novo not in t:
                falhas.append(f'500 {ref}: falta «{novo[:40]}» no texto')
        for c, v2, velho, novo in FRAGMENTOS:
            if (c, v2) == (cap, vv) and novo not in n:
                falhas.append(f'500 {ref}: falta «{novo[:40]}» na nota')
        if (cap, vv) in LEX_REFEITA and LEX_REFEITA[(cap, vv)] not in n:
            falhas.append(f'500 {ref}: Análise Léxica refeita não confere')
        for tok in _token_misto(n) + _token_misto(t):
            falhas.append(f'500 {ref}: palavra greco-latina mista «{tok}»')
    estados = {b['status'] for b in dados['review']['editorial_blocks']}
    if estados != {'rascunho'}:
        falhas.append(f'500 review: estados {estados} (esperado rascunho)')
    for bloco in (BLOCO_CAP3, BLOCO_CAP4):
        if bloco not in dados['review']['editorial_blocks']:
            falhas.append(f"500 review: falta o bloco do capítulo "
                          f"{bloco['chapter']} desta lapidação")
    biblio = [i for i in dados.get('bibliography', [])
              if i.get('papel') == 'evidência']
    if not biblio or 'capítulos 1–4' not in biblio[0].get('attribution', ''):
        falhas.append('500 bibliografia: âmbito da colação não é 1–4')
    cntr = [i for i in dados.get('bibliography', [])
            if i.get('name', '').startswith('CNTR')]
    if not cntr or 'P45' not in cntr[0].get('attribution', ''):
        falhas.append('500 bibliografia: P45 fora das testemunhas CNTR')
    for entrada in HISTORICO:
        if entrada not in dados.get('history', []):
            falhas.append(f"500 history: falta {entrada['model']} "
                          f"{entrada['chapter']}:{entrada['verse_from']}")
    return falhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verificar', action='store_true',
                    help='confere o estado sem escrever')
    args = ap.parse_args()

    dados = json.loads(DADOS.read_text(encoding='utf-8'))
    colacao = json.loads(COLACAO.read_text(encoding='utf-8'))
    relatorio: list[str] = []
    if args.verificar:
        falhas = conferir(dados, colacao)
    else:
        antes = json.dumps(dados, ensure_ascii=False)
        aplicar(dados, colacao, relatorio)
        falhas = conferir(dados, colacao)
        if not falhas and json.dumps(dados, ensure_ascii=False) != antes:
            temporario = DADOS.with_suffix('.tmp')
            with temporario.open('w', encoding='utf-8') as fh:
                json.dump(dados, fh, ensure_ascii=False, indent=2)
                fh.write('\n')
            os.replace(temporario, DADOS)

    for linha in relatorio:
        print(' ', linha)
    if falhas:
        print('\nFALHAS:')
        for f in falhas:
            print(' -', f)
        return 1
    if args.verificar:
        print('\nOK: João 3:34–36 e 4:1–28 conferem com a lapidação '
              'de 2026-11-20.')
    else:
        print(f'\nOK: {len(relatorio)} alterações aplicadas e conferidas.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
