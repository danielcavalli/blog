---
title: Agentes de IA e a ilusão de continuidade
excerpt: 'A continuidade em agentes de IA não vem da memória do modelo, mas da engenharia de contexto ao redor dele: o que você preserva, descarta e transforma em artefato.'
tags:
- IA
- agentes de IA
- engenharia de contexto
- fluxo de trabalho
lang: pt-br
translation_of: ai-agents-and-the-illusion-of-continuity.md
source_digest: eef52dcd3a79875436f83b7c09a024834153a5c0548d148b388820b2a95323ee
translated_by: openai/gpt-5.5, via opencode
---

Retome uma sessão de agente depois de algumas horas e ela continua exatamente de onde você parou. Lembra uma decisão anterior, segue uma linha de trabalho, usa as mesmas ferramentas. Como se nenhum tempo tivesse passado.

Isso não é memória. Entre chamadas de API, o modelo não leva nada adiante por conta própria. O que persiste é tudo ao redor dele: mensagens armazenadas, saídas de ferramentas, resumos, notas, qualquer coisa que o harness reintroduza na próxima requisição [[1]](#ref-1)[[2]](#ref-2). O modelo não tem estado. A continuidade que você percebe é construída a partir de contexto que alguém, ou alguma coisa, escolheu colocar de volta.

Quando você aceita que continuidade é produto de engenharia de contexto, e não do modelo, as perguntas interessantes mudam. A questão deixa de ser se o modelo "entende" e passa a ser o que você entrega a ele, quando e com que limpeza você separa uma tarefa da próxima.

## Mais Contexto Não É Uma Estratégia

O primeiro impulso da maioria das pessoas é preservar mais histórico. Um impulso razoável. Qualquer humano estudando um assunto tentaria absorver o máximo de informação possível para chegar a uma conclusão, então parece lógico que dar mais informação a um agente produziria um raciocínio melhor. A partir de certo ponto, porém, acontece o contrário.

Informação relevante fica mais difícil de recuperar quando se desloca para o meio de um prompt longo [[4]](#ref-4), modelos se ancoram em contexto antigo ou gerado por eles mesmos [[6]](#ref-6), e entradas mais longas podem prejudicar o desempenho mesmo quando a recuperação é tecnicamente perfeita [[5]](#ref-5). As janelas de contexto continuam crescendo, mas o modelo não fica melhor em adivinhar quais partes são relevantes para o que você de fato quer. Quanto mais você entrega, mais possibilidades ele tem para escolher, e ele vai escolher a que parecer ótima do ponto em que ele está.

Mais importante do que quanto contexto cabe é qual contexto você decide manter ativo, e o que você transforma em artefato ou deixa para trás de vez [[1]](#ref-1)[[2]](#ref-2)[[3]](#ref-3). Recursos do provedor ajudam com custo e latência, mas o problema da seleção ainda cai no seu colo.

## O Que Eu Acho Mais Importante Do Que Skills

Há muita conversa agora sobre skills de agentes, prompts customizados, templates reutilizáveis, instruções cuidadosamente ajustadas. Eles podem ajudar, mas acho que a maior parte da alavanca está em boa gestão de contexto, planejamento e desenho do sistema. Menos no que a skill faz, mais em quão bem a informação que alimenta o modelo foi curada.

Depois de cometer o erro de complicar demais as coisas, posso aconselhar com confiança contra isso. Tirando a vontade periódica de exagerar, meu setup hoje é bem simples. Essencialmente tenho uma base de conhecimento, parecida com a do Karpathy [[7]](#ref-7), e um orquestrador multiagente customizado que construí no começo deste ano e decidi manter por preguiça (e hábito). O que quero dizer, no fim, é que os detalhes do setup importam muito pouco. O valor está em decidir como o trabalho é dividido, o que cada sessão enxerga e qual artefato ela precisa deixar para trás.

Agora, e provavelmente pelos próximos 6 a 12 meses, modelos são muito bons na execução quando há um alvo claro. Nem tanto quando o plano está nebuloso e mal definido. Fechar pontas soltas e desenhar um plano com clareza suficiente para que cada parte possa ser executada isoladamente é difícil, mas compensa muito no longo prazo. Então eu prefiro gastar energia com enquadramento do problema, trade-offs e qualidade dos artefatos do que construindo setups elaborados de agentes que, na maior parte, vão representar melhorias marginais sobre o desempenho baseline.

## Uma Sessão, Uma Tarefa

Se eu tivesse que transformar tudo acima em uma única regra, seria uma sessão, uma tarefa. Não porque sessões mais longas nunca funcionem, mas porque elas acumulam resíduo. Becos sem saída, objetivos misturados, restrições antigas, ramificações abandonadas que ainda parecem localmente plausíveis. Quanto mais uma sessão se estende, mais esse resíduo se acumula, e mais difícil fica distinguir o que ainda é relevante do que já deveria ter ficado para trás.

A sessão que pesquisa um problema não deveria escrever a especificação final. A sessão que escreve a especificação não deveria implementá-la. Pesquisa é divergente: ela existe para explorar opções, rejeitar ideias, revelar desconhecidos. Uma especificação é convergente: ela existe para decidir. Implementação é ainda mais estreita: ela não precisa saber de decisões potenciais que nunca foram tomadas, só executar a partir de um objetivo definido.

Quando uma sessão faz as três coisas, o contexto de implementação acaba carregando abordagens rejeitadas, restrições meio decididas e raciocínios exploratórios que foram úteis antes, mas agora atrapalham. Esse é exatamente o tipo de contexto que volta à vida por acidente.

Por isso, o artefato de passagem importa mais do que a sessão em si. Uma sessão de pesquisa deixa uma nota de pesquisa: opções consideradas, direção escolhida, razões de rejeição, perguntas em aberto. Uma sessão de especificação tenta fechar essas perguntas e as decisões restantes, e transforma isso em um pacote de implementação: escopo, critérios de aceitação, restrições, não objetivos. A sessão de implementação começa limpa a partir desse pacote. Se algo importante mudar, pare e abra uma nova sessão em vez de arrastar o contexto antigo adiante.

Para mim, essa é a forma mais prática de continuidade: uma cadeia de artefatos limpos sendo construída até uma conclusão final, no lugar de uma sessão imortal esticada além da conta.

## Fluxo De Trabalho Pessoal, Não Doutrina

E, seguindo o conselho dos meus advogados, devo dizer que tudo isso é uma opinião pessoal. Uma opinião informada, talvez. Uso essas ferramentas diariamente e passo uma boa quantidade de tempo pesquisando como funcionam os modelos por trás delas. Ainda assim, uma opinião. Posso estar errado em muita coisa (e provavelmente estou), ninguém sabe de fato qual é a melhor forma de trabalhar com IA ainda. Muita coisa vai mudar nos próximos anos, mas, dito isso, não espero que o centro de gravidade se desloque tanto nos próximos meses. Por enquanto, continuo achando que a alavanca está mais em gestão de contexto, planejamento e desenho do sistema do que em persistência de sessão cada vez mais sofisticada.

É também por isso que sou cético quanto a copiar o setup de outra pessoa por inteiro. A maioria das pessoas ainda trata fluxos de trabalho com IA como software tradicional: encontre algo que funciona, copie, use como está. Alguém encontra uma skill útil e copia o arquivo markdown como se tivesse encontrado uma solução empacotada que não pudesse ser realmente alterada. Para mim, isso é sinal de que essa pessoa ainda não percebeu o que torna trabalhar com IA diferente. Tudo pode ser customizado. Cada aspecto de um fluxo de trabalho pode carregar o seu gosto, as suas pequenas mudanças bobas e manias. Então, em vez de procurar o template certo, pegue a ideia e reconstrua até ela caber no seu jeito de pensar.

As ferramentas vão melhorar, os modelos vão melhorar. Mas acho que as pessoas que aprenderem a trabalhar bem com o que temos agora vão se sair muito melhor do que aquelas esperando o próximo salto. Entender que você é a camada de continuidade, e não aquilo que a ferramenta que você usa tenta fazer você acreditar, ajuda bastante nisso.

---

**Fontes:**

[1] OpenAI, *Conversation state*. `previous_response_id`, respostas armazenadas e objetos de conversa. [platform.openai.com/docs/guides/conversation-state](https://platform.openai.com/docs/guides/conversation-state)

[2] Anthropic, *Messages API*. Documenta conversas multi-turn sem estado por meio da reintrodução repetida de mensagens. [docs.anthropic.com/en/api/messages](https://docs.anthropic.com/en/api/messages)

[3] Anthropic, *Compaction*. Recomenda compactação para conversas longas e fluxos de trabalho agênticos. [docs.anthropic.com/en/docs/build-with-claude/compaction](https://docs.anthropic.com/en/docs/build-with-claude/compaction)

[4] Liu, N. F. et al., *Lost in the Middle: How Language Models Use Long Contexts*, TACL 2024. [arxiv.org/abs/2307.03172](https://arxiv.org/abs/2307.03172)

[5] Du, X. et al., *Context Length Alone Hurts LLM Performance Despite Perfect Retrieval*, Findings of EMNLP 2025. [arxiv.org/abs/2510.05381](https://arxiv.org/abs/2510.05381)

[6] Tan, H. et al., *Blinded by Generated Contexts: How Language Models Merge Generated and Retrieved Contexts When Knowledge Conflicts?*, ACL 2024. [aclanthology.org/2024.acl-long.337](https://aclanthology.org/2024.acl-long.337/)

[7] Karpathy, A., *Context Engineering*. [x.com/karpathy/status/2040470801506541998](https://x.com/karpathy/status/2040470801506541998)
