# Edição nova — como produzir na voz do ESTILO_BEE (v0.5)

Este documento liga a **voz** aprovada em [`ESTILO_BEE.md`](ESTILO_BEE.md) à
infraestrutura existente **sem alterar a linha legada** e **sem ativar a
automação da nova edição**. Cumpre a regra de ouro do guia: *recomeçar a
tradução, não a infraestrutura*.

## O que mudou no código

Foi acrescentado um **perfil de edição** em [`bee/perfil.py`](../bee/perfil.py):

| Perfil | Voz | Quando entra |
|---|---|---|
| `legado` | prompts/glossário herdados, byte a byte | **sempre que nada é configurado** (padrão) |
| `nova` | `ESTILO_BEE.md` v0.5 (português contemporâneo com cadência, nota separada do versículo, glossário de *ἐπίγνωσις* → «pleno conhecimento») | só com `BEE_EDICAO=nova` |

Pontos de injeção, todos preservando o comportamento por omissão:

- `bee/ia.py` — `MotorIA` aceita `perfil` opcional; sem ele, `_system()`
  devolve exatamente `SYSTEM_PROMPT + PROMPT_REVISAO`.
- `bee/gerador.py` — `_contexto_estilo` usa o glossário do perfil ativo;
  padrão = `GLOSSARIO_PADRAO`.
- `autopiloto.py` / `gerar_bee.py` — passam o perfil resolvido do ambiente e
  mostram a edição ativa no `--doctor`.

Um nome de perfil desconhecido é **erro de configuração** (`ValueError`), nunca
uma queda silenciosa para o legado: misturar vozes corrompe a calibração.

## Isolar a nova edição (obrigatório)

O guia manda isolar **diretório, checkpoints e artefactos** e não retomar nem
misturar texto antigo. Os caminhos já são parametrizáveis, por isso basta apontar
para outra pasta — o estado/diário/quarentena seguem automaticamente para
`<dados>/.bee/`:

```bash
export GEMINI_API_KEY="a-sua-chave"     # só na sessão, nunca no Git
export GROQ_API_KEY="a-sua-chave"        # reserva, opcional
export BEE_EDICAO=nova                   # <-- ativa a voz nova

pasta=edicoes/nova/livros_json           # raiz ISOLADA desta edição

python3 autopiloto.py --doctor   --dados "$pasta"    # confirma edição+pasta, não gasta quota
python3 autopiloto.py --testar   --dados "$pasta"    # confirma chave/modelo (1 pedido)
python3 autopiloto.py --uma-vez  --dados "$pasta"    # primeira fatia real (começa em Filemom)
python3 autopiloto.py --status   --dados "$pasta"    # progresso, sem gastar quota
```

Com a pasta nova **vazia**, a fila começa do início do plano editorial — e a
fase 1 abre precisamente com **Filemom (640)**, o piloto de livro inteiro
aprovado. A linha legada (`livros_json/`, a retomar em João 19:13) não é tocada.

Verificar e compilar de forma independente:

```bash
python3 scripts/verificar_dados.py --dados "$pasta" --minimo 0
python3 gerar_bee.py --compilar --dados "$pasta" --saida edicoes/nova/modulos
```

Artefactos da nova edição devem sair rotulados como **prévia/rascunho** e ficar
fora dos pacotes da linha legada (`entregas/auto/`).

## Antes de gerar livros inteiros

Do [`ESTILO_BEE.md`](ESTILO_BEE.md): **fixar a edição-base antes de gerar**. O
SBLGNT usado hoje é uma edição crítica sob **CC BY 4.0**, não domínio público;
se o requisito for domínio público sem exceções, documentar uma base compatível
antes de migrar (não trocar só o rótulo da licença). Manter atribuições
exigidas (texto, transcrição, morfologia e aparato conferidos separadamente).

## Estado da automação

- Já existe um workflow **isolado** para a nova edição:
  [`.github/workflows/bee-nova-edicao.yml`](../.github/workflows/bee-nova-edicao.yml).
  Ele define `BEE_EDICAO=nova`, `BEE_DADOS=edicoes/nova/livros_json` e
  `BEE_SAIDA=edicoes/nova/entregas/auto` e publica num release separado
  (`bee-previa-nova`). Todo o estado vive no Git, ao lado dos dados
  (`edicoes/nova/livros_json/.bee/`). Não toca em nada da linha legada.
- **Ativação continua a ser uma decisão explícita.** O `schedule` só dispara a
  partir do `main` (depois do merge); entretanto use *Actions → "BEE — edição
  nova" → Run workflow* para lançamentos manuais com controlo. Recomenda-se:
  1. correr uma vez para **Filemom**, rever o HTML/JSON/módulo gerados;
  2. só depois deixar o relógio ligado de forma contínua.
  Validar Filemom de ponta a ponta (JSON íntegro, correspondência JSON↔SQLite,
  abertura no MyBible) antes de produção em massa é a regra do guia de estilo.
- O repositório público dá minutos ilimitados; o limite real é a **quota das
  APIs** (Gemini ~480 pedidos/dia, Groq ~66/dia como reserva). Para dedicar toda
  a quota à edição nova, **desative o workflow legado** na UI (Actions → Disable)
  enquanto esta corre. Os dois partilham o grupo de concorrência `bee-producao`,
  pelo que nunca escrevem no `main` ao mesmo tempo.
- Produção contínua não é autorização de publicação: distinguir sempre os três
  estados — cobertura (rascunho/parcial/completo), revisão editorial e revisão
  especializada — nos artefactos e no diário (`edicoes/nova/livros_json/.bee/diario.md`).

## Semente dos livros já aprovados

Uma execução automática reproduziu Filemom **abaixo** do piloto aprovado («Apfia»,
«a tua amor», «entranhas», vv. 8–9 achatados). Os pilotos em `edicoes/piloto/`
foram aprovados pelo responsável, portanto são eles o texto de partida da edição
nova — não algo a regenerar por cima. O script
[`scripts/importar_piloto.py`](../scripts/importar_piloto.py) copia-lhes o TEXTO
aprovado para os JSON de `edicoes/nova/livros_json`:

```bash
python3 scripts/importar_piloto.py --dry-run     # confere contagens antes
python3 scripts/importar_piloto.py               # escreve (sobrescreve com cuidado)
```

- Filemom, Tito, Judas, 2 João e 3 João ficam como capítulos **completos**; a
  produção automática não os volta a gerar (já estão ao nível aprovado).
- O comentário é reconstruído com as três secções obrigatórias usando as notas
  exegéticas do piloto quando existem; onde faltam, fica marcado como rascunho a
  migrar. Continua RASCUNHO até revisão especializada.
- Um capítulo só vira completo se o número de versículos igualar o catálogo;
  senão vai para `in_progress` com aviso (nunca marcamos lacunas como completas).

## Provedores e resiliência (erros 503)

O motor **suporta** uma fila alargada de serviços gratuitos:
`gemini,cerebras,openrouter,nvidia,cohere,groq`. As chaves vêm dos secrets
`CEREBRAS_API_KEY`, `OPENROUTER_API_KEY`, `NVIDIA_API_KEY` e `COHERE_API_KEY`, além
das antigas; um provedor sem chave é simplesmente saltado. NVIDIA NIM e Cohere
entram pelos seus endpoints compatíveis com OpenAI. A **Cloudflare Workers AI ainda
não é suportada** (exige `CF_ACCOUNT_ID` e rota `@cf/...`).

**Atenção à deriva:** modelos diferentes têm "sotaques" diferentes — foi isso que
espalhou o «vós» em 2 Tessalonicenses quando vários provedores escreveram o mesmo
livro. Por isso o **modelo atual do workflow calibra com poucos provedores**
(`BEE_PROVEDORES='gemini,groq'`). Quando a voz agradar de forma consistente, alarga-se
a fila editando essa linha. Vários livros gerados por um só provedor soam muito mais
coesos.

Sobre o HTTP 503 do Gemini (sobrecarga temporária, não bloqueio de chave): o motor
**já** o trata como transitório — nova tentativa com espera curta e *backoff*, e,
se persistir, passa ao provedor seguinte no próprio ciclo (o 429 salta de
imediatamente). Lotes pequenos (4–6 versículos/pedido) reduzem respostas cortadas
e a probabilidade de 503 em capítulos longos. O limite real de velocidade continua
a ser a **quota diária** de cada serviço, não os minutos de Actions.

## Guarda de estilo (anti-deriva)

[`scripts/verificar_estilo.py`](../scripts/verificar_estilo.py) é uma rede de
segurança independente do modelo: varre os versículos gerados e sinaliza

- **falhas duras** — arcaísmos («vós/vos/sois/sejais/sabeis/padeceis…») e hesitação
  dentro do verso («ou seja», travessão com alternativa); fazem o script sair com 1;
- **avisos** — marcadores tipo Almeida («sobremaneira», «porventura», «o sem lei»…).

```bash
python3 scripts/verificar_estilo.py                 # edição nova inteira
python3 scripts/verificar_estilo.py 600             # só 2 Tessalonicenses
python3 scripts/verificar_estilo.py --rigoroso      # avisos também chumbam
```

O modelo do workflow corre-o no fim da produção e põe o relatório no resumo da
execução (sem bloquear a publicação; tire `continue-on-error` para travar em falha
dura). Os pilotos aprovados passam limpos — se um texto aprovado der aviso, o
marcador está agressivo demais e deve ser afinado.

## Testes

`tests/test_perfil.py` garante: legado idêntico por omissão, `nova` injeta voz,
glossário e âncoras próprios, argumento explícito sobrepõe o ambiente, nome
inválido é erro, e `_contexto_estilo` acompanha o perfil ativo.
`tests/test_importar_piloto.py` cobre a análise do markdown dos pilotos, a troca
de livro no ficheiro conjunto 2/3 João e a reconstrução do comentário.
