#!/usr/bin/env bash
# Aplica a proposta da Etapa 1 aos dois ficheiros que têm de ficar iguais.
#
# O GitHub recusa o push de `.github/workflows/` quando a integração não tem a
# permissão `workflows`; este script só copia no seu computador. Depois faça
# commit e push com uma conta que tenha essa permissão.
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
origem="$raiz/docs/bee-autopiloto.yml"

if [[ ! -f "$origem" ]]; then
  echo "Não encontrei $origem" >&2
  exit 1
fi

cp "$origem" "$raiz/modelos/bee-autopiloto.yml"
mkdir -p "$raiz/.github/workflows"
cp "$origem" "$raiz/.github/workflows/bee-autopiloto.yml"

echo "Workflow aplicado nos dois sítios."
echo "Confirme com: python3 -m unittest tests.test_workflow_sincronizado -v"
echo "Depois: git add modelos/bee-autopiloto.yml .github/workflows/bee-autopiloto.yml"
echo "        git commit -m 'BEE: workflow com timeout de 12 min' && git push"
