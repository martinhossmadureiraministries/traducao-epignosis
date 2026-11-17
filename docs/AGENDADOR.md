# Agendador — pôr a produção a correr sem ninguém

Este documento existe por uma razão concreta: em 17/11/2026, às 21:23 UTC, o
workflow estava `active`, o ficheiro correcto estava no `main` e a produção
manual funcionava — mas o GitHub tinha **zero** execuções `schedule`. O botão
"Run workflow" não prova autonomia: quem carrega no botão é uma pessoa. Aqui
está o caminho para deixar de depender desse botão, por ordem de esforço.

Leitura rápida: faça as **fases 1 a 3** (10 minutos, tudo no site do GitHub).
A fase 4 só é necessária se, uma hora depois, o contador de execuções agendadas
continuar a zero.

---

## Fase 0 — Saber onde estamos (2 min)

```bash
python3 scripts/verificar_agendador.py
```

Lê as execuções pela API e responde à única pergunta que interessa:

| Veredicto | Significado |
|---|---|
| `a-funcionar` | há uma execução `schedule` nas últimas 3 h — está autónomo |
| `nunca-agendado` | só existem execuções manuais: o cron não dispara |
| `parado` | já disparou, mas parou nas últimas 3 h |
| `sem-execucoes` | o workflow nunca correu |

Estado em 17/11/2026, 21:23 UTC: **`nunca-agendado`** — 1 execução, manual
(`44120273655`), zero agendadas desde a criação do workflow em 16/11 às 14:42.
O cron `7,27,47 * * * *` (20 em 20 minutos) nunca chegou a ser registado.

---

## Fase 1 — Um cron que o GitHub aceita (3 min)

Cron de 20 em 20 minutos é muito frequente: o GitHub trava em silêncio
agendadores de alta frequência (filtro anti-abuso), e um cron travado não deixa
rasto nenhum — nem erro, nem aviso. Passa-se a **uma vez por hora, ao minuto 23**:
24 disparos por dia chegam para produzir ~1 900 versículos por dia, que é o
tecto imposto pela quota da IA, não pelos minutos de Actions.

O modelo já está actualizado (`docs/bee-autopiloto.yml`, `modelos/bee-autopiloto.yml`,
cron `23 * * * *`, `timeout-minutes: 15`). Falta colá-lo no ficheiro ativo:

1. Abrir
   <https://github.com/martinhossmadureiraministries/traducao-epignosis/edit/main/.github/workflows/bee-autopiloto.yml>.
2. Seleccionar tudo (`Ctrl+A`), apagar e colar o conteúdo de
   [`docs/bee-autopiloto.yml`](bee-autopiloto.yml).
3. **Commit changes** (mensagem: `cron horário ao minuto 23`).

> Porque é que isto não pode ser feito por `git push`: a integração que escreve
> neste repositório não tem a permissão `workflows`, e o GitHub recusa. A UI é o
> caminho normal para ficheiros em `.github/workflows/`.

## Fase 2 — Forçar o GitHub a re-registar o agendador (2 min)

Um ficheiro novo no `main` não garante o re-registo imediato; desactivar e
reactivar o workflow obriga o agendador a recomeçar do zero.

1. **Actions** → **BEE — produção automática** (barra lateral esquerda).
2. Menu **⋯** (à direita) → **Disable workflow**.
3. Esperar 10 segundos, **⋯** → **Enable workflow**.
4. **Run workflow** → **Run workflow** uma vez (execução manual de controlo).
   Confirme que fica verde; ela também prova que o YAML novo é válido.

Se aparecer erro de sintaxe, o problema é a colagem: refaça a fase 1 e copie o
ficheiro **inteiro**, incluindo a primeira linha (`name: BEE — produção automática`).

## Fase 3 — Um segundo relógio que vigia o primeiro (3 min)

O `bee-relogio.yml` corre de hora a hora (minuto 41), vê se a produção correu
nos últimos 65 minutos e, se não correu, despacha-a pela API. Não duplica
trabalho: quando a produção está viva, sai em segundos.

1. Abrir
   <https://github.com/martinhossmadureiraministries/traducao-epignosis/new/main/.github/workflows>
2. Nome do ficheiro: `bee-relogio.yml`.
3. Colar o conteúdo de [`docs/bee-relogio.yml`](bee-relogio.yml) (igual a
   `modelos/bee-relogio.yml`).
4. **Commit changes**.
5. **Actions** → **BEE — relógio de segurança** → **Run workflow** uma vez para
   confirmar que aparece o resumo *"A produção correu nos últimos 65 min"*.

Este relógio usa o mesmo tipo de cron do GitHub. Se ambos os crons falharem,
não há redundância possível dentro do GitHub — é para isso que existe a fase 4.

## Fase 4 — Pinger externo (só se as fases 1–3 não bastarem)

Um serviço gratuito de cron na Internet chama a API do GitHub de hora a hora.
Passa a haver dois agendadores completamente independentes.

### 4.1 Criar um token só para isto (2 min)

1. <https://github.com/settings/personal-access-tokens/new>
2. **Token name**: `bee-pinger`.
3. **Expiration**: 1 ano.
4. **Repository access** → *Only select repositories* → `traducao-epignosis`.
5. **Permissions** → *Repository permissions* → **Actions: Read and write**.
   (Mais nada. `Contents` fica em *No access*.)
6. **Generate token** e copiar (`github_pat_…`). Não colar no repositório nem
   em ficheiros do projeto.

### 4.2 Criar o trabalho no cron-job.org (3 min)

1. Conta gratuita em <https://cron-job.org> → **Create cronjob**.
2. **URL**:
   `https://api.github.com/repos/martinhossmadureiraministries/traducao-epignosis/actions/workflows/bee-autopiloto.yml/dispatches`
3. **Schedule**: *Every 1 hour*, minuto **0** (o pinger não usa o cron do
   GitHub, por isso o minuto cheio não é problema).
4. **Advanced → Request method**: `POST`.
5. **Headers**:
   | Header | Valor |
   |---|---|
   | `Accept` | `application/vnd.github+json` |
   | `Authorization` | `Bearer github_pat_…` |
   | `Content-Type` | `application/json` |
   | `User-Agent` | `bee-pinger` |
6. **Request body**: `{"ref":"main"}`
7. **Test run** → deve responder **204 No Content**. 401 = token errado;
   403 = falta `Actions: Read and write`; 404 = token sem acesso a este
   repositório.
8. Guardar. O GitHub passa a receber um `workflow_dispatch` por hora, mesmo que
   todos os crons internos estejam mortos.

Se preferir não criar token no GitHub, a alternativa é um `cron` numa máquina
sempre ligada (Raspberry Pi, VPS) com o mesmo `curl`; qualquer uma serve, desde
que seja independente do GitHub.

---

## Fase 5 — Confirmar (1 min, uma hora depois)

```bash
python3 scripts/verificar_agendador.py
```

Deve dizer `a-funcionar`. Na UI, a coluna de evento da execução mostra
**schedule** (fases 1–3) ou **Manually run** (fase 4) — a fase 4 é autónoma na
mesma, porque ninguém carregou em nada.

Para não voltar a ficar na dúvida, vale a pena olhar uma vez por dia:

| Onde | O que deve ver |
|---|---|
| `Actions` | uma execução por hora, verde ou com diagnóstico |
| Execuções do dia | 24; o repositório é público, os minutos são ilimitados |
| `artefactos` | `BEE-modulos-<n>` e `BEE-capitulos-<n>` em cada execução com capítulo novo |
| `livros_json/.bee/estado.json` | `capitulos_completos` a subir |

---

## Se ainda assim não disparar

1. **Sintoma**: `Bee — relógio de segurança` também nunca corre.
   **Causa provável**: o agendador está bloqueado ao nível da conta, não do
   repositório. **Acção**: ficar só com a fase 4 (o pinger não depende do cron).
2. **Sintoma**: aparece a execução mas falha em 10 s.
   **Causa**: YAML inválido ou `permissions` em falta. **Acção**: ver o log do
   passo, corrigir o ficheiro na UI, correr à mão.
3. **Sintoma**: corre e diz *"Sem provedor na fila"*.
   **Causa**: secrets `GEMINI_API_KEY` / `GROQ_API_KEY` em falta ou revogadas
   (Settings → Secrets and variables → Actions). **Acção**: renovar a chave.
4. **Sintoma**: corre mas produz 0 versículos (`versos: 0`).
   **Causa**: 503 do provedor ou quota diária esgotada. **Acção**: nenhuma
   imediata — o estado está intacto e o ciclo seguinte retoma no versículo
   guardado. Confirme em `livros_json/.bee/diario.md`.

## O que fica garantido, e o que não fica

- **Garantido**: com a fase 4, a produção continua com o computador desligado,
  mesmo que o GitHub deixe de agendar.
- **Não garantido**: que um dia com 503 em todos os provedores produza
  versículos. O agendador resolve *quando* o trabalho arranca; a quota e a
  disponibilidade dos serviços de IA resolvem *se* ele produz. Por isso as
  execuções verdes com `versos: 0` são normais e não pedem intervenção.
