# Passagem para a próxima sessão

Documento de passagem, escrito em 2026-11-26, depois da varredura completa que precedeu o merge do PR 75 para `main`. Serve para quem retomar o trabalho num ramo novo. Ler antes de tocar em texto.

## Estado após o merge

- **26 livros** em `edicoes/nova/livros_json/` (o 26.º, 1 Timóteo, está redigido e **por aprovar**), **119 capítulos**, **2 669 versículos**, todos completos.
- **Editorial:** os 25 estão `aprovado editorialmente` pelo responsável.
- **Ministério:** aprovado em 8 livros: Oseias, Joel, Colossenses, 2 Timóteo, Tiago, 1 Pedro, 2 Pedro e 1 João. Pendente nos outros 17.
- **Especializada:** pendente nos 25, a cargo de especialista externo.
- **Próximo livro:** **Gálatas (550, 149 versículos)**, na ordem de `docs/RESUMO_ESTILO.md`, secção 10.
- Verificações de 2026-11-26: dados, estilo, convenções e documentação passam. As notas de cada livro com colação conferem com a colação. As 25 leituras em `edicoes/nova/*.md` estão iguais aos JSON. Testes: `./.venv/bin/python -m unittest discover -s tests`, 188 testes OK.

## Regras de processo (instruções do responsável)

1. **As decisões de texto são do responsável.** O agente não decide variantes que mudem o sentido ou influenciem o texto: pergunta antes de redigir (`ask_user`), uma pergunta por variante, com a base e a RP descritas com o texto grego e a tradução.
2. **Variantes só de forma, artigo ou pronome sem efeito no sentido** podem ser decididas pelo agente, desde que fiquem registadas na CT do versículo.
3. **Nenhum texto novo de livro é commitado antes de o responsável aprovar o MD completo.** Commits de colação são aceites antes disso.
4. **Aprovação editorial e do ministério são decisões do responsável.** Registam-se só quando ele as indica. O agente não aprova em nome dele nem declara revisão especializada concluída.
5. **Ortografia:** português europeu, Acordo Ortográfico de 1990 (AO90). Artigo obrigatório depois de «todo/toda» («toda a boa obra», não «toda boa obra»). Teste em `tests/test_critica_textual.py`.
6. **Estilo de 1 João:** «vocês» com terceira pessoa. Nada de «vós», «vos», «sois», «sabeis», «conheceis», «tendes» (`verificar_estilo.py`, falha dura).
7. **Notas de crítica textual:** escrever a partir do aparato e da colação, nunca de memória. A CT de cada versículo traz o aparato SBLGNT lido da colação e a decisão.

## Como trabalhar um livro novo

1. Colação: `python3 scripts/colar.py --livro 610` (produz `docs/colacao/1_Timoteo.json` e `.md`). Precisa de `.bee-cache/cntr/` (acervo CNTR, CC BY-SA 4.0, revisão `4e743a41`, de `codeload.github.com`). Se faltar, descarregar de novo.
2. Ler o texto base SBLGNT e o aparato de cada versículo na colação. Listar as variantes que mudam o sentido e perguntá-las ao responsável.
3. Redigir o rascunho num ficheiro fora de `livros_json/` até as decisões estarem todas tomadas.
4. Construir o JSON, com `review.editorial_blocks` em `rascunho`, `specialist` em `pendente` e `ministerio` em `pendente`.
5. Verificar: `verificar_dados.py`, `verificar_estilo.py`, `verificar_convencoes_notas.py`, `verificar_notas_colacao.py --dados … --colacao …`, `gerar_leitura_livro.py`.
6. Apresentar o MD ao responsável. Só depois da aprovação: commit, e marcar `aprovado editorialmente`.
7. Atualizar `docs/ESTADO.md` (tabela e contagens), `README.md`, `docs/EDITORIAL.md`, `docs/RESUMO_ESTILO.md`, `scripts/gerar_apresentacao.py` (texto «Próximo livro») e regenerar `docs/APRESENTACAO_BEE.docx` com `./.venv/bin/python scripts/gerar_apresentacao.py`.

## Ambiente e ferramentas

- `.venv` (fora do Git): `pyspellchecker` e `python-docx`. Usar `./.venv/bin/python` para a ortografia, a apresentação e os testes completos. Com o Python do sistema, 5 testes saltam.
- `scripts/verificar_ortografia.py`: 119 alertas em 2026-11-26. Os alertas novos de Tiago e 1 João são falsos positivos (primícias, transgressores, enganamo-nos, fazemo-lo, amemo-nos, gloriação). Continua por confirmar «acepção» / «aceção» (AO90).
- `gh pr edit` falha por causa de um aviso de Projects clássicos. Para atualizar o corpo de um PR: `gh api -X PATCH repos/martinhossmadureiraministries/traducao-epignosis/pulls/N -F "body=@ficheiro.md"`.
- `python3 -m unittest discover -s tests -t .` falha com ImportError. Usar `python3 -m unittest discover -s tests`.

## Pendências abertas

**Para o responsável (decisões):**
- **1 João 2:27** («dele», RP «isso»), **3:15** («nele», RP «em si mesmo») e **5:2** («praticamos», RP «guardamos»): o agente seguiu a base. Não foram confirmadas pelo responsável. Estas variantes podem mudar o sentido e devem ser perguntadas.
- **Artigos acrescentados em textos aprovados** (2026-11-26, para passar o teste de português europeu): Colossenses 1:10 («toda a boa obra»); 2 Timóteo 2:21 e 3:17 («toda a boa obra»); 2 Timóteo 4:18 («toda a obra má»). Não mudam o sentido. O responsável deve confirmar.
- **Tiago:** as variantes só de forma foram decididas pelo agente, e estão nas CT. Rever na revisão especializada ou na leitura final.
- **1 Pedro 5:14:** «Ἰησοῦ» e «ἀμήν» da RP foram omitidos por analogia com 5:10, sem perguntar. Perguntar antes de manter.
- **Colossenses 1:15:** «primogénito de toda a criação» (decisão do responsável). Não trocar por «protótipo» sem nova decisão.
- **2 Timóteo 4:13 e 4:20:** não interpretados no cruzamento com o SBLGNT.

**Revisão especializada (especialista externo), nos 25 livros.** Itens conhecidos: 2 Pedro 2:4 (WH e Treg com «σιροῖς» segundo o aparato, mas a colação regista «σειροῖς» para WH; discrepância na CT); 1 João 3:19 e 5:13 decididos como base pelo responsável; 1 Pedro, 2 Timóteo e Colossenses com as variantes de forma seguindo a base.

**Dívida de processo:** 1 João foi commitado como rascunho antes da aprovação do MD (commit `2a94b90`). A aprovação indevida que veio a seguir (`465016b`) foi revertida em `6856c2a`. Não repetir: aprovar o MD antes de commitar texto.

## Histórico relevante

- `465016b` (aprovação indevida de 1 João, sem decisão do responsável) foi revertido em `6856c2a`. A aprovação correta de 1 João e Tiago está em `a454d8a`, na sequência de instrução explícita do responsável em 2026-11-26.
- Tiago foi redigido de 1:1 a 5:20 com 108 versículos. Decisões de sentido do responsável: 1:19 base; 2:20 RP («morta»); 3:5 RP («um pouco de fogo»); 3:9 base; 3:12, 4:4, 4:9, 4:11, 4:12, 4:13, 4:14 («são»), 4:15, 5:4, 5:5, 5:10, 5:11, 5:12, 5:16 e as restantes variantes de sentido: base.
