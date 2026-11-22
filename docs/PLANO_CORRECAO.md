# Plano de correção e reorganização

Base: `docs/REVISAO_GERAL.md` (primeira varredura, commit `f507104`). Este plano transforma os achados A1–A9, M1–M16 e B1–B4 em etapas com critério de saída.

**Regra de ordem.** A produção de livros e cartas só retoma depois da Etapa 9. As etapas 1 a 8 tiram do caminho o que atrapalha: ferramentas que dão falsos resultados, estados errados, texto aprovado alterado, ficheiros mortos.

**Regra de segurança.** Nada é apagado sem estar no histórico do Git. Ficheiros removidos ficam recuperáveis por commit. Ações irreversíveis fora do repositório (apagar branches remotos) são indicadas ao utilizador, não executadas.

---

## Decisões que bloqueiam etapas

Estas decisões precisam do responsável. Sem elas, a etapa indicada fica parada.

| # | Decisão | Bloqueia |
|---|---|---|
| D1 | Texto de referência de Tito e Judas: restaurar o piloto ou aceitar a versão nova com reaprovação | Etapa 4 |
| D2 | 1 e 2 Tessalonicenses: registar como aprovados editorialmente (voz), com revisão especializada pendente | Etapa 3 |
| D4 | Linha legada (Mateus, Marcos, João, Filemom): arquivar em pasta própria, ou apagar, ou manter como está | Etapa 6 |
| D5 | ZIP `entregas/BEE-previa.zip` e `docs/arquivo/BEE-gerador.zip`: remover, marcar obsoleto, ou manter | Etapa 8 |
| D6 | Regra de tratamento «tu»/«vocês»: regra escrita ou prática aprovada | Etapa 5 |
| D7 | Convenção do grego nas notas: itálico ou texto corrido | Etapa 5 |

**Por defeito, sem resposta:** D3 (cinco livros só em MD) fica como pendência documentada, sem produzir JSON agora; D10, D12 e D13 seguem a recomendação da Etapa 5; D11 (`.bee/`) é tratado na Etapa 1 como ficheiro operacional fora do Git.

---

## Etapa 1 — Higiene do repositório (sem decisões)

**Ações**

1. Remover `scripts/fechar_joao4.py`. É um script de uma vez, com o texto de João 4:29–54 escrito no código. O conteúdo já vive no JSON; confirmar antes de apagar.
2. `.bee/` operacional (`livros_json/.bee/*` e `edicoes/nova/livros_json/.bee/*`): sair do Git. Acrescentar ao `.gitignore` a regra `**/.bee/` (a atual só cobre a raiz). Os ficheiros ficam no disco local; o histórico mantém-se.
3. Quarentena (`edicoes/nova/livros_json/.bee/quarentena.json`): fechar as 24 entradas `pendente` de João 2 e 4 que já têm texto no JSON. Cada entrada fecha com a referência ao versículo e a data. Não se apaga nenhuma entrada, para manter o registo.
4. Estado de João 5 (`in_progress`, 5:1): deixar como está; é trabalho em curso.

**Critério de saída:** `git ls-files` sem `.bee/`; `git status` limpo; quarentena com zero `pendente` obsoletos; suíte de testes OK.

---

## Etapa 2 — Ferramentas que dão falsos resultados (bloqueante)

Esta etapa vem antes de qualquer correção de texto, porque sem ela os verificadores não provam nada.

**Ações**

1. `scripts/verificar_ortografia.py`: sair com erro (código ≠ 0) quando `pyspellchecker` falta. Instalar a dependência no workflow `bee-nova-edicao.yml`, num passo que bloqueia. Teste: sem a dependência, o script falha.
2. Defaults `livros_json` → edição nova:
   - `gerar_bee.py`: `--dados` por defeito aponta para `edicoes/nova/livros_json`.
   - `scripts/verificar_dados.py`: idem.
   - Legada só com `--dados livros_json` explícito.
   - `bee-autopiloto.yml` linha 145: passar `--dados` explícito.
   - Teste: o default resolve para a edição nova.
3. `scripts/verificar_notas_colacao.py`:
   - `[[ ]]` verificado só nas notas, nunca no texto dos versículos (corrige o falso positivo de Judas 1:5 e Filemom 1:2 na verificação).
   - Reconhecer nomes por extenso das edições («Tregelles», «Westcott-Hort», «Nestle-Aland») além das siglas.
   - Suportar Filipenses e 1 Tessalonicenses quando houver colação (ver Etapa 5).
   - Teste para cada caso.
4. `verificar_estilo.py`: acrescentar a verificação de «você» com fronteira de palavra (já feita à mão). A regra de tratamento e a do grego entram depois de D6 e D7 (Etapa 5).
5. Workflows com `|| true` nos testes (`bee-nova-edicao.yml` linha 163, `bee-autopiloto.yml` linha 185): documentar porquê, ou tornar o passo bloqueante. Por defeito, documentar.

**Critério de saída:** suíte OK com os testes novos; cada falso positivo da varredura passa a ser ignorado pelo código, não à mão; `verificar_ortografia` falha sem a dependência.

---

## Etapa 3 — Fonte de verdade e estados (depois de D2)

**Ações**

1. Alinhar `review` no JSON com a decisão de D2 para Tito, Judas, 2 João, 3 João, Filemom, 1 e 2 Tessalonicenses. Cada estado diz exatamente o que foi aprovado (voz) e o que está pendente (revisão especializada).
2. Alinhar os cabeçalhos MD (`1_TESSALONICENSES.md`, `2_TESSALONICENSES.md` e os pilotos) com o JSON.
3. Alinhar `LOTE_01.md`, `LOTE_05.md`, `LOTE_06.md`, `LOTE_07.md`, `docs/ESTADO.md` e `docs/EDICAO_NOVA.md` com o JSON. Corrigir a frase «a legada retoma-se em João 19:13».
4. Declaração de LOTE_03 sobre Oseias e Joel: confirmar que diz «leitura MD aprovada; JSON pendente».
5. Cópias `edicoes/piloto/dados/`: são cópias de JSON que divergem da edição nova. Depois de D1, apagar as que ficam por substituir, ou gerá-las a partir da edição nova. Uma só fonte.
6. 2 e 3 João: separar `edicoes/piloto/2_E_3_JOAO.md` em dois ficheiros de leitura, cada um com a sua ligação (regra do projeto).

**Critério de saída:** para cada livro, um só estado em JSON, MD e lotes; `verificar_dados` sem contradições; cada livro com uma só cópia de texto.

---

## Etapa 4 — Texto aprovado (depois de D1)

**Ações**

1. Tito e Judas (A1):
   - Se D1 = restaurar: repor o texto do piloto em `630_Tito.json` e `720_Judas.json` (sete versículos de Tito; Judas 1:7). Regenerar MD. Verificar que as notas continuam coerentes com o texto restaurado.
   - Se D1 = aceitar: deixar o texto novo, registar a alteração no `LOTE_*` com a lista de versículos, e pedir reaprovação ao responsável antes de fechar o estado.
2. Filemom 1:2 (A9): decidir `[[ ]]` com nível A (D8). Recomendação: retirar a marca se a leitura é adotada pela base sem apoio noutro testemunho; baixar o nível se a marca fica. A escolha vai para a CT.

**Critério de saída:** texto aprovado igual ao piloto aprovado, ou alteração aprovada com registo; `[[ ]]` coerente com o nível da CT.

---

## Etapa 5 — Conteúdo técnico e estilo

**Ações**

1. **2 Tessalonicenses (M1):** corrigir em `scripts/regenerar_2ts.py` (não no JSON, para não quebrar o teste de reprodutibilidade):
   - retirar o histórico de versão das 20 notas (15 «conta uma versão anterior» e 5 «história de correções»);
   - corrigir as 9 CT que não citam o aparato e as 4 que falam de variante sem entrada (1:3, 1:12, 3:3, 3:16), após ler a colação;
   - nota: a contagem de hoje é 33; o resumo anterior dizia 15. Confirmar antes de fechar.
2. **Grafias (M5):** `acção` → `ação` (João 2:13), `directo` → `direto` (João 2:16). Confirmar primeiro a norma em `modelos/estilo_bee.json`. `lêem`/`leem`: escolher uma forma pela norma e uniformizar (108 e 26 ocorrências). `facto` fica como está.
3. **Grego fora de itálico (M7, D7):** aplicar a convenção decidida. Se D7 = itálico, aplicar a todas as notas e acrescentar teste no verificador. Se D7 = texto corrido, documentar essa regra e acrescentar o teste no sentido inverso.
4. **Tratamento (M6, D6):** decidir a regra. Depois ler os nove capítulos medidos (Rute 2 e 4; Jonas 1; Habacuque 1; Malaquias 2; João 1, 3 e 4; Filemom 1) e corrigir só o que for erro. Verificador com teste.
5. **Aspas (M16):** 120 versículos com «» desequilibrado. Classificar caso a caso: diálogo que atravessa versículos (legítimo) ou erro. Corrigir só os erros.
6. **3 João 1:14 (M15, D13):** confirmar contra a colação se a saudação final pertence ao v. 14 (numeração KJV) ou ao v. 15 (SBLGNT). Recomendação: manter a numeração KJV, que é a da casa, e fazer uma nota de versificação visível no texto da colação.
7. **Citações em inglês (B2, D12):** Judas 1:7 (ESV) e Tito 3:10 (KJV). Recomendação: manter, com atribuição; traduzir só se o responsável preferir.
8. **Habacuque 3:19 (M4, D10):** rubrica numa linha própria, como no MD. Recomendação: linha própria, com regra escrita.
9. **Colação de Filipenses e 1 Tessalonicenses (M12):** criar `docs/colacao/Filipenses.json` e `1_Tessalonicenses.json` a partir do SBLGNT (pin `d7f35ad`); correr o verificador; ler os sete candidatos de Filipenses e os três de 1 Tessalonicenses.

**Critério de saída:** verificadores de notas, ortografia e estilo sem falhas em todos os livros com colação; regras escritas com teste; decisões D6, D7, D10, D12, D13 registadas em `modelos/estilo_bee.json` ou em `docs/ESTILO_BEE.md`.

---

## Etapa 6 — Linha legada (depois de D4)

**Ações**

- Se D4 = arquivar: mover `livros_json/` para `legado/` (ou `docs/arquivo/legado/`), fora dos defaults. Verificar que nenhum script aponta para o caminho antigo.
- Se D4 = retomar: fechar as 17 `pending_decisions` de João legado, uma a uma, e corrigir as 330 falhas de «vós» (96 em Mateus, 76 em Marcos, 158 em João).
- Se D4 = manter: documentar no `README` que a legada não é fonte e que não é usada pelos defaults.
- Em qualquer caso: Filemom legado e Filemom novo ficam com um só canónico (D9 em `REVISAO_GERAL.md`; recomendação: edição nova).

**Critério de saída:** nenhum comando por defeito lê a legada; decisão registada.

---

## Etapa 7 — Cinco livros só em Markdown (D3 por defeito)

**Ações**

- Não produzir JSON agora. São produção, e a produção só retoma na Etapa 9.
- Registar em `docs/ESTADO.md` e em `LOTE_03.md`: Oseias e Joel com leitura MD aprovada e revisão especializada pendente; Amós, Obadias e Zacarias sem aprovação. Dizer que o JSON não existe.
- Acrescentar ao `verificar_documentacao.py` uma regra que falha se um livro for declarado «entregue» sem JSON.

**Critério de saída:** nenhuma declaração de entrega sem JSON; pendência registada.

---

## Etapa 8 — Limpeza do repositório (depois de D5)

**Ações no repositório**

1. ZIP (D5): se remover, `git rm` de `entregas/BEE-previa.zip` e `docs/arquivo/BEE-gerador.zip`. Se marcar, acrescentar aviso no `README` da pasta. Nenhum ZIP novo sem pedido expresso.
2. `docs/APRESENTACAO_BEE.docx`: preservar (ligado no README).
3. Procurar duplicados e restos: ficheiros fora de qualquer caminho usado pelo README, pelos scripts ou pelos testes. Remover o que for resto e não tiver referências. Lista e motivo antes de apagar.
4. Confirmar que `out/`, `*.SQLite3` e outros artefactos gerados estão no `.gitignore`.

**Ações fora do repositório (para o utilizador)**

Os branches remotos `arena/*` seguintes têm PR fundido (#56–#68) e podem ser apagados. Não os apaguei: esta sessão não pode enviar alterações para outros branches.

- `arena/6ff2ad51-traducao-epignosis` (#56), `arena/9249dcf6-traducao-epignosis` (#57), `arena/384105cc-traducao-epignosis` (#58), `arena/e33ee8a2-traducao-epignosis` (#59), `arena/a8d06f4d-traducao-epignosis` (#60), `arena/5c26c1e4-traducao-epignosis` (#61), `arena/c8266cc9-traducao-epignosis` (#62), `arena/614e2f59-traducao-epignosis` (#63), `arena/ccdcbc43-traducao-epignosis` (#64), `arena/e9dbcb1e-traducao-epignosis` (#65), `arena/40e0b67d-traducao-epignosis` (#66), `arena/6089a33a-traducao-epignosis` (#67), `arena/32f77979-traducao-epignosis` (#68).
- Comando: `git push origin --delete <nome>` para cada um, depois de confirmar que os PR estão fundidos.
- Não apagar `main` nem o branch desta sessão (`arena/b6fccf92-traducao-epignosis`).

**Critério de saída:** `git ls-files` só com ficheiros usados; repositório sem ZIP sem decisão; lista de branches entregue ao utilizador.

---

## Etapa 9 — Verificação completa e fecho

1. Documentação coerente: `docs/ESTADO.md`, `LOTE_*.md`, `EDICAO_NOVA.md`, `README.md`.
2. Verificação completa: suíte de testes, `verificar_estilo`, `verificar_dados`, `verificar_documentacao`, `verificar_notas_colacao` (todos os livros com colação), `verificar_ortografia` (com a dependência), compilação de controlo (`gerar_bee.py --compilar`).
3. Atualizar `docs/REVISAO_GERAL.md`: marcar cada achado como resolvido com o commit, ou como pendente com a razão.
4. Abrir PR para `main` e fundir quando as verificações estiverem verdes.
5. Só depois: retomar produção em João 5, ou no próximo livro/carta, segundo `LOTE_04.md`.

**Critério de saída:** nenhum achado A ou M por resolver sem razão escrita; PR fundido; produção retomada a partir de `ESTADO.md`.

---

## Resumo de ordem

1 higiene → 2 ferramentas → 3 estados → 4 texto aprovado → 5 conteúdo → 6 legada → 7 cinco MD → 8 limpeza → 9 fecho → produção.

Etapas 1 e 2 começam já, porque não dependem de decisões. Etapas 3 a 8 esperam pelas decisões indicadas.

---

## Estado de execução

Atualizado em 2026-11-22, depois das decisões do responsável (D1 aceitar e reaprovar; D2 sim; D6 caso a caso; D7 itálico; D4 arquivar; D5 remover; D11 sair do Git).

| Etapa | Estado | Notas |
|---|---|---|
| 1 Higiene | **Parcial** | Quarentena: 24 entradas `pendente` marcadas `resolvida` (texto verificado; nenhuma apagada). `scripts/fechar_joao4.py` removido (26 versículos conferidos antes). **D11 bloqueada**: ver «Bloqueio D11». |
| 2 Ferramentas | **Feito; workflows ativos por copiar** | Verificadores, defaults (`gerar_bee.py` e `verificar_dados.py` para a edição nova), `|| true` documentados, ortografia sem `tee` nos modelos. Os workflows ativos (`.github/workflows/`) não foram enviados: o GitHub recusou o envio sem permissão `workflows`. Ficheiros completos em `para_colar/.github/workflows/` (ver `para_colar/LEIA-ME.md`). Até serem copiados, `test_workflow_sincronizado` fica vermelho de propósito. |
| 3 Estados | **Feito (2026-11-22)** | `review` de todos os JSON alinhado: Tito, Judas e Filemom em `rascunho` (texto alterado depois do piloto, reaprovação D1); 2 Tessalonicenses, 2 e 3 João, 1 Tessalonicenses e Filipenses em `aprovado editorialmente` com revisão especializada pendente na nota; nota de revisão acrescentada aos sete livros do AT que não a tinham. MD de piloto: cabeçalhos e texto dos versículos alterados sincronizados (Filemom 1:2 e 1:16; Tito 7 versículos; Judas 1:7). `2_E_3_JOAO.md` dividido em `2_JOAO.md` e `3_JOAO.md`. `edicoes/piloto/dados/` removido (ver «Piloto: cópias e fonte»). LOTE_01/03/05, `ESTADO.md` (tabela de estado gerada do JSON) e `EDICAO_NOVA.md` alinhados. Por fazer, sem bloquear: sincronizar as notas dos MD de piloto (Filemom, Tito, Judas) com as notas do JSON. |
| 4 Texto aprovado | **Feito (D1, D8)** | Tito e Judas: texto novo mantido, `rascunho`, com a lista dos versículos alterados em cada nota e reaprovação pendente. Filemom 1:2 (`[[ ]]` retirados, D8) e 1:16 (D6): texto alterado depois do piloto, Filemom também `rascunho` até reaprovação. |
| 5 Conteúdo | **Em curso** | Feito: D7 (itálico no grego das notas, `7e3f189`); M1 em 2 Tessalonicenses (`7105728`: história de versão retirada; 31 avisos → 0); M5, D10, D12 (`6d13ca6`); D8, M15, M16 (`73d0e51`: Filemom 1:2 sem `[[ ]]`; 3 João 1:14 com a versificação dita na CT; 120 versículos com aspas medidos, sem anomalias por capítulo); M12 (colações de **Filipenses** e **1 Tessalonicenses** em `docs/colacao/`; 1 Ts: bug do aparato corrigido em `bee/fontes.py` — nota de um versículo SBLGNT chegava ao anterior quando a BEE junta 2:6–7; regenerada a CT; os 10 candidatos lidos: todos lemas, remissões, trocadilho declarado ou variante discutida, nenhum erro). D6 (tu/vocês, 9 capítulos): regra aplicada caso a caso. A alternância mantém-se quando o original alterna o número (João 3:7 e 3:11, σοι e ὑμᾶς/λαμβάνετε; Malaquias 2; Rute 4; Habacuque 1:5; Jonas 1:12). Corrigido Filemom 1:16: «na vida de vocês» acrescentava o plural a σοί (singular); passou a «na convivência humana» e a nota foi ajustada. O cruzamento automático com a SBLGNT não encontra outra discrepância no NT. As formas do Antigo Testamento foram julgadas pelo número do hebraico, sem fonte hebraica consultada: revisão especializada pendente. Etapa 5 concluída. |
| 6 Legada | **Bloqueada** | D4 (arquivar) depende de desativar o fluxo legado `bee-autopiloto.yml`, que lê `livros_json/`. Sem alteração ao workflow, mover a pasta parte esse fluxo. |
| 7 Cinco MD | **Feito (2026-11-22)** | Nenhum JSON criado (D3). Oseias e Joel: leitura MD aprovada, JSON pendente. Amós, Obadias e Zacarias: sem aprovação, sem JSON. Declarado em `LOTE_03.md`, `LOTE_04.md` (Amós e Obadias: «lidos para revisão, sem JSON») e `docs/ESTADO.md`. Regra em `verificar_documentacao.py`: falha se um livro sem JSON for declarado «entregue» (`tests/test_documentacao.py`). |
| 8 Limpeza | **Feito (2026-11-22), exceto branches** | ZIP removidos (D5): `entregas/BEE-previa.zip`, `entregas/BEE-previa/LEIA-ME.txt`, `docs/arquivo/BEE-gerador.zip`. Removidos também: `docs/LER_TITO.md` (roteiro de uma entrega com ZIP), `scripts/lapidar_mistos.py` (correção única já aplicada: 0 tokens mistos nos JSON), `rascunhos/440_Ageu_1_1-6.md`, `rascunhos/440_Ageu_1_7-11.md`, `rascunhos/HABACUQUE_amostra.md`, `rascunhos/Joao_4_29-32.md` (rascunhos superados, sem referências). Mantidos: `rascunhos/230_Salmos_23.json` e `640_Filemom_1.json` (usados por `tests/test_conteudo_colaborativo.py`) e `600_2_Tessalonicenses_aprovado_2026-11-19.json` (arquivo do texto aprovado anterior). Mantidos também os `lapidar_*` de João e 2Ts, que as notas dos JSON citam como proveniência. `out/` acrescentado ao `.gitignore`, com `*.zip`. Branches remotos: ver abaixo. Tags `arquivo-bee-dados-2026-11-17`, `bee-previa`, `bee-previa-nova` continuam; decisão do responsável. |
| 9 Fecho | **Verificação feita (2026-11-22); PR e produção por fazer** | Verificação: 448 testes OK (2 saltados); `verificar_dados`, `verificar_estilo`, `verificar_documentacao` limpos; notas de João, 1Ts, 2Ts, Filipenses, Tito, Filemom, 2 e 3 João e Judas conferem com a colação; módulo parcial compila (17 livros); ortografia com `pyspellchecker` sai 0 com 80 alertas para confirmar à mão (nomes hebraicos, transliterações e citações em inglês; sem erro conhecido). Corrigido: «lêem» → «leem» nas notas (AO90, 162 ocorrências, só notas) e «perspectiva» → «perspetiva» (Judas 1:14). Bloqueado: PR para `main` e produção dependem da Etapa 6 (D4) e da permissão `workflows`. Sem PR e sem produção nesta sessão. |

### Decisões do utilizador (2026-11-22, depois do plano)

- **Workflows desativados.** Os três fluxos (`BEE — produção automática`, `BEE — edição nova`, `BEE — relógio de segurança`) estão `disabled_manually` no GitHub, confirmado com `gh workflow list --all`. A produção de texto passa a ser feita passo a passo, sem IA no workflow.
- **Aprovação por bloco.** O utilizador aprova em blocos de vários capítulos, não por capítulo. O bloco pode ser João 5–6, por exemplo.
- **Markdown acrescentado, não recriado.** A leitura MD de cada livro cresce capítulo a capítulo no mesmo ficheiro. Não se cria um ficheiro novo por bloco.
- **Ritmo.** Dois capítulos por turno como regra, com verificação após cada capítulo. Capítulos grandes (João 6, 71 versículos) podem ir sozinhos.
- **Worker** (`worker/`, `Dockerfile`): experimental, fora do fluxo; o utilizador não o vai implementar.

### Bloco A (João 5–6) e leitura de João (2026-11-22)

- **Redação manual, sem IA no workflow.** João 5 (47 vv.) e João 6 (71 vv.) foram escritos pelo agente a partir do SBLGNT, com a tradução, a Análise Léxica e a Síntese; a Crítica Textual saiu de `scripts/regenerar_critica.py`, com a colação completa (`colar.py --livro 500 --saida /tmp/colac`, que não é publicada).
- **Estado:** `rascunho` em `review.editorial_blocks`, à espera da aprovação do responsável por bloco. Revisão especializada pendente em 5 e 6 (`review.specialist`).
- **João 5:4** (fora da base SBLGNT, presente no Textus Receptus) fica entre colchetes, com nível de certeza C. A Crítica Textual foi escrita à mão a partir dos factos da colação. **Não regenerar 5:4** com `regenerar_critica.py`, que a reescreve.
- **Leitura:** `edicoes/nova/JOAO.md`, gerada por `scripts/gerar_leitura_livro.py` a partir do JSON (João 1–6). Não se edita à mão; cresce com os capítulos novos.
- **Grafia AO90:** `scripts/regenerar_critica.py` passa a escrever «leem» (antes «lêem»). Em 5–6 corrigiram-se «lêem» e «ruptura» → «rutura».
- **Correção de estado:** a nota do capítulo 4 de João dizia «em curso» com 28 versículos; o capítulo está completo com 54 (sem marcadores).
- **Alertas de ortografia rejeitados (falsos positivos):** «contêm», «denários», «barquinho», «durativo».
- **Verificações:** `verificar_notas_colacao` (João), `verificar_dados`, `verificar_estilo` (João 500) limpos; suíte com 1 falha esperada (cópia do workflow pendente).

### Bloqueio: permissão `workflows` (2026-11-22, ainda ativo no envio)

O utilizador indicou que deu a permissão, mas o envio continuou recusado nesta sessão. Solução provisória: ficheiros completos em `para_colar/.github/workflows/` para copiar à mão.

### Bloqueio (histórico): permissão `workflows`

O GitHub recusou o push de alterações a `.github/workflows/*` com a mensagem «refusing to allow a GitHub App to create or update workflow ... without `workflows` permission». A ligação atual não tem essa permissão. Para desbloquear, o responsável deve reconectar o GitHub na Arena com permissão de workflows. Enquanto isso, não há alterações a workflows nem aos defaults abaixo.

### Bloqueio D11: `.bee/` e a produção

`bee/agenda.py` diz que o estado «nunca» vive no Git, mas `nuvem.py` define `RAMO_DADOS = 'main'`, e os workflows usam `BEE_BRAMO_DADOS: main`. Ou seja, o estado de produção (`estado.json`, `quarentena.json`, `revisoes.json`, `diario.md`) vive **no próprio `main`**. Tirar o `.bee/` do índice faria a próxima execução arrancar sem estado. Não foi feito. Para avançar, é preciso primeiro mudar o ramo de dados (por exemplo, um ramo `bee-dados` próprio, com `RAMO_DADOS` e os workflows atualizados). Isto também exige a permissão `workflows`.

### Pendente de permissão: alterações exatas a aplicar

Aplicar na ordem indicada, com os três ficheiros de workflow iguais (`tests/test_workflow_sincronizado.py` exige sincronia entre `.github/workflows/`, `docs/` e `modelos/`):

1. `.github/workflows/bee-autopiloto.yml`, `docs/bee-autopiloto.yml`, `modelos/bee-autopiloto.yml`, linha 145: `verificar_dados.py --minimo 18` → `verificar_dados.py --dados livros_json --minimo 18`. Obrigatório antes do passo 2.
2. `docs/ci.yml`, `modelos/ci.yml`, linha 30: idem.
3. `.github/workflows/bee-nova-edicao.yml` e `modelos/workflows/bee-nova-edicao.yml`, linha 237: `... | tee /tmp/ortografia.txt` → `... > /tmp/ortografia.txt` seguido de `cat /tmp/ortografia.txt` (o `tee` mascarava o código de saída).
4. `gerar_bee.py`: `--dados` por defeito `edicoes/nova/livros_json`.
5. `scripts/verificar_dados.py`: `--dados` por defeito `edicoes/nova/livros_json`. Só depois do passo 1.

Depois de aplicar: `python3 -m unittest discover -s tests -q` deve continuar a passar, e `tests/test_workflow_sincronizado.py` também.

### Branches remotos (para o responsável)

Os 13 branches `arena/*` com PR fundido (#56–#68) podem ser apagados. Esta sessão não pode enviar alterações para outros branches, por isso não os apaguei:

```
git push origin --delete arena/6ff2ad51-traducao-epignosis arena/9249dcf6-traducao-epignosis arena/384105cc-traducao-epignosis arena/e33ee8a2-traducao-epignosis arena/a8d06f4d-traducao-epignosis arena/5c26c1e4-traducao-epignosis arena/c8266cc9-traducao-epignosis arena/614e2f59-traducao-epignosis arena/ccdcbc43-traducao-epignosis arena/e9dbcb1e-traducao-epignosis arena/40e0b67d-traducao-epignosis arena/6089a33a-traducao-epignosis arena/32f77979-traducao-epignosis
```

Não apagar `main` nem `arena/b6fccf92-traducao-epignosis`.

### Piloto: cópias e fonte

**Decisão de 2026-11-22 (Etapa 3):** `edicoes/piloto/dados/` foi removido. As cinco cópias já divergiam da edição nova (Filemom, Tito, Judas, 2 e 3 João), e o princípio é uma só fonte de texto: `edicoes/nova/livros_json/`. O README passa a gerar os módulos a partir da edição nova. Os scripts de migração única (`migrar_notas_cinco.py`, `lapidar_seis.py`, `importar_piloto.py`) têm uma nota no topo; a origem recupera-se com `git show de2f6af:edicoes/piloto/dados/<ficheiro>`. Os MD de piloto continuam como leitura (`edicoes/piloto/`); o texto dos versículos coincide com o JSON, mas as notas dos MD ainda não foram sincronizadas (pendente).

---

## Decisões escolhidas pela equipa técnica (delegação do responsável, 2026-11-22)

O responsável pediu que escolhêssemos o melhor para a BEE nas decisões pendentes. As escolhas abaixo podem ser revistas; ficam registadas aqui e no estado de execução.

| # | Escolha | Razão |
|---|---|---|
| D3 | Não produzir o JSON de Oseias, Joel, Amós, Obadias e Zacarias agora. Ficam como pendência documentada. | Produção só depois do fecho (Etapa 9). Criar JSON agora misturaria produção com limpeza. |
| D4 | Arquivar a linha legada (`livros_json/`) fora dos defaults, quando o fluxo legado `bee-autopiloto.yml` for desativado. | A legada tem 330 falhas de «vós» e 17 decisões abertas; não deve ser a fonte de nenhum comando por defeito. Mover só depois de desativar o fluxo, para não o partir. |
| D8 | Retirar o `[[ ]]` de Filemom 1:2 se a nota da CT confirmar que a leitura tem apoio nos testemunhos (nível A). Se a nota disser o contrário, baixar o nível para B. | O protocolo reserva `[[ ]]` para leituras sem apoio noutro testemunho. A combinação com nível A não é coerente. A verificação é feita na Etapa 5. |
| D9 | Canónico: edição nova, para Filemom e para João (caps. 1–4 já fechados; 5 em curso). A legada só se mantém como arquivo. | A edição nova é a que segue as regras atuais. |
| D10 | Rubricas (Habacuque 3:19) numa linha própria, como no MD. | É legível e já é a forma dos MD. A regra fica escrita em `docs/ESTILO_BEE.md`. |
| D12 | Manter as citações em inglês nas notas (ESV em Judas 1:7, KJV em Tito 3:10), com atribuição. | São citações explícitas para mostrar o termo grego em contraste; sem atribuição a leitura não se compreende. |
| D13 | 3 João 1:14: seguir a numeração KJV, que é a da casa. A nota de versificação fica visível. | A BEE segue a KJV. A diferença com o SBLGNT é de numeração, e a confirmação contra a colação fica na Etapa 5. |
| D11 | **Manter `.bee/` no `main` por agora.** Não sair do Git. Migrar para um ramo de dados dedicado quando houver permissão `workflows` e um teste de execução completo. | Produção ativa depende deste ramo. Tirar agora sem o ramo novo deixa a próxima execução sem estado. A migração é um passo com risco e precisa de permissão. Ver nota abaixo. |

**Nota sobre D11.** O comentário de `bee/agenda.py` diz que o estado «vive ao lado dos dados, nunca no Git», e isso está errado face ao `RAMO_DADOS = 'main'` de `nuvem.py`. Corrigir o comentário faz parte da Etapa 1 (ver secção de bloqueios). A decisão de manter o estado no `main` é provisória, até existir o ramo de dados.

**Próximo passo.** Com estas escolhas, a Etapa 5 pode avançar. Começa pelo que já tem decisão: D7 (itálico no grego das notas, aplicado pelo gerador e reforçado pelo verificador), M1 (2 Tessalonicenses em `scripts/regenerar_2ts.py`), D8, M15 e M16. D6 (leitura caso a caso dos 9 capítulos) é a parte mais demorada e fica para depois.
