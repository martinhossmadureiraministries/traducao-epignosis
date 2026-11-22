# Bíblia de Estudo Epignósis (BEE)

> **Obra:** Bíblia de Estudo Epignósis (BEE) — *Projeto Epignósis*\
> **Autor:** Martinho S. S. Madureira\
> **Publicado por:** Martinho S. S. Madureira Ministries

Tradução e comentários para os 66 livros e **1.189 capítulos** do cânone
escolhido, com ferramentas de linha de comando e compilação para os módulos
MyBible `BEE.SQLite3` e `BEE.commentaries.SQLite3`.

> **Rascunho:** o texto e os comentários são gerados por IA sob direcção
> editorial e passam por revisão humana antes de qualquer edição final. Os
> módulos identificam-se sempre como **RASCUNHO** ou **RASCUNHO PARCIAL**. O
> repositório é **público**; não coloque chaves nem dados pessoais no Git.

## Onde está o quê

| Documento | Para quê |
|---|---|
| [docs/ESTADO.md](docs/ESTADO.md) | Fotografia actual: progresso, decisões e o que falta. |
| [docs/OPERACAO.md](docs/OPERACAO.md) | Ligar, pausar, recuperar e diagnosticar a produção. |
| [docs/AGENDADOR.md](docs/AGENDADOR.md) | Pôr a produção a correr sozinha (cron, relógio de segurança e pinger externo). |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Módulos, fluxo, formato dos JSON e compilação. |
| [docs/EDITORIAL.md](docs/EDITORIAL.md) | Directrizes editoriais, variantes e revisão. |
| [docs/CRITICA_TEXTUAL.md](docs/CRITICA_TEXTUAL.md) | Protocolo de crítica textual, manuscritologia, exegese, hermenêutica, geografia e arquivologia. |
| [docs/OFICINA_TRADUCAO.md](docs/OFICINA_TRADUCAO.md) | Como decidir uma variante sem ser especialista, regras de ofício e o que rever. |
| [docs/colacao/](docs/colacao/) | Relatórios de colação por livro: a evidência verificável de cada nota (`scripts/colar.py`). |
| [AUTOMACAO.md](docs/AUTOMACAO.md) | Quotas gratuitas, provedores, ritmo e resolução de problemas. |
| [EDICAO_NOVA.md](docs/EDICAO_NOVA.md) | Produzir na voz do ESTILO_BEE (`BEE_EDICAO=nova`) com dados isolados, sem ativar a automação. |
| [PLANO_ORGANIZACAO.md](docs/PLANO_ORGANIZACAO.md) | Plano da reorganização, etapa por etapa. |
| [docs/arquivo/](docs/arquivo/) | Guias e pacotes antigos, só para consulta. |

## Começar a produzir

Requisitos: **Python 3.10+**; nenhuma dependência externa para o fluxo
principal (as APIs são chamadas por HTTPS com a biblioteca padrão).

```bash
git clone https://github.com/martinhossmadureiraministries/traducao-epignosis.git
cd traducao-epignosis

# Chave gratuita, só na sessão (nunca no código nem no Git)
export GEMINI_API_KEY="a-sua-chave"
export GROQ_API_KEY="a-sua-chave-de-reserva"   # opcional

python3 autopiloto.py --doctor   # configuração e próximo capítulo, sem gastar quota
python3 autopiloto.py --testar   # confirma a chave/modelo (gasta 1 pedido)
python3 autopiloto.py --uma-vez  # primeira fatia real
python3 autopiloto.py --status   # progresso, sem gastar quota
```

O comando de produção é **`autopiloto.py`**. Para correr sozinho com o
computador desligado, o mesmo trabalho corre em `nuvem.py` numa GitHub Action
(ver [docs/OPERACAO.md](docs/OPERACAO.md)).

## Estado actual (verificado em 19/11/2026)

- **Linha legada:** 50 capítulos estruturalmente completos; ao todo há
  2033 versículos guardados (1.977 nos capítulos completos + 56 em
  `in_progress`). Números conferidos por `python3 scripts/verificar_dados.py`.
- **Linha nova (voz do ESTILO_BEE):** isolada em `edicoes/nova/`, com workflow
  próprio em [`.github/workflows/bee-nova-edicao.yml`](.github/workflows/bee-nova-edicao.yml)
  e prévia no release `bee-previa-nova` — ver [docs/EDICAO_NOVA.md](docs/EDICAO_NOVA.md).
- O progresso só conta capítulos completos; versículos de capítulos em curso
  ficam separados em `autopiloto.py --status`.
- Para confirmar se o agendador dispara sozinho:
  `python3 scripts/verificar_agendador.py` (passo a passo em
  [docs/AGENDADOR.md](docs/AGENDADOR.md)).
- Tudo é provisório (RASCUNHO gerado por IA) e precisa de revisão humana
  especializada antes de qualquer publicação.

Números de referência: **1.189 capítulos**, **31.102 versículos**. O progresso
só conta capítulos completos; versículos de capítulos em curso aparecem
separados em `autopiloto.py --status`.

## Dados e módulos

- Os JSON versionados ficam em `livros_json/`; a fonte de verdade é o **`main`**
  (não existe um segundo ramo de dados).
- `chapters` = capítulos completos (entram nos módulos); `in_progress` =
  versículos já guardados de um capítulo a meio.
- Estado, diário e quarentena: `livros_json/.bee/estado.json`,
  `diario.md` e `quarentena.json`.
- `python3 scripts/verificar_dados.py --minimo 18` verifica a integridade dos
  JSON sem rede.
- A compilação offline é feita por `gerar_bee.py --compilar` ou pelo
  `autopiloto.py` quando um capítulo fecha.

O percurso antigo `gerar_bee.py --livro N` / `--todos` continua disponível,
mas gera um livro inteiro por chamada, sem janela diária, rodízio de provedores
nem estado. Prefira `autopiloto.py` para texto novo.

## Testes

```bash
python3 -m unittest discover -s tests -v
```

O CI proposto está em `docs/ci.yml`; para ativar, copie-o para
`.github/workflows/ci.yml` na UI. O teste `tests/test_workflow_sincronizado.py` compara
`modelos/bee-autopiloto.yml` com `.github/workflows/bee-autopiloto.yml` e falha
de propósito enquanto o workflow ativo não receber a versão de
`docs/bee-autopiloto.yml`. O `worker/` é experimental e tem dependências
próprias (ver `worker/README.md`).

## Antes de publicar

Podem existir erros de tradução, Strong, transliteração, atribuição a léxicos
ou crítica textual. A validação automática verifica estrutura e marcação
(HTML, numeração, variantes), **não** fidelidade teológica ou filológica. Faça
revisão humana especializada e confira direitos e licenças. O projeto não é um
produto oficial ou aprovado pelo MyBible.

Referências, licenças e detalhes ficam nos JSON e nos metadados dos módulos.

### Nova edição: proposta de voz

Veja o [guia de estilo da BEE](docs/ESTILO_BEE.md), com amostras, ordem de tradução e plano para preservar a automação durante a transição editorial.

**Leia já:** [Filemom — piloto completo](edicoes/piloto/FILEMOM.md) · [Conheça a base grega SBLGNT](docs/SBLGNT.md).
Para gerar os módulos a partir da edição nova (parcial enquanto houver livros em curso): `python gerar_bee.py --compilar --dados edicoes/nova/livros_json --saida entregas/nova`.

**Próximas cartas:** [2 João — texto e notas para análise](edicoes/piloto/2_JOAO.md) · [3 João — texto e notas para análise](edicoes/piloto/3_JOAO.md).

**Leia também:** [Judas — carta completa e notas exegéticas](edicoes/piloto/JUDAS.md).

**Nova carta:** [Tito — texto integral e notas exegéticas](edicoes/piloto/TITO.md).

**Apresentação da BEE:** [documento de referência em Word](docs/APRESENTACAO_BEE.docx). As versões para apresentação pública (PDF, PPTX e outros formatos) ficam para o encerramento do projeto.
