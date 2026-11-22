#!/usr/bin/env python3
"""Lapidação dos seis livros que não são 2 Tessalonicenses (2026-11-20).

O que este script faz, e só isto:

1. João (500) — corrige o texto onde ele se afastava da base SBLGNT ou da
   ortografia da casa, e reescreve as notas que citavam testemunhas não
   fornecidas, atribuíam a edições impressas o nome de manuscritos, ou
   registavam uma variante que o aparato não tem.
2. Tito (630) — migra a nota do piloto aprovado (``edicoes/piloto/dados``)
   para a secção Síntese Exegética, que estava por preencher, e corrige a
   pontuação de fim de verso.
3. Judas (720) — dois retoques de redação no v. 7.
4. Normalização mecânica das notas de João: cabeçalhos, aspas, hífenes e
   entidades HTML.

Nada aqui inventa leitura, testemunha ou definição. Cada alteração de texto
num livro aprovado pelo responsável recebe uma **Nota de redação** na nota do
versículo, como manda o perfil (``bee/perfil.py``).

Uso::

    python3 scripts/lapidar_seis.py            # aplica e guarda
    python3 scripts/lapidar_seis.py --verificar # confere sem escrever
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
DADOS = RAIZ / 'edicoes/nova' / 'livros_json'
# Nota (2026-11-22): execução única já feita. `edicoes/piloto/dados/` e `2_E_3_JOAO.md` foram removidos;
# para recuperar a origem: `git show de2f6af:edicoes/piloto/dados/<ficheiro>`.
PILOTO = RAIZ / 'edicoes' / 'piloto' / 'dados'

MODELO_EDITORIAL = 'editorial:lapidacao-seis-livros'
CARIMBO = '2026-11-20T10:00:00+00:00'

SECÇÕES = (
    'Análise Léxica',
    'Crítica Textual',
    'Síntese Exegética',
    'Hermenêutica e Contexto',
    'Geografia e História',
    'Nota de redação',
)

# --------------------------------------------------------------------------
# 1. Texto dos versículos — (capítulo, verso, trecho antigo, trecho novo)
# --------------------------------------------------------------------------

TEXTOS: dict[int, list[tuple[int, int, str, str]]] = {
    500: [
        # πᾶς anártrico: em português europeu o artigo é gramatical.
        (1, 9, 'ilumina todo homem que vem', 'ilumina todo o homem que vem'),
        # 1:12 termina em vírgula: 1:13 é a relativa «os que não nasceram…».
        (1, 12, 'aos que creem no seu nome.', 'aos que creem no seu nome,'),
        # μονογενοῦς παρὰ πατρός é procedência, não posse; e grafia portuguesa.
        (1, 14, 'glória como a do unigênito do Pai,',
                'glória como a do unigénito que vem do Pai,'),
        # πρῶτός μου ἦν: ele era anterior a João, não o contrário.
        (1, 15, 'O que vem depois de mim tornou-se antes de mim, porque eu o precedi.',
                'O que vem depois de mim passou à minha frente, porque existia antes de mim.'),
        # μονογενὴς θεὸς é a leitura da base; «o Filho unigênito» é a de RP/TR.
        (1, 18, 'Ninguém jamais viu a Deus; o Filho unigênito, que está no seio do Pai, o revelou.',
                'Ninguém jamais viu a Deus; Deus, o unigénito, que está no seio do Pai, o revelou.'),
        # ἦν βαπτίζων: imperfeito + particípio presente = gerúndio na casa.
        (1, 28, 'onde João estava a batizar.', 'onde João estava batizando.'),
        # ἔμπροσθέν μου γέγονεν, a mesma cláusula de 1:15.
        (1, 30, 'que passou a estar diante de mim,', 'que passou à minha frente,'),
        # ἔμεινεν ἐπʼ αὐτόν: um só pronome.
        (1, 32, 'como pomba, e ele pousou sobre ele.»', 'como pomba, e permaneceu sobre ele.»'),
        # Fala de primeira linha: aspas da casa, não aspas curvas.
        (1, 33, 'disse-me: “Aquele sobre quem vires o Espírito descer e pousar, esse é o que batiza com o Espírito Santo.”',
                'disse-me: «Aquele sobre quem vires o Espírito descer e pousar, esse é o que batiza com o Espírito Santo.»'),
        # 1:35 continua em 1:36 com minúscula.
        (1, 35, 'com dois dos seus discípulos', 'com dois dos seus discípulos,'),
        # Ponto final dentro das aspas, como no resto da edição.
        (1, 43, 'diz-lhe: «Segue-me».', 'diz-lhe: «Segue-me.»'),
        (1, 45, 'Jesus, filho de José, o de Nazaré».', 'Jesus, filho de José, o de Nazaré.»'),
        (1, 46, '«De Nazaré pode vir alguma coisa boa?». Filipe diz-lhe: «Vem e vê».',
                '«De Nazaré pode vir alguma coisa boa?» Filipe diz-lhe: «Vem e vê.»'),
        (1, 47, 'em quem não há falsidade».', 'em quem não há falsidade.»'),
        (1, 48, '«De onde me conheces?». Jesus respondeu e disse-lhe: '
                '«Antes de Filipe te chamar, quando estavas debaixo da figueira, eu vi-te».',
                '«De onde me conheces?» Jesus diz-lhe: '
                '«Antes de Filipe te chamar, quando estavas debaixo da figueira, eu vi-te.»'),
        # καὶ λέγει αὐτῷ é presente histórico, e a casa usa ênclise.
        (1, 51, 'E ele lhe disse: «Amém, amém,', 'E diz-lhe: «Amém, amém,'),
        (1, 51, 'descendo sobre o Filho do Homem».', 'descendo sobre o Filho do Homem.»'),
    ],
    630: [
        # §5.1: verso que continua no seguinte termina em vírgula.
        (1, 13, 'para que sejam sadios na fé', 'para que sejam sadios na fé,'),
        (2, 7, 'mostra integridade, seriedade', 'mostra integridade, seriedade,'),
        (2, 9, 'sem responder com insolência', 'sem responder com insolência,'),
        # πᾶς anártrico: artigo gramatical do português europeu.
        (2, 14, 'resgatar de toda iniquidade', 'resgatar de toda a iniquidade'),
        (3, 1, 'prontos para toda boa obra', 'prontos para toda a boa obra'),
        (3, 2, 'mostrem toda mansidão', 'mostrem toda a mansidão'),
        # ποικίλαις é «variados», não «de todo o tipo».
        (3, 3, 'desejos e prazeres de todo tipo', 'desejos e prazeres variados'),
    ],
    720: [
        (1, 7, 'uma carne diferente, de modo semelhante a esses. Elas ficam como exemplo,',
               'uma carne diferente, tal como aqueles. Estão postas como exemplo,'),
    ],
}

# --------------------------------------------------------------------------
# 2. Notas reescritas — (capítulo, verso, nota completa)
# --------------------------------------------------------------------------

JOAO_9 = (
    '<p><b>Análise Léxica:</b> <i>ἀληθινόν</i> (alēthinón) não é apenas «verdadeiro»: '
    'designa o que é real por oposição à aparência, e é o mesmo adjetivo de 4:23 e 15:1. '
    '<i>φωτίζει</i> (phōtízei) está no presente: a iluminação é contínua, não um ato único. '
    '<i>πάντα ἄνθρωπον</i> (pánta ánthrōpon) é anártrico e distributivo: cada homem. '
    '<i>ἐρχόμενον εἰς τὸν κόσμον</i> (erchómenon eis tòn kósmon) pode qualificar '
    '<i>ἄνθρωπον</i> («todo o homem que vem ao mundo») ou <i>φῶς</i> («a luz que, ao vir ao '
    'mundo, ilumina todo o homem»); adota-se a primeira, que é a mais simples e a que a '
    'pontuação da base favorece.</p>'
    '<p><b>Crítica Textual:</b> O aparato SBLGNT não regista variante neste versículo e o '
    'Textus Receptus de Scrivener coincide com a base. Nada a decidir.</p>'
    '<p><b>Síntese Exegética:</b> Identifica Cristo como a luz autêntica que ilumina todo o '
    'homem que vem ao mundo, e prepara o v. 10, onde o mundo não o reconhece.</p>'
    '<p><b>Nota de redação:</b> A redação anterior dizia «todo homem». Em português europeu o '
    'artigo depois de <i>todo</i> no singular é gramatical e não traduz o artigo grego: a '
    'Almeida de 1911, impressa em Portugal, escreve «a todo o homem» exatamente onde o grego é '
    'anártrico — documento de língua, não evidência textual. O facto grego fica aqui: '
    '<i>πάντα ἄνθρωπον</i> não tem artigo, e por isso distribui.</p>'
)

JOAO_14 = (
    '<p><b>Análise Léxica:</b> <i>σὰρξ ἐγένετο</i> (sàrx egéneto) é «fez-se carne»: '
    '<i>σάρξ</i> é a humanidade concreta e mortal, não a natureza pecaminosa. '
    '<i>ἐσκήνωσεν</i> (eskḗnōsen) vem de <i>σκηνή</i>, «tenda»: literalmente «armou a tenda '
    'entre nós». A redação usa «habitou», que é o verbo corrente; a imagem da tenda fica aqui e '
    'é ela que dá peso ao «entre nós». <i>ἐθεασάμεθα</i> (etheasámetha) é aoristo e primeira '
    'pessoa do plural: «contemplámos», de testemunhas oculares. <i>μονογενοῦς παρὰ πατρός</i> '
    '(monogenoûs parà patrós) é «unigénito que vem do Pai»: <i>παρὰ</i> com genitivo indica '
    'procedência, não posse. <i>πλήρης χάριτος καὶ ἀληθείας</i> (plḗris cháritos kaì '
    'alētheías) forma um par que o v. 17 repete.</p>'
    '<p><b>Crítica Textual:</b> O aparato SBLGNT não regista variante e o Textus Receptus de '
    'Scrivener coincide com a base. A diferença para o v. 18 não é de variante: aqui a base lê '
    '<i>μονογενοῦς</i> sem substantivo, ali lê <i>μονογενὴς θεὸς</i>.</p>'
    '<p><b>Síntese Exegética:</b> Afirma a encarnação do Verbo, a sua presença real entre os '
    'homens e a revelação da sua glória divina.</p>'
    '<p><b>Nota de redação:</b> «unigênito» era grafia brasileira; a casa escreve «unigénito». '
    'E «a glória do unigénito do Pai» dava como posse o que o grego diz como origem: '
    '<i>παρὰ πατρός</i> é «que vem do Pai».</p>'
)

JOAO_15 = (
    '<p><b>Análise Léxica:</b> <i>μαρτυρεῖ</i> (martirei) e <i>κέκραγεν</i> (kekrāgen) são '
    'presentes: João «testemunha» e «clama» no momento em que se lê. <i>λέγων</i> (legōn) é '
    'particípio de modo e fica subordinado: a casa pontua «clama:» em vez de «clama, dizendo». '
    '<i>ὁ ὀπίσω μου ἐρχόμενος</i> (ho opíso mou erchómenos) é «o que vem depois de mim», '
    'ordem de ministério e não de tempo. <i>ἔμπροσθέν μου γέγονεν</i> (émprosthen mou gégonen) '
    'é perfeito de <i>γίνομαι</i>: «passou à minha frente», um estado adquirido. '
    '<i>πρῶτός μου ἦν</i> (prōtós mou ēn) é «existia antes de mim»: <i>πρῶτος</i> com '
    'genitivo diz anterioridade, e <i>ἦν</i> é o imperfeito que o prólogo usa para a existência '
    'anterior do Verbo (1:1, 1:2).</p>'
    '<p><b>Crítica Textual:</b> A base lê <i>ὃν εἶπον</i>, «aquele de quem eu falei»; o '
    'aparato regista <i>ὁ εἰπών</i> em WH. O Textus Receptus de Scrivener coincide com a base. '
    'Sem colação para João, nenhuma leitura é atribuída a códice ou papiro: o aparato nomeia '
    'edições. <b>Nível de certeza A</b> para o resto do versículo, idêntico nas duas '
    'edições.</p>'
    '<p><b>Síntese Exegética:</b> João declara a preexistência de Cristo: embora venha depois '
    'dele na ordem do ministério, Jesus já existia antes dele.</p>'
    '<p><b>Nota de redação:</b> Três correções. (1) «porque eu o precedi» invertia o grego: '
    '<i>πρῶτός μου ἦν</i> diz que <b>ele</b> era anterior a João, e 1:30, que traz a mesma '
    'cláusula, já a traduzia bem — o livro contradizia-se a si mesmo. (2) «tornou-se antes de '
    'mim» deu «passou à minha frente», a mesma fórmula de 1:30 para o mesmo grego. (3) A nota '
    'anterior atribuía ao aparato uma variante «<i>ὃν ἔλεγον</i>» que o aparato não regista; a '
    'leitura divergente é <i>ὁ εἰπών</i>, em WH.</p>'
)

JOAO_18 = (
    '<p><b>Análise Léxica:</b> <i>οὐδεὶς ἑώρακεν πώποτε</i> (oudeìs heṓraken pṓpote) é '
    'perfeito: ninguém viu a Deus em momento nenhum, e o estado permanece. '
    '<i>μονογενὴς θεὸς</i> (monogenḕs theòs) é a leitura da base; <i>μονογενής</i> é «único '
    'no seu género», e <i>θεὸς</i> vem sem artigo, como em 1:1. <i>ὁ ὢν εἰς τὸν κόλπον τοῦ '
    'πατρὸς</i> (ho ṑn eis tòn kólpon toû patrós) é «o que está no seio do Pai»: '
    '<i>κόλπος</i> diz intimidade, não localização. <i>ἐξηγήσατο</i> (exēgḗsato) é o aoristo '
    'de <i>ἐξηγέομαι</i>, «explicar, dar a conhecer» — o verbo de que vem «exegese».</p>'
    '<p><b>Crítica Textual:</b> Unidade com decisão de texto. A base lê <i>μονογενὴς θεὸς</i>, '
    'sem artigo; o aparato regista <i>ὁ μονογενὴς υἱός</i> em RP, e o Textus Receptus de '
    'Scrivener acompanha RP. <b>Decisão: seguir a base</b> — «Deus, o unigénito». O argumento '
    'transcricional é claro: <i>θεὸς</i> é a leitura mais difícil, e um escriba tenderia a '
    'suavizá-la para o <i>υἱός</i> que a piedade e a liturgia já consagravam; o caminho '
    'contrário não tem motivo. O argumento intrínseco confirma: o versículo fecha o prólogo '
    'como 1:1 o abre, e João usa <i>θεός</i> sem artigo para o Verbo nos dois extremos. '
    '<b>Nível de certeza B.</b> Sem colação para João, nenhuma leitura é atribuída a códice ou '
    'papiro: o aparato nomeia edições.</p>'
    '<p><b>Síntese Exegética:</b> Embora Deus seja invisível, o unigénito, que está na '
    'intimidade do Pai, deu-o a conhecer.</p>'
    '<p><b>Nota de redação:</b> A redação anterior dizia «o Filho unigênito», que é a leitura '
    'de RP e do Textus Receptus, e a nota afirmava ter escolhido a leitura do SBLGNT: texto e '
    'nota contradiziam-se. O texto segue agora a base, e a grafia é «unigénito».</p>'
)

JOAO_28 = (
    '<p><b>Análise Léxica:</b> <i>ἐγένετο</i> (egéneto) é «aconteceu». <i>πέραν τοῦ '
    'Ἰορδάνου</i> (péran toû Iordánou) é «além do Jordão», a margem oriental. '
    '<i>ἦν ὁ Ἰωάννης βαπτίζων</i> (ēn ho Iṓannēs baptízōn) é imperfeito com particípio '
    'presente: «João estava batizando», uma atividade em curso — não um lugar chamado '
    '«Batismo».</p>'
    '<p><b>Crítica Textual:</b> O aparato regista apenas o artigo: <i>ὁ Ἰωάννης</i> na base '
    '(WH, Tregelles, NA28) contra <i>Ἰωάννης</i> sem artigo em RP. O nome do lugar difere '
    'entre as edições fornecidas: a base lê <i>Βηθανίᾳ</i> e o Textus Receptus de Scrivener '
    '<i>Βηθαβαρᾷ</i>. Segue-se a base. <b>Nível de certeza B:</b> uma edição impressa não é um '
    'manuscrito, e João não tem colação — por isso nenhuma destas leituras é aqui atribuída a '
    'códice, papiro ou família. O texto distingue esta Betânia da de 11:18, que ficava perto de '
    'Jerusalém; a identificação do lugar continua por fazer.</p>'
    '<p><b>Síntese Exegética:</b> O narrador fixa o cenário do testemunho e do batismo de '
    'João, na margem oriental do Jordão, e marca a transição do ministério do precursor para a '
    'revelação de Jesus.</p>'
    '<p><b>Nota de redação:</b> A nota anterior chamava «melhores manuscritos antigos» a WH, '
    'Tregelles e NA28, que são edições impressas, e atribuía-lhes um juízo de valor que nenhuma '
    'fonte fornecida sustenta. O aparato deste versículo não fala de Βηθανία: fala do artigo '
    'antes de <i>Ἰωάννης</i>. No texto, «estava a batizar» deu «estava batizando»: o '
    'particípio presente grego tem gerúndio na casa, e «estar a + infinitivo» não aparece nos '
    'sete livros.</p>'
)

JOAO_30 = (
    '<p><b>Análise Léxica:</b> <i>οὗτος</i> (hoûtos) é «este». <i>ὑπέρ</i> (hypér) e '
    '<i>περί</i> (perí) são ambas «a respeito de». <i>ἀνήρ</i> (anḗr) é «homem» no sentido de '
    'varão adulto, não <i>ἄνθρωπος</i>. <i>ἔμπροσθέν μου γέγονεν</i> (émprosthen mou gégonen) '
    'é perfeito de <i>γίνομαι</i>: passou à minha frente e aí está. <i>πρῶτος</i> (prōtos) com '
    'genitivo é anterioridade: «primeiro do que eu».</p>'
    '<p><b>Crítica Textual:</b> O aparato regista <i>ὑπὲρ</i> (WH, Tregelles, NA28) contra '
    '<i>περὶ</i> (RP), e o Textus Receptus de Scrivener lê <i>περὶ</i>. Segue-se a base. A '
    'diferença é de preposição sinónima e não muda o sentido; <b>nível de certeza A</b>. O '
    'resto do versículo coincide nas duas edições.</p>'
    '<p><b>Síntese Exegética:</b> O testemunho retoma a declaração anterior para sublinhar o '
    'paradoxo: Jesus vem depois na ordem do ministério público e, no entanto, existe antes — é '
    'essa anterioridade que lhe dá a primazia.</p>'
    '<p><b>Nota de redação:</b> «passou a estar diante de mim» deu «passou à minha frente», a '
    'fórmula que 1:15 usa para o mesmo <i>ἔμπροσθέν μου γέγονεν</i>: grego igual, português '
    'igual. A Análise Léxica trazia «γέγονen», com letras latinas dentro da forma grega.</p>'
)

JOAO_34 = (
    '<p><b>Análise Léxica:</b> <i>ἑώρακα</i> (heṓraka) e <i>μεμαρτύρηκα</i> (memartúrēka) são '
    'dois perfeitos: «vi» e «dei testemunho», com o efeito de ambos a permanecer. '
    '<i>ἐκλεκτός</i> (eklektós) é «escolhido, eleito»; <i>υἱός</i> (huiós) é «filho».</p>'
    '<p><b>Crítica Textual:</b> Unidade com decisão de texto. A base lê <i>ὁ ἐκλεκτὸς τοῦ '
    'θεοῦ</i>; o aparato atribui essa leitura a Holmes e à margem de WH, e regista <i>υἱὸς</i> '
    'em WH, Tregelles, NA28 e RP. O Textus Receptus de Scrivener lê <i>ὁ υἱὸς τοῦ θεοῦ</i>. '
    '<b>Decisão: seguir a base</b> — «o escolhido de Deus». <b>Nível de certeza C:</b> a '
    'leitura adotada apoia-se numa conjetura de um editor, aceite pela base e pela margem de WH, '
    'e o apoio que as edições fornecidas lhe dão é estreito. A favor dela está a probabilidade '
    'transcricional: <i>ἐκλεκτὸς</i> é a leitura mais difícil, e um escriba teria motivo para '
    'escrever o <i>υἱός</i> consagrado, não o contrário. Contra ela está o peso da tradição '
    'impressa. Sem colação para João, não se nomeia aqui nenhum códice nem papiro: o aparato '
    'nomeia edições e um editor. Cabe à revisão especializada confirmar.</p>'
    '<p><b>Síntese Exegética:</b> Com base na visão do Espírito, o Batista sela o seu '
    'testemunho e afirma a identidade de Jesus diante dos ouvintes.</p>'
    '<p><b>Nota de redação:</b> A nota anterior escrevia que a base seguia «manuscritos como '
    'P66c, P75, B». Nenhum desses testemunhos consta do aparato fornecido nem existe colação '
    'para João: a citação não tinha fonte e foi retirada. O texto não muda; a decisão passa a '
    'estar registada com o seu nível de certeza.</p>'
)

JOAO_42 = (
    '<p><b>Análise Léxica:</b> <i>ἤγαγεν</i> (ḗgagen) é «levou, conduziu». '
    '<i>ἐμβλέψας</i> (emblépsas) é «fitando, olhando de frente», mais intenso do que o simples '
    '<i>βλέπων</i>. <i>κληθήσῃ</i> (klēthḗsē) é futuro passivo: «serás chamado». '
    '<i>Κηφᾶς</i> (Kēphâs) é o aramaico que o versículo traduz por <i>Πέτρος</i>.</p>'
    '<p><b>Crítica Textual:</b> O aparato regista duas unidades: <i>ἤγαγεν</i> (WH, Tregelles, '
    'NA28) contra <i>καὶ ἤγαγεν</i> (RP), e <i>Ἰωάννου</i> contra <i>Ἰωνᾶ</i> (RP). O '
    'Textus Receptus de Scrivener lê <i>καὶ ἤγαγεν</i> e <i>υἱὸς Ἰωνᾶ</i>. Segue-se a base '
    'nas duas. <b>Nível de certeza B</b> no nome do pai: <i>Ἰωνᾶ</i> é a leitura bizantina e '
    'pode ter sido assimilada a Mateus 16:17, onde o mesmo Simão é chamado «filho de Jonas». '
    'Sem colação para João, nenhuma leitura é atribuída a manuscrito nem a família de '
    'manuscritos.</p>'
    '<p><b>Síntese Exegética:</b> O olhar de Jesus sobre Simão reconhece a sua origem familiar '
    'e ao mesmo tempo lhe dá um nome novo: a identidade vem dele, não da linhagem.</p>'
    '<p><b>Nota de redação:</b> A nota anterior concluía que as leituras «seguem os manuscritos '
    'alexandrinos». O aparato nomeia edições (WH, Tregelles, NA28, RP) e não manuscritos, e não '
    'há colação para João: a atribuição a uma família textual não tinha fonte e foi '
    'retirada.</p>'
)

NOTAS: dict[int, dict[tuple[int, int], str]] = {
    500: {
        (1, 9): JOAO_9,
        (1, 14): JOAO_14,
        (1, 15): JOAO_15,
        (1, 18): JOAO_18,
        (1, 28): JOAO_28,
        (1, 30): JOAO_30,
        (1, 34): JOAO_34,
        (1, 42): JOAO_42,
    },
}

# Fragmentos de nota — (capítulo, verso, trecho antigo, trecho novo)
FRAGMENTOS: dict[int, list[tuple[int, int, str, str]]] = {
    500: [
        (1, 3, 'obra independente de sua participação',
               'obra independente da sua participação'),
        (1, 21, 'interrogatório através de figuras',
                'interrogatório por meio de figuras'),
        (1, 33, 'Sem variante verificada de relevo entre a SBLGNT e o Textus Receptus neste '
                'versículo.',
                'O aparato SBLGNT não regista variante neste versículo e o Textus Receptus de '
                'Scrivener coincide com a base.'),
    ],
    720: [
        (1, 7, '«A esses» provavelmente remete aos anjos do v. 6; não substituí o pronome por '
               'uma explicação.',
               '«Aqueles» remete aos anjos do v. 6; o pronome não foi substituído por uma '
               'explicação.'),
    ],
}

# Notas de redação acrescentadas como <p> próprio no fim da nota.
NOTAS_REDACAO: dict[int, dict[tuple[int, int], str]] = {
    630: {
        (3, 3):
            '<p><b>Nota de redação:</b> «prazeres de todo tipo» dava a <i>ποικίλαις</i> '
            '(poikílais) o sentido de «de todas as espécies»; o adjetivo é «variados, de muitas '
            'cores», e é assim que aparece em 2 Timóteo 3:6 e 1 Pedro 1:6. O «nós também» liga '
            'o passado do próprio grupo à mansidão pedida no v. 2.</p>',
    },
    720: {
        (1, 7):
            '<p><b>Nota de redação:</b> «de modo semelhante a esses» deu «tal como aqueles», e '
            '«elas ficam como exemplo» deu «estão postas como exemplo», que é o que '
            '<i>πρόκεινται</i> (prókeitai) diz: estão postas à vista de todos. O pronome '
            'continua a remeter aos anjos do v. 6.</p>',
    },
}

# Nota de redação acrescentada às notas dos versos cuja redação mudou por
# causa do artigo depois de «todo/toda» (regra corrigida em 2026-11-20).
NOTA_ARTIGO = (
    '<p><b>Nota de redação:</b> A redação anterior não trazia artigo («toda iniquidade», '
    '«toda boa obra», «toda mansidão»). Em português europeu o artigo depois de <i>todo</i> no '
    'singular é gramatical e não traduz o artigo grego: <i>πάσης</i>, <i>πᾶν</i> e '
    '<i>πᾶσαν</i> são anártricos e distribuem. Ver <i>docs/ESTILO_BEE.md</i>, πᾶς com e sem '
    'artigo.</p>'
)

ACRESCENTA_NOTA_ARTIGO = {630: [(2, 14), (3, 1), (3, 2)]}

# --------------------------------------------------------------------------
# Normalização mecânica das notas de João
# --------------------------------------------------------------------------

CABECALHO_FORTE = re.compile(
    r'<strong>(' + '|'.join(re.escape(s) for s in SECÇÕES) + r')</strong>\s*[—–-]\s*')
CABECALHO_TRAVESSAO = re.compile(
    r'<b>(' + '|'.join(re.escape(s) for s in SECÇÕES) + r')</b>\s*[—–]\s*')


def normalizar_nota(nota: str) -> str:
    """Põe a nota de João na forma da casa: cabeçalho, aspas, hífenes."""
    nota = CABECALHO_FORTE.sub(lambda m: f'<b>{m.group(1)}:</b> ', nota)
    nota = CABECALHO_TRAVESSAO.sub(lambda m: f'<b>{m.group(1)}:</b> ', nota)
    nota = nota.replace('\u2011', '-')
    nota = nota.replace('[[sem variante verificada]]', 'sem variante verificada')
    # &quot; e aspas curvas passam às aspas da casa, que são as de 600.
    estado = {'aberta': False}

    def aspas(_: re.Match[str]) -> str:
        estado['aberta'] = not estado['aberta']
        return '«' if estado['aberta'] else '»'

    nota = re.sub(r'&quot;|[“”]', aspas, nota)
    return nota


def normalizar_texto(texto: str) -> str:
    return texto.replace('\u2011', '-')


# --------------------------------------------------------------------------
# Migração das notas do piloto (Tito)
# --------------------------------------------------------------------------

SINTESE_ESBOCO = 'rascunho a migrar das notas do piloto aprovado.'


def migrar_sintese(nota: str, piloto: str) -> str:
    """Substitui a Síntese-esboço pela nota do piloto aprovado."""
    corpo = piloto.strip()
    if corpo.startswith('<p>'):
        corpo = corpo[3:]
    if corpo.endswith('</p>'):
        corpo = corpo[:-4]
    assert SINTESE_ESBOCO in nota, 'a Síntese já não é esboço'
    return nota.replace(SINTESE_ESBOCO, corpo.strip())


# --------------------------------------------------------------------------
# Aplicação
# --------------------------------------------------------------------------

def ler(numero: int) -> dict[str, Any]:
    caminho = next(DADOS.glob(f'{numero}_*.json'))
    with caminho.open(encoding='utf-8') as fh:
        return json.load(fh)


def caminho_de(numero: int) -> Path:
    return next(DADOS.glob(f'{numero}_*.json'))


def guardar(caminho: Path, dados: dict[str, Any]) -> None:
    temporario = caminho.with_suffix('.tmp')
    with temporario.open('w', encoding='utf-8') as fh:
        json.dump(dados, fh, ensure_ascii=False, indent=2)
        fh.write('\n')
    os.replace(temporario, caminho)


def verso(dados: dict[str, Any], cap: int, vv: int) -> dict[str, Any]:
    return dados['chapters'][str(cap)][vv - 1]


def aplicar(numero: int, dados: dict[str, Any], relatorio: list[str]) -> None:
    mudancas: list[tuple[int, int, int]] = []

    for cap, vv, velho, novo in TEXTOS.get(numero, []):
        alvo = verso(dados, cap, vv)
        if velho in alvo['text']:
            alvo['text'] = alvo['text'].replace(velho, novo, 1)
            mudancas.append((cap, vv, vv))
            relatorio.append(f'{numero} {cap}:{vv} texto: «{velho[:48]}…» → «{novo[:48]}…»')
        elif novo in alvo['text']:
            relatorio.append(f'{numero} {cap}:{vv} texto: já aplicado')
        else:
            raise SystemExit(f'{numero} {cap}:{vv}: trecho de texto não encontrado: {velho!r}')

    for (cap, vv), nota in NOTAS.get(numero, {}).items():
        alvo = verso(dados, cap, vv)
        if alvo['commentary'] == nota:
            relatorio.append(f'{numero} {cap}:{vv} nota: já aplicada')
            continue
        alvo['commentary'] = nota
        mudancas.append((cap, vv, vv))
        relatorio.append(f'{numero} {cap}:{vv} nota reescrita')

    for cap, vv, velho, novo in FRAGMENTOS.get(numero, []):
        if velho == novo:
            continue
        alvo = verso(dados, cap, vv)
        if velho in alvo['commentary']:
            alvo['commentary'] = alvo['commentary'].replace(velho, novo, 1)
            relatorio.append(f'{numero} {cap}:{vv} nota: fragmento corrigido')
        elif novo in alvo['commentary']:
            relatorio.append(f'{numero} {cap}:{vv} nota: fragmento já aplicado')
        else:
            raise SystemExit(f'{numero} {cap}:{vv}: fragmento de nota não encontrado')

    for cap, vv in ACRESCENTA_NOTA_ARTIGO.get(numero, []):
        alvo = verso(dados, cap, vv)
        if '<b>Nota de redação:</b>' not in alvo['commentary']:
            alvo['commentary'] += NOTA_ARTIGO
            relatorio.append(f'{numero} {cap}:{vv} nota: Nota de redação do artigo')
        else:
            relatorio.append(f'{numero} {cap}:{vv} nota: Nota de redação já presente')

    for (cap, vv), nota in NOTAS_REDACAO.get(numero, {}).items():
        alvo = verso(dados, cap, vv)
        if nota not in alvo['commentary']:
            alvo['commentary'] += nota
            relatorio.append(f'{numero} {cap}:{vv} nota: Nota de redação acrescentada')
        else:
            relatorio.append(f'{numero} {cap}:{vv} nota: Nota de redação já presente')

    if numero == 500:
        for cap, vs in dados['chapters'].items():
            for alvo in vs:
                antes = alvo['commentary']
                alvo['commentary'] = normalizar_nota(antes)
                alvo['text'] = normalizar_texto(alvo['text'])
                if alvo['commentary'] != antes:
                    relatorio.append(f'500 {cap}:{alvo["verse"]} nota normalizada')

    if numero == 630:
        piloto = json.loads(
            (PILOTO / '630_Tito.json').read_text(encoding='utf-8'))
        for cap, vs in dados['chapters'].items():
            for alvo in vs:
                nota = piloto['chapters'][cap][alvo['verse'] - 1]['commentary']
                if SINTESE_ESBOCO in alvo['commentary']:
                    alvo['commentary'] = migrar_sintese(alvo['commentary'], nota)
                    relatorio.append(f'630 {cap}:{alvo["verse"]} Síntese migrada do piloto')

    for cap, de, ate in mudancas:
        dados.setdefault('history', []).append({
            'chapter': cap,
            'verse_from': de,
            'verse_to': ate,
            'provider': 'local',
            'model': MODELO_EDITORIAL,
            'generated_at_utc': CARIMBO,
        })


def conferir(numero: int, dados: dict[str, Any]) -> list[str]:
    """Confere o estado final: nada antigo ficou, nada falta."""
    falhas: list[str] = []
    for cap, vv, velho, novo in TEXTOS.get(numero, []):
        texto = verso(dados, cap, vv)['text']
        # Há pares em que o trecho novo contém o antigo (acrescentar uma vírgula
        # no fim do verso): só a presença do novo prova que a edição foi feita.
        if novo not in texto:
            falhas.append(f'{numero} {cap}:{vv}: falta «{novo[:48]}»')
    for (cap, vv), nota in NOTAS.get(numero, {}).items():
        if verso(dados, cap, vv)['commentary'] != nota:
            falhas.append(f'{numero} {cap}:{vv}: nota reescrita não confere')
    if numero == 500:
        for cap, vs in dados['chapters'].items():
            for alvo in vs:
                n, t = alvo['commentary'], alvo['text']
                for proibido in ('<strong>', '&quot;', '\u2011', '“', '”'):
                    if proibido in n:
                        falhas.append(f'500 {cap}:{alvo["verse"]}: nota ainda tem «{proibido}»')
                # As aspas curvas são legítimas no texto quando a citação é
                # interior a outra («…» por fora, “…” por dentro).
                for proibido in ('\u2011', 'estar a batizar', 'unigênito', 'todo homem'):
                    if proibido in t:
                        falhas.append(f'500 {cap}:{alvo["verse"]}: texto ainda tem «{proibido}»')
                if n.count('«') != n.count('»'):
                    falhas.append(f'500 {cap}:{alvo["verse"]}: aspas desequilibradas na nota')
                if t.count('«') != t.count('»'):
                    falhas.append(f'500 {cap}:{alvo["verse"]}: aspas desequilibradas no texto')
                for sec in SECÇÕES[:3]:
                    if f'<b>{sec}:</b>' not in n:
                        falhas.append(f'500 {cap}:{alvo["verse"]}: falta a secção {sec}')
    for (cap, vv), nota in NOTAS_REDACAO.get(numero, {}).items():
        if nota not in verso(dados, cap, vv)['commentary']:
            falhas.append(f'{numero} {cap}:{vv}: falta a Nota de redação')

    if numero == 630:
        for cap, vs in dados['chapters'].items():
            for alvo in vs:
                if SINTESE_ESBOCO in alvo['commentary']:
                    falhas.append(f'630 {cap}:{alvo["verse"]}: Síntese ainda é esboço')
    return falhas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verificar', action='store_true',
                    help='confere o estado sem escrever')
    args = ap.parse_args()

    relatorio: list[str] = []
    falhas: list[str] = []
    for numero in (500, 630, 720):
        caminho = caminho_de(numero)
        dados = json.loads(caminho.read_text(encoding='utf-8'))
        antes = json.dumps(dados, ensure_ascii=False)
        if args.verificar:
            falhas += conferir(numero, dados)
            continue
        aplicar(numero, dados, relatorio)
        falhas += conferir(numero, dados)
        if json.dumps(dados, ensure_ascii=False) != antes:
            guardar(caminho, dados)

    for linha in relatorio:
        print(' ', linha)
    if falhas:
        print('\nFALHAS:')
        for f in falhas:
            print(' -', f)
        return 1
    if args.verificar:
        print(f'\nOK: os três livros conferem com a lapidação de {CARIMBO[:10]}.')
    else:
        print(f'\nOK: {len(relatorio)} alterações aplicadas e conferidas.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
