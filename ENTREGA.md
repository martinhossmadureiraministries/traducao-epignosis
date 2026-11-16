# Correção definitiva da produção automática — 16/11/2026

**Estado:** já está tudo no `main`. Não precisa de mudar chaves, segredos nem ficheiros.

## O que falhou e porquê

As duas execuções pararam pelo mesmo motivo, e não era o seu computador nem a sua chave:

| Execução | Erro | Causa real |
|---|---|---|
| 1.ª | `gemini: HTTP 503; esgotadas 3 tentativas` | O Google estava instável naquele minuto |
| 2.ª | `groq: HTTP 404; verifique o endereço ou o nome do modelo` | O Gemini voltou a dar 503 **e** a reserva Groq apontava para `llama-3.3-70b-versatile`, que a Groq **retirou do plano gratuito em 16/08/2026** |

O programa tentava uma reserva, mas com um nome de modelo escrito à mão. Corrigir o nome à mão resolvia hoje e voltava a falhar no mês seguinte.

## O que ficou feito (5 correções, todas no `main`)

1. **O programa pergunta ao serviço qual é o modelo.** Antes de produzir, lê a lista de modelos da própria conta (`/v1/models` na Groq/Cerebras/OpenRouter, `models` no Gemini), ignora os que o serviço já retirou e escolhe um que exista. Se a listagem falhar, usa os nomes de reserva do código.
2. **Se um modelo der 404, passa ao seguinte sem parar.** Um nome retirado deixa de ser capaz de parar a produção — é a última vez que este problema aparece.
3. **GPT-OSS da Groq com esforço de raciocínio baixo**, para os lotes de 6–8 versículos não voltarem truncados (o que gastava quota a repetir).
4. **Serviço em baixo (5xx) já não pinta a execução de vermelho.** Termina com "Serviço de IA indisponível neste momento; o próximo ciclo agendado volta a tentar" e o cron retoma em 15 minutos. Um 5xx também deixou de contar para o limite de 6 falhas seguidas que parava o agendador (aconteceu: o serviço em baixo durante uma hora faria a produção parar até alguém a correr à mão).
5. **Relatório honesto.** O resumo dizia `0/31102 versículos` mesmo depois de guardar 6, porque só contava capítulos completos. Agora diz `6/31102 versículos guardados`. E quando nada é gerado por causa do serviço, diz "não precisa de fazer nada" em vez de "falha".

Além disso: a chave do Gemini deixou de ir na URL da listagem (passou para o cabeçalho), os guias deixaram de mandar fazer coisas já feitas (merge do PR #2, etiquetas em PRs fechados) e o número de testes nos documentos passou a ser o real.

## Prova, com os seus dados verdadeiros

Simulação de ponta a ponta com `livros_json` real, Gemini **sempre** em 503, a lista de modelos do Gemini a devolver um nome desconhecido, e a Groq a devolver 404 ao modelo retirado:

```
BEE · nuvem: gemini, groq
A gerar João 5 (47 versículos)...
  Guardados João 5:1-6.
  Guardados João 5:7-12.
- Ação: **gerado** — João 5
- Esta execução: +12 versículos, +0 capítulos
- Progresso: **5/1189 capítulos completos**, 203/31102 versículos guardados
- A seguir: João 5
- Faltam 701 versículos para concluir **João**; 30899 em toda a fila
```

E a variante em que o serviço está mesmo em baixo (Gemini 503 + Groq 503):

```
- Ação: **nada gerado nesta execução** — o serviço de IA não respondeu.
- **Não é um erro do projeto nem da sua chave.** O próximo ciclo agendado (15 min) volta a tentar sozinho; não precisa de fazer nada.
```

91 testes automáticos passam (2 ignorados por precisarem de rede), e 12 são novos e cobrem exatamente estes casos.

## O que você faz agora (2 minutos, uma vez)

1. **Atualize o workflow no site** (só mudou uma frase do diagnóstico): abra `modelos/bee-autopiloto.yml` no GitHub → *Raw* → copie tudo → abra `.github/workflows/bee-autopiloto.yml` → lápis (editar) → cole → *Commit changes* em `main`.
   - Se ainda não tinha criado este ficheiro, crie-o com esse conteúdo (passo 2 do `COMECAR_HOJE.md`).
2. **Dispare:** *Actions* → **BEE — produção automática** → **Run workflow** → **Run workflow**. Deixe o campo *modelo* **vazio**.
3. O que deve ver no resumo, em poucos minutos: `Ação: gerado — João 5`, `+40 versículos`, `5/1189 capítulos completos` a subir. O `BEE-modulos.zip` fica em *Artifacts* para o MyBible.

Não precisa de mexer nos segredos. Se quiser confirmar a chave e o modelo escolhido sem gastar quota: `python autopiloto.py --doctor` (no seu computador).

## Onde está o quê

| Ficheiro | Para quê |
|---|---|
| `ENTREGA.md` | Esta página |
| `AUTOMACAO.md` | Planos gratuitos, descoberta do modelo, ritmo, minutos de Actions, problemas comuns |
| `COMECAR_HOJE.md` | Guia passo a passo atualizado |
| `modelos/bee-autopiloto.yml` | O workflow a copiar para `.github/workflows/` |

## Nota honesta sobre o ritmo

O progresso está em **5 de 1.189 capítulos** e **191 versículos** guardados (203 na simulação, que não foi publicada). O que mudou hoje foi a produção deixar de parar por motivos técnicos — não a velocidade da IA. A 300–800 versículos/dia com os planos gratuitos, a Bíblia inteira são semanas ou meses, e o Antigo Testamento continua a precisar da sua revisão humana antes de ser publicado. O que garanto: a partir de agora, quando a nuvem falhar, é o serviço que está em baixo — não um nome de modelo que alguém esqueceu de atualizar.
