# Estado do projeto — 17/11/2026

> Etapas 1 e 2 integradas no `main` (PR #32); etapas 3 e 4 no PR #37
> (merge `4972e27`); etapa 5 neste ramo de trabalho.

Este ficheiro é o **ponto único de verdade** sobre o que está feito, o que está
a meio e o que falta. O `PLANO_ORGANIZACAO.md` explica o diagnóstico e as
etapas; este documento regista a execução.

## Decisões fechadas

| Tema | Decisão |
|---|---|
| Fonte de dados | `main` (o ramo `bee-dados` deixa de ser a fonte) |
| Provedores de IA | **Gemini** (principal) e **Groq** (reserva) |
| OVHcloud | Só com opt-in explícito (`OVH_API_KEY_ATIVO=1` ou chave) |
| Cadência | cron **horário** (`23 * * * *`), `timeout-minutes: 15`; o cron de 20 min nunca disparou (17/11) |
| Prazo interno | `BEE_TEMPO_MAXIMO=540` s por ciclo e `BEE_TEMPO_TOTAL=660` s por execução |
| Visibilidade | repositório continua **público** |
| Dados no código | os JSON ficam versionados no `main` (Etapa 2) |

Não se apagam ramos, capítulos ou texto gerado, nem se muda a visibilidade,
sem autorização explícita.

## Etapa 1 — Actions sob controlo

### O que estava errado

1. `bee/rede.py` dormia o `Retry-After` sem limite. A execução #12 registou
   esperas de **523 s, 1176 s, 989 s e 1542 s** e foi cancelada aos 50 min.
2. `timeout-minutes: 50` era maior do que o intervalo do cron (20 min).
3. O commit dos dados só acontecia no fim; um cancelamento perdia os
   versículos já gerados (João 18:1–12 no run #12).
4. O resumo do workflow percorria uma lista fixa (`OVH/GEMINI/GROQ/OPENROUTER`)
   e escrevia sempre “a produção continua pela OVHcloud”, mesmo com a OVH sem
   chave e a falhar a listagem.
5. O contador diário só somava lotes guardados; os 429 e 5xx não contavam.
   Além disso, se o único provedor usado fosse o Gemini (sem tecto próprio),
   `all([])` era `True` e o dia parava com uma mensagem vazia.
6. Não havia prazo interno: o ciclo só terminava quando o gerador acabasse.

### O que foi alterado

- `bee/rede.py`
  - `ESPERA_MAXIMA = 45.0` s: nenhum `Retry-After` bloqueia mais do que isto.
  - **HTTP 429** levanta `CotaExcedida` de imediato (sem dormir) e reporta o
    `Retry-After`; o `Rodizio` troca de provedor/modelo.
  - `ClienteHTTP.pedidos_por_provedor()` conta **todas** as tentativas,
    incluindo 429/5xx, para o orçamento diário deixar de ser ficção.
- `bee/ia.py`: as chamadas passam `provedor=` ao cliente HTTP.
- `autopiloto.py`
  - A OVHcloud só entra com chave **ou** `OVH_API_KEY_ATIVO=1`.
  - `BEE_PROVEDORES=gemini,groq` é uma lista branca: uma chave esquecida no
    ambiente não acrescenta provedores à fila.
  - O principal por omissão passou de `ovh` para `gemini`.
  - Os tectos por provedor deixam de ser `{}` quando `lote` é `None`.
- `bee/agenda.py`
  - `_registar_consumo()` usa o contador real de tentativas HTTP.
  - `ConfigAgenda.max_tempo_ciclo` e `Estado.dia()['pedidos_ok']`.
  - Corrigido o `all([])` que parava o dia com o Gemini sozinho.
- `bee/gerador.py`
  - `ConfigGeracao.max_segundos` / `Progresso.tempo_esgotado`.
  - O prazo é verificado antes de cada capítulo e antes de cada lote; o que
    está gravado é válido e o ciclo termina para o `nuvem.py` publicar.
- `nuvem.py`
  - `BEE_TEMPO_MAXIMO` (9 min) para o ciclo e `BEE_TEMPO_TOTAL` (11 min) para
    a execução inteira, abaixo dos 12 min do job. O tecto total também protege
    se o workflow ativo ainda tiver `BEE_TENTATIVAS_CICLO=8`.
  - **Checkpoint imediato** no ramo de dados logo após o ciclo.
  - Handler de `SIGTERM`/`SIGINT` para fechar o ciclo no ponto seguro.
  - Resumo com os provedores **realmente carregados**, não uma lista fixa.
  - `RELATORIO.txt` sempre escrito em `entregas/auto/`; o artefacto deixa de
    poder sair vazio mesmo quando não há módulos.
  - Resumo já não rebenta quando `resultado is None`.
- Workflow — **proposta em `bee-autopiloto.yml`**
  - O GitHub recusou o push de `.github/workflows/bee-autopiloto.yml` com
    “GitHub App … without `workflows` permission”. O ficheiro ativo tem
    `timeout-minutes: 12`, mas os passos finais estão triplicados/corrompidos;
    a configuração do job só fica correta quando a proposta for copiada na UI.
  - `timeout-minutes: 15`; cron `23 * * * *` (horário). Foi `7,27,47` (20 min)
    até 17/11 — expressão que o GitHub nunca chegou a agendar.
  - `BEE_VERSOS_POR_CICLO=80`, `BEE_TENTATIVAS_CICLO=2`,
    `BEE_TENTATIVAS=2`, `BEE_TIMEOUT=90`, `BEE_PEDIDOS_POR_DIA=500`.
  - `BEE_PROVEDORES=gemini,groq`, `OVH_API_KEY_ATIVO=0`.
  - Removido o bloco de resumo hardcoded; o `nuvem.py` é a única fonte.
  - Passo de verificação dos artefactos antes do upload.

### Testes

`python3 -m unittest discover -s tests` → **152 testes, 2 skipped**; os únicos
falhanços são o teste de sincronização do workflow ativo, que continua
corrompido no `main` (ver abaixo). Sem esse teste, **152 testes OK** (2 skipped).
Foram acrescentados testes para o 429 sem espera, o limite de 45 s, a contagem
de tentativas, o prazo do ciclo, o orçamento com o Gemini sozinho, o
relatório sem módulos, a quarentena e os pacotes com o número da execução.

### O que ainda não está validado

- O workflow ativo está **corrigido e igual** a `docs/bee-autopiloto.yml` e a
  `modelos/bee-autopiloto.yml` (SHA-256 igual, teste de sincronização verde).
  A execução manual **16** (`44120273655`, 15:57 UTC) terminou verde em 1m12s
  e criou `BEE-modulos-16` e `BEE-capitulos-16`.
- A execução 16 não somou versículos: o Gemini devolveu **HTTP 503** e a quota
  da Groq estava esgotada. Não é falha do agendador; o próximo ciclo volta a
  tentar.
- **O cron nunca disparou.** Verificado às 21:23 UTC de 17/11: 1 execução no
  total, `event=workflow_dispatch`; **0 `schedule`** em 5 h 30 desde que o
  workflow ficou activo. O cron de 20 em 20 minutos foi travado em silêncio
  (filtro anti-abuso do GitHub); passou a horário (`23 * * * *`) e ganhou o
  `bee-relogio.yml`. Procedimento e verificação: [AGENDADOR.md](AGENDADOR.md) e
  `python3 scripts/verificar_agendador.py`.
- Apesar da falha, a execução `44115508985` (run 15) **produziu** os artefactos
  `BEE-modulos-15` (763 KB) e `BEE-capitulos-15` (253 KB), actualizou os HTML no
  release `bee-previa` e levou os dados a 19 capítulos completos e 818
  versículos guardados (João 19:1–12 em curso). O primeiro upload de cada nome
  passou; as cópias seguintes do workflow ativo receberam **HTTP 409
  (Conflict: an artifact with this name already exists)**. Não é falha de
  produção nem dos dados: é a duplicação do workflow.
- O `SIGTERM` num cancelamento real.

### Como desativar o workflow

A API recusou `gh workflow disable` com **HTTP 403** (a integração não tem
âmbito de administração). Para parar a produção sem apagar o ficheiro:

1. GitHub → **Actions** → **BEE — produção automática**.
2. Menu **⋯** (canto superior direito) → **Disable workflow**.
3. Para voltar: **Enable workflow**.

### Workflow: como foi aplicado e como voltar a aplicar

A versão ativa foi colada pela UI (o push de `.github/workflows/*` é recusado
sem a permissão `workflows`). O teste
`python3 -m unittest tests.test_workflow_sincronizado -v` confirma que os três
ficheiros são iguais. Se for preciso alterar novamente, copie
`docs/bee-autopiloto.yml` para `.github/workflows/bee-autopiloto.yml` na UI e
confirme o teste.

## Etapa 2 — dados no `main`

### Migração

- Os 18 capítulos do antigo `bee-dados` foram copiados para `livros_json/` no
  `main`: **João 1–17 + Filemom = 766 versículos**. Depois das execuções 14 e
  15, João 18 ficou completo e há mais **12 versículos de João 19** em
  `in_progress`; o total guardado é **818** (806 completos).
- Os capítulos 1–4 de João e Filemom 1 já existiam no `main` e são
  **byte a byte iguais** aos do `bee-dados`; a migração não reescreveu texto.
- Antes de apagar o ramo, foi criada a etiqueta
  `arquivo-bee-dados-2026-11-17` (o ramo fica recuperável pela etiqueta).
- `livros_json/.bee/estado.json` e `diario.md` foram trazidos. A execução
  #12 tinha perdido João 18:1–12; a execução `44109642278` voltou a gerá-los e
  guardou João 18:1–19; a execução `44115508985` fechou o capítulo 18 e
  começou João 19 (1–12).

### Código

- `nuvem.py` passou a usar `RAMO_DADOS = 'main'` e **ignora** o antigo
  `BEE_BRAMO_DADOS=bee-dados`. Isto evita que o workflow antigo recrie o ramo
  que foi arquivado.
- O bloco de recuperação por `BEE_REMOTO` foi removido; o checkout do `main`
  já traz os dados. `_reparar_dados` continua a proteger contra um checkout
  atrasado.
- `scripts/verificar_dados.py` verifica sequência de versículos, texto,
  comentário e regressões; o workflow proposto corre-o com `--minimo 18`.
- `_commit_dados` atualiza `refs/remotes/origin/main` depois de cada push: sem
  isso, o checkpoint e a publicação final do mesmo ciclo eram commits irmãos e
  o segundo push era recusado por não ser fast-forward.
- O workflow proposto (`bee-autopiloto.yml`) já não tem o passo de
  recuperar `bee-dados` e define `BEE_BRAMO_DADOS: main`.

### Limpeza de ramos

O utilizador autorizou apagar os ramos desnecessários e ficar apenas com o
ramo de trabalho e o `main`. A lista e o resultado ficam registados abaixo
### Ramos apagados

Ficaram apenas **`main`** e o **ramo de trabalho da sessão**. Foram apagados
20 ramos: 15 `arena/*` antigos, 4 `vibe/*` e o `bee-dados`. Antes de apagar o
`bee-dados`, foi criada a etiqueta **`arquivo-bee-dados-2026-11-17`**, que
preserva os 18 capítulos/766 versículos.

## Etapa 5 — documentação coerente

- `README.md` passou a ser uma entrada curta: o que é, como produzir, estado
  actual, dados e avisos de rascunho.
- O runbook está em `docs/OPERACAO.md`; a arquitetura em
  `docs/ARQUITETURA.md`; as directrizes editoriais em `docs/EDITORIAL.md`.
- `COMECAR_HOJE.md`, `ENTREGA.md` e o antigo `BEE-gerador.zip` foram movidos
  para `docs/arquivo/`, com aviso de documento histórico.
- `AUTOMACAO.md` e o plano da reorganização passaram para `docs/`; os links
  foram actualizados.
- `requirements-dev.txt` separa as dependências opcionais (pytest e worker
  Mistral); o fluxo principal continua só com a biblioteca padrão.
- `entregas/BEE-previa.zip` foi regenerado a partir dos **19 capítulos/806
  versículos completos** e o respectivo `LEIA-ME.txt` já não fala de cinco capítulos.

## Etapa 10 — crítica textual aplicada (20/11/2026)

A proposta do responsável («estudo de crítica textual, manuscritos,
manuscritologia… os mais antigos e com mais cópias devem ser priorizados») foi
transformada em procedimento e aplicada a um livro inteiro.

- **Protocolo:** `docs/CRITICA_TEXTUAL.md` — convicção doutrinária e o que ela
  exige do método, por que a regra dos «mais antigos e com mais cópias» não se
  aplica como slogan (com 2Ts 2:13 como caso real), quatro níveis de evidência e
  três proibições, registo de testemunhas com as pendências, procedimento de sete
  passos por unidade, exegese/hermenêutica, geografia bíblica, arquivologia e a
  tabela de decisões do livro.
- **Evidência:** `bee/manuscritos.py` lê as transcrições MES do acervo CNTR
  (revisão `4e743a4`, CC BY-SA, em `.bee-cache/` fora do Git) e `scripts/colar.py`
  produz `docs/colacao/2_Tessalonicenses.json` e `.md`: 47 versículos contra 01,
  02, 03, P30 e P92 e os textos WH, RP, ST, KJTR, SR e Scrivener, com o estado
  físico do suporte (lacuna, texto suprido, mão corrigida, letra ilegível).
- **Livro regenerado:** `edicoes/nova/livros_json/600_2_Tessalonicenses.json`, a
  partir de `scripts/regenerar_2ts.py` (`--verificar` valida sem escrever). A
  versão anterior aprovada foi guardada em
  `rascunhos/600_2_Tessalonicenses_aprovado_2026-11-19.json` e o histórico de
  geração dos provedores foi conservado na íntegra.
- **Guarda corrigida:** `bee/inspetor.py` comparava marcadores acentuados contra
  texto sem acentos, por isso «filho da perdição», «manifestação da sua vinda»,
  «glória da sua força» e «dar-se-á» nunca eram assinalados — o falso negativo que
  deixou passar 2Ts 2:3 e 2:8.
- **Memória de estilo v1.1:** três regras duras novas (pontuação e maiúscula
  inicial; SENHOR e Senhor; crítica textual só com evidência colacionada),
  `registro.ortografia`, oito entradas de glossário e três vetos novos.
- **Testes:** `tests/test_manuscritos.py` (40) e `tests/test_critica_textual.py`
  (69). O segundo verifica, entre outras coisas, que nenhuma nota cita uma
  testemunha sem registo de colação naquele versículo, que as âncoras da
  memória de estilo citam o texto aprovado em vez de o reescreverem, e — na classe
  de lapidação — que nenhum dos sete livros tem próclise com gerúndio, marcas
  desequilibradas, verbos supridos sem itálico ou famílias lexicais incoerentes.
  Total: 370 testes.

### Lapidação (mesmo dia)

Doze versículos e catorze notas revistos sobre a colação, com a regra reutilizável
de cada correção. Os achados que mais pesam:

- **1:2 traduzia contra a base.** A nota registava que a base lê *θεοῦ πατρὸς* sem
  *ἡμῶν*, e o texto escrevia «Deus, nosso Pai» por uniformidade com Filemom 1:3,
  cuja base **tem** *ἡμῶν*. Nota e versículo a contradizerem-se é o pior dos dois
  erros; ficou «da parte de Deus Pai», nível B, e a regra «uniformidade só onde o
  grego é igual» entrou na memória de estilo.
- **1:8-9 apagava uma relativa.** *οἵτινες* liga o v. 9 ao v. 8; o texto fechava o
  v. 8 com ponto e abria o v. 9 com «Eles». Fica vírgula e «os quais sofrerão».
- **Gralhas nas notas:** *introduce* por «introduz» (1:12), «adverbio» sem acento
  (3:6), «pererergoso» — palavra portuguesa inventada para explicar *περίεργος*
  (3:11), um itálico nunca fechado (3:16) e «duas letras» onde é uma só, o *ρ* de
  *τρόπος* (3:16).
- **Dois `»` sem `«` em João 1:31 e 1:34**: o discurso de João Batista continuava
  fora de citação. Apanhado porque o teste de marcas equilibradas corre sobre os
  sete livros da edição nova, não só sobre 2 Tessalonicenses.
- **Próclise brasileira** («se metendo», 3:11) num corpus que só tem ênclise.

Regras novas na memória de estilo (v1.3): ênclise com gerúndio, uniformidade só
onde o grego é igual, o artigo depois de «todo» como facto do português e não do
grego, verbo suprido em itálico, e dois vetos (próclise, derivação inventada). Guia prático em
`docs/OFICINA_TRADUCAO.md`: como decidir sem ser especialista, recomendação
fundamentada das duas unidades C, e o que o responsável pode rever sem saber grego.

### Seis livros lapidados e notas migradas (ainda 2026-11-20)

- A lapidação chegou a João 1, Tito e Judas (`scripts/lapidar_seis.py`) e a
  regra de *πᾶς* foi corrigida no mesmo dia: artigo depois de «todo», como a
  Almeida de 1911 impressa em Portugal.
- Os cinco livros curtos foram colacionados (`docs/colacao/`) e as 123 notas
  de enchimento foram substituídas por Análise Léxica do piloto aprovado e
  Crítica Textual do aparato + colação, com nível de certeza por versículo
  (`scripts/migrar_notas_cinco.py`). Decisões registadas em
  `docs/CRITICA_TEXTUAL.md` §10; nível C em Judas 1:5 e 1:22–23.
- Os sete livros têm agora `bibliography` e `review` em **RASCUNHO**.
- Comparação com ARC/ACF/NVI/NTLH/ALM1911, incluindo Hebreus 11:1 como
  demonstração fora da edição: `docs/COMPARACAO_POPULAR.md`.

Estado do livro: **RASCUNHO**, com `review` a declarar revisão editorial e
especializada pendentes e as duas unidades de nível C (2:13 e 3:6) nomeadas.
37 dos 47 versículos diferem da versão de 19/11, cuja voz foi aprovada; esta
redação não foi lida pelo responsável.

### Marcas de citação desequilibradas (2026-11-22)

- **João 4, linha legada.** Cinco versículos (12, 20, 22, 23, 24) fechavam a
  citação e não a abriam: o discurso da samaritana e o de Jesus vieram cortados
  verso a verso e cada continuação perdeu o « de entrada. Reabre-se em cada um;
  o capítulo fecha a zero. É o mesmo remédio que já tinha sido aplicado a João
  1:31 e 1:34 e a mesma família de defeito.
- **Malaquias 3–4.** A fala que abre em 3:17 só fechava em 4:1 («diz o SENHOR
  dos Exércitos»), a cavalgar a divisão de capítulo, que o teste de marcas não
  admite. Fecha-se em 3:18 e reabre-se em 4:1: mudam duas marcas de pontuação,
  não muda nenhuma palavra, e o MD e o JSON continuam iguais versículo a
  versículo.
- **Teste de migração com âmbito corrigido.** As três secções e o estado
  RASCUNHO valem para os sete livros que a migração de 2026-11-20 tocou (os
  cinco curtos, João e 2 Tessalonicenses). Os lotes posteriores foram aprovados
  com notas BEE de outra forma; para eles exige-se proveniência declarada e
  estados editoriais conhecidos, não o formato migrado.

### Guardas com âmbito declarado (2026-11-22)

- **`verificar_estilo.py`** exigia as três secções da casa a todos os livros da
  edição nova: 576 versículos chumbavam por não terem rótulos que nunca
  tiveram. O âmbito passou a estar declarado em
  `bee.inspetor.LIVROS_FORMATO_CASA` (os sete livros da migração); a linha
  legada e os lotes em prosa ficam de fora. O motor (`bee/porta.py`) continua a
  exigir as secções a todo o texto **novo**. Restam três achados reais, na fila
  abaixo.
- **`verificar_dados.py`** relata os versículos marcados como pendentes. Num
  rascunho não chumba (o compilador já impede edição final com pendentes), mas
  um versículo pendente dentro de um bloco `aprovado…` **chumba**
  (`pendentes_em_aprovados`): aprovar texto que não existe não passa.
- **`verificar_notas_colacao.py`** (novo) confere as notas de cada versículo
  com a colação: siglas do aparato, «sem variante» sobre aparato não vazio,
  TR que coincide ou diverge contra as formas normalizadas, `[[ ]]` soltos,
  histórico de correções e texto de quarentena. Sai com erro (código 1) a
  qualquer problema listado; em João não há nenhum.
- **`limpar_historico_notas.py`** (novo) retira o histórico de correções das
  «Notas de redação» (frase a frase, mantendo a justificação) e recusa
  qualquer livro com bloco aprovado.
- **Decidido — «estar a + infinitivo» é a forma da casa.** A regra antiga
  proibia a perífrase e mandava usar gerúndio, mas três versículos já aprovados
  usavam-na (Rute 2:9 «estão a ceifar», Rute 4:3 «está a vender», Habacuque 1:5
  «estou a fazer») e a proibição contradizia a norma europeia que a casa segue
  na ortografia e na ênclise. Decisão do responsável de 22/11/2026: a perífrase
  passa a ser a forma normal do progressivo; os cinco progressivos com gerúndio
  (João 1:28, 3:23, 3:26; 2Ts 1:3; 3Jo 1:10) ficam como variante aceite e
  **nenhum texto aprovado muda**. A guarda deixou de os assinalar
  (`bee/inspetor.py`), a memória de estilo, `ESTILO_BEE.md` e
  `OFICINA_TRADUCAO.md` foram atualizados.

### Lote 7 — Filipenses (2026-11-22)

- **4 capítulos, 104 versículos** de primeira redação BEE a partir do SBLGNT
  (`d7f35ad`) e do seu aparato: 91 notas de trabalho e 35 variantes explicadas no
  JSON; leitura em [`edicoes/nova/FILIPENSES.md`](../edicoes/nova/FILIPENSES.md) e
  registo em [`LOTE_07.md`](../edicoes/nova/LOTE_07.md).
- **Decisões de fundo:** 2:6 ἁρπαγμός, «algo a que se agarrasse» (a ARC e a ARA
  dizem «usurpação», a NVI «usar como vantagem»); 2:7 μορφή/σχῆμα; 3:8 σκύβαλα,
  «lixo»; 3:9 πίστις Χριστοῦ, «fé em Cristo», com a leitura «fidelidade de Cristo»
  registada na nota; 4:13 sem o «em Cristo» que a tradição bizantina acrescenta.
- **Estado:** `aprovado editorialmente` nos quatro capítulos, pelo responsável,
  **só quanto à voz e à legibilidade**. A revisão especializada está
  **pendente** e não é certificação de fidelidade textual.
- **Compilação de controlo:** 17/66 livros, 53/1.189 capítulos, 1.016 versículos,
  build PARCIAL. Os 26 marcadores de João 4:29–54 que estavam aqui como
  pendentes já estão fechados (ver a correção de João abaixo).

### Correção de João (2026-11-20)

- **João 1–4 fechado**: 166 versículos, 0 pendentes. João 4:29–54 escrito com
  `scripts/fechar_joao4.py` (script removido em 2026-11-22; recuperável no histórico) (texto, Análise Léxica e Síntese).
- **Greek conferido com a fonte**: os 166 versículos de `base.sblgnt` coincidem
  com `John.txt` do SBLGNT no pin `d7f35ad`, em bruto, sem diferença nem após
  normalização.
- **Notas regeneradas** a partir da colação (`scripts/regenerar_critica.py`):
  o diário de correções, os `[[ ]]`, a quarentena e as siglas em falta saíram.
  `verificar_notas_colacao.py` passa em João.
- **Texto corrigido em 1:43** (`<i>Jesus</i>` → `Jesus`), 4:27 («estivesse a
  falar» → «estivesse falando», pela forma da casa) e 4:35–38 (aspas «“…”»).
- **Fora do âmbito e por fazer:** João 5 (1 versículo em curso); a Análise
  Léxica de João 1:14 usa a palavra «redação» no sentido comum (não é resíduo).
- **Estado de João:** continua `rascunho` (sem aprovação do responsável) e a
  revisão especializada está pendente.

### Pendências abertas (atualizado em 2026-11-22)

- **2 Tessalonicenses** (aprovada editorialmente, voz; revisão especializada pendente): 47 versículos, 0 avisos do verificador de notas. A redação é regenerada por `scripts/regenerar_2ts.py`; não se edita o JSON à mão.
- **Tito, Judas e Filemom** (`rascunho`): texto alterado depois da aprovação do piloto. Reaprovação do responsável pendente (decisão D1); revisão especializada pendente. Filemom: 1:2 (colchetes retirados) e 1:16 (singular do original).
- **2 e 3 João** (aprovados editorialmente, voz; revisão especializada pendente). Cada carta tem o seu MD de leitura (`edicoes/piloto/2_JOAO.md`, `3_JOAO.md`).
- **João 1–4** (`rascunho`): sem aprovação do responsável; revisão especializada pendente.
- **Notas dos MD de piloto** (Filemom, Tito, Judas): o texto dos versículos já coincide com o JSON; as notas dos MD são a versão anterior à migração de 2026-11-20 e ainda não foram sincronizadas.

### Estado atual dos livros (edição nova, JSON)

| Livro | Estado nos blocos editoriais | Revisão especializada |
|---|---|---|
| Rute (4 cap.) | aprovado editorialmente | pendente |
| Jonas (4 cap.) | aprovado editorialmente | pendente |
| Miqueias (7 cap.) | aprovado editorialmente | pendente |
| Naum (3 cap.) | aprovado editorialmente | pendente |
| Habacuque (3 cap.) | aprovado editorialmente | pendente |
| Sofonias (3 cap.) | aprovado editorialmente | pendente |
| Ageu (2 cap.) | aprovado editorialmente | pendente |
| Malaquias (4 cap.) | aprovado editorialmente | pendente |
| João (4 cap.) | rascunho | pendente |
| Filipenses (4 cap.) | aprovado editorialmente | pendente |
| 1 Tessalonicenses (5 cap.) | aprovado editorialmente | pendente |
| 2 Tessalonicenses (3 cap.) | aprovado editorialmente | pendente |
| Tito (3 cap.) | rascunho | pendente |
| Filemom (1 cap.) | rascunho | pendente |
| 2 João (1 cap.) | aprovado editorialmente | pendente |
| 3 João (1 cap.) | aprovado editorialmente | pendente |
| Judas (1 cap.) | rascunho | pendente |

Livros só em Markdown, sem JSON (Oseias, Joel, Amós, Obadias, Zacarias): ver `edicoes/nova/LOTE_03.md`, `LOTE_04.md` e `LOTE_05.md`. Revisão especializada pendente em todos.

## Próximas etapas

| Etapa | Estado |
|---|---|
| 1. Actions sob controlo | feita e aplicada; cron horário e relógio prontos a colar (AGENDADOR.md) |
| 2. Dados no `main` | feito: 19 capítulos completos/818 versículos guardados |
| 3. Motor de produção | feita no ramo: quarentena, troca de provedor, lote real, cache, `/models` |
| 4. Artefactos e publicação | feita no ramo: 3 ZIP por execução, verificação, release; falta aplicar o workflow |
| 5. Documentação coerente | feita: README curto, runbook, arquitetura e editorial; guias antigos em `arquivo/` |
| 6. CI e testes | proposta em `docs/ci.yml`; testes de higiene e documentação feitos |
| 7. Diagnóstico do cron | feito: `schedule` nunca correu; hora+cron reduzidos, relógio e pinger documentados |
| 8. Limpeza física | feita: raiz curta e antigos em `docs/arquivo/` |
| 9. Verificação final | por fazer |
| 10. Crítica textual aplicada | feita para 2 Tessalonicenses; falta colacionar os outros livros da edição nova e rever as duas unidades de nível C |
