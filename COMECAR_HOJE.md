# Arrancar hoje — guia cronometrado

> **Objetivo até ao fim do dia:** produção a correr sozinha, `BEE-modulos.zip` a ser gerado e o primeiro lote real de versículos novos já no MyBible. O plano completo e as quotas estão em [AUTOMACAO.md](AUTOMACAO.md).

Tempo total: **cerca de 40 minutos**, dos quais ~25 são só esperar.

| Hora sugerida | Passo | Tempo |
|---|---|---|
| H+0 | 1. Chave gratuita do Gemini | 3 min |
| H+3 | 2. Ligar a automação (caminho A, sem computador) | 10 min |
| H+13 | 3. Primeiro teste real e leitura da qualidade | 10 min |
| H+23 | 4. Pôr no MyBible | 5 min |
| H+28 | 5. Rodízio com Groq (opcional, recomendado) | 5 min |
| H+33 | 6. Primeiras 24 horas e o que esperar | — |

---

## Passo 1 — Chave gratuita do Gemini (3 min)

1. Abra <https://aistudio.google.com/apikey> com a sua conta Google.
2. **Create API key** → escolha um projeto (qualquer um) → *Create*.
3. Copie a chave. Ela começa por `AIza…`. Não pede cartão e não expira.

> Se o AI Studio disser que o seu país não está disponível, use a Groq como plano B: <https://console.groq.com/keys> (também gratuita, sem cartão). O resto do guia funciona igual, só muda o nome da variável.

**A chave não é um medicamento:** não a cole em ficheiros do projeto, no README, em issues nem em mensagens. Só em dois lugares: variável de ambiente (no seu computador) ou *secret* do GitHub.

---

## Passo 2 — Onde a automação vai correr

### Caminho A — Nuvem (recomendado: é o que cumpre "mesmo estando offline")

Requer conta no GitHub (já tem, o repositório é seu) e 10 minutos.

1. **Confirme que está no `main` atualizado:** `git pull` (ou *Sync fork* no site). As correções de automação já estão no `main` e verificadas por 91 testes locais; nada disto toca no texto bíblico.
2. **Atualize o workflow.** Se já criou `.github/workflows/bee-autopiloto.yml` antes, substitua o conteúdo pelo de `modelos/bee-autopiloto.yml` (só mudou uma frase do diagnóstico). Se ainda não o criou, o ficheiro está em `modelos/` porque o agente não tem permissão de escrita em `.github/workflows`. Duas formas:
   - **Pelo site:** no repositório, *Add file → Create new file*, nome exato `.github/workflows/bee-autopiloto.yml`, cole o conteúdo de `modelos/bee-autopiloto.yml` e *Commit changes* em `main`.
   - **No seu computador:**
     ```bash
     git clone https://github.com/martinhossmadureiraministries/traducao-epignosis.git
     cd traducao-epignosis
     mkdir -p .github/workflows
     cp modelos/bee-autopiloto.yml .github/workflows/
     git add .github && git commit -m "ativar autopiloto" && git push
     ```
3. **Guarde a chave como segredo:** *Settings → Secrets and variables → Actions → New repository secret*.
   - Nome: `GEMINI_API_KEY` (exatamente assim, sem espaços)
   - Valor: a chave `AIza…`
4. **Confirme:** separador *Actions* → *BEE — produção automática*. Se aparecer, está ativo. O horário está no fuso UTC (`*/15`); a janela 05h–23h é interpretada em `Africa/Luanda`.

> **Já tem execuções de teste antes do merge?** Nada foi produzido: sem o segredo `GEMINI_API_KEY` o script termina com aviso, sem gerar texto e sem publicar nada.

#### Quer ver o primeiro ciclo já, sem esperar os 15 minutos?

O seu código já está no `main`. Para disparar uma execução imediata:

1. *Actions* → **BEE — produção automática** → botão **Run workflow** → **Run workflow** (deixe o modelo vazio: o programa descobre qual está disponível).
2. Em poucos minutos, o resumo da execução mostra `Ação: gerado — …` com os versículos produzidos, e o `BEE-modulos.zip` fica em *Artifacts*.
3. Se a etiqueta **`bee-producao`** já existir no repositório, aplicá-la a um PR também dispara o workflow (evento `pull_request: labeled`).

Se o GitHub estiver lento ou o botão não aparecer, use o caminho B abaixo para o primeiro teste e deixe a nuvem arrancar sozinha depois.

### Caminho B — Seu computador (funciona sempre, mesmo sem GitHub)

1. Instale o Python 3.10+ (Windows: <https://python.org>, marque *Add to PATH*).
2. Obtenha o projeto: `git clone https://github.com/martinhossmadureiraministries/traducao-epignosis.git`
3. Crie um ficheiro `.env` **na pasta do projeto** (já está no `.gitignore`):
   ```
   GEMINI_API_KEY=AIza...a-sua-chave
   ```
   O programa lê este ficheiro automaticamente; variáveis de ambiente continuam a ter precedência.
4. Teste:
   ```bash
   cd traducao-epignosis
   python autopiloto.py --doctor      # configuração e próximo capítulo (não gasta quota)
   python autopiloto.py --uma-vez     # 6 versículos reais
   ```

Não quer esperar por um terminal aberto? Agende-o no sistema:

- **Windows** (Agendador de Tarefas → Criar tarefa → A cada 15 minutos → *Iniciar um programa*):
  `python` com argumentos `autopiloto.py --uma-vez` e *Iniciar em*: `C:\caminho\traducao-epignosis`
- **Linux/macOS** (`crontab -e`):
  ```
  */15 * * * * cd /caminho/traducao-epignosis && /usr/bin/python3 autopiloto.py --uma-vez >> /tmp/bee.log 2>&1
  ```

Nos dois casos, `--uma-vez` produz um bloco e termina: nada fica preso se a máquina reiniciar.

---

## Passo 3 — Primeiro teste real (10 min, gasta ~2 pedidos)

1. Confirme que a chave funciona (**gasta 1 pedido**):
   ```bash
   python autopiloto.py --testar
   ```
   Esperado: `OK · gemini/<modelo que a sua conta tem>: respondeu 'ok'`. O nome não é fixo: o programa pergunta ao serviço quais os modelos disponíveis e indica no ecrã qual escolheu. Se a lista não puder ser lida, usa os nomes de reserva e, se um deles der `HTTP 404`, passa sozinho ao seguinte.
2. Produza um bloco:
   ```bash
   python autopiloto.py --uma-vez --fuso Africa/Luanda
   ```
3. Abra o diário e leia o resultado:
   ```bash
   cat livros_json/.bee/diario.md
   ```
4. **Leia os versículos com olhos críticos.** Abra `livros_json/500_Joao.json` no GitHub e vá ao capítulo 5: cada versículo tem `text` e `commentary` com as três secções. Pergunte-se:
   - a tradução respeita o grego que o projeto já usa nos capítulos 1–4?
   - o comentário diz "não verificada em léxico" quando não consultou?
   - o tamanho das notas serve para leitura no telemóvel?
5. Se a qualidade servir, não mude nada. Se as notas vierem curtas ou genéricas, experimente outro modelo uma vez:
   ```bash
   python autopiloto.py --uma-vez --max-versos 4
   ```

> **Regra prática:** prefira lotes de 4–8 versículos. Lotes grandes truncam e o programa gasta quota a repetir.

---

## Passo 4 — No MyBible (5 min)

Com o caminho A, o ZIP está em *Actions → execução → Artifacts → BEE-modulos-…*; com o caminho B, em `entregas/auto/BEE-modulos.zip` (ou `--zip` onde quiser).

1. Descarregue e descomprima: deve ter `BEE.SQLite3`, `BEE.commentaries.SQLite3` e `LEIA-ME.txt`.
2. Copie os **dois** ficheiros `.SQLite3` para `/Android/data/ua.mybible/files/MyBible` (nalgumas versões: `/MyBible`).
3. Reinicie o MyBible → escolha a Bíblia **BEE** → ative o módulo de comentários.
4. Verifique **Filemom 1** (obrigatório: se este não abrir, a cópia está errada) e depois **João 5** (novo).
5. Repita o passo 4 sempre que quiser a versão mais recente; copie sempre o par junto.

---

## Passo 5 — Rodízio com a Groq (5 min, opcional e recomendado)

Com dois provedores o trabalho continua quando a quota gratuita de um acaba.

1. Chave em <https://console.groq.com/keys>.
2. No GitHub: novo segredo `GROQ_API_KEY`. No computador: mais uma linha no `.env`.
3. Nada mais a fazer: o programa começa pelo Gemini e passa sozinho à Groq quando receber `HTTP 429`, registando a troca no diário.

---

## Passo 6 — As primeiras 24 horas

| Momento | O que deve ver |
|---|---|
| Primeiros 15 min | primeira execução no GitHub (ou primeiro bloco local) |
| 1 hora | 3–4 execuções, ~100–150 versículos, módulos recompilados |
| 6 horas | ~600–900 versículos; **João 5 e 6 provavelmente completos** |
| 24 horas | 500–1.500 versículos conforme o modelo e a quota; a fila avança |

**Como acompanhar sem abrir o código:** no GitHub, *Actions* mostra o resumo de cada execução com “Faltam N versículos para concluir João”. No computador: `python autopiloto.py --status`.

**Sinais de que está tudo bem:** o `main` recebe commits `BEE: +12 versículos (…/1189 capítulos completos)`; o diário tem uma linha por ciclo; nunca aparece uma chave nos ficheiros.

**Sinais de que algo precisa de você:**
| No diário / Actions | O que fazer |
|---|---|
| `HTTP 429` repetido | quota do dia esgotada: acrescente `GROQ_API_KEY` ou baixe `--max-versos` |
| `FALHOU · … HTTP 404` | nome retirado pelo serviço; corra de novo: o programa escolhe outro sozinho |
| `resposta inválida após 3 tentativas` | baixe o lote: `--lote 4` |
| Execução vermelha por minutos de Actions | mude o cron para `*/30` ou use o caminho B |

---

## O que fica combinado (para não haver desilusão)

- **Hoje** o que começa é a **produção contínua**, não a Bíblia completa. 1.189 capítulos com plano gratuito levam **semanas a meses**.
- **O que você revê é lei.** Se editar um versículo localmente e depois recuperar o ramo de dados, a versão local **prevalece**: a nuvem só acrescenta texto novo (o `nuvem.py` foi testado para isso).
- **A revisão não se automatiza.** O texto automático entra como rascunho, diz o que não verificou, e o MyBible mostra o aviso. A sua leitura no telemóvel é a etapa seguinte — e é ela que transforma rascunho em Bíblia de estudo.
- **O plano das oito fases mantém-se:** o autopiloto segue a fila do `PLANO_BEE.md` e está agora em **João 18**.

---

## Atalho: tudo o que vai escrever hoje

```bash
# computador
export GEMINI_API_KEY="AIza..."          # ou o ficheiro .env
python autopiloto.py --testar            # 1 pedido, confirma modelo e chave
python autopiloto.py --uma-vez           # primeiro texto real
python autopiloto.py --status            # progresso
cat livros_json/.bee/diario.md           # o que aconteceu
```

```text
# nuvem (uma vez)
1. Código atualizado no main (git pull)
2. Criar .github/workflows/bee-autopiloto.yml a partir de modelos/bee-autopiloto.yml
3. Secret GEMINI_API_KEY (e, se quiser, GROQ_API_KEY)
4. Actions → BEE — produção automática → Run workflow (ou etiqueta bee-producao no PR)
5. Artifacts → BEE-modulos-… → copiar os dois .SQLite3 para o MyBible
```
