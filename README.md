# Bíblia de Estudo Epignósis (BEE)

> **Obra:** Bíblia de Estudo Epignósis (BEE) — *Projeto Epignósis*\
> **Autor:** Martinho S. S. Madureira\
> **Publicado por:** Martinho S. S. Madureira Ministries

Tradução e comentários para os 66 livros e **1.189 capítulos** do cânone
escolhido, com compilação para os módulos MyBible `BEE.SQLite3` e
`BEE.commentaries.SQLite3`.

> **Rascunho:** o texto e os comentários estão em revisão. Nenhum livro é
> edição final enquanto a revisão especializada não estiver registada. O
> repositório é **público**; não coloque chaves nem dados pessoais no Git.

## Onde está o quê

| Documento | Para quê |
|---|---|
| [docs/ESTADO.md](docs/ESTADO.md) | Fotografia atual: progresso, decisões e o que falta. |
| [docs/ESTILO_BEE.md](docs/ESTILO_BEE.md) | Guia de estilo da voz BEE: formato das notas, grego, tratamento e rubricas. |
| [docs/EDICAO_NOVA.md](docs/EDICAO_NOVA.md) | Formato dos JSON da edição nova e comandos de compilação. |
| [docs/CRITICA_TEXTUAL.md](docs/CRITICA_TEXTUAL.md) | Protocolo de crítica textual, manuscritologia e exegese. |
| [docs/EDITORIAL.md](docs/EDITORIAL.md) | Diretrizes editoriais, colchetes, variantes e revisão. |
| [docs/colacao/](docs/colacao/) | Relatórios de colação por livro: a evidência verificável de cada nota (`scripts/colar.py`). |
| [docs/ARQUITETURA.md](docs/ARQUITETURA.md) | Módulos, fluxo e formato dos dados. |
| [docs/arquivo/PLANO_CORRECAO.md](docs/arquivo/PLANO_CORRECAO.md) | Plano de correção por etapas e decisões D1–D13 (arquivado). |
| [docs/SBLGNT.md](docs/SBLGNT.md) | A base grega (SBLGNT) e como é usada. |

## Dados e módulos

- Os JSON da edição nova ficam em `edicoes/nova/livros_json/`. É a única fonte
  de texto; os comandos usam esta pasta por defeito.
- Cada livro tem `chapters` (capítulos completos, que entram nos módulos) e
  `in_progress` (versículos de um capítulo em curso).
- A leitura em Markdown de cada livro é gerada a partir dos JSON, por exemplo:
  `python3 scripts/gerar_leitura_livro.py --livro 500 --dados edicoes/nova/livros_json --saida edicoes/nova/JOAO.md`.
- Verificações sem rede:
  - `python3 scripts/verificar_dados.py` (integridade dos JSON);
  - `python3 scripts/verificar_estilo.py <número>` (estilo e marcação);
  - `python3 scripts/verificar_notas_colacao.py --dados edicoes/nova/livros_json/<ficheiro>.json --colacao docs/colacao/<livro>.json`;
  - `python3 scripts/verificar_documentacao.py`.
- Compilação dos módulos MyBible, com a parte já completa:
  `python3 gerar_bee.py --compilar --dados edicoes/nova/livros_json --saida entregas/nova`.
- Estado atual: 91 capítulos e 2089 versículos guardados na edição nova
  (`verificar_documentacao.py`), dos 1.189 capítulos e 31.102 versículos do cânone.
  Inclui 2 Pedro e Colossenses 1, em rascunho ainda não aprovado (ver `docs/ESTADO.md`).

## Testes

```bash
python3 -m unittest discover -s tests -v
```

## Antes de publicar

Podem existir erros de tradução, Strong, transliteração, atribuição a léxicos
ou crítica textual. A validação automática verifica estrutura e marcação
(HTML, numeração, variantes), **não** fidelidade teológica ou filológica. Faça
revisão humana especializada e confira direitos e licenças. O projeto não é um
produto oficial ou aprovado pelo MyBible.

Referências, licenças e detalhes ficam nos JSON e nos metadados dos módulos.

**Leia:** [Filemom](edicoes/nova/FILEMOM.md) · [Judas](edicoes/nova/JUDAS.md) · [Tito](edicoes/nova/TITO.md) · [2 João](edicoes/nova/2_JOAO.md) · [3 João](edicoes/nova/3_JOAO.md) · [Filipenses](edicoes/nova/FILIPENSES.md) · [1 Tessalonicenses](edicoes/nova/1_TESSALONICENSES.md) · [2 Tessalonicenses](edicoes/nova/2_TESSALONICENSES.md) · [João](edicoes/nova/JOAO.md).

**Apresentação da BEE:** [`docs/APRESENTACAO_BEE.docx`](docs/APRESENTACAO_BEE.docx), gerada por `scripts/gerar_apresentacao.py` a partir dos JSON. A versão anterior fica em `docs/arquivo/APRESENTACAO_BEE.docx`.
