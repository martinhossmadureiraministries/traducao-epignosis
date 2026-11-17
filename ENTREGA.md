# Correção definitiva da produção automática

**Estado:** no `main`. Nada a mudar nos segredos. Se já copiou o workflow antes, copie-o outra vez (mudaram duas variáveis).

## Execução de 16/11 (16:42) — o que falhou

```
Resposta inválida ou truncada (João 5:1-8: Tag HTML ou atributo não permitido: <div>.)
groq: HTTP 429; nova tentativa em 8.0s (1/3).
- Ação: nada — falha: João 5:7: resposta inválida após 3 tentativa(s).
```

Três defeitos somados, nenhum deles na sua chave:

1. **`<div>`**: o modelo envolvia os parágrafos num `<div>` e o validador recusava **a resposta inteira** por causa de uma tag sem significado. O lote era dividido até 1 versículo e o capítulo não avançava.
2. **429**: um único HTTP 429 marcava a Groq como esgotada **pelo dia todo** — mas 429 é o limite por minuto. Ficava sem nenhum provedor.
3. **Recomeço**: cada execução repetia o pedido do início do lote e o teto de 4096 tokens truncava 8 versículos com comentário (quota gasta a repetir).

## Correções

| Problema | Correção |
|---|---|
| `<div>` recusado | contentores neutros são aceites e convertidos em `<p>`; scripts, iframes, comentários, atributos e tags desconhecidas continuam recusados |
| Conteúdo de `<script>` lido como HTML | ignorado por inteiro |
| Secção do comentário em falta | nota "não devolvida pelo modelo; assinalada para revisão" — o lote não se perde |
| Repetir o mesmo pedido 3× | divide uma vez e, se falhar, passa ao provedor seguinte |
| 429 = quota do dia | só após 3 falhas; 429 conta como transitório |
| Recomeçar do 5:1 | o estado guarda o versículo em falta e o ciclo seguinte pede **só** esse |
| Lotes truncados | `--max-tokens` 12000; o workflow passa a pedir 6 versículos por pedido |
| Execução sem nada guardado | 8 tentativas por execução (era 1) com 20 s entre elas |

## Prova (dados reais, Gemini sempre 503, Groq 429 na primeira chamada, `<div>` em tudo)

```
A retomar João 5 a partir do versículo 7/47.
- Ação: gerado — João 5 · +6 versículos
Progresso: 5/1189 capítulos completos, 203/31102 versículos guardados
7..12 guardados, sem <div> nos ficheiros
```

**100 testes automáticos** passam (12 novos reproduzem exatamente estes erros).

## O que fazer agora (2 minutos)

1. **Atualize o workflow** — `modelos/bee-autopiloto.yml` → *Raw* → copiar → `.github/workflows/bee-autopiloto.yml` → editar → colar → *Commit changes* em `main`. Mudou: `BEE_LOTE` 8→6, `BEE_TENTATIVAS_CICLO` 1→8, `BEE_ESPERA_ENTRE_TENTATIVAS` 20.
2. **Actions → BEE — produção automática → Run workflow** (campo *modelo* **vazio**).
3. O resumo deve dizer `Ação: gerado — João 5` e o `BEE-modulos.zip` aparece em *Artifacts*.

Se o Gemini estiver mesmo em baixo, o resumo diz "não precisa de fazer nada" e o ciclo de 15 minutos retoma sozinho — mas agora, quando um dos dois provedores responde, alguma coisa é sempre guardada.

## Nota honesta

O progresso guardado é **5 de 1.189 capítulos** e **191 versículos**. O que mudou hoje foi o programa deixar de perder trabalho e de parar por detalhes de marcação; a velocidade da IA e a revisão humana continuam iguais. A Bíblia inteira são semanas ou meses nestes planos gratuitos.
