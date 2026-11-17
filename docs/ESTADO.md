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
