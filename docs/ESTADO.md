# Estado do projeto — 20/11/2026

Este documento descreve o estado **atual**. O histórico (diário de 17 a 24 de novembro, workflows retirados, migrações de dados) está no Git (`git log`). Os documentos de processo antigos estão em `docs/arquivo/`.

## Três revisões, separadas

| Revisão | Quem faz | Estado nos 22 livros |
|---|---|---|
| **Editorial** (`review.editorial_blocks`) | O responsável (Martinho S. S. Madureira). Só ele aprova. | `aprovado editorialmente` em todos os blocos |
| **Especializada** (`review.specialist`) | Especialista externo (hebraísta, grecista, crítico textual ou teólogo). Não é feita pelo responsável nem pelo agente. | `pendente` em todos |
| **Aprovada pelo ministério** (`review.ministerio`) | Martinho S. S. Madureira Ministries, etapa própria. | `pendente` nos 17 livros; `aprovado pelo ministério` em Oseias, Joel, 2 Pedro, Colossenses e 2 Timóteo |

Não há revisão por inteligência artificial no processo. Nenhum agente aprova em nome do responsável, nem declara a revisão especializada concluída.

## Livros com edição nova

Edição nova: 23 livros, 103 capítulos e 2 343 versículos, todos em prosa. Os 22 livros estão `aprovado editorialmente` pelo responsável, incluindo 2 Timóteo (620, 4 capítulos, 83 versículos). A revisão especializada está pendente nos 22, a cargo de especialista externo. A aprovação pelo ministério está registada em Oseias, Joel e 2 Pedro. 1 Pedro (670, 5 capítulos, 105 versículos) está redigido em rascunho (`edicoes/nova/livros_json/670_1_Pedro.json`), por aprovar pelo responsável e pelo ministério.

Todos os 22 estão `aprovado editorialmente` pelo responsável: Rute, Oseias, Joel, Jonas, Miqueias, Naum, Habacuque, Sofonias, Ageu, Malaquias, João, Filipenses, 1 Tessalonicenses, 2 Tessalonicenses, Tito, Filemom, 2 João, 3 João, Judas, 2 Pedro, Colossenses e 2 Timóteo.

| Livro | Capítulos | Versículos | Notas com CT | Editorial | Especializada | Ministério |
|---|---|---|---|---|---|---|
| Rute (080) | 4 | 85 | 0 | aprovado | pendente | pendente |
| Oseias (350) | 14 | 197 | 0 | aprovado | pendente | aprovado pelo ministério |
| Joel (360) | 3 | 73 | 0 | aprovado | pendente | aprovado pelo ministério |
| Jonas (390) | 4 | 48 | 0 | aprovado | pendente | pendente |
| Miqueias (400) | 7 | 105 | 0 | aprovado | pendente | pendente |
| Naum (410) | 3 | 47 | 0 | aprovado | pendente | pendente |
| Habacuque (420) | 3 | 56 | 0 | aprovado | pendente | pendente |
| Sofonias (430) | 3 | 53 | 0 | aprovado | pendente | pendente |
| Ageu (440) | 2 | 38 | 0 | aprovado | pendente | pendente |
| Malaquias (460) | 4 | 55 | 0 | aprovado | pendente | pendente |
| João (500) | 21 | 879 | 705 | aprovado | pendente | pendente |
| Filipenses (570) | 4 | 104 | 48 | aprovado | pendente | pendente |
| Colossenses (580) | 4 | 95 | 57 | aprovado | pendente | aprovado pelo ministério |
| 2 Timóteo (620) | 4 | 83 | 0 | aprovado | pendente | aprovado pelo ministério |
| 1 Tessalonicenses (590) | 5 | 89 | 38 | aprovado | pendente | pendente |
| 2 Tessalonicenses (600) | 3 | 47 | 28 | aprovado | pendente | pendente |
| Tito (630) | 3 | 46 | 19 | aprovado | pendente | pendente |
| Filemom (640) | 1 | 25 | 14 | aprovado | pendente | pendente |
| 2 Pedro (680) | 3 | 61 | 36 | aprovado | pendente | aprovado pelo ministério |
| 2 João (700) | 1 | 13 | 9 | aprovado | pendente | pendente |
| 3 João (710) | 1 | 14 | 8 | aprovado | pendente | pendente |
| Judas (720) | 1 | 25 | 14 | aprovado | pendente | pendente |

«Notas com CT» conta os versículos com parágrafo «Crítica Textual:». Os livros do AT não têm CT porque ainda não têm colação (`docs/colacao/`).

**Leituras** (`edicoes/nova/*.md`) são geradas a partir dos JSON por `scripts/gerar_leitura_livro.py`. Os ficheiros de 2 João, 3 João, Filemom, Judas e Tito estão lá com o mesmo formato dos outros.

**Joel e Oseias (lote 3):** entraram em `livros_json/` em 2026-11-24, com aprovação editorial do responsável em todos os capítulos e aprovação pelo ministério. As aspas de discurso direto foram acertadas conforme indicação do responsável: Oseias 6:4–6, 8:14, 10:9–11 e 11:8–11; Joel 2:25–27 e 3:1–8. Revisão especializada pendente, como nos outros livros. Por serem do AT, não têm colação de manuscritos nem «Crítica Textual».

## João

- **1–21:** aprovados pelo responsável como editorial. Os colchetes mantidos (3:13, 3:15, 3:34, 5:4, 7:53–8:11) são por evidência de manuscritos. Base SBLGNT mantida onde verificável.
- **Decisões de texto registadas:** 4:1 «Jesus» (com «o Senhor» na nota); 14:16, 14:26, 15:26 e 16:7 «Parácletos» e «Parácleton»; 16:25 e 16:29 «com clareza»; 20:15 «Jardineiro»; 20:17 «Não me segures»; 21:15 «mais do que estes»; 21:15–17 «amas-me» e «queres-me bem»; 14:22 «te vás manifestar a nós».
- **Pendências de texto de João, tratadas em 20/11/2026:** 11:1 «chamado» em itálico, com nota e CT (a colação regista que 02 omite «καὶ Μάρθας»). 11:16: itálico em «que quer dizer gémeo», com nota; «chamado» traduz λεγόμενος e fica em tipo normal (ver Pendências). 20:15: nota e CT conferidas com a colação (032 corrigido). 7:3, 7:8 e 8:25: CT conferida com o aparato e a colação; estava correta (7:8 com precisão sobre a primeira ocorrência de ἑορτήν). Colchetes já existentes, com nota: 5:4, 3:13, 3:15, 3:34, 7:53 e 8:1–8:11.

## 2 Tessalonicenses

Aprovado editorialmente pelo responsável, que o indicou como **livro-base** da memória de estilo (`modelos/estilo_bee.json`, `ancoras.livros_base`). A revisão especializada (especialista externo) e a revisão do ministério continuam pendentes.

## Cartas seguintes

Ordem por tamanho, das menores para as maiores, com prioridade para os livros que definem o estilo: ver `docs/RESUMO_ESTILO.md`, secção 10. Colossenses (95 versículos) está aprovado editorialmente em `edicoes/nova/livros_json/580_Colossenses.json`; a decisão de 1:15 manteve «primogénito». 2 Pedro está concluído na edição nova (`edicoes/nova/livros_json/680_2_Pedro.json`); a colação está em `docs/colacao/2_Pedro.json` e `.md`. A decisão de ἐπίγνωσις (1:2, 1:3, 1:8, 2:20) está aplicada no rascunho: alternar «pleno conhecimento» e «conhecimento pleno» conforme a construção. As passagens que pedem decisão estão nas Críticas Textuais.

## Verificações (2026-11-20)

- `scripts/verificar_dados.py`: rc 0; 103 capítulos e 2 343 versículos (inclui Colossenses, 1 a 4, e 2 Timóteo, 1 a 4, aprovado editorialmente).
- `scripts/verificar_estilo.py`: rc 0; sem arcaísmos nem marcas de Almeida.
- `scripts/verificar_convencoes_notas.py`: rc 0; 0 falhas, 0 avisos.
- `scripts/verificar_documentacao.py`: rc 0.
- `scripts/verificar_notas_colacao.py` (João, Filipenses, 1 e 2 Tessalonicenses, Tito, Filemom, 2 e 3 João, Judas): rc 0.
- `python3 -m unittest discover -s tests`: 188 testes, OK. Saltam 5 quando faltam `pyspellchecker` (verificação ortográfica, que por isso não correu) ou `python-docx` (documento de apresentação).

## Documento de apresentação

`docs/APRESENTACAO_BEE.docx` é gerado por `scripts/gerar_apresentacao.py` (`pip install python-docx`). Os números e a tabela de estado vêm dos JSON. Não menciona revisão por IA. A versão anterior (com texto de 17/11) está em `docs/arquivo/APRESENTACAO_BEE.docx`. A pasta `arquivo/scripts/gerar_apresentacao.py` é o gerador antigo, arquivado.

## Código e arquivo

- Mantidos e ativos: `bee/inspetor.py`, `bee/sanea.py`, `bee/arquivos.py`, `bee/manuscritos.py`, `bee/fontes.py`, `bee/rede.py`, `bee/catalogo.py`, `bee/trava.py`, `bee/compilador.py`, `bee/grego.py`.
- Arquivados em `arquivo/`: `bee/porta.py`, `bee/memoria_estilo.py`, `scripts/aprovar_voz.py`. Não são importados por código ativo.
- Arquivados em `docs/arquivo/`: `PLANO_CORRECAO.md`, `REVISAO_GERAL.md`, `ci.yml`, leituras antigas (lotes, calibração, Amós, Obadias, Zacarias) em `leituras_legadas/` e os pilotos em `piloto/`.
- Sem automação de produção: o repositório não tem workflows de GitHub Actions. Não se recriam sem decisão do responsável.

## Pendências

1. **Responsável:** confirmar que `aprovado editorialmente` é o valor definitivo para os 22 livros.
2. **Responsável:** decidir se o documento de apresentação volta a ser a versão oficial (o README e `arquivo/LEIA-ME.md` diziam que estava arquivado de propósito).
3. **Responsável:** decidir 11:16: itálico só em «que quer dizer gémeo» (como fica) ou também em «chamado».
4. **Revisão especializada:** pendente nos 22 livros, a cargo de especialista externo.
5. **Revisão do ministério:** pendente nos 17 livros (Oseias, Joel, 2 Pedro, Colossenses e 2 Timóteo já a têm registada). A estrutura de `review.ministerio` é provisória, a confirmar.
6. **2 Pedro:** aprovado editorialmente e pelo ministério (2026-11-25). Falta a revisão especializada, a cargo de especialista externo.
7. **Marcos 16:9–20:** ainda não produzido (ver `docs/EDITORIAL.md`).
8. **Joel e Oseias:** resolvido em 2026-11-24 (ver acima). Falta a revisão especializada, como nos demais livros.
