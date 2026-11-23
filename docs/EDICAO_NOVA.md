# Edição nova — como produzir (20/11/2026)

Este documento descreve o processo **atual** de produção da edição nova. A voz e as
regras de escrita estão em [`ESTILO_BEE.md`](ESTILO_BEE.md); o estado dos livros, em
[`ESTADO.md`](ESTADO.md). O processo anterior (perfis, autopiloto, workflows,
provedores de IA externos e a porta obrigatória do gerador) foi retirado e está no
histórico do Git.

## Princípios

- **Sem serviços externos de IA.** Os textos e as notas são escritos e revistos
  no repositório. Não há chaves de API nem produção automática.
- **Sem automação de publicação.** O repositório não tem workflows de GitHub Actions.
- **Rascunho primeiro.** Todo o livro nasce em `rascunho`. Só o responsável
  aprova. O agente não aprova em nome dele.
- **A colação manda na crítica textual.** Nenhuma testemunha é citada numa nota sem
  constar do aparato SBLGNT ou de `docs/colacao/<livro>.json`.

## Fonte de verdade

| Ficheiro | Conteúdo |
|---|---|
| `edicoes/nova/livros_json/NNN_Livro.json` | Texto e notas. Fonte única. |
| `edicoes/nova/<LIVRO>.md` | Leitura em Markdown, gerada a partir do JSON. Não se edita à mão. |
| `docs/colacao/<livro>.json` e `.md` | Colação verificável, gerada por `scripts/colar.py`. |
| `modelos/estilo_bee.json` | Memória de estilo: regras, glossário e vetos. Referência para quem escreve. |

Estrutura de um JSON de livro:

- `chapters`: objeto cujas chaves são os capítulos (`"1"`, `"2"`, …), com uma lista de
  versículos. Cada versículo tem `verse`, `text` (a tradução) e `commentary` (a nota).
- `review.editorial_blocks`: lista de blocos por intervalo de versículos, com `chapter`,
  `verse_from`, `verse_to`, `status` (`rascunho` ou `aprovado`) e `nota`.
- `review.specialist`: revisão especializada, em regra `pendente`.

## Formato da nota

Cada nota é um parágrafo de prosa, sem rótulos. A regra completa está em
[`ESTILO_BEE.md`](ESTILO_BEE.md), secção «Formato das notas — prosa». Em resumo:

1. O termo grego vai em itálico, com a transliteração entre parênteses na primeira ocorrência.
2. A razão da escolha e a alternativa rejeitada entram na própria prosa.
3. A «Crítica Textual:» é um parágrafo próprio, só quando há variante, e cita as siglas
   do aparato e da colação.
4. Não se escrevem níveis de certeza (A, B, C) nem rótulos antigos. Uma passagem de
   decisão difícil é assinalada em `review` para revisão especializada.
5. Colchetes no texto só quando a evidência o pede (regra de 2026-11-22).

`bee/inspetor.analisar_comentario` verifica estas regras.

## Fluxo por livro

1. **Colação.** `python3 scripts/colar.py --livro N` gera `docs/colacao/<livro>.json` e `.md`.
   Precisa das transcrições CNTR em `.bee-cache/cntr/`, que não estão no Git.
2. **Texto e notas.** Escrever ou rever o JSON do livro, capítulo a capítulo.
3. **Itálico do grego.** `python3 scripts/italico_grego.py --dados edicoes/nova/livros_json`
   mostra o que falta. Com `--aplicar` altera todos os JSON da pasta: correr só depois de
   rever o que vai mudar.
4. **Verificar a voz.** `python3 scripts/verificar_estilo.py 500` (ou sem argumentos para
   todos os livros). Com `--rigoroso`, os avisos de Almeida também chumbam.
5. **Verificar a crítica textual.**
   `python3 scripts/verificar_notas_colacao.py --dados edicoes/nova/livros_json/500_Joao.json --colacao docs/colacao/João.json`
   Deve sair com rc 0. Toda a variante do aparato tem de ter CT no capítulo.
6. **Ortografia.** `python3 scripts/verificar_ortografia.py` (alerta, não substitui leitura).
7. **Leitura.** `python3 scripts/gerar_leitura_livro.py --livro 500 --saida edicoes/nova/JOAO.md`.
8. **Integridade.** `python3 scripts/verificar_dados.py` e `python3 -m pytest`.
9. **Estado e módulos.** `python3 gerar_bee.py --status`; `python3 gerar_bee.py --compilar`
   compila os módulos MyBible (só capítulos completos e consecutivos desde o capítulo 1).

## Aprovação

- O agente não muda nenhum bloco para `aprovado`.
- A aprovação é do responsável e fica registada em `review.editorial_blocks` com a
  data e a nota.
- Revisão especializada em línguas bíblicas é outra etapa e não se confunde com a
  aprovação editorial.

## Limitações conhecidas

- Os scripts de conversão usados em 2026-11-20 (para passar notas de formato antigo
  para prosa) não estão no repositório. Os JSON resultantes são a fonte; a reprodução
  faz-se revendo o texto, não reexecutando um script.
- A colação depende de `.bee-cache/` (ignorado pelo Git, com licença CC BY-SA das
  transcrições). Sem esse cache, `colar.py` não corre.
- `docs/colacao/João.md` ainda não foi revisto.
- Marcos 16:9–20 não está produzido.

## Testes

```
python3 -m venv /tmp/venv && /tmp/venv/bin/pip install pytest
/tmp/venv/bin/python -m pytest -q
```

Em 2026-11-20: 163 passam, 1 ignorado.
