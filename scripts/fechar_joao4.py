#!/usr/bin/env python3
"""Fecha João 4:29–54 — 26 versículos que estavam como marcadores de quarentena.

Escreve, para cada versículo, a tradução BEE (a partir do SBLGNT d7f35ad, com
os textos de `docs/colacao/João.json`), a Análise Léxica e a Síntese Exegética.
A Crítica Textual não é escrita à mão: é gerada por `scripts/regenerar_critica.py`
a partir do aparato e da colação, e depois conferida por
`scripts/verificar_notas_colacao.py`.

Também corrige 4:27 («estivesse falando» → «estivesse a falar»), porque a forma
com gerúndio não está entre as variantes aceites (decisão de 22/11/2026).

Uso (com `--aplicar` escreve; sem ele, só confere que os versículos existem):
    python3 scripts/fechar_joao4.py --aplicar
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DADOS = RAIZ / 'edicoes' / 'nova' / 'livros_json' / '500_Joao.json'

# verso: (texto BEE, Análise Léxica, Síntese Exegética)
VERSOS: dict[int, tuple[str, str, str]] = {
    29: (
        'Venham ver um homem que me disse tudo o que fiz. Não será este o Cristo?',
        '<i>Δεῦτε</i> (deûte) «venham»; <i>ἴδετε</i> (ídete) «vejam»; <i>ὅσα ἐποίησα</i> «tudo o que fiz»; '
        '<i>μήτι</i> (mḗti) introduz uma pergunta que espera «não» como resposta, mas a mulher deixa-a aberta, '
        'e a tradução conserva essa hesitação.',
        'A primeira pregação da mulher é um convite e uma pergunta, não uma confissão. Ela ainda não sabe, '
        'mas já não consegue calar-se.',
    ),
    30: (
        'Saíram da cidade e vinham ter com ele.',
        '<i>ἐξῆλθον</i> (exêlthon) «saíram», aoristo, ação concluída; <i>ἤρχοντο</i> (êrchonto) «vinham», '
        'imperfeito, movimento em curso.',
        'A saída segue de imediato a voz da mulher. A fé ainda não é certeza, mas já é deslocação.',
    ),
    31: (
        'Entretanto, os discípulos insistiam com ele, dizendo: «Rabi, come.»',
        '<i>ἠρώτων</i> (ērṓtōn) «insistiam», imperfeito de repetição; <i>Ῥαββί</i> (Rhabbí) «Rabi»; '
        '<i>φάγε</i> (phage) «come», imperativo aoristo.',
        'Os discípulos leem Jesus a partir da fome. O diálogo que segue corrige a pergunta: o alimento que ele tem '
        'não está nas compras que foram fazer à aldeia (v. 8).',
    ),
    32: (
        'Mas ele disse-lhes: «Eu tenho uma comida para comer que vocês não conhecem.»',
        '<i>βρῶσιν</i> (brṓsin) «alimento, comida»; <i>φαγεῖν</i> (phagein) «para comer», infinitivo que completa o '
        'substantivo; <i>οὐκ οἴδατε</i> «não conhecem».',
        'Jesus desloca a ideia de alimento do pão para a obra de Deus. Os discípulos ainda estão no nível do pão.',
    ),
    33: (
        'Então os discípulos diziam uns aos outros: «Será que alguém lhe trouxe de comer?»',
        '<i>ἔλεγον οὖν</i> «diziam, pois»; <i>πρὸς ἀλλήλους</i> «uns aos outros»; <i>Μή τις</i> (mḗ tis) '
        'pergunta que espera «não», traduzida por «será que alguém…?»; <i>ἤνεγκεν</i> (ênenken) «trouxe».',
        'A pergunta é dita entre eles, não a Jesus. Não entendem, e não se atrevem a perguntar (cf. v. 27).',
    ),
    34: (
        'Jesus disse-lhes: «A minha comida é fazer a vontade daquele que me enviou e acabar a sua obra.»',
        '<i>Ἐμὸν βρῶμά ἐστιν</i> «a minha comida é»; <i>ἵνα ποιήσω</i> «que eu faça», subjuntivo de conteúdo; '
        '<i>πέμψαντός</i> (pémpsantos) «daquele que enviou», particípio aoristo; <i>τελειώσω</i> (teleiṓsō) '
        '«acabe, leve a termo».',
        'O sustento de Jesus é a obediência ao Pai. A obra de Deus não é um peso que ele aguenta: é o que o alimenta.',
    ),
    35: (
        '«Não dizem vocês: “Ainda faltam quatro meses, e chega a ceifa”? Eu digo-lhes: levantem os olhos e vejam '
        'os campos, que estão brancos para a ceifa.»',
        '<i>τετράμηνός</i> (tetrámēnos) «de quatro meses», intervalo entre a sementeira e a ceifa; '
        '<i>θερισμός</i> (therismós) «ceifa»; <i>λευκαί</i> (leukaí) «brancas», isto é, maduras; '
        '<i>θεάσασθε</i> (theásasthe) «vejam». O advérbio <i>ἤδη</i> «já» fecha o v. 35 na base, mas governa a frase '
        'do v. 36; a tradução põe-no no início do v. 36.',
        'A conta de quatro meses mede a paciência humana. Jesus diz que a colheita já está madura: o tempo de esperar '
        'acabou.',
    ),
    36: (
        '«Já o que ceifa recebe o salário e ajunta fruto para a vida eterna, para que o que semeia se alegre '
        'juntamente com o que ceifa.»',
        '<i>μισθὸν</i> (misthón) «salário»; <i>καρπὸν</i> (karpón) «fruto»; <i>ζωὴν αἰώνιον</i> «vida eterna»; '
        '<i>σπείρων</i> (speírōn) «o que semeia»; <i>ὁμοῦ</i> (homoú) «juntamente»; <i>χαίρῃ</i> (chaírē) «se alegre», '
        'subjuntivo de finalidade.',
        'Semeador e ceifeiro alegram-se juntos. Na obra de Deus, quem colhe não tem mérito maior do que quem semeou.',
    ),
    37: (
        '«Pois nisto se verifica o provérbio verdadeiro: “Um é o que semeia, e outro o que ceifa.”»',
        '<i>ἐν τούτῳ</i> «nisto»; <i>ἀληθινὸς</i> (alēthinòs) «verdadeiro», o mesmo adjetivo de 1:9; '
        '<i>ἄλλος … ἄλλος</i> «um … outro».',
        'O provérbio contrasta quem semeia com quem colhe. O v. 38 mostra que a missão dos discípulos liga-se a uma '
        'sementeira feita antes deles.',
    ),
    38: (
        '«Eu enviei vocês a ceifar aquilo em que não trabalharam; outros trabalharam, e vocês entraram no trabalho deles.»',
        '<i>ἀπέστειλα</i> (apésteila) «enviei»; <i>θερίζειν</i> (therízein) «ceifar»; <i>κεκοπιάκατε</i> '
        '(kekopiákate) «trabalharam com fadiga», perfeito; <i>εἰσεληλύθατε</i> (eiselēlýthate) «entraram», perfeito.',
        'Os discípulos colhem o que outros trabalharam. O texto não diz quem são esses «outros»; a tradição '
        'interpreta-o de várias maneiras, e a tradução não decide.',
    ),
    39: (
        'Muitos samaritanos daquela cidade creram nele por causa do testemunho da mulher: «Disse-me tudo o que fiz.»',
        '<i>ἐπίστευσαν εἰς αὐτόν</i> «creram nele»; <i>μαρτυρούσης</i> (martyroúsēs) «que testemunhava», particípio; '
        '<i>Εἶπέν μοι πάντα ἃ ἐποίησα</i> «disse-me tudo o que fiz», citação do testemunho.',
        'Antes de ver Jesus, a fé dos samaritanos começa no testemunho de uma mulher, e não de uma autoridade.',
    ),
    40: (
        'Quando os samaritanos chegaram junto dele, pediram-lhe que ficasse com eles; e ele ficou ali dois dias.',
        '<i>ἠρώτων αὐτὸν μεῖναι</i> «pediam-lhe que ficasse», com infinitivo; <i>ἔμεινεν</i> (émeinen) «ficou»; '
        '<i>δύο ἡμέρας</i> «dois dias».',
        'Os samaritanos, que em 4:9 não tinham relações com os judeus, são os que pedem a Jesus que fique.',
    ),
    41: (
        'E muitos mais creram por causa da palavra dele.',
        '<i>πολλῷ πλείους</i> (pollō pleíous) «muito mais»; <i>διὰ τὸν λόγον αὐτοῦ</i> «por causa da palavra dele».',
        'A fé passa do testemunho da mulher para a palavra de Jesus. O v. 42 descreve essa passagem.',
    ),
    42: (
        'E diziam à mulher: «Já não é pela tua fala que cremos; nós mesmos ouvimos, e sabemos que este é '
        'verdadeiramente o Salvador do mundo.»',
        '<i>Οὐκέτι</i> «já não»; <i>λαλιάν</i> (lalián) «fala»; <i>ἀκηκόαμεν</i> (akēkóamen) «ouvimos», perfeito; '
        '<i>ἀληθῶς</i> (alēthṓs) «verdadeiramente»; <i>σωτὴρ τοῦ κόσμου</i> «salvador do mundo».',
        'Confissão decisiva: o título «Salvador do mundo» aplica a Jesus uma esperança que ultrapassa Israel '
        'e a Samaria. É a única vez que o Evangelho de João usa este título.',
    ),
    43: (
        'Passados aqueles dois dias, saiu dali para a Galileia.',
        '<i>Μετὰ δὲ τὰς δύο ἡμέρας</i> «passados os dois dias»; <i>ἐξῆλθεν ἐκεῖθεν</i> «saiu dali».',
        'A saída para a Galileia é explicada pelo versículo seguinte.',
    ),
    44: (
        'Porque o próprio Jesus tinha declarado que um profeta não tem honra na sua própria pátria.',
        '<i>αὐτὸς γὰρ Ἰησοῦς</i> «pois o próprio Jesus»; <i>ἐμαρτύρησεν</i> (emartýrēsen) «declarou, testemunhou»; '
        '<i>ἰδίᾳ πατρίδι</i> «na sua própria pátria»; <i>τιμὴν</i> (timḗn) «honra».',
        'A frase é ambígua: «pátria» pode ser a Galileia, onde Jesus cresceu segundo os sinóticos, ou a Judeia. '
        'O contexto favorece a Judeia: o «pois» explica a saída para a Galileia, e o v. 45 apresenta a receção dos '
        'galileus. A tradução mantém «pátria» sem decidir.',
    ),
    45: (
        'Quando, pois, chegou à Galileia, os galileus receberam-no, porque tinham visto tudo o que ele fizera em '
        'Jerusalém durante a festa; pois também eles tinham ido à festa.',
        '<i>ὅτε οὖν</i> «quando, pois»; <i>πάντα ἑωρακότες</i> «tendo visto tudo», perfeito de <i>ὁράω</i>; '
        '<i>ἑορτῇ</i> (heortḗ) «festa», a de Jerusalém.',
        'Os galileus recebem Jesus pelo que viram, não por uma fé provada. João regista essa receção com reserva '
        '(cf. 2:23–25).',
    ),
    46: (
        'Foi, pois, de novo a Caná da Galileia, onde tinha transformado a água em vinho. E havia um funcionário do '
        'rei cujo filho estava doente em Cafarnaum.',
        '<i>βασιλικός</i> (basilikós) «funcionário do rei», adjetivo substantivado; <i>οὗ ὁ υἱὸς ἠσθένει</i> «cujo '
        'filho estava doente»; <i>Καφαρναούμ</i> «Cafarnaum».',
        'Caná volta a ser o ponto de partida: a cena seguinte começa onde começou o primeiro sinal (2:11). O texto '
        'diz só que o oficial é do rei; não permite identificá-lo com mais precisão.',
    ),
    47: (
        'Este, ao ouvir que Jesus tinha chegado da Judeia à Galileia, foi ter com ele e pediu-lhe que descesse e '
        'curasse o filho dele, porque estava para morrer.',
        '<i>ἥκει</i> (hḗkei) «tinha chegado», perfeito com valor de presente; <i>καταβῇ</i> (katabê) «que desça»; '
        '<i>ἰάσηται</i> (iásētai) «curasse»; <i>ἤμελλεν ἀποθνῄσκειν</i> «estava para morrer».',
        'O homem vai até Jesus, a cerca de vinte e cinco quilómetros, e pede que ele desça. Para ele, a cura exige '
        'a presença física.',
    ),
    48: (
        'Jesus disse-lhe: «Se vocês não virem sinais e prodígios, de modo nenhum crerão.»',
        '<i>σημεῖα καὶ τέρατα</i> «sinais e prodígios»; <i>ἴδητε</i> (ídēte) «virem», aoristo subjuntivo, segunda '
        'pessoa do plural; <i>οὐ μὴ πιστεύσητε</i> «de modo nenhum crerão», dupla negação enfática.',
        'O verbo está no plural, embora a fala seja dirigida a um homem: Jesus fala à multidão de quem o oficial é '
        'representante, e a tradução mantém o plural. A resposta repreende a fé que depende de sinais, sem recusar o '
        'pedido.',
    ),
    49: (
        'Disse-lhe o funcionário: «Senhor, desce antes que morra o meu menino.»',
        '<i>Κύριε</i> «Senhor»; <i>κατάβηθι</i> (katábēthi) «desce», imperativo aoristo; <i>πρὶν ἀποθανεῖν</i> «antes '
        'de morrer»; <i>παιδίον</i> (paidíon) «menino», diminutivo que a tradução mantém.',
        'O funcionário insiste sem recuar. Ainda pede a presença física, mas já chama Jesus «Senhor».',
    ),
    50: (
        'Jesus disse-lhe: «Vai; o teu filho vive.» O homem acreditou na palavra que Jesus lhe tinha dito, e ia.',
        '<i>Πορεύου</i> (poreúou) «vai»; <i>ζῇ</i> (zē̂) «vive»; <i>ἐπίστευσεν</i> (epísteusen) «acreditou», aoristo: '
        'a decisão de fé é pontual; <i>ἐπορεύετο</i> (eporeúeto) «ia», imperfeito.',
        'A cura acontece à distância, pela palavra de Jesus. O homem parte sem prova e acredita.',
    ),
    51: (
        'Quando ele já descia, os servos saíram ao seu encontro e disseram-lhe que o seu menino vive.',
        '<i>ἤδη δὲ … καταβαίνοντος</i> «quando ele já descia», genitivo absoluto; <i>ὑπήντησαν</i> (hypḗntēsan) '
        '«saíram ao encontro»; <i>ζῇ</i> «vive».',
        'Os servos trazem a confirmação antes de o pai chegar. A fé veio antes da prova, e a notícia confirma a palavra.',
    ),
    52: (
        'Perguntou-lhes, então, a que hora tinha começado a melhorar. Disseram-lhe: «Ontem, à sétima hora, a febre '
        'o deixou.»',
        '<i>ἐπύθετο</i> «perguntou»; <i>κομψότερον ἔσχεν</i> «tinha-se sentido melhor»; <i>ὥραν ἑβδόμην</i> '
        '«a sétima hora», contada como em 4:6, em que a sexta é meio-dia; <i>πυρετός</i> (pyretós) «febre».',
        'A cura é verificada pela hora. A coincidência é o argumento do v. 53, e o texto deixa a prova no tempo.',
    ),
    53: (
        'O pai reconheceu que era àquela mesma hora em que Jesus lhe dissera: «O teu filho vive.» E creu ele, e toda '
        'a sua casa.',
        '<i>ἔγνω</i> (égnō) «reconheceu»; <i>ἐκείνῃ τῇ ὥρᾳ</i> «naquela mesma hora»; <i>οἰκία</i> (oikía) «casa», '
        'o agregado familiar; <i>ὅλη</i> «toda».',
        'A fé do oficial torna-se a fé da casa: uma família inteira crê. O sinal ganha um alcance que ultrapassa o '
        'indivíduo.',
    ),
    54: (
        'Este foi, de novo, o segundo sinal que Jesus fez, ao vir da Judeia para a Galileia.',
        '<i>δεύτερον σημεῖον</i> «segundo sinal», em contraste com o primeiro de 2:11; <i>ἐλθὼν</i> (elthṓn) «ao vir»; '
        '<i>πάλιν</i> «de novo».',
        'João fecha este bloco com a contagem dos sinais. A numeração é teológica, não apenas cronológica.',
    ),
}

CT_VAZIA = '<p><b>Crítica Textual:</b> </p>'


def _comentario(analise: str, sintese: str) -> str:
    return (f'<p><b>Análise Léxica:</b> {analise}</p>{CT_VAZIA}'
            f'<p><b>Síntese Exegética:</b> {sintese}</p>')


def aplicar(dados: dict) -> int:
    capitulo = dados['chapters']['4']
    alterados = 0
    for verso in capitulo:
        n = verso['verse']
        if 29 <= n <= 54:
            texto, analise, sintese = VERSOS[n]
            verso['text'] = texto
            verso['commentary'] = _comentario(analise, sintese)
            alterados += 1
    for verso in capitulo:
        if verso['verse'] == 27:
            verso['text'] = verso['text'].replace('estivesse falando', 'estivesse a falar')
    return alterados


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--aplicar', action='store_true')
    args = ap.parse_args(argv)
    dados = json.loads(DADOS.read_text(encoding='utf-8'))
    faltam = sorted(set(range(29, 55)) - set(VERSOS))
    if faltam:
        raise SystemExit(f'faltam versículos: {faltam}')
    alterados = aplicar(dados)
    print(f'versículos de 4:29–54 escritos: {alterados}')
    if args.aplicar:
        DADOS.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('escrito:', DADOS)
    else:
        print('(simulação: use --aplicar para escrever)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
