# Estado do projeto — 17/11/2026

Este ficheiro é o **ponto único de verdade** sobre o que está feito, o que está
a meio e o que falta. O `PLANO_ORGANIZACAO.md` explica o diagnóstico e as
etapas; este documento regista a execução.

## Decisões fechadas

| Tema | Decisão |
|---|---|
| Fonte de dados | `main` (o ramo `bee-dados` deixa de ser a fonte) |
| Provedores de IA | **Gemini** (principal) e **Groq** (reserva) |
| OVHcloud | Só com opt-in explícito (`OVH_API_KEY_ATIVO=1` ou chave) |
| Cadência | cron a cada **20 min**, `timeout-minutes: 12` (proposto) |
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
- Workflow — **proposta em `docs/bee-autopiloto.yml`**
  - O GitHub recusou o push de `.github/workflows/bee-autopiloto.yml` com
    “GitHub App … without `workflows` permission”. O ficheiro ativo continua
    com `timeout-minutes: 50`; o `nuvem.py` já limita o trabalho a 11 min, mas
    a configuração do job só muda quando a proposta for copiada.
  - `timeout-minutes: 12`; cron `7,27,47` (20 min).
  - `BEE_VERSOS_POR_CICLO=80`, `BEE_TENTATIVAS_CICLO=2`,
    `BEE_TENTATIVAS=2`, `BEE_TIMEOUT=90`, `BEE_PEDIDOS_POR_DIA=500`.
  - `BEE_PROVEDORES=gemini,groq`, `OVH_API_KEY_ATIVO=0`.
  - Removido o bloco de resumo hardcoded; o `nuvem.py` é a única fonte.
  - Passo de verificação dos artefactos antes do upload.

### Testes

`python3 -m unittest discover -s tests` → **143 testes, 2 skipped, OK**.
Foram acrescentados testes para o 429 sem espera, o limite de 45 s, a contagem
de tentativas, o prazo do ciclo, o orçamento com o Gemini sozinho e o
relatório sem módulos.

### O que ainda não está validado

- Uma execução real no GitHub com o código novo (só depois do merge).
- O workflow ativo: falta aplicar `docs/bee-autopiloto.yml` em
  `.github/workflows/bee-autopiloto.yml` e em `modelos/bee-autopiloto.yml`
  (têm de ficar iguais). Enquanto isso, o job continua com 50 min, mas o
  `nuvem.py` pára aos 11 min.
- O `SIGTERM` num cancelamento real.
- O cron: continuam a existir **0 execuções `schedule`** desde a criação do
  workflow. O ficheiro está `active`, o `on.schedule` está no `main` e o
  repositório não está inativo. Hipótese principal: o agendador do GitHub
  ainda não registou o workflow ou a conta/organização tem uma política que o
  impede. A verificação prática é, depois do merge, correr uma vez à mão e
  confirmar se aparece uma execução `schedule` no ciclo seguinte.

### Como desativar o workflow

A API recusou `gh workflow disable` com **HTTP 403** (a integração não tem
âmbito de administração). Para parar a produção sem apagar o ficheiro:

1. GitHub → **Actions** → **BEE — produção automática**.
2. Menu **⋯** (canto superior direito) → **Disable workflow**.
3. Para voltar: **Enable workflow**.

### Aplicar o workflow novo (devido à permissão `workflows`)

1. `./scripts/aplicar_workflow.sh` copia `docs/bee-autopiloto.yml` para
   `.github/workflows/bee-autopiloto.yml` e para `modelos/bee-autopiloto.yml`
   (o teste `test_modelo_e_workflow_ativo_sao_iguais` exige que sejam iguais).
2. Confirme com `python3 -m unittest tests.test_workflow_sincronizado -v`.
3. Faça commit e push com uma conta/integração que tenha a permissão
   `workflows` no GitHub.
4. Em **Actions → BEE — produção automática → Run workflow**, corra uma vez à
   mão para confirmar o resumo, o `RELATORIO.txt` e o tempo total.

## Próximas etapas

| Etapa | Estado |
|---|---|
| 1. Actions sob controlo | implementada; falta validar em execução real |
| 2. Dados no `main` | por fazer |
| 3. Capítulos e artefactos visíveis | base pronta (`RELATORIO.txt`); falta publicar/validar |
| 4. Documentação coerente | por fazer (`AUTOMACAO.md` ainda diz 15 min) |
| 5. Diagnóstico do cron | por fazer |
| 6. Limpeza física | por fazer |
| 7. Verificação final | por fazer |
