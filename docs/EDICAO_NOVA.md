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

## Testes

`tests/test_perfil.py` garante: legado idêntico por omissão, `nova` injeta voz e
glossário próprios, argumento explícito sobrepõe o ambiente, nome inválido é erro,
e `_contexto_estilo` acompanha o perfil ativo.
