# Hebreus — estudo prévio

**Estado: rascunho de estudo, 20/11/2026. Não aprovado.** Nada neste documento foi aprovado pelo responsável. A tradução da secção 7 é uma amostra para testar a voz, não o texto de Hebreus da edição. As sugestões de variantes são propostas para decisão do responsável (`docs/RESUMO_ESTILO.md` §9.4).

**Base e acervo.** Texto traduzido: SBLGNT `d7f35ad` (base fixada do projeto). Comparação: Scrivener TR 1894. Colação: `docs/colacao/Hebreus.json` e `.md` (303 versículos, 115 com aparato), gerada por `python3 scripts/colar.py --livro 650`. Transcrições CNTR (classe 1, livro 58) lidas diretamente para as passagens disputadas, com cópia local em `.bee-cache/cntr/` (não redistribuída).

**Limite declarado.** Não consultei comentários, gramáticas nem edições críticas além das já colacionadas. Por isso este estudo não cita literatura secundária. Referências à interpretação corrente ficam marcadas como pendentes (protocolo §3, nível 4). A única fonte externa usada é a datação de P46 (secção 2.2).

---

## 1. Resumo para decisão

| Grupo | Passagens | O que se pede |
|---|---|---|
| **A. Decisão de sentido** (muda a tradução) | 9:11; 9:14; 8:8; 10:34; 11:11 | O responsável escolhe a leitura. Sugestão de método na secção 3. |
| **B. Adição ou omissão substantiva** | 2:7; 3:6; 7:21; 11:37; 13:21 | Sugere-se manter a base e registar a variante na nota. Há alternativa com colchetes simples, se o responsável preferir. |
| **C. Pequenas diferenças de palavra ou construção** | 1:8; 7:14; 9:1; 9:3; 9:10; 12:3; 12:18; 12:27; 6:2 | Base mantida. Quase sem efeito na tradução. Algumas merecem nota. |
| **D. Só ortografia ou ordem** | 1:2; 1:3; 2:9 (χωρίς); 3:10 (ἐκείνῃ); 9:13; 11:4 (λαλεῖται) | Sem decisão. Registo em bloco, se o protocolo o pedir. |

Três pontos que pedem atenção antes de qualquer decisão:

1. **P46 é um dos testemunhos mais antigos de Hebreus** (datação em 2.2). Quando P46 e os códices do século IV ou V divergem, a leitura de P46 não se pode descartar só por ser minoritária.
2. **01 e 02 não formam um bloco.** Em 9:11 leem «μελλόντων» (contra P46 e 03), e em 8:8 leem «αὐτούς» (contra P46 e 03). A oposição «alexandrino contra ocidental» não explica estes casos.
3. **O aparato do SBLGNT não cita 01 e 02 em todos os casos em que a colação os regista.** Em 11:4, 01 e 02 leem τῷ θεῷ, e o aparato só menciona Treg. A nota deve usar a colação, não só o aparato.

---

## 2. Manuscritologia

### 2.1 Testemunhas colacionadas para Hebreus

Os números são versículos com dados na colação (de 303). «Ausente» quer dizer lacuna ou falta de cobertura do manuscrito, não omissão de texto.

| Sigla | Suporte | Versículos com dados | Estado e observações (das transcrições e da colação) |
|---|---|---|---|
| **P46** | papiro | 300 | Lacunoso em poucos pontos. Corpo paulino. Tem lacuna em 9:14 depois de «ἄμωμον τῷ θεῷ»; a colação restaura «ζῶντι» entre chavetas. Em 12:18 lê σκότει (contra o ζόφῳ da base). |
| **01** (א) | pergaminho | 303 | Carta inteira. Corrigido em alguns pontos, por exemplo 2:7 (a forma ἐστεφάνωσας). Uma mão corrigida conta como duas testemunhas de duas épocas (protocolo §5, passo 3). |
| **02** (A) | pergaminho | 303 | Carta inteira. Acrescenta καὶ ἀληθινῷ em 9:14 e ἔργῳ καὶ λόγῳ em 13:21. |
| **03** (B) | pergaminho | 156 | Dados até 9:14. Sem 9:15 em diante na colação. Em 2:7 e 3:6 omite os acréscimos de 01, 02 e 04. |
| **04** (C) | pergaminho (palimpsesto) | 187 | Lacunoso. Lê ἐκείνῃ em 3:10 (contra ταύτῃ da base). |
| **P13** | papiro | 114 | Em partes. Lê αὐτούς em 12:3 (contra ἑαυτούς da base). |
| **P116** | papiro | 7 | Fragmentos. |
| **P130** | papiro | 9 | Fragmentos. Lê γενομένων em 9:11 (confirmado na transcrição). |
| **P114** | papiro | 6 | Fragmentos. Lê σου em 1:8. |
| **P17** | papiro | 8 | Fragmentos. |
| **P89** | papiro | 6 | Fragmentos. |
| **0228** | uncial | 6 | Fragmentos. |
| **0252** | uncial | 5 | Fragmentos. Lê διδαχήν em 6:2. |
| **P126** | papiro | 4 | Fragmentos. |

Edições colacionadas: WH, Treg, NA28 (todas no aparato), RP, KJTR, ST, SR, Scrivener, Holmes e WHmarg. **As edições não são testemunhos manuscritos** (protocolo §3): só servem para mostrar o que as escolhas editoriais fizeram.

### 2.2 Datação

- **P46 (Chester Beatty II; Ann Arbor, Inv. 6238): c. 175–225**, segundo a paleografia. Fontes consultadas: [Papyrus 46, Wikiwand](https://www.wikiwand.com/en/Papyrus_46), que cita a datação de Orsini e Clarysse para o início do século III; e [Manuscript P46, CSNTM](https://manuscripts.csntm.org/manuscript/Group/GA_P46?OSIS=1Cor.13.1), que indica «late second century or early third century (c. 200)». Os dois concordam em torno de 200.
- **As datas dos restantes manuscritos não foram verificadas nesta sessão.** Não as escrevo aqui. Antes de publicar, confirmar cada uma numa fonte consultada.

### 2.3 O que a manuscritologia permite dizer

- P46 tem o texto de Hebreus com cerca de dois séculos de antiguidade. Quando lê como a base, a base tem apoio de antiguidade. Quando lê diferente, a variante tem apoio de antiguidade.
- Em 9:11 e 8:8, P46 e 03 leem juntos (γενομένων; αὐτοῖς). Em 3:6 e 7:21, ambos omitem os acréscimos. É um padrão a registar.
- Os fragmentos (P114, P116, P126, P130, P17, P89, 0228, 0252) só pesam nas passagens que cobrem. Não se fala de «os papiros» em geral.

---

## 3. Crítica textual: variantes com detalhe

Para cada variante: leitura da base; leituras alternativas com testemunhos; o que a alternativa mudaria no português; sugestão. Os sete passos do protocolo (§5) estão condensados em cada entrada: evidência externa, evidência transcricional, evidência intrínseca, sugestão.

### Grupo A — decisão de sentido

#### 9:11 — «γενομένων» (base) ou «μελλόντων»

- **Base** (WH, NA28, SBLGNT): τῶν *γενομένων* ἀγαθῶν, «dos bens que já vieram».
- **Alternativa** (Treg, RP): τῶν *μελλόντων* ἀγαθῶν, «dos bens que hão de vir».
- **Externa:** γενομένων em P46 (grafado γεναμενων), P130 e 03. μελλόντων em 01, 02 e nas edições KJTR, RP, ST, Scrivener e Treg.
- **Transcricional:** a alternativa μελλόντων é o que um copista poderia introduzir por harmonização com 10:1, onde o texto diz τῶν μελλόντων ἀγαθῶν. Este é um argumento a favor de γενομένων como *lectio difficilior*.
- **Intrínseca:** 10:1 usa a expressão «os bens futuros». Isso favorece μελλόντων se o contexto de 9:11 se lê como promessa. Mas em 9:11 o argumento fala de Cristo já entrado no santuário, e γενομένων encaixa nessa leitura: os bens já chegaram com a sua entrada.
- **Efeito no português:** «dos bens que já chegaram» contra «dos bens que hão de vir». A diferença é de tempo: realizado ou prometido.
- **Sugestão: manter γενομένων** (base), com nota que menciona 10:1. O responsável decide.

#### 9:14 — «ἡμῶν» (base) ou «ὑμῶν»

- **Base** (WH, NA28): τὴν συνείδησιν **ἡμῶν**, «a nossa consciência».
- **Alternativa** (Treg, RP, KJTR, ST, SR, Scrivener): τὴν συνείδησιν **ὑμῶν**, «a vossa consciência».
- **Externa:** ἡμῶν em 02. ὑμῶν em 01. P46 tem lacuna depois de «τῷ θεῷ». 03 tem lacuna nesta parte.
- **Material:** P46 não lê o trecho seguinte a «ἄμωμον τῷ θεῷ» (lacuna do papiro; a colação restaura «ζῶντι»). Não diz nada sobre ἡμῶν/ὑμῶν.
- **Intrínseca:** o autor usa a primeira pessoa do plural em todo o capítulo 9 e em 10:19–25 (ἡμῶν, ἔχοντες, προσερχώμεθα). A leitura ἡμῶν é a que mantém o autor incluído na purificação. ὑμῶν dirige a afirmação aos destinatários, o que é também possível.
- **Efeito no português:** «a nossa consciência» (autor e leitores) contra «a vossa consciência». Muda quem está incluído.
- **Sugestão: manter ἡμῶν** (base). O responsável confirma. A diferença é clara e cabe numa nota curta.

#### 8:8 — «αὐτούς» (base) ou «αὐτοῖς» (com μεμφόμενος)

- **Base** (WH, NA28): μεμφόμενος γὰρ **αὐτούς** λέγει, «pois, censurando-os, diz».
- **Alternativa** (Treg, RP, KJTR, ST, Scrivener): μεμφόμενος γὰρ **αὐτοῖς**, «pois, censurando-os».
- **Externa:** αὐτούς em 01 e 02. αὐτοῖς em P46 e 03.
- **Gramatical:** o verbo μέμφομαι rege, em regra, o dativo da pessoa censurada. Isso favorece αὐτοῖς como forma esperada, e a variante pode ter nascido de correção gramatical.
- **Intrínseca:** o contexto (8:8–12, citação de Jeremias) fala de um povo que não permaneceu na aliança. Ambos os casos cabem.
- **Efeito no português:** nenhum, se a tradução for «censurando-os». Ambos os casos se traduzem assim. A diferença fica só na nota.
- **Sugestão: manter αὐτούς** (base) e traduzir «censurando-os», o que serve para as duas leituras. Registar a divisão dos testemunhos antigos.

#### 10:34 — «δεσμίοις» (base) ou «δεσμοῖς μου»

- **Base** (WH, Treg, NA28): τοῖς **δεσμίοις** συνεπαθήσατε, «vós vos solidarizastes com os presos».
- **Alternativa** (RP, KJTR, ST, Scrivener): τοῖς **δεσμοῖς μου** συνεπαθήσατε, «vós vos solidarizastes com as minhas cadeias».
- **Externa:** δεσμίοις em 02. μου em 01. P46 lê δεσμοισ, que é δεσμοῖς (sem μου). P13 lê δεσμίοις, como a base.
- **Intrínseca:** o autor fala de solidariedade com os presos, não com as suas próprias cadeias. μου cria uma primeira pessoa que a frase não pede, e por isso pode ser uma harmonização.
- **Efeito no português:** «com os presos» (base) contra «com as minhas cadeias». A segunda leitura faz do autor um prisioneiro. Isso é uma informação biográfica que o texto só dá se se ler μου.
- **Sugestão: manter δεσμίοις** (base). Registar que 01 lê δεσμοῖς μου, e que P46 lê δεσμοῖς.

#### 11:11 — «αὐτῇ Σάρρᾳ» (base) ou «αὐτὴ Σάρρα στεῖρα»

- **Base** (SBLGNT): πίστει καὶ **αὐτῇ Σάρρᾳ**, «pela fé, também a própria Sara».
- **Alternativa** (NA28): **αὐτὴ Σάρρα στεῖρα**, «também ela, Sara, estéril». A mesma leitura aparece em P46 (αυτη σαρρα στειρα).
- **Externa:** στεῖρα só em P46 e NA28, entre os testemunhos colacionados. 01, 02 e P13 não a têm. As edições WH, Treg e RP leem αὐτὴ Σάρρα sem στεῖρα.
- **Transcricional:** στεῖρα pode ser uma glosa explicativa, que um copista acrescenta para deixar claro o obstáculo. Se for assim, P46 é o único testemunho antigo que a tem, e a omissão nos outros é o caminho mais simples. A hipótese inversa (corte por ser redundante) não tem apoio nos testemunhos colacionados.
- **Intrínseca:** a própria frase já diz que Sara recebeu força para conceber «fora de tempo da idade» (παρὰ καιρὸν ἡλικίας). A esterilidade fica implícita.
- **Efeito no português:** «a própria Sara» contra «Sara, estéril». O português pode pôr «estéril» sem ser tradução fiel, por isso é uma escolha de clareza.
- **Sugestão: manter a base** («a própria Sara»). Na nota, mencionar P46 e NA28 e a ideia de que a frase já a implica.

### Grupo B — adição ou omissão substantiva

#### 2:7 — acréscimo «καὶ κατέστησας αὐτὸν ἐπὶ τὰ ἔργα τῶν χειρῶν σου»

- **Base** (SBLGNT, NA28, RP, SR): sem o acréscimo. «Tu o fizeste um pouco inferior aos anjos, de glória e honra o coroaste.»
- **Alternativa** (WH, Treg, KJTR, ST, Scrivener): com o acréscimo. Com o acréscimo em 01, 02 e 04.
- **Externa:** sem acréscimo em P46 e 03. Com acréscimo em 01, 02 e 04.
- **Transcricional e intrínseca:** o acréscimo vem do Salmo 8:7 LXX, que o autor cita aqui. Um copista que conhecesse o salmo podia completá-lo. Por outro lado, a citação é do próprio autor e pode não a ter feito inteira. A decisão é difícil porque os testemunhos se dividem por épocas.
- **Efeito no português:** o acréscimo põe o homem a governar «as obras das tuas mãos», o que ecoa o domínio de Gn 1:26–28 (eco, não citação). Sem ele, a frase fica na coroação.
- **Sugestão:** a base não tem colchetes, e o projeto segue a base (protocolo §5, passo 6). Registar na nota e deixar ao responsável a opção de colchetes simples, porque aqui há testemunhos antigos dos dois lados.

#### 3:6 — acréscimo «μέχρι τέλους βεβαίαν»; «ἐὰν» ou «ἐάνπερ»; «ὃς» ou «οὗ»

- **Base** (SBLGNT): ὃς οἶκός ἐσμεν ἡμεῖς, ἐὰν … κατάσχωμεν τῆς ἐλπίδος. Sem acréscimo.
- **Alternativa** (WH, Treg, RP, KJTR, ST): «… τὸ καύχημα τῆς ἐλπίδος μέχρι τέλους βεβαίαν κατάσχωμεν», «… até ao fim firme».
- **Externa:** sem acréscimo em P46, P13 e 03. Com acréscimo em 01, 02 e 04.
- **Relativo:** ὃς (base e P46). οὗ em WH, Treg, NA28, RP e nos outros. A diferença é de forma: o relativo concorda com «casa» ou com «Cristo».
- **Intrínseca:** o acréscimo repete o tema de 3:14 e 6:11. É o tipo de frase que um copista tende a assimilar.
- **Efeito no português:** o acréscimo põe «até ao fim» a firmeza da esperança, o que reforça a advertência de 3:12–14.
- **Sugestão: manter a base.** Registar a divisão, em particular em relação a P13 e 03.

#### 7:21 — acréscimo «κατὰ τὴν τάξιν Μελχισεδέκ»

- **Base** (SBLGNT, WH, NA28): sem o acréscimo. «… tu és sacerdote para sempre».
- **Alternativa** (KJTR, RP, ST, Scrivener): com «segundo a ordem de Melquisedeque».
- **Externa:** sem o acréscimo em P46, 01, 03 e 04. Com ele em 02.
- **Transcricional:** o acréscimo vem de 7:17. Um copista podia completar a citação do Salmo 110:4 com o que lhe ficou na memória. A base tem apoio em quatro dos cinco testemunhos.
- **Efeito no português:** sem o acréscimo, a citação fica mais curta, e a ligação a Melquisedeque depende do contexto. Com o acréscimo, a citação é explícita.
- **Sugestão: manter a base**, sem colchetes. Registar a harmonização com 7:17 na nota.

#### 11:37 — «ἐπειράσθησαν» antes ou depois de «ἐπρίσθησαν»

- **Base** (Treg, NA28): ἐλιθάσθησαν, ἐπρίσθησαν, ἐν φόνῳ μαχαίρης ἀπέθανον. Sem «ἐπειράσθησαν».
- **Alternativa** (WH, KJTR, RP, ST, Scrivener): acrescenta «ἐπειράσθησαν», antes ou depois de «ἐπρίσθησαν».
- **Externa:** sem o acréscimo em P46. Com ele em 01 (antes de ἐπρίσθησαν), 02 e P13 (depois).
- **Transcricional:** a variação de posição entre 01, 02 e P13 é o sinal de um acréscimo que entrou no texto em lugares diferentes. Uma leitura estável não se movimentaria assim. É um argumento para uma glosa marginal que se incorporou por copistas diferentes.
- **Efeito no português:** «foram tentados» acrescentaria um quinto modo de morte ou de sofrimento à lista. A base não o tem, e a lista fica com três (apedrejados, serrados, mortos à espada).
- **Sugestão: manter a base** (sem «ἐπειράσθησαν»). Registar a variação de posição como sinal de glosa.

#### 13:21 — acréscimo «ἔργῳ» e «ἔργῳ καὶ λόγῳ»

- **Base** (SBLGNT, WH, NA28): ἐν παντὶ ἀγαθῷ, «em toda a obra boa». Sem «ἔργῳ».
- **Alternativa** (Treg, RP): ἐν παντὶ **ἔργῳ** ἀγαθῷ.
- **Externa:** sem «ἔργῳ» em P46 e 01 (03 e P13 não têm dados neste versículo). Com «ἔργῳ» em 04. Com «ἔργῳ καὶ λόγῳ» em 02.
- **Intrínseca:** «ἔργῳ καὶ λόγῳ ἀγαθῷ» aparece em 2 Tessalonicenses 2:17. O acréscimo em Hebreus é provavelmente uma harmonização com essa frase paulina.
- **Efeito no português:** o acréscimo põe «obra» onde a base tem «bem» ou «bom» de forma mais geral.
- **Sugestão: manter a base.** Registar o paralelo de 2 Tessalonicenses 2:17 na nota, como harmonização provável.

### Grupo C — diferenças pequenas

#### 1:8 — «σου» ou «αὐτοῦ»

- **Base** (SBLGNT, Treg, NA28, RP): «ῥάβδος τῆς βασιλείας **σου**».
- **Alternativa** (WH): «… αὐτοῦ».
- **Externa:** σου em 02 e P114. αὐτοῦ em P46, 01 e 03.
- **Intrínseca:** a frase é uma citação do Salmo 44:7 LXX (45:7 hebraico), que tem «σου» no final. A citação segue a LXX. Um copista podia mudar a segunda pessoa para a terceira, como a frase anterior já faz com «ὁ θεός».
- **Efeito no português:** «do teu reino» (dirigido ao Filho, com «ó Deus» no vocativo) contra «do seu reino». A segunda leitura é gramatical mas pesa menos.
- **Marcação da base:** o SBLGNT assinala a cláusula «καὶ ἡ ῥάβδος τῆς εὐθύτητος» entre ⸂ ⸃ (colchetes do aparato). Os testemunhos que a têm (P46, 01, 02, 03, P114) sustentam a sua presença no texto. A BEE não a põe entre colchetes simples, e a nota regista a marcação da base.
- **Sugestão: manter σου** (base) pela citação do salmo.

#### 7:14 — «περὶ ἱερέων οὐδὲν» ou «οὐδὲν περὶ ἱερωσύνης»

- **Base** (SBLGNT, WH, Treg, NA28): «… sobre sacerdotes nada disse Moisés». περὶ ἱερέων.
- **Alternativa** (RP, KJTR, ST, Scrivener): «… nada disse Moisés sobre o sacerdócio». περὶ ἱερωσύνης.
- **Externa:** περὶ ἱερέων em 01, 02, 03, 04 e P46. ἱερωσύνης só nas edições RP, KJTR, ST e Scrivener, entre os testemunhos colacionados.
- **Efeito no português:** «sobre sacerdotes» (pessoas) contra «sobre o sacerdócio» (instituição). Muda o tipo de afirmação.
- **Sugestão: manter a base.** Apoio amplo e antigo.

#### 9:1 — «καὶ» antes de «ἡ πρώτη»

- **Base** (SBLGNT, Holmes): «Εἶχε μὲν οὖν ἡ πρώτη». Sem καί.
- **Alternativa** (WH, Treg, NA28, RP): com καί.
- **Externa:** sem καί em P46 e 03. Com καί em 01 e 02.
- **Efeito no português:** uma conjunção a mais («e também»). Pequeno.
- **Sugestão: manter a base.** Tradução: «Ora, a primeira aliança tinha…».

#### 9:3 — «ἅγια ἁγίων» ou «τὰ ἅγια τῶν ἁγίων»

- **Base** (SBLGNT, WH, NA28, RP): «τὰ» ausente. 01 e 02 leem ἅγια ἁγίων.
- **Alternativa** (Treg; 03): «τὰ ἅγια τῶν ἁγίων».
- **Efeito no português:** nenhum relevante. «o Santo dos Santos» serve para ambos.
- **Sugestão: manter a base.**

#### 9:10 — «καί» antes de «δικαιώματα»

- **Base** (SBLGNT, WH, NA28): «… δικαιώματα σαρκὸς».
- **Alternativa** (Treg, RP): «καὶ δικαιώματα»; RP lê também «καὶ δικαιώμασιν».
- **Externa:** sem καί em P46, 01 e 02. Com καί em 03 e P130.
- **Sugestão: manter a base.** Efeito mínimo.

#### 12:3 — «ἑαυτούς», «αὐτούς» ou «ἑαυτόν»; imperativo ou infinitivo

- **Base** (SBLGNT, WH): ἀναλογίσασθε … εἰς **ἑαυτούς** ἀντιλογίαν. Imperativo.
- **Alternativa 1:** P46 e P13 leem «εἰς αὐτούς» (não reflexivo).
- **Alternativa 2:** NA28 e Treg leem «εἰς ἑαυτόν»; RP lê «εἰς αὐτόν».
- **Alternativa 3:** P46, P13 e 02 leem ἀναλογίσασθαι (infinitivo).
- **Efeito no português:** «a hostilidade dos pecadores contra si mesmos» (reflexivo) contra «contra eles» (contra os crentes). O reflexivo deixa a contradição com os pecadores; o não reflexivo a deixa com a comunidade. A tradução «contra si mesmos» segue a base.
- **Sugestão: manter a base.** Registar que P46 e P13 leem «contra eles», porque é uma leitura séria e não só ortográfica.

#### 12:18 — «ζόφῳ» ou «σκότῳ»; acréscimo «ὄρει»

- **Base** (SBLGNT, WH, NA28): ψηλαφωμένῳ … ζόφῳ. Sem «ὄρει».
- **Alternativa** (RP, KJTR, ST, Scrivener): acréscimo «ὄρει» (monte) e «σκότῳ».
- **Externa:** ζόφῳ em 01, 02 e 04. σκότει em P46.
- **Efeito no português:** nenhum relevante. «escuridão» ou «trevas» servem.
- **Sugestão: manter a base.** Registar que P46 lê σκότει, o que faz concordar a sua leitura com RP.

#### 12:27 — «τὴν τῶν σαλευομένων» ou «τῶν σαλευομένων»

- **Base** (SBLGNT, Holmes, WHmarg): «… τῶν σαλευομένων μετάθεσιν». Sem artigo.
- **Alternativa** (WH, Treg, NA28, RP): «τὴν τῶν σαλευομένων» (ou «τῶν σαλευομένων τὴν» em RP).
- **Externa:** sem artigo em P46. Com artigo em 01, 02 e 04.
- **Efeito no português:** nenhum. «a remoção das coisas abaladas» serve para as duas.
- **Sugestão: manter a base.** Registar em bloco se o protocolo o pedir.

#### 6:2 — «διδαχὴν» ou «διδαχῆς»; «τε»

- **Base** (SBLGNT, WH): βαπτισμῶν **διδαχήν**, «ensinamento sobre batismos» (acusativo, em aposição a θεμέλιον).
- **Alternativa** (Treg, NA28, RP): βαπτισμῶν **διδαχῆς**, «doutrina dos batismos» (genitivo).
- **Externa:** acusativo em P46, 03 e 0252. Genitivo em 01, 02 e 04.
- **Efeito no português:** a construção muda a relação entre «fundamento» e «ensinamento». Na tradução, «o ensinamento sobre batismos» serve para os dois casos.
- **Sugestão: manter a base**, sem efeito na tradução.

### Grupo D — ortografia, ordem e pequenas palavras

- **1:2:** ἐποίησεν τοὺς αἰῶνας (base) ou τοὺς αἰῶνας ἐποίησεν (RP). Só ordem.
- **1:3:** καθαρισμὸν τῶν ἁμαρτιῶν ποιησάμενος (base) ou ποιησάμενος τῶν ἁμαρτιῶν ἡμῶν (RP). Tradução igual: «tendo feito a purificação dos pecados».
- **2:9:** χάριτι θεοῦ (base e todos os colacionados) ou χωρὶς θεοῦ (só Holmes). Manter χάριτι. A variante só aparece numa edição, sem testemunho manuscrito.
- **3:10:** ταύτῃ (base; P46, P13, 01, 02, 03) ou ἐκείνῃ (04 e RP). Manter ταύτῃ. A leitura ἐκείνῃ de 04 é isolada entre os manuscritos colacionados.
- **9:13:** τράγων καὶ ταύρων (base) ou ταύρων καὶ τράγων (RP). Ordem apenas.
- **11:4:** λαλεῖ (base; WH, Treg, NA28) ou λαλεῖται (RP). A forma passiva faria do Abel «ainda é falado». Manter a base. Registar que 01 e 02 leem τῷ θεῷ, o que o aparato do SBLGNT não mostra, mas a colação regista.

---

## 4. Exegese

### 4.1 Género e forma

Hebreus não tem nome de autor, nem saudação de carta no início. A forma é de homilia ou de exortação escrita. O próprio texto a chama de «palavra de exortação» (13:22: λόγος τῆς παρακλήσεως). No fim (13:22–25) tem traços de carta: pedido de oração, notícia sobre Timóteo, saudação. Por isso é lido como carta-homilia.

### 4.2 Estrutura do argumento

| Secção | Passagem | Conteúdo |
|---|---|---|
| Prólogo | 1:1–4 | Deus falou pelo Filho. O Filho é superior aos profetas e aos anjos. |
| Filho e anjos | 1:5–2:4 | Sete citações do AT provam a superioridade do Filho. Primeira advertência (2:1–4). |
| Homem e Filho | 2:5–18 | Salmo 8 aplicado a Jesus, que se fez homem e sofreu. Sumo sacerdote misericordioso. |
| Moisés e Jesus | 3:1–6 | Jesus é fiel como filho sobre a casa, e Moisés como servo. |
| Repouso | 3:7–4:13 | Salmo 95 (LXX 94): o povo não entrou no repouso por incredulidade. «Hoje.» |
| Sumo sacerdote | 4:14–5:10 | Jesus, sumo sacerdote que simpatiza com as fraquezas. Ordem de Melquisedeque. |
| Advertência | 5:11–6:20 | Lerdeza, advertência (6:4–8), esperança firme, juramento a Abraão. |
| Melquisedeque | 7 | O sacerdócio de Melquisedeque é superior ao de Levi. Salmo 110:4. |
| Nova aliança | 8 | Jeremias 31 (LXX 38) citado inteiro. A antiga aliança envelheceu. |
| Santuário | 9 | O tabernáculo antigo; a entrada única de Cristo com o seu próprio sangue (9:11–14). |
| Sacrifício único | 10:1–18 | Salmo 40 (LXX 39): «Um corpo me preparaste». Sacrifício feito de uma vez. |
| Exortação | 10:19–39 | Aproximar-se com confiança. Advertência (10:26–31). Lembrança (10:32–34). |
| Fé | 11 | Definição (11:1). Lista de testemunhas. |
| Corrida e disciplina | 12:1–17 | Correr com perseverança. A disciplina do Pai. Esaú. |
| Sinai e Sião | 12:18–29 | Duas montanhas. «Nosso Deus é fogo consumidor» (12:29). |
| Exortações finais | 13 | Amor fraterno, hospitalidade, respeito pelos líderes, bênção, saudações. |

### 4.3 Passagens centrais

- **1:1–4.** Prólogo de um só período. O verbo principal é ἐλάλησεν (1:2); depois vêm os títulos do Filho, e o período fecha com ἐκάθισεν (1:3). A ordem faz do Filho o centro: herdeiro, criador, resplendor, sustentador, purificador, assento. Cada oração acrescenta um título, e o peso está no fim.
- **1:5–13.** A cadeia de citações atribui as palavras a Deus e à Escritura (p. ex., «Υἱός μου εἶ σύ», 1:5). São lidas em conjunto, e a leitura é cumulativa: cada citação acrescenta um traço do Filho.
- **2:9.** «Pela graça de Deus, provou a morte por todos» (ὅπως χάριτι θεοῦ ὑπὲρ παντὸς γεύσηται θανάτου). A base não tem variante séria aqui; a alternativa χωρὶς («sem Deus») só aparece em Holmes e é descartada.
- **3:7–4:11.** O «hoje» (σήμερον) do Salmo 95 é o eixo. O repouso (κατάπαυσις) não é só a terra prometida, é um repouso que continua. A palavra σαββατισμός (4:9) só aparece aqui no NT, e a tradução deve dizer «repouso sabático».
- **5:11–6:12.** A advertência sobre a lerdeza (νωθροί, 6:12). A passagem de 6:4–8 é das mais debatidas do NT. Ver a secção 5.
- **7.** Melquisedeque é tipo, não ancestral. O argumento depende do silêncio da Escritura sobre a sua genealogia (7:3). A tradução deve manter a ordem «sem pai, sem mãe, sem genealogia».
- **9:11–14.** O sumo sacerdote entra no santuário com o próprio sangue, e isso é mais eficaz do que o sangue de animais (9:13–14). A expressão «espírito eterno» (πνεύματος αἰωνίου) é ambígua. A tradição lê o Espírito Santo, mas o texto grego sem artigo não obriga a essa leitura.
- **11:1.** «A fé é a garantia (ὑπόστασις) das coisas esperadas e a prova (ἔλεγχος) das coisas que não se veem.» Esta é a definição mais citada do livro. Há duas palavras difíceis: ὑπόστασις (realidade, base, garantia) e ἔλεγχος (prova, convicção). A tradução deve escolher uma palavra para cada uma e manter-se nela no resto do capítulo.
- **12:18–29.** A contraposição entre o Sinai (fogo, trevas, tempestade) e o Sião (cidade do Deus vivo). O texto usa uma imagem de tremor para falar da permanência do que não treme (τὰ μὴ σαλευόμενα, 12:27).
- **13:21.** A bênção final, com a oração «faça em nós o que lhe agrada».

### 4.4 Citações do Antigo Testamento

Quase todas as citações seguem a LXX. A lista é do próprio texto; a numeração é a da LXX, e precisa de confirmação contra a LXX antes de publicação.

| Passagem | Citação |
|---|---|
| 1:5 | Sl 2:7; 2 Sm 7:14 |
| 1:6 | Dt 32:43 (LXX) |
| 1:7 | Sl 103:4 (LXX) |
| 1:8–9 | Sl 44:7–8 (LXX) |
| 1:10–12 | Sl 101:26–28 (LXX) |
| 1:13 | Sl 109:1 (LXX) |
| 2:6–8 | Sl 8:5–7 (LXX) |
| 3:7–11; 4:3, 5, 7 | Sl 94:7–11 (LXX) |
| 5:5 | Sl 2:7 |
| 5:6; 7:17, 21 | Sl 109:4 (LXX) |
| 8:8–12 | Jr 38:31–34 (LXX) |
| 10:5–7 | Sl 39:7–9 (LXX) |
| 10:30 | Dt 32:35–36 |
| 12:5–6 | Pr 3:11–12 |
| 12:26 | Ag 2:6 |
| 13:5 | Dt 31:6; Js 1:5 |

---

## 5. Hermenêutica

### 5.1 Regras do método

1. **A unidade é o argumento, não o versículo.** O autor usa conectores longos (γάρ, διό, ὥστε, εἰ γάρ). A tradução deve preservá-los. Frases curtas que quebram o argumento devem ser evitadas.
2. **O texto é ocasional.** A carta responde a uma situação concreta: cansaço, possível recuo, pressão da comunidade. A leitura não deve fazer do texto um tratado sistemático.
3. **A tipologia é do autor, não do leitor.** O tabernáculo, Melquisedeque e a aliança são tipos que o autor lê no Cristo. A nota deve dizer que é leitura do autor, não necessariamente a única leitura possível do AT.
4. **Não converter interpretação em tradução.** As passagens de advertência (6:4–8; 10:26–31) têm leituras debatidas. A tradução fica no texto. As leituras entram na nota, sem se escolher uma.
5. **Não harmonizar com outros livros.** Hebreus não se lê para confirmar Romanos ou Gálatas. A ligação com Paulo é um problema de atribuição, e o livro não se pronuncia sobre ela.

### 5.2 Destinatários e data

- **Destinatários:** comunidade de origem judaica ou com forte formação no AT, de lugar não identificado. A expressão «os da Itália» (13:24) pode significar «os que vêm de Itália» (ausentes) ou «os que estão na Itália». A ambiguidade fica registada.
- **Data:** não determinada. O texto fala do culto do tabernáculo em tempo presente (9:8: ἔτι στάσιν ἔχουσης τῆς πρώτης σκηνῆς, «enquanto a primeira tenda ainda tem o seu lugar»). Parte dos leitores lê isto como prova de que o templo ainda funcionava. Essa leitura não está verificada aqui, e não se escreve na nota.
- **Timóteo** (13:23): «nosso irmão Timóteo foi libertado». A notícia pode indicar prisão do próprio Timóteo ou de outro, e o texto não diz.

### 5.3 Ligação entre Antigo e Novo Testamento

O autor lê o AT como palavra presente (Sl 95, «hoje»). A tradução deve manter o «hoje» e as citações em discurso direto, quando o texto assim o faz. A nota identifica a citação, mas não a explica em excesso.

---

## 6. Teologia (leitura do próprio texto)

Esta secção segue o argumento do texto. Não se adota nenhuma leitura de debate doutrinário como posição da edição.

1. **Filho.** Deus fala no Filho (1:2). O Filho é herdeiro, criador, sustentador, purificador e assentado à direita (1:2–3). A confissão de Cristo como Deus é a de 1:8, citação do Salmo 44.
2. **Sacerdócio.** O sacerdócio de Cristo é segundo a ordem de Melquisedeque (5:6; 7:17). É eterno (7:24–25), porque não se transmite por linhagem.
3. **Aliança nova.** A antiga aliança envelheceu (8:13). A nova põe a lei no coração (8:10, Jr 31). Isto fundamenta a exortação ao culto e à perseverança.
4. **Sacrifício único.** O sacrifício de Cristo é feito uma vez (9:12; 10:10). Não se repete (10:11–14).
5. **Fé.** A fé é confiança no que não se vê (11:1), e as testemunhas de 11 mostram-na em ação.
6. **Disciplina.** O Pai disciplina os filhos (12:5–11). A disciplina é sinal de filiação, não de rejeição.
7. **Perseverança e advertência.** As advertências (2:1–4; 3:12–14; 6:4–8; 10:26–31) são intensas. O texto liga-as à confiança firme («nós somos casa de Cristo, se mantivermos a confiança», 3:6). Há leituras diferentes sobre o alcance dessas advertências. O estudo não escolhe; a tradução segue o texto e a nota regista a disputa.

---

## 7. Amostra de tradução (proposta provisória)

Não é a tradução da edição. Serve para testar a voz nas passagens mais difíceis, antes de o livro inteiro ser redigido.

### 1:1–4

**1:1** Deus, que outrora falou aos antepassados, em muitas partes e de muitos modos, pelos profetas,

**1:2** nestes dias finais falou-nos em *um* Filho, a quem constituiu herdeiro de tudo e por meio de quem também fez os mundos.

**1:3** Ele é o resplendor da glória e a marca exata da sua essência, e sustenta todas as coisas pela palavra do seu poder. Depois de ter feito a purificação dos pecados, sentou-se à direita da Majestade, nas alturas.

**1:4** Tornou-se tão superior aos anjos quanto o nome que herdou é mais excelente do que o deles.

*Notas da amostra:*
- **1:1 «antepassados».** O grego é τοῖς πατράσιν, «os pais». «Pais» em português pode ler-se como pais dos leitores em sentido familiar. «Antepassados» segue o sentido de geração anterior.
- **1:2 em *um* Filho.** ἐν υἱῷ. O itálico marca o acréscimo de «um» (o grego não tem artigo nem numeral). A preposição ἐν indica a esfera em que Deus fala, e «em um Filho» mantém essa ambiguidade. «Por meio de um Filho» seria uma leitura de instrumento, mais forte.
- **1:2 «os mundos».** αἰῶνας pode ser tempo («os séculos») ou o universo que o tempo mede. O autor usa o termo em 11:3 para o mundo criado pela palavra de Deus, e por isso «os mundos» é a leitura escolhida aqui. «Os séculos» é a alternativa tradicional.
- **1:3 «a marca exata da sua essência».** χαρακτὴρ τῆς ὑποστάσεως. «Marca» traduz χαρακτήρ (o cunho de uma moeda, a impressão). «Essência» traduz ὑπόστασις, que aqui não é «pessoa» no sentido posterior. A decisão está ligada à definição de 11:1.
- **1:3 «sentou-se».** A ordem do grego tem o verbo no fim do período. O português mantém a sequência: primeiro a purificação, depois o assento.

Crítica Textual: em 1:3, a base lê «καθαρισμὸν τῶν ἁμαρτιῶν ποιησάμενος», e RP lê «ποιησάμενος τῶν ἁμαρτιῶν ἡμῶν» (ordem diferente e «nossos»). A tradução da base não acrescenta «nossos»; a versão RP acrescentaria.

### 1:8 (com a variante das leituras de σου)

**1:8** Mas, quanto ao Filho: «O teu trono, ó Deus, é para todo o sempre; e o cetro de justiça é o cetro do teu reino.»

*Notas da amostra:*
- **1:8 «ó Deus».** O grego tem ὁ θεός no lugar de um vocativo. A tradução põe o vocativo, porque a frase se dirige a Deus.
- **1:8 «para todo o sempre».** εἰς τὸν αἰῶνα τοῦ αἰῶνος é literalmente «para o século do século». A forma tradicional é «pelos séculos dos séculos». «Para todo o sempre» é mais clara e mantém o sentido de eternidade.
- **1:8 «cetro de justiça».** ῥάβδος τῆς εὐθύτητος. O substantivo εὐθύτης é retidão, direção reta. «Justiça» é a palavra corrente em português para esta ideia.

Crítica Textual: sobre o final, «σου» (base, Treg, NA28, RP) contra «αὐτοῦ» (WH). Ver 3, grupo C. A tradução segue a base.

### 9:11–14

**9:11** Mas Cristo veio como sumo sacerdote dos bens que já chegaram, por meio de um tabernáculo maior e mais perfeito, não feito por mãos humanas, isto é, não desta criação.

**9:12** Não por meio do sangue de bodes e de bezerros, mas pelo seu próprio sangue, entrou uma vez por todas no santuário, tendo obtido redenção eterna.

**9:13** Porque, se o sangue de bodes e de touros, e a cinza de uma novilha borrifada sobre os que estavam contaminados, os consagra para a pureza da carne,

**9:14** quanto mais o sangue de Cristo, que, por meio de um Espírito eterno, se ofereceu a si mesmo sem mácula a Deus, purificará a nossa consciência das obras mortas, para servirmos o Deus vivo?

*Notas da amostra:*
- **9:11 «os bens que já chegaram».** Leitura γενομένων (base). A alternativa μελλόντων daria «os bens que hão de vir». A decisão está na secção 3, grupo A.
- **9:11 «isto é, não desta criação».** τοῦτʼ ἔστιν, ou seja, «isto é». «Desta criação» ecoa a palavra κτίσις, que aqui não é só o mundo material.
- **9:12 «santuário».** τὰ ἅγια é plural neutro, o lugar santo. Em português «santuário» serve. «Santo dos Santos» seria uma leitura mais específica que o texto não diz.
- **9:13 «os consagra».** ἁγιάζει. Verbo de santificação, que em português é «consagrar» ou «santificar». Escolheu-se «consagrar», por ser o termo do culto.
- **9:14 «a nossa consciência».** Leitura ἡμῶν (base). A alternativa é «a vossa». A secção 3 explica a escolha.
- **9:14 «um Espírito eterno».** Sem artigo, sem maiúscula decidida pelo texto. A tradição lê o Espírito Santo; o texto grego não impõe essa leitura, e a tradução não a decide.
- **9:14 «servirmos o Deus vivo».** λατρεύειν é o serviço cultual. Em português «servir» é o verbo que o português usa sem perder o tom de culto.

Crítica Textual (9:11): a alternativa μελλόντων (Treg, RP, KJTR, ST, Scrivener; 01, 02) é a leitura que a base não segue. Ver secção 3, grupo A.

Crítica Textual (9:14): P46 não lê o trecho seguinte a «ἄμωμον τῷ θεῷ» (lacuna do papiro). A alternativa ὑμῶν (01 e Treg, RP, KJTR, ST, SR, Scrivener) é a leitura que a base não segue. Ver secção 3, grupo A.

---

## 8. Pendências e próximos passos

1. **Decisão do responsável** sobre as cinco passagens do grupo A (9:11; 9:14; 8:8; 10:34; 11:11) e sobre a opção de colchetes nas do grupo B (2:7; 3:6; 7:21; 11:37; 13:21). Sem decisão, a edição segue a base e regista as alternativas na nota.
2. **Datas dos manuscritos** (secção 2.2): só P46 está verificada. Confirmar as restantes numa fonte consultada antes de publicar.
3. **Literatura secundária** (protocolo §3, nível 4): nenhum comentário ou gramática foi consultado. Antes de citar qualquer autor, consultar a obra. Até lá, nada é citado de fora.
4. **Colação e aparato:** registar a discrepância de 11:4 (01 e 02 leem τῷ θεῷ, o aparato do SBLGNT só cita Treg). Verificar se a extração do aparato conta estas leituras da mesma forma em outros versículos.
5. **Lacunas:** 03 não tem dados a partir de 9:15 na colação. Confirmar nas transcrições antes de afirmar que o Vaticanus não lê uma passagem.
6. **Tradução:** redigir o livro inteiro (303 versículos) em `.bee-cache/heb/` no mesmo formato de Efésios, com o montador, as notas e as Críticas Textuais. Só depois da decisão do responsável sobre o grupo A.
7. **Atualizar** `docs/ESTADO.md` e `docs/EDITORIAL.md` quando o texto estiver redigido, e não antes.
8. **Não aprovar.** A aprovação é do responsável (`review.editorial_blocks`), não do agente.
