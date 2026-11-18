# Tito — roteiro para receber e rever a próxima carta da BEE

**Estado:** [Tito já está disponível para leitura](../edicoes/piloto/TITO.md) como prévia da nova BEE. O fluxo agendado legado não foi alterado.

## Como receber a prévia

1. O piloto inclui **Tito completo**, com três capítulos e 46 versículos. A entrega deve trazer uma versão de leitura (Markdown), um JSON integral e um pacote com os módulos de texto e comentários MyBible (`.SQLite3`). A carta vai identificada como prévia editorial, não como publicação definitiva.
2. Abrir primeiro o Markdown: permite ler sem instalar nada e mantém as notas fora da primeira leitura. Para ler no MyBible, extrair os dois módulos do ZIP para a pasta de módulos usada pelo aplicativo; guardar uma cópia dos módulos BEE anteriores se os ficheiros tiverem os mesmos nomes.
3. Verificar se o pacote recebido é o da **nova BEE** e se Tito 1–3 aparece inteiro. Se a entrega estiver no repositório, mas sem ZIP, a compilação é offline: `python gerar_bee.py --compilar --dados edicoes/piloto/dados --saida entregas/piloto`. Esse comando **não traduz Tito**; só compila o que já existe.

## Como ler com cuidado

| Leitura | O que observar |
|---|---|
| **Tito 1 — liderança e ensino** | Ouve a saudação e a passagem de «presbíteros» (1:5) para «supervisor/bispo» (1:7). A redação preserva a ligação do argumento sem impor uma estrutura eclesiástica? Em 1:12–13, consegues distinguir a citação das palavras que Paulo dirige a Tito? |
| **Tito 2 — a graça que nos ensina** | Lê 2:11–14 de uma vez. A relação entre a graça que se manifesta, a vida que ela ensina e a esperança que aguardamos fica clara? Em 2:13, confere se a nota explica a ligação entre «Deus» e «Salvador» sem fazer a tradução dizer mais do que a construção suporta. |
| **Tito 3 — misericórdia e boas obras** | Lê 3:3–8 em conjunto. A salvação não vem das obras que praticámos (3:5), mas Paulo pede dedicação às boas obras (3:8). Em 3:5, vê se a nota distingue a imagem do lavar, a regeneração e a interpretação batismal. |

Na primeira leitura, marca apenas onde **perdeste o fio** ou onde uma frase **te pareceu dizer algo diferente**. Na segunda, vai às notas e vê se dão uma razão verificável. Para devolver observações, basta algo como `Tito 2:13 — li a frase como duas pessoas; a nota não esclareceu a minha dúvida`. Não é preciso rever grego nem aprovar versículo a versículo.

A preparação do fluxo isolado e a prova de retoma/agendamento são tarefas do projeto. Não é necessário deixar o computador ligado, partilhar credenciais ou configurar o GitHub para ler a carta quando a prévia estiver disponível.
