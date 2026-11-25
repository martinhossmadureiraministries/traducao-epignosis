# Estado do projeto — após a aprovação de Hebreus (2026-11-20)

Para retomar o trabalho num ramo novo, ver `docs/PASSAGEM_DE_SESSAO.md`. Este documento descreve o estado **atual**. O histórico (diário de 17 a 24 de novembro, workflows retirados, migrações de dados) está no Git (`git log`). Os documentos de processo antigos estão em `docs/arquivo/`.

## Três revisões, separadas

| Revisão | Quem faz | Estado nos 30 livros |
|---|---|---|
| **Editorial** (`review.editorial_blocks`) | O responsável (Martinho S. S. Madureira). Só ele aprova. | `aprovado editorialmente` em todos os blocos |
| **Especializada** (`review.specialist`) | Especialista externo (hebraísta, grecista, crítico textual ou teólogo). Não é feita pelo responsável nem pelo agente. | `pendente` em todos |
| **Aprovada pelo ministério** (`review.ministerio`) | Martinho S. S. Madureira Ministries, etapa própria. | `aprovado pelo ministério` em todos os 30 livros (indicação do responsável) |

Não há revisão por inteligência artificial no processo. Nenhum agente aprova em nome do responsável, nem declara a revisão especializada concluída.

## Livros com edição nova

Edição nova: 30 livros no repositório, 157 capítulos e 3 533 versículos, todos em prosa. Todos os 30 estão aprovados editorialmente e pelo ministério, por indicação do responsável; a revisão especializada está pendente em todos. O 28.º é 2 Coríntios (540, 13 capítulos, 257 versículos), redigido pelo agente a partir do SBLGNT e da colação (`edicoes/nova/livros_json/540_2_Corintios.json`, `docs/colacao/2_Coríntios.json`), **aprovado editorialmente e pelo ministério** (2026-11-27); revisão especializada pendente. O 27.º é Gálatas (550, 6 capítulos, 149 versículos), redigido pelo agente a partir do SBLGNT e da colação (`edicoes/nova/livros_json/550_Galatas.json`), aprovado editorialmente pelo responsável (2026-11-27); revisão especializada e do ministério pendentes. O 26.º é 1 Timóteo (610, 6 capítulos, 113 versículos), redigido pelo agente a partir do SBLGNT e da colação (`edicoes/nova/livros_json/610_1_Timoteo.json`, `edicoes/nova/1_TIMOTEO.md`), **aprovado editorialmente e pelo ministério**, com 1:1 RP e 2:9 com «καὶ» (base). A revisão especializada está pendente. Os 25 livros anteriores estão `aprovado editorialmente` pelo responsável, incluindo 2 Timóteo (620, 4 capítulos, 83 versículos), 1 Pedro (670, 5 capítulos, 105 versículos), **1 João (690, 5 capítulos, 105 versículos)** e **Tiago (660, 5 capítulos, 108 versículos)**, aprovados em 2026-11-26. A revisão especializada está pendente nos 25, a cargo de especialista externo. A aprovação pelo ministério está registada nos 25 livros, por indicação do responsável nesta sessão. O ministério também aprovou as variações de forma sugeridas pelo agente (ver `docs/EDITORIAL.md`).

Os 30 livros estão `aprovado editorialmente` pelo responsável. Efésios (560) foi refeito a partir do grego e o responsável confirmou que corresponde ao texto aprovado antes; Hebreus (650) foi aprovado editorialmente e pelo ministério em 2026-11-20 (ver Cobertura do Novo Testamento).

| Livro | Capítulos | Versículos | Notas com CT | Editorial | Especializada | Ministério |
|---|---|---|---|---|---|---|
| Rute (080) | 4 | 85 | 0 | aprovado | pendente | aprovado pelo ministério |
| Oseias (350) | 14 | 197 | 0 | aprovado | pendente | aprovado pelo ministério |
| Joel (360) | 3 | 73 | 0 | aprovado | pendente | aprovado pelo ministério |
| Jonas (390) | 4 | 48 | 0 | aprovado | pendente | aprovado pelo ministério |
| Miqueias (400) | 7 | 105 | 0 | aprovado | pendente | aprovado pelo ministério |
| Naum (410) | 3 | 47 | 0 | aprovado | pendente | aprovado pelo ministério |
| Habacuque (420) | 3 | 56 | 0 | aprovado | pendente | aprovado pelo ministério |
| Sofonias (430) | 3 | 53 | 0 | aprovado | pendente | aprovado pelo ministério |
| Ageu (440) | 2 | 38 | 0 | aprovado | pendente | aprovado pelo ministério |
| Malaquias (460) | 4 | 55 | 0 | aprovado | pendente | aprovado pelo ministério |
| João (500) | 21 | 879 | 706 | aprovado | pendente | aprovado pelo ministério |
| 2 Coríntios (540) | 13 | 257 | 120 | aprovado | pendente | aprovado pelo ministério |
| Gálatas (550) | 6 | 149 | 65 | aprovado | pendente | aprovado pelo ministério |
| Efésios (560) | 6 | 155 | 70 | aprovado | pendente | aprovado pelo ministério |
| Filipenses (570) | 4 | 104 | 48 | aprovado | pendente | aprovado pelo ministério |
| Colossenses (580) | 4 | 95 | 57 | aprovado | pendente | aprovado pelo ministério |
| 1 Tessalonicenses (590) | 5 | 89 | 38 | aprovado | pendente | aprovado pelo ministério |
| 2 Tessalonicenses (600) | 3 | 47 | 28 | aprovado | pendente | aprovado pelo ministério |
| 1 Timóteo (610) | 6 | 113 | 36 | aprovado | pendente | aprovado pelo ministério |
| 2 Timóteo (620) | 4 | 83 | 33 | aprovado | pendente | aprovado pelo ministério |
| Tito (630) | 3 | 46 | 19 | aprovado | pendente | aprovado pelo ministério |
| Filemom (640) | 1 | 25 | 14 | aprovado | pendente | aprovado pelo ministério |
| Hebreus (650) | 13 | 303 | 120 | aprovado | pendente | aprovado pelo ministério |
| Tiago (660) | 5 | 108 | 56 | aprovado | pendente | aprovado pelo ministério |
| 1 Pedro (670) | 5 | 105 | 64 | aprovado | pendente | aprovado pelo ministério |
| 2 Pedro (680) | 3 | 61 | 36 | aprovado | pendente | aprovado pelo ministério |
| 1 João (690) | 5 | 105 | 53 | aprovado | pendente | aprovado pelo ministério |
| 2 João (700) | 1 | 13 | 9 | aprovado | pendente | aprovado pelo ministério |
| 3 João (710) | 1 | 14 | 8 | aprovado | pendente | aprovado pelo ministério |
| Judas (720) | 1 | 25 | 14 | aprovado | pendente | aprovado pelo ministério |

«Notas com CT» conta os versículos com parágrafo «Crítica Textual:». Os livros do AT não têm CT porque ainda não têm colação (`docs/colacao/`).

**Leituras** (`edicoes/nova/*.md`) são geradas a partir dos JSON por `scripts/gerar_leitura_livro.py`. Os ficheiros de 2 João, 3 João, Filemom, Judas e Tito estão lá com o mesmo formato dos outros.

**Joel e Oseias (lote 3):** entraram em `livros_json/` em 2026-11-24, com aprovação editorial do responsável em todos os capítulos e aprovação pelo ministério. As aspas de discurso direto foram acertadas conforme indicação do responsável: Oseias 6:4–6, 8:14, 10:9–11 e 11:8–11; Joel 2:25–27 e 3:1–8. Revisão especializada pendente, como nos outros livros. Por serem do AT, não têm colação de manuscritos nem «Crítica Textual».

## Cobertura do Novo Testamento

O Novo Testamento tem 27 livros. No repositório estão **20**, todos aprovados editorialmente e pelo ministério. Aprovados:

- João (500), 2 Coríntios (540), Gálatas (550), Filipenses (570), Colossenses (580), 1 Tessalonicenses (590), 2 Tessalonicenses (600), 1 Timóteo (610), 2 Timóteo (620), Tito (630), Filemom (640), Tiago (660), 1 Pedro (670), 2 Pedro (680), 1 João (690), 2 João (700), 3 João (710) e Judas (720).

**Em falta: 7 livros.** Mateus (470), Marcos (480), Lucas (490), Atos (510), Romanos (520), 1 Coríntios (530) e Apocalipse (730).

- **Efésios (560)**: o ficheiro aprovado pelo responsável não foi encontrado (nem em Git, nem em ramos, nem no sistema de ficheiros). O texto foi refeito a partir do grego, com o aparato da colação, e o responsável confirmou em 2026-11-20 que corresponde ao texto aprovado. Aprovado editorialmente e pelo ministério. Revisão especializada pendente, a cargo de especialista externo.
- **Hebreus (650)**: 13 capítulos e 303 versículos. Aprovado editorialmente e pelo ministério em 2026-11-20, por indicação do responsável. Revisão especializada pendente. Pontos abertos registados em `review.editorial_blocks`: 1:8, 3:6, 9:14 e 13:21 (diferenças entre a colação e as transcrições, por confirmar); a revisão de 12:1–13:25 foi feita por amostragem.
- Decisões de Efésios já registadas pelo responsável: 1:18 «coração» (base, καρδίας); 3:9 «administração» (base, οἰκονομία). As restantes estão em `docs/PASSAGEM_DE_SESSAO.md`.

## João

- **1–21:** aprovados pelo responsável como editorial. Os colchetes mantidos (3:13, 3:15, 3:34, 5:4, 7:53–8:11) são por evidência de manuscritos. Base SBLGNT mantida onde verificável.
- **Decisões de texto registadas:** 4:1 «Jesus» (com «o Senhor» na nota); 14:16, 14:26, 15:26 e 16:7 «Parácletos» e «Parácleton»; 16:25 e 16:29 «com clareza»; 20:15 «Jardineiro»; 20:17 «Não me segures»; 21:15 «mais do que estes»; 21:15–17 «amas-me» e «queres-me bem»; 14:22 «te vás manifestar a nós».
- **Pendências de texto de João, tratadas em 20/11/2026:** 11:1 «chamado» em itálico, com nota e CT (a colação regista que 02 omite «καὶ Μάρθας»). 11:16: itálico em «que quer dizer gémeo», com nota; «chamado» traduz λεγόμενος e fica em tipo normal (ver Pendências). 20:15: nota e CT conferidas com a colação (032 corrigido). 7:3, 7:8 e 8:25: CT conferida com o aparato e a colação; estava correta (7:8 com precisão sobre a primeira ocorrência de ἑορτήν). Colchetes já existentes, com nota: 5:4, 3:13, 3:15, 3:34, 7:53 e 8:1–8:11.

## 2 Tessalonicenses

Aprovado editorialmente pelo responsável, que o indicou como **livro-base** da memória de estilo (`modelos/estilo_bee.json`, `ancoras.livros_base`). A revisão especializada (especialista externo) e a revisão do ministério continuam pendentes.

## Cartas seguintes

Ordem por tamanho, das menores para as maiores, com prioridade para os livros que definem o estilo: ver `docs/RESUMO_ESTILO.md`, secção 10. **1 Timóteo (610, 113 versículos) está aprovado editorialmente e pelo ministério** (indicação do responsável); a revisão especializada está pendente. Próximo passo: **Apocalipse (730, 404 versículos)**, pela ordem de `docs/RESUMO_ESTILO.md`, secção 10; começar só após decisão do responsável. Colossenses (95 versículos) está aprovado editorialmente em `edicoes/nova/livros_json/580_Colossenses.json`; a decisão de 1:15 manteve «primogénito». 2 Pedro está concluído na edição nova (`edicoes/nova/livros_json/680_2_Pedro.json`); a colação está em `docs/colacao/2_Pedro.json` e `.md`. A decisão de ἐπίγνωσις (1:2, 1:3, 1:8, 2:20) está aplicada no rascunho: alternar «pleno conhecimento» e «conhecimento pleno» conforme a construção. As passagens que pedem decisão estão nas Críticas Textuais.

## Verificações (2026-11-20)

- `scripts/verificar_dados.py`: íntegro; 157 capítulos e 3 533 versículos completos.
- `scripts/verificar_documentacao.py`: coerente; 157 capítulos, 3 533 versículos, 0 em curso.
- `scripts/verificar_estilo.py`: limpo em 560 (Efésios) e 650 (Hebreus). Global: 1 falha dura pré-existente em 1 Timóteo (610), 5:18 («ponto fora das aspas»). Não foi tocada: alterar um livro aprovado depende de decisão do responsável.
- `scripts/verificar_convencoes_notas.py`: 0 falhas, 0 avisos.
- `scripts/verificar_notas_colacao.py`: conferem em Efésios (560) e Hebreus (650).
- `python3 -m unittest discover -s tests`: 188 testes, OK, 5 saltados (sem `pyspellchecker` e `python-docx` no Python do sistema). Com `/tmp/spellenv/bin/python`, 188 testes, OK, 1 saltado.

## Verificações (2026-11-27)

- `scripts/verificar_dados.py`: íntegro; 138 capítulos e 3 075 versículos completos (2 Coríntios e Gálatas incluídos).
- `scripts/verificar_notas_colacao.py` em 1 Timóteo (610): conferem com a colação.
- `scripts/verificar_estilo.py` e `scripts/verificar_convencoes_notas.py` em 1 Timóteo: sem falhas.
- `unittest discover -s tests`: ver a secção de testes após a atualização de 2026-11-27.

## Verificações (2026-11-26)

- `scripts/verificar_dados.py`: rc 0; 113 capítulos e 2 556 versículos completos.
- `scripts/verificar_estilo.py`: sem falhas duras nem avisos; sem arcaísmos nem marcas de Almeida.
- `scripts/verificar_convencoes_notas.py`: 0 falhas, 0 avisos.
- `scripts/verificar_documentacao.py`: rc 0; 113 capítulos e 2 556 versículos, 0 em curso.
- `scripts/verificar_notas_colacao.py`: confere as notas de 1 João (690) e de Tiago (660) com as respetivas colações; as restantes colações foram conferidas em verificações anteriores.
- `python3 -m unittest discover -s tests`: não repetido nesta atualização (última execução em 2026-11-20: 188 testes, OK; 5 saltados por falta de `pyspellchecker` e `python-docx`).
- Ortografia (`scripts/verificar_ortografia.py`): verificação de 2026-11-26, sem erros confirmados nos livros do PR.

## Documento de apresentação

`docs/APRESENTACAO_BEE.docx` é gerado por `scripts/gerar_apresentacao.py` (`pip install python-docx`). Os números e a tabela de estado vêm dos JSON. Não menciona revisão por IA. A versão anterior (com texto de 17/11) está em `docs/arquivo/APRESENTACAO_BEE.docx`. A pasta `arquivo/scripts/gerar_apresentacao.py` é o gerador antigo, arquivado.

## Código e arquivo

- Mantidos e ativos: `bee/inspetor.py`, `bee/sanea.py`, `bee/arquivos.py`, `bee/manuscritos.py`, `bee/fontes.py`, `bee/rede.py`, `bee/catalogo.py`, `bee/trava.py`, `bee/compilador.py`, `bee/grego.py`.
- Arquivados em `arquivo/`: `bee/porta.py`, `bee/memoria_estilo.py`, `scripts/aprovar_voz.py`. Não são importados por código ativo.
- Arquivados em `docs/arquivo/`: `PLANO_CORRECAO.md`, `REVISAO_GERAL.md`, `ci.yml`, leituras antigas (lotes, calibração, Amós, Obadias, Zacarias) em `leituras_legadas/` e os pilotos em `piloto/`.
- Sem automação de produção: o repositório não tem workflows de GitHub Actions. Não se recriam sem decisão do responsável.

## Pendências

1. **Responsável:** confirmar que `aprovado editorialmente` é o valor definitivo para os livros aprovados.
2. **Responsável:** decidir se o documento de apresentação volta a ser a versão oficial (o README e `arquivo/LEIA-ME.md` diziam que estava arquivado de propósito).
3. **Responsável:** decidir 11:16: itálico só em «que quer dizer gémeo» (como fica) ou também em «chamado».
4. **Revisão especializada:** pendente nos 30 livros, a cargo de especialista externo.
5. **Revisão do ministério:** registada em 30 livros, por indicação do responsável. A estrutura de `review.ministerio` é provisória, a confirmar.
6. **2 Pedro:** aprovado editorialmente e pelo ministério (2026-11-25). Falta a revisão especializada, a cargo de especialista externo.
7. **Marcos 16:9–20:** ainda não produzido (ver `docs/EDITORIAL.md`).
8. **Joel e Oseias:** resolvido em 2026-11-24 (ver acima). Falta a revisão especializada, como nos demais livros.
