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
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Módulos, fluxo, formato dos JSON e compilação. |
| [docs/EDITORIAL.md](docs/EDITORIAL.md) | Directrizes editoriais, variantes e revisão. |
| [AUTOMACAO.md](docs/AUTOMACAO.md) | Quotas gratuitas, provedores, ritmo e resolução de problemas. |
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

## Estado actual (17/11/2026)

- **19 capítulos estruturalmente completos:** João 1–18 e Filemom 1.
- **818 versículos guardados:** 806 nos capítulos completos + João 19:1–12 em
  `in_progress`.
- A fila retoma em **João 19:13**.
- O workflow ativo já está corrigido e igual a `docs/bee-autopiloto.yml`; a
  execução manual **16** (`44120273655`) terminou verde e criou
  `BEE-modulos-16` e `BEE-capitulos-16`.
- A execução 16 não somou versículos porque o Gemini devolveu **HTTP 503** e a
  quota da Groq estava esgotada. A próxima execução agendada volta a tentar;
  isto é disponibilidade dos serviços, não falta de agendamento.
  A correcção tem de ser colada na UI; o passo a passo está em
  [docs/OPERACAO.md](docs/OPERACAO.md#aplicar-a-versão-correcta-do-workflow).
- Tudo é provisório e precisa de revisão especializada.

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
