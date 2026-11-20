# Workflow da edição nova — cópia para colar

`bee-nova-edicao.yml` nesta pasta é o workflow **completo e corrigido** da
produção automática da edição nova. O agente que prepara o código não tem
permissão do GitHub para escrever em `.github/workflows/`, por isso a
actualização faz-se à mão, uma vez:

1. No site do GitHub, abrir `.github/workflows/bee-nova-edicao.yml`.
2. Carregar no lápis (**Edit**), apagar tudo e colar o conteúdo inteiro de
   `modelos/workflows/bee-nova-edicao.yml`.
3. **Commit changes** (directamente no `main`).

## O que esta versão corrige (2026-11-20)

- **OpenRouter e NVIDIA**: os secrets criados chamam-se `OPENROUTER_KEY` e
  `NVIDIA_KEY`, mas o workflow lia `OPENROUTER_API_KEY`/`NVIDIA_API_KEY` —
  chegavam vazios e os dois provedores nunca eram usados. O workflow passa
  a aceitar os dois nomes (`secrets.X_API_KEY || secrets.X_KEY`), nos
  passos de teste, de produção e de diagnóstico. Não é preciso renomear
  secret nenhum.
- **Mistral**: entra na lista de provedores (`BEE_PROVEDORES`), mas a
  chave nunca era injectada nos passos. Passa a ser
  (`MISTRAL_API_KEY` ou `MISTRAL_KEY`). Ainda não existe esse secret no
  repositório: sem ele, o Mistral é simplesmente ignorado; para o activar,
  criar o secret `MISTRAL_API_KEY`.
- **Cloudflare**: o secret `CLOUDFLARE_KEY` não é usado — a Cloudflare
  Workers AI ainda não é suportada pelo motor (exige `CF_ACCOUNT_ID` e
  rotas de modelo por conta). Pode ficar guardado; não faz falta nem mal.

## Depois de colar

Lançar **Actions → BEE — edição nova → Run workflow** com
`pular_teste=nao`: o passo «Testar as ligações (não produz nada)» mostra no
resumo da execução o estado de cada provedor, sem escrever nada. É aí que
as chaves se verificam pela primeira vez.
