> **Documento histórico (arquivado em 17/11/2026).** Conserva o conteúdo
> original para memória; os comandos, números e o ramo `bee-dados` já não
> são os actuais. Use [../OPERACAO.md](../OPERACAO.md) e
> [../ESTADO.md](../ESTADO.md).

# BEE — como está a produção agora (17/11, 04:30)

## Resposta curta

**Está a funcionar.** A execução das 04:29 foi a primeira que correu de ponta a
ponta:

```
Provedores disponíveis: Gemini (principal) + Groq (reserva).
A retomar João 5 a partir do versículo 7/47.
  Guardados João 5:7-12.  ... Guardados João 5:43-46.
- Ação: gerado — João 5 · +40 versículos
- Progresso: 5/1189 capítulos completos, 237/31102 versículos guardados
- Dados: JSON publicados (ramo bee-dados)
```

Repare nas três coisas que antes falhavam e agora acontecem:

1. **Retomou no versículo 7**, não recomeçou o capítulo (os 6 versículos de
   antes foram aproveitados).
2. **Guardou 40 versículos** apesar de o Gemini ter dado `HTTP 503` (a resposta
   veio da Groq, sem intervenção).
3. **Publicou** os JSON no ramo `bee-dados`.

## O que ainda não está perfeito (e ficou corrigido agora)

`Módulos: ainda não há capítulos completos` — a frase que o fez desconfiar.
Era verdade, mas inútil: o programa só compilava o módulo do MyBible quando um
capítulo era **fechado**, e João 5 tem 47 versículos com lotes de 6. Ou seja:
oito execuções (duas horas) sem nada novo no telemóvel, apesar de o trabalho
estar a ser feito.

Agora:

- **compila no fim de cada ciclo** sempre que há versículos novos (falha de
  compilação nunca estraga a produção);
- o resumo diz `Módulos: parciais, 6 capítulos completos e 238 versículos
  (o MyBible só aceita capítulos inteiros)`;
- e diz onde descarregar: `Artifacts → BEE-modulos.zip`;
- quando a próxima execução retoma um lote, indica o versículo (`João 6:6`).

## O que fazer para ver no MyBible (5 minutos)

1. Em *Actions* → **BEE — produção autopiloto** → a última execução →
   **Artifacts** → `BEE-modulos-N.zip` → descarregar.
2. Descompactar e copiar **os dois** ficheiros (`BEE.SQLite3` e
   `BEE.commentaries.SQLite3`) para a pasta do MyBible no Android.
3. No MyBible: *Configurações → Módulos* → ativar os dois.

O que vai ver: **João 1–4 completos** e João 5 a crescer. Note que o MyBible
**só mostra capítulos fechados** — João 5 aparece quando o programa chegar ao
versículo 47, o que deve acontecer na próxima execução (tem 46 de 47).

## O que ainda é frágil, sem rodeios

- **O Gemini está instável** (503 repetidos). A Groq segura o trabalho, mas a
  qualidade do comentário varia com o modelo que responde.
- **Ritmo**: 40 versículos por execução, de 15 em 15 minutos, dentro da janela
  05:00–23:00 em Luanda. Na prática, algumas centenas de versículos por dia —
  semanas ou meses para os 31.102. Não prometo mais do que isto.
- **Revisão humana**: tudo o que está nos JSON é rascunho sinalizado como tal.
  Nada disto substitui a sua leitura crítica, que é o objetivo do projeto.

## Ficheiros

| Ficheiro | Para quê |
|---|---|
| `ENTREGA.md` | Esta página |
| `AUTOMACAO.md` | Planos gratuitos, janela horária, minutos de Actions, problemas comuns |
| `COMECAR_HOJE.md` | Passo a passo |
| `modelos/bee-autopiloto.yml` | O workflow (copiar para `.github/workflows/`) |
