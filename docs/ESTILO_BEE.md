# A voz da Bíblia de Estudo Epignósis

**Proposta editorial v0.4 — amostras de calibração, não texto aprovado.**

> Clareza para ler, cadência para proclamar, profundidade para estudar. O impacto deve vir do texto, não de frases que lhe acrescentamos.

## O que aprender com outras Bíblias

| Referência | Princípio que interessa à BEE | Limite |
|---|---|---|
| NVT | Português natural, compreensível na primeira leitura | Não eliminar uma tensão ou ambiguidade que pertence ao original |
| KJA | Solenidade e cadência na leitura pública | Não acrescentar grandiloquência ou arcaísmos |
| A Mensagem | Perceber o movimento do argumento e a força das imagens | Reservar a expansão devocional para fora do versículo |
| ARC | Atenção aos termos, às repetições e às conexões | Fidelidade não significa copiar a sintaxe nem pressupor a mesma edição grega |

Não combinar frases dessas versões nem as usar como texto de partida. A redação é própria e nasce da passagem no original. Obras protegidas podem orientar o estudo; registar o que foi efetivamente consultado e sintetizar com palavras próprias, sem redistribuir conteúdo protegido sem autorização.

## Regras para escrever e editar

1. **Traduzir a unidade antes de fechar os versículos.** Identificar quem fala, a quem, em que situação e com que propósito. Preservar conectores decisivos, contrastes, imagens e repetições intencionais. Dividir frases longas quando isso não altera a lógica.
2. **Escrever para o ouvido sem escrever um sermão.** Ler em voz alta. Preferir verbos concretos e ordem natural. Usar português contemporâneo com voz própria, sem adotar uma região como norma; evitar regionalismos desnecessários. Usar «vocês» quando natural no plural e manter concordância consistente ao usar «tu».
3. **Preservar a precisão teológica sem jargão gratuito.** Não substituir automaticamente graça, fé, justiça ou santidade por explicações. Manter um glossário de decisões por contexto; o mesmo termo grego não exige sempre a mesma palavra portuguesa.
4. **Separar tradução e nota exegética.** O versículo traduz. A nota apresenta a expressão original, explica a escolha no contexto, indica alternativas plausíveis e compara traduções identificadas quando houver diferenças úteis. Oração, declaração e aplicação devocional não entram nas notas.
5. **Justificar escolhas que mudam a leitura.** Registar referência, edição e revisão, expressão original, opção adotada, alternativa relevante e razão contextual. Distinguir análise gramatical, divergência entre edições e interpretação. Não listar léxicos ou comentários como consultados se não foram; Strong é índice, não prova de sentido.

**Convenção para toda a BEE — Selá.** Quando o original trouxer a indicação musical סֶלָה, mantê-la no lugar como *[Selá]* (no módulo MyBible: `<i>[Selá]</i>`). Na leitura pública a marca não se pronuncia. Não a acrescentar por sugestão de pausa nem aplicar a convenção a nomes de lugar.

**Convenção para toda a BEE — rubricas de título.** Quando o original trouxer uma indicação dirigida ao regente ou aos instrumentos (por exemplo, «Ao mestre de música. Com os meus instrumentos de cordas.», Hab. 3:19), a leitura em Markdown dá-lhe uma linha própria, em itálico, depois do versículo. No JSON da edição nova a rubrica fica em `<i>` no fim do texto do versículo, porque o formato não tem quebra de parágrafo dentro de `text`. Não é texto do versículo em disputa e não leva `[[ ]]`.

## Três testes de voz

Exercícios de redação a partir das expressões gregas indicadas. Não constituem uma colação de edições nem uma revisão lexical especializada.

**Filemom 1:7 — afeto sem sentimentalismo**

> O teu amor trouxe-me muita alegria e consolo, irmão, porque, por meio de ti, o coração dos santos encontrou alívio.

**Decisão:** «coração» comunica em português o valor afetivo de *σπλάγχνα* sem importar a imagem anatómica. Conferir a relação com a linguagem afetiva dos vv. 12 e 20 ao traduzir a carta inteira; «alívio» deve ser avaliado com a alternativa «descanso».

**Romanos 12:2 — contraste sem explicação embutida**

> Não se amoldem a esta era, mas sejam transformados pela renovação da mente, para discernirem qual é a vontade de Deus: o que é bom, agradável e perfeito.

**Decisão:** «esta era» procura preservar o valor temporal de *αἰών*, que «este mundo» pode obscurecer. «Sejam transformados» conserva a passiva, sem inserir no versículo um agente que o verbo não explicita.

**Judas 1:24 — cadência sem promessa inventada**

> Àquele que pode guardar vocês de tropeçar e apresentá-los sem mancha, com grande alegria, diante da sua glória…

**Decisão:** «tropeçar» preserva a imagem de *ἀπταίστους*. A frase fica aberta porque a doxologia continua no v. 25. A passagem celebra o poder de Deus; não diz que o leitor nunca enfrentará dificuldades.

## Ordem da nova edição

1. **Cartas:** Filemom como piloto de livro inteiro; depois 2 João, 3 João, Judas, Tito, 2 Tessalonicenses, Colossenses e Filipenses. Prosseguir com Gálatas, Efésios, 1 Tessalonicenses, 1 e 2 Timóteo, Tiago, 1 e 2 Pedro, 1 João, Hebreus, 1 e 2 Coríntios e Romanos.
2. **NT narrativo e profético:** começar pelo Evangelho mais curto, Marcos; seguir com João, Mateus, Lucas, Atos e Apocalipse. Os livros menores do AT ficam para depois do NT.
3. **AT:** planear a ordem e calibrar a voz para narrativa, poesia e profecia após o ciclo do NT.

## Fontes e produção

- Fixar a edição-base antes de gerar livros. O Scrivener já integrado é declarado de domínio público pelo fornecedor e representa uma tradição textual específica. O SBLGNT usado hoje é uma edição crítica sob CC BY 4.0, não domínio público. Se o requisito for domínio público sem exceções para a base, documentar a escolha de uma edição compatível antes da migração; não trocar apenas a licença no rótulo. Conferir separadamente licenças do texto, da transcrição, da morfologia e do aparato. Manter atribuições quando exigidas.
- Para cada unidade: ler o contexto, conferir original e comparação autorizada, consultar léxicos e comentários onde necessário, redigir, testar a leitura em voz alta e registar as decisões. Se a base ou a evidência faltar, guardar o ponto como pendência em vez de inventar.
- **Recomeçar a tradução, não a infraestrutura.** Preservar JSON, checkpoints, validação, compilação e agendamento legados. Antes de ligar a nova edição ao agendador, isolar diretório, checkpoints e artefactos por edição; não retomar nem misturar texto antigo na nova redação. Validar primeiro Filemom de ponta a ponta.
- **Entrega proposta:** um JSON por livro integral, mais os módulos de texto e comentários MyBible (`.SQLite3`), ambos rotulados como prévia. Checkpoints de produção não são entregas de livros completos. Conferir correspondência JSON/SQLite, integridade dos módulos e abertura no aplicativo.
- Depois da calibração, gerar rascunhos sem pedir aprovação por bloco, desde que as fontes estejam disponíveis e a execução configurada. Separar os estados de cobertura, revisão editorial e revisão especializada. O responsável pode baixar e rever os artefactos enquanto a produção avança; produção contínua não é autorização de publicação.

Este documento não altera o agendador nem ativa uma segunda linha de produção. O [plano anterior](EDITORIAL.md) descreve a edição legada e as convenções técnicas existentes.

## Calibração — naturalidade e voz própria

- **Almeida como referência comparativa, não como norma de redação.** Preservar uma expressão familiar quando é clara, natural e fiel (por exemplo, «oração da fé»). Quando a forma memorizada já não comunica bem ou depende de outra leitura grega, redigir em português corrente e explicar a diferença numa nota se for substantiva. Distinguir mudança de linguagem de variante textual.
- **Mais naturalidade no corpo do texto.** Preferir verbos e frases que soem bem quando lidos em voz alta. Não trocar uma imagem clara por uma explicação nem introduzir uma conclusão doutrinária para tornar a passagem mais enfática. Testar a redação com leitores habituados à Almeida e com leitores novos: conseguem explicar o mesmo sentido depois de ouvir o trecho?
- **Coerência teológica é ler a passagem inteira.** Em Marcos 11, ler a declaração à luz da fé em Deus, da oração e do perdão (vv. 22–25). Em Tiago 5, não apagar os responsáveis da igreja, o óleo, a oração ou a ação do Senhor. Notas de fé e cura não devem atribuir culpa ao enfermo nem prometer resultados que a passagem não especifica.

### Referências observadas no movimento da Fé

- **Kenneth E. Hagin — KJV:** a [história do ministério Rhema](https://rhema.org/index.php?Itemid=141&catid=174&id=9%3Ahistory-of-the-ministry&limitstart=&option=com_content&showall=1&view=article) apresenta Marcos 11:22–24 na redação da KJV; o artigo [Confession of God’s Word Builds Faith](https://rhema.org/index.php?Itemid=11&id=2785%3Aconfession-of-god-s-word-builds-faith&option=com_content&view=article) retoma o v. 23. Observar a força dos verbos «dizer» e «crer», sem converter a aplicação do pregador em redação bíblica.
- **Chris Oyakhilome — KJV e Amplified Classic (AMPC) nas amostras:** a [Rhapsody de junho de 2020](https://christembassyhouston.org/wp-content/uploads/2020/06/June-2020-Rhapsody-of-Realities.pdf) cita Marcos 11:23 em redação KJV. A [coletânea devocional](https://rhapsodyofrealities.b-cdn.net/prayernetwork/bumper_packs/Rhapsody_Combo.pdf) cita Josué 1:8 como AMPC e distingue NKJV, AMP e AMPC na legenda; a legenda não permite medir frequência nem torna AMP e AMPC intercambiáveis. A BEE pode acolher a ideia de esclarecer em notas, sem importar expansões da Amplified para o versículo.
- **Rick Renner — referência para o formato de estudo:** em [Is There Any Sick Among You?](https://renner.org/articles/is-there-any-sick-among-you/), Renner discute o grego de Tiago 5:14–15 e separa a oração e a declaração da exposição. Imitar a separação editorial, não tratar a sua análise como autoridade lexical nem concluir, por este artigo, qual versão ele mais utiliza.

Esta sondagem documenta exemplos, não um ranking do movimento.

### Dois novos testes de voz (rascunhos)

**Marcos 11:22–23:** «Jesus respondeu: “Tenham fé em Deus. É verdade o que lhes digo: se alguém disser a este monte: ‘Ergue-te e lança-te ao mar’, e não duvidar no coração, mas crer que o que diz vai acontecer, assim lhe acontecerá.”»

**Razão:** preservar o monte, o ato de falar e o contraste entre dúvida e fé. A abertura dá o rumo à leitura: a fé é em Deus. Conferir o tratamento do plural e a ligação com os vv. 24–25 na revisão da unidade.

**Tiago 5:14–15:** «Há alguém doente entre vocês? Que chame os presbíteros da igreja, para que o unjam com óleo em nome do Senhor e orem por ele. A oração da fé salvará o doente, e o Senhor o levantará. Se tiver cometido pecados, eles lhe serão perdoados.»

**Razão:** manter «oração da fé» como ponte com a Almeida. «Salvará» conserva a amplitude de *sōzō*; o contexto imediato é de doença e a nota pode explicar a leitura «restabelecerá». Conferir a ordem da ação e a ligação de «em nome do Senhor» na revisão.


## Comparações de leitura — calibração v0.3

A **NTLH** e a **VFL** são referências para testar acessibilidade; a **NVI** é um contraponto útil para medir quanto da estrutura e do vocabulário bíblico se pode preservar sem tornar a frase pesada. A proximidade com a NVT varia por passagem; nenhuma dessas versões é fonte da redação BEE.

### João 3:16 — o amor demonstrado no ato de dar

> Foi assim que Deus amou o mundo: deu o seu Filho único, para que todo aquele que nele crê não pereça, mas tenha vida eterna.

**Nota exegética:** οὕτως (*houtōs*, «assim») aponta para o modo como o amor se manifesta: Deus deu o Filho. A [NVT](https://www.bibliaonline.com.br/nvt/jo/3) põe em primeiro plano a intensidade com «amou tanto»; a [VFL](https://www.bible.com/bible/200/JHN.3.16.VFL) usa «de tal maneira», que pode comportar as duas ideias. «Filho único» comunica μονογενής (*monogenēs*) em português corrente; «Unigênito», na [NVI consultada](https://www.bibliaonline.com.br/nvi/jo/3/16), é a alternativa tradicional. «Pereça», em contraste com «vida eterna», evita reduzir o contraste à morte física; a [NTLH](https://www.bible.com/pt/bible/211/JHN.3.16.NTLH) prefere «não morra».

### Romanos 12:2 — transformação e discernimento

> Não tomem esta época como modelo. Em vez disso, sejam transformados pela renovação da mente. Assim poderão discernir a vontade de Deus: o que é bom, agradável e perfeito.

**Nota exegética:** αἰών (*aiōn*) pode designar uma era; «esta época» mantém essa dimensão, ao passo que a [NVI](https://www.bible.com/pt/bible/129/ROM.12.2.NVI) explicita a ideia de «padrão deste mundo». μεταμορφοῦσθε (*metamorphousthe*) tem forma médio-passiva. A BEE testa «sejam transformados» sem explicitar o agente; a [NVT](https://www.geografica.com.br/biblia-nvt-bilingue/p) e a [NTLH](https://www.bible.com/pt/bible/211/ROM.12.2.NTLH) tornam Deus explícito. δοκιμάζειν (*dokimazein*) pode expressar examinar e reconhecer o que passa pelo teste. «Discernir» destaca o reconhecimento; «comprovar» é outra possibilidade, e a NVI consultada usa «experimentem».

Estas notas são amostras editoriais, não colações de manuscritos. Na produção, identificar a edição original e a edição de cada tradução comparada sempre que disponíveis. Não forçar divergências, inventar alternativas ou confundir uma opção de tradução com uma variante do original.

## Calibração v0.4 — cadência da King James e comparação internacional

Aqui, **KJV** designa a King James Version inglesa, não a KJA portuguesa. Usá-la como referência de cadência: paralelismo, contraste, imagens concretas e finais de frase com peso. Não importar arcaísmos, calques do inglês ou leituras de outra tradição textual sem justificação. A redação parte sempre do original.

**Notas exegéticas:** não restringir a comparação às versões semelhantes à NVT. Selecionar testemunhos de estratégias tradutórias diferentes, inclusive em outros idiomas (por exemplo, KJV, ESV, NJPS para o AT e traduções portuguesas de linhas diferentes), quando iluminarem a decisão. Identificar a edição efetivamente consultada. Uma tradução moderna é testemunho de uma escolha tradutória, não evidência manuscrita.

**Romanos 12:2 — novo teste, preferido para revisão:** «Não tomem esta época como modelo. Em vez disso, sejam transformados pela renovação da mente, para que possam pôr à prova e reconhecer a boa, agradável e perfeita vontade de Deus.» A expressão εἰς τὸ δοκιμάζειν marca o propósito; «pôr à prova e reconhecer» explicita dois aspectos de um só verbo, não duas etapas prescritas por Paulo. «Comprovar» é a opção mais concisa; «alcançar» pode sugerir obter aquilo que o verbo aqui apresenta como objeto de avaliação. A KJV usa *prove* e descreve a vontade de Deus como *good, and acceptable, and perfect*. A ESV conserva uma formulação equivalente a «o que é bom, agradável e perfeito». A nova redação integra os adjetivos à expressão «vontade de Deus» como escolha sintática em português.

**João 3:16 — cadência no contraste:** «Foi assim que Deus amou o mundo: deu o seu Filho único, para que ninguém que nele crê pereça, mas tenha vida eterna.» A KJV usa *only begotten Son*; «Filho único» mantém a singularidade expressa por μονογενής sem importar a formulação tradicional inglesa. «Ninguém que nele crê» reformula πᾶς ὁ πιστεύων sob a negação: a alternativa mais próxima da sintaxe é «todo aquele que nele crê não pereça».

**Salmo 23:1 — cadência pela concisão:** «O SENHOR é meu pastor; nada me falta.» לֹא אֶחְסָר (*lo eḥsar*) também admite «nada me faltará», como na leitura futura da KJV (*I shall not want*). O presente testa a confiança como realidade contínua. Nesse inglês, *want* exprime ter falta, não desejar. SENHOR representa o nome divino יהוה.

**2 Coríntios 4:8 — cadência pelos pares:** «De todos os lados, pressionados, mas não esmagados; perplexos, mas não desesperados.» A KJV traz *troubled … not distressed* e *perplexed … not in despair*. Em grego, ἀπορούμενοι e ἐξαπορούμενοι são formas aparentadas; o português «perplexos … desesperados» preserva o contraste, não o jogo sonoro. «Sem saber o que fazer, mas sem perder a esperança» é outra possibilidade, mais explícita e menos compacta.

## Calibração v0.5 — decisões e evidência

- **Romanos 12:2:** manter o rascunho com «para que possam comprovar a boa, agradável e perfeita vontade de Deus». A preferência editorial não equivale à revisão do capítulo inteiro.
- **João 3:16:** substituir o teste «Foi assim» por «Pois Deus amou tanto o mundo que deu o seu Filho único, para que todo aquele que nele crê não pereça, mas tenha vida eterna.» A construção οὕτως … ὥστε liga a intensidade do amor ao ato de dar. O resumo do [estudo de Aaron Michael Jensen (2019)](https://doi.org/10.1017/S0028688519000201) sustenta essa leitura com paralelos do grego antigo. A alternativa «Foi assim» destaca o modo, mas deixa a intensidade implícita. Esta é uma decisão de sintaxe, não de variante manuscrita.
- **2 Coríntios 4:8:** retirar o teste anterior como modelo. Novo rascunho: «Por todos os lados sofremos pressão, mas não somos esmagados. Ficamos sem saber o que fazer, mas não caímos no desespero.» A segunda frase explicita o contraste de ἀπορούμενοι / ἐξαπορούμενοι; não funde perplexidade com incredulidade. Ler com 4:7–9: a fragilidade dos mensageiros não é negada e o poder pertence a Deus. Rascunho em aberto.
- **Protocolo de evidência:** distinguir (1) crítica textual, que compara leituras e testemunhos quando variam, (2) sintaxe e semântica, que avaliam como traduzir a leitura adotada, e (3) exegese, que testa a escolha no argumento da passagem. Registar edição, aparato ou publicação de facto consultada e se foi consultado apenas o resumo. Comparar versões internacionais para mostrar as consequências das escolhas, não para decidir por maioria. Citar testemunhos manuscritos só quando verificados em fonte adequada.

## Calibração — Hebreus 11:1,3 e Marcos 16:17

- **Hebreus 11:1:** testar «A fé é o firme fundamento do que esperamos e a evidência do que não vemos.» ὑπόστασις permite discutir firmeza objetiva e segurança; «fundamento» é uma escolha contextual, não uma definição fixa nem a ideia de que a fé produz o que se espera. Comparar KJV (*substance*) e ESV (*assurance*). ἔλεγχος admite «evidência» e «convicção»; a primeira destaca a força probante, sem fazer da fé uma prova empírica. Ler com os exemplos do capítulo.
- **Hebreus 11:3:** testar «Pela fé entendemos que Deus formou o universo pela sua palavra, de modo que aquilo que vemos não veio de coisas visíveis.» O grego nega a origem em coisas visíveis (μὴ ἐκ φαινομένων); «veio do invisível» formula positivamente uma leitura que a frase não enuncia nesses termos. O texto nomeia a palavra de Deus como meio; não identifica o invisível como matéria-prima.
- **Marcos 16:17:** «[[Estes sinais seguirão os que crerem: em meu nome expulsarão demónios, falarão em novas línguas,]]». παρακολουθήσει admite «seguirão» e «acompanharão» (KJV *shall follow*; ESV *will accompany*). «Seguirão» não prova sequência cronológica ou posição física. A leitura dos sinais como consequência, não como alvo da missão, decorre de 16:15–20. Manter a sinalização do final longo.

## Calibração — vocabulário tradicional e poesia sapiencial

O responsável aprovou as amostras apresentadas de João 1:1; 14:6; 19:30; Romanos 6:23; Marcos 9:23–24; Romanos 10:17 e Gálatas 2:20 como referências de voz. A aprovação não se estende aos capítulos ou livros inteiros nem substitui revisão especializada.

Não substituir todo termo tradicional: manter «consumado» quando o contexto sustenta o peso da palavra; trocar «longânimo» por «paciente» quando o termo mais corrente comunica o contraste; esclarecer imagens idiomáticas sem eliminar imagens poéticas úteis. Em Eclesiastes, tratar הֶבֶל (*hevel*, imagem de sopro ou vapor) por contexto, sem converter toda ocorrência numa afirmação de que a vida não tem valor. Em Provérbios, preservar as relações e os paralelismos; não transformar máximas sapienciais em garantias incondicionais.

## Calibração — equivalência dinâmica e passagens em debate

- **Gálatas 5:20–21:** adotar «grupos rivais» para αἱρέσεις e manter «festas desenfreadas» para κῶμοι. **Josué 1:8:** redação ainda em revisão; conservar como pontos de estudo a relação entre boca, meditação e prática e as alternativas para o verbo final. Manter Marcos 11:23–24, Romanos 10:9–10 e Hebreus 10:23 como amostras de voz.
- Reestruturar a frase e explicitar relações claras no contexto quando isso comunicar melhor o sentido. Não converter uma inferência debatida em afirmação do versículo. Em textos sobre eleição, conservar os verbos e as relações do original; não enfraquecer «predestinou», «atrair» ou «endurece», nem inserir «fé prevista», «irresistivelmente» ou qualificações equivalentes onde não constam. As notas descrevem as alternativas e os limites da gramática sem dar preferência a um sistema teológico por identidade editorial.

## Glossário — ἐπίγνωσις

Por decisão editorial, traduzir o substantivo ἐπίγνωσις (*epignōsis*) por «pleno conhecimento» ou «conhecimento pleno», com minúsculas no corpo do texto. Não estender automaticamente a regra a γνῶσις ou a verbos aparentados. A nota explica a função no contexto; não apresenta o prefixo como prova de intensidade idêntica em todos os usos. Nas amostras aprovadas, ajustar 1 Timóteo 2:4 («cheguem ao pleno conhecimento da verdade») e Efésios 4:13 («à unidade da fé e do pleno conhecimento do Filho de Deus»). As demais redações dessas amostras permanecem aprovadas para calibração, não para publicação definitiva.

## Calibração — visões, linguagem íntima e violência

O responsável aprovou as amostras mais recentes sobre ἐπίγνωσις, salvação e narrativa. A próxima etapa editorial é aplicar o guia a Filemom inteiro, com fontes e decisões registadas antes de ligar a nova edição à automação.

Em textos apocalípticos e proféticos, preservar imagens, números, e ambiguidades cuja explicação pertence à nota; não converter uma interpretação em tradução. Em poesia amorosa, conservar metáforas e usar termos anatómicos correntes quando o original é explícito, sem acrescentar detalhes nem censurar a imagem. Em narrativas íntimas ou embaraçosas, manter o grau de explicitude do original e esclarecer eufemismos na nota. Em textos de violência, não suavizar as vítimas nem dramatizar a cena: distinguir cuidadosamente quem fala, quem age e se o texto narra, ordena, lamenta ou impreca.

## Última ronda de calibração proposta

Mateus 5:3–12 foi aprovado como amostra de voz («Bem-aventurados» e repetição preservados). Para concluir a calibração, testar Filemom 1:8–21 (argumento e apelo pessoal), Salmo 22:1–3,16–18 (lamento e dificuldade textual), Deuteronómio 6:4–9 (lei, recitação e ambiguidade sintática) e Lucas 15:25–32 (diálogo e final aberto). Filemom é o primeiro piloto de livro inteiro, não um teste a descartar; os restantes são amostras, não uma reordenação da produção.

## Piloto de cartas curtas

Filemom inteiro foi aprovado pelo responsável como referência de voz do piloto; isso não equivale a revisão especializada. 2 João e 3 João foram preparados para análise editorial, mantendo o SBLGNT fixado e a produção isolada. Em 3 João, a saudação final integra o v. 14 na numeração tradicional do JSON e dos módulos (v. 15 no SBLGNT).

2 João e 3 João foram aprovados pelo responsável para a calibração da voz. Judas foi acrescentado como prévia para análise editorial; não houve ativação da automação da nova edição.

**Judas:** carta aprovada como amostra editorial, incluindo a redação final «São ímpios, há muito assinalados para esta condenação» no v. 4. A alteração é de estilo, não de variante textual. A aprovação não substitui revisão especializada.

**Tito:** carta aprovada como referência de voz, incluindo «escravas do vinho» (2:3) e «conciliadores» (3:2). As notas explicam as nuances das duas escolhas. A aprovação editorial não substitui revisão especializada.

## Formato das notas — prosa (vigente desde 2026-11-23)

Este é o formato de todo o texto da edição nova. Aplica-se a todos os livros e
capítulos, sem exceções por livro ou por capítulo.

**Exemplo — Filipenses 2:6** (aprovado em voz e legibilidade; revisão especializada pendente):

> *Texto:* que, existindo em forma de Deus, não considerou o ser igual a Deus algo a que se agarrasse,
>
> *Nota (um parágrafo, sem rótulos):* *ἁρπαγμός* é a palavra mais discutida do hino. Pode significar o que se agarra (uma presa a conquistar), o que já se possui e não se larga, ou o que se usa em vantagem própria. A ARC e a ARA dizem «usurpação»; a NVI, «usar como vantagem»; a NAA, «reter a qualquer custo»; a NVT, «apegar-se». A BEE escolhe a imagem do gesto — «algo a que se agarrasse» — porque mantém as duas pontas: não nega a igualdade (que *μορφὴ θεοῦ* afirma), nega o agarramento. O versículo não diz que Cristo deixou de ser Deus; diz que não reteve por força o que era seu.

**Regras:**

1. Um parágrafo de comentário por versículo. Sem rótulos («Análise Léxica», «Síntese Exegética») e sem notação de nível (A, B, C), nem como rótulo nem como «confirmação».
2. Cada termo grego vem em itálico, com a transliteração entre parênteses na primeira ocorrência. O grego fica dentro da prosa, não numa lista.
3. A «Crítica Textual» é um parágrafo próprio, que começa por «Crítica Textual:», e só aparece quando o aparato SBLGNT ou a colação regista variante. Cita as siglas (WH, Treg, NA28, RP, e as testemunhas da colação) e diz, em frase clara, o que a variante muda e porque a base foi seguida. Sem variante, não há parágrafo.
4. A razão da escolha e a alternativa rejeitada entram no próprio parágrafo, não numa etiqueta. A revisão especializada é registada em `review`, não na nota.
5. Colchetes no texto só para o que não aparece nos manuscritos; a nota explica-os (`docs/EDITORIAL.md`).

Referência de estrutura: `docs/CRITICA_TEXTUAL.md`, secção 6.2.

## v0.6 — crítica textual, pontuação e arquivologia (20/11/2026)

A voz continua a mesma; o que muda é a **exigência de prova** por detrás de cada
nota e a coerência gráfica entre versículos. O protocolo completo está em
[CRITICA_TEXTUAL.md](CRITICA_TEXTUAL.md); aqui ficam as consequências para a
redação, que são as que um revisor precisa de ter à mão.

**Formato de notas (substituído).** A v0.6 pedia três secções e níveis de certeza. Esse formato foi retirado em 2026-11-23: ver «Formato das notas — prosa» acima.

**Só se cita o que se colacionou.** O aparato do SBLGNT nomeia edições (WH, Treg,
NA28, RP), nunca códices; por isso «o Sinaiticus lê X» só pode escrever-se onde
existe colação (`docs/colacao/`). Uma edição impressa não é um manuscrito, uma
tradução moderna não é evidência textual e «o Textus Receptus» não é um texto
único. Idade e número de cópias são indícios, não critério: decide-se por
evidência externa e interna, e a nota diz a evidência e a razão da escolha, sem notação de nível.

**Pontuação e maiúscula inicial.** Um versículo que continua a frase do anterior
termina em vírgula (ou ponto e vírgula) e o seguinte começa em minúscula; um
versículo que abre frase nova termina em ponto e o seguinte começa em maiúscula.
Nunca minúscula depois de ponto, nunca maiúscula depois de vírgula, e nenhum
versículo fica sem pontuação final.

**SENHOR e Senhor.** As maiúsculas são do Tetragrama יהוה no texto hebraico. No
grego do NT κύριος está escrito por extenso: escreve-se «Senhor». «O dia do
SENHOR» em 2Ts 2:2 afirmava do texto grego algo que ele não diz; a ligação à
fórmula profética (Jl 2:1; Am 5:18; Sf 1:14) pertence à nota.

**Norma ortográfica.** Português europeu, sem oscilar: «connosco», «de facto»,
«registo», «secção», «aspeto». Está em `modelos/estilo_bee.json` →
`registro.ortografia` e chega a todos os provedores.

**Colocação pronominal e progressivo.** Ênclise, como o português europeu a
faz: «metendo-se», «admoestem-no», «gloria-se», «ouvindo-o». A próclise em
início de oração («se metendo») é brasileira e está vetada. O progressivo faz-se
com «estar a + infinitivo» — «estava a batizar», «estão a ceifar», «estou a
fazer» —, que é a forma de Portugal e de Angola; «está fazendo» é brasileira.
O gerúndio simples verte o particípio presente grego («dizendo», «ouvindo-o»), e
«continuará a fazê-lo» entra como aspetual. Um progressivo com gerúndio já
aprovado não se reescreve só por causa da regra: mantém-se como variante. Esta
é a decisão do responsável de 22/11/2026, tomada quando o corpus mostrou as duas
formas em livros aprovados (Rute 2:9, Habacuque 1:5 contra João 1:28, 2Ts 1:3).

**Uniformidade só onde o grego é igual.** As fórmulas consolidadas repetem-se
letra a letra entre livros **quando as bases coincidem**. Filemom 1:3 tem
*πατρὸς ἡμῶν* e 2Ts 1:2 não tem: por isso a saudação de Filemom diz «Deus, nosso
Pai» e a de 2 Tessalonicenses diz «Deus Pai». Uniformidade fabricada é
infidelidade disfarçada de coerência.

**πᾶς com e sem artigo — correção de 2026-11-20.** O artigo depois de «todo» no
singular é obrigatório em português europeu e **não traduz o artigo grego**: «todo
o desejo de bondade e toda a obra de fé» (2Ts 1:11), «todo o irmão» (2Ts 3:6),
«toda a boa obra» (2Ts 2:17), «todo o homem» (João 1:9), «toda a iniquidade»
(Tito 2:14). A distinção grega regista-se na nota, não no artigo:
*πᾶς* anártrico distribui (cada desejo, cada obra); *πᾶς* com artigo pode
totalizar («todos os que creram», «todas as perseguições»). A redação anterior
desta regra mandava suprimir o artigo para marcar o anártrico; foi revertida no
mesmo dia, porque a distinção em que se apoiava («todo o desejo» = «o desejo
inteiro») é do português do Brasil e não do europeu. Prova de língua, não de
texto: a Almeida de 1911, impressa em Portugal e em domínio público, escreve
«todo o desejo» e «todo o irmão» para grego anártrico, e a ARC brasileira escreve
«todo desejo». «Com todo o poder» (2Ts 2:9) já seguia esta forma e deixa de ser
exceção.

**Famílias lexicais coerentes.** Uma família grega tem uma família portuguesa no
livro inteiro: *ἀτακτ-* → «viver desordenadamente» nos vv. 6, 7 e 11 do capítulo 3;
*ἀνομ-* → «rebelião»/«ímpio». E um só adversativo por frase: se o grego tem
*καί* … *ἀλλά*, o *καί* é continuativo e o contraste fica todo no «mas».

**Nota não inventa.** Nem etimologias, nem derivadas portuguesas que não existem,
nem «todas as edições» quando se consultaram seis. E, acima de tudo, **a nota não
pode contradizer o versículo**: se a nota regista que a base não tem uma palavra,
o texto não a traduz. A passagem de lapidação de 2 Tessalonicenses — verso a
verso, com a regra reutilizável de cada correção — está em
`OFICINA_TRADUCAO.md`.

**Proveniência.** Cada livro declara em `bibliography` as fontes efetivamente
consultadas, com revisão (commit), URL, licença e o que se consultou nelas; e em
`review` os estados de revisão editorial e especializada, que nunca se confundem
com cobertura. O acervo CNTR é CC BY-SA: é consultado e citado, nunca
redistribuído — vive em `.bee-cache/`, fora do Git.

**2 Tessalonicenses** foi o primeiro livro regenerado sob este protocolo
(47 versículos, 30 unidades de variação decididas, duas de nível C) e o primeiro a
levar uma passagem de lapidação completa: doze versículos e catorze notas revistos
sobre a colação, mais duas aspas de citação reabertas em João 1:31 e 1:34, que o
teste transversal de marcas apanhou. A redação é
editorial, não saída de modelo, e o livro continua RASCUNHO: a voz da versão
anterior tinha sido aprovada, esta redação ainda não foi lida pelo responsável.

**Gente / pessoas.** Usar «gente» quando se ouve ou vê um conjunto (Mq 2:12); preferir «pessoas» quando se contam indivíduos (Jn 4:11). Não trocar «povo» por «gente» quando está em causa a identidade de uma comunidade. Evitar «essa gente» se introduzir desprezo que não vem do texto.

## Convenções de notas — fixadas na revisão de João 1–15

Estas convenções saíram da revisão de João e valem para todos os livros novos e para
as correções dos já aprovados. `scripts/verificar_convencoes_notas.py` confere as
que se verificam sem ler o grego.

1. **Nomes e termos fixos.** O Espírito é «Parácletos» (nominativo, com s, como em 14:26, 15:26 e 16:7), transliteração literal de παράκλητος, *parákletos* (acento no primeiro «a»; η dá «e»). O acusativo, em 14:16, é «Parácleton», *parákleton*. «Paráclito» e «Paracletos» não se usam. Decisão do responsável; antes era «Paráclito». Em 1 João 2:1, onde o original tem o mesmo acusativo (παράκλητον), usa-se «Parácleton» com nota sobre «consolador, advogado».
2. **NIV é tradução, nunca testemunha.** Na Crítica Textual, a NIV só aparece quando
   diverge da base, como escolha de tradução: «a NIV segue essa leitura por escolha de
   tradução» ou «a NIV omite a palavra, por escolha de tradução». Quando concorda com a
   base ou com um dos editores, não se cita.
3. **Crítica Textual.** Um parágrafo próprio, «Crítica Textual:», uma só vez por
   versículo. Cita WH, Treg, NA28, RP e as testemunhas da colação que diferem; diz o que
   a variante muda; diz porque a base foi seguida. Quando a variante só existe na
   colação (aparato vazio), diz-se que o aparato da SBLGNT não regista variante. Os
   sinais de aparato (⸀ ⸁ ⸂ ⸃) não entram na nota.
4. **«a base».** Depois dos dois pontos do aparato, «a base» em minúscula
   («Aparato de edições SBLGNT, 9:8: a base lê…»). Com maiúscula só no início de frase.
5. **Português europeu nas notas.** «leem» (não «lêm»), «regista» (não «registra»),
   «contacto», «facto», «secção», «ativa» e «receção» conforme a norma do projeto. Formas
   brasileiras só dentro de citação de outra tradução, entre aspas.
6. **Transliteração.** Itálico para o grego, com a transliteração entre parênteses na
   primeira ocorrência. Minúsculas nas formas gregas (*huios*, não *Huios*). Vogais
   longas com macron ou circunflexo na transliteração (*melleis*, *paraklēton*).
7. **Decisões do responsável.** Só o responsável aprova. Cada aprovação fica na nota do
   bloco (`review.editorial_blocks`), com o que foi alterado depois dela. Mudança de
   texto de versículo já aprovado fica registada na nota do bloco, com o motivo.
8. **Escolhas de texto em aberto.** Quando a escolha é substantiva (ex.: 4:1, «Jesus» ou
   «o Senhor»), a nota diz qual é a leitura da base e qual é a alternativa, e o bloco
   fica com a nota «para decisão». A tradução segue a base até decisão contrária.

## Estilo verificado — decisões aprovadas em João 1–15

Estas decisões foram tomadas pelo responsável e valem para os capítulos seguintes e para os
outros livros.

**Norma ortográfica.** Acordo de 1990 (AO90) em toda a edição, em português europeu. Angola
assinou o acordo, mas não o ratificou: a escolha é editorial, não oficial. Não se misturam
formas de 1945 («ação» sim, «acção» não; «aspeto», «atividade», «ato», «perceção», «receção»,
«aceção», «ativa», «rutura», «leãozinhos»). Exemplos corrigidos: 2 Tessalonicenses 3:14 («rutura»,
não «ruptura», que é a grafia brasileira); Naum 2:11 e 2:13 («leãozinhos», não «leõezinhos»).

**Acréscimos no texto.** Palavras acrescentadas por clareza ficam em `<i>…</i>`. Os colchetes
ficam para a evidência dos manuscritos (regra de 2026-11-22). Exemplos: Habacuque 3:3, 3:9, 3:13
e 3:19; Filipenses 1:16; 2 Tessalonicenses 1:5, 1:7, 2:3, 2:7, 2:9 e 3:9. «[Selá]» segue a
convenção pública, à parte.

**Colchetes de variante.** Quando a base lê uma palavra que a maioria não tem, põe-se a palavra
entre colchetes simples, com nota que diz a evidência e a leitura alternativa. Não se usam
colchetes duplos. Exemplo: Judas 1:5, «[Jesus]» (NA28 e base; WH e Treg leem «o Senhor»).

**Nome de Jesus e leituras de «Senhor».** Em 4:1, a base lê «Jesus» (NA28, 01, 05); WH, Treg e
RP leem «o Senhor». Decisão do responsável: «Jesus» no texto, com a alternativa na nota.

**NIV.** Só aparece na Crítica Textual como escolha de tradução, quando diverge da base. Exemplos
aprovados: 12:19 («a NIV acrescenta «ὅλος», por escolha de tradução»); 15:18 («a NIV omite a
palavra, por escolha de tradução»).

**Termos fixos.** «Parácletos» (14:26, 15:26, 16:7) e «Parácleton» (14:16), com acento, transliteração literal. «Te vás manifestar» em 14:22
(opção A). «levava» em 12:6, não «tomava».

**Confronto com o grego.** Antes de aprovar um capítulo, conferir cada versículo com o SBLGNT da
colação (`docs/colacao/João.json`, campo `base.sblgnt`) e com as palavras citadas nas notas. Na
revisão de 12, 14 e 15, não se encontrou omissão, acréscimo sem marca nem inversão de sentido.

## Lista de verificação para cada capítulo novo

1. Ler o original (SBLGNT) e a colação (`docs/colacao/João.json`, ou o equivalente do livro)
   antes de redigir. Para cada versículo, confrontar `divergencias` com a Crítica Textual.
2. Redigir o texto e uma nota em prosa por versículo, sem rótulos, com o grego em itálico
   e a transliteração na primeira ocorrência.
3. Conferir a Crítica Textual: uma só, em parágrafo próprio, sem sinais de aparato, com as
   siglas e as testemunhas que diferem, e com a NIV só como escolha de tradução.
4. Correr as verificações: `python3 scripts/verificar_dados.py`,
   `python3 scripts/verificar_estilo.py`, `python3 scripts/verificar_convencoes_notas.py`,
   `python3 scripts/verificar_notas_colacao.py --dados edicoes/nova/livros_json --colacao docs/colacao/João.json`
   (para João), `python3 -m unittest discover -s tests`, e o verificador ortográfico
   com `pyspellchecker` instalado (alerta; confirmar à mão).
5. Listar para o responsável as passagens que precisam de decisão, com a leitura da base e
   a alternativa. Não aprovar nem marcar aprovação em nome dele.
6. Regenerar a leitura do livro (`scripts/gerar_leitura_livro.py`), atualizar `docs/ESTADO.md`
   e fazer commit no ramo de trabalho.
