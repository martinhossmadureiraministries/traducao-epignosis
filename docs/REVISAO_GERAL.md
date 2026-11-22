# Revisão geral do projeto — primeira varredura

**Estado: só anotação.** Nesta varredura não se alterou nenhum texto, nota, script ou dado. Os achados abaixo serão resolvidos depois de a lista ser lida e de as decisões da secção 5 serem tomadas. Só depois disso se segue para o próximo livro ou carta.

Este ficheiro é o registo de referência da revisão. Quando um achado for resolvido, marca-se aqui com a data e o commit.

---

## 1. Âmbito e método

**Âmbito.** Tudo o que já existe no repositório:

- a edição nova, `edicoes/nova/livros_json/` (17 livros e cartas);
- as leituras em Markdown, `edicoes/nova/*.md` (incluindo cinco livros que só existem em MD);
- os pilotos, `edicoes/piloto/` (MD e cópias em `dados/`);
- a linha legada, `livros_json/` (Mateus, Marcos, João, Filemom).

O livro em curso é João. A varredura cobre o que já foi criado antes de João e o que já existe depois dele (Filipenses, 1 e 2 Tessalonicenses, Tito, Filemom, 2 e 3 João, Judas), porque também está no repositório.

**Métodos.**

1. Verificadores existentes: `verificar_estilo`, `verificar_dados`, `verificar_documentacao`, `verificar_notas_colacao`, `verificar_ortografia` (este só correu depois de instalar `pyspellchecker` num ambiente temporário fora do repositório) e a suíte de testes (`unittest`).
2. Comparação JSON ↔ MD de leitura, versículo a versículo, para todos os livros que têm os dois.
3. Grego: o campo `base` da colação contra o SBLGNT no pin `d7f35ad`, para os seis livros com colação e para João 1–4.
4. Grego nas notas dos livros sem colação (Filipenses, 1 Tessalonicenses), como lista de candidatos a verificar à mão.
5. Consistência de estados entre JSON, MD, `LOTE_*.md`, `ESTILO_BEE.md` e `ESTADO.md`.
6. Higiene do texto: marcas `«»`, `<i>`/`<b>`, espaços, aspas, artefactos.
7. Inventário de ficheiros, links de leitura e artefactos no Git.

**Limites.** Não se fez leitura linha a linha de cada versículo nesta varredura (ver secção 7). Os achados vêm de verificações automáticas e de comparações entre fontes. Os achados mais graves foram confirmados no texto.

---

## 2. Inventário

Contagens com a numeração tradicional (KJV), que é a que a casa segue. As contagens da edição nova batem com ela.

| Livro | Onde está | Vv. | Estado no JSON | Leitura MD | Grego vs. fonte | Achados |
|---|---|---|---|---|---|---|
| Rute | nova | 85 | aprovado editorialmente | `RUTE.md` = JSON | sem colação (AT) | M4 |
| Jonas | nova | 48 | aprovado editorialmente | `JONAS.md` = JSON | sem colação (AT) | — |
| Miqueias | nova | 105 | aprovado editorialmente | `MIQUEIAS.md` = JSON | sem colação (AT) | — |
| Naum | nova | 47 | aprovado editorialmente | `NAUM.md` = JSON | sem colação (AT) | — |
| Habacuque | nova | 56 | aprovado editorialmente | `HABACUQUE.md` ≈ JSON | sem colação (AT) | M4 |
| Sofonias | nova | 53 | aprovado editorialmente | `SOFONIAS.md` = JSON | sem colação (AT) | — |
| Ageu | nova | 38 | aprovado editorialmente | `AGEU.md` = JSON | sem colação (AT) | — |
| Malaquias | nova | 55 | aprovado editorialmente | `MALAQUIAS.md` = JSON | sem colação (AT) | — |
| Oseias | **só MD** | 197 (14 caps.) | — (MD: aprovada editorialmente; revisão especializada pendente) | `OSEIAS.md` | — | **A7** |
| Joel | **só MD** | 73 | — (MD: aprovada editorialmente; revisão especializada pendente) | `JOEL.md` | — | **A7** |
| Amós | **só MD** | 146 | — (MD: não aprovado) | `AMOS.md` | — | **A7** |
| Obadias | **só MD** | 21 | — (MD: não aprovado) | `OBADIAS.md` | — | **A7** |
| Zacarias | **só MD** | 211 | — (MD: não aprovado) | `ZACARIAS.md` | — | **A7** |
| Filipenses | nova | 104 | aprovado editorialmente (voz) | `FILIPENSES.md` = JSON | sem colação; 7 candidatos (M12) | M12 |
| 1 Tessalonicenses | nova | 89 | **rascunho** (LOTE_06: aprovada) | `1_TESSALONICENSES.md` = JSON (cabeçalho: não aprovada) | sem colação; 3 candidatos (M12) | **A2**, M12 |
| 2 Tessalonicenses | nova | 47 | **rascunho** (LOTE_06: aprovada) | `2_TESSALONICENSES.md` = JSON (cabeçalho: não aprovada) | 47/47 | **A2**, M1 |
| Tito | nova + piloto | 46 | rascunho (nota: piloto aprovado) | `edicoes/piloto/TITO.md` | 46/46 | **A1**, **A2** |
| Filemom | nova + piloto | 25 | rascunho (nota: piloto aprovado) | `edicoes/piloto/FILEMOM.md` = JSON | 25/25 | **A2**, **A9** |
| Judas | nova + piloto | 25 | rascunho (nota: piloto aprovado) | `edicoes/piloto/JUDAS.md` | 25/25 | **A1**, **A2** |
| 2 João | nova + piloto | 13 | rascunho (nota: piloto aprovado) | `edicoes/piloto/2_E_3_JOAO.md` = JSON | 13/13 | **A2**, M8 |
| 3 João | nova + piloto | 14 | rascunho (nota: piloto aprovado) | idem | 14/14 em bruto; 1:14 a confirmar (M15) | **A2**, M8, M15 |
| João | nova (caps. 1–4 completos; 5 em curso) | 166 (caps. 1–4) | rascunho | sem MD (em curso) | 166/166 (1–4) | M9, M10 |
| Mateus (legado) | `livros_json/` | 395 (12/28 caps.) | sem campo de estado | — | não verificado | **A4** |
| Marcos (legado) | `livros_json/` | 678 (16/16) | sem campo de estado | — | não verificado | **A4** |
| João (legado) | `livros_json/` | 879 (21/21) | estado de capítulos; 17 decisões abertas | — | não verificado | **A4**, M10, M11 |
| Filemom (legado) | `livros_json/` | 25 (1/1) | 1:1–3 aprovados originalmente; 1:2 com alterações pendentes; revisão especializada pendente | — | não verificado | M11 |

**Leitura da tabela.** Os cinco livros de piloto e a carta 2 Tessalonicenses estão em `rascunho` no JSON, mas as notas e os lotes dizem que foram aprovados (voz). Os estados têm de ser alinhados com o que foi decidido.

---

## 3. Achados de gravidade alta (A)

Os itens A afetam texto aprovado, o que o leitor recebe, ou a confiança nos verificadores.

### A1 — Texto aprovado alterado sem reaprovação (Tito e Judas)

**Onde.** `edicoes/nova/livros_json/630_Tito.json` e `720_Judas.json`, comparados com `edicoes/piloto/dados/` e com os MD do piloto (`edicoes/piloto/TITO.md`, `JUDAS.md`).

**O que.** O texto da edição nova não é o do piloto aprovado:

- **Judas 1:7** (reescrita, não é só pontuação): piloto «…de modo semelhante a esses. Elas ficam como exemplo…» → nova «…tal como aqueles. Estão postas como exemplo…».
- **Tito 1:13, 2:7, 2:9**: acrescentada vírgula no fim do versículo.
- **Tito 2:14, 3:1, 3:2**: acrescentado o artigo (ex.: «toda boa obra» → «toda a boa obra»; «toda mansidão» → «toda a mansidão»). Não há registo de reaprovação. Falta confirmar se a mudança foi intencional.
- **Tito 3:3** (troca de palavra, não de artigo): «de todo tipo» → «variados».

**Por que é grave.** Os pilotos são o texto já aprovado que serve de ponto de partida. Mudar o texto aprovado sem nova aprovação quebra essa regra. Além disso, o leitor do MD do piloto lê uma coisa e o módulo compilado tem outra.

**Proposta.** Decidir qual é o texto de referência (D1). Depois, ou se restaura o piloto e se marca como aprovado, ou se aceita a versão nova e se pede reaprovação registada.

### A2 — Estados contraditórios entre JSON, MD, lotes e notas

| Livro | JSON (`review`) | Outro registo | Conflito |
|---|---|---|---|
| Tito, Judas, 2 João, 3 João, Filemom (nova) | `rascunho` | nota do bloco: «Texto do piloto aprovado pelo responsável»; `LOTE_01` e `LOTE_05`: «voz aprovada» | status não reflete a aprovação |
| 1 Tessalonicenses | `rascunho` | `LOTE_06`: «leitura integral aprovada pelo responsável» | `LOTE_06` diz aprovada; JSON e MD dizem não |
| 2 Tessalonicenses | `rascunho` | `LOTE_06`: aprovada; `LOTE_05` e `ESTADO.md`: «aguarda releitura»; cabeçalho MD: «não aprovação editorial» | três versões diferentes |

**Nota.** A decisão registada na sessão é que a aprovação editorial de 1 e 2 Tessalonicenses fica registada como tal, com a revisão especializada pendente (D2). Se essa decisão vale, o JSON e os cabeçalhos MD estão desatualizados. Não se altera nada até D2 ser respondida.

### A3 — Artefactos obsoletos e distribuíveis no repositório

- **`entregas/BEE-previa.zip`** — datado de 17/11/2026 (antes da edição nova). Contém Filemom e João 1–18 (806 textos), anteriores à edição nova. Se for distribuído, leva texto antigo, incluindo João 1–4 antes da correção de PR #68.
- **`docs/arquivo/BEE-gerador.zip`** — pacote histórico, com aviso de documento histórico em `docs/arquivo/README.md`.

A política do projeto diz que ZIP só se cria a pedido expresso e que o responsável o põe na `main`. Não se verificou quem adicionou os ZIPs: o clone é raso (um único commit), por isso o histórico não o mostra.

**Proposta.** Decidir se ficam, se saem ou se são marcados como obsoletos (D5). Em qualquer caso, nenhum ZIP é gerado sem pedido.

### A4 — Linha legada com «vós» e defaults que a apontam

- **330 versículos** da linha legada têm formas proibidas pela lista negra (`vos`, `vós`, `vossa`, `tendes`, `sois`): Mateus 96, Marcos 76, João 158. Ver `verificar_estilo.py --dados livros_json`.
- **Os defaults apontam para a legada.** `gerar_bee.py --dados` e `verificar_dados.py --dados` usam `livros_json` por defeito (confirmado nos scripts). O workflow `bee-autopiloto.yml` (linha 145) corre `verificar_dados.py --minimo 18` sem `--dados`, ou seja, na legada.
- O `EDICAO_NOVA.md` (linha 51) diz que a legada «não é tocada» e que se retoma em João 19:13. O JSON tem os 21 capítulos completos (ver M10).

**Proposta.** Mudar os defaults para a edição nova (ou exigir `--dados` explícito), e decidir o destino da legada (D4).

### A5 — O verificador de ortografia saltava em silêncio

`verificar_ortografia.py` imprime «pyspellchecker não instalado; verificação ortográfica saltada» e **sai com código 0**. No workflow `bee-nova-edicao.yml` (linhas 232–241) é um passo de «alerta», que não bloqueia a execução. Na prática nunca produziu verificação.

Depois de o instalar num ambiente temporário, correu com 159 versículos sinalizados. A maioria são falsos positivos (nomes e gentílicos como moabita, amonitas, galileus; termos técnicos como qere, anártrico, hamartia; citações do KJV/ESV). Os reais estão em M5 e B1.

**Proposta.** O verificador tem de falhar quando a dependência falta (ou a dependência tem de ser instalada no workflow). Ver Fase 3.

### A6 — Quarentena obsoleta, versionada no Git

`edicoes/nova/livros_json/.bee/` está versionado (`quarentena.json`, `estado.json`, `revisoes.json`, `diario.md`). O `.gitignore` só ignora `livros_json/.bee/` na raiz (verificado com `git check-ignore`): o caminho `edicoes/nova/livros_json/.bee/` não é ignorado.

- `quarentena.json` tem 31 entradas: **24 `pendente`** e 7 `chumbado-estilo`. As 24 pendentes são de João 2 (3 entradas) e 4 (21 entradas). Os exemplos conferidos (2:7, 2:17, 2:21, 4:32–36) **já têm texto** no JSON novo. A lista completa tem de ser fechada na Fase 2.
- `estado.json` mostra provedores «exaustos» de 19/11.

**Proposta.** Fechar as entradas resolvidas, e decidir se o estado operacional fica versionado (D11).

### A7 — Cinco livros existem só em Markdown

Oseias (197 vv., 14 capítulos), Joel (73), Amós (146), Obadias (21) e Zacarias (211) têm leitura MD (`edicoes/nova/*.md`) e contagens que batem com a numeração, mas **não têm JSON na edição nova** nem histórico no Git. Por isso:

- não entram no compilador nem no módulo;
- o `LOTE_03.md` diz que Oseias e Joel estão «aprovados editorialmente após leitura integral», mas não há dados que o provem;
- o marco «27 livros do NT / AT em curso» não pode ser verificado com estes livros fora dos dados.

**Proposta.** Decidir se se criam os JSON a partir dos MD (D3). Para os não aprovados (Amós, Obadias, Zacarias), a criação não altera o estado.

### A8 — Verificadores com falsos positivos e falsos negativos

| Ferramenta | Problema | Efeito |
|---|---|---|
| `verificar_notas_colacao.py` | aplica a regra de `[[ ]]` **também ao texto** | falso positivo em Judas 1:5 e Filemom 1:2, onde `[[ ]]` é a marca correta de leitura assinalada |
| `verificar_notas_colacao.py` | só reconhece a sigla `Treg`, não o nome «Tregelles» que as CT usam | falso positivo em Filemom 1:6, Tito 2:4, 2 João 1:5 |
| `verificar_notas_colacao.py` | não corre em Filipenses nem em 1 Tessalonicenses (sem colação) | notas sem verificação das variantes |
| `verificar_ortografia.py` | salta sem erro (A5) | gate falso |
| `verificar_estilo.py` | não cobre (a confirmar) a regra de tratamento (`tu`/`vocês`, M6) nem o uso do itálico no grego (M7) | regras escritas sem guarda |
| `verificar_dados.py` / `gerar_bee.py` | padrão `livros_json` (A4) | verificação e compilação na pasta errada |

Os testes existentes não cobrem (a confirmar) estes casos. Ver Fase 3.

### A9 — `[[ ]]` com nível A em Filemom 1:2

A CT de Filemom 1:2 declara **nível A** (a variante é bizantina e as edições críticas apoiam a base). Mas o texto marca «nossa `[[irmã]]`», e o protocolo (`docs/CRITICA_TEXTUAL.md`, §5.1) reserva `[[ ]]` para «leitura assinalada: adotada pela base mas ausente noutros testemunhos». As duas marcas não batem entre si. Em Judas 1:5, pelo contrário, o `[[Jesus]]` vem com nível C, e isso está coerente.

**Proposta.** Ou se retira `[[ ]]` (com nível A), ou se baixa o nível para B e se explica (D8). Nota: o verificador (A8) não distingue este caso do de Judas 1:5, onde o `[[ ]]` está em texto de nível C.

---

## 4. Achados médios (M) e baixos (B)

### M1 — 2 Tessalonicenses: notas e CT por corrigir

- `verificar_notas_colacao.py` (com `--dados edicoes/nova/livros_json/600_2_Tessalonicenses.json --colacao docs/colacao/2_Tessalonicenses.json`): **33** avisos. **20** notas com história de versão ou resíduo de processo (15 «nota de redação que conta uma versão anterior», 5 «história de correções no comentário»); **9** CT que não citam uma sigla do aparato (NA28, Treg, WH, RP); **4** CT que falam de variante sem entrada no aparato (1:3, 1:12, 3:3, 3:16). Nota: o resumo de sessão anterior dizia 15; esta corrida dá 33. A divergência fica por explicar (ver D12 se for de método).
- Estas notas vêm de `scripts/regenerar_2ts.py`. Editar só o JSON faz o teste de reprodutibilidade falhar (`test_critica_textual.LivroRegeneradoTest`), por isso a correção tem de ir para o script.
- Os quatro avisos «sem entrada no aparato» têm de ser lidos contra a colação antes de se decidir se é a CT ou o verificador que está errado.

### M2 — Tito e Judas: histórico já retirado

Na sessão anterior retiraram-se três frases de histórico em Tito e uma em Judas, com `scripts/limpar_historico_notas.py`. Revisado em amostra: a justificação ficou. Os textos continuam sujeitos a A1.

### M3 — «Nota de redação» (legítima)

A secção «Nota de redação» é legítima. Só o histórico de correções dentro dela é resíduo. Sem ação; o verificador já distingue os dois casos (M1).

### M4 — Habacuque 3:19: rubrica montada de forma diferente

No JSON, «*Ao mestre de música. Com os meus instrumentos de cordas.*» está dentro do texto do versículo, em itálico. No MD, a mesma rubrica está numa linha própria. O conteúdo é o mesmo, mas a convenção não está escrita. Também em Rute e Jonas não há rubricas, pelo que a decisão é sobre a regra, não sobre um caso isolado (D10).

### M5 — Ortografia real (pré-Acordo e hesitação)

- `acção` (João 2:13, comentário) e `directo` (João 2:16, comentário): grafias pré-Acordo. A norma de `modelos/estilo_bee.json` (campo `ortografia`) tem de ser confirmada antes de as trocar por «ação» e «direto».
- **`lêem` (108) e `leem` (26)** convivem nas notas. A norma diz «sem hesitação entre normas». Escolher uma forma e aplicar em todos os livros.
- `facto` (2Ts 1:6, 1:11, 3:8, 3:10) é a forma usada em PT-PT e em PT-AO. Não é erro e não entra na lista de correções.
- `receção` está na forma correta. Sem ação.

### M6 — Tratamento de 2.ª pessoa: regra escrita diferente da prática

A regra escrita (`modelos/estilo_bee.json`) diz que «tu» só aparece em oração direta a Deus. A prática aprovada é outra: há «tu» em perguntas e diálogo a uma pessoa (ex.: Rute 3:9; Jonas 1:10; João 1:19–25, segundo a sessão anterior).

**Medido** (com fronteiras de palavra, nos JSON da edição nova): capítulos com «tu» e «vocês» no mesmo capítulo: Rute 2, Rute 4, Jonas 1, Habacuque 1, Malaquias 2, João 1, João 3, João 4, Filemom 1 (9 capítulos). A sessão anterior dava 14 capítulos aprovados, com outro critério (incluía a legada). Cada caso tem de ser lido: a mudança de falante pode ser legítima.

**Proposta.** Decidir a regra (D6) e só depois auditar os capítulos listados.

### M7 — Grego: convenção de itálico não escrita e não uniforme

Palavras gregas fora de `<i>` (inclui as leituras da CT entre «»): Filipenses ~303, 1 Tessalonicenses ~103, Tito ~167, Judas ~94, Filemom ~96, 2 João ~56, 3 João ~56, João ~796. Em 2 Tessalonicenses o grego vai em `<i>` (83 casos) e em Filemom e Judas há alguns casos. A regra escrita proíbe o **negrito** no grego, mas não prescreve o itálico.

**Proposta.** Decidir a convenção (D7) e aplicá-la de forma uniforme.

### M8 — Pilotos: 2 e 3 João num só ficheiro, e cópias duplicadas

- `edicoes/piloto/2_E_3_JOAO.md` junta dois livros. A regra do projeto é «cada livro com o seu link de leitura».
- `edicoes/piloto/dados/` tem cópias dos JSON dos pilotos que **diferem** da edição nova (ver A1). Não há regra escrita sobre qual é a fonte.

### M9 — João: leitura por fazer em 5:1 e estado do capítulo 5

João 5 tem um versículo em `in_progress` (5:1), com marcador `[Versículo pendente …chumbado-estilo]`. Não entra nos capítulos completos, o que é correto. Fica para o plano do livro.

### M10 — João legado: decisões abertas e documentação desatualizada

- O JSON legado tem **17 `pending_decisions`** em aberto. A primeira é «Rever editorialmente e submeter o capítulo completo a revisão especializada». Há ainda decisões sobre 1:3–4, 1:5–18, 1:24–34 (incluindo a leitura «Escolhido/Filho de Deus» em 1:34), 2:4–20, 3:3–36, e outras.
- `EDICAO_NOVA.md` diz que a legada «se retoma em João 19:13». O JSON tem os 21 capítulos completos (879 versículos, que é a contagem tradicional com 5:4 e 7:53–8:11). A frase está desatualizada ou quer dizer outra coisa; tem de ser esclarecida.

### M11 — Livros duplicados em duas edições

- **Filemom**: legado (`livros_json/640_Filemom.json`, aprovado pelo responsável) e nova (`edicoes/nova/livros_json/640_Filemom.json`, rascunho), com o mesmo número. Qual é o canónico? (D9)
- **João**: legado (21 capítulos) e nova (1–4 completos, 5 em curso). A nova substitui a legada em 1–4? E em 5–21? (D9)

### M12 — Filipenses e 1 Tessalonicenses: grego sem colação

Sem colação, não há verificação automática das variantes nem do grego. Usou-se o SBLGNT (pin `d7f35ad`) para uma lista de candidatos: palavras gregas nas notas que não aparecem no versículo indicado.

- **Filipenses** (7 candidatos, em 135 palavras): 1:3 ποιούμενος, 1:7 κοινωνία, 1:22 σάρξ, 2:7 κένωσις, 2:22 δοῦλοι, 3:2 περιτομή, 4:23 πάντων. Muitos devem ser remissões a versículos vizinhos ou lemas (ex.: 2:7 κένωσις é o substantivo de ἐκένωσεν). Ver à mão.
- **1 Tessalonicenses** (3 candidatos, em 9 palavras): 2:7 μήτηρ e νήπιοι (×2). **νήπιοι é a leitura variante** de 2:7 (contra ἤπιοι), por isso deve estar na nota, e não é erro. Confirmar.

**Proposta.** Criar a colação de Filipenses e de 1 Tessalonicenses (`docs/colacao/`) e correr o verificador (Fase 4).

### M13 — Filemom: 25 versículos iguais ao piloto

O texto da edição nova é igual ao do piloto (25/25). O que falta é o estado (A2) e a decisão de canónico (M11).

### M14 — Antigo Testamento não verificável contra o hebraico nesta varredura

Não há fonte hebraica no repositório. O WLC está disponível em `openscriptures/morphhb` (pin `db6c5c9`, já citado nos MD), e pode ser lido pelo GitHub. Fica na Fase 5.

### M15 — 3 João 1:14: divergência com o SBLGNT a confirmar

A colação de 3 João traz no fim do versículo 14 a saudação final («Os amigos mandam-te saudações. Saúda os amigos, cada um pelo nome.»). Contra o SBLGNT (pin `d7f35ad`), a frase aparece em posição diferente. A hipótese mais provável é de numeração: a KJV e a BEE põem a saudação no v. 14, e o SBLGNT no v. 15. Tem de se confirmar contra a colação antes de se fechar. Ver D13.

### M16 — Aspas desequilibradas em 120 versículos da edição nova

120 versículos têm número diferente de «» abertas e fechadas. Exemplos: Rute 1:8, 1:9, 1:11. Pode ser convenção de diálogo que atravessa versículos (uma fala que continua no seguinte), ou defeito. Classificar caso a caso antes de qualquer alteração. Não há regra escrita sobre isto.

### B1 — Grafias

Mencionadas em M5. `receção` está na forma correta e não deve ser alterada.

### B2 — Citações em inglês nas notas

«unnatural desire» (Judas 1:7, na Análise Léxica, citação da ESV) e «heretick» (Tito 3:10, na Análise Léxica, citação da KJV). Ver D12: se são citações legítimas com atribuição, ficam; se são deriva de idioma, substituem-se.

### B3 — Scripts one-off

`scripts/fechar_joao4.py` contém o texto e as notas de João 4:29–54 como código. É um script de uma vez; o conteúdo devia viver só no JSON. `limpar_historico_notas.py` e `regenerar_critica.py` são ferramentas e ficam.

### B4 — Passos sem efeito de gate

`bee-nova-edicao.yml` (linha 163) e `bee-autopiloto.yml` (linha 185) têm `|| true` no teste da chave (`autopiloto.py --testar`). Não é erro de conteúdo, mas um passo que não pode falhar não é um gate.

---

## 5. Decisões que preciso do responsável

| # | Pergunta | Opções |
|---|---|---|
| D1 | Qual é o texto de referência de **Tito** e **Judas**? | (a) restaurar o piloto aprovado; (b) aceitar a versão nova e pedir reaprovação |
| D2 | Estado de **1 e 2 Tessalonicenses**: registar como aprovados editorialmente (voz), com revisão especializada pendente? Atualizar JSON e cabeçalhos MD? | sim / não / depende |
| D3 | Criar o JSON de **Oseias, Joel, Amós, Obadias e Zacarias** a partir dos MD? | (a) sim, com o estado de cada MD; (b) só depois do fecho de João |
| D4 | Destino da **linha legada** (Mateus, Marcos, João, Filemom): arquivar, ou retomar com a voz atual? | arquivar / retomar / manter tal como está |
| D5 | **ZIP** `entregas/BEE-previa.zip` e `docs/arquivo/BEE-gerador.zip` | remover / marcar obsoleto / manter |
| D6 | Regra de **tratamento**: «tu» só em oração (escrita), ou «tu» em diálogo a uma pessoa (prática aprovada)? | regra escrita / prática / caso a caso |
| D7 | Convenção do **grego**: itálico sempre nas notas? | sim / só em Análise Léxica / sem regra |
| D8 | **Filemom 1:2** `[[irmã]]` com nível A: retirar `[[ ]]` ou baixar para B? | retirar / baixar |
| D9 | **Filemom** e **João**, legado e nova: qual é o canónico, e em que capítulos? | nova / legada / por capítulo |
| D10 | **Rubricas** (Habacuque 3:19): dentro do texto (itálico) ou numa linha própria? | dentro / linha própria |
| D11 | Estado operacional `edicoes/nova/livros_json/.bee/`: versionar ou ignorar? | versionar / ignorar |
| D12 | **Citações em inglês** nas notas (Judas 1:7 ESV, Tito 3:10 KJV): manter com atribuição, ou traduzir? | manter / traduzir |
| D13 | **3 João 1:14**: a frase final (saudação) pertence ao v. 14 (numeração KJV) ou ao v. 15 (SBLGNT)? | KJV 14 / SBLGNT 15 / confirmar a colação |

---

## 6. Verificado e sem ação

Só entram aqui as verificações que foram feitas e que deram resultado limpo.

- **Contagens**: os livros da edição nova batem com a numeração tradicional, por capítulo e no total (53 capítulos, 1016 versículos, em `verificar_dados`).
- **Grego da colação contra o SBLGNT (pin `d7f35ad`)**: João 1–4 (166/166), Filemom (25/25), Judas (25/25), Tito (46/46), 2 João (13/13), 2 Tessalonicenses (47/47). 3 João: idêntico exceto 1:14 (M15).
- **JSON ↔ MD**: idênticos em 11 pares (Rute, Jonas, Miqueias, Naum, Sofonias, Ageu, Malaquias, Filipenses, 1 e 2 Tessalonicenses, Filemom, 2 e 3 João), com exceção de Habacuque 3:19 (M4). Tito e Judas divergem do piloto (A1).
- **`verificar_estilo`** limpo na edição nova.
- **`verificar_dados`** íntegro na edição nova (53 capítulos, 1016 versículos).
- **`verificar_documentacao`** coerente.
- **Suíte de testes**: 417 OK, 2 saltados.
- **Compilação de controlo** (`gerar_bee.py --compilar --dados edicoes/nova/livros_json`): PARCIAL, 17/66 livros, 53/1189 capítulos, 1016 versículos.
- **Links de leitura**: os ficheiros locais do README existem (incluindo os quatro pilotos). Os alarmes do teste de links eram URLs externas.
- **Sem «você»** nos JSON da edição nova (busca com fronteiras de palavra).
- **Versificação**: 3 João tem 14 versículos, como na KJV (ver M15).
- **Estados dos cinco livros só-MD**: Oseias e Joel dizem «aprovada editorialmente; revisão especializada pendente»; Amós, Obadias e Zacarias dizem «não aprovada» (A7).
- **Ortografia**: não verificada com o verificador oficial (A5). A leitura de M5 foi feita com o verificador instalado num ambiente temporário.

**Não verificado nesta varredura** (ficaram por fazer, não estão confirmados como limpos): `<i>`/`<b>` equilibrados em todos os capítulos; Selá; `[[ ]]` em Judas 1:5; `.gitignore` de `out/`; «Pontuação dos Doze» (Malaquias 3:17–4:1).

---

## 7. O que não foi revisto nesta varredura

- **Leitura linha a linha** de cada versículo de Rute a Malaquias, Filipenses, 1 e 2 Tessalonicenses, Filemom, Tito, Judas, 2 e 3 João. Só se fez a leitura das aprovações anteriores e as verificações automáticas. A leitura integral é a Fase 6.
- **Antigo Testamento contra o hebraico** (M14). Fica na Fase 5.
- **Qualidade de voz e de prosa** das notas: só amostras.
- **Grego** de Filipenses e de 1 Tessalonicenses palavra a palavra (só candidatos, M12).
- **Linha legada**: só verificações automáticas (A4).
- **Notas de João 5**: não existem ainda (em curso).

---

## 8. Plano de resolução

A ordem segue o risco para o leitor, não o número dos livros.

**Fase 0 — Decisões.** Responder às perguntas D1–D13. Nenhuma fase começa antes de D1, D2, D5 e D6, porque as outras dependem delas.

**Fase 1 — Textos aprovados (A1, A2, A9).**
- Restaurar ou reaprovar Tito e Judas (D1). Ver os sete versículos de Tito e o 1:7 de Judas.
- Alinhar os estados de Tito, Judas, 2 e 3 João, Filemom, 1 e 2 Tessalonicenses com a decisão (D2).
- Decidir `[[ ]]` em Filemom 1:2 (D8).
- *Critério de saída:* `verificar_dados` com aprovados sem pendentes; JSON, MD e lotes com o mesmo estado; testes OK.

**Fase 2 — Dados e artefactos (A3, A6, A7, M8, M11, M13).**
- Tratar os ZIP (D5). Não gerar nenhum sem pedido.
- Fechar a quarentena obsoleta e decidir o estado operacional (D11).
- Criar os JSON dos cinco livros só-MD, se D3 for sim.
- Canonizar Filemom e João, legado e nova (D9). Fundir as cópias de `edicoes/piloto/dados/` ou eliminá-las.
- Separar 2 e 3 João em dois ficheiros de leitura (M8).
- *Critério de saída:* um só texto por livro; sem artefato obsoleto no repositório.

**Fase 3 — Ferramentas (A4, A5, A8, B4).** Inclui os verificadores que devolvem falsos positivos em M15–M16 e D12.
- Mudar os defaults `--dados` para a edição nova; exigir `--dados` na legada.
- `verificar_ortografia.py` falha se a dependência faltar; instalá-la no workflow.
- `verificar_notas_colacao.py`: `[[ ]]` só no comentário (fora de itálico), e no texto só com leitura assinalada; reconhecer os nomes das edições («Tregelles», «Westcott-Hort», «Nestle-Aland»); correr também em Filipenses e 1 Tessalonicenses quando houver colação.
- `verificar_estilo.py`: a regra de tratamento (D6) e a convenção do grego (D7), com testes.
- Retirar `|| true` do teste de chave, ou documentar porque é aceitável.
- *Critério de saída:* testes novos para cada regra; os quatro falsos positivos desta varredura passam a ser ignorados pelo código, não à mão.

**Fase 4 — Conteúdo (M1, M4, M5, M7, M12, M10).**
- 2 Tessalonicenses: corrigir em `regenerar_2ts.py` as 20 notas com histórico, as 9 CT sem sigla e as 4 CT sem entrada (M1).
- Habacuque 3:19: aplicar a convenção decidida (D10).
- Grafias: `acção`, `directo`, e uniformizar `lêem`/`leem` (M5). M16 (aspas): classificar caso a caso. D12 e D13: decidir antes de alterar 3 João 1:14, Judas 1:7 e Tito 3:10.
- Grego: aplicar a convenção (D7).
- Filipenses e 1 Tessalonicenses: criar a colação e verificar os sete e três candidatos (M12).
- João legado: fechar ou transferir as 17 decisões (M10), conforme D4.
- *Critério de saída:* `verificar_notas_colacao` e `verificar_ortografia` sem falhas em todos os livros com colação.

**Fase 5 — Antigo Testamento contra o hebraico (M14).**
- Ler WLC (`openscriptures/morphhb`, pin `db6c5c9`) e confirmar o texto dos livros aprovados por contagem, ordem e amostra de versículos com nomes próprios, números e termos técnicos.
- *Critério de saída:* relatório por livro, com as divergências listadas.

**Fase 6 — Leitura integral, por ordem.** Cada livro com registo de achados, sem alterar sem pedido:
1. Filemom; 2. Tito; 3. Judas; 4. 2 e 3 João; 5. Filipenses; 6. 1 Tessalonicenses; 7. 2 Tessalonicenses; 8. João 1–5.
- *Critério de saída:* para cada livro, um registo com o que foi lido, o que foi corrigido e o que ficou pendente.

**Fase 7 — Documentação e fecho.** Atualizar `docs/ESTADO.md`, `LOTE_*.md` e `EDICAO_NOVA.md` com os estados reais. Correr a verificação completa (testes, estilo, dados, documentação, compilação de controlo). Abrir o PR para `main`.

**Depois disto**, e só depois, segue-se para o próximo livro ou carta.

---

## 9. Resumo dos números

- Livros e cartas na edição nova: **17** (+ 5 só em MD; + 4 na legada).
- Versículos na edição nova: **1016** em JSON; **+ 648** em MD (Oseias 197, Joel 73, Amós 146, Obadias 21, Zacarias 211), só se D3 for sim.
- Achados: **9 altos (A1–A9)**, **16 médios (M1–M16)**, **4 baixos (B1–B4)**.
- Decisões pedidas: **13 (D1–D13)**.
- Verificações sem falha: estilo, dados, documentação, testes (417), grego da colação de 166 + 25 + 25 + 46 + 13 + 47 versículos (e 3 João, salvo 1:14).
