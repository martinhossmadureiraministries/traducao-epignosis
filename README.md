# Bíblia de Estudo Epignósis (BEE) — projeto para MyBible

Projeto de tradução e comentários para os 66 livros e 1.189 capítulos do cânone escolhido, com ferramentas **de linha de comando** e compilação para `BEE.SQLite3` e `BEE.commentaries.SQLite3`.

## Produção automática com ferramentas gratuitas

> **Comece por [AUTOMACAO.md](AUTOMACAO.md).** É o guia passo a passo: chave gratuita, primeiro teste, ritmo diário, funcionamento com o computador desligado e cópia para o MyBible.

O projeto passou a ter um **autopiloto** que produz sozinho, em blocos pequenos, com provedores de IA que têm plano gratuito (Google Gemini, Groq, Cerebras e OpenRouter). Ele grava cada lote, recompila os módulos quando um capítulo fica completo e registra tudo num diário legível:

```bash
export GEMINI_API_KEY="a-sua-chave-gratuita"   # nunca no código nem no Git
python autopiloto.py --doctor                  # configuração e próximo capítulo, sem gastar quota
python autopiloto.py --uma-vez                 # primeiro teste real (6 versículos)
python autopiloto.py --horas 6 --fuso Africa/Luanda
```

Para continuar **com o computador desligado**, o modelo de workflow [`modelos/bee-autopiloto.yml`](modelos/bee-autopiloto.yml) (copie-o para `.github/workflows/`) corre `nuvem.py` numa GitHub Action a cada 15 minutos, publica os JSON no ramo `bee-dados` e deixa o `BEE-modulos.zip` como artefato descarregável. O programa não depende do GitHub: `autopiloto.py` faz o mesmo localmente ou num `cron`.

Limites honestos: os planos gratuitos não são ilimitados. Com quota gratuita, 300–800 versículos por dia é realista; a Bíblia inteira leva semanas a meses, não dias, e continua a exigir revisão humana. Os textos automáticos entram marcados como rascunho, e o prompt automático proíbe atribuir consultas a BDB/Thayer/Nestle-Aland que não aconteceram. Detalhes, tabelas de quota e estimativas em [AUTOMACAO.md](AUTOMACAO.md).

## Fluxo colaborativo atual

A produção colaborativa é feita entre o responsável e o assistente, sem chaves, e é complementada pelo autopiloto descrito acima (que usa APIs gratuitas). A ordem inicial escolhida é Salmos 23 e depois Filemom; veja [PLANO_BEE.md](PLANO_BEE.md). O [Salmo 23](rascunhos/230_Salmos_23.json) e Filemom 1:1–3 foram aprovados editorialmente pelo responsável, mas ainda requerem revisão especializada. O responsável autorizou prosseguir sem solicitar aprovação a cada bloco e reverá os textos mais tarde no aplicativo; isso não significa que o material posterior já esteja aprovado. Salmos 23 permanece fora dos módulos por ser uma amostra isolada.

[Filemom completo](livros_json/640_Filemom.json) contém os 25 versículos e comentários: a redação e os comentários originais de 1:1–3 foram aprovados editorialmente, mas os colchetes e o adendo textual novos em 1:2 aguardam revisão; 1:4–25 permanecem provisórios. Todo o livro aguarda revisão especializada. [João 1–4](livros_json/500_Joao.json) contém 166 versículos e comentários provisórios, também sem revisão especializada. O progresso é **5/1.189 capítulos estruturalmente completos**, não revisados para publicação.

Trechos com variantes relevantes são marcados como `[[...]]`. Conforme o caso, eles podem ser a leitura do SBLGNT **ou** um suplemento explicitamente identificado de Scrivener; a nota de crítica textual informa qual é o caso e relata a evidência consultada. Os colchetes, sozinhos, não significam que o trecho seja necessariamente um acréscimo tardio. Veja a convenção e os limites em [PLANO_BEE.md](PLANO_BEE.md#convenção-de-variantes-textuais). O validador confere apenas pares não vazios e não aninhados por versículo, não a exatidão das notas nem se todas as variantes relevantes foram marcadas.

A [prévia parcial para MyBible](entregas/BEE-previa.zip) reúne os dois módulos da mesma compilação; não é uma edição final. `python gerar_bee.py --status` conta capítulos, não aprovações. `--compilar` opera offline, valida intervalos dos estados informados e os inclui nos metadados, mas não comprova as revisões nem exige aprovação editorial. Referências, licenças e detalhes permanecem nos JSON e nos metadados; a visualização dessas informações depende do leitor. **Para produzir texto novo, use `autopiloto.py`** (ver [AUTOMACAO.md](AUTOMACAO.md)); `--livro` e `--todos` do `gerar_bee.py` continuam a funcionar, mas são o percurso antigo de um livro inteiro por chamada, sem janela diária, rodízio de provedores nem estado. Amostras isoladas ou capítulos incompletos não são compiláveis.

> **Antes de publicar:** rascunhos produzidos com IA podem conter erros de tradução, Strong, transliteração, atribuição a léxicos ou crítica textual. A validação automática verifica a estrutura, **não** a fidelidade teológica ou filológica. Faça revisão humana especializada e confira direitos e licenças. O projeto não é um produto oficial ou aprovado pelo MyBible.

## Gerador direto (linha de comando)

As secções 1 a 3 abaixo documentam o gerador de linha de comando, ainda útil para gerar um livro inteiro de uma vez. Elas **não são instruções para o fluxo colaborativo atual** e envolvem chamadas pagas ou sujeitas a quota. As secções posteriores sobre JSON e compilação descrevem a implementação existente, ainda sujeita à adaptação mencionada acima.

## 1. Requisitos e preparação

- Python **3.10 ou superior** com `sqlite3` (incluído na instalação habitual do Python).
- Internet para descarregar as fontes e aceder à API. A compilação dos JSON existentes funciona **offline**, sem chave.
- Uma chave de API do provedor escolhido. O padrão passou a ser o **Google Gemini** (plano gratuito); também são aceites Groq, Cerebras, OpenRouter e OpenAI. A variável é `GEMINI_API_KEY`, `GROQ_API_KEY`, `CEREBRAS_API_KEY`, `OPENROUTER_API_KEY` ou `OPENAI_API_KEY`; `API_KEY` continua a funcionar como alternativa genérica.
- Não são necessários pacotes externos: as APIs são chamadas por HTTPS com a biblioteca padrão. `requirements.txt` existe para compatibilidade com o fluxo habitual de instalação.

No macOS/Linux, dentro da pasta do projeto:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# Introduza a chave sem a mostrar no terminal nem a gravar no histórico:
export GEMINI_API_KEY="$(python -c 'import getpass; print(getpass.getpass("GEMINI_API_KEY: "))')"
```

No Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$chaveSegura = Read-Host 'GEMINI_API_KEY' -AsSecureString
$env:GEMINI_API_KEY = [System.Net.NetworkCredential]::new('', $chaveSegura).Password
Remove-Variable chaveSegura
```

A variável vale apenas para a sessão atual; não coloque a chave no código, nos JSON nem no GitHub. O `.gitignore` exclui `.env`, cache e módulos binários, mas não substitui o cuidado com segredos.

## 2. Começar com pouco e retomar

```bash
# Consulte todos os book_number e o número de capítulos.
python gerar_bee.py --listar-livros

# Primeiro teste: apenas o próximo capítulo ainda não concluído de João (500).
python gerar_bee.py --livro 500 --max-capitulos 1

# Ver o progresso. Para continuar, use o mesmo comando ou gere o resto do livro:
python gerar_bee.py --status
python gerar_bee.py --livro 500

# Gere apenas outro livro, por exemplo Mateus (470):
python gerar_bee.py --livro 470

# Depois de rever/editar os JSON, atualize ambos os módulos, sem API_KEY:
python gerar_bee.py --compilar
```

Por padrão usa o **Gemini**, modelo gratuito `gemini-3.5-flash-lite`:

```bash
python gerar_bee.py --livro 500 --max-capitulos 1
# Outro provedor gratuito com a respetiva variável definida:
python gerar_bee.py --livro 500 --provedor groq --modelo llama-3.3-70b-versatile --max-capitulos 1
```

Para processar toda a Bíblia, de forma sequencial:

```bash
python gerar_bee.py --todos
```

**Atenção aos custos:** a geração integral exige milhares de chamadas em lotes, muitas entradas e saídas de tokens e pode levar muito tempo. `--max-capitulos` limita o número de **novos capítulos completos**, não estabelece um teto monetário nem impede que um capítulo precise de várias chamadas ou tentativas. Consulte os preços e a utilização do seu provedor e defina ali um limite de faturação. Em modelos de raciocínio, o limite de saída também pode incluir tokens internos. Comece por um capítulo, reveja a qualidade e estime o custo antes de executar `--todos`.

A cada lote válido, o progresso é gravado atomicamente no JSON do livro. Se parar com `Ctrl+C` ou houver falha, rode novamente o mesmo comando: capítulos completos não são enviados outra vez e um capítulo parcialmente gerado continua no versículo seguinte. Os lotes recebidos antes da interrupção são preservados; uma chamada já faturada mas ainda não guardada poderá precisar de ser repetida. Travas impedem execuções concorrentes na mesma pasta de dados ou compilações simultâneas na mesma pasta de saída; são libertadas quando o processo termina.

A geração compila automaticamente ao terminar. Para guardar apenas JSON, acrescente `--sem-compilar`. Uma compilação com menos de 1.189 capítulos é explicitamente identificada como **PARCIAL**; apenas capítulos completos entram nos módulos. Nenhum conteúdo é inventado para livros ainda não gerados.

## 3. Opções úteis

| Opção | Exemplo / efeito |
|---|---|
| `--livro N` | Livro pelo número MyBible; `--livro 500` é João. |
| `--todos` | Todos os 66 livros, em ordem. |
| `--compilar` | Lê os JSON existentes e recompila os dois módulos, sem chave ou rede. |
| `--listar-livros` / `--status` | Catálogo completo / progresso local. |
| `--provedor NOME` | `gemini` (padrão), `groq`, `cerebras`, `openrouter` ou `openai`. |
| `--modelo NOME` | Padrões gratuitos por provedor; modelos disponíveis podem variar por conta. |
| `--max-capitulos N` | Para após N novos capítulos completos nesta execução. |
| `--versos-por-pedido N` | Máximo por chamada; padrão 8. Respostas inválidas ou truncadas são divididas em lotes menores. |
| `--max-tokens N` | Limite de tokens de saída por chamada; padrão 8192, mínimo 256. |
| `--pausa SEGUNDOS` | Pausa mínima **após** cada requisição; padrão 1. `0` desativa a pausa. |
| `--tentativas N` | Tentativas em falhas transitórias ou resposta inválida; padrão 4. |
| `--timeout SEGUNDOS` | Tempo-limite por chamada; padrão 120. |
| `--dados PASTA` | Pasta de JSON/checkpoints; padrão `livros_json`. |
| `--saida PASTA` | Pasta dos dois SQLite; padrão diretório atual. |
| `--cache-fontes PASTA` | Cache dos originais descarregados; padrão `.bee-cache`. |
| `--sem-compilar` | Não compila depois de gerar. |

Para o resumo completo: `python gerar_bee.py --help`. Erros de rede, HTTP 429 e 5xx têm novas tentativas com espera crescente, respeitando `Retry-After` quando enviado; erros permanentes de chave/modelo são informados sem imprimir a chave ou o corpo da resposta. Se as tentativas forem esgotadas, corrija o problema e retome. **Uma resposta inválida, um bloqueio ou uma chamada que exceda o tempo também pode ser cobrada pelo provedor.**

## 4. Revisar os ficheiros JSON

Cada livro com progresso fica num ficheiro UTF-8, por exemplo `livros_json/010_Genesis.json`, `500_Joao.json` ou `730_Apocalipse.json`. `chapters` contém apenas capítulos estruturalmente concluídos; `in_progress` guarda trechos de um capítulo ainda incompleto. `sources` identifica as revisões das fontes e do alinhamento. No fluxo colaborativo, `history` registra eventos de redação e revisão; no legado, registra provedor, modelo, lote e hora — nunca a chave. Se o alinhamento ou as fontes mudarem, o gerador não mistura versões automaticamente num checkpoint que já as identifique: faça cópia e reveja os textos antes de tomar uma decisão.

Um **excerto ilustrativo** de um ficheiro (o capítulo real deve conservar todos os versículos, não apenas o mostrado):

```json
{
  "format_version": 1,
  "book_number": 500,
  "book_name": "João",
  "chapter_count": 21,
  "chapters": {
    "1": [
      {"verse": 1, "text": "Texto revisto", "commentary": "<p>Comentário revisto.</p>"}
    ]
  },
  "in_progress": {},
  "history": []
}
```

Edite `text` e `commentary` no ficheiro real, preserve todos os números e mantenha JSON válido. No texto bíblico é permitido `<i>...</i>`; nos comentários são permitidas tags simples sem atributos: `p`, `br`, `b`, `strong`, `i`, `em`, `ul`, `ol`, `li`, `sup` e `sub`. Os colchetes duplos de variantes devem ser equilibrados, não vazios e não aninhados dentro de cada versículo; uma passagem longa é marcada versículo a versículo. O compilador rejeita HTML inseguro, marcadores malformados, chaves duplicadas, capítulos fora do intervalo e versículos ausentes, repetidos ou fora de ordem — inclusive a falta do último versículo. Também rejeita lacunas entre capítulos de um mesmo livro, pois MyBible espera capítulos consecutivos desde 1. Não substitui os módulos anteriores quando a validação falha.

Quando informada, a seção `review` registra `editorial_blocks` como lista de intervalos e `specialist` como intervalo ou lista de intervalos. Cada intervalo tem `chapter`, `verse_from`, `verse_to` e `status`; dentro da mesma categoria não pode haver sobreposição. Os estados editorial e especializado são independentes: uma aprovação editorial não comprova revisão especializada. Nos dois SQLite, `bee_review_by_book` contém os estados declarados apenas para capítulos compilados; versículos sem estado declarado aparecem como **não informados**, nunca como aprovados. O compilador verifica a forma e os limites, não a veracidade das declarações.

Para regenerar um capítulo, faça primeiro uma cópia do JSON, remova a respetiva entrada de `chapters` e, se existir, de `in_progress`, e execute novamente `--livro N`. Isso gera novas chamadas pagas; se havia capítulos posteriores, recompilar antes de preencher a lacuna será recusado. A edição manual seguida de `--compilar` não usa IA. Os JSON de `livros_json` **não** são ignorados pelo Git e podem ser revistos e versionados no GitHub; os SQLite e o cache são regeneráveis e ficam ignorados por padrão.

## 5. Fontes, versificação e limitações

No **gerador legado**, na primeira geração o programa descarrega versões fixas do GitHub para `.bee-cache`, confirma SHA-256 e reutiliza o cache. Aproximadamente 20 MB são necessários para o pacote do AT e 2 MB para os do NT. Nesse fluxo legado, são enviados à API os trechos e o contexto necessários para cada lote:

- **AT:** [Open Scriptures Hebrew Bible](https://github.com/openscriptures/morphhb), baseado no Westminster Leningrad Codex, com lemas e o `VerseMap.xml` da própria fonte. O texto WLC é de domínio público; lemas e morfologia OSHB são [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Atribuição exigida: “Original work of the Open Scriptures Hebrew Bible available at https://github.com/openscriptures/morphhb”.
- **NT:** texto e aparato [SBL Greek New Testament](https://github.com/Faithlife/SBLGNT), edição 1.2, [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Atribuição: “Scripture quotations marked SBLGNT are from the SBL Greek New Testament. Copyright © 2010 Society of Biblical Literature and Logos Bible Software.”
- **Comparação e suplemento:** [Textus Receptus de Scrivener (1894)](https://github.com/byztxt/greektext-scrivener), digitalizado por Maurice A. Robinson e declarado de domínio público pelo fornecedor. A transcrição ASCII é convertida mecanicamente para grego Unicode, **sem acentos, espíritos ou pontuação**; essa ausência não é uma variante textual. O TR é fornecido para comparação e usado como única fonte nas posições tradicionais sem texto correspondente no SBLGNT; o comentário recebe uma nota explícita. Isso inclui Romanos 16:25–27, ausentes no ficheiro SBLGNT fixado. As atribuições, as adaptações e o aviso de revisão também constam nos módulos.

As revisões exatas são OSHB `db6c5c9b46b8f39346f10915ddb1a70dcd429901`, SBLGNT `d7f35adca9ec410e1d1499c63b4dd989d76c8d4d` e Scrivener `6049a43b135ed870f843b83eb6a04764fc796678`; endereços e hashes completos estão em `bee/fontes.py`.

O inventário usa **31.102 posições da numeração tradicional KJV**; outras edições têm divisões e contagens diferentes. As contagens, não o texto KJV, foram conferidas com [este inventário público](https://github.com/renniemaharaj/kjv-bible). Há adaptações explícitas entre WLC e KJV e entre os limites das edições gregas, por exemplo em Lucas 6:17–18, Hebreus 1:1–2, Atos 19:40–41, 2 Coríntios 13:12–14, 3 João 1:14 e Apocalipse 13:1. Essas adaptações são heurísticas e **não garantem alinhamento filológico perfeito**: referências repartidas e diferenças de ordem recebem avisos nos comentários e requerem revisão. Os títulos de Salmos que são versículos separados no WLC não são incorporados ao versículo 1. Correspondências WLC parciais recebem aviso: o mapa original nem sempre fornece os limites exatos das partes.

O SBLGNT coloca Marcos 16:9–20 e João 7:53–8:11 entre colchetes críticos; no gerador legado, todas essas posições recebem aviso para investigação, mesmo quando os sinais de abertura e fecho aparecem apenas nos extremos. Isso **não** gera automaticamente a nova marcação editorial `[[...]]`: essas passagens ainda não foram produzidas no fluxo colaborativo. Em 1 João 5:7–8 a expansão, caso seja apresentada, será distinguida do texto comum e identificada como suplemento.

**Neemias 7:68:** não há texto correspondente no WLC usado para essa posição da numeração tradicional. O programa grava um marcador, não uma tradução inventada; antes da publicação, substitua-o por texto e comentário revistos a partir de uma fonte suplementar autorizada. O compilador avisa e regista a quantidade de marcadores em `bee_source_gaps`.

No gerador legado, o Nestle-Aland e os léxicos BDB/Thayer **não são fornecidos** ao modelo. O prompt pede que a IA não alegue consulta direta nem invente informações não verificadas, mas isto não garante que obedeça. Na colaboração atual, entradas da [Open Scriptures Hebrew Lexicon](https://github.com/openscriptures/HebrewLexicon) foram consultadas manualmente para Salmos 23: a transcrição resumida do BDB está em desenvolvimento, e os arquivos do léxico são CC BY 4.0, com atribuição ao Open Scriptures Hebrew Bible Project. A revisão exata, as entradas usadas e a atribuição constam do rascunho; o léxico não foi integrado à CLI. O aparato SBLGNT compara edições e não substitui a consulta dos próprios manuscritos. Reveja todos os códigos Strong, definições, variantes, fontes de passagens e obrigações de atribuição antes de distribuir. A numeração completa ou `bee_complete=true` indica apenas cobertura estrutural, não revisão ou ausência de marcadores.

## 6. Instalar no MyBible

1. Depois de gerar e rever, execute `python gerar_bee.py --compilar` e copie **os dois ficheiros da mesma compilação** para o dispositivo.
2. No Android, coloque-os no diretório de dados indicado pelo MyBible, normalmente `/Android/data/ua.mybible/files/MyBible`; algumas instalações usam `/MyBible`. O acesso varia conforme a versão do Android e o gestor de ficheiros. Consulte as [instruções do MyBible](https://mybible.zone/doers/).
3. Reinicie o aplicativo, selecione a Bíblia BEE e ative/selecione o módulo de comentários. Se atualizar a tradução, substitua os dois ficheiros juntos.

As tabelas `books`/`books_all` e os índices necessários são criados além das tabelas pedidas. `commentaries` segue as colunas MyBible, incluindo `marker`, e também contém `book_number_to` para compatibilidade com o formato solicitado. Cada comentário é associado ao mesmo livro, capítulo e versículo do seu texto. Os dois módulos incluem o mesmo `bee_build_id`. A substituição é atômica **por ficheiro**, com tentativa de reversão em caso de erro; numa interrupção abrupta entre as duas substituições, volte a executar `--compilar` para criar um par consistente.

A prévia real de Filemom 1 e João 1–4 foi aberta programaticamente com o leitor independente [Bible for Sermon Preparation](https://github.com/Saymon-J/Bible-for-Sermon-Preparation/blob/7ec3d446b9b921ff6783546d5ee47ad57cbea891/app/module.py): os 191 versículos e os 191 comentários foram recuperados. Isso verifica a leitura das tabelas, **não** a instalação ou a apresentação visual no aplicativo MyBible, que ainda precisam ser testadas no dispositivo. Uma amostra fictícia anterior da Bíblia também foi aberta com [mybible-cli-python](https://github.com/kosivantsov/mybible-cli-python). Leitores de terceiros podem impor restrições próprias: por exemplo, `@whiteand/mybible` 0.0.8 rejeitou a amostra fictícia por exigir metadados adicionais e restringir o idioma, apesar de `pt` ser o código solicitado.

## 7. Testes

Os testes normais (67) não usam credenciais nem rede; simulam as respostas das APIs, interrupção, retomada, validação, compilação, o autopiloto, o rodízio de provedores e o orçamento diário. Não foram feitas chamadas reais às APIs; disponibilidade, preços e permissões do modelo devem ser verificados na sua conta:

```bash
python -m unittest discover -s tests -v
```

Para auditar também os 66 livros das **fontes reais** fixadas (descarrega os ficheiros se não estiverem no cache, mas não usa a API de IA):

```bash
BEE_TEST_FONTES_REAIS=1 python -m unittest discover -s tests -p 'test_fontes_reais.py' -v
```

No PowerShell, defina `$env:BEE_TEST_FONTES_REAIS = '1'` antes do comando. Esses testes não conferem o conteúdo gerado pela IA nem substituem a revisão humana.

## Catálogo MyBible

Os números abaixo não são ordinais simples: as lacunas são reservadas a outros livros no padrão MyBible. A lista e as contagens estão também em `bee/catalogo.py` e `bee/versos_por_capitulo.json`.

| Número | Livro | Capítulos | Número | Livro | Capítulos |
|---:|---|---:|---:|---|---:|
| 010 | Gênesis | 50 | 410 | Naum | 3 |
| 020 | Êxodo | 40 | 420 | Habacuque | 3 |
| 030 | Levítico | 27 | 430 | Sofonias | 3 |
| 040 | Números | 36 | 440 | Ageu | 2 |
| 050 | Deuteronômio | 34 | 450 | Zacarias | 14 |
| 060 | Josué | 24 | 460 | Malaquias | 4 |
| 070 | Juízes | 21 | 470 | Mateus | 28 |
| 080 | Rute | 4 | 480 | Marcos | 16 |
| 090 | 1 Samuel | 31 | 490 | Lucas | 24 |
| 100 | 2 Samuel | 24 | 500 | João | 21 |
| 110 | 1 Reis | 22 | 510 | Atos | 28 |
| 120 | 2 Reis | 25 | 520 | Romanos | 16 |
| 130 | 1 Crônicas | 29 | 530 | 1 Coríntios | 16 |
| 140 | 2 Crônicas | 36 | 540 | 2 Coríntios | 13 |
| 150 | Esdras | 10 | 550 | Gálatas | 6 |
| 160 | Neemias | 13 | 560 | Efésios | 6 |
| 190 | Ester | 10 | 570 | Filipenses | 4 |
| 220 | Jó | 42 | 580 | Colossenses | 4 |
| 230 | Salmos | 150 | 590 | 1 Tessalonicenses | 5 |
| 240 | Provérbios | 31 | 600 | 2 Tessalonicenses | 3 |
| 250 | Eclesiastes | 12 | 610 | 1 Timóteo | 6 |
| 260 | Cânticos | 8 | 620 | 2 Timóteo | 4 |
| 290 | Isaías | 66 | 630 | Tito | 3 |
| 300 | Jeremias | 52 | 640 | Filemom | 1 |
| 310 | Lamentações | 5 | 650 | Hebreus | 13 |
| 330 | Ezequiel | 48 | 660 | Tiago | 5 |
| 340 | Daniel | 12 | 670 | 1 Pedro | 5 |
| 350 | Oseias | 14 | 680 | 2 Pedro | 3 |
| 360 | Joel | 3 | 690 | 1 João | 5 |
| 370 | Amós | 9 | 700 | 2 João | 1 |
| 380 | Obadias | 1 | 710 | 3 João | 1 |
| 390 | Jonas | 4 | 720 | Judas | 1 |
| 400 | Miqueias | 7 | 730 | Apocalipse | 22 |
