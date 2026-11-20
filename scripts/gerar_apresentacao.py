#!/usr/bin/env python3
"""Gera docs/APRESENTACAO_BEE.docx — o documento de apresentação da BEE.

Todo o conteúdo factual (autor, datas, números de progresso, testemunhas)
vem dos documentos do próprio repositório (README.md, docs/ESTADO.md,
docs/CRITICA_TEXTUAL.md, docs/SBLGNT.md) e dos JSON da edição nova,
conferidos no dia da geração. Ao atualizar números, conferir com
``python3 scripts/verificar_dados.py`` e com os relatórios de colação.

Uso:  PYTHONPATH=<python-docx> python3 scripts/gerar_apresentacao.py
"""
from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / 'docs' / 'APRESENTACAO_BEE.docx'

AZUL = RGBColor(0x1F, 0x3B, 0x63)
CINZ = RGBColor(0x55, 0x55, 0x55)


def titulo(doc, texto, nivel=1):
    h = doc.add_heading(texto, level=nivel)
    for r in h.runs:
        r.font.color.rgb = AZUL
    return h


def p(doc, texto, **kw):
    par = doc.add_paragraph(texto)
    for chave, valor in kw.items():
        setattr(par, chave, valor)
    return par


def tabela(doc, cabecalho, linhas, larguras=None):
    t = doc.add_table(rows=1, cols=len(cabecalho))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(cabecalho):
        cel = t.rows[0].cells[i]
        cel.text = ''
        run = cel.paragraphs[0].add_run(texto)
        run.bold = True
    for linha in linhas:
        celulas = t.add_row().cells
        for i, texto in enumerate(linha):
            celulas[i].text = texto
    doc.add_paragraph()
    return t


def construir() -> Document:
    doc = Document()
    for secao in doc.sections:
        secao.top_margin = Cm(2.2)
        secao.bottom_margin = Cm(2.2)
        secao.left_margin = Cm(2.4)
        secao.right_margin = Cm(2.4)
    estilo = doc.styles['Normal']
    estilo.font.name = 'Calibri'
    estilo.font.size = Pt(11)

    # ---------- Capa ----------
    for _ in range(5):
        doc.add_paragraph()
    capa = doc.add_paragraph()
    capa.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = capa.add_run('BÍBLIA DE ESTUDO EPIGNÓSIS')
    r.bold = True
    r.font.size = Pt(30)
    r.font.color.rgb = AZUL
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = sub.add_run('BEE — Documento de Apresentação do Projeto')
    r.font.size = Pt(15)
    r.font.color.rgb = CINZ
    doc.add_paragraph()
    info = doc.add_paragraph()
    info.alignment = WD_ALIGN_PARAGRAPH.CENTER
    info.add_run(
        'Autor e responsável editorial: Martinho S. S. Madureira\n'
        'Publicado por: Martinho S. S. Madureira Ministries\n'
        'Documento gerado em 20 de novembro de 2026\n'
        'Estado da obra: RASCUNHO em produção (geração assistida por IA '
        'sob direção editorial, com revisão humana pendente)').font.size = Pt(11)
    doc.add_page_break()

    # ---------- Índice ----------
    titulo(doc, 'Índice', 1)
    for item in [
        '1. O que é a Bíblia de Estudo Epignósis',
        '2. O autor e a origem do projeto',
        '3. Porquê uma nova tradução',
        '4. Os textos de partida: as fontes nas línguas originais',
        '5. Os manuscritos: o que são e como se leem as suas siglas',
        '6. As variantes textuais e como a BEE decide entre elas',
        '7. O método de tradução',
        '8. As notas de estudo',
        '9. Como a obra é produzida (a oficina)',
        '10. Progresso atual',
        '11. O que falta e os próximos passos',
        '12. Perguntas frequentes',
        'Anexo A — Testemunhas e edições citadas nas notas',
        'Anexo B — Glossário mínimo',
    ]:
        doc.add_paragraph(item)
    doc.add_page_break()

    # ---------- 1 ----------
    titulo(doc, '1. O que é a Bíblia de Estudo Epignósis', 1)
    p(doc, 'A Bíblia de Estudo Epignósis (BEE) é um projeto de tradução '
           'completa da Bíblia — os 66 livros e 1.189 capítulos do cânone, '
           '31.102 versículos — para português europeu contemporâneo, '
           'acompanhada de notas de estudo versículo a versículo. '
           'O nome vem do grego ἐπίγνωσις (epígnōsis), «pleno '
           'conhecimento»: a palavra que o apóstolo Paulo usa quando fala '
           'de conhecer a verdade de forma plena e pessoal (por exemplo, '
           '1 Timóteo 2:4). O projeto adotou-a como nome e como regra de '
           'tradução: no texto da BEE, ἐπίγνωσις é traduzido por «pleno '
           'conhecimento».')
    p(doc, 'A obra destina-se a leitores que querem ler a Escritura numa '
           'linguagem portuguesa atual e, ao mesmo tempo, ver — sem '
           'precisar de grego nem de formação teológica — por que razão o '
           'texto diz o que diz: o que está no original, onde as cópias '
           'antigas divergem, e com que grau de certeza o sabemos.')
    p(doc, 'Formato final previsto: módulos para a aplicação MyBible '
           '(BEE.SQLite3, o texto; BEE.commentaries.SQLite3, as notas), '
           'gerados automaticamente a partir dos ficheiros de dados do '
           'projeto. Até à revisão humana final, todos os módulos se '
           'identificam honestamente como RASCUNHO.')

    # ---------- 2 ----------
    titulo(doc, '2. O autor e a origem do projeto', 1)
    p(doc, 'Autor e responsável editorial: Martinho S. S. Madureira, '
           'através de Martinho S. S. Madureira Ministries. É o '
           'responsável quem fixa as decisões editoriais — texto-base, '
           'método, voz da tradução, aprovação de amostras — e quem lê e '
           'aprova (ou manda refazer) o que a oficina produz.')
    p(doc, 'Início do projeto: novembro de 2026. Os documentos de '
           'organização e de estado datam de 17 de novembro de 2026; a '
           'produção de texto arrancou nos dias seguintes, primeiro em '
           'livros-piloto curtos (Filemom, Tito, 2 e 3 João, Judas), '
           'depois em 2 Tessalonicenses e no Evangelho de João. O '
           'repositório do projeto é público no GitHub '
           '(martinhossmadureiraministries/traducao-epignosis): código, '
           'documentos de método, relatórios de evidência e dados '
           'versionados — a oficina inteira pode ser inspecionada.')
    p(doc, 'O projeto usa modelos de inteligência artificial como '
           'ferramenta de produção, sob direção editorial humana e com '
           'verificações automáticas independentes (ver a secção 9). '
           'Nenhum texto é publicado como final sem revisão humana '
           'especializada: neste momento, tudo o que existe é rascunho '
           'identificado como tal.')

    # ---------- 3 ----------
    titulo(doc, '3. Porquê uma nova tradução', 1)
    for texto in [
        'Português europeu atual, sem arcaísmos de púlpito. As versões '
        'portuguesas mais lidas herdaram formas como «vós adorareis», '
        '«conheceis», «eis que» a cada frase. A BEE trata o plural sempre '
        'por «vocês», reserva «tu» à oração direta a Deus e escreve na '
        'ortografia europeia de hoje («connosco», «de facto», «registo», '
        '«secção»).',
        'Transparência textual. As Bíblias de estudo costumam esconder '
        'que o texto grego tem variantes — ou mencionam-nas sem dizer com '
        'que apoio. A BEE mostra a variante, diz quem a lê (edições e, '
        'quando foram colacionados, manuscritos) e classifica a certeza '
        'da decisão (A, B ou C). A incerteza regista-se; não se esconde.',
        'Notas com evidência verificável. Cada afirmação de crítica '
        'textual das notas pode ser conferida num relatório de colação '
        'guardado no repositório (docs/colacao/), produzido por programa '
        'a partir das transcrições dos manuscritos. Apoio que não está '
        'na evidência não pode ser citado — e há verificações '
        'automáticas que o impedem.',
        'Fidelidade sem comentário embutido. O versículo traduz o '
        'original; a interpretação vai para a nota. Ambiguidade do '
        'original que a exegese deve discutir é preservada no texto, não '
        'resolvida à socapa dentro da tradução.',
    ]:
        doc.add_paragraph(texto, style='List Bullet')

    # ---------- 4 ----------
    titulo(doc, '4. Os textos de partida: as fontes nas línguas originais', 1)
    p(doc, 'A BEE não traduz de outra tradução. Traduz dos textos nas '
           'línguas originais, fixados e versionados para que qualquer '
           'decisão possa ser auditada:')
    tabela(doc, ['Testamento', 'Texto-base fixado', 'Papel'], [
        ['Novo Testamento',
         'SBL Greek New Testament (SBLGNT), edição de Michael W. Holmes '
         '(Society of Biblical Literature / Logos, 2010), revisão digital '
         'd7f35ad, licença CC BY 4.0',
         'É o texto grego traduzido. O seu aparato compara edições '
         'impressas (WH, Tregelles, NA28, Robinson–Pierpont), não '
         'manuscritos.'],
        ['Novo Testamento (comparação)',
         'Textus Receptus de Scrivener (1894), revisão 6049a43; edições '
         'WH, Tregelles, NA28 e Robinson–Pierpont (RP) via aparato',
         'Mostram onde a tradição impressa diverge da base; a nota diz '
         'sempre qual das edições lê o quê.'],
        ['Antigo Testamento',
         'Westminster Leningrad Codex / OSHB (texto massorético '
         'hebraico), com comparação pelas versões antigas quando o '
         'método o exigir',
         'Base definida na memória de estilo; a produção atual concentra-se '
         'no Novo Testamento.'],
        ['Manuscritos (evidência)',
         'Transcrições eletrónicas CNTR (Center for New Testament '
         'Restoration, Alan Bunning), revisão 4e743a4, CC BY-SA 4.0',
         'Transcrições diplomáticas dos códices e papiros; delas se geram '
         'os relatórios de colação por livro.'],
    ])
    p(doc, 'Fixar a revisão exata («d7f35ad», «6049a43») não é preciosismo: '
           'significa que duas pessoas, em anos diferentes, abrem exatamente '
           'o mesmo texto e podem conferir qualquer decisão da BEE contra '
           'ele.')

    # ---------- 5 ----------
    titulo(doc, '5. Os manuscritos: o que são e como se leem as suas siglas', 1)
    p(doc, 'Nenhum original («autógrafo») de qualquer livro da Bíblia '
           'sobreviveu. O que temos são cópias de cópias, feitas à mão ao '
           'longo de quinze séculos. Os estudiosos catalogam-nas pelo '
           'sistema Gregory–Aland (GA), que é o que as notas da BEE usam:')
    tabela(doc, ['Categoria', 'Sigla', 'O que é'], [
        ['Papiros', 'P + número (P45, P66, P75…)',
         'Os testemunhos mais antigos (séculos II–VII), escritos em '
         'papiro; chegam quase sempre fragmentários.'],
        ['Unciais (maiúsculos)', '01, 02, 03… (também א, A, B…)',
         'Códices em pergaminho, em letras maiúsculas (séculos IV–X). '
         '01 = Códice Sinaítico; 02 = Alexandrino; 03 = Vaticano.'],
        ['Minúsculos', 'número sem zero inicial (33, 565, 1739…)',
         'Códices em letra cursiva (séculos IX–XVI); são a grande maioria '
         'dos cerca de 5.800 manuscritos gregos catalogados.'],
        ['Lecionários', 'ℓ + número',
         'Livros de leituras litúrgicas; úteis, mas adaptados ao culto.'],
        ['Versões antigas', 'lat, sir, cop, got…',
         'Traduções antigas (latim, siríaco, copta, gótico…) que '
         'testemunham o grego que os seus tradutores tinham diante de si.'],
        ['Pais da Igreja', 'nome do autor',
         'Citações bíblicas em escritores dos primeiros séculos.'],
    ])
    p(doc, 'Como a BEE usa os manuscritos. Antes de um livro entrar em '
           'produção, o programa de colação (scripts/colar.py) compara, '
           'versículo a versículo, o texto-base com as transcrições CNTR '
           'disponíveis e grava um relatório (docs/colacao/<Livro>.json). '
           'Só as testemunhas que esse relatório mostra podem ser citadas '
           'na nota — e a oficina verifica-o automaticamente. Exemplos '
           'reais de testemunhas colacionadas:')
    tabela(doc, ['Livro', 'Testemunhas manuscritas colacionadas'], [
        ['2 Tessalonicenses (47 vv.)',
         'P92 e P30 (papiros, fragmentários), 01 (Sinaítico), 02 '
         '(Alexandrino), 03 (Vaticano) — além das edições impressas WH, '
         'RP, Stephanus, KJTR e SR.'],
        ['João 1–4 (166 vv.)',
         'P45, P5, P66, P75, P106, P119, P120, P134 e os unciais 01, 02, '
         '03, 04, 05, 0162, 029, 032 — além das edições.'],
        ['Tito, Filemom, 2 e 3 João, Judas',
         'Relatórios próprios em docs/colacao/, gerados pelo mesmo '
         'programa antes da revisão das notas.'],
    ])
    p(doc, 'Dois cuidados que a BEE observa sempre: (1) uma leitura '
           'sustentada só por texto suprido pelo editor numa lacuna '
           '(parte rasgada do manuscrito) vale menos do que uma leitura '
           'legível; (2) uma correção de mão posterior dentro do mesmo '
           'códice conta como testemunha de outra época, não como a '
           'mesma voz. O estado físico de cada testemunha (lacunas, '
           'correções, abreviaturas dos nomes sagrados) faz parte do '
           'relatório.')

    # ---------- 6 ----------
    titulo(doc, '6. As variantes textuais e como a BEE decide entre elas', 1)
    titulo(doc, '6.1 O que é uma variante', 2)
    p(doc, 'Onde as cópias divergem — uma palavra trocada, uma frase a '
           'mais ou a menos, outra ordem — há uma «unidade de variação». '
           'A esmagadora maioria é inofensiva: erros de ortografia dos '
           'escribas (itacismos), trocas de ordem sem mudança de sentido. '
           'Em 2 Tessalonicenses, por exemplo, sobre 47 versículos '
           'colacionados, nenhuma unidade de variação altera um artigo '
           'de fé, um mandamento ou uma promessa. Mas algumas variantes '
           'mudam o sentido, e essas a nota tem de mostrar.')
    titulo(doc, '6.2 Por que não basta «o mais antigo» nem «a maioria»', 2)
    p(doc, 'Antiguidade e número são indícios, não árbitros. Caso real '
           '(2 Tessalonicenses 2:13): os três unciais mais antigos '
           'dividem-se — 03 e 02 leem ἀπαρχήν («como primícias»), 01 e '
           'toda a tradição bizantina leem ἀπʼ ἀρχῆς («desde o '
           'princípio»). A antiguidade empata; a maioria contaria '
           'milhares de cópias tardias que descendem umas das outras — '
           'contar o mesmo voto milhares de vezes. Decide o argumento: '
           '«como primícias» é a leitura mais difícil e mais '
           'caracteristicamente paulina; um escriba tende a trocar o '
           'difícil pelo fácil, não o contrário. NA28 e o SBLGNT '
           'imprimem ἀπαρχήν — e é essa a leitura que a BEE traduz.')
    titulo(doc, '6.3 O método: ecletismo fundamentado, em sete passos', 2)
    for texto in [
        'Fixar e ler — base, aparato, Scrivener e testemunhas colacionadas; '
        'ler o parágrafo, não só a palavra.',
        'Classificar a diferença — ortográfica, de ordem, de adição/omissão '
        'ou de substituição. Só as duas últimas exigem decisão e nota.',
        'Evidência externa — quem lê o quê, há quanto tempo, em que famílias '
        'textuais e regiões, e em que estado físico.',
        'Evidência transcricional — que leitura explica a origem das outras? '
        '(A direção habitual do erro de escriba é esclarecer, completar e '
        'harmonizar.)',
        'Evidência intrínseca — o vocabulário, a sintaxe e o argumento do '
        'autor noutros lugares.',
        'Decidir e traduzir — regra geral, traduz-se a base fixada; a nota '
        'diz que a decisão é da base, sem a BEE se apropriar dela.',
        'Registar — leituras, apoio, decisão, razão e nível de certeza '
        'ficam na nota e nos dados de auditoria do livro.',
    ]:
        doc.add_paragraph(texto, style='List Number')
    titulo(doc, '6.4 Níveis de certeza', 2)
    tabela(doc, ['Nível', 'Significado'], [
        ['A', 'Decisão segura: sem variante registada, ou a alternativa é '
              'apenas bizantina/tardia e as edições críticas apoiam a base.'],
        ['B', 'Decisão provável: as edições críticas dividem-se, ou resta '
              'uma alternativa plausível.'],
        ['C', 'Texto difícil: decisão provisória, assinalada para revisão '
              'especializada (por exemplo, João 1:34 e Judas 1:22–23).'],
    ])
    titulo(doc, '6.5 A posição doutrinária e o método', 2)
    p(doc, 'O projeto confessa a inerrância, a infalibilidade e a '
           'imutabilidade das Escrituras — e distingue duas afirmações: '
           '«a Escritura é inerrante» diz respeito ao texto que Deus deu '
           '(o autógrafo); «esta cópia lê X, aquela lê Y» diz respeito às '
           'cópias que chegaram até nós, e decide-se pela evidência. A '
           'crítica textual não corrige a doutrina: procura o texto. Por '
           'isso nenhuma variante é adotada ou rejeitada por favorecer '
           'uma teologia; se a evidência aponta para uma leitura '
           'incómoda, adota-se a leitura e discute-se a teologia na nota. '
           'Foi também por decisão consciente que a BEE não adotou a '
           'posição «majoritária» (prioridade sistemática ao texto '
           'bizantino): fixou o SBLGNT como base, e a escolha está '
           'registada e fundamentada no protocolo (docs/CRITICA_TEXTUAL.md).')

    # ---------- 7 ----------
    titulo(doc, '7. O método de tradução', 1)
    for texto in [
        'Fechar a unidade antes dos versículos: quem fala, a quem, em que '
        'situação e com que propósito; só depois traduzir frase a frase.',
        'Construir a frase portuguesa a partir das cláusulas do original — '
        'nunca a partir de versões portuguesas memorizadas. Preservar '
        'conectores decisivos, contrastes e repetições intencionais.',
        'Voz: português europeu contemporâneo, com cadência para leitura '
        'em voz alta. Plural sempre «vocês»; «tu» apenas em oração '
        'direta a Deus. Nada de arcaísmos de registo («vós», «convosco», '
        '«sois», «eis») nem de hesitação ortográfica («connosco», nunca '
        '«conosco»; «de facto», nunca «de fato»).',
        'Palavras acrescentadas só para o português fazer sentido '
        '(sujeito ou verbo que o grego elide) vão em itálico, para o '
        'leitor saber o que é suplemento: por exemplo, 2 Tessalonicenses '
        '1:5, «Isso é índice…».',
        'Em passagens de eleição, violência, lamento ou intimidade, não '
        'suavizar nem dramatizar: conservar os verbos e as relações do '
        'original, sem qualificações de nenhum sistema teológico — a '
        'discussão vai para a nota.',
        'Nomes próprios nas formas portuguesas consagradas (Filemom, '
        'Áfia, Arquipo, Onésimo…); ἐπίγνωσις sempre «pleno '
        'conhecimento»; SENHOR em maiúsculas só para o Tetragrama (יהוה) '
        'no Antigo Testamento.',
    ]:
        doc.add_paragraph(texto, style='List Bullet')

    # ---------- 8 ----------
    titulo(doc, '8. As notas de estudo', 1)
    p(doc, 'Cada versículo traz uma nota com três secções fixas — é este '
           'formato que permite à oficina verificar automaticamente que '
           'nenhuma nota sai incompleta:')
    tabela(doc, ['Secção', 'Conteúdo'], [
        ['Análise Léxica',
         'As palavras gregas (ou hebraicas) decisivas do versículo, com '
         'transliteração e tradução: o que a palavra significa e porque '
         'foi traduzida assim.'],
        ['Crítica Textual',
         'As variantes do versículo: o que lê a base, o que leem as '
         'edições comparadas e — só quando colacionados — os '
         'manuscritos, com o nível de certeza A/B/C. Gerada a partir do '
         'aparato e do relatório de colação, nunca de memória.'],
        ['Síntese Exegética',
         'O sentido do versículo no seu contexto: o argumento, as '
         'imagens, as ligações com o resto do livro e da Escritura.'],
        ['(Quando se aplicam)',
         'Hermenêutica e Contexto, Geografia e História e Nota de '
         'redação — esta última regista decisões editoriais e '
         'pendências, para auditoria.'],
    ])

    # ---------- 9 ----------
    titulo(doc, '9. Como a obra é produzida (a oficina)', 1)
    p(doc, 'A produção corre numa «oficina» de programas (Python, sem '
           'dependências externas no fluxo principal) que orquestra '
           'modelos de IA de vários fornecedores — Gemini como principal, '
           'Groq como reserva e um rodízio por outros provedores '
           '(Cerebras, NVIDIA, Cohere, entre outros) — porque as quotas '
           'gratuitas são o verdadeiro ritmo da obra. Todos os '
           'fornecedores recebem a mesma memória de estilo '
           '(modelos/estilo_bee.json), para convergirem numa só voz. '
           'A oficina corre de hora a hora, sozinha, em GitHub Actions '
           '(o «agendador»), e cada ciclo fica registado num diário '
           'público no repositório. As camadas de controlo são:')
    for texto in [
        'Porta de estilo (bee/porta.py + bee/inspetor.py): nenhum '
        'versículo é gravado com arcaísmos («-eis», «vós»), hesitação '
        'ortográfica, «estar a» + infinitivo, ponto fora das aspas, '
        'marcadores de rascunho ou palavras greco-latinas misturadas. '
        'A deriva chumba na geração, não meses depois.',
        'Lapidação automática (bee/lapidador.py): quando um capítulo '
        'fecha, a forma das notas é normalizada e a Crítica Textual é '
        'regenerada da evidência antes de qualquer revisão. Notas '
        'curadas à mão são intocáveis — a lapidação é avessa à perda.',
        'Alertas de evidência: siglas de manuscritos citadas sem '
        'testemunha na colação e grego fora da base são assinalados no '
        'diário; o alerta ortográfico PT-PT sinaliza palavras a 1–2 '
        'letras de uma palavra real (a assinatura da gralha).',
        'Revisão por segunda IA: cada capítulo fechado é revisto por um '
        'modelo de outro fornecedor que não o autor do capítulo, com as '
        'emendas filtradas pela mesma porta de estilo.',
        'Testes e verificações: mais de 400 testes automáticos e três '
        'auditores (estilo, dados, documentação) correm sobre o que '
        'fica gravado.',
        'Revisão humana: o responsável lê amostras e aprova pilotos; '
        'a revisão especializada completa é condição de publicação. '
        'Até lá, tudo é RASCUNHO — e diz que o é.',
    ]:
        doc.add_paragraph(texto, style='List Bullet')

    # ---------- 10 ----------
    titulo(doc, '10. Progresso atual', 1)
    p(doc, 'Fotografia de 20 de novembro de 2026, conferida pelos '
           'auditores do projeto (a meta global é 66 livros, 1.189 '
           'capítulos, 31.102 versículos):')
    titulo(doc, '10.1 Edição nova (a voz atual da BEE)', 2)
    tabela(doc, ['Livro', 'Capítulos completos', 'Versículos', 'Estado'], [
        ['João', '1–3 (cap. 4 em curso, 28 vv.)', '112 + 28', 'Rascunho '
         'lapidado; revisão especializada pendente'],
        ['2 Tessalonicenses', '1–3 (livro completo)', '47',
         'Rascunho editorial sobre a base e a colação'],
        ['Tito', '1–3 (livro completo)', '46', 'Piloto aprovado; notas '
         'migradas para o protocolo'],
        ['Filemom', '1 (livro completo)', '25', 'Piloto aprovado; notas '
         'migradas'],
        ['2 João', '1 (livro completo)', '13', 'Piloto aprovado; notas '
         'migradas'],
        ['3 João', '1 (livro completo)', '14', 'Piloto aprovado; notas '
         'migradas'],
        ['Judas', '1 (livro completo)', '25', 'Piloto aprovado; notas '
         'migradas'],
        ['Total edição nova', '13 capítulos', '282 completos + 28 em curso',
         'Tudo RASCUNHO'],
    ])
    titulo(doc, '10.2 Linha legada (produção anterior)', 2)
    p(doc, 'A primeira linha de produção (voz anterior, em revisão) tem '
           '50 capítulos estruturalmente completos e 1.977 versículos, '
           'mais 56 versículos em capítulos em curso — 2.033 versículos '
           'guardados. Esta linha será refeita ou revista à luz da voz e '
           'do protocolo atuais antes de qualquer publicação.')
    titulo(doc, '10.3 Infraestrutura concluída', 2)
    for texto in [
        'Protocolo de crítica textual v1.0 e memória de estilo v1.4 '
        'aprovados e versionados.',
        'Relatórios de colação CNTR para os sete livros em curso '
        '(2 Tessalonicenses integral; João, capítulos 1–4).',
        'Porta de estilo, lapidação automática, alertas de evidência e de '
        'ortografia, revisão por segunda IA e mais de 400 testes.',
        'Agendador horário em GitHub Actions com diário público de cada '
        'ciclo; compilação para módulos MyBible implementada.',
    ]:
        doc.add_paragraph(texto, style='List Bullet')

    # ---------- 11 ----------
    titulo(doc, '11. O que falta e os próximos passos', 1)
    for texto in [
        'Completar o Evangelho de João (capítulo 4 em curso; seguem-se '
        'os capítulos 5–21) e continuar o Novo Testamento.',
        'Revisão especializada das notas marcadas com nível C e das '
        'prioridades registadas (João 1:18; 1:34; 2 Ts 2:13; Judas '
        '1:22–23), seguida da leitura integral pelo responsável.',
        'Estender a colação de manuscritos livro a livro, à medida que '
        'cada um entra em produção, e colacionar as testemunhas '
        'indiretas (versões antigas e Pais da Igreja), hoje registadas '
        'como pendência.',
        'Antigo Testamento sobre o Westminster Leningrad Codex/OSHB, '
        'com o mesmo protocolo.',
        'Só depois da revisão humana: edição final e publicação dos '
        'módulos MyBible sem a marca de rascunho.',
    ]:
        doc.add_paragraph(texto, style='List Bullet')

    # ---------- 12 ----------
    titulo(doc, '12. Perguntas frequentes', 1)
    faq = [
        ('A BEE é «mais uma tradução da Almeida»?',
         'Não. A BEE traduz diretamente do grego e do hebraico fixados, '
         'construindo as frases a partir das cláusulas originais. '
         'Comparações com a Almeida (ARC) servem apenas para documentar '
         'consequências de opções — nunca como fonte nem como modelo.'),
        ('A tradução é feita por inteligência artificial?',
         'A produção de rascunhos usa modelos de IA de vários '
         'fornecedores, sob direção editorial humana, com portas '
         'automáticas de estilo e de evidência, lapidação mecânica e '
         'revisão por um segundo modelo de outro fornecedor. Nada é '
         'publicado como final sem revisão humana especializada. O '
         'projeto diz isto abertamente, no próprio texto: tudo, por '
         'agora, é RASCUNHO.'),
        ('Por que não seguir só os manuscritos mais antigos, ou a '
         'maioria?',
         'Porque os dois critérios medem coisas diferentes e muitas '
         'vezes apontam em direções opostas (ver o caso de 2 '
         'Tessalonicenses 2:13, na secção 6.2). A BEE pesa antiguidade, '
         'diversidade de famílias, distribuição geográfica e as '
         'probabilidades de erro dos escribas — e diz, com nível de '
         'certeza, onde a evidência não decide.'),
        ('«O Textus Receptus diz…» — porque é que as notas não falam '
         'assim?',
         'Porque não existe um só Textus Receptus: o de Scrivener, o de '
         'Stephanus e o texto bizantino de Robinson–Pierpont divergem '
         'entre si em centenas de lugares. As notas dizem sempre qual '
         'das edições lê o quê.'),
        ('Posso usar a BEE na minha igreja ou aplicação?',
         'O texto-base grego (SBLGNT) é CC BY 4.0 e as transcrições '
         'CNTR são CC BY-SA 4.0, com atribuição. A tradução BEE está em '
         'rascunho e em revisão; qualquer uso público deve aguardar a '
         'edição revista pelo responsável. O repositório é público '
         'justamente para que o processo possa ser acompanhado e '
         'conferido.'),
        ('Como posso conferir uma afirmação de uma nota?',
         'Abra o relatório de colação do livro em docs/colacao/: lá '
         'estão, versículo a versículo, a base, o aparato e o que cada '
         'testemunha colacionada lê. Se uma nota citar apoio que o '
         'relatório não mostra, isso é um erro do projeto — e há '
         'verificações automáticas desenhadas para o apanhar.'),
    ]
    for pergunta, resposta in faq:
        par = doc.add_paragraph()
        run = par.add_run(pergunta)
        run.bold = True
        p(doc, resposta)

    # ---------- Anexo A ----------
    titulo(doc, 'Anexo A — Testemunhas e edições citadas nas notas', 1)
    tabela(doc, ['Sigla', 'Identificação'], [
        ['P45, P66, P75…', 'Papiros do Novo Testamento (numeração '
                           'Gregory–Aland).'],
        ['01 (א)', 'Códice Sinaítico, séc. IV — um dos dois grandes '
                   'códices completos mais antigos.'],
        ['02 (A)', 'Códice Alexandrino, séc. V.'],
        ['03 (B)', 'Códice Vaticano, séc. IV.'],
        ['04, 05, 0162, 029, 032…', 'Outros unciais colacionados onde o '
                                     'relatório do livro os mostra.'],
        ['SBLGNT', 'SBL Greek New Testament (Holmes, 2010) — a base '
                   'traduzida.'],
        ['WH', 'Westcott–Hort (1881).'],
        ['Treg', 'Tregelles (1857–1872).'],
        ['NA28', 'Nestle–Aland, 28.ª edição — conhecida nas notas '
                 'através do aparato do SBLGNT.'],
        ['RP', 'Robinson–Pierpont, Texto Bizantino Maioritário (2005).'],
        ['Scrivener / ST / KJTR', 'Textus Receptus de Scrivener (1894), '
                                  'de Stephanus (1550) e o da King James.'],
        ['CNTR', 'Center for New Testament Restoration — transcrições '
                 'eletrónicas dos manuscritos (Alan Bunning).'],
    ])

    # ---------- Anexo B ----------
    titulo(doc, 'Anexo B — Glossário mínimo', 1)
    tabela(doc, ['Termo', 'Significado'], [
        ['Autógrafo', 'O exemplar original escrito pelo autor bíblico; '
                      'não sobrevive de nenhum livro.'],
        ['Variante (unidade de variação)', 'Um ponto onde as cópias '
                      'divergem entre si.'],
        ['Aparato crítico', 'O registo, ao pé do texto grego, das '
                      'leituras alternativas e de quem as apoia.'],
        ['Colação', 'A comparação sistemática, versículo a versículo, '
                      'de várias testemunhas.'],
        ['Itacismo', 'Troca ortográfica de sons que em grego tardio se '
                      'pronunciavam da mesma maneira (ει/ι, ο/ω…): erro '
                      'típico de escriba, sem mudança de sentido.'],
        ['Nomina sacra', 'As abreviaturas sagradas dos copistas '
                      '(θεός → ΘΣ, κύριος → ΚΣ…), com traço por cima.'],
        ['Lacuna', 'Parte perdida ou ilegível de um manuscrito.'],
        ['Ecletismo fundamentado', 'O método que pesa, unidade a '
                      'unidade, a evidência externa e interna para '
                      'estabelecer o texto.'],
        ['Epígnōsis (ἐπίγνωσις)', '«Pleno conhecimento» — a palavra '
                      'que dá nome ao projeto.'],
    ])

    doc.add_page_break()
    fim = doc.add_paragraph()
    fim.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = fim.add_run('— Fim do documento de apresentação —\n')
    r.bold = True
    r.font.color.rgb = AZUL
    p(doc, 'Fontes internas: README.md; docs/ESTADO.md (17/11/2026); '
           'docs/CRITICA_TEXTUAL.md (protocolo v1.0, 20/11/2026); '
           'docs/SBLGNT.md; modelos/estilo_bee.json (memória de '
           'estilo v1.4); relatórios de colação em docs/colacao/; '
           'dados da edição nova em edicoes/nova/livros_json/, '
           'conferidos por scripts/verificar_dados.py em 20/11/2026.',
      alignment=WD_ALIGN_PARAGRAPH.CENTER)
    return doc


if __name__ == '__main__':
    documento = construir()
    documento.save(SAIDA)
    print(f'Escrito: {SAIDA}')
