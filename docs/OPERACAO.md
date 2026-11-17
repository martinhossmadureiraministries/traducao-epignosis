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

- Workflow: `.github/workflows/bee-autopiloto.yml`, cron `23 * * * *`
  (1× por hora, ao minuto 23), `timeout-minutes: 15`.
- Segundo relógio: `.github/workflows/bee-relogio.yml`, cron `41 * * * *`;
  despacha a produção se ela não correu nos últimos 65 min.
- Se o GitHub não disparar o cron, o caminho está em
  [AGENDADOR.md](AGENDADOR.md). Para saber onde está:
  `python3 scripts/verificar_agendador.py`.
- Segredos necessários: `GEMINI_API_KEY` e, como reserva, `GROQ_API_KEY`
  (**Settings → Secrets and variables → Actions**). Nunca no repositório.
- O repositório é **público**: os minutos de Actions são ilimitados; o limite
  real é a quota gratuita da IA.

### Aplicar a versão correcta do workflow

O push de `.github/workflows/*` é recusado quando a integração não tem a
permissão `workflows`; por isso a alteração faz-se na UI. Desde 17/11/2026 há
**dois** ficheiros a colar — o da produção (cron horário) e o do relógio de
segurança — e o passo a passo completo, com o que verificar em cada fase, está
em [AGENDADOR.md](AGENDADOR.md). Resumo:

1. Abrir
   <https://github.com/martinhossmadureiraministries/traducao-epignosis/edit/main/.github/workflows/bee-autopiloto.yml>.
2. Seleccionar tudo, apagar e colar o conteúdo de
   [`docs/bee-autopiloto.yml`](bee-autopiloto.yml) (igual a
   `modelos/bee-autopiloto.yml`).
3. **Commit changes**.
4. Criar `.github/workflows/bee-relogio.yml` e colar
   [`docs/bee-relogio.yml`](bee-relogio.yml).
5. **Actions → BEE — produção automática → ⋯ → Disable → ⋯ → Enable**, para o
   GitHub voltar a registar o agendador, e depois **Run workflow** uma vez.
6. Confirmar com `python3 -m unittest tests.test_workflow_sincronizado -v`
   (verde quando os dois ficheiros activos forem iguais aos modelos) e, uma hora
   depois, `python3 scripts/verificar_agendador.py` (deve dizer `a-funcionar`).

O teste `test_modelo_e_workflow_ativo_sao_iguais` falha de propósito — e diz
qual é a linha que difere — enquanto os ficheiros activos não receberem os
modelos.

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

## CI e desenvolvimento

O CI proposto está em `docs/ci.yml` (igual a `modelos/ci.yml`): corre os testes,
valida os JSON, verifica a coerência da documentação e a igualdade
modelo↔workflow. Para ativar, copie-o para `.github/workflows/ci.yml` na UI,
como no workflow de produção. Enquanto o workflow ativo estiver corrompido, o
passo de sincronização falha — é intencional.

```bash
python3 -m unittest discover -s tests -v
python3 -m unittest tests.test_workflow_sincronizado -v
python3 scripts/verificar_dados.py --minimo 18
python3 scripts/verificar_documentacao.py
```

Os testes principais usam só a biblioteca padrão. O `worker/` é experimental e
tem dependências próprias (ver `worker/README.md`).
