> **Experimental.** Este worker Mistral não faz parte do fluxo principal e
> não é usado pelo GitHub Actions nem pelo `autopiloto.py`. O caminho de
> produção actual está em [../docs/OPERACAO.md](../docs/OPERACAO.md).

# Worker BEE — workflow durável `bee-producao`

Produção contínua da Bíblia de Estudo Epignósis com modelos Mistral, num
deployment gerenciado da Mistral: depois de iniciada, a execução corre sozinha,
commita cada fatia no `main` e publica os módulos MyBible na release
`bee-previa` — sem depender do computador de ninguém.

## Como funciona

Cada iteração (fatia) é uma atividade:

1. Baixa os JSON de `livros_json/` do ramo de dados (o `main`, com recurso
   ao `main` quando o ramo ainda não tem ficheiros).
2. Gera um orçamento de versículos (`versos_por_fatia`) com o gerador existente
   (`gerar_fatia`), que consulta as fontes fixadas (WLC/OSHB, SBLGNT, Textus
   Receptus de Scrivener) e aplica o glossário e o contexto dos versículos
   anteriores. As diretrizes do responsável (`orientacoes`) entram no prompt do
   sistema com prioridade sobre o padrão.
3. Valida (HTML permitido, colchetes de variantes, numeração) e commita os JSON
   alterados num único commit de árvore no ramo de dados.
4. Quando um capítulo completa, recompila `BEE.SQLite3`,
   `BEE.commentaries.SQLite3` e `BEE-modulos.zip`, commita-os em `entregas/` e
   atualiza a release `bee-previa` (é daí que se descarrega o ZIP para o
   MyBible no Android).

O `continue-as-new` mantém o histórico pequeno, por isso a execução pode correr
até aos 1.189 capítulos. Três fatias consecutivas sem produção param a execução
com `motivo_paragem` em vez de girar à toa.

## Como usar

Executar (Console ou API), com entrada opcional:

```json
{
  "modelo": "mistral-medium-latest",
  "versos_por_fatia": 24,
  "versos_por_pedido": 8,
  "fatias_maximas": 60,
  "compilar": true,
  "publicar_release": true,
  "orientacoes": "Diretrizes editoriais adicionais do responsável.",
  "ordem": [640, 500]
}
```

Todos os campos têm padrão: sem entrada, produz pela ordem das oito fases do
`docs/EDITORIAL.md` com 24 versículos por fatia e até 60 fatias por execução (uma
execução nova retoma donde a anterior ficou, porque o estado vive nos JSON do
ramo de dados).

Signals numa execução a correr:

- `orientacoes` com `{"texto": "..."}`: novas diretrizes, aplicadas a partir da
  fatia seguinte.
- `parar` (sem payload): termina a execução ao fim da fatia em curso, sem
  perder o que já foi commitado.

Query `estado` devolve `{"parar": bool, "orientacoes_pendentes": bool}`.

## Requisitos do deployment

- **Secret do workspace** `GITHUB_TOKEN`: token fino do GitHub com permissão
  `contents: write` sobre este repositório (criar/atualizar o `main`,
  commitar módulos em `entregas/` e publicar a release). Vincular ao deployment
  como secret do workspace; o valor nunca vai para o código nem para o Git.
- `MISTRAL_API_KEY` não é precisa: no deployment o worker autentica-se com o
  token rotativo da conta de serviço; em desenvolvimento local, o SDK usa a
  variável `MISTRAL_API_KEY` do `.env`.

## Desenvolvimento

```bash
python -m venv .venv && source .venv/bin/activate
pip install "mistralai-workflows[mistralai]>=3.10" pytest pytest-asyncio
pytest worker/tests
```

Os testes não usam rede nem chaves: o motor Mistral, a sincronização GitHub e
as fatias são simulados.
