# Produção automática da BEE — guia prático

> **Quer começar hoje?** Siga [COMECAR_HOJE.md](COMECAR_HOJE.md): é o mesmo conteúdo em ordem cronometrada, com os atalhos para a nuvem e para o MyBible.

Este guia responde a três perguntas: **como** a produção passa a acontecer sozinha, **o que** é realista esperar com ferramentas gratuitas, e **como** você põe os ficheiros no MyBible em cinco minutos.

> **Antes de tudo, uma correção de expectativa.** A BEE tem 1.189 capítulos e 31.102 versículos. Nenhuma ferramenta gratuita gera 31 mil versículos com tradução + comentário léxico em poucos dias: os planos gratuitos não são ilimitados e cada versículo consome tokens de entrada e de saída. O que se automatiza aqui é o **ritmo**: o programa trabalha sozinho, em blocos pequenos, respeitando a quota gratuita, e você vai lendo o que já está pronto. A estimativa honesta com um plano gratuito está no fim.

---

## 1. O que foi construído

| Peça | Para que serve |
|---|---|
| `autopiloto.py` | O motor. Trabalha em ciclos (por exemplo, 6 versículos a cada 5 minutos), compila e registra o progresso. Anda com o seu computador. |
| `nuvem.py` | O mesmo trabalho numa GitHub Action: continua com o computador desligado. |
| `modelos/bee-autopiloto.yml` | O agendador na nuvem (a cada 15 minutos, das 05h às 23h de Luanda). É um **modelo**: copie-o para `.github/workflows/` para o ativar (ver secção 4). |
| `bee/ia.py` | Cinco provedores, todos com plano gratuito: **Gemini, Groq, Cerebras, OpenRouter** (e OpenAI, opcional e paga). |
| `bee/agenda.py` | Estado, diário legível, janela diária, tetos de quota e rodízio de provedores. |
| `bee/gerador.py` | Agora grava **por fatia**: pode parar a meio do capítulo e retomar sem repetir pedidos. |

Cada peça funciona offline nos testes: 91 testes automáticos não usam rede nem chaves.

### O que cada execução faz

1. Vê qual é o próximo capítulo incompleto (na ordem das oito fases do `PLANO_BEE.md`).
2. Pede à IA um bloco pequeno de versículos, com o texto original (WLC/SBLGNT) e o contexto do versículo anterior para manter o vocabulário coerente.
3. Valida tudo (HTML permitido, colchetes de variantes, numeração) e **grava imediatamente** no JSON do livro.
4. Quando um capítulo fica completo, **recompila** `BEE.SQLite3` e `BEE.commentaries.SQLite3`.
5. Escreve uma linha no diário: o que gerou, quantos pedidos gastou hoje, qual é o próximo.

O estado fica em `livros_json/.bee/estado.json` e o diário em `livros_json/.bee/diario.md`. Nada disso vai para o Git (só o conteúdo dos capítulos vai).

---

## 1b. A janela horária — para que serve e como se muda

A produção agendada só corre entre `BEE_HORA_INICIO` e `BEE_HORA_FIM`. Essas
duas horas estão em **UTC**, porque quem as compara é o cron do GitHub: com
`4` e `22` produz entre as **05:00 e as 23:00 em Luanda**. Serve para não
gastar os 2.000 minutos mensais de Actions de madrugada, enquanto dorme, e
para o trabalho acontecer na altura em que pode ler o resultado. Não tem nada
a ver com a quota da IA — essa é outra coisa (ver §2).

- Uma execução **manual** (*Run workflow*) produz a qualquer hora, mesmo de
  madrugada — a janela só se aplica às execuções agendadas.
- Fora da janela, a execução termina em segundos e o resumo diz
  `Fora da janela (03 UTC): a produção retoma às 04:00 UTC`. Não é falha.
- Para produzir 24 horas: mude `BEE_HORA_INICIO: '0'` e `BEE_HORA_FIM: '24'`
  no workflow (e conte com mais minutos de Actions).

## 1c. Quanto tempo até terminar (contas honestas)

Com o repositório **público**, os minutos de Actions são **ilimitados**. O
limitador passou a ser a **quota gratuita da IA**, e o número que a controla é
`BEE_PEDIDOS_POR_DIA`.

Configuração actual, a 24 horas por dia:

| Peça | Valor | Porquê |
|---|---|---|
| cron | `7,27,47 * * * *` | 3 execuções/hora, fora da hora cheia |
| janela | 00–24 | ninguém precisa de estar acordado |
| `BEE_VERSOS_POR_CICLO` | 240 | blocos grandes, menos arranques |
| `BEE_LOTE` | 10 | menos pedidos para os mesmos versículos |
| `BEE_PEDIDOS_POR_DIA` | 1200 | teto de segurança (Gemini ~480 + Groq ~1000) |

Contas:

| Cenário | Versículos/dia | Até terminar |
|---|---|---|
| só o teto de pedidos (1.200 × 10) | 12.000 | **~3 dias** |
| só o Gemini (480 pedidos × 10) | 4.800 | ~7 dias |
| ritmo observado em 17/11 (com 503 e 429) | 140 | ~7 meses |

As duas primeiras linhas mostram o que é possível **quando o serviço responde**.
A terceira mostra o que aconteceu **quando não respondeu**. É por isso que as
correções desta ronda são sobre a rede e não sobre o cron: o TPM da Groq passou
a ser respeitado, o que elimina a rajada de 429 que travou a produção.

**Onde afinar:** se aparecerem 429 nos registos, baixe `BEE_PEDIDOS_POR_DIA`.
É o único número que corta a produção diária.

## 2. Plano gratuito: o que é possível de verdade

Os números abaixo são **referências de 2026 que mudam sem aviso**; confirme-os na sua conta antes de confiar neles. O programa já vem com tetos conservadores e nunca tenta esgotar a quota.

| Provedor | Plano gratuito (ordem de grandeza) | Modelos que o programa tenta | Serve para |
|---|---|---|---|
| **Google Gemini** (AI Studio) | Flash-Lite: ~500 pedidos/dia; Flash: ~20/dia | `gemini-3.5-flash-lite` | Melhor combinação qualidade/quota para este trabalho |
| **Groq** | ~30 pedidos/min, ~14.400/dia, mas poucos milhares de tokens/min | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` | Trabalho contínuo rápido; bom segundo lugar |
| **Cerebras** | Plano gratuito com contexto curto (~8K) | `gpt-oss-120b`, `qwen-3-32b` | Reserva; use lotes de 4 versículos |
| **OpenRouter** | modelos com sufixo `:free`, teto diário baixo | `openai/gpt-oss-120b:free`, `qwen/qwen3-235b-a22b:free` | Terceira reserva |
| OpenAI | sem plano gratuito | — | Só se você já tiver crédito |

### Quando o serviço está mesmo em baixo

Se o Gemini responder 503 e a reserva também falhar, a execução termina com
`Serviço de IA indisponível neste momento; o próximo ciclo agendado volta a
tentar`. Não é um defeito do projeto nem da sua chave: o cron volta em 15
minutos e um 5xx não conta para o limite de 6 falhas seguidas que pararia o
agendador. Só a configuração (chave recusada, quota esgotada) marca a execução
como falhada, para não passar em claro.

**Nunca é preciso correr atrás de um nome de modelo.** Se o serviço retirar o
modelo que estava a ser usado, a execução seguinte escolhe outro e continua.

### O programa pergunta ao serviço qual é o modelo

Nomes de modelos envelhecem. A Groq retirou os Llama 3.x do plano gratuito em
agosto de 2026 e passou a responder **HTTP 404**; o programa falhava por causa
de um nome escrito à mão no código.

Agora, antes de produzir, o programa chama a lista de modelos do próprio
serviço (`/v1/models` na Groq e nos compatíveis, `models` no Gemini), escolhe o
primeiro nome que existe **e** está na lista curada, e ignora uma lista de
modelos retirados. Se o serviço não deixar listar, usa os nomes de reserva do
código — e, se mesmo assim um nome der 404, passa ao nome seguinte sem parar a
produção. Não precisa de decidir nada nem de editar ficheiros: se amanhã outro
modelo for retirado, o programa adapta-se sozinho.

Para ver o que foi escolhido na sua conta:

```bash
python autopiloto.py --doctor
```

**A conta que importa.** Um versículo com comentário exegético ocupa ~700–1.200 tokens de saída; com os textos originais e o contexto no pedido, o custo total por versículo fica perto de **2.000 tokens**. Um bloco de 6 versículos ≈ 12 mil tokens.

- Com ~500 pedidos/dia do Gemini Flash-Lite a 6 versículos por pedido: **~3.000 versículos/dia** no melhor caso — mas os limites por minuto e a qualidade real cortam isso. Plano realista: **300 a 800 versículos/dia** com um provedor, somando Groq como segundo.
- A Bíblia inteira tem 31.102 versículos. A 500/dia, são **~60 dias** de trabalho contínuo; a 200/dia, ~5 meses. Não prometo 1.189 capítulos numa semana: prometo que o programa não para e que você vê o progresso todos os dias.
- O gargalo do Antigo Testamento não é a IA: é a **revisão humana**. 31 mil comentários gerados sem revisão são um rascunho, não uma Bíblia de estudo publicável. O próprio projeto já diz isso no README; isso não mudou.

Por isso o programa já vem preparado para a revisão: todo texto gerado automaticamente entra marcado como rascunho, com uma regra extra no prompt (`PROMPT_REVISAO`) que **proíbe atribuir consulta a BDB/Thayer/Nestle-Aland** quando ela não aconteceu e obriga a escrever “não verificada em léxico”.

---

## 3. Começar em 3 minutos (no seu computador)

### Passo 1 — obter uma chave gratuita

1. **Gemini:** <https://aistudio.google.com/apikey> → *Create API key*. Não pede cartão.
2. **Groq (opcional, recomendado como reserva):** <https://console.groq.com/keys>.
3. Guarde a chave. **Nunca** a coloque no código, no README ou num commit.

### Passo 2 — definir a chave

macOS/Linux:

```bash
export GEMINI_API_KEY="cole-a-chave-aqui"
# opcional, para rodízio automático:
export GROQ_API_KEY="cole-a-outra-chave-aqui"
```

Windows PowerShell (só nesta sessão):

```powershell
$env:GEMINI_API_KEY = Read-Host 'GEMINI_API_KEY'
```

### Passo 3 — ver o diagnóstico (não gasta quota)

```bash
python autopiloto.py --doctor --fuso Africa/Luanda
```

Deve mostrar o provedor detetado, o modelo, o próximo capítulo e o estado do agendador.

### Passo 4 — produzir

```bash
# Um único bloco de 6 versículos (bom para o primeiro teste real)
python autopiloto.py --uma-vez --fuso Africa/Luanda

# Trabalhar 6 horas, 6 versículos a cada 5 minutos, e parar sozinho
python autopiloto.py --horas 6 --intervalo-min 5 --max-versos 6 --fuso Africa/Luanda

# Só um livro (Filemom), com lotes maiores e um ZIP pronto a copiar
python autopiloto.py --horas 2 --livros 640 --lote 8 --zip BEE-Filemom.zip

# Deixar a correr sem limite (Ctrl+C a qualquer momento; nada se perde)
python autopiloto.py --fuso Africa/Luanda
```

O primeiro arranque descarrega os textos originais (~22 MB) para `.bee-cache` e confirma o SHA-256. Depois disso, funciona offline para as fontes.

### Passo 5 — ver o progresso a qualquer momento

```bash
python autopiloto.py --status
cat livros_json/.bee/diario.md
```

---

## 4. Funcionar com o computador desligado (GitHub Actions)

O `autopiloto.py` só corre enquanto a máquina está ligada. Para continuar sem você, use o workflow incluído em `modelos/bee-autopiloto.yml`.

1. **Leve o código ao ramo `main`** do repositório `traducao-epignosis` (privado).
2. **Ative o workflow.** O ficheiro está em `modelos/` porque foi preparado por um agente sem permissão para criar workflows. No site do GitHub: *Add file → Create new file*, escreva `.github/workflows/bee-autopiloto.yml` e cole o conteúdo de `modelos/bee-autopiloto.yml`. (Alternativa: no seu computador, `mkdir -p .github/workflows && cp modelos/bee-autopiloto.yml .github/workflows/ && git add .github && git commit -m "ativar autopiloto" && git push`.)
3. **Acrescente o segredo:** *Settings → Secrets and variables → Actions → New repository secret* → nome `GEMINI_API_KEY`, valor a sua chave. (Opcional: `GROQ_API_KEY` como reserva.)
4. **Confirme em *Actions*** que o workflow aparece ativo; ajuste o ritmo nas variáveis `BEE_*` do ficheiro ou dispare manualmente com *Run workflow*.

O que acontece em cada execução (a cada 15 minutos):

- recupera o progresso do ramo **`bee-dados`**;
- produz 40 versículos (configurável), compila os módulos;
- publica os JSON no ramo `bee-dados` (história limpa, só dados);
- publica `entregas/auto/BEE-modulos.zip` como **artefato** descarregável (retenção de 14 dias);
- escreve um resumo com o progresso no resumo da execução.

**Vantagem:** continua 24 horas por dia. **Atenção:** repositórios privados consomem minutos de Actions do plano gratuito (2.000 minutos/mês). A 1 minuto por execução, 4 execuções por hora, 18 horas por dia, são ~2.100 minutos/mês — no limite. Se os minutos acabarem, reduza para `*/30 * * * *` (a cada 30 minutos) e suba `BEE_VERSOS_POR_CICLO` de 40 para 80: metade das execuções, o mesmo trabalho. O programa não depende do GitHub: o mesmo comando corre em qualquer lugar.

**Se a execução ficar vermelha:** leia o resumo no topo da página da execução. Ele diz em uma linha se foi o serviço (não precisa de fazer nada) ou a configuração (`--testar` mostra o resto). Com um modelo retirado pelo serviço, nem isso: o programa escolhe outro sozinho e continua.

**Alternativas gratuitas à nuvem do GitHub**, se preferir:

| Onde | Como | Limite |
|---|---|---|
| Computador de casa | `python autopiloto.py` com o Agendador de Tarefas (Windows) ou `cron` (Linux/macOS) | A máquina tem de estar ligada |
| Servidor doméstico / Raspberry Pi | `cron` a cada 15 min: `*/15 * * * * cd /caminho && GEMINI_API_KEY=... python3 autopiloto.py --uma-vez` | Consome pouca energia |
| GitHub Actions | o modelo em `modelos/bee-autopiloto.yml` (ativar, ver secção 4) | Minutos do plano gratuito |

---

## 5. Ver no MyBible em cinco minutos

1. Tenha os dois ficheiros da **mesma compilação**: `BEE.SQLite3` e `BEE.commentaries.SQLite3` (ou o `BEE-modulos.zip`, que já traz os dois e um `LEIA-ME.txt`).
2. Copie os dois para o telemóvel, para a pasta de dados do MyBible (normalmente `/Android/data/ua.mybible/files/MyBible`; em algumas versões, `/MyBible`).
3. Reinicie o MyBible, escolha a Bíblia **BEE** e ative o módulo de comentários.
4. Abra **Filemom 1**. Os 25 versículos e os 25 comentários já estão lá desde o início do projeto; os capítulos novos entram nas compilações seguintes.
5. O módulo diz sempre se é **RASCUNHO** ou **RASCUNHO PARCIAL**, e os metadados registram o estado de revisão de cada trecho. Não é uma edição final — e o próprio módulo diz isso ao leitor.

Se o MyBible não mostrar o livro, verifique se copiou **os dois ficheiros juntos** (um par de compilações diferentes pode ser recusado) e se o nome está exatamente `BEE.SQLite3`.

---

## 6. Rodízio automático de provedores

Se definir mais de uma chave (`GEMINI_API_KEY` e `GROQ_API_KEY`, por exemplo), o programa:

- começa pelo Gemini (melhor quota gratuita);
- se receber `HTTP 429` (quota esgotada) depois de todas as tentativas, **passa ao Groq** sem perder o progresso e registra o motivo no diário;
- tenta as várias chaves do mesmo provedor em rodízio, útil quando você tem mais de um projeto;
- adormece até à próxima janela diária quando **todos** esgotarem, em vez de insistir e arriscar bloqueio.

Para forçar a ordem ou usar só um:

```bash
python autopiloto.py --uma-vez --provedor groq --lote 4
```

---

## 7. Ritmo, custo zero e qualidade

| Objetivo | Comando |
|---|---|
| Gastar o mínimo de quota | `--max-versos 4 --intervalo-min 15 --lote 4` |
| Produzir mais depressa | `--max-versos 12 --intervalo-min 2 --lote 8` |
| Só nas horas em que você revê | `--hora-inicio 19 --hora-fim 23 --fuso Africa/Luanda` |
| Testar antes de comprometer | `--uma-vez --livros 640 --max-versos 4` |
| Um livro de cada vez | `--livros 500 --horas 6` |

Recomendações práticas:

- **Comece com `--uma-vez --max-versos 6`** e leia o que saiu. Se a qualidade servir, aumente o lote.
- Prefira lotes de **4 a 8 versículos**: lotes grandes truncam a resposta (o programa deteta e divide automaticamente, mas gasta quota a repetir).
- Antes de distribuir qualquer coisa, revise. O material automático é rascunho: os comentários dizem explicitamente o que não foi verificado.
- Se mudar de modelo a meio de um livro, o diário registra a data e o modelo no `history` do JSON; não misture modelos sem revisão, porque o estilo muda.

---

## 8. Perguntas diretas

**Isto acaba com a revisão humana?**
Não. A automação resolve o gargalo da *redação*, não o da *revisão*. Ela produz rascunhos com rasto (fonte, modelo, data, versículos) para você revisar no MyBible. O README do projeto continua correto ao dizer que cobertura estrutural não é aprovação.

**E os léxicos BDB/Thayer, que o fluxo colaborativo consultava à mão?**
Não são fornecidos ao modelo em execução automática. Para não inventar atribuições, o prompt automático proíbe citá-los como consultados e exige “não verificada em léxico”. Traduzir bem é possível com o texto original; já a análise léxica de nível académico exige revisão com os léxicos à mão — para os trechos que você decidir aprofundar.

**E se a internet falhar ou a quota acabar a meio?**
O bloco atual é perdido (não é gravado nada inválido), o ciclo falha, e o seguinte recomeça do último versículo guardado. Depois de 6 falhas seguidas o agendador para e diz o motivo no diário, em vez de insistir.

**Os ficheiros são seguros para o Git?**
Os JSON dos capítulos são versionados (é a história editorial do projeto). Chaves, cache de fontes, estado do agendador e módulos SQLite ficam fora do Git pelo `.gitignore`. Nenhuma chave é escrita em ficheiros; a chave aparece só no cabeçalho HTTP.

**Por que o OpenAI deixou de ser o padrão?**
Porque o objetivo é custo zero. O Gemini tem o plano gratuito mais generoso para este tipo de trabalho, e a OpenAI não tem plano gratuito permanente. O código continua a suportar OpenAI se você já tiver crédito.

**Que licenças continuam a valer?**
As mesmas. WLC/OSHB (CC BY 4.0), SBLGNT (CC BY 4.0), Scrivener (domínio público segundo o fornecedor). As atribuições continuam nos módulos compilados. O texto gerado pela IA é rascunho seu, mas revise direitos antes de publicar.

---

## 9. Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `Nenhum provedor configurado` | variável não definida na sessão | repita o passo 2 no mesmo terminal |
| `HTTP 429` repetido | quota gratuita esgotada | espere a reposição diária, acrescente outra chave/provedor ou baixe `--max-versos` |
| Respostas inválidas/truncadas seguidas | lote grande para o modelo | `--lote 4` ou `--versos-por-pedido groq=4` |
| `Já existe uma execução a usar ...` | dois autopilotos ao mesmo tempo | feche o outro processo (a trava é libertada ao terminar) |
| `as versões das fontes diferem do checkpoint` | atualização das fontes a meio de um livro | não misture: conclua o livro com a versão antiga ou faça cópia e revise |
| MyBible não mostra o livro | só um dos dois ficheiros copiado | copie o par completo da mesma compilação |
| Ação do GitHub falha por minutos | plano gratuito de Actions esgotado | `*/30` no cron, ou use o agendador do seu computador |

---

## 10. Referência rápida de comandos

```bash
python autopiloto.py --testar                 # chave e modelo respondem? (1 pedido)
python autopiloto.py --doctor                 # configuração e próximo capítulo (não gasta quota)
python autopiloto.py --status                 # progresso nos JSON
python autopiloto.py --uma-vez                # um bloco
python autopiloto.py --horas 6                # seis horas
python autopiloto.py --livros 640,500         # fila restrita
python autopiloto.py --zip BEE.zip            # pacote com os dois módulos
python autopiloto.py --sem-compilar           # só JSON (compila depois com gerar_bee.py --compilar)
python gerar_bee.py --compilar                # compilar sem IA, sem rede e sem chave
python -m unittest discover -s tests -v       # 91 testes, sem rede nem chaves
```

Lista completa: `python autopiloto.py --help`.
