---
title: O Que Eu Faço o Dia Inteiro
slug: what-i-do-ml-engineering
date: 2026-07-05
excerpt: Engenharia de Machine Learning, explicada pros meus amigos.
tags:
- Machine Learning
- Engenharia
- Carreira
lang: pt-br
content_type: presentation
---

<!-- presentation:slide id="title" layout="lead" density="normal" -->

# O Que Eu Faço o Dia Inteiro

## Engenharia de Machine Learning, explicada pros meus amigos

Daniel Cavalli | dan.rio

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="dense" -->

# Daniel Cavalli

Senior Machine Learning Engineer

Nove anos construindo sistemas de machine learning. Me formei em economia, estudei numa escola de fazer videogame, e de algum jeito fui parar aqui. Escreve em dan.rio.

![Daniel Cavalli](/static/images/presentations/what-i-do-ml-engineering/profile-picture.png)

| # | Parte | O que você leva daqui |
| - | ----- | --------------------- |
| 1 | O Trabalho Que Ninguém Sabe Nomear | "Então, o que é mesmo que você faz?" |
| 2 | O Que é um Modelo, de Verdade | A coisa, sem o mistério |
| 3 | A Plataforma | O que eu faço enquanto você me manda mensagem |
| 4 | Deixar o Treino Rápido | Por que sou obcecado em esperar menos |
| 5 | Por Que Modelos Apodrecem | Por que o trabalho nunca acaba |
| 6 | Como Cheguei Aqui | Como um cara de economia foi parar aqui |

<!-- /presentation:slide -->

<!-- presentation:slide id="job-nobody-can-name" layout="divider" density="normal" -->

# O Trabalho Que Ninguém Sabe Nomear

## Todo mundo fala "IA" agora. Quase ninguém sabe dizer quem constrói o encanamento embaixo disso.

<!-- /presentation:slide -->

<!-- presentation:slide id="when-you-ask" layout="content" density="dense" -->

# Quando você pergunta o que eu faço

Eu falo "Engenheiro de Machine Learning". Você ouve "IA". Imagina um robô, ou o ChatGPT, ou eu num quarto escuro treinando a Skynet caladinho. Aí você balança a cabeça educadamente e a gente muda de assunto.

E tá tudo bem, porque durante anos as únicas pessoas explicando isso estavam tentando te vender alguma coisa, então as palavras ficaram estranhas antes de ficarem úteis. Então aqui vai a versão que eu te contaria de verdade tomando uma cerveja.

> Sabe aquela IA que todo mundo comenta? Eu construo o encanamento chato e invisível que impede ela de cair no segundo em que uma pessoa de verdade usa.

O modelo esperto é a parte famosa. O encanamento é a parte que decide se aquele modelo um dia sai do notebook de alguém.

<!-- /presentation:slide -->

<!-- presentation:slide id="two-jobs" layout="split" density="dense" -->

# Dois trabalhos que todo mundo confunde

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### O Cientista de Dados
A pergunta dele: *o que essa coisa deveria aprender, e ela é boa?* Ele inventa a receita. O que ele entrega é algo que funcionou uma vez, no notebook dele, num dia bom.
<!-- /presentation:column -->
<!-- presentation:column -->
### O Engenheiro de ML (eu)
Minha pergunta: *tá, mas como isso roda milhões de vezes por dia sem quebrar, e quem recebe a ligação às 3 da manhã quando quebra?* Eu mantenho a receita funcionando pra sempre, pra todo mundo, sem ninguém olhando.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### O restaurante, resumindo
O cientista de dados é o chef que inventa um prato. Eu construo a cozinha que faz esse mesmo prato dez mil vezes por noite, com o mesmo sabor toda vez, sem botar fogo no lugar. Inventar uma receita e tocar uma cozinha são trabalhos diferentes. As pessoas confundem porque os dois envolvem comida.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="notebook-vs-production" layout="emphasis" density="normal" -->

# A frase que explica tudo

> Um modelo no notebook de alguém é um projeto de feira de ciências bem legal. O mesmo modelo lá fora, no mundo real, é uma promessa que você tem que cumprir a cada segundo de cada dia.

O ofício inteiro vive na distância entre essas duas frases. Fazer algo funcionar uma vez é a parte fácil e divertida que quase qualquer um consegue. Manter funcionando, pra gente de verdade, enquanto o mundo muda embaixo, é a parte difícil. E acontece que essa parte difícil é mais encanamento do que matemática.

É nessa distância que eu passo os meus dias.

<!-- /presentation:slide -->

<!-- presentation:slide id="what-a-model-is" layout="divider" density="normal" -->

# O Que é um Modelo, de Verdade

## Antes do trabalho fazer sentido, a própria coisa precisa fazer sentido

<!-- /presentation:slide -->

<!-- presentation:slide id="model-learns-rules" layout="content" density="dense" -->

# Um modelo aprende as regras sozinho

Software normal é só uma lista de regras que uma pessoa escreveu na mão: *se o cliente ganha mais que isso e é mais novo que aquilo, nega o empréstimo.* Cada regra foi digitada por um humano, e quando erra, dá pra apontar pro humano que digitou.

Um modelo inverte isso. Ninguém escreve as regras. Você mostra pra ele milhões de exemplos do passado, os bons e os ruins, e ele descobre as próprias regras a partir dos padrões. Pensa em como você reconhece o rosto de um amigo no meio da multidão sem conseguir explicar exatamente como. Ele acaba tomando decisões que ninguém nunca escreveu, o que é justamente o motivo de ser tão poderoso e, ao mesmo tempo, meio perturbador.

> Você não está escrevendo a resposta. Você está construindo a coisa que chega na resposta. E depois tem que confiar em algo cujo raciocínio você não consegue ler de volta por inteiro.

<!-- /presentation:slide -->

<!-- presentation:slide id="two-phases" layout="card_grid" density="dense" -->

# Duas fases, dois problemas completamente diferentes

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Treino (o estudo)
O modelo senta com montanhas de exemplos do passado e vai aprendendo devagar. É a parte cara e lenta: salas cheias de chips especiais rodando por dias, queimando uma conta de luz que te faria fazer careta. Você faz isso raramente.
<!-- /presentation:card -->
<!-- presentation:card -->
### Usar (a prova)
Depois que estudou, você faz uma pergunta de verdade e ele responde na hora. Isso precisa ser instantâneo e barato, porque pode acontecer dezenas de milhares de vezes por minuto, e cada resposta tem que chegar antes de alguém perceber que esperou.
<!-- /presentation:card -->
<!-- presentation:card -->
### Onde eu entro
As duas partes são, no fundo, problemas de encanamento vestidos de jaleco. Alguém precisa deixar o estudo rápido o suficiente pra valer a pena e a resposta confiável o suficiente pra confiar. Esse alguém sou eu.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="lifecycle" layout="card_grid" density="very_dense" -->

# O ciclo, e onde cada um de nós vive

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Dados
Coletar, limpar, deixar confiável. Chato, sem glamour, e o maior motivo isolado de modelos falharem.
<!-- /presentation:card -->
<!-- presentation:card -->
### Treinar
Onde o cientista de dados mais vive. Transformar dados num modelo que funciona.
<!-- /presentation:card -->
<!-- presentation:card -->
### Colocar no ar
Tirar do notebook e botar no aplicativo de verdade que as pessoas usam.
<!-- /presentation:card -->
<!-- presentation:card -->
### Monitorar
Ficar de olho nele solto no mundo. Pegar no exato momento em que começa a piorar caladinho.
<!-- /presentation:card -->
<!-- presentation:card -->
### Retreinar
O mundo mudou, então o modelo tem que mudar. Aí o ciclo inteiro roda de novo.
<!-- /presentation:card -->
<!-- /presentation:block -->

O cientista de dados cuida mais de uma dessas caixas. Eu cuido das setas entre todas elas, e do fato de esse círculo todo continuar girando sozinho enquanto todo mundo dorme.

<!-- /presentation:slide -->

<!-- presentation:slide id="the-platform" layout="divider" density="normal" -->

# A Plataforma

## Meus usuários não são clientes. São as pessoas que constroem os modelos.

<!-- /presentation:slide -->

<!-- presentation:slide id="tools-for-builders" layout="split" density="dense" -->

# Eu faço as ferramentas pra quem faz a IA

A maioria dos aplicativos é feita pra pessoas normais, como você. Eu faço ferramentas pras pessoas que constroem a IA, a galera cujo trabalho inteiro é inventar modelos novos. Eu sou o chão em que elas pisam, o que na prática quer dizer que elas só reparam em mim quando o chão treme.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Pra quem eu construo
Uma empresa inteira dessas pessoas que constroem modelos, com montes de modelos rodando ao vivo a qualquer momento. Cada uma quer construir e lançar sem antes ter que virar especialista em encanamento. Meu trabalho é poupar elas disso.
<!-- /presentation:column -->
<!-- presentation:column -->
### O que eu construo de fato
Uma base compartilhada, pra ninguém ter que reinventar a máquina chata do zero toda santa vez. Elas trazem a ideia esperta. A plataforma cuida caladinha de tudo embaixo.
<!-- /presentation:column -->
<!-- /presentation:block -->

> Se eu faço bem, ninguém nunca pensa em mim. Se eu faço mal, nada funciona. Meu trabalho inteiro é ser invisível, o que é uma coisa genuinamente estranha pra se construir uma carreira em cima.

<!-- /presentation:slide -->

<!-- presentation:slide id="what-platform-means" layout="card_grid" density="very_dense" -->

# O que "plataforma" quer dizer na prática

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Um lugar pra treinar
Todos os computadores pesados e chips, ligados de um jeito que a pessoa só diz "roda meu experimento" e recebe a resposta de volta, sem nunca ter que brigar com um servidor.
<!-- /presentation:card -->
<!-- presentation:card -->
### Um jeito seguro de lançar
Uma estrada asfaltada de "funciona no meu notebook" até "no ar pra todo mundo", com grades de proteção pra uma versão quebrada não escapar caladinha pras pessoas de verdade.
<!-- /presentation:card -->
<!-- presentation:card -->
### Um jeito de ficar de olho
Manter os modelos no ar rápidos e saudáveis, e me cutucar no ombro no instante em que um começa a se afastar da realidade.
<!-- /presentation:card -->
<!-- presentation:card -->
### Espaço pra crescer
Construir de um jeito que a mesma coisa funcione num lugar novo sem ter que derrubar tudo e recomeçar. Crescer devia ser um ajuste pequeno, não uma reconstrução inteira.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="making-training-fast" layout="divider" density="normal" -->

# Deixar o Treino Rápido

## O número sem glamour que decide tudo em silêncio: quanto tempo você tem que esperar.

<!-- /presentation:slide -->

<!-- presentation:slide id="one-computer" layout="split" density="dense" -->

# Um computador nunca é suficiente

Ensinar um modelo grande numa máquina só pode levar semanas. Boa parte do meu trabalho é transformar "semanas" em "alguns dias", pra treinar um modelo deixar de ser um evento raro que você planeja o mês em volta e virar uma terça-feira comum.

Você pensaria que é só botar mais computadores e vai mais rápido. É exatamente aí que o palpite da maioria das pessoas para, e é um palpite perfeitamente sensato. É também onde o problema de verdade começa, porque computadores, que nem gente, são péssimos em trabalhar juntos sem muita ajuda.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### O problema do trabalho em grupo
Imagina um trabalho em grupo onde todo mundo tem que estar na mesma página, o tempo todo. Você divide as tarefas, mas agora todos têm que parar e comparar anotações de novo e de novo. Coordena mal e oito pessoas de algum jeito terminam mais devagar que uma. Computadores são exatamente assim.
<!-- /presentation:column -->
<!-- presentation:column -->
### Onde meu trabalho de verdade está
Então o trabalho quase nunca é "compra mais máquinas". É fazer elas conversarem entre si sem tropeçar nos próprios pés: quem faz qual pedaço, quando dão notícia, e como manter todo mundo ocupado em vez de parado esperando.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="wait-time" layout="emphasis" density="dense" -->

# O número que importa mais que a velocidade pura

> O verdadeiro prêmio é encurtar a espera entre "tive uma ideia" e "consigo ver se funcionou", de uma pausa pro café pra um respiro.

Parece só uma comodidade. Mas na verdade muda o jeito como as pessoas pensam. Quando o retorno leva vários minutos, você fica cauteloso, junta seus palpites, para de experimentar porque cada tentativa custa um tempo real. Quando leva segundos, você simplesmente tenta.

Retorno rápido não deixa só as pessoas mais rápidas. Deixa elas mais corajosas. É essa a coisa que eu de fato vendo, e quase ninguém de fora desse mundo imaginaria que uma plataforma inteira é construída em torno de algo tão humano quanto o tempo que as pessoas topam esperar.

<!-- /presentation:slide -->

<!-- presentation:slide id="why-models-rot" layout="divider" density="normal" -->

# Por Que Modelos Apodrecem

## A parte que ninguém te avisa: o modelo que estava certo mês passado está calado e errado hoje.

<!-- /presentation:slide -->

<!-- presentation:slide id="world-moves" layout="content" density="dense" -->

# O mundo se mexe. O modelo não.

Um modelo aprende com o passado. É esse o truque inteiro e também o problema inteiro, porque o passado é a única coisa que ele vai conhecer, e o mundo se recusa a ficar parado.

Os padrões de fraude mudam na semana seguinte a você pegá-los. Preços mudam. As pessoas mudam de comportamento. O modelo não percebe nada disso. Ele continua aplicando com confiança as regras de ontem ao mundo de hoje, e todos os painéis dizem que está rodando perfeitamente enquanto as respostas dele escorregam devagar de úteis pra erradas.

> Isso se chama drift, e é o vilão silencioso do campo inteiro. Nada trava. Nenhum alarme dispara. O modelo só vai piorando em completo silêncio até alguém pensar em conferir.

Então o trabalho nunca é "lança e esquece". É ficar de olho, pegar o drift, retreinar, relançar, e fazer tudo de novo, pra sempre.

<!-- /presentation:slide -->

<!-- presentation:slide id="mlops" layout="card_grid" density="very_dense" -->

# Fazendo tudo isso, pra muitos modelos ao mesmo tempo

Agora imagina tudo do slide anterior, mas pra centenas de modelos ao mesmo tempo, e sem um exército de gente segurando na mão de cada um. Meu canto da área tem um nome feio pra isso, "MLOps", mas no fundo só quer dizer deixar as partes chatas e repetitivas automáticas e confiáveis.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Linhas de montagem
Em vez de uma pessoa clicando em cada atualização na mão, os passos chatos rodam sozinhos numa agenda. Um humano decide o que deve acontecer; a máquina cuida do trabalho tedioso de fazer acontecer.
<!-- /presentation:card -->
<!-- presentation:card -->
### Uma receita escrita
O setup inteiro está escrito passo a passo, tipo manual de montar móvel, pra qualquer um conseguir reconstruir ou achar um erro. A alternativa é ele viver só na cabeça de uma pessoa e numa pasta de scripts frágeis que quebram se você olhar torto.
<!-- /presentation:card -->
<!-- presentation:card -->
### Reconstruindo em pleno voo
Boa parte do meu trabalho recente é trocar as fundações enquanto centenas de pessoas continuam usando a coisa todo dia. É um pouco como trocar o motor de um avião sem pousar o avião.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="how-i-got-here" layout="divider" density="normal" -->

# Como Cheguei Aqui

## Eu tenho um diploma de economia e estudei numa escola de fazer videogame. Isso não era um plano.

<!-- /presentation:slide -->

<!-- presentation:slide id="path-made-no-sense" layout="split" density="dense" -->

# O caminho não fazia sentido até fazer

Eu me formei em economia na faculdade. Antes disso, um ensino técnico de fazer videogame. Nenhum dos dois é a pista de decolagem óbvia pra uma carreira em infraestrutura de machine learning, o que é mais ou menos o ponto.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Onde começou
Meu primeiro trabalho de verdade foi ler texto aberto de pesquisas com um modelo de linguagem antigo, numa época em que explicar "IA" num jantar rendia um olhar vazio em vez de uma opinião. Depois anti-fraude, que é onde aprendi que um modelo só é tão bom quanto o sistema que o sustenta.
<!-- /presentation:column -->
<!-- presentation:column -->
### O que de fato foi pro ar
Aquele trabalho de anti-fraude barrou uma quantidade relevante de fraude a um custo minúsculo por checagem. O que ficou comigo foi a lição, não o número: o modelo importava, e a máquina em volta dele importava mais.
<!-- /presentation:column -->
<!-- /presentation:block -->

O fio condutor não é um diploma. É um gosto específico pela metade sem glamour do problema, a metade que decide se a parte esperta um dia chega numa pessoa de verdade.

<!-- /presentation:slide -->

<!-- presentation:slide id="trade-not-talent" layout="emphasis" density="normal" -->

# O que eu quero que meus amigos levem daqui

> Isso é um ofício, não um dom. É mais perto de ser um encanador teimoso do que um gênio solitário. O romance é opcional. A confiabilidade não é.

A área se enrola num mistério porque mistério vende, e por um tempo eu também quase acreditei. Mas tirando isso, é artesanato: constrói a coisa, deixa rápida, mantém honesta, e esteja lá quando quebrar. Dá pra aprender, é sem glamour, e é silenciosamente satisfatório do jeito que todo ofício de verdade é.

Você não precisa de doutorado nem da permissão de ninguém pra começar. Eu com certeza não tinha nenhum dos dois.

<!-- /presentation:slide -->

<!-- presentation:slide id="home-lab" layout="split" density="dense" -->

# O laboratório em casa, e por que ele existe

Tem duas placas de vídeo zumbindo no meu apartamento agora, sem ninguém pagando por isso. Eu montei essa maquininha de propósito.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Não pra ser rápido
Ela nunca vai ganhar nenhuma competição de velocidade, e nunca foi essa a ideia. Ela está ali pra eu poder ver dois chips tentando aprender uma coisa juntos, bem na minha frente, e de fato entender por que fica lento em vez de só ler que fica.
<!-- /presentation:column -->
<!-- presentation:column -->
### Pra realmente entender
Esse trabalho recompensa curiosidade muito mais do que qualquer diploma. Você aprende como a versão gigante funciona construindo uma versão minúscula que você entende por inteiro, quebrando de propósito, e consertando. O aprendizado genuinamente nunca para, o que é a melhor e a mais cansativa parte.
<!-- /presentation:column -->
<!-- /presentation:block -->

Isso, numa única máquina que aquece o apartamento, é o trabalho inteiro. Construir a coisa sem glamour que faz a coisa esperta virar real, e continuar curioso o suficiente pra reconstruir de novo.

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Obrigado

## Perguntas são bem-vindas, principalmente as ingênuas

dan.rio | github.com/danielcavalli

<!-- /presentation:slide -->
