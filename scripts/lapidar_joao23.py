#!/usr/bin/env python3
"""Lapidação de João 2 (fechado) e João 3 (em curso) — 2026-11-20.

Os capítulos 2 e 3 de João foram produzidos na nuvem pelo código antigo,
antes do protocolo da memória v1.4, e guardam os vícios dessa geração:

* quatro versículos (2:7, 2:17, 2:21, 3:9) são marcadores de quarentena
  («[Versículo pendente: tradução ainda não produzida…]») guardados como se
  fossem texto — o capítulo 2 estava até dado como completo;
* as notas de Crítica Textual citam testemunhas que ninguém colacionou
  («segue os manuscritos alexandrinos principais», 2:11), confundem edições
  com manuscritos («o Textus Receptus com o Textus Receptus (RP)», 2:11),
  afirmam o contrário da colação (3:31) ou escondem a variante atrás de
  «[[ ]]» (2:1, 2:5, 2:6, 2:15, 3:23, 3:24, 3:27);
* há gralhas nas secções lexicais («vendentem», «ergueré», «téns guardado»,
  letras latinas dentro de palavras gregas: «ἐξέβαλen», «διέτριβen»);
* textos com o paradigma proibido de «vós» («Tirai», «Destruí»), «lhes» por
  «a vocês» (3:12), gerúndio por fazer («estava a batizar», 3:23/3:26),
  pontuação fora da forma da casa (3:2–3:5) e dois desvios da base fixada
  (2:12 e 3:16 liam o possessivo que a base não tem).

Este script, e só isto:

1. traduz editorialmente os quatro versículos pendentes, da base, palavra
   por palavra, e dá-lhes nota completa (léxica, crítica, síntese);
2. regenera a Crítica Textual dos 58 versículos a partir do aparato da
   SBLGNT e do relatório de colação CNTR aparado aos capítulos 1–3
   (``docs/colacao/João.json``), com o nível de certeza da casa (A: variante
   só bizantina; B: edições críticas divididas — docs/CRITICA_TEXTUAL.md
   §10). Os únicos manuscritos citados são os dos quatro factos de colação
   lidos verso a verso no relatório (``CT_EXTRA``);
3. corrige as gralhas lexicais e a síntese de 3:22, que dizia o contrário
   do texto («deixa a Judeia», quando Jesus entra nela);
4. repõe a base onde o texto a tinha trocado pela leitura de NA28/RP
   (2:12, 3:16), uniformiza «unigénito» (3:16, 3:18) e normaliza registo
   e pontuação como em João 1 (scripts/lapidar_seis.py);
5. regista cada decisão de fundo em Nota de redação e acrescenta os blocos
   de revisão dos capítulos 2 e 3. Nada se aprova: João continua RASCUNHO
   e o capítulo 3 continua ``in_progress``.

Uso::

    python3 scripts/lapidar_joao23.py             # aplica e guarda
    python3 scripts/lapidar_joao23.py --verificar # confere sem escrever
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / 'scripts'))

import lapidar_seis as lapidar          # normalização mecânica da casa
import migrar_notas_cinco as mig        # parsing do aparato (só edições)

DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '500_Joao.json'
COLACAO = RAIZ / 'docs' / 'colacao' / 'João.json'

MODELO_EDITORIAL = 'editorial:lapidacao-joao-2-3'
CARIMBO = '2026-11-20T12:00:00+00:00'

ZONAS = (('chapters', 2), ('in_progress', 3))

# ---------------------------------------------------------------------------
# 1. Versículos que eram marcadores de quarentena — tradução editorial da base
# ---------------------------------------------------------------------------

TEXTOS_COMPLETOS: dict[tuple[int, int], str] = {
    (2, 7): 'Jesus disse-lhes: «Encham as talhas de água.» '
            'E encheram-nas até acima.',
    (2, 17): 'Os seus discípulos lembraram-se de que está escrito: '
             '«O zelo da tua casa me consumirá.»',
    (2, 21): 'Mas ele falava do santuário do seu corpo.',
    (3, 9): 'Nicodemos respondeu-lhe: «Como podem estas coisas acontecer?»',
}

NOTAS_COMPLETAS: dict[tuple[int, int], tuple[str, str]] = {
    (2, 7): (
        '<p><b>Análise Léxica:</b> <i>γεμίζω</i> (gemízō) — encher; '
        '<i>ὑδρία</i> (hydría) — talha, vasilha grande para água (as seis '
        'do v. 6); <i>ἕως ἄνω</i> (héōs ánō) — até acima, até ao cimo.</p>',
        '<p><b>Síntese Exegética:</b> Jesus manda encher de água as talhas '
        'da purificação e os serventes enchem-nas até acima: a obediência é '
        'completa antes de se revelar o que vai acontecer àquela água '
        '(v. 9).</p>'),
    (2, 17): (
        '<p><b>Análise Léxica:</b> <i>μιμνῄσκομαι</i> (mimnḗiskomai) — '
        'lembrar-se, vir à memória; <i>ζῆλος</i> (zêlos) — zelo, ardor; '
        '<i>καταφάγεται</i> (kataphágetai) — consumirá, devorará (futuro '
        'de <i>κατεσθίω</i>).</p>',
        '<p><b>Síntese Exegética:</b> Os discípulos leem a purificação do '
        'templo à luz da Escritura: «O zelo da tua casa me consumirá» é a '
        'palavra do Salmo 69, aplicada aqui ao zelo de Jesus pela casa do '
        'Pai (v. 16).</p>'),
    (2, 21): (
        '<p><b>Análise Léxica:</b> <i>ναός</i> (naós) — santuário, a parte '
        'interior e sagrada do templo (assim nos vv. 19–20); <i>σῶμα</i> '
        '(sôma) — corpo.</p>',
        '<p><b>Síntese Exegética:</b> O narrador levanta o véu do enigma '
        'do v. 19: o santuário de que Jesus falava é o seu corpo; a '
        'destruição e o levantamento em três dias apontam para a morte e '
        'a ressurreição, como os discípulos entenderam depois (v. 22).</p>'),
    (3, 9): (
        '<p><b>Análise Léxica:</b> <i>ἀποκρίνομαι</i> (apokrínomai) — '
        'responder; <i>δύναται</i> (dýnatai) — pode, é possível; '
        '<i>γενέσθαι</i> (genésthai) — acontecer, vir a ser.</p>',
        '<p><b>Síntese Exegética:</b> A pergunta de Nicodemos confessa o '
        'limite do entendimento: como pode acontecer o nascimento do '
        'alto? A resposta de Jesus aprofunda o ensino nos vv. 10–15.</p>'),
}

# ---------------------------------------------------------------------------
# 2. Textos — (capítulo, verso, trecho antigo, trecho novo)
# ---------------------------------------------------------------------------

TEXTOS: list[tuple[int, int, str, str]] = [
    # 2:9 continua em 2:10 («e disse-lhe»): vírgula de fim de verso (cf. 1:12).
    (2, 9, 'chamou o noivo', 'chamou o noivo,'),
    # A base não tem αὐτοῦ depois de ἀδελφοί (ver Crítica Textual, nível B).
    (2, 12, 'a sua mãe, os seus irmãos e os seus discípulos',
            'a sua mãe, os irmãos e os seus discípulos'),
    # Imperativo plural na forma da casa («vocês»), como 2:5 e 2:8.
    (2, 16, '«Tirai isto daqui', '«Tirem isto daqui'),
    # ὅτι é causal: o sinal é pedido porque Jesus faz estas coisas.
    (2, 18, '«Que sinal nos mostras para fazeres estas coisas?»',
            '«Que sinal nos mostras, visto que fazes estas coisas?»'),
    (2, 19, '«Destruí este santuário', '«Destruam este santuário'),
    # Ponto dentro das aspas, a forma da casa (cf. 1:43, 1:45–1:48).
    (3, 2, 'se Deus não estiver com ele».',
           'se Deus não estiver com ele.»'),
    (3, 3, 'não pode ver o reino de Deus».',
           'não pode ver o reino de Deus.»'),
    (3, 4, 'e nascer?».', 'e nascer?»'),
    (3, 5, 'não pode entrar no reino de Deus».',
           'não pode entrar no reino de Deus.»'),
    # ἄνωθεν «de novo», como em 3:3; fim ao artefacto «<i>.</i>».
    (3, 7, 'Não te andes a admirar por eu te ter dito: '
           '«convém que vocês nasçam do alto»<i>.</i>',
           'Não te admires por eu te ter dito: '
           '«É necessário que vocês nasçam de novo.»'),
    # ὑμῖν é «a vocês», segunda pessoa, não «lhes».
    (3, 12, 'Se lhes falei de coisas terrestres e não acreditam, '
            'como acreditarão se lhes falar de coisas celestiais?',
            'Se falei a vocês de coisas terrestres e não acreditam, '
            'como acreditarão se falar a vocês de coisas celestiais?'),
    # A base não tem αὐτοῦ depois de υἱόν; μονογενής é «unigénito» (1:18).
    (3, 16, 'que deu o seu Filho único, para que',
            'que deu o Filho unigénito, para que'),
    (3, 18, 'no nome do Filho único de Deus',
            'no nome do Filho unigénito de Deus'),
    # A casa usa gerúndio (cf. 1:28).
    (3, 23, 'João também estava a batizar em Enom',
            'João também estava batizando em Enom'),
    (3, 26, 'ele está a batizar e todos vão ter com ele',
            'ele está batizando e todos vão ter com ele'),
]

# ---------------------------------------------------------------------------
# 3. Notas — gralhas e a síntese de 3:22 (trecho antigo → trecho novo)
# ---------------------------------------------------------------------------

FRAGMENTOS: list[tuple[int, int, str, str]] = [
    (2, 10, '«téns guardado»', '«tens guardado»'),
    (2, 14, 'os que vendentem', 'os que vendem'),
    (2, 14, 'probatata', 'próbata'),
    (2, 15, 'ἐξέβαλen', 'ἐξέβαλεν'),
    (2, 19, '(lysamate/lysate)', '(lýsate)'),
    (2, 19, '«levantarei» ou «ergueré»', '«levantarei»'),
    (3, 21, 'tornar visible', 'tornar visível'),
    (3, 22, 'διέτριβen', 'διέτριβεν'),
    # «Aἰνὼν» com A latino (U+0041) em vez do alfa grego (U+0391).
    (3, 23, 'Aἰνὼν',
            'Αἰνὼν'),
    (3, 22, 'Jesus deixa a Judeia em direção ao campo onde os seus '
            'discípulos realizam batismos semelhantes aos de João, '
            'marcando uma transição geográfica e ministerial na narrativa.',
            'Depois do diálogo com Nicodemos, Jesus sai de Jerusalém com '
            'os discípulos para a região da Judeia, onde permanece com '
            'eles e batizava, ao mesmo tempo que João (v. 23).'),
]

# ---------------------------------------------------------------------------
# 4. Crítica Textual — factos de colação lidos no relatório (só CNTR de João)
# ---------------------------------------------------------------------------

CT_EXTRA: dict[tuple[int, int], str] = {
    (2, 12): 'Na colação, 02 e P66 acrescentam o possessivo '
             '(«os irmãos dele»), com NA28/RP; 03 e P75 leem com a base.',
    (2, 19): 'Na colação, 01 lê «ὁ Ἰησοῦς», com o artigo, como o Textus '
             'Receptus de Scrivener; a base omite o artigo.',
    (3, 13): 'Na colação, 01, 03, P66 e P75 leem com a base; o acréscimo '
             '«que está no céu» aparece em 02, com Tregelles e RP.',
    (3, 25): 'Na colação, 01 e P66 leem o plural «dos judeus», com o '
             'Textus Receptus de Scrivener; P75 lê o singular com a base.',
}


def critica_textual(cap: int, verso: int, item_col: dict) -> str:
    """Crítica Textual gerada do aparato (edições) + nível de certeza.

    A fraseologia é a de ``scripts/migrar_notas_cinco.py``, já provada nos
    cinco livros curtos; a frase dos versículos sem aparato é ajustada à
    colação de João, onde também há transposições e leituras partilhadas
    que nenhuma edição imprime — dizer «só leituras singulares» seria falso.
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
    extra = CT_EXTRA.get((cap, verso))
    if extra:
        frases.append(extra)
    return '<p><b>Crítica Textual:</b> ' + ' '.join(frases) + '</p>'


# ---------------------------------------------------------------------------
# 5. Notas de redação — uma por decisão de fundo
# ---------------------------------------------------------------------------

NOTA_PENDENTE = (
    '<p><b>Nota de redação:</b> Este versículo estava guardado como '
    'marcador de quarentena da produção automática, sem tradução; o texto '
    'e a nota são editoriais, desta lapidação (2026-11-20), feitos da '
    'base fixada. O capítulo continua RASCUNHO.</p>')

NOTAS_REDACAO: dict[tuple[int, int], str] = {
    (2, 12): '<p><b>Nota de redação:</b> O texto anterior lia «os seus '
             'irmãos», com NA28/RP; a base (SBLGNT, WH, Tregelles) não '
             'traz o possessivo depois de «irmãos» e o texto volta à base '
             '(ver Crítica Textual, nível B).</p>',
    (2, 16): '<p><b>Nota de redação:</b> «Tirai» deu «Tirem»: o '
             'tratamento plural da casa é «vocês», como já em 2:5 '
             '(«Façam») e 2:8 («tirem»); o paradigma de «vós» está '
             'proibido no texto (memória de estilo).</p>',
    (2, 18): '<p><b>Nota de redação:</b> O texto anterior lia «Que sinal '
             'nos mostras para fazeres estas coisas», como se o sinal '
             'servisse para fazer; o grego tem <i>ὅτι</i> causal: o sinal '
             'é pedido porque Jesus faz estas coisas.</p>',
    (2, 19): '<p><b>Nota de redação:</b> «Destruí» deu «Destruam», pelo '
             'mesmo motivo de 2:16: imperativo plural na forma da casa '
             '(«vocês»).</p>',
    (3, 7): '<p><b>Nota de redação:</b> O texto anterior misturava «tu» '
            'com um artefacto de marcação («&lt;i&gt;.&lt;/i&gt;») e lia '
            '«nasçam do alto»; <i>ἄνωθεν</i> fica «de novo», como em 3:3, '
            'e a dupla nuance («do alto») está registada na Análise '
            'Léxica.</p>',
    (3, 12): '<p><b>Nota de redação:</b> «Se lhes falei» deu «Se falei a '
             'vocês»: <i>ὑμῖν</i> é segunda pessoa («a vocês»), não '
             'terceira («lhes»); Jesus fala a Nicodemos em nome dos seus '
             '(cf. 3:11, «vocês não aceitam»).</p>',
    (3, 16): '<p><b>Nota de redação:</b> O texto anterior lia «deu o seu '
             'Filho único»: a base não traz <i>αὐτοῦ</i> depois de '
             '«Filho» (o possessivo é de Tregelles/RP) e <i>μονογενής</i> '
             'é «unigénito», o termo da casa (1:14, 1:18).</p>',
    (3, 18): '<p><b>Nota de redação:</b> «Filho único» deu «Filho '
             'unigénito»: <i>μονογενής</i> tem um só termo na casa '
             '(1:14, 1:18; 3:16).</p>',
    (3, 23): '<p><b>Nota de redação:</b> «estava a batizar» deu «estava '
             'batizando»: a casa usa o gerúndio (cf. 1:28).</p>',
    (3, 26): '<p><b>Nota de redação:</b> «está a batizar» deu «está '
             'batizando»: a casa usa o gerúndio (cf. 1:28).</p>',
}
for _ref in TEXTOS_COMPLETOS:
    NOTAS_REDACAO[_ref] = NOTA_PENDENTE

BLOCOS_REVISAO = [
    {'chapter': 2, 'verse_from': 1, 'verse_to': 25, 'status': 'rascunho',
     'nota': 'Capítulo 2 lapidado em 2026-11-20 por '
             'scripts/lapidar_joao23.py: os versículos 7, 17 e 21 eram '
             'marcadores de quarentena dados como texto completo e foram '
             'traduzidos editorialmente da base; a Crítica Textual dos 25 '
             'versículos foi refeita do aparato da SBLGNT e da colação '
             'CNTR (docs/colacao/João.json, capítulos 1–3), com níveis de '
             'certeza; registo («vocês», gerúndio) e pontuação '
             'normalizados. Continua RASCUNHO.'},
    {'chapter': 3, 'verse_from': 1, 'verse_to': 33, 'status': 'rascunho',
     'nota': 'Capítulo em curso: os 33 versículos já produzidos foram '
             'lapidados em 2026-11-20 por scripts/lapidar_joao23.py (3:9 '
             'era marcador de quarentena, traduzido editorialmente; '
             'Crítica Textual refeita como no capítulo 2). Os versículos '
             'seguintes continuam por produzir. Continua RASCUNHO.'},
]

# ---------------------------------------------------------------------------
# Aplicação
# ---------------------------------------------------------------------------

CABECALHO_FORA = re.compile(
    r'<b>(Análise Léxica|Crítica Textual|Síntese Exegética)</b>:')


def _versos(dados: dict, zona: str, cap: int) -> list[dict]:
    return dados[zona][str(cap)]


def aplicar(dados: dict, colacao: dict, relatorio: list[str]) -> None:
    for zona, cap in ZONAS:
        for v in _versos(dados, zona, cap):
            vv = v['verse']
            ref = f'{cap}:{vv}'
            item_col = colacao['versiculos'][ref]
            ct = critica_textual(cap, vv, item_col)

            # --- texto ---
            if (cap, vv) in TEXTOS_COMPLETOS:
                if not v['text'].startswith('[Versículo pendente'):
                    raise SystemExit(f'{ref}: já não é marcador pendente')
                v['text'] = TEXTOS_COMPLETOS[(cap, vv)]
                relatorio.append(f'500 {ref} texto reconstruído da base')
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
            nota = CABECALHO_FORA.sub(r'<b>\1:</b>', v['commentary'])
            if (cap, vv) in NOTAS_COMPLETAS:
                lx, sintese = NOTAS_COMPLETAS[(cap, vv)]
                nota = lx + ct + sintese
                relatorio.append(f'500 {ref} nota completa (era pendente)')
            else:
                secoes = mig.secoes(nota)
                atuais = dict(secoes)
                for seccao in ('Análise Léxica', 'Crítica Textual',
                               'Síntese Exegética'):
                    if seccao not in atuais:
                        raise SystemExit(f'{ref}: falta a secção {seccao}')
                extras = [p for r, p in secoes
                          if r not in ('Análise Léxica', 'Crítica Textual',
                                       'Síntese Exegética')]
                nota = (atuais['Análise Léxica'] + ct
                        + atuais['Síntese Exegética'] + ''.join(extras))
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
    for bloco in BLOCOS_REVISAO:
        if not any(b['chapter'] == bloco['chapter'] for b in blocos):
            blocos.append(bloco)
    dados.setdefault('history', []).extend([
        {'chapter': 2, 'verse_from': 1, 'verse_to': 25, 'provider': 'local',
         'model': MODELO_EDITORIAL, 'generated_at_utc': CARIMBO},
        {'chapter': 3, 'verse_from': 1, 'verse_to': 33, 'provider': 'local',
         'model': MODELO_EDITORIAL, 'generated_at_utc': CARIMBO},
    ])


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
    for zona, cap in ZONAS:
        versos = _versos(dados, zona, cap)
        esperado = 25 if cap == 2 else 33
        if len(versos) != esperado:
            falhas.append(f'500 cap. {cap}: {len(versos)} versículos '
                          f'(esperados {esperado})')
        for v in versos:
            vv, ref = v['verse'], f'{cap}:{v["verse"]}'
            t, n = v['text'], v['commentary']
            for proibido in ('pendente', 'Pendente', 'Pendente'):
                if proibido in t or proibido in n:
                    falhas.append(f'500 {ref}: ainda tem «{proibido}»')
            for proibido in ('[[', ']]', '&quot;', '&#', '<strong>',
                             '“', '”', '‘', '’', '\u2011',
                             'Textus Receptus (RP)', 'testemunhos alexandrinos'):
                if proibido in n:
                    falhas.append(f'500 {ref}: nota ainda tem «{proibido}»')
            for proibido in ('\u2011', 'estava a batizar',
                             'está a batizar', 'Filho único'):
                if proibido in t:
                    falhas.append(f'500 {ref}: texto ainda tem «{proibido}»')
            for seccao in ('Análise Léxica', 'Crítica Textual',
                           'Síntese Exegética'):
                if f'<b>{seccao}:</b>' not in n:
                    falhas.append(f'500 {ref}: falta a secção {seccao}')
            ct = critica_textual(cap, vv, colacao['versiculos'][ref])
            if ct not in n:
                falhas.append(f'500 {ref}: Crítica Textual não é a gerada')
            for (c, v2), nota_red in NOTAS_REDACAO.items():
                if (c, v2) == (cap, vv) and nota_red not in n:
                    falhas.append(f'500 {ref}: falta a Nota de redação')
            for c, v2, velho, novo in TEXTOS:
                if (c, v2) == (cap, vv) and novo not in t:
                    falhas.append(f'500 {ref}: falta «{novo[:40]}» no texto')
            if (cap, vv) in TEXTOS_COMPLETOS \
                    and t != TEXTOS_COMPLETOS[(cap, vv)]:
                falhas.append(f'500 {ref}: texto reconstruído não confere')
            if t.count('«') != t.count('»'):
                falhas.append(f'500 {ref}: aspas desequilibradas no texto')
            if n.count('«') != n.count('»'):
                falhas.append(f'500 {ref}: aspas desequilibradas na nota')
            for tok in _token_misto(n) + _token_misto(t):
                falhas.append(f'500 {ref}: palavra greco-latina mista '
                              f'«{tok}»')
    estados = {b['status'] for b in dados['review']['editorial_blocks']}
    if estados != {'rascunho'}:
        falhas.append(f'500 review: estados {estados} (esperado rascunho)')
    for cap in (2, 3):
        if not any(b['chapter'] == cap
                   for b in dados['review']['editorial_blocks']):
            falhas.append(f'500 review: falta o bloco do capítulo {cap}')
    biblio = [i for i in dados.get('bibliography', [])
              if i.get('papel') == 'evidência']
    if not biblio or 'capítulos 1–3' not in biblio[0].get('attribution', ''):
        falhas.append('500 bibliografia: âmbito da colação não é 1–3')
    if '3' in dados.get('chapters', {}):
        falhas.append('500: o capítulo 3 devia continuar in_progress')
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
        print('\nOK: João 2–3 conferem com a lapidação de 2026-11-20.')
    else:
        print(f'\nOK: {len(relatorio)} alterações aplicadas e conferidas.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
