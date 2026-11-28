# Plano: completar o Novo Testamento, livro a livro e bloco a bloco

Data de referência: 2026-11-20 (sessão do ramo `arena/16306170`, fundido em `main` pelo PR #80).

Este plano segue `docs/RESUMO_ESTILO.md` (§8 correções de texto aprovado, §9 processo por livro, §10 ordem das cartas) e `docs/EDICAO_NOVA.md`. O agente redige, confere e regista. **Não aprova** nem marca aprovação; a aprovação editorial é do responsável, a especializada é de especialista externo, e a do ministério é da Martinho S. S. Madureira Ministries.

## Estado de partida

- 30 livros em `edicoes/nova/livros_json/`: 157 capítulos e 3 533 versículos. Apocalipse (730) em curso desde 2026-11-27: capítulo 1 em rascunho.
- Novo Testamento em falta (7 livros): **Mateus, Marcos, Lucas, Atos, Romanos, 1 Coríntios e Apocalipse.**
- Marcos 16:9–20 ainda não produzido (`docs/ESTADO.md`, pendência 7).

## Fase 0: concluída nesta sessão

- [x] Verificador de estilo apanha as formas de «vós» de imperativo e subjuntivo (testes novos; 190 OK).
- [x] «vós» → «vocês» no texto aprovado (João 10:37–38, 14:13–14; Tiago 1:19) e nas glosas das notas de 20 livros. Motivo registado na nota de cada bloco afetado (§8).
- [x] 1 Timóteo 5:18: pontuação. Hebreus 11:11: P46 na nota.
- [x] MD regenerados de todos os 30 livros; SQLite3 de prévia em `entregas/nova/` (parcial, 157/1189).
- [x] Merge para `main`.

## Fase 1: revisão dos 30 livros aprovados

Não se faz de uma vez. Faz-se livro a livro, na ordem de `docs/RESUMO_ESTILO.md` §10.

1. [ ] **Sinalizações léxicas (83).** Verificar à mão as entradas da heurística de termos gregos nas notas. Feito: 2 Tessalonicenses 1:2, Filipenses 2:7, 1 Pedro 4:16. Por fazer: as restantes (João com 41, 2 Tessalonicenses com 24, Filipenses com 5, Gálatas com 3, e as demais).
2. [ ] **Alertas ortográficos (166 versículos).** Amostra de 30 revista: falsos positivos (enclíticos, «lêem» com acento AO90, termos bíblicos). Restantes por confirmar à mão.
3. [ ] **Colação de Filipenses.** Em `docs/colacao/Filipenses.json`, «καὶ σχήματι εὑρεθεὶς ὡς ἄνθρωπος» está em 2:8 e deve estar em 2:7 (versificação padrão). Corrigir a colação com o SBLGNT à mão (não está no espaço de trabalho).
4. [ ] **Hebreus, discrepâncias colação × transcrições** (por decidir): 1:8 (01, 03, P46); 3:6; 9:14; 11:37 (01); 13:21 (01).
5. [ ] **Hebreus, CT a confirmar:** 9:1 (lista de «καί»), 9:3 (Treg e 03), 9:13 (ST e Scrivener). 10:17 e 10:22 verificados nesta sessão contra a colação (ok).
6. [ ] **Colchetes por verificar:** João 5:4 e 7:53–8:11 (`docs/RESUMO_ESTILO.md` §11).
7. [ ] **Regra de «vós» nas notas.** Rever as glosas que ficaram: citações da ARC (ex.: João 3:12) e leituras RP com «vós» já trocadas. Confirmar com o responsável se as citações de ARC devem manter «vós».

## Fase 2: os três livros pendentes que já têm lugar na ordem

Por tamanho e ordem de §10. Cada livro segue §9 e cada bloco é um capítulo (ou um intervalo, se o capítulo for longo).

| Ordem | Livro | Versículos | Notas |
|---|---|---|---|
| 1 | Romanos | 433 | Após a fase 1 dos livros de Paulo, que definem o estilo |
| 2 | 1 Coríntios | 437 | Colação `colar.py` a confirmar; `.bee-cache/cntr` necessário |
| 3 | Apocalipse | 404 | Ordem 17 em §10; último da lista de cartas |

Para cada livro:
1. Colação: `python3 scripts/colar.py --livro <N>` (exige `.bee-cache/cntr`; descarregar antes, ver `docs/CRITICA_TEXTUAL.md`).
2. Redação por bloco, a partir do SBLGNT e da colação. Notas em prosa, sem rótulos.
3. Verificadores: `verificar_dados.py`, `verificar_estilo.py`, `verificar_convencoes_notas.py`, `verificar_notas_colacao.py --dados … --colacao docs/colacao/<livro>.json`, `unittest`.
4. Lista para o responsável das passagens que pedem decisão (leitura da base e alternativa).
5. Regenerar MD (`scripts/gerar_leitura_livro.py`) e atualizar `docs/ESTADO.md`.

## Fase 3: Evangelhos e Atos

Mateus (1 071), Marcos (678, com 16:9–20 por decidir), Lucas (1 151) e Atos (1 007). Não estão em §10 e pedem uma decisão do responsável sobre a ordem e sobre a colação (os Evangelhos têm mais variantes). Só começam depois de:
- decisão do responsável sobre a ordem e sobre 16:9–20;
- colações geradas para cada livro.

## Fase 4: fecho

- Compilar os 66 livros: `python3 gerar_bee.py --compilar --dados edicoes/nova/livros_json --saida entregas/nova`. Hoje sai PARCIAL (157/1189).
- Gerar SQLite3, MD e JSON de todos os livros. Enviar para `main` por PR, só com os verificadores a passar.

## Decisões que cabem ao responsável

1. Confirmar, nos blocos alterados nesta sessão, a forma «vocês» (ver `docs/ESTADO.md`, «Correções desta sessão»).
2. Ordem e tratamento dos Evangelhos e de Atos (fase 3), e Marcos 16:9–20.
3. Se as citações de ARC mantêm «vós».
4. 11:16 em Hebreus: itálico só em «que quer dizer gémeo» (como fica) ou também em «chamado».

## Fora do alcance do agente

- Revisão especializada: só especialista externo (hebraísta, grecista, crítico textual ou teólogo).
- Revisão do ministério: Martinho S. S. Madureira Ministries.
- Aprovação editorial: responsável.
