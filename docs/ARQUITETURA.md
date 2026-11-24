# Arquitetura

Estado em 20/11/2026, depois da retirada da produção por IA (`d82baf3`). O
registo do que foi retirado está no histórico (`git show a80fa33:<caminho>`).

## Fluxo de trabalho

1. **Fontes fixadas.** O texto grego é o SBLGNT (`bee/fontes.py`), com o aparato
   e o Textus Receptus como comparação. Cada versão tem um commit fixado.
2. **Colação.** `scripts/colar.py` confronta o aparato com as testemunhas
   consultadas (`bee/manuscritos.py`) e grava o relatório em `docs/colacao/`.
3. **Redação.** Texto de cada versículo, e a nota quando a há, ficam em
   `edicoes/nova/livros_json/<número>_<Livro>.json`. O formato da nota é prosa
   (ver `docs/ESTILO_BEE.md`).
4. **Verificação.** `scripts/verificar_dados.py` (integridade),
   `scripts/verificar_estilo.py` (estilo e marcação),
   `scripts/verificar_notas_colacao.py` (notas contra a colação),
   `scripts/verificar_ortografia.py` (ortografia europeia) e
   `scripts/verificar_documentacao.py` (documentos contra os dados).
5. **Leitura.** `scripts/gerar_leitura_livro.py` gera o Markdown de cada livro.
6. **Compilação.** `gerar_bee.py --compilar` gera os módulos MyBible
   (`BEE.SQLite3` e `BEE.commentaries.SQLite3`).

A revisão editorial, a especializada (especialista externo) e a aprovada pelo ministério
ficam registadas em `review` no próprio JSON, e nunca são confundidas com cobertura.

## Módulos (`bee/`)

| Módulo | Função |
|---|---|
| `arquivos.py` | leitura validada dos JSON e checkpoints atómicos |
| `catalogo.py` | os 66 livros e a numeração MyBible |
| `fontes.py` | textos originais fixados, cache e versificação |
| `manuscritos.py` | leitura das transcrições e colação verificável |
| `rede.py` | pedidos HTTPS com limite de ritmo, usados pela colação e pelas fontes |
| `grego.py` | convenção do grego nas notas (itálico) |
| `inspetor.py` | guarda determinística da voz: arcaísmos, marcas e formato único em prosa |
| `compilador.py` | compilação dos módulos MyBible |
| `trava.py` | trava de processo para que duas compilações não escrevam ao mesmo tempo |
| `sanea.py` | validação de HTML simples; usado por `arquivos.py` na leitura das respostas |

## Scripts principais (`scripts/`)

- `colar.py` — colação por livro.
- `gerar_leitura_livro.py` — leitura em Markdown.
- `verificar_*.py` — verificações listadas no fluxo acima.
- `italico_grego.py` — aplica o itálico ao grego das notas.

`gerar_bee.py` (na raiz) só faz `--compilar`, `--status` e `--listar-livros`.
Não há produção automática nem chamadas a modelos de IA.

## Formato dos dados

Cada JSON de livro tem `format_version`, `book_number`, `book_name`,
`chapter_count`, `chapters`, `in_progress`, `history`, `sources`,
`bibliography` e `review`.

- `chapters`: capítulos completos; só estes entram nos módulos. Cada versículo
  tem `verse` e `text`. `commentary` (a nota) é opcional: omite-se a chave quando
  não há nota; se existir, não pode estar vazia.
- `in_progress`: versículos já guardados de um capítulo ainda a meio.
- `bibliography`: fontes efetivamente consultadas, com commit, URL e licença.
- `review`: estados das três revisões (editorial, especializada e ministério).

Marcadores que **não** são texto bíblico: `[Versículo sem texto
correspondente no WLC consultado.]` (fonte ausente) e `[Versículo pendente:
…]` (quarentena).

Formato único (decisão de 2026-11-23): quando há nota, é um parágrafo de
comentário em prosa, sem rótulos de secção e sem níveis de certeza. A
Crítica Textual é um parágrafo próprio, «Crítica Textual:», e só aparece
quando o aparato da SBLGNT ou a colação registam variante. Não há listas de
livros ou capítulos com formato diferente: `bee/inspetor.analisar_comentario`
verifica a regra para o livro inteiro.

## Estado do repositório

- `edicoes/nova/` é a única fonte de texto. A pasta legada `livros_json/` da raiz
  foi retirada.
- `livros_json/.bee/` (estado e diário da produção) mantém-se no repositório,
  por decisão D11 em `docs/arquivo/PLANO_CORRECAO.md`, até existir um ramo de dados.


## Código arquivado

`arquivo/` guarda `bee/porta.py`, `bee/memoria_estilo.py`, `scripts/aprovar_voz.py` e a versão antiga de `scripts/gerar_apresentacao.py` (ver `arquivo/LEIA-ME.md`). O gerador ativo é `scripts/gerar_apresentacao.py`, que produz `docs/APRESENTACAO_BEE.docx` a partir dos JSON. A apresentação anterior está em `docs/arquivo/APRESENTACAO_BEE.docx`. Os documentos `PLANO_CORRECAO.md` e `REVISAO_GERAL.md` estão em `docs/arquivo/`.
