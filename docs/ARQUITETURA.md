# Arquitetura — código, dados e compilação

## Entradas

| Ficheiro | Papel |
|---|---|
| `autopiloto.py` | Produção local em ciclos, com estado, diário e orçamento diário. |
| `nuvem.py` | Uma fatia de produção numa GitHub Action: gera, compila, publica e empacota. |
| `gerar_bee.py` | Percurso antigo de um livro inteiro por chamada; não tem janela, rodízio nem estado. |
| `scripts/verificar_dados.py` | Verifica a integridade dos JSON versionados, sem rede. |

## Módulos (`bee/`)

| Módulo | Responsabilidade |
|---|---|
| `catalogo.py` | Os 66 livros, números MyBible, nomes de ficheiro e versículos por capítulo. |
| `fontes.py` | Descarrega e alinha WLC/OSHB, SBLGNT e Textus Receptus; marca fontes ausentes. |
| `ia.py` | Provedores, descoberta de modelos, prompts, validação da resposta e `Rodizio`. |
| `rede.py` | `ClienteHTTP`: pausas, tentativas, 429 sem dormir, contagem real de pedidos. |
| `gerador.py` | Gera por lotes, divide respostas truncadas, grava checkpoints e trata a quarentena. |
| `arquivos.py` | Lê, valida e grava os JSON de forma atómica. |
| `compilador.py` | Constrói `BEE.SQLite3` e `BEE.commentaries.SQLite3` no formato MyBible. |
| `agenda.py` | Estado diário, diário legível, janela horária, tectos por provedor e decisões do ciclo. |
| `trava.py` | Impede duas execuções a escrever nos mesmos dados. |

## Fluxo de uma fatia

1. `autopiloto.py`/`nuvem.py` escolhe os livros da fila e o próximo capítulo
   incompleto.
2. `bee/fontes.py` fornece o texto-base alinhado ao versículo.
3. `bee/ia.py` pede um lote pequeno ao provedor disponível; em JSON inválido,
   outro provedor/modelo é tentado.
4. `bee/gerador.py` valida HTML, numeração e variantes; grava imediatamente em
   `in_progress` (checkpoint após cada lote).
5. Quando o capítulo fica completo, passa de `in_progress` para `chapters`.
6. `bee/compilador.py` recompila os dois módulos com os capítulos completos.
7. `nuvem.py` publica os JSON no `main`, exporta um HTML por capítulo e cria os
   ZIP da execução.

## Formato dos dados

`livros_json/<número>_<Livro>.json`:

```json
{
  "format_version": 1,
  "book_number": 640,
  "book_name": "Filemom",
  "chapter_count": 1,
  "sources": {"sblgnt_commit": "...", "textus_receptus_commit": "..."},
  "chapters": {"1": [{"verse": 1, "text": "...", "commentary": "..."}]},
  "in_progress": {"18": [{"verse": 1, "text": "...", "commentary": "..."}]},
  "history": [{"chapter": 1, "verse_from": 1, "verse_to": 6,
               "provider": "gemini", "model": "...", "generated_at_utc": "..."}]
}
```

- `chapters`: capítulos estruturalmente completos; só estes entram nos módulos.
- `in_progress`: versículos já guardados de um capítulo ainda a meio.
- Cada versículo tem `verse`, `text` e `commentary` com as três secções
  obrigatórias (Análise Léxica, Crítica Textual, Síntese Exegética).
- Marcadores que **não** são texto bíblico: `[Versículo sem texto
  correspondente no WLC consultado.]` (fonte ausente) e `[Versículo pendente:
  …]` (quarentena).
- `livros_json/.bee/estado.json`: ciclos, consumo por dia/provedor, lote em
  falta, última compilação.
- `livros_json/.bee/diario.md`: registo legível.
- `livros_json/.bee/quarentena.json`: referência, provedor, modelo, erro e data
  dos versículos por refazer.

## Compilação e artefactos

- `BEE.SQLite3`: texto bíblico; `BEE.commentaries.SQLite3`: comentários; ambos
  com `bee_complete`, `bee_source_gaps`, `bee_pending_verses` e estado de
  rascunho.
- `nuvem.py` cria `BEE-modulos-<run>.zip`, `BEE-capitulos-<run>.zip` e
  `BEE-diagnostico-<run>.zip` em `entregas/auto/`.
- O release `bee-previa` recebe os HTML e os ZIP para descarregar sem sessão.

## Testes

`tests/` cobre rede e 429, provedores/rodízio, geração e retoma, quarentena,
validação dos JSON, compilação, workflow sincronizado e pacotes. Os testes
principais não usam rede nem chaves. `worker/` é um protótipo separado para um
deployment Mistral e não faz parte do fluxo principal.
