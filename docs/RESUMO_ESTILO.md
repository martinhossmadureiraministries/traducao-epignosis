# Resumo de estilo e tradução — regras vigentes para o próximo livro

**Data:** 20 de novembro de 2026. **Fonte:** `docs/ESTILO_BEE.md` (guia completo e calibrações, que continua a ser a referência histórica) e `docs/EDITORIAL.md`. Este resumo junta só o que vale hoje, para quem vai traduzir ou rever o próximo livro. Em caso de conflito, prevalece a decisão mais recente do responsável registada em `docs/EDITORIAL.md`.

## 1. A voz

- Clareza para ler, cadência para proclamar, profundidade para estudar. O impacto vem do texto, não de frases acrescentadas.
- Escrever para o ouvido: frases que se leem em voz alta. Dividir frases longas quando a lógica não muda.
- Traduzir a unidade (parágrafo, discurso, argumento) antes de fechar os versículos. Identificar quem fala, a quem e com que propósito.
- Não combinar frases de NVT, KJA, A Mensagem ou ARC, nem usá-las como ponto de partida. A redação nasce do original.
- Almeida e KJV são referências de cadência e de vocabulário tradicional, não normas. Manter o termo tradicional quando o contexto sustenta o peso (por exemplo, «consumado»), e trocá-lo quando o corrente comunica melhor (por exemplo, «paciente» no lugar de «longânimo»).
- Não converter uma imagem clara numa explicação, nem uma interpretação debatida numa afirmação do versículo.

## 2. Notas

- Quando há nota, um parágrafo de prosa, sem rótulos («Análise Léxica», «Síntese Exegética») e sem níveis de certeza. A nota é opcional: escreve-se onde há algo a explicar (`docs/EDITORIAL.md` §3). É obrigatória com acréscimo em itálico ou colchetes simples no texto. Colchetes só simples, nunca `[[ ]]`.
- O grego vai em itálico, com a transliteração entre parênteses na primeira ocorrência. Minúsculas nas formas gregas (*huios*).
- A nota traz a palavra original decisiva, a razão da escolha e a alternativa rejeitada. Não traz oração nem aplicação devocional.
- **Crítica Textual:** parágrafo próprio, uma só vez por versículo, e só quando o aparato ou a colação regista variante. Cita as siglas (WH, Treg, NA28, RP) e as testemunhas que diferem, diz o que a variante muda e porque a base foi seguida. Sem sinais de aparato (⸀ ⸁ ⸂ ⸃).
- **Só se cita o que se colacionou.** Não se diz «o Sinaiticus lê X» sem colação. Edição impressa não é manuscrito, e tradução moderna não é evidência textual.
- **NIV** só aparece na Crítica Textual, quando diverge da base: «a NIV segue essa leitura por escolha de tradução». Nunca como testemunha.
- A nota não contradiz o versículo e não inventa etimologias, derivadas, edições consultadas ou revisões que não aconteceram.
- Verificar a nota contra a colação: `scripts/verificar_notas_colacao.py`.

## 3. Itálico e colchetes

- **Itálico (`<i>…</i>`)** só para palavras acrescentadas sem correspondência no grego, por clareza.
- **Colchetes simples** só quando a evidência dos manuscritos pede (a base lê uma palavra que a maioria não tem). A nota explica a evidência e a leitura alternativa. Nunca colchetes duplos. Exemplo: Judas 1:5, «[Jesus]».
- «[Selá]» segue a convenção pública, à parte: no texto, `<i>[Selá]</i>` no MyBible, sem pronúncia.
- Rubricas (títulos de salmos e semelhantes): linha própria em itálico na leitura; `<i>` no fim do texto no JSON.

## 4. Pontuação e maiúsculas

- Versículo que continua a frase anterior: termina em vírgula ou ponto e vírgula; o seguinte começa em minúscula.
- Versículo que abre frase nova: termina em ponto; o seguinte começa em maiúscula.
- Nunca minúscula depois de ponto, nem maiúscula depois de vírgula, e nenhum versículo fica sem pontuação final.
- **SENHOR** em maiúsculas só para o Tetragrama יהוה no hebraico. No grego do NT, «Senhor».

## 5. Português europeu (AO90)

- Acordo de 1990, em toda a edição, sem misturar formas de 1945: «ação», «aspeto», «atividade», «ato», «receção», «ativa», «rutura», «leãozinhos».
- Termos fixos: «connosco», «de facto», «registo», «secção», «aspeto».
- Nas notas: «leem» (não «lêm»), «regista» (não «registra»). Formas brasileiras só dentro de citação, entre aspas.
- **Ênclise** como em Portugal: «metendo-se», «admoestem-no», «gloria-se». Próclise em início de oração («se metendo») está vetada.
- **Progressivo** com «estar a + infinitivo» («estava a batizar»). «Está fazendo» é brasileiro. Um progressivo com gerúndio já aprovado mantém-se como variante.
- Falsos positivos do verificador ortográfico (manter): efrateus, moabitas, pretório, anártricos, paulinas, contacto, facto, secção, transliterada, bem-estar, meio-dia, jumentinho, denários, nardo, galileus, aloés, transpassaram.

## 6. Termos e nomes

- **Espírito:** «Parácletos» (nominativo), *parákletos*; «Parácleton» (acusativo), *parákleton*. Não se usa «Paráclito».
- **ἐπίγνωσις:** «pleno conhecimento» ou «conhecimento pleno», só no substantivo e no corpo do texto. Não estender a γνῶσις nem aos verbos. A nota explica a função no contexto. (1 Timóteo 2:4 e Efésios 4:13 já ajustados.)
- **Nomes próprios aprovados:** Getsêmani, Gólgota, Arimateia, Clopas, Madalena, Caifás, Pilatos, Anás, Cedrom, Malco, Barrabás. Usar sempre estas formas.
- **Jesus ou o Senhor** (4:1 de João): «Jesus» no texto, «o Senhor» na nota.
- **Gente / pessoas:** «gente» para um conjunto que se ouve ou vê; «pessoas» para indivíduos contados. Não trocar «povo» por «gente» quando está em causa a identidade de uma comunidade.
- **Famílias lexicais coerentes:** uma família grega tem uma família portuguesa no livro inteiro. Um só adversativo por frase.
- **Uniformidade só onde o grego é igual.** A saudação de Filemom («Deus, nosso Pai») tem *πατρὸς ἡμῶν* e a de 2 Tessalonicenses («Deus Pai») não tem. Uniformidade fabricada é infidelidade.

## 7. πᾶς

- Com artigo grego, pode totalizar («todos os que creram»).
- Anártrico distribui (cada desejo, cada obra). A distinção regista-se na nota, não no artigo.
- Em português europeu, o artigo depois de «todo» no singular é obrigatório e não traduz o artigo grego: «toda a obra de fé», «todo o irmão».
- **Não aplicar** a regra antiga de suprimir o artigo para marcar o anártrico (revertida em 20/11/2026).

## 8. Livros já aprovados

- Não reescrever uma forma já aprovada só para seguir uma regra nova. A regra nova aplica-se ao texto novo; a correção de texto aprovado exige decisão do responsável, registada na nota do bloco com o motivo.

## 9. Processo para cada livro

1. Ler o original (SBLGNT) e a colação do livro (`docs/colacao/`) antes de redigir. Confrontar as divergências com a Crítica Textual.
2. Redigir texto e notas. Conferir cada versículo com o SBLGNT e com as palavras citadas nas notas.
3. Correr os verificadores: `scripts/verificar_dados.py`, `scripts/verificar_estilo.py`, `scripts/verificar_convencoes_notas.py`, `scripts/verificar_notas_colacao.py --dados edicoes/nova/livros_json --colacao docs/colacao/<livro>.json`, e `python3 -m unittest discover -s tests`.
4. Listar para o responsável as passagens que precisam de decisão, com a leitura da base e a alternativa. **Não aprovar nem marcar aprovação em nome dele.**
5. Regenerar a leitura (`scripts/gerar_leitura_livro.py --livro N --saida edicoes/nova/<LIVRO>.md`) e atualizar `docs/ESTADO.md`.
6. Revisão especializada: só por especialista externo (hebraísta, grecista, crítico textual ou teólogo). Revisão do ministério: Martinho S. S. Madureira Ministries. Nenhuma das duas é feita pelo agente nem pelo responsável.

## 10. Ordem das cartas (das menores para as maiores)

Tamanho em versículos (catálogo):

| Ordem | Livro | Versículos |
|---|---|---|
| 1 | 2 João | 13 |
| 2 | 3 João | 14 |
| 3 | Filemom | 25 |
| 4 | Judas | 25 |
| 5 | Tito | 46 |
| 6 | 2 Tessalonicenses | 47 |
| 7 | 2 Pedro | 61 |
| 8 | 2 Timóteo | 83 |
| 9 | 1 Tessalonicenses | 89 |
| 10 | Colossenses | 95 |
| 11 | Filipenses | 104 |
| 12 | 1 Pedro | 105 |
| 13 | 1 João | 105 |
| 14 | Tiago | 108 |
| 15 | 1 Timóteo | 113 |
| 16 | Hebreus | 303 |
| 17 | Apocalipse | 404 |

Já com edição nova: 2 Pedro, 2 João, 3 João, Filemom, Judas, Tito, 2 Tessalonicenses, 1 Tessalonicenses, Filipenses. Em aberto nesta lista: 2 Timóteo, Colossenses, 1 Pedro, 1 João, Tiago, 1 Timóteo, Hebreus e Apocalipse. Gálatas, Efésios, Romanos e os dois Coríntios também estão por fazer e entram depois das cartas menores, segundo a mesma regra de tamanho.

**Prioridade para o que define o estilo:** 2 Pedro, por causa da decisão pendente sobre ἐπίγνωσις, e depois Colossenses, que também deve usar ἐπίγνωσις (a confirmar na colação antes de redigir). Ambos testam a regra de termos fixos antes de Tiago e 1 Pedro, que dependem menos de termos já fixados.

## 11. Decisões pendentes que afetam o próximo livro

- **2 Pedro — ἐπίγνωσις em 1:2, 1:3, 1:8 e 2:20:** decidido pelo responsável: alternar «pleno conhecimento» e «conhecimento pleno» conforme a construção. Colação: 60 de 61 versículos têm alguma testemunha divergente, sobretudo ortográfica; a colação bruta não decide sozinha.
- **Colchetes por verificar:** 5:4 e 7:53–8:11 (João).
- **Por confirmar na fonte:** «προβάτια» em 21:16–17 é citado para WH na colação, não no aparato SBLGNT.
