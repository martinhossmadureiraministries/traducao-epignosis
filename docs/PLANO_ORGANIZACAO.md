# Plano de organização e correção da BEE

> **Estado:** plano proposto em 17/11/2026, depois de auditar o repositório, o ramo
> `bee-dados`, o workflow e as duas execuções do GitHub Actions.
> **Nada em produção foi alterado.** Nenhum ficheiro de dados, módulo, ramo ou
> segredo foi apagado. A execução fica congelada até a Etapa 1 estar concluída.
>
> **Regra desta reorganização:** primeiro tornar a produção **previsível e
> recuperável**; depois aumentar o ritmo. Não vale a pena produzir mais capítulos
> enquanto se perdem os que já foram gerados.

---

## 0. Resumo executivo

O projeto tem um bom motor, mas a operação está a perder trabalho por cinco
motivos concretos:

1. **O GitHub Actions espera demasiado tempo.** A Groq devolveu `HTTP 429` com
   `Retry-After` de **523 s, 1176 s, 989 s e 1542 s** e o programa dormiu esse
   tempo todo. Uma única tentativa podia durar 26 minutos. A execução foi
   cancelada aos 50 minutos, com trabalho já gerado e não publicado.
2. **O trabalho só é publicado no fim.** João 18:1–12 foi guardado no disco do
   runner, mas o `commit` para o ramo `bee-dados` só acontece no fim do ciclo.
   Ao ser cancelada, a execução perdeu esses versículos.
3. **Os dados estão partidos entre `main` e `bee-dados`.** O `main` tem 5
   capítulos; o `bee-dados` tem 18. Quem clona o `main` não vê João 5–17.
4. **O resumo do Actions não diz a verdade.** A lista de provedores é escrita à
   mão no YAML e inclui OVHcloud/OpenRouter mesmo quando não têm chave; a frase
   “a produção continua pela OVHcloud” é impressa sempre, mesmo quando a OVH
   falhou ao listar modelos.
5. **O cron nunca disparou.** Desde a criação do workflow só existem **duas
   execuções, ambas manuais**; zero execuções `schedule`. O projecto não está a
   produzir sozinho como a documentação promete.

Além disso, a documentação tinha contagens de testes e de capítulos
 desactualizadas, chamava o repositório de privado quando é público, e havia
ZIPs de versões antigas que confundiam.

---

## 1. Diagnóstico confirmado

### 1.1 O que o GitHub Actions fez

| Execução | Quando (UTC) | Como foi lançada | Resultado | Duração |
|---|---|---|---|---|
| #7 | 17/11 04:30 | manual | sucesso | 4m36 |
| #12 | 17/11 08:43 | manual | **cancelada** | 50m17 |

- Execuções **agendadas**: **0**.
- Artefactos existentes: apenas `BEE-modulos-7` (152 KB). Não existe
  `BEE-capitulos-*`, porque a execução #7 usou uma versão antiga do workflow,
  sem esse passo, e a #12 foi cancelada antes de exportar.
- Release `bee-previa`: **não existe**.
- Último commit no `bee-dados`: 17/11 05:40 UTC, com **18/1189 capítulos**.

### 1.2 Porque a execução “nunca acaba”

Trecho do registo da execução #12 (screenshot do responsável):

```text
A gerar João 18 (40 versículos)...
groq: HTTP 429; nova tentativa em 523.0s (1/3).
groq: HTTP 429; nova tentativa em 62.0s (2/3).
  Guardados João 18:1-6.
groq: HTTP 429; nova tentativa em 1176.0s (1/3).
groq: HTTP 429; nova tentativa em 17.0s (2/3).
  Resposta inválida ou truncada (... <br>.); a dividir o lote para 3 versículo(s).
  Guardados João 18:7-9.
groq: HTTP 429; nova tentativa em 989.0s (1/3).
  Guardados João 18:10-12.
groq: HTTP 429; nova tentativa em 1542.0s (1/3).
Error: The operation was canceled.
```

Causa técnica:

- `bee/rede.py::_retry_after` devolve o valor do cabeçalho `Retry-After` **sem
  limite** e `ClienteHTTP.obter` faz `time.sleep(atraso)` com esse valor.
- `bee/ia.py::MotorIA._requisicao` tenta 3 vezes **antes** de levantar
  `CotaExcedida`; o `Rodizio` só passa ao provedor seguinte depois disso.
- Resultado: 3 × `Retry-After` grande = dezenas de minutos no mesmo provedor,
  mesmo com o Gemini disponível.
- O `timeout-minutes: 50` do workflow é maior do que o intervalo do cron (20
  min), portanto as execuções podem sobrepor-se ou enfileirar-se.

### 1.3 Porque os capítulos “não aparecem”

- O `main` tem **Filemom 1 + João 1–4** (5 capítulos, 191 versículos).
- O ramo `bee-dados` tem **Filemom 1 + João 1–17** (18 capítulos, 766 versículos).
- O `main` nunca recebe os dados produzidos. Quem clona o `main`, ou abre a
  página do repositório, vê 5 capítulos.
- João 18:1–12 foi gerado na execução #12, mas **não foi commitado** (o commit
  só acontece no fim) e perdeu-se quando o job foi cancelado.
- O MyBible só mostra capítulos completos e consecutivos desde o capítulo 1.
  Um capítulo em curso não entra no módulo — isto é correto, mas precisa de ser
  dito de forma clara e de haver uma prévia HTML para leitura.

### 1.4 Porque a lista de IAs “mente”

O passo “Provedores nesta execução” do workflow percorre uma lista fixa:

```text
OVH_API_KEY:OVHcloud
GEMINI_API_KEY:Gemini
GROQ_API_KEY:Groq
OPENROUTER_API_KEY:OpenRouter
```

Depois imprime sempre:

> “Sem chave para: OpenRouter. A produção continua pela OVHcloud (2 ped/min ~
> 2.880 versículos/dia).”

Mas:

- OpenRouter **não** está na fila;
- a OVH **falhou** a listagem de modelos (`ovh: não foi possível listar os
  modelos; a usar os nomes de reserva do código`);
- a linha verdadeira é `BEE · nuvem: groq, ovh, gemini`, impressa pelo
  `nuvem.py`;
- a OVH entra sempre na fila por ter `sem_chave=True`, mesmo sem chave e sem
  teste de saúde;
- o `--testar` não foi executado na #12 (`pular_teste` ou passo condicionado).

### 1.5 Outros desalinhamentos confirmados

| Item | Realidade | Onde está escrito |
|---|---|---|
| Testes | **136** testes unittest (2 skipped) + 10 do worker | README: 71; AUTOMACAO: 91 |
| Progresso | 18 capítulos no `bee-dados` | README/ENTREGA: 5 capítulos, João 5 |
| Visibilidade | repositório **público** | AUTOMACAO: “privado” |
| `BEE-gerador.zip` | snapshot antigo (20 ficheiros) | apresentado como pacote |
| `entregas/BEE-previa.zip` | compilado a partir dos 5 capítulos do `main` | parece a prévia atual |
| `modelos/bee-autopiloto.yml` | duplicado de `.github/workflows/...` | teste exige igualdade |
| `worker/` | workflow Mistral pago, sem uso atual | README não o distingue |
| Cron | 0 execuções agendadas | docs prometem produção a cada 15/20 min |

### 1.6 O que NÃO está errado

- Os 136 testes passam em ~2 s, sem rede.
- Não há chaves nem segredos no repositório.
- O `.gitignore` protege `.env`, cache, SQLite e estado.
- A compilação é atómica e valida a integridade dos dois SQLite.
- O `main` e o `bee-dados` têm os mesmos `sources`, `review` e `bibliography`
  para João; o que falta no `main` são capítulos e `history`.

---

## 2. Princípios que passam a valer

1. **Uma única fonte de verdade para os dados.** Não pode haver dois sítios
   com contagens diferentes.
2. **Trabalho gerado é trabalho guardado.** Cada capítulo (ou fatia) é
   publicado antes de se pedir o seguinte.
3. **Tempo limitado.** Nenhuma execução pode durar mais do que o intervalo do
   cron. Nenhuma espera de rede pode ser superior a 45 s.
4. **Relatório honesto.** O resumo só lista provedores que existem na fila e
   só afirma fallback se ele existir e responder.
5. **Falhar cedo é melhor do que falhar devagar.** Se não há provedor saudável,
   a execução termina em minutos com diagnóstico, não em 50 minutos.
6. **Nada de dados inventados.** Um versículo que falha persistentemente fica
   marcado como pendente para revisão; não é traduzido por suposição.
7. **Documentação curta e atual.** Um README de entrada, um documento de estado
   gerado a partir dos dados, e o resto em `docs/`.

---

## 3. Plano por etapas

### Etapa 0 — Congelar e decidir (hoje, ~20 min)

**Objetivo:** parar a produção, tirar fotografia do estado e fechar as decisões
que condicionam tudo o resto.

Ações:

- [ ] Desativar temporariamente o workflow (`gh workflow disable`) — **403** com
      o token atual; usar a UI, para não haver execuções manuais acidentais.
- [ ] Criar uma etiqueta de segurança no `main` e no `bee-dados`
      (`estado-17nov-2026`) para poder voltar atrás.
- [ ] Registar em `docs/ESTADO.md` a fotografia real: 18 capítulos, 766
      versículos, último commit, artefactos, execuções.
- [ ] Responder às quatro decisões da secção 5.

**Aceitação:** ninguém corre produção; existe um ponto de restauro; as decisões
estão escritas.

---

### Etapa 1 — Pôr o GitHub Actions sob controlo (prioridade máxima, 2–3 h)

> **Estado (17/11, 14:xx UTC):** implementada no ramo
> `arena/e4c173dc-traducao-epignosis`; ver `docs/ESTADO.md`. Falta a validação
> numa execução real, que só acontece depois do merge para o `main`.

**Objetivo:** uma execução nunca passa do tempo previsto, nunca perde o que
gerou e diz a verdade no resumo.

#### 1.1 Limite de tempo real

- [x] `timeout-minutes` do job: **12 min** (menor que os 20 min do cron).
- [x] Prazo interno no `nuvem.py` (`BEE_TEMPO_MAXIMO`, padrão **9 min**): parar a
      geração a tempo de compilar, publicar e carregar artefactos.
- [x] Cron: mantido de **20 em 20 minutos** (7,27,47), por decisão do utilizador.
      minutos com timeout de 12. A soma tem de fechar.
- [ ] `concurrency`: decidir entre `cancel-in-progress: true` (não empilhar) ou
      fila com timeout curto. Recomendação: cancelar a execução anterior e
      publicar sempre antes de sair.

#### 1.2 Política de rede e de quota

- [x] `ClienteHTTP.obter`: **limitar `Retry-After` a 45 s**. Se o serviço pedir
      mais do que isso, levantar `CotaExcedida` imediatamente e passar ao
      provedor seguinte em vez de dormir 20 minutos.
- [x] `MotorIA._requisicao`: no máximo **1 tentativa por modelo** em `429`;
      o rodízio decide. Manter as tentativas apenas para 5xx/rede.
- [x] `Rodizio`: trocar de provedor ao primeiro `429`, sem esperar 3 falhas.
      Guardar o motivo no diário.
- [ ] Limite global de espera por lote (ex.: 2 min); se exceder, falha o lote e
      o ciclo seguinte recomeça do ponto guardado.
- [x] Contar **todas** as tentativas HTTP no orçamento diário, não só os
      pedidos que tiveram sucesso.

#### 1.3 Fila de provedores verdadeira

- [x] Só entram na fila provedores com chave **validada** ou com opt-in
      explícito. A OVH anónima fica **desligada por omissão**; para a usar,
      `BEE_OVH_ANONIMO=1`.
- [ ] O passo “Testar as ligações” passa a ser **obrigatório** para os
      provedores com chave; um provedor que falhe o teste não entra na fila.
- [x] O resumo do Actions é gerado a partir da lista real de motores (a mesma
      que o `nuvem.py` imprime), não de uma lista fixa no YAML.
- [x] Remover a frase automática “a produção continua pela OVHcloud”; escrever
      “provedores ativos: …” e “provedores sem chave: …” sem prometer fallback.
- [ ] `--doctor` ganha uma saída legível por máquina (`--doctor --json`) para o
      workflow poder resumir sem duplicar lógica.

#### 1.4 Publicar cedo e sempre

- [~] Publicar no ramo de dados **depois de cada ciclo** (checkpoint imediato); falta o commit por capítulo.
      fatia), não só no fim.
- [ ] Mover compilação, exportação, artefactos e release para um bloco
      `finally`/equivalente, executado mesmo quando o ciclo falha.
- [x] Instalar um handler de `SIGTERM` no `nuvem.py` para publicar o que existe
      antes de o runner matar o processo.
- [x] `upload-artifact`: falhar (ou avisar de forma visível) se a pasta estiver
      vazia; nunca produzir artefacto vazio com “success”.
- [x] Passo de verificação que lista o conteúdo do ZIP e confirma que
      `BEE.SQLite3` e `BEE.commentaries.SQLite3` têm versículos.

#### 1.5 Perceber porque o cron não dispara

- [ ] Criar um workflow mínimo de diagnóstico (`cron: '*/5 * * * *'`) que só
      escreve a hora no resumo. Se ele disparar, o problema é a expressão ou o
      registo do workflow principal; se não disparar, é configuração do
      repositório/agendador.
- [ ] Reenviar o workflow principal para o `main` e confirmar
      `gh run list --event schedule`.
- [ ] Se o cron continuar sem disparar: usar um agendador externo que chame
      `workflow_dispatch` por API, ou um cron local/Raspberry Pi. Não deixar a
      produção dependente de um mecanismo que não funciona.

**Aceitação da Etapa 1:**

- Uma execução manual termina em menos de 15 min.
- Nenhum `Retry-After` superior a 45 s aparece no registo.
- Uma execução cancelada a meio deixa os versículos já gerados no `bee-dados`,
  um artefacto com conteúdo e um resumo verdadeiro.
- O resumo lista apenas `gemini`/`groq` (ou os que estiverem realmente ativos).
- Existe uma explicação confirmada para o cron (dispara ou substitui-se).

---

### Etapa 2 — Consolidar os dados numa só fonte (1–2 h)

**Objetivo:** acabar com “os capítulos existem mas não aparecem”.

Recomendação: **o `main` passa a ser a fonte única**. O repositório é pequeno
(≈150 KB de JSON) e o utilizador não tem de saber que existe um ramo escondido.
O `bee-dados` fica arquivado como histórico.

Ações:

- [x] Migrar os 18 capítulos do `bee-dados` para o `main`, preservando
      `history`, `review`, `bibliography` e `sources` (eram idênticos).
- [x] Corrigir `nuvem.py`: o `main` é a fonte; `_unir_progresso` deixou de ser
      usado no caminho normal e o `BEE_REMOTO` foi removido.
- [ ] Regenerar João 18:1–12 (perdidos na execução #12). O estado aponta para
      João 18:1; falta uma execução com chaves. Custo estimado: 1–2 pedidos.
- [x] Remover a dependência do `worktree /tmp/bee-remoto` e do `git fetch` do
      ramo de dados; o checkout do `main` já traz tudo.
- [~] Criar `scripts/verificar_dados.py` (JSON e regressões; falta a comparação
      com os módulos SQLite).
- [x] Criar etiqueta/tag de segurança: `arquivo-bee-dados-2026-11-17`.

**Aceitação:** um clone limpo do `main` mostra 18/1189 no `--status`;
`--compilar` produz módulos com 766 versículos; não há dois sítios com números
diferentes.

---

### Etapa 3 — Corrigir o motor de produção (2–3 h)

**Objetivo:** produzir de forma previsível, sem bloqueios e sem contar mal a
quota.

- [x] Contabilidade de pedidos: `ClienteHTTP` conta tentativas por provedor;
      `Agendador` grava esses números no estado. O teto diário passa a ser real.
- [x] Orçamento por provedor calculado com o lote **daquele** provedor (hoje
      `_tectos_por_provedor(args.lote)` ignora `--versos-por-pedido`).
- [x] Em resposta JSON inválida a meio:
      - [x] dividir até 1 versículo (já existe);
      - [x] se continuar inválida, tentar **outro provedor/modelo** para esse lote;
      - [x] se todos falharem, gravar um marcador de “versículo pendente” com
        comentário explícito e seguir, em vez de bloquear o capítulo inteiro.
- [x] Um único versículo problemático não pode parar a fila para sempre. Estado
      de quarentena em `livros_json/.bee/quarentena.json`, com referência,
      provedor, erro e data.
- [x] Cache da descoberta de modelos por execução (não repetir `/models` a cada
      motor).
- [x] Lote por provedor revisto com os dados reais: Gemini 6–8, Groq 4–6,
      OVH 4. Lotes grandes truncam e gastam quota a repetir.
- [x] Testes de regressão:
      - [x] `Retry-After` de 1200 s não dorme 1200 s;
      - [x] `429` troca de provedor em menos de X segundos;
      - [x] o orçamento conta tentativas falhadas;
      - [x] um JSON inválido num versículo não bloqueia o capítulo;
      - [x] o resumo só lista provedores ativos.

**Aceitação:** uma rajada de 429 não consome mais de 2 min; o estado diário
reflete os pedidos reais; um versículo problemático fica em quarentena e a fila
continua.

---

### Etapa 4 — Artefactos e publicação que se encontram (1 h)

**Objetivo:** “está no Actions” passa a significar “posso descarregar e abrir”.

- [x] Um único pacote por execução: `BEE-modulos-<run>.zip` com
      `BEE.SQLite3`, `BEE.commentaries.SQLite3`, `LEIA-ME.txt`.
- [x] Pacote de leitura: `BEE-capitulos-<run>.zip` com um HTML por capítulo,
      incluindo capítulos em curso (marcados “em curso: X de Y”).
- [x] Pacote de diagnóstico: `estado.json`, `diario.md`, `quarentena.json`.
- [x] Release `bee-previa` criada automaticamente na primeira execução com
      conteúdo; assets atualizados com `--clobber`.
- [x] Nomes com número da execução; retenção explícita (14 dias).
- [x] Passo “Verificar artefactos” que falha se o ZIP não tiver os dois módulos
      ou se o módulo não tiver versículos.

**Aceitação:** qualquer execução com progresso tem, no mínimo, um ZIP
descarregável e um resumo com o link/nome; o ZIP abre no MyBible.

---

### Etapa 5 — Organizar o repositório e a documentação (2 h)

**Objetivo:** uma pessoa nova percebe o projeto em 5 minutos e não encontra
números contraditórios.

Estrutura proposta:

```text
README.md                  entrada: o que é, como correr, onde estão os dados
docs/ESTADO.md             fotografia gerada a partir dos dados (18/1189, etc.)
docs/OPERACAO.md           runbook: ativar, pausar, recuperar, diagnosticar
docs/ARQUITETURA.md        módulos, fluxo, fontes, formato JSON
docs/EDITORIAL.md          diretrizes, variantes, revisão (absorve PLANO_BEE)
docs/arquivo/              documentos antigos e ZIPs fora de uso
scripts/                   verificar_dados.py, sincronizar_workflow.py, estado.py
```

Ações:

- [x] `README.md` curto e verdadeiro; detalhes movidos para `docs/`.
- [x] `ENTREGA.md` e `COMECAR_HOJE.md`: atualizar ou arquivar (não manter três
      guias com números diferentes).
- [x] `AUTOMACAO.md`: atualizar quotas, provedores, janela, contagens e
      visibilidade do repositório; remover o que já não é usado.
- [x] `BEE-gerador.zip`: mover para `docs/arquivo/` ou apagar (é um snapshot
      antigo do código).
- [x] `entregas/BEE-previa.zip`: regenerar a partir dos 18 capítulos ou remover
      até haver uma prévia válida.
- [ ] `modelos/`: manter uma só cópia do workflow. Recomendação: `.github/` é a
      fonte; `scripts/sincronizar_workflow.py` gera `modelos/`, e o teste
      continua a vigiar.
- [x] `worker/`: decidir entre “experimental” documentado ou arquivo. Não pode
      parecer parte do fluxo principal.
- [x] `requirements.txt`: separar `requirements-dev.txt` (pytest,
      pytest-asyncio, mistralai-workflows) e documentar o Python mínimo.
- [x] Referir claramente que o repositório é público e que o conteúdo é
      rascunho; se passar a privado, rever minutos de Actions e segredos.

**Aceitação:** não restam afirmações antigas sobre contagens de testes,
progresso ou visibilidade do repositório nos documentos actuais; a raiz tem
poucos ficheiros; um leitor sabe qual é o comando de produção.

---

### Etapa 6 — CI e testes (1–2 h)

- [ ] `.github/workflows/ci.yml` em `push`/`pull_request` (proposta pronta em
      `docs/ci.yml`; falta colar na UI por causa da permissão `workflows`).
- [ ] Testes do worker em job separado (ou marcados como opcionais) com as
      dependências fixadas.
- [x] Teste que falha se houver segredos, `.env` ou SQLite versionados (`tests/test_repositorio.py`).
- [x] Teste que compara as contagens documentadas com os dados reais
      (`tests/test_documentacao.py` e `scripts/verificar_documentacao.py`).
- [ ] (Opcional) `ruff`/`black` para consistência.

**Aceitação:** um PR não faz merge com testes vermelhos; o número de testes no
README é lido do CI, não escrito à mão.

---

### Etapa 7 — Validar no MyBible (1 h)

- [ ] Compilar a partir dos 18 capítulos consolidados.
- [ ] Abrir os dois SQLite com um leitor independente e conferir 766 versículos
      e 766 comentários.
- [ ] Copiar para o Android e abrir Filemom 1 e João 1–17.
- [ ] Confirmar que os avisos de rascunho aparecem e que a prévia HTML abre no
      telemóvel.
- [ ] Documentar o caminho exato das pastas e o procedimento de atualização.

**Aceitação:** o utilizador vê 18 capítulos no MyBible e consegue identificar
que é rascunho.

---

### Etapa 8 — Retomar a produção com ritmo controlado (contínuo)

- [ ] Reativar o workflow com 30 min de intervalo, 15 min de timeout e
      `BEE_VERSOS_POR_CICLO` moderado (ex.: 60–120).
- [ ] Observar 24 h: quantos ciclos, quantos versículos, quantos 429, quantos
      artefactos.
- [ ] Só depois aumentar o teto. O limitador é a quota gratuita, não o cron.
- [ ] Separar produção de revisão: o JSON guarda os estados; a revisão
      editorial não é automática.
- [ ] Atualizar `docs/ESTADO.md` em cada marco.

**Aceitação:** 24 h sem execuções canceladas, sem trabalho perdido e com
progresso visível no `main` e no MyBible.

---

## 4. Ordem, dependências e estimativa

| Ordem | Etapa | Depende de | Tempo estimado |
|---:|---|---|---:|
| 0 | Congelar e decidir | — | 20 min |
| 1 | Actions sob controlo | 0 | 2–3 h |
| 2 | Dados numa só fonte | 0, 1 | 1–2 h |
| 3 | Motor de produção | 1, 2 | 2–3 h |
| 4 | Artefactos e publicação | 1, 2 | 1 h |
| 5 | Documentação e limpeza | 2, 4 | 2 h |
| 6 | CI e testes | 1–5 | 1–2 h |
| 7 | MyBible | 2, 4 | 1 h |
| 8 | Retomar produção | 1–7 | contínuo |

**Caminho crítico:** 0 → 1 → 2 → 4 → 7. Só depois vale a pena acelerar a
produção (3/8).

---

## 5. Decisões que preciso do responsável

1. **Fonte de verdade dos dados**
   - **A (recomendada):** `main` passa a ter os JSON; o `bee-dados` fica
     arquivado. Mais simples de clonar e de consultar.
   - B: manter `bee-dados` como fonte e espelhar automaticamente no `main`.
   - C: repositório separado só para dados.

2. **Provedores de IA que queremos mesmo**
   - **A (recomendada):** Gemini + Groq. OVH só com opt-in e teste; remover
     OpenRouter/Cerebras/OpenAI da fila e do resumo.
   - B: Gemini + Groq + OVH (testada).
   - C: só Gemini (mais simples, mais lento).
   - D: manter todos os que tiverem chave.

3. **Cadência**
   - **A (recomendada):** cron de 30 min, timeout 15 min, 60–120 versículos por
     execução, 24 h/dia.
   - B: 20 min, timeout 12 min, blocos menores.
   - C: janela 05:00–23:00 em Luanda.
   - D: só execuções manuais até estabilizar.

4. **Visibilidade do repositório**
   - **A:** manter público (Actions ilimitados; conteúdo e release públicos).
   - B: passar a privado (2.000 min/mês; conteúdo reservado).

5. **`worker/` Mistral**
   - **A:** manter como experimental, documentado e fora do fluxo principal.
   - B: arquivar em `docs/arquivo/` para reduzir confusão.

---

## 6. O que não será feito sem autorização explícita

- Apagar o ramo `bee-dados`, `livros_json`, `rascunhos` ou qualquer capítulo.
- Reescrever texto bíblico ou comentários já gerados.
- Mudar a visibilidade do repositório.
- Remover o workflow, os segredos ou o histórico do Git.
- Publicar uma edição final: tudo continua marcado como rascunho.

---

## Anexo A — Comandos de verificação usados neste diagnóstico

```bash
# Estado do repositório e dos ramos
git log origin/main --oneline -5
git show origin/bee-dados:livros_json/500_Joao.json | python3 -c "..."

# Execuções e artefactos
gh api repos/.../actions/runs?per_page=30
gh api repos/.../actions/artifacts?per_page=20
gh run view 44049165005

# Testes
python3 -m unittest discover -s tests -v

# Progresso
python3 gerar_bee.py --status
python3 autopiloto.py --status
```

## Anexo B — Ficheiros que serão tocados na Etapa 1

| Ficheiro | Alteração |
|---|---|
| `.github/workflows/bee-autopiloto.yml` | timeout, cron, resumo real, verificação |
| `modelos/bee-autopiloto.yml` | cópia sincronizada |
| `bee/rede.py` | limite de `Retry-After`, contagem de tentativas |
| `bee/ia.py` | 429 passa ao provedor seguinte; descoberta cacheada |
| `bee/agenda.py` | orçamento real; prazo interno |
| `bee/gerador.py` | quarentena de lote inválido; ponto de paragem |
| `nuvem.py` | publicar cedo, `finally`, SIGTERM, resumo verdadeiro |
| `autopiloto.py` | opt-in da OVH; `--doctor --json`; ordem |
| `tests/` | regressões dos casos acima |
