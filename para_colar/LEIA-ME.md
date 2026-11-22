# Workflows para copiar à mão

O GitHub recusou o envio de `.github/workflows/*` (permissão `workflows` em falta
na ligação desta sessão). As alterações estão aqui, completas, prontas a copiar.

Copiar para o repositório (substitui o conteúdo atual, ficheiro a ficheiro):

| Esta pasta | Destino no repositório |
|---|---|
| `para_colar/.github/workflows/bee-autopiloto.yml` | `.github/workflows/bee-autopiloto.yml` |
| `para_colar/.github/workflows/bee-nova-edicao.yml` | `.github/workflows/bee-nova-edicao.yml` |

No site do GitHub: abrir o ficheiro de destino, Edit, apagar tudo, colar o conteúdo
desta pasta, Commit no próprio ramo `arena/b6fccf92-traducao-epignosis`.

Depois de copiar, `tests/test_workflow_sincronizado.py` deve passar (o ativo fica
igual a `modelos/bee-autopiloto.yml`). Até lá, esse teste fica vermelho de propósito.

As alterações são só estas: `--dados livros_json` explícito na verificação da
linha legada; ortografia sem `tee`; comentários nos testes de ligação (`|| true`).
Nenhum horário de cron mudou.

Quando estiver copiado e confirmado, esta pasta pode ser apagada.
