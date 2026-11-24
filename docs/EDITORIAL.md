# Plano de trabalho — Bíblia de Estudo Epignósis

**Estado (20/11/2026):** a edição nova está em prosa em todos os livros já tratados: João 1–10, 1 Tessalonicenses, 2 Tessalonicenses, Tito, Filemom, 2 João, 3 João e Judas. João 5–6 foram aprovados pelo responsável em 23/11; o restante está em rascunho, à espera de leitura e aprovação. Os blocos de cada livro estão em `review` no respetivo JSON, e a tabela de estados é a fonte de verdade. Nada disto é aprovação editorial sem leitura do responsável, e tudo precisa de revisão especializada antes de publicação.

## 1. Objetivo e forma de trabalho

Produzir, em colaboração entre o responsável pelo projeto e o assistente nesta conversa, uma Bíblia de estudo em português contemporâneo: 66 livros, 1.189 capítulos e comentários ligados aos versículos. Não usar serviços externos de IA nem exigir `API_KEY` para criar os textos neste novo fluxo.

O assistente prepara os rascunhos, consulta as fontes efetivamente disponíveis, regista decisões e organiza os ficheiros do projeto. O responsável autorizou a produção contínua sem aprovação a cada bloco e pretende fazer uma revisão posterior no aplicativo; ele pode ajustar as opções editoriais em qualquer momento. A autorização para avançar não equivale à aprovação dos textos ainda não examinados. A aprovação editorial não substitui a revisão por especialistas em línguas bíblicas, crítica textual e teologia antes de uma publicação.

## 2. Diretrizes editoriais propostas

- **Português claro, atual e reverente:** frases naturais, sem arcaísmos desnecessários ou paráfrases longas. Empregar “vocês” para o plural quando adequado; “tu” e os seus correspondentes podem ser mantidos em oração direta, com concordância consistente.
- **Texto bíblico distinto do comentário:** manter no texto aquilo que a passagem expressa e reservar explicações, inferências e aplicações para as notas. Distinguir observação linguística de interpretação teológica.
- **Redação própria:** a fluidez de traduções contemporâneas pode inspirar características gerais de linguagem, mas a BEE não deve copiar a redação de uma tradução protegida. Conferir os direitos dos exemplos e das fontes antes da distribuição.
- **Acréscimos:** usar `<i>...</i>` para palavras acrescentadas por clareza que não estejam expressas no original, segundo um critério editorial consistente. Não marcar automaticamente cada palavra exigida pela gramática portuguesa; documentar decisões difíceis.
- **Nome divino:** propor `SENHOR` para o Tetragrama, distinguindo-o de `Senhor` para *Adonai*; decidir os casos em que os dois nomes ocorrem juntos.
- **Títulos dos Salmos:** preservar e identificar as inscrições hebraicas quando pertinentes, sem deslocar a numeração dos versículos. O tratamento atual das superscrições no gerador precisará de revisão antes de publicar Salmos.
- **Texto e versificação:** usar o WLC por meio da Open Scriptures Hebrew Bible para o AT; o SBLGNT para o NT, com Textus Receptus de Scrivener e aparato SBLGNT como comparação ou suplemento identificado quando necessário. A numeração-alvo segue o inventário tradicional adotado no projeto; diferenças de versificação deverão ser sinalizadas e revistas.

### Convenção de variantes textuais

Seguir a edição crítica escolhida para o texto-base, considerando os testemunhos antigos e a crítica textual sem pressupor que o manuscrito mais antigo tenha sempre razão. O SBLGNT é uma edição eclética, não a cópia de um único manuscrito. Assinalar variantes relevantes com `[[...]]` no trecho correspondente e explicar objetivamente no comentário as leituras e as evidências disponíveis, sem ocultar testemunhos que apoiem a alternativa nem forçar conclusões dogmáticas. Os levantamentos consultados e suas limitações devem ser identificados; não apresentar comparação de edições como exame direto de manuscritos.

**Regra do responsável (2026-11-22):** colchetes no texto da tradução só para o que não aparece nos manuscritos ou situação semelhante (passagem ausente da maioria ou das testemunhas mais antigas, suplemento de edição, variante substantiva). Cada passagem marcada tem nota com a evidência e a razão da escolha. «[Selá]» não entra nesta regra: é a marca musical da convenção pública.

Os colchetes podem indicar **uma leitura adotada pelo SBLGNT** que outros testemunhos não têm (por exemplo, João 3:31), **uma leitura alternativa substantiva** (João 1:34) ou **um suplemento do Scrivener ausente no SBLGNT** (João 3:13, 15 e 34). Em João 4:42, eles assinalam o final da leitura curta do SBLGNT, e a nota informa um acréscimo do Scrivener que não aparece no texto traduzido. Em cada caso, a nota deve dizer qual é o tipo de sinalização e qual leitura está na edição crítica; retirar todos os colchetes ou todo o texto entre eles **não** recupera automaticamente o SBLGNT em todos os casos. A sinalização editorial, embora útil, não estabelece por si só a origem nem a autenticidade de uma leitura. A convenção permanece sujeita à revisão do responsável.

O procedimento completo está em [CRITICA_TEXTUAL.md](CRITICA_TEXTUAL.md), que fixa quatro níveis de evidência, as três proibições (edição impressa não é manuscrito; tradução moderna não é evidência textual; «o Textus Receptus» não é um texto único) e a decisão por unidade, sem níveis de certeza impressos. Onde há colação efetiva — `docs/colacao/<livro>.json`, produzido por `scripts/colar.py --livro N` — a nota pode nomear códices e papiros; onde não há, só pode nomear o que o aparato nomeia. 2 Tessalonicenses é o livro de referência deste procedimento.

Ao chegar a Marcos 16:9–20 e João 7:53–8:11, marcar cada versículo da passagem longa independentemente, inclusive ao atravessar capítulos, e mencionar a evidência pertinente e as leituras alternativas nas notas. Em 1 João 5:7–8, conservar sem colchetes as palavras comuns e marcar somente a expansão disputada se for apresentada como suplemento, identificando sua fonte. João 7:53–8:11 **foi produzida** no bloco B (2026-11-22), entre colchetes, com revisão especializada pendente; Marcos 16:9–20 **ainda não foi produzida**. Quando os dados forem insuficientes, registrar a lacuna e submetê-la a revisão especializada.

## 3. Comentários por versículo

Cada nota é um parágrafo em prosa, sem rótulos. Dentro dele, o comentário cobre três conteúdos:

1. **Léxico:** destacar as palavras realmente relevantes, com forma original, transliteração, referência Strong e explicação contextual quando verificadas.
2. **Crítica textual:** apresentar variantes importantes apenas quando apoiadas pelas fontes consultadas; indicar a edição e a referência. Se não houver verificação suficiente, dizer isso em vez de inventar testemunhos ou diferenças. A certeza não se imprime na nota: as passagens de decisão difícil ficam assinaladas em `review` como prioridade de revisão especializada.
3. **Sentido:** explicar o argumento e o contexto em linguagem acessível, distinguindo o que o texto diz de uma interpretação ou aplicação possível.

Para Salmos 23, foram consultadas manualmente entradas da transcrição resumida de BDB e do dicionário de Strong na [Open Scriptures Hebrew Lexicon](https://github.com/openscriptures/HebrewLexicon); essa transcrição está em desenvolvimento e não é uma edição completa do BDB. Para Filemom, foram consultados os léxicos de Dodson e Abbott-Smith; para João 1–4 a conferência com esses dois léxicos foi feita em 2026-11-20 (ver «Léxico» abaixo). Para Filemom, também foram consultadas as entradas [G2842](https://www.blueletterbible.org/lexicon/g2842/kjv/tr/0-1/), [G1922](https://www.blueletterbible.org/lexicon/g1922/kjv/tr/0-1/) e [G4698](https://www.blueletterbible.org/lexicon/g4698/kjv/tr/0-1/) de Thayer disponibilizadas pela Blue Letter Bible. A base eletrônica de Thayer exibida pelo sítio tem aviso de direitos da Biblesoft: foi consultada, não incorporada; verifique direitos antes de qualquer reprodução. As referências, revisões, entradas consultadas e limitações constam dos respetivos JSON. Os léxicos não foram integrados à CLI nem fornecidos ao gerador legado. O Nestle-Aland não foi consultado diretamente. Não atribuir definições ou leituras a obras sem acesso e consulta verificáveis. O aparato SBLGNT compara edições; não deve ser apresentado, por si só, como consulta direta aos manuscritos. A disponibilidade de códigos Strong e dados morfológicos também varia conforme a fonte.

**Base e comparação (decisão de 2026-11-24).** O texto-base continua a ser o SBLGNT. Quando a NA28 divergir do SBLGNT, a nota dá a leitura da NA28 como segunda referência explícita (João 1:34; pontuação de 1:3–4). Para comparação de tradução, usam-se ARC, ACF, NVI, NTLH e Almeida 1911 (`docs/COMPARACAO_POPULAR.md`), acrescidas de TEB e Bíblia de Jerusalém. Antes de publicar, os textos da TEB e da Bíblia de Jerusalém são confirmados na edição impressa; citações de terceiros não bastam.

**Formato das notas (decisão de 2026-11-23).** As notas seguem o formato das cartas e dos livros do AT já aprovados (Filipenses, 1 e 2 Tessalonicenses, Rute, Jonas, Ageu, e o piloto Filemom): um parágrafo de comentário em prosa por versículo, sem rótulos. A Crítica Textual vai num parágrafo próprio, «Crítica Textual:», **só quando** o aparato da SBLGNT ou a colação registam variante; cita as siglas do aparato (WH, Treg, NA28, RP, Holmes, WHmarg) e diz, em frase clara, o que a variante muda. Não se usa notação de nível (A, B, C) nem «confirmação» como rótulo. Cada nota abre com o termo grego em itálico e a transliteração, expõe as opções de tradução e justifica a escolha. Toda a variante do aparato tem de ter CT nos capítulos em prosa.

**Formato único (decisão de 2026-11-20).** Todo o texto da edição nova está em prosa, e não há formato por livro nem por capítulo. `bee/inspetor.analisar_comentario` verifica a regra: sem rótulos antigos («Análise Léxica», «Síntese Exegética»), sem níveis de certeza A/B/C impressos, e sem palavras greco-latinas mistas fora de itálico. A «Crítica Textual:» é um parágrafo próprio, só quando o aparato ou a colação registam variante. A porta do gerador por máquina foi arquivada, e nenhum texto novo entra por essa via.

**Léxico (2026-11-20).** As glosas das notas de João 1–4 foram conferidas com os Strong do Dodson (CC0) e com o Abbott-Smith (domínio público). Cobriram-se as formas isoladas em itálico (cerca de 300): as que têm lema no Abbott-Smith foram comparadas com a definição breve do Dodson, e as formas flexionadas (aoristos, imperfeitos, particípios) foram conferidas pelo radical no Abbott-Smith. Não foram conferidas uma a uma as expressões de mais de uma palavra, nem as glosas de tradução que não são lemas. Nenhuma nota foi alterada por esta conferência, porque nenhuma glosa contradisse os léxicos.

## 4. Duas etapas transversais

### Preparação e calibração — antes da fase 1 (histórico)

1. Rever Salmos 23 como amostra de poesia; em seguida, iniciar Filemom como primeiro livro completo. Romanos 12:2 continua disponível como amostra de prosa para uma etapa posterior, em momento a combinar. O responsável avalia o tom, o tamanho das notas e as convenções.
2. Definir a política de títulos, pronomes, itálicos, variantes e nomes divinos. Identificar afirmações exegéticas que precisam de revisão.
3. Guardar capítulos estruturalmente completos no formato JSON que a CLI valida, sem chamadas a APIs de IA, e registrar em metadados separados a aprovação editorial e a revisão especializada. O compilador valida os limites dos estados declarados e os copia para os módulos, mas não comprova as revisões nem exige aprovação; amostras isoladas e capítulos incompletos não entram nos módulos.
4. Preparar prévias MyBible claramente identificadas como parciais e sujeitas a revisão. A prévia atual contém Filemom 1 e João 1–4; os dois módulos foram lidos por um leitor independente, mas ainda não foram testados visualmente no MyBible.

**Situação técnica atual (2026-11-20):** `gerar_bee.py --status` e `--compilar` funcionam offline sobre JSON válidos. O repositório não tem workflows de GitHub Actions, e a produção automática por provedores de IA foi retirada. O compilador aceita apenas capítulos completos e exige capítulos consecutivos desde o capítulo 1 de cada livro. Por isso, capítulos isolados devem ficar em rascunhos separados, sem serem apresentados como módulos compiláveis.

### Revisão final e publicação — após a fase 8

Revisar uniformidade editorial e teológica, códigos Strong, transliterações, variantes, títulos, numeração, licenças e atribuições. Conferir as duas bases SQLite, testar os módulos no MyBible e submeter o material a revisão especializada. Corrigir ou manter explicitamente identificadas todas as lacunas antes de qualquer publicação; cobertura estrutural não significa revisão completa.

## 5. Oito fases de produção propostas

A ordem pode ser alterada pelo responsável. Filemom é proposto como primeiro livro completo por ter um capítulo: permite testar o fluxo e os módulos antes de avançar para livros longos. As contagens abaixo cobrem cada livro exatamente uma vez.

| Fase | Livros e ordem proposta | Livros | Capítulos |
|---|---|---:|---:|
| 1. Piloto e Evangelho | Filemom; João | 2 | 22 |
| 2. Evangelhos e Igreja nascente | Marcos; Mateus; Lucas; Atos | 4 | 96 |
| 3. Origens | Gênesis; Êxodo | 2 | 90 |
| 4. Poesia e sabedoria | Salmos; Provérbios; Jó; Eclesiastes; Cânticos | 5 | 243 |
| 5. Cartas restantes | Romanos; 1 e 2 Coríntios; Gálatas; Efésios; Filipenses; Colossenses; 1 e 2 Tessalonicenses; 1 e 2 Timóteo; Tito; Hebreus; Tiago; 1 e 2 Pedro; 1, 2 e 3 João; Judas | 20 | 120 |
| 6. Lei e história | Levítico; Números; Deuteronômio; Josué; Juízes; Rute; 1 e 2 Samuel; 1 e 2 Reis; 1 e 2 Crônicas; Esdras; Neemias; Ester | 15 | 346 |
| 7. Profetas | Isaías; Jeremias; Lamentações; Ezequiel; Daniel; Oseias; Joel; Amós; Obadias; Jonas; Miqueias; Naum; Habacuque; Sofonias; Ageu; Zacarias; Malaquias | 17 | 250 |
| 8. Apocalipse | Apocalipse | 1 | 22 |
| **Total** | | **66** | **1.189** |

## 6. Ciclo de cada passagem, capítulo e livro

1. **Consultar em paralelo:** reunir original, edição comparativa, léxico, contexto e evidências de variantes por capítulo ou unidade de sentido. Registar versões e dificuldades; tarefas independentes de pesquisa e verificações podem correr simultaneamente, mas as edições do mesmo JSON são integradas sequencialmente.
2. **Preparar:** redigir tradução e comentários por versículo, sem interromper para pedir aprovação a cada bloco. Identificar suplementos e distinguir questões gramaticais de variantes de manuscritos.
3. **Conferir e registrar:** revisar a passagem em contexto e confrontar a redação com as fontes; distinguir os trechos aprovados dos textos novos e anotar as dúvidas e limitações. Checagens automáticas de números, códigos, HTML e colchetes ajudam, mas não verificam a exegese ou a evidência histórica.
4. **Guardar:** conservar fontes, histórico e estados de revisão separados. Um capítulo só entra como estruturalmente completo quando todos os versículos estiverem presentes e validados; isso não significa aprovação editorial.
5. **Compilar e conferir:** compilar capítulos completos consecutivos a partir de 1; comparar textos, comentários, metadados e integridade dos dois SQLite com os JSON. A prévia continua identificada como rascunho; o teste visual no MyBible é uma etapa separada.
6. **Revisar o livro:** conferir consistência do vocabulário, referências cruzadas, numeração e títulos. A revisão editorial e a revisão especializada são registadas separadamente.

Manter amostras isoladas e capítulos incompletos fora dos capítulos estruturalmente completos. O compilador copia os estados declarados e verifica seus intervalos, mas não comprova que a revisão tenha ocorrido.

## 7. Pontos conhecidos para a calibração

- Em Romanos 12:2, a passiva descreve a transformação recebida, mas a forma verbal sozinha não identifica o agente nem estabelece automaticamente a ideia de “rendição”; tais afirmações devem ser apresentadas como interpretação. O SBLGNT não traz explicitamente “de vocês” após “mente”; o TR consultado traz o possessivo. O uso de “sua” pode ser uma opção contextual, com a diferença assinalada.
- Em Salmos 23:6, a expressão final se refere literalmente à extensão ou duração dos dias. Uma leitura de comunhão eterna pode ser discutida teologicamente, sem ser apresentada como sentido gramatical inevitável. A classificação de וְשַׁבְתִּי como “habitar” ou “voltar” também requer revisão especializada; uma diferença de análise não demonstra por si só uma variante de manuscritos.
- O WLC utilizado não fornece um correspondente para Neemias 7:68 na numeração escolhida. Antes da publicação, essa posição exigirá uma fonte suplementar autorizada e revisão; não será preenchida por suposição.
- Datas de conclusão dependem do tamanho das passagens, da profundidade das notas e do ritmo de revisão. Medir o andamento após o piloto, em vez de prometer um prazo sem base.

## Próxima decisão

Continuar João a partir de **19:13** (o capítulo 19 tem 38 versículos; os
primeiros 12 já estão guardados), sem pedir aprovação a cada bloco e
actualizando as prévias quando o capítulo fechar. João 5:4 não consta no SBLGNT
fixado e exige tratamento explícito da versificação e da evidência se for
apresentado como suplemento. Os textos novos continuam provisórios e precisam
de revisão especializada. A ordem das fases posteriores e o momento da revisão
de Romanos 12:2 podem ser ajustados.
