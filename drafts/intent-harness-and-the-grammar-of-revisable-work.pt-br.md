---
title: Intent Harness e a gramática do trabalho revisável
excerpt: Quando mudamos o que queremos de um software, parte do trabalho que já aceitamos precisa ser reavaliada. O Intent Harness é minha tentativa de acompanhar qual parte e por quê.
tags:
- Agentes de IA
- Engenharia de Contexto
- arquitetura de software
- Teoria das Categorias
- Ferramentas
lang: pt-br
translation_of: intent-harness-and-the-grammar-of-revisable-work.md
translated_by: openai/gpt-5.6-sol (high), via opencode
translated_at: '2026-09-06'
---

Suponha que eu peça a um agente um aplicativo de notas para uso pessoal. Uma versão que salve de forma confiável o que escrevo e me permita encontrar esse conteúdo depois talvez atenda a todas as minhas necessidades, até o momento em que eu decida que outras pessoas também devem poder usá-la. Agora preciso saber se elas conseguiriam ler minhas notas, e os testes que ontem me tranquilizavam nada dizem sobre isso.

Comecei o Intent Harness para tornar mudanças como essa visíveis em todo o trabalho que faço com agentes. O aplicativo pode continuar cumprindo perfeitamente sua função original; o que precisa ser reavaliado é minha decisão de considerar o trabalho concluído. À medida que essa decisão serve de base para novas tarefas, as condições vinculadas a ela precisam acompanhá-la. Caso contrário, um agente pode trabalhar com base em uma aprovação sem saber o que ela de fato abrangia.

## Do que depende a aceitação

Uma transcrição pode explicar por que aceitei a primeira versão do aplicativo, sobretudo se alguém teve o cuidado de resumir a decisão. Quando decido compartilhá-lo, porém, preciso encontrar o trabalho que se apoiou nessa aceitação e entender por que dependia dela. Mesmo um resumo cuidadoso nos obriga a reconstruir essas dependências, a menos que tenham sido registradas explicitamente.

O Parametric Intent Graph é o modelo que estou desenvolvendo para esse registro. Ele representa decisões, especificações, tarefas, evidências e entregas como nós versionados. As relações entre esses nós distinguem uma decisão que `constrains` uma especificação de um patch que `implements` uma tarefa ou de um teste que `verifies` uma afirmação. Uma revisão pode então `promote` a evidência: aceitá-la como base para trabalhos posteriores, sob condições declaradas. [[1]](#ref-3)

Essas condições incluem quem tinha autoridade para aprovar o trabalho, quais evidências foram aceitas e um snapshot de dependências que registra as versões a montante das quais a aceitação dependia. O snapshot permite preservar uma decisão histórica válida sem estendê-la silenciosamente a circunstâncias que ninguém revisou. No caso do aplicativo de notas, a evidência de que é possível salvar e recuperar notas continua sendo útil, mas compartilhar o aplicativo exige uma nova evidência de que um usuário não consegue ler as notas de outro.

É por depender de restrições que a tese do produto recorre à analogia com CAD para o trabalho de software com agentes. Alterar uma dimensão em um modelo CAD pode afetar a geometria em outras partes; alterar uma decisão pode afetar trabalhos separados dela por várias tarefas. Quero que o sistema identifique essas dependências e leve a intenção revisada a tudo o que precisa ser reconsiderado. Ao executar novamente uma tarefa, um agente pode escrever um código diferente, mas ainda precisa receber os objetivos, as restrições e os requisitos de evidência que o trabalho deve satisfazer. [[1]](#ref-3), [[2]](#ref-4)

Em um grafo declarado, é possível aplicar regras fixas para verificar quais versões a montante mudaram e acompanhar suas dependências. Decidir se uma mudança de significado exige nova revisão, um ajuste ou uma reexecução completa ainda requer o julgamento de agentes e das pessoas responsáveis pela revisão.

## Que trabalho precisa ser reaberto

Um grafo se torna muito mais exigente quando se espera que suas arestas justifiquem a reabertura de trabalhos já aceitos. Dois documentos podem tratar do mesmo assunto sem que um dependa do outro. Em uma dependência operacional, uma mudança na fonte precisa ser capaz de afetar algo relevante no destino: seu escopo, resultado, autoridade ou as evidências necessárias para aceitá-lo. A semelhança ajuda a encontrar candidatos, mas não estabelece essa relação.

Semantic Dependency Mapping é a pesquisa sobre como identificar, preservar, explicar e corrigir essas relações. Uma aresta inferida precisa de um trecho-fonte, uma passagem que a pessoa responsável pela revisão possa inspecionar para decidir se a dependência existe. Quando uma mudança afeta um trabalho a vários passos de distância, o sistema também precisa explicar o caminho entre os dois. Caso contrário, teremos trocado o esforço de reconstruir uma conversa pelo esforço de interrogar um grafo. [[3]](#ref-5), [[4]](#ref-6)

Algumas dependências pertencem a um conjunto de fontes. Um gate pode exigir tanto um teste aprovado quanto aprovação humana antes que o trabalho prossiga. Dois vínculos genéricos não nos diriam se ambos são necessários ou se basta um deles. O ambiente de experimentação usa hiperarestas para preservar o conjunto de fontes e a condição que ele precisa satisfazer, impedindo que a aprovação desapareça só porque o teste passou.

O erro que mais quero medir é um resultado de *falsa segurança*: um trabalho tratado como seguro para servir de base quando deveria ter sido invalidado ou revisado. Falsos alarmes desperdiçam atenção, um recurso renovável apenas em documentos de planejamento. A falsa segurança permite que alguém entregue ou delegue trabalho com base em uma aceitação cujas condições já não são válidas.

O ambiente de experimentação atual compara o fecho de dependências, seguindo o grafo por todos os nós afetados a jusante, com baselines baseados em vizinhos imediatos, semelhança de palavras-chave e títulos e métodos de recuperação como TF-IDF e BM25. O método de fecho recupera bem as dependências declaradas. Como as respostas esperadas foram obtidas do próprio grafo e dos casos de teste de correção, esse resultado confirma, em grande medida, que o mecanismo segue as relações fornecidas. Não estabelece que essas sejam as relações corretas no mundo real. [[4]](#ref-6)

A avaliação ainda depende de rótulos derivados do grafo, muitas vezes chamados de rótulos *silver*, e de consenso sintético de modelos. Avaliações humanas independentes continuam sendo necessárias para estabelecer quais mudanças importam, o que elas afetam e quais evidências ou aprovações exigem. Os resultados da extração por modelos externos também são diagnósticos, não um novo baseline independente. Em operação, um gate que não consiga sustentar sua decisão com texto-fonte ou um caminho de dependência deve deixar o trabalho aguardando revisão, por mais persuasiva que soe a explicação do modelo.

## O que a teoria das categorias exige do grafo

O Intent Harness surgiu antes de eu conhecer a teoria das categorias como área. Eu tentava preservar a intenção humana ao longo de revisões e sessões com agentes; encontrar essa matemática me deu uma maneira mais exata de examinar o que eu queria dizer com “preservar”.

Uma categoria consiste em objetos e setas entre eles, chamadas morfismos, além de setas de identidade e regras para compor setas compatíveis. A composição é associativa, e compor uma seta com uma identidade não a altera. Levar essa linguagem a sério exige especificar essas operações e demonstrar que as leis se aplicam ao modelo proposto. A [introdução de Jean-Pierre Marquis](https://plato.stanford.edu/entries/category-theory/) apresenta a formulação formal. [[5]](#ref-2)

Para o Intent Harness, a composição traz de imediato uma questão de projeto para o centro da discussão. Se uma decisão restringe uma especificação, e essa especificação restringe uma tarefa, que obrigação chega à tarefa por meio dessas duas etapas? Seguir o caminho só é útil se preservarmos ao longo dele a restrição relevante. Se dois caminhos devem justificar a mesma aceitação, também precisamos estabelecer que eles sustentam afirmações compatíveis, em vez de presumir concordância apenas porque terminam no mesmo registro.

Funtores, mapeamentos entre categorias que preservam identidades e composição, sugerem um critério semelhante para traduzir o trabalho de uma forma para outra. Notas de pesquisa se transformam em planos; planos se transformam em pacotes de tarefas que um agente executa. Um pacote pode reproduzir fielmente a redação de um plano e, ainda assim, omitir a exigência de aprovação humana. As frases sobreviveram, mas o agente recebeu instruções diferentes sobre o que lhe cabe decidir. Chamar essa tradução de preservadora de estrutura exigiria uma descrição precisa dessas obrigações e evidências de que o mapeamento as preserva.

A divisão e a fusão de tarefas expõem um problema relacionado. Manter o nome de uma tarefa depois de reescrevê-la pouco nos diz sobre quais obrigações sobreviveram. O ambiente de experimentação inclui pequenos casos de teste para essa questão de identidade semântica; uma formulação geral da identidade entre ramificações e revisões continua inacabada.

## Quando a gramática muda

No exemplo das notas, acrescentamos um requisito a um modelo que já sabe representar requisitos. Uma revisão mais difícil altera o próprio modelo. Podemos descobrir que alternativas rejeitadas merecem registros próprios ou que decisões de gosto exigem um limite de autoridade que nosso esquema não consegue expressar. Acrescentar os campos é simples quando comparado a decidir o que os registros existentes significam sob as novas regras.

Uma aceitação antiga pode continuar válida, passar a valer para uma afirmação mais restrita ou precisar ser reaberta. Algumas obrigações talvez só se tornem visíveis porque o esquema revisado nos oferece uma forma de descrevê-las. Uma migração bem-sucedida do banco de dados mostra que os registros cabem na nova estrutura; a validade do trabalho ainda precisa ser estabelecida.

Fiona Wang e Markus Buehler examinam um problema relacionado em seu [preprint sobre sistemas de descoberta autorrevisáveis](https://arxiv.org/abs/2606.01444v1). O arcabouço distingue o trabalho realizado dentro de um regime de representação estabelecido da descoberta que altera os tipos, as operações ou os verificadores disponíveis. Os autores usam uma construção chamada extensão de Kan à esquerda para transportar estados de artefatos a um regime modificado e, em seguida, comparam o que esse transporte fornece com o estado alcançado após a transição. O resíduo identifica o conteúdo que o transporte, por si só, não forneceu. [[6]](#ref-1)

A analogia me parece útil para o Intent Harness: mudar as regras usadas para descrever o trabalho não realiza, por si só, o trabalho que essas novas regras passam a exigir. O preprint oferece um tratamento formal em outro domínio. Ainda precisa ser demonstrado se um tratamento comparável consegue preservar as obrigações do meu trabalho de software.

As questões filosóficas já estão presentes nessas decisões de implementação. Tratar uma tarefa reescrita como a mesma tarefa é fazer um julgamento sobre identidade; aceitar um teste como fundamento para uma entrega é fazer um julgamento sobre evidência. Permitir que um agente aprove uma mudança no comportamento do produto é lhe atribuir autoridade. O esquema e o fluxo de trabalho incorporarão respostas a essas questões, quer as examinemos, quer deixemos que a implementação as forneça.

É por isso que espero que áreas intensivas em raciocínio precisem de mais filosofia à medida que automatizem uma parcela maior do trabalho. Sistemas que inferem, revisam e agem mais rápido do que conseguimos inspecionar cada etapa tornam nossos pressupostos mais consequentes. Deixá-los implícitos abre espaço para que padrões predefinidos e respostas fluentes decidam o que conta como evidência ou quem pode aprovar um resultado. É outra forma de [terceirizar o pensamento](../posts/dont-outsource-the-thinking.pt-br.md), desta vez por meio do projeto das ferramentas.

O Intent Harness é minha tentativa de tornar esses compromissos inspecionáveis no momento em que importam. Quando eu decidir compartilhar o aplicativo de notas, quero ver o que a aprovação anterior abrangia, qual trabalho precisa ser reavaliado e quem pode aceitar o resultado. Os testes originais podem continuar passando enquanto tudo isso permanece sem resposta.

---

**Fontes:**

<a id="ref-3"></a>[1] `intent-harness.idea`, especialmente a definição provisória, o Parametric Intent Graph, os snapshots de dependências, o protocolo de invalidação, os gates e as linhas de pesquisa.

<a id="ref-4"></a>[2] `intent-harness.product-thesis.md`, especialmente a afirmação de que o histórico da conversa é a unidade de estado errada para o trabalho de software com IA e a analogia de escopo restrito com CAD.

<a id="ref-5"></a>[3] `artifacts/research/RESEARCH-0002-semantic-dependency-mapping.md`, especialmente a atribuição de trechos-fonte, o mapeamento de dependências operacionais, o risco de falsa segurança, a autoridade do grafo e os não objetivos.

<a id="ref-6"></a>[4] `artifacts/research/semantic_dependency_mapping_workbench/README.md`, `thesis/thesis_draft.md`, `thesis/claims_evidence_matrix.md` e as especificações e os resultados relacionados em `artifacts/research/semantic_dependency_mapping_workbench/`, especialmente o formalismo do grafo, a semântica de nós e arestas, os snapshots, os gates, a preservação semântica, a identidade semântica, as hiperarestas, os requisitos de anotação, os relatórios de experimentos, os resultados dos baselines e as limitações atuais.

<a id="ref-2"></a>[5] Jean-Pierre Marquis, *Category Theory*, Stanford Encyclopedia of Philosophy. [plato.stanford.edu/entries/category-theory](https://plato.stanford.edu/entries/category-theory/)

<a id="ref-1"></a>[6] Fiona Y. Wang and Markus J. Buehler, *Self-Revising Discovery Systems for Science: A Categorical Framework for Agentic Artificial Intelligence*, arXiv:2606.01444v1, 2026. [Version 1, May 31, 2026](https://arxiv.org/abs/2606.01444v1).
