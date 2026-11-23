# Crítica textual, manuscritologia, exegese, hermenêutica, geografia e arquivologia

**Protocolo da edição nova (v1.0) — 20/11/2026.**
Aplica-se à Bíblia de Estudo Epignósis. Primeiro livro tratado por este
protocolo: **2 Tessalonicenses** (`edicoes/nova/livros_json/600_2_Tessalonicenses.json`).
Colação verificável em [`docs/colacao/2_Tessalonicenses.md`](colacao/2_Tessalonicenses.md)
e `.json`, produzida por `python3 scripts/colar.py --livro 600`.

> Este documento parte de uma proposta do responsável — *«vamos fazer estudo de
> crítica textual, manuscritos, manuscritologia… manuscritos mais antigos e com
> mais cópias devem ser priorizados»* — e reformula-a como procedimento. A
> reformulação não enfraquece a convicção: torna-a verificável.

---

## 1. Convicção doutrinária e o que ela exige do método

O projeto confessa a **inerrância, a infalibilidade e a imutabilidade das
Escrituras**. Este protocolo leva essa confissão a sério e, por isso, distingue
duas afirmações que costumam ser fundidas:

| Afirmação | Sobre o quê | Quem a decide |
|---|---|---|
| «A Escritura é inerrante e imutável» | o texto que Deus deu (o autógrafo) | a confissão de fé |
| «Esta cópia lê ἀπαρχήν, aquela lê ἀπʼ ἀρχῆς» | os manuscritos que chegaram até nós | a evidência |

Consequências práticas, e são estas que governam todo o resto:

1. **A crítica textual não corrige a doutrina; procura o texto.** Ela existe
   porque o texto nos chegou em cópias feitas por seres humanos. A confissão de
   inerrância não afirma que cada cópia é perfeita — se afirmasse, as milhares
   de diferenças entre cópias refutariam a confissão em cinco minutos. Afirmar
   que o **original** é inerrante e trabalhar para o recuperar é a posição
   coerente; é também a posição histórica das igrejas da Reforma, que
   produziram e usaram aparato crítico.
2. **A doutrina não decide uma variante.** Nenhuma leitura é adotada por
   favorecer uma teologia, nem rejeitada por desfavorecê-la. Se a evidência
   aponta para uma leitura teologicamente incómoda, adota-se a leitura e
   discute-se a teologia na nota. O inverso também vale.
3. **A incerteza regista-se, não se esconde.** Onde a evidência não decide, o
   livro diz que não decide. Esconder uma variante para «proteger» o leitor
   produz exatamente o ceticismo que se queria evitar, no dia em que o leitor
   abrir uma Bíblia com aparato.
4. **O que a evidência mostra é tranquilizador, e convém dizê-lo com números.**
   Em 2 Tessalonicenses, sobre 47 versículos colacionados contra 5 testemunhas
   manuscritas e 6 textos impressos, **nenhuma** unidade de variação altera um
   artigo de fé, um mandamento ou uma promessa. A maior parte das divergências
   (57 registos) é ortográfica — itacismos de escriba como ὀφείλομεν/ὀφίλομεν.
   As que têm peso exegético são cerca de duas dezenas, e todas estão listadas
   e decididas abaixo. Isto não é um argumento de fé contra a crítica textual: é
   o **resultado** da crítica textual aplicada com honestidade.

---

## 2. A regra dos «mais antigos e com mais cópias» — por que não se aplica como slogan

A proposta original diz que se devem priorizar os manuscritos **mais antigos** e
**com mais cópias**. Os dois critérios são legítimos, mas medem coisas
diferentes e, com frequência, **apontam em direções opostas**. Aplicá-los como
um só slogan produz decisões arbitrárias disfarçadas de método.

### 2.1 O caso real que desfaz o slogan: 2 Tessalonicenses 2:13

Leitura em causa: ὅτι εἵλατο ὑμᾶς ὁ θεὸς **ἀπαρχὴν** εἰς σωτηρίαν («Deus vos
escolheu **como primícias** para a salvação») ou **ἀπʼ ἀρχῆς** («**desde o
princípio**»). Colação efetiva (transcrições CNTR, revisão `4e743a4`):

| Testemunha | Leitura | Tradução |
|---|---|---|
| **03** Vaticanus (séc. IV) | ἀπαρχήν | «como primícias» |
| **02** Alexandrinus (séc. V; aqui com lacuna suprida) | ἀπαρχήν | «como primícias» |
| **01** Sinaiticus (séc. IV) | ἀπʼ ἀρχῆς | «desde o princípio» |
| RP (Texto Bizantino Maioritário) | ἀπʼ ἀρχῆς | «desde o princípio» |
| ST, KJTR, Scrivener TR | ἀπʼ ἀρχῆς | «desde o princípio» |
| WH (Westcott–Hort) | ἀπʼ ἀρχῆς | «desde o princípio» |
| SBLGNT (base fixada) e NA28 | **ἀπαρχήν** | «como primícias» |

O que acontece aos dois critérios:

- **Antiguidade não decide.** Os três unciais mais antigos que conservam o
  versículo dividem-se 2 × 1. Não há «o mais antigo» a que recorrer: há três
  testemunhas do mesmo século-ish, em desacordo.
- **Quantidade não decide.** O grosso da tradição (milhares de manuscritos
  bizantinos, representados aqui por RP/ST/KJTR) lê ἀπʼ ἀρχῆs — mas esses
  manuscritos são tardios e descendem, em boa parte, uns dos outros. Contá-los
  como votos independentes é contar o mesmo voto milhares de vezes.
- **Decide o argumento.** ἀπαρχήν é a leitura **mais difícil**: «escolhidos como
  primícias» é uma imagem paulina específica (cf. Rm 16:5; 1 Co 16:15) e menos
  corrente do que a fórmula banal «desde o princípio». Um escriba tende a
  transformar o difícil no fácil, não o fácil no difícil; e ἀπʼ ἀρχῆs pode ainda
  ter sido sugerida pelo contexto (2 Ts 2:13 fala de escolha). Por isso NA28 e o
  SBLGNT imprimem ἀπαρχήν. **Esta é a leitura da nossa base fixada, e é ela que
  a BEE traduz.**

Moral do caso, e é a regra que fica: **antiguidade e número são indícios, não
árbitros.** O que se avalia é a antiguidade e a qualidade da **leitura**, não do
suporte — uma cópia do séc. XIV pode transmitir fielmente um ancestral do séc.
II, e um códice do séc. IV pode conter um erro do seu próprio escriba.

### 2.2 O que a evidência externa realmente mede

Quatro perguntas, por esta ordem:

1. **Antiguidade** — quão cedo a leitura aparece? (Não: quão antigo é o
   manuscrito. Um códice antigo pode ser o único a conter uma inovação.)
2. **Qualidade e diversidade genealógica** — as testemunhas pertencem a famílias
   textuais diferentes? Uma leitura com apoio em Alexandria, em Bizâncio, no
   Ocidente latino e na tradição siríaca é mais difícil de explicar como erro
   local do que uma leitura com apoio numa só família, mesmo que essa família
   tenha muitos membros.
3. **Distribuição geográfica** — apoio espalhado pesa mais do que apoio
   concentrado numa região.
4. **Número** — só depois de 1 a 3. Nunca antes.

### 2.3 O que a evidência interna realmente mede

1. **Probabilidade transcricional** (o que os escribas faziam): a leitura mais
   difícil tende a ser anterior; harmonizações a passagens paralelas, expansões
   explicativas, correções gramaticais e assimilações de fórmulas epistolares
   tendem a ser posteriores. A direção habitual do erro é **esclarecer,
   completar e harmonizar**.
2. **Probabilidade intrínseca** (o que o autor escrevia): vocabulário, sintaxe e
   teologia do autor noutros lugares; o argumento da passagem.
3. **Regra de ouro**: a leitura adotada deve **explicar a origem das outras**.
   Se uma teoria da variante não diz por que razão algum escriba escreveria a
   alternativa, está incompleta.

### 2.4 O método resultante

Ecletismo fundamentado (*reasoned eclecticism*): evidência externa e interna
pesadas em conjunto, unidade por unidade, sem preferência automática por um só
manuscrito nem pela maioria. É o método da base que o projeto já fixou (o
SBLGNT é uma edição eclética de Michael W. Holmes) e é compatível com a
confissão de inerrância — que se refere ao autógrafo, não a uma edição.

> **Nota sobre uma alternativa legítima.** Existe uma escola que dá prioridade
> sistemática ao Texto Bizantino Maioritário (posição «majoritária»). Ela é
> defendida por crentes igualmente convictos da inerrância e não é uma posição
> herética. A BEE **não** a adota, porque fixou o SBLGNT como base antes de
> começar a gerar livros (ver [`SBLGNT.md`](SBLGNT.md)) e porque a posição
> maioritária exige demonstrar que a tradição bizantina preserva o texto
> original em cada unidade, o que os dados de 2Ts 2:13 e 2:2 não sustentam.
> Regista-se aqui para que a escolha seja visível e não pareça acidente.

---

## 3. Níveis de evidência: nunca os misturar num mesmo enunciado

| Nível | O que é | O que se pode dizer com ele |
|---|---|---|
| **1. Base fixada** | SBLGNT `d7f35ad` + aparato SBLGNT + Scrivener TR `6049a43` | «a base traduzida lê X»; «o aparato regista Y em WH/Treg/NA28/RP/NIV» |
| **2. Testemunhas** | transcrições CNTR em MES: P30, P92, 01, 02, 03 | «o Vaticanus lê X»; «o Sinaiticus foi corrigido de X para Y» |
| **3. Indiretas** | versões antigas, citações patrísticas (acervo CNTR `class 3`) | ainda **não colacionadas** para 2Ts — pendência |
| **4. Interpretação** | comentários, gramáticas, dicionários | «segundo X…» — só com obra efetivamente consultada |

Três proibições que vêm daqui:

- **Edição impressa não é manuscrito.** O aparato do SBLGNT compara WH, Treg,
  NA28, RP e NIV. Dizer «os manuscritos mais antigos dizem…» com base nesse
  aparato é falso: são edições, e uma edição é uma decisão de um editor.
- **Tradução moderna não é evidência textual.** A NIV aparece no aparato do
  SBLGNT como registo de uma escolha tradutória. Citar a ARC, a NVI ou a KJV
  mostra **consequências de opções**, não testemunhos.
- **«O Textus Receptus» não é um texto único.** Na nossa colação, RP
  (Robinson–Pierpont, Texto Bizantino Maioritário) lê πιστεύσασιν em 1:10,
  enquanto Scrivener/ST/KJTR leem πιστεύουσιν; em 3:6 RP lê παρέλαβον e Scrivener
  παρέλαβεν. Falar de «o TR» sem dizer qual é falar de uma abstração.

---

## 4. Registo de testemunhas de 2 Tessalonicenses (manuscritologia + arquivologia)

Acervo efetivamente consultado: **CNTR Electronic Transcriptions**, Alan
Bunning / Center for New Testament Restoration, revisão
`4e743a41a4b2ca010ece53229cd272aa59b1efe6` (1/10/2026), licença **CC BY-SA 4.0**,
<https://github.com/Center-for-New-Testament-Restoration/transcriptions>.
Cópia local em `.bee-cache/cntr/` (**ignorada pelo Git** — ver §8).

| Sigla | Gregory-Aland | Suporte | 2Ts conservado | Estado físico em 2Ts | Correções de mão posterior |
|---|---|---|---|---|---|
| **P92** | P92 (P.Oxy. 3523) | papiro | 4 versículos: 1:4-5.11-12 | lacunoso em todos os 4; texto suprido pelo editor | — |
| **P30** | P30 | papiro | 6 versículos: 1:1-2; 2:1; 2:9-11 | lacunoso nos 6 | — |
| **01** | 01 (א, Sinaiticus) | códice em pergaminho | carta inteira (47 vv.) | íntegro | 1:1; 2:1; 2:4; 2:14; 2:16 |
| **02** | 02 (A, Alexandrinus) | códice em pergaminho | carta inteira | 11 versículos com lacuna | 2:10; 3:16 |
| **03** | 03 (B, Vaticanus) | códice em pergaminho | carta inteira | 3 versículos com lacuna | — |

Textos impressos colacionados do mesmo acervo: **WH** (Westcott–Hort), **RP**
(Robinson–Pierpont, Byzantine Majority Text), **ST** (Stephanus), **KJTR**
(Textus Receptus da KJV), **SR** (Statistical Restoration, CNTR).

### 4.1 O que este registo NÃO autoriza a dizer

O acervo CNTR consultado contém, para 2 Tessalonicenses, **apenas estas cinco
testemunhas**. Portanto a BEE **não** pode afirmar nada sobre:

- os restantes unciais de Paulo (04/C, 06/D, 010/F, 012/G, 018/K, 020/L,
  025/P, 044/Ψ, 0278);
- os minúsculos (33, 81, 104, 177, 365, 1175, 1881, 2464…);
- as versões antigas (Vetus Latina, Vulgata, Peshitta, Copta, Gótica);
- as citações dos Padres (Marcion, Irineu, Orígenes, Tertuliano…), embora o
  acervo CNTR tenha uma pasta `class 3` com alguns deles.

Sempre que uma destas fontes for invocada, é preciso colacioná-la primeiro ou
escrever «não verificado». **Não existe manuscrito em 2Ts a que se possa chamar
«o mais antigo»: o papiro P92 é o suporte mais antigo que conservamos, mas só
traz quatro versículos.** Quem escreve «os manuscritos mais antigos» a pensar
num corpo de evidência que não abriu está a escrever ficção.

### 4.2 Pendências de verificação (registadas, não inventadas)

| Item | Estado | Onde confirmar |
|---|---|---|
| Datação de P92, P30, 01, 02, 03 | **não verificada eletronicamente** neste ambiente; as datações usuais (P92 séc. III; P30 séc. IV; א e B séc. IV; A séc. V) são consenso de catálogo, não resultado de exame | *Kurzgefasste Liste* (INTF Münster) / NTVMR |
| Localização atual de cada códice (British Library, Biblioteca Vaticana, etc.) | **não verificada** | catálogos das instituições detentoras |
| Identificação de «P30» com 2Ts | o acervo CNTR atribui-lhe 1Ts **e** 2Ts 1:1-2; 2:1; 2:9-11; catálogos impressos costumam descrever P30 por 1 Tessalonicenses | *Liste*; P.Oxy. 1236 |
| Códigos Strong | **não integrados**; não há conjunto de dados Strong verificado no projeto | integrar um léxico com licença verificada |
| Testemunhas indiretas (versões, Padres) | **não colacionadas** | acervo CNTR `class 3`; edições das versões |
| Nestle-Aland 28 aparato completo | **não consultado**; só o que o aparato SBLGNT regista sobre NA28 | edição impressa/licenciada |

Nenhuma destas lacunas é preenchida por suposição. Uma nota que precise delas
diz que precisa delas.

---

## 5. Procedimento por unidade de variação (sete passos)

1. **Fixar e ler.** Base SBLGNT; aparato SBLGNT; Scrivener TR; testemunhas CNTR.
   Ler o versículo inteiro e o parágrafo, não a palavra.
2. **Classificar a diferença.** (a) ortográfica/itacismo — não é variante
   textual relevante; (b) transposição sem mudança de sentido; (c) adição ou
   omissão; (d) substituição substantiva. Só (c) e (d) exigem decisão editorial
   e nota; (a) e (b) podem ser registadas em bloco.
3. **Evidência externa.** Quem lê o quê, e em que estado físico. Uma leitura
   sustentada só por texto suprido numa lacuna vale menos do que uma leitura
   legível. Uma mão corrigida conta como **duas** testemunhas de duas épocas
   diferentes, não como uma.
4. **Evidência transcricional.** Qual leitura explica a origem das outras?
5. **Evidência intrínseca.** O que Paulo escreve noutros lugares; o que o
   argumento exige aqui.
6. **Decidir e traduzir.** Se a base já decidiu, a BEE traduz a base e diz que a
   decisão é da base — não se apropria de uma decisão editorial alheia.
7. **Registar.** Referência, leituras, apoio, decisão, razão e pendências. O registo vive em duas partes: a nota do versículo (para o
   leitor) e o campo `critica_textual` do JSON do livro (para auditoria).

### 5.1 Convenções de marcação

| Marca | Uso | Exemplo |
|---|---|---|
| `[[ … ]]` | leitura assinalada: adotada pela base mas ausente noutros testemunhos; alternativa substantiva; ou suplemento do Scrivener ausente do SBLGNT | Marcos 16:9-20 |
| `<i>…</i>` | palavra acrescentada pela tradução para clareza, sem correspondente no original | 2Ts 2:3 `<i>esse dia não virá</i>`; 1:5 `<i>Isso é</i>`; 2:9 `<i>acontece</i>` |
| `SENHOR` (maiúsculas) | **só** o Tetragrama יהוה no AT | Sl 23:1 |
| `Senhor` | κύριος/אֲדֹנָי, inclusive no NT | 2Ts 2:2 «o dia do Senhor» |
| vírgula no fim do versículo + minúscula no seguinte | o versículo continua a frase do anterior | 2Ts 1:11 → 1:12; 2:16 → 2:17; 3:1 → 3:2 |
| ponto (ou ponto e vírgula) + maiúscula | o versículo abre frase nova | 2Ts 2:8 `;` → 2:9 |

**Onde vai o itálico.** Marcam-se verbo, sujeito ou oração que o português exige e
o grego não tem — 1:5 é um fragmento nominal (*ἔνδειγμα τῆς δικαίας κρίσεως*) e
precisa de «*Isso é*»; 2:9 é uma relativa sem verbo (*οὗ ἐστιν ἡ παρουσία*) e
precisa de «*acontece*»; 3:9 tem um *ἀλλʼ ἵνα* elíptico e precisa de «*fizemos
assim*». **Não** se marcam artigo, pronome e preposição meramente gramaticais
(«ele os chamou», «o nome do nosso Senhor»): marcar tudo torna o texto ilegível e
não marca nada esconde do leitor onde o português acrescentou. O critério é: o
leitor consegue apontar para o grego e não encontrar a palavra? Se sim, itálico.

**Pontuação e maiúscula inicial.** A relação sintática entre versículos nunca é
apagada: se um versículo continua a frase do anterior, termina em vírgula (ou
ponto e vírgula) e o seguinte começa em minúscula; se abre frase nova, termina em
ponto e o seguinte começa em maiúscula. Nunca minúscula depois de ponto, nunca
maiúscula depois de vírgula, e nenhum versículo fica sem pontuação final. Onde o
grego tem uma relativa que o português não consegue pendurar no antecedente sem
ambiguidade, abre-se frase nova e a nota regista-o — é o caso de 2Ts 2:9
(*οὗ ἐστιν ἡ παρουσία*, «cuja vinda…», que depois de «o esplendor da sua vinda»
tomaria «vinda» como antecedente). A regra está em
[`modelos/estilo_bee.json`](../modelos/estilo_bee.json) →
`regras_duras` → «PONTUAÇÃO E MAIÚSCULA INICIAL» e é conferida
mecanicamente pelo verificador de pontuação e maiúscula, e por
[`tests/test_critica_textual.py`](../tests/test_critica_textual.py).

> **Correção aplicada em 2Ts 2:2.** O texto anterior trazia «o dia do SENHOR»,
> em maiúsculas. No grego do NT não há Tetragrama: κύριος está escrito por
> extenso. Usar `SENHOR` ali afirma que a base grega contém יהוה, o que não é
> verdade do texto que traduzimos. A ligação com a fórmula profética «o dia do
> SENHOR» (Jl 2:1; Am 5:18; Sf 1:14) é real e pertence à **nota**, não à
> tipografia do versículo.

---

## 6. Exegese e hermenêutica

### 6.1 Regras

1. **A unidade é o parágrafo, não o versículo.** Em 2Ts 1:3-12 uma só frase
   corre dos vv. 3 a 10; traduzir cada versículo como sentença isolada destrói o
   argumento. A BEE preserva os conectores (ὥστε, εἴπερ, ὅταν, ὅπως, εἰς ὃ) e só
   divide onde a lógica sobrevive à divisão.
2. **A carta é ocasional.** Lê-se perguntando: quem escreve, a quem, que
   problema concreto motivou, o que o autor quer que os destinatários **façam**.
   Em 2Ts são duas situações: (a) uma alegação de que «o dia do Senhor já
   chegou», atribuída a espírito, a palavra ou a carta pretensamente paulina
   (2:2); (b) irmãos a viver ἀτάκτως, sem trabalhar (3:6-13).
3. **Reserva escatológica.** Em texto apocalíptico, conservar imagens, números e
   ambiguidades. **Não converter uma interpretação em tradução.** O caso-limite
   é 2:6-7: o grego distingue τὸ κατέχον (**neutro**, «o que detém») de
   ὁ κατέχων (**masculino**, «aquele que detém»). Neutralizar a diferença na
   tradução é escolher um sistema escatológico à revelia do leitor. A tradução
   mantém o neutro e o masculino; a nota lista as leituras principais (império e
   imperador romanos; Espírito/Evangelho; anjo; autoridade civil; um «detentor»
   escatológico) **sem adotar nenhuma**.
4. **Gramática antes de teologia.** Voz (a passiva de 1:5 καταξιωθῆναι, «serem
   considerados dignos», não nomeia o agente e a tradução não o inventa), aspeto
   (πέμπει presente em 2:11 contra πέμψει futuro do Bizantino: a base lê um envio
   em curso, não apenas futuro), caso (dativo de instrumento em τῷ πνεύματι τοῦ
   στόματος, 2:8), artigo (ὁ ἄνομος é título, não descrição).
5. **Fundo do AT na nota, não no versículo.** 1:7-10 usa linguagem de teofania
   (Is 66:15; Sl 50:3; Dn 7:9-10) e 2:8 ecoa Is 11:4 e 30:33. Citar os ecos
   ajuda; escrevê-los dentro do versículo, não.
6. **Não harmonizar à força.** 2Ts não se lê para confirmar 1Ts nem um sistema;
   lê-se para dizer o que diz. Diferenças entre as duas cartas (por exemplo o
   tratamento do «dia») ficam registadas como diferenças.

### 6.2 Estrutura da nota de cada versículo

Forma vigente (desde 2026-11-23): **um parágrafo de prosa por versículo, sem
rótulos e sem notação de nível.** A Crítica Textual é um parágrafo próprio, só
quando há variante registada:

1. **Comentário** (um parágrafo) — o termo grego em itálico com transliteração,
   as opções de tradução, a razão da escolha e a síntese do que a passagem diz e
   do que não diz. Se a passagem pede, o parágrafo também traz o género, o fundo
   do AT ou a leitura concorrente legítima.
2. **«Crítica Textual:»** (parágrafo próprio, opcional) — só o que foi
   colacionado ou está no aparato. Cita as siglas, diz as leituras, o apoio e a
   decisão. Sem variante, não há parágrafo: não se escreve «sem variante
   verificada» como enchimento.

A redação anterior (Análise Léxica / Crítica Textual / Síntese Exegética) está arquivada no histórico: `git log` até `a80fa33`, e a
conversão de 5–10 ainda está por fazer (ver `docs/EDITORIAL.md`).

### 8.1 O que cada fonte tem de declarar

Nome · edição/revisão (commit) · URL · licença · papel (base / comparação /
testemunha / aparato) · data de acesso · integridade (SHA-256 quando aplicável) ·
o que foi efetivamente consultado nela.

Isto vai para o campo **`bibliography`** do JSON do livro, que a infraestrutura já
valida (`bee/arquivos.py`). O campo `sources` continua a fixar os commits.

### 8.2 Três estados de revisão, sempre separados

| Estado | O que afirma | Onde vive |
|---|---|---|
| **Cobertura** | quantos versículos/capítulos existem e são estruturalmente válidos | `chapters` / `in_progress` |
| **Revisão editorial** | o responsável leu e aprovou a voz e as decisões | `review.editorial_blocks` |
| **Revisão especializada** | hebraísta/grecista/crítico textual/teólogo reviu | `review.specialist` |

Cobertura completa **não** é aprovação editorial, e aprovação editorial **não** é
revisão especializada. O compilador copia os estados declarados e valida os
intervalos, mas não prova que aconteceram — por isso os módulos saem sempre
rotulados **RASCUNHO**.

### 8.3 Licenças e redistribuição

| Fonte | Licença | O que isso obriga |
|---|---|---|
| SBLGNT (base) | CC BY 4.0 | atribuição; indicar alterações; **não** é domínio público |
| Scrivener TR | domínio público segundo o fornecedor | atribuição de cortesia |
| WLC/OSHB (AT) | CC BY 4.0 | atribuição |
| **CNTR transcriptions** | **CC BY-SA 4.0** | atribuição + **ShareAlike**: um derivado teria de usar a mesma licença |
| BHP/SR/KJTR (CNTR) | CC BY 4.0 | atribuição |

Decisão de custódia sobre o CC BY-SA: **a BEE consulta e cita as transcrições
CNTR; não as redistribui.** O acervo descarregado vive em `.bee-cache/`, que o
`.gitignore` já exclui, e o repositório guarda apenas o **relatório de colação**
(`docs/colacao/`), que é obra nossa: cita leituras curtas com atribuição e não
reproduz os ficheiros. Assim a tradução não se torna um derivado das
transcrições e não fica sujeita ao ShareAlike — ao mesmo tempo que a atribuição
exigida é cumprida em cada livro e neste documento.

### 8.4 Fixidez

Nada de «descarreguei um dia destes». Cada fonte é fixada por **commit** e
verificada por **SHA-256** (`bee/fontes.py` já o faz para WLC, SBLGNT e Scrivener;
`scripts/colar.py` regista a revisão CNTR no cabeçalho do relatório). Uma colação
sem revisão fixada não é reproduzível e, portanto, não é evidência.

---

## 9. Decisões de crítica textual registadas para 2 Tessalonicenses

A nota diz a razão da escolha e a alternativa rejeitada, sem notação de nível de
certeza. As passagens de decisão difícil ficam assinaladas em `review`, como
prioridade de revisão especializada.

| Ref. | Unidade | Base (adotada) | Alternativa e apoio | Decisão |
|---|---|---|---|---|
| 1:2 | θεοῦ πατρὸς [ἡμῶν] | πατρὸς (sem ἡμῶν) | + ἡμῶν: 01, 02, RP, ST, KJTR, SR, Scrivener; NA28 e Treg têm ἡμῶν; 03 e WH não | **segue a base**: «da parte de Deus Pai», sem «nosso». O argumento transcricional aponta todo num sentido — o v. 1 tem πατρὶ ἡμῶν, a fórmula paulina corrente é «Deus, nosso Pai», e em 1Ts 1:1 o RP acrescenta a fórmula inteira; um escriba tinha três razões para escrever ἡμῶν e nenhuma para o omitir. A tradução anterior seguia a expansão bizantina enquanto a nota registava a divergência |
| 1:3 | πάντων ὑμῶν | ὑμῶν presente | 01 omite o segundo ὑμῶν; lê ὀφίλομεν (itacismo) | segue a base |
| 1:4 | αὐτοὺς ἡμᾶς / ἐγκαυχᾶσθαι | ordem αὐτοὺς ἡμᾶς; composto ἐγκαυχᾶσθαι | ἡμᾶς αὐτοὺς e καυχᾶσθαι: RP, ST, KJTR, Scrivener; ἐνκαυχᾶσθαι (sem γ): 02, 03 | segue a base; «gloriamo-nos» cobre as duas |
| 1:8 | φλογὶ πυρός / πυρὶ φλογός | **φλογὶ πυρός** (SBL com Tregelles) | πυρὶ φλογός: 01, 02, WH, NA28, RP, ST, KJTR, Scrivener, SR | **segue a base mesmo com apoio minoritário**: só 03 (Vaticanus) sustenta φλογὶ πυρός entre as testemunhas colacionadas; a ordem das palavras não muda o sentido («chama de fogo» / «fogo em chama»). Registado como decisão da base, não nossa |
| 1:8 | τοῦ κυρίου ἡμῶν Ἰησοῦ [Χριστοῦ] | sem Χριστοῦ | + Χριστοῦ: 01, 02, ST, KJTR, SR, Scrivener | segue a base; expansão litúrgica habitual |
| 1:10 | πιστεύσασιν / πιστεύουσιν | **aoristo** πιστεύσασιν | presente πιστεύουσιν: ST, KJTR, Scrivener (**RP não**) | segue a base: «os que creram» (ato de crer que já aconteceu). Note-se que RP e o TR de Scrivener divergem — «o Bizantino» não é um texto único |
| 1:12 | κυρίου ἡμῶν Ἰησοῦ [Χριστοῦ] | sem Χριστοῦ (1ª ocorrência) | + Χριστοῦ: KJTR, ST, Scrivener; 02 lê ἡμεῖς por ὑμεῖς | segue a base; ἡμεῖς registado na nota |
| 2:2 | μηδὲ / μήτε | μηδὲ | μήτε: RP, ST, KJTR, Scrivener | segue a base; conjunção equivalente |
| 2:2 | ἡ ἡμέρα τοῦ **κυρίου** / τοῦ **Χριστοῦ** | κυρίου | Χριστοῦ: RP, ST, KJTR, Scrivener; 01, 02, 03 apoiam κυρίου | **segue a base**: «o dia do Senhor», com κύριος por extenso no grego (sem Tetragrama) e a ligação profética na nota |
| 2:3 | ὁ ἄνθρωπος τῆς **ἀνομίας** / τῆς **ἁμαρτίας** | ἀνομίας | ἁμαρτίας: 02, RP, ST, KJTR, Scrivener; 01 e 03 apoiam ἀνομίας | segue a base: «o homem da rebelião»; a designação «homem do pecado» fica na nota. Para ὁ υἱὸς τῆς ἀπωλείας a tradução usa «o filho da ruína»: «filho da perdição» é corrente de genitivos à Almeida e está vetado na memória de estilo |
| 2:4 | εἰς τὸν ναὸν τοῦ θεοῦ [ὡς θεόν] | sem ὡς θεόν | + ὡς θεόν: RP, ST, KJTR, Scrivener; Scrivener lê também πᾶν τὸ por πάντα | segue a base: o versículo já diz «proclamando-se deus» (ἀποδεικνύντα ἑαυτὸν ὅτι ἔστιν θεός) — a adição é duplicação |
| 2:6 | ἐν τῷ **ἑαυτοῦ** καιρῷ / **αὐτοῦ** | ἑαυτοῦ | αὐτοῦ: 01, 02, WH, Treg, SR; NA28 e RP têm ἑαυτοῦ | segue a base; 01 lê ainda κατέχω/οἴδαται (registado como leitura própria, abreviatura a rever) |
| 2:8 | ὃν ὁ κύριος **Ἰησοῦς** ἀνελεῖ | com Ἰησοῦς | 03 omite Ἰησοῦς; ἀναλώσει em RP, ST, KJTR, Scrivener | segue a base: «o Senhor Jesus… destruirá». ἀναιρέω («tirar a vida») vs ἀναλίσκω («consumir») registado |
| 2:10 | πάσῃ ἀπάτῃ ἀδικίας [ἐν] τοῖς | ἀδικίας direto | τῆς ἀδικίας ἐν: RP, ST, KJTR, Scrivener | segue a base |
| 2:11 | **πέμπει** / πέμψει | presente πέμπει | futuro πέμψει: RP, ST, KJTR, Scrivener | segue a base: «envia» (ação em curso), não «enviará» |
| 2:12 | πάντες / ἅπαντες; τῇ ἀδικίᾳ / ἐν τῇ | πάντες; τῇ | ἅπαντες: SR, RP; + ἐν: RP, ST, KJTR, Scrivener | segue a base |
| 2:13 | **ἀπαρχὴν** / ἀπʼ ἀρχῆς | **ἀπαρχὴν** («primícias») | ἀπʼ ἀρχῆs: 01, WH, RP, ST, KJTR, SR, Scrivener, NIV; 02 e 03 apoiam ἀπαρχήν | **segue a base**: ver §2.1. Tradução: «como primícias para a salvação»; «desde o princípio» fica na nota. A tradução anterior seguia a leitura bizantina sem o dizer |
| 2:13 | εἵλατο / εἵλετο | εἵλατο | εἵλετο: RP, ST, KJTR, Scrivener | ortográfica; segue a base |
| 2:14 | εἰς ὃ ἐκάλεσεν **ὑμᾶς** / ἡμᾶς | ὑμᾶς | ἡμᾶς: 02, 03; 01 foi corrigido de ὑμῶν para ἡμῶν no v. anterior; NA28 tem + καί | segue a base: «ele os chamou» |
| 2:16 | θεὸς ὁ πατήρ / ὁ θεὸς καὶ πατήρ | καὶ θεὸς ὁ πατήρ | ὁ θεὸς καὶ πατήρ: RP, ST, KJTR, Scrivener; 01 recebeu καί e «ὁ ἀγαπήσας ἡμᾶς» por mão posterior | segue a base |
| 2:17 | στηρίξαι [ὑμᾶς]; ἔργῳ καὶ λόγῳ | sem ὑμᾶς; ordem ἔργῳ καὶ λόγῳ | + ὑμᾶς e λόγῳ καὶ ἔργῳ: RP, ST, KJTR, Scrivener | segue a base; a ordem não muda o sentido |
| 3:3 | πιστὸς δέ ἐστιν ὁ **κύριος** | κύριος | 02 lê ὁ θεός e acrescenta καί (com letra danificada em στηρίξει) | segue a base; leitura de 02 registada |
| 3:4 | ἃ παραγγέλλομεν [ὑμῖν] | sem ὑμῖν | + ὑμῖν: RP, ST, KJTR, Scrivener; 03 acrescenta καὶ ἐποιήσατε | segue a base |
| 3:6 | τὴν παράδοσιν ἣν **παρελάβοσαν** | παρελάβοσαν («que **eles** receberam») | παρελάβετε («que **vocês** receberam»): 03, WH, Treg, NIV; παρέλαβον: RP; παρέλαβεν: Scrivener; παρελαβεν + ἀφʼ ἡμῶν em 03 | segue a base (3ª pessoa do plural), mas a alternativa é forte e muda o referente. A tradução evita comprometer o referente («a tradição que receberam de nós») e a nota expõe as três leituras |
| 3:6 | τοῦ κυρίου [ἡμῶν] Ἰησοῦ Χριστοῦ | com ἡμῶν (Treg/RP/NA28) | WH e NIV não têm ἡμῶν; 03 abrevia | segue a base |
| 3:8 | νυκτὸς καὶ ἡμέρας / νύκτα καὶ ἡμέραν | genitivos | acusativos: 02, RP, ST, KJTR, Scrivener | segue a base; «noite e dia» serve as duas |
| 3:12 | ἐν κυρίῳ Ἰησοῦ Χριστῷ / διὰ τοῦ κυρίου ἡμῶν | ἐν κυρίῳ | διὰ τοῦ κυρίου ἡμῶν: RP, ST, KJTR, Scrivener | segue a base: «no Senhor Jesus Cristo» |
| 3:13 | ἐγκακήσητε / ἐκκακήσητε | ἐγκακήσητε | ἐκκακήσητε: RP, ST, KJTR, Scrivener; 03 lê ἐνκακήσητε | ortográfica; segue a base |
| 3:14 | μὴ συναναμίγνυσθαι / καὶ μὴ συναναμίγνυσθε | infinitivo, sem καί | καὶ + imperativo: RP, ST, KJTR, Scrivener | segue a base |
| 3:16 | ἐν παντὶ **τρόπῳ** | τρόπῳ («de todas as maneiras») | 02 escreveu **τόπῳ** («em todo o lugar») na mão original e foi corrigido para τρόπῳ | segue a base; a correção de 02 é o achado manuscritológico mais interessante do capítulo e vai na nota |
| 3:18 | μετὰ πάντων ὑμῶν [ἀμήν] | sem ἀμήν | + ἀμήν: 02, RP, ST, KJTR, Scrivener; 01 e 03 não o têm | segue a base; não se marca com `[[ ]]` porque não é texto traduzido, é fecho litúrgico bizantino — registado na nota |

### 9.1 Achados manuscritológicos de 2 Tessalonicenses

Estes dados vêm da transcrição, não de um aparato; são o que o acervo CNTR
permite afirmar com o suporte à vista:

- **01 (Sinaiticus) 1:1** — o escriba original escreveu «ἐν θεῷ **καὶ** πατρὶ
  ἡμῶν»; uma mão posterior apagou o καί. A versão corrigida coincide com a base.
- **01 (Sinaiticus) 2:1** — o início do versículo está danificado (letra não
  identificada na transcrição) e a palavra ἐρωτῶμεν é restituída; o Sinaiticus
  não pode ser citado aqui como testemunha legível da primeira palavra.
- **01 (Sinaiticus) 2:4** — três camadas: a mão original omitiu «καὶ
  ὑπεραιρόμενος»; a camada editada tem ϗ ὑπεραμενος (com itacismo); o corretor
  **a** escreveu ϗ ὑπεραιρόμενος. O códice que hoje se lê coincide com a base —
  mas só depois de correção.
- **01 (Sinaiticus) 2:14** — corrigido de ὑμῶν para ἡμῶν no «evangelho
  <de quem>»; **02 e 03** leem efetivamente ἡμᾶς em vez de ὑμᾶς. A 1ª pessoa é
  uma leitura antiga e minoritária que a nota regista.
- **01 (Sinaiticus) 2:16** — a mão original omitiu «καί» e «ὁ ἀγαπήσας ἡμᾶς»;
  ambos foram acrescentados depois.
- **02 (Alexandrinus) 2:10** — a mão original tem uma lacuna ilegível; a
  sequência «οὐκ ἐδέξαντο εἰς τὸ σωθῆναι» é restituída.
- **02 (Alexandrinus) 3:16** — **τόπῳ → τρόπῳ**: a mão original escreveu «em
  todo o *lugar*» e um corretor escreveu «de toda a *maneira*». Uma só letra decide
  entre as duas leituras: o *ρ* de τρόπος, ausente de τόπος. É o achado mais
  económico do livro — uma letra entre «em todo o lugar» e «de todas as maneiras».
- **03 (Vaticanus) 2:8** — omite Ἰησοῦς: «ὃν ὁ κύριος ἀνελεῖ».
- **03 (Vaticanus) 3:4** — acrescenta «καὶ ἐποιήσατε»: «o que ordenamos **e
  fizestes** e fazeis e fareis».
- **03 (Vaticanus) 3:6** — lê «παρέλαβετε ἀφʼ ἡμῶν» (2ª pessoa + ἀπό).
- **P92** conserva apenas 1:4-5.11-12, tudo em lacuna com texto suprido; **P30**
  apenas 1:1-2; 2:1; 2:9-11. Nenhum dos dois pode decidir uma variante sozinho.
- **Nenhum manuscrito colacionado apoia φλογὶ πυρός em 1:8 exceto 03**, e no
  entanto é essa a leitura da base fixada. É o melhor exemplo do livro de que
  «seguir a base» não é «seguir a maioria dos manuscritos».

---

## 10. Decisões registadas para os cinco livros curtos e João 1 (2026-11-20)

Os cinco livros do piloto aprovado (Tito, Filemom, 2 João, 3 João, Judas)
foram colacionados com o mesmo acervo e a mesma revisão CNTR de
2 Tessalonicenses (`scripts/colar.py --livro N`; relatórios em
`docs/colacao/`). Em todos, **o texto segue a base fixada**; as Críticas
Textuais das notas foram geradas, em 2026-11-20, por um script de conversão não versionado, a partir do
aparato (edições) e dos relatórios (manuscritos). Quando a variante é apenas
bizantina (RP) e WH/Tregelles/NA28 apoiam a base, a nota regista-o; quando as
edições críticas se dividem, regista-se a divisão. Os dois casos de decisão
difícil são os abaixo. O registo completo é a nota de cada
versículo mais o relatório do livro; aqui ficam as decisões de consequência.

| Ref. | Unidade | Decisão |
|---|---|---|
| Jd 1:5 | *Ἰησοῦς* (NA28) / *κύριος* (WH, Tregelles) / *ὁ κύριος* (RP) | segue a base: «[[Jesus]] salvou um povo». Das testemunhas colacionadas, 03 e SR leem com a base; 01 e 04 leem *κύριος*; P72 lê *θεὸς Χριστός*. **Decisão do responsável (2026-11-20): seguir NA28** — a leitura mantém-se; a dificuldade fica registada na nota, não como pendência |
| Jd 1:22–23 | *ἐλεᾶτε* (WH, NA28) / *ἐλεεῖτε* (RP) / *ἐλέγχετε* (Tregelles), com três arranjos das cláusulas | segue a base; o arranjo RP desloca «em temor» para junto de «salvai» |
| Fm 1:6 | *τοῦ* (WH, NA28, RP) / omissão (Tregelles, 02, 04); *ἡμῖν* / *ὑμῖν* (01, TR) | segue a base: «o bem que há em nós» |
| 2 Jo 1:8 | *εἰργασάμεθα* «nós trabalhámos» / *εἰργάσασθε* «vocês trabalharam» (Tregelles, NIV; 02, SR) | segue a base; a pessoa dos três verbos fica registada na nota |
| 2 Jo 1:12 | *ὑμῶν* «a vossa alegria» (WH, Tregelles; 01) / *ἡμῶν* (NA28, RP) | segue a base com WH/Tregelles contra NA28 |
| Tt 2:13; Fm 1:5; 3 Jo 1:4–5; Jd 1:15–16, 18 | edições críticas divididas em pormenor (ordem, artigo, sinónimos) | segue a base em todos; pormenor na nota de cada versículo |

Leituras de manuscritos que nenhuma edição imprime, registadas nas notas a
partir dos relatórios (não mudam o texto): Jd 1:12 *ἀπάταις* «enganos» em 02
e 04 (assimilação provável a 2 Pedro 2:13); 3 Jo 1:8 *τῇ ἐκκλησίᾳ* em 01 e
02; Jd 1:14 «santos anjos» em 01 e P72; Jd 1:21 subjuntivo *τηρήσωμεν* em 03,
04 e P72; Fm 1:16 omissão de *ἀδελφόν* em 01; Fm 1:3 omissão de *ἡμῶν* em 01
(a base mantém «nosso Pai», ao contrário de 2Ts 1:2 — ver §9); Tt 1:9
leitura singular de 02. 3 João 1:14: a aparente falta da saudação final nas
testemunhas é numeração (v. 15), não texto.

João 1 (capítulo revisto na mesma data, com o mesmo método): as
notas citam o aparato e o relatório `docs/colacao/João.json`. Decisões de
consequência: 1:18 *μονογενὴς θεός* contra *ὁ μονογενὴς υἱός* (RP) — a
redação anterior seguia RP; 1:34 *ἐκλεκτός* (Holmes, WHmarg) contra *υἱός*
(WH, Tregelles, NA28, RP): decisão difícil, assinalada em `review`.

## 11. Ligação à infraestrutura (estado de 2026-11-20)

| Onde | O quê |
|---|---|
| [`bee/manuscritos.py`](../bee/manuscritos.py) | analisador MES + colação: camadas de correção, lacunas, nomina sacra por família flexional, abreviaturas por barra |
| [`scripts/colar.py`](../scripts/colar.py) | CLI: `--livro N` gera `docs/colacao/<livro>.json` e `.md`; `--verso 2:13` detalha uma unidade |
| [`scripts/verificar_notas_colacao.py`](../scripts/verificar_notas_colacao.py) | confere as Críticas Textuais das notas contra a colação do livro; toda a variante do aparato tem de ter CT no capítulo |
| [`bee/inspetor.py`](../bee/inspetor.py) | guarda da voz: arcaísmos, marcas de Almeida, rótulos antigos, níveis de certeza impressos, grego fora de itálico |
| [`modelos/estilo_bee.json`](../modelos/estilo_bee.json) | memória de estilo: regras, glossário, vetos e decisões lexicais |
| [`tests/test_manuscritos.py`](../tests/test_manuscritos.py) | testes do analisador MES |
| [`tests/test_critica_textual.py`](../tests/test_critica_textual.py) | o protocolo contra os dados: nenhuma testemunha citada sem colação naquele versículo, decisões registadas, proveniência e estados de revisão declarados |
| `docs/colacao/` | relatórios de colação versionados (obra nossa; as transcrições CNTR ficam fora do Git) |

Fluxo por livro: `scripts/colar.py --livro N` → decisões em `docs/CRITICA_TEXTUAL.md`
→ tradução e notas → `scripts/verificar_estilo.py` → `scripts/verificar_notas_colacao.py`
→ `scripts/verificar_dados.py` → `gerar_bee.py --compilar` → revisão editorial → revisão especializada.

Os scripts de conversão usados em 2026-11-20 para passar as notas a prosa não estão no
repositório; os JSON são a fonte. Ver [`EDICAO_NOVA.md`](EDICAO_NOVA.md), «Limitações conhecidas».

## 12. O que este protocolo não é

Não é uma afirmação de que o texto está perdido, nem de que a igreja se enganou
durante séculos, nem de que cada versículo precisa de uma dúvida. É o contrário:
é o procedimento que permite dizer, com evidência verificável e revisão fixada,
**o que as cópias leem, por que razão se adotou o que se adotou, e onde ainda não
se sabe**. Uma confissão de inerrância que precise de ignorar as variantes é
frágil. Uma confissão de inerrância que as registe e as enfrente não é.
