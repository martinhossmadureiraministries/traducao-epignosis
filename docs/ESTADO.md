# Estado do projeto — 20/11/2026

Este documento descreve o estado **atual**. O histórico de etapas (diário de
2026-11-17 a 2026-11-23, incluindo os workflows retirados e as migrações de dados)
está no Git: `git log` e os ficheiros anteriores a esta reescrita. Os documentos
de processo antigos estão em `docs/arquivo/`.

## Decisões em vigor

- **Formato único em prosa** (2026-11-23). Toda a nota é um parágrafo de prosa, sem
  rótulos («Análise Léxica», «Síntese Exegética»), sem níveis de certeza A/B/C impressos.
  A «Crítica Textual:» é um parágrafo próprio, só quando o aparato ou a colação
  registam variante. Regra verificada por `bee/inspetor.analisar_comentario`.
- **Crítica textual só com evidência colacionada** (2026-11-20). Um códice ou papiro
  só é citado onde existe colação em `docs/colacao/`. Edição impressa não é manuscrito;
  tradução moderna não é evidência textual; «o Textus Receptus» não é um texto único.
- **Desempate NA28** (decisão do responsável, 2026-11-20): quando as edições se dividem,
  segue-se NA28, e a nota regista a alternativa e a razão.
- **Colchetes só onde a evidência o pede** (regra do responsável, 2026-11-22).
- **Estatuto honesto.** Todo o livro nasce em `rascunho` (`review.editorial_blocks`) e
  a revisão especializada começa `pendente`. Só o responsável promove a `aprovado`.
  Nenhum agente aprova em nome do responsável.
- **Sem automação de produção.** O repositório não tem workflows de GitHub Actions. O
  responsável retirou-os; não se recriam nem se reativam sem decisão dele.
- **Ortografia europeia** (pt-PT): «connosco», «de facto», «registo», «facto», «ação».

## Estado dos livros (edição nova, `edicoes/nova/livros_json/`)

| Livro | Capítulos | Versículos | Com CT | Blocos editoriais | Revisão especializada |
|---|---|---|---|---|---|
| Rute (080) | 4 | 85 | 0 | aprovado (4) | — |
| Jonas (390) | 4 | 48 | 0 | aprovado (4) | — |
| Miqueias (400) | 7 | 105 | 0 | aprovado (7) | — |
| Naum (410) | 3 | 47 | 0 | aprovado (3) | — |
| Habacuque (420) | 3 | 56 | 0 | aprovado (3) | — |
| Sofonias (430) | 3 | 53 | 0 | aprovado (3) | — |
| Ageu (440) | 2 | 38 | 0 | aprovado (2) | — |
| Malaquias (460) | 4 | 55 | 0 | aprovado (4) | — |
| João (500) | 10 | 479 | 276 | 1–4 rascunho; 5–6 aprovado; 7–10 rascunho | pendente |
| Filipenses (570) | 4 | 104 | 48 | aprovado (4) | — |
| 1 Tessalonicenses (590) | 5 | 89 | 38 | rascunho (5) | — |
| 2 Tessalonicenses (600) | 3 | 47 | 28 | rascunho (3) | pendente |
| Tito (630) | 3 | 46 | 19 | rascunho (3) | pendente |
| Filemom (640) | 1 | 25 | 14 | rascunho (1) | pendente |
| 2 João (700) | 1 | 13 | 9 | rascunho (1) | pendente |
| 3 João (710) | 1 | 14 | 8 | rascunho (1) | pendente |
| Judas (720) | 1 | 25 | 14 | rascunho (1) | pendente |

Total: 59 capítulos e 1329 versículos, todos em prosa. Números de `scripts/verificar_dados.py`.

**Quem aprovou o quê.** Os oito livros do AT e Filipenses estão aprovados editorialmente
pelo responsável. João 5–6 foram aprovados em 2026-11-23. Os restantes estão em rascunho.
Os blocos 7–10 apareceram marcados como aprovados no ficheiro em 2026-11-20, sem registo
de aprovação do responsável. Foram revertidos para `rascunho` (ver nota abaixo).

## João

- **1–4:** prosa em rascunho. As Críticas Textuais de 4:1, 4:44 e 4:54 foram conferidas
  contra `docs/colacao/João.json` em 2026-11-20. As glosas das formas isoladas foram
  conferidas com o Dodson e o Abbott-Smith (ver `docs/EDITORIAL.md`, «Léxico»).
- **5–6:** aprovados pelo responsável em 2026-11-23.
- **7–10:** prosa em rascunho. Pendente: leitura do responsável; verificação versículo
  a versículo de 8:9, 8:11, 8:41, 9:1–41 e 10:29 contra o aparato e a colação. Estes
  versículos têm variantes com decisão difícil. Só depois de lidos e verificados
  podem ser aprovados.
- **Revisão especializada:** pendente em todo o livro. Os níveis de certeza
  ficam como classificação interna do trabalho (`review`), não nas notas.
- O ficheiro de leitura `edicoes/nova/JOAO.md` foi regenerado em 2026-11-20
  (`scripts/gerar_leitura_livro.py --livro 500`).

## Cartas

Filemom, Tito, Judas, 2 João, 3 João e 2 Tessalonicenses estão em prosa, gravadas e
conferidas com a colação respetiva (`scripts/verificar_notas_colacao.py`, rc 0).
Todos os blocos estão em `rascunho`, à espera de leitura. Em 2 Tessalonicenses as notas
recuperaram o conteúdo editorial verificado da versão anterior: 1:2 (sem «nosso», seguindo
a base), 1:11–12, 2:2, 2:13 (ἀπαρχήν, com a alternativa ἀπʼ ἀρχῆς), 3:6 (anártrico e
terceira pessoa de παρελάβοσαν), 3:16 (τόπῳ/τρόπῳ). Não há níveis de certeza impressos.

## 1 Tessalonicenses

Convertido e gravado (89 versículos, 38 com CT), `verificar_notas_colacao.py` rc 0.
Blocos em `rascunho`. Aguarda leitura do responsável.

## Verificações (2026-11-20)

- `python3 -m pytest`: 163 passam, 1 ignorado.
- `python3 scripts/verificar_estilo.py`: rc 0 (nenhum arcaísmo, hesitação ou marcador de Almeida).
- `python3 scripts/verificar_notas_colacao.py` para João, 1 Tessalonicenses, 2 Tessalonicenses,
  Tito, Filemom, 2 e 3 João e Judas: rc 0.
- `python3 scripts/verificar_dados.py`: dados íntegros.

## Código e arquivo

- `bee/inspetor.py`: guarda da voz (arcaísmos, marcas de Almeida, rótulos antigos, grego
  fora de itálico, `analisar_comentario`).
- `bee/sanea.py`: **mantido**. `bee/arquivos.py` depende dele para ler e validar os JSON.
- `bee/manuscritos.py`, `bee/fontes.py`, `bee/rede.py`, `bee/catalogo.py`, `bee/trava.py`,
  `bee/compilador.py`, `bee/grego.py`: mantidos.
- `arquivo/` (decisão do responsável, 2026-11-20): `bee/porta.py`, `bee/memoria_estilo.py`,
  `scripts/aprovar_voz.py`. Não são importados por código ativo.
- `docs/arquivo/`: `PLANO_CORRECAO.md`, `REVISAO_GERAL.md` e a proposta de CI `ci.yml`.

## Pendências

1. **Responsável:** ler João 7–10 (`edicoes/nova/JOAO.md`, linhas 602–999 e 2314–3216).
   Depois, verificar os versículos listados acima e só então aprovar.
2. **Responsável:** ler 1 Tessalonicenses e as cartas em rascunho.
3. **Revisão especializada:** pendente nos livros indicados na tabela. Não é substituível
   pelo responsável nem pelo agente.
4. **João 1–4:** léxico conferido; falta a leitura do responsável.
5. **`colacao/João.md`:** a versão em Markdown da colação ainda não foi revista.
6. **Commit e merge:** o trabalho de 2026-11-20 está por commitar no ramo
   `arena/86a50674-traducao-epignosis`, em conjunto com as alterações desta reescrita.
7. **Marcos 16:9–20:** ainda não produzido (ver `docs/EDITORIAL.md`).

## Nota sobre João 7–10 (2026-11-20)

O ficheiro chegou a ter os blocos 7–10 marcados como `aprovado`, com uma nota que dizia
«aprovado pelo responsável após leitura». Não há registo de aprovação do responsável que a suporte. Foi revertida para `rascunho`, com a nota anterior, e o texto e as notas
ficaram intactos (backup em `/tmp/conv/500_Joao.antes_reverte710.json`, efémero).
