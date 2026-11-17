# Operação — ligar, pausar, recuperar e diagnosticar

Este é o guia de operação da produção automática. Para o desenho do código e
dos dados, ver [ARQUITETURA.md](ARQUITETURA.md); para números e decisões,
[ESTADO.md](ESTADO.md); para quotas e custos, [AUTOMACAO.md](AUTOMACAO.md).

## Comando de produção

O código novo produz com **`autopiloto.py`** (ou `nuvem.py` dentro do GitHub
Actions). `gerar_bee.py` fica para o percurso antigo, de um livro inteiro por
chamada.

```bash
# Uma fatia pequena, sem ficar em ciclo
python3 autopiloto.py --uma-vez

# Estado actual (não gasta quota)
python3 autopiloto.py --status

# Testar as chaves e descobrir o modelo disponível (gasta 1 pedido)
python3 autopiloto.py --testar

# Configuração e próximo capítulo, sem gastar quota
python3 autopiloto.py --doctor
```

A fonte de dados é o **`main`**: não existe um segundo ramo de dados. O estado
fica em `livros_json/.bee/estado.json`, o diário em `livros_json/.bee/diario.md`
e a quarentena em `livros_json/.bee/quarentena.json`.

## Nuvem (GitHub Actions)

- Workflow: `.github/workflows/bee-autopiloto.yml`, cron `7,27,47 * * * *`
  (20 em 20 minutos), `timeout-minutes: 12`.
- Segredos necessários: `GEMINI_API_KEY` e, como reserva, `GROQ_API_KEY`
  (**Settings → Secrets and variables → Actions**). Nunca no repositório.
- O repositório é **público**: os minutos de Actions são ilimitados; o limite
  real é a quota gratuita da IA.

### Aplicar a versão correcta do workflow

O push de `.github/workflows/*` é recusado quando a integração não tem a
permissão `workflows`. Nesse caso, a alteração faz-se na UI:

1. Abrir
   <https://github.com/martinhossmadureiraministries/traducao-epignosis/edit/main/.github/workflows/bee-autopiloto.yml>.
2. Seleccionar tudo, apagar e colar o conteúdo de
   [`docs/bee-autopiloto.yml`](bee-autopiloto.yml) (ou de
   `modelos/bee-autopiloto.yml`, que deve ser igual).
3. **Commit changes**.
4. Confirmar com `python3 -m unittest tests.test_workflow_sincronizado -v`
   e correr uma vez em **Actions → BEE — produção automática → Run workflow**.

Enquanto o workflow ativo estiver diferente do modelo, o teste
`test_modelo_e_workflow_ativo_sao_iguais` falha de propósito.

### Pausar

Não apague o workflow para pausar. Na UI: **Actions → BEE — produção
automática → ⋯ → Disable workflow**. Para voltar: **Enable workflow**. A API
recusa `gh workflow disable` com HTTP 403 nesta integração.

Localmente: `Ctrl+C` interrompe no ponto seguro; o último lote válido fica
gravado e `--uma-vez` retoma do versículo seguinte.

### Recuperar

```bash
git pull
python3 scripts/verificar_dados.py --minimo 18
python3 autopiloto.py --status
python3 autopiloto.py --uma-vez
```

- Se um capítulo ficou a meio, o `in_progress` é retomado no versículo
  seguinte; não se recomeça o capítulo.
- Se um versículo entrou em quarentena, o texto tem um marcador
  `[Versículo pendente: …]`, há uma entrada em `livros_json/.bee/quarentena.json`
  e a produção continua. Para o refazer, remova o marcador e a entrada depois de
  confirmar o erro; nunca apague texto já produzido sem autorização.
- Se os dados tiverem sido substituídos por engano, o histórico do `main` e a
  etiqueta `arquivo-bee-dados-2026-11-17` permitem recuperar os 18 capítulos
  antigos.
- O `RELATORIO.txt` é escrito mesmo quando a execução falha.

### Diagnosticar

1. Ler o **resumo** no topo da execução no GitHub e os últimos 25 linhas de
   `livros_json/.bee/diario.md`.
2. Descarregar o artefacto `BEE-diagnostico-<run>.zip` (estado, diário,
   quarentena e relatório) ou, depois de aplicar o workflow novo,
   `BEE-modulos-<run>.zip` e `BEE-capitulos-<run>.zip`.
3. Erros comuns:
   - **HTTP 401/403**: chave errada ou sem permissão; corrigir o segredo.
   - **HTTP 404**: modelo retirado; o programa descobre outro sozinho.
   - **HTTP 429**: limite por minuto/quota; o rodízio passa ao outro provedor.
   - **HTTP 5xx / rede**: falha passageira; o próximo ciclo volta a tentar.
   - **Resposta inválida persistente**: o lote é dividido; se continuar, o
     versículo vai para quarentena e a fila não bloqueia.
4. `python3 autopiloto.py --testar` isola a chave e o modelo sem produzir texto.

## Desenvolvimento

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_workflow_sincronizado -v
```

Os testes principais usam só a biblioteca padrão. O `worker/` é experimental e
tem dependências próprias (ver `worker/README.md`).
