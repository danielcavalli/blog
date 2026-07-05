---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  section {
    background: #ffffff;
    color: #111111;
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 22px;
    line-height: 1.5;
    padding: 48px 64px;
  }
  h1, h2, h3 {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    color: #1A6B7A;
    letter-spacing: -0.03em;
  }
  h1 {
    font-size: 1.8em;
    font-weight: 600;
    margin-bottom: 0.5em;
  }
  h2 {
    font-size: 1.3em;
    font-weight: 500;
    letter-spacing: -0.02em;
    margin-top: 0;
  }
  code {
    background: #F4F4F4;
    color: #1A6B7A;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9em;
  }
  pre {
    background: #1A1A1A !important;
    border-radius: 8px;
    padding: 16px 24px !important;
    font-size: 0.78em;
    margin: 8px 0;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  figure, img { border: none !important; outline: none !important; }
  pre code {
    background: transparent;
    color: #e0e0e0;
    padding: 0;
  }
  a { color: #1A6B7A; }
  table { font-size: 0.78em; width: 100%; margin: 12px 0; border-collapse: collapse; border-spacing: 0; }
  table, thead, tbody, tr, th, td { border: none !important; outline: none !important; border-style: none !important; }
  th {
    background: #1A6B7A;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
  }
  th:first-child { border-radius: 8px 0 0 0; }
  th:last-child { border-radius: 0 8px 0 0; }
  td {
    background: #F5F5F5;
    padding: 8px 16px;
  }
  blockquote {
    border-left: 3px solid #1A6B7A;
    background: #F4F4F4;
    padding: 12px 24px;
    margin: 12px 0;
    font-size: 0.95em;
    color: #333333;
    border-radius: 0 8px 8px 0;
  }
  ul, ol { margin: 6px 0; }
  li { margin: 4px 0; }
  p { margin: 10px 0; }
  section::after { color: #6B6B6B; }
  strong { color: #1A1A1A; }
  section.lead {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.lead h1 {
    font-size: 2.6em;
    text-align: center;
    color: #ffffff;
  }
  section.lead h2 {
    text-align: center;
    font-size: 1.2em;
    color: #8CC8D4;
    font-weight: 400;
  }
  section.lead p {
    text-align: center;
    color: #B8DEE6;
    font-size: 1.05em;
  }
  section.divider {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.divider h1 {
    font-size: 2.4em;
    text-align: center;
    color: #ffffff;
  }
  section.divider h2 {
    text-align: center;
    color: #8CC8D4;
    font-size: 1.1em;
    font-weight: 400;
  }
  section.emphasis {
    background: #F4F4F4;
  }
  section.emphasis blockquote {
    background: #ffffff;
    font-size: 1.15em;
    padding: 24px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .bio-layout {
    display: flex;
    gap: 48px;
    align-items: flex-start;
    margin-top: 0;
  }
  .bio-content { flex: 1; }
  .bio-content h1 { margin-bottom: 4px; }
  .bio-photo {
    flex-shrink: 0;
    margin-top: 8px;
  }
  .bio-photo img {
    width: 260px;
    height: 260px;
    border-radius: 16px;
    object-fit: cover;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  }
  .bio-detail {
    color: #6B6B6B;
    font-size: 0.88em;
    margin: 2px 0;
  }
  .card-row {
    display: flex;
    gap: 20px;
    margin-top: 16px;
  }
  .card {
    flex: 1;
    background: #F5F5F5;
    border-radius: 10px;
    padding: 20px 24px;
    border-left: 3px solid #1A6B7A;
  }
  .card h3 {
    font-size: 0.95em;
    margin: 0 0 8px 0;
  }
  .card p {
    font-size: 0.82em;
    color: #555;
    margin: 0;
    line-height: 1.45;
  }
  .card-dark {
    background: #152D38;
    border-left: 3px solid #8CC8D4;
  }
  .card-dark h3 { color: #8CC8D4; }
  .card-dark p { color: #B8DEE6; }
  .split {
    display: flex;
    gap: 40px;
    align-items: flex-start;
  }
  .split > div { flex: 1; }
  .split > div + div { border-left: 2px solid #E0E0E0; padding-left: 40px; }
  .dim { color: #6B6B6B; font-size: 0.85em; }
  .small { font-size: 0.8em; }
  section.dark-content {
    background: #1A1A1A;
    color: #E0E0E0;
    padding: 36px 56px 28px;
  }
  section.dark-content h1 {
    color: #ffffff;
    font-size: 1.5em;
    margin: 0 0 20px 0;
  }
  section.dark-content blockquote {
    background: #252525;
    color: #B8DEE6;
    border-left-color: #1A6B7A;
  }
  footer {
    color: #6B6B6B;
    font-size: 0.65em;
  }
footer: Daniel Cavalli | dan.rio
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# O Que Eu Faço o Dia Inteiro

## Engenharia de Machine Learning, explicada pros meus amigos

Daniel Cavalli | dan.rio

---

<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="bio-layout">
  <div class="bio-content">
    <h1 style="margin-bottom: 4px;">Daniel Cavalli</h1>
    <p class="bio-detail">Senior Machine Learning Engineer</p>
    <p class="bio-detail">9 anos em ML. Formado em economia. Escreve em dan.rio</p>
    <div style="margin-top: 28px;">
      <table>
        <tr><th></th><th>Parte</th><th>O que você leva daqui</th></tr>
        <tr><td>1</td><td>O Trabalho Que Ninguém Sabe Nomear</td><td>"Então, o que é mesmo que você faz?"</td></tr>
        <tr><td>2</td><td>O Que é um Modelo, de Verdade</td><td>A coisa, sem o mistério</td></tr>
        <tr><td>3</td><td>A Plataforma</td><td>O que eu faço enquanto você me manda mensagem</td></tr>
        <tr><td>4</td><td>Deixar o Treino Rápido</td><td>Por que sou obcecado em esperar menos</td></tr>
        <tr><td>5</td><td>Por Que Modelos Apodrecem</td><td>Por que o trabalho nunca acaba</td></tr>
        <tr><td>6</td><td>Como Cheguei Aqui</td><td>Como um cara de economia foi parar aqui</td></tr>
      </table>
    </div>
  </div>
  <div class="bio-photo">
    <img src="./assets/profile-picture.png" />
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# O Trabalho Que Ninguém Sabe Nomear

## Todo mundo fala "IA" agora. Quase ninguém sabe dizer quem constrói o encanamento embaixo disso.

---

# Quando você pergunta o que eu faço

Eu falo "Engenheiro de Machine Learning". Você ouve "IA". Imagina um robô, ou o ChatGPT, ou eu num quarto escuro treinando a Skynet caladinho. Aí você balança a cabeça educadamente e a gente muda de assunto.

E tá tudo bem, porque durante anos as únicas pessoas explicando isso estavam tentando te vender alguma coisa, então as palavras ficaram estranhas antes de ficarem úteis. Então aqui vai a versão que eu te contaria de verdade tomando uma cerveja.

> Sabe aquela IA que todo mundo comenta? Eu construo o encanamento chato e invisível que impede ela de cair no segundo em que uma pessoa de verdade usa.

O modelo esperto é a parte famosa. O encanamento é a parte que decide se aquele modelo um dia sai do notebook de alguém.

---

# Dois trabalhos que todo mundo confunde

<div class="split">
  <div>
    <h3>O Cientista de Dados</h3>
    <p>A pergunta dele: <em>o que essa coisa deveria aprender, e ela é boa?</em> Ele inventa a receita. O que ele entrega é algo que funcionou uma vez, no notebook dele, num dia bom.</p>
  </div>
  <div>
    <h3>O Engenheiro de ML (eu)</h3>
    <p>Minha pergunta: <em>tá, mas como isso roda milhões de vezes por dia sem quebrar, e quem recebe a ligação às 3 da manhã quando quebra?</em> Eu mantenho a receita funcionando pra sempre, pra todo mundo, sem ninguém olhando.</p>
  </div>
</div>

<div class="card-row">
  <div class="card">
    <h3>O restaurante, resumindo</h3>
    <p>O cientista de dados é o chef que inventa um prato. Eu construo a cozinha que faz esse mesmo prato dez mil vezes por noite, com o mesmo sabor toda vez, sem botar fogo no lugar. Inventar uma receita e tocar uma cozinha são trabalhos diferentes. As pessoas confundem porque os dois envolvem comida.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# A frase que explica tudo

> Um modelo no notebook de alguém é um projeto de feira de ciências bem legal. O mesmo modelo lá fora, no mundo real, é uma promessa que você tem que cumprir a cada segundo de cada dia.

O ofício inteiro vive na distância entre essas duas frases. Fazer algo funcionar uma vez é a parte fácil e divertida que quase qualquer um consegue. Manter funcionando, pra gente de verdade, enquanto o mundo muda embaixo, é a parte difícil. E acontece que essa parte difícil é mais encanamento do que matemática.

É nessa distância que eu passo os meus dias.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# O Que é um Modelo, de Verdade

## Antes do trabalho fazer sentido, a própria coisa precisa fazer sentido

---

# Um modelo aprende as regras sozinho

Software normal é só uma lista de regras que uma pessoa escreveu na mão: *se o cliente ganha mais que isso e é mais novo que aquilo, nega o empréstimo.* Cada regra foi digitada por um humano, e quando erra, dá pra apontar pro humano que digitou.

Um modelo inverte isso. Ninguém escreve as regras. Você mostra pra ele milhões de exemplos do passado, os bons e os ruins, e ele descobre as próprias regras a partir dos padrões. Pensa em como você reconhece o rosto de um amigo no meio da multidão sem conseguir explicar exatamente como. Ele acaba tomando decisões que ninguém nunca escreveu, o que é justamente o motivo de ser tão poderoso e, ao mesmo tempo, meio perturbador.

> Você não está escrevendo a resposta. Você está construindo a coisa que chega na resposta. E depois tem que confiar em algo cujo raciocínio você não consegue ler de volta por inteiro.

---

# Duas fases, dois problemas completamente diferentes

<div class="card-row">
  <div class="card">
    <h3>Treino (o estudo)</h3>
    <p>O modelo senta com montanhas de exemplos do passado e vai aprendendo devagar. É a parte cara e lenta: salas cheias de chips especiais rodando por dias, queimando uma conta de luz que te faria fazer careta. Você faz isso raramente.</p>
  </div>
  <div class="card">
    <h3>Usar (a prova)</h3>
    <p>Depois que estudou, você faz uma pergunta de verdade e ele responde na hora. Isso precisa ser instantâneo e barato, porque pode acontecer dezenas de milhares de vezes por minuto, e cada resposta tem que chegar antes de alguém perceber que esperou.</p>
  </div>
  <div class="card card-dark">
    <h3>Onde eu entro</h3>
    <p>As duas partes são, no fundo, problemas de encanamento vestidos de jaleco. Alguém precisa deixar o estudo rápido o suficiente pra valer a pena e a resposta confiável o suficiente pra confiar. Esse alguém sou eu.</p>
  </div>
</div>

---

# O ciclo, e onde cada um de nós vive

<div class="card-row">
  <div class="card" style="text-align: center;">
    <h3>Dados</h3>
    <p>Coletar, limpar, deixar confiável. Chato, sem glamour, e o maior motivo isolado de modelos falharem.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Treinar</h3>
    <p>Onde o cientista de dados mais vive. Transformar dados num modelo que funciona.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Colocar no ar</h3>
    <p>Tirar do notebook e botar no aplicativo de verdade que as pessoas usam.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Monitorar</h3>
    <p>Ficar de olho nele solto no mundo. Pegar no exato momento em que começa a piorar caladinho.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Retreinar</h3>
    <p>O mundo mudou, então o modelo tem que mudar. Aí o ciclo inteiro roda de novo.</p>
  </div>
</div>

<p style="margin-top: 20px;">O cientista de dados cuida mais de uma dessas caixas. Eu cuido das setas entre todas elas, e do fato de esse círculo todo continuar girando sozinho enquanto todo mundo dorme.</p>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# A Plataforma

## Meus usuários não são clientes. São as pessoas que constroem os modelos.

---

# Eu faço as ferramentas pra quem faz a IA

A maioria dos aplicativos é feita pra pessoas normais, como você. Eu faço ferramentas pras pessoas que constroem a IA, a galera cujo trabalho inteiro é inventar modelos novos. Eu sou o chão em que elas pisam, o que na prática quer dizer que elas só reparam em mim quando o chão treme.

<div class="split">
  <div>
    <h3>Pra quem eu construo</h3>
    <p>Uma empresa inteira dessas pessoas que constroem modelos, com montes de modelos rodando ao vivo a qualquer momento. Cada uma quer construir e lançar sem antes ter que virar especialista em encanamento. Meu trabalho é poupar elas disso.</p>
  </div>
  <div>
    <h3>O que eu construo de fato</h3>
    <p>Uma base compartilhada, pra ninguém ter que reinventar a máquina chata do zero toda santa vez. Elas trazem a ideia esperta. A plataforma cuida caladinha de tudo embaixo.</p>
  </div>
</div>

> Se eu faço bem, ninguém nunca pensa em mim. Se eu faço mal, nada funciona. Meu trabalho inteiro é ser invisível, o que é uma coisa genuinamente estranha pra se construir uma carreira em cima.

---

# O que "plataforma" quer dizer na prática

<div class="card-row">
  <div class="card">
    <h3>Um lugar pra treinar</h3>
    <p>Todos os computadores pesados e chips, ligados de um jeito que a pessoa só diz "roda meu experimento" e recebe a resposta de volta, sem nunca ter que brigar com um servidor.</p>
  </div>
  <div class="card">
    <h3>Um jeito seguro de lançar</h3>
    <p>Uma estrada asfaltada de "funciona no meu notebook" até "no ar pra todo mundo", com grades de proteção pra uma versão quebrada não escapar caladinha pras pessoas de verdade.</p>
  </div>
  <div class="card">
    <h3>Um jeito de ficar de olho</h3>
    <p>Manter os modelos no ar rápidos e saudáveis, e me cutucar no ombro no instante em que um começa a se afastar da realidade.</p>
  </div>
  <div class="card">
    <h3>Espaço pra crescer</h3>
    <p>Construir de um jeito que a mesma coisa funcione num país novo sem ter que derrubar tudo e recomeçar. Crescer devia ser um ajuste pequeno, não uma reconstrução inteira.</p>
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Deixar o Treino Rápido

## O número sem glamour que decide tudo em silêncio: quanto tempo você tem que esperar.

---

# Um computador nunca é suficiente

Ensinar um modelo grande numa máquina só pode levar semanas. Boa parte do meu trabalho é transformar "semanas" em "alguns dias", pra treinar um modelo deixar de ser um evento raro que você planeja o mês em volta e virar uma terça-feira comum.

Você pensaria que é só botar mais computadores e vai mais rápido. É exatamente aí que o palpite da maioria das pessoas para, e é um palpite perfeitamente sensato. É também onde o problema de verdade começa, porque computadores, que nem gente, são péssimos em trabalhar juntos sem muita ajuda.

<div class="split">
  <div>
    <h3>O problema do trabalho em grupo</h3>
    <p>Imagina um trabalho em grupo onde todo mundo tem que estar na mesma página, o tempo todo. Você divide as tarefas, mas agora todos têm que parar e comparar anotações de novo e de novo. Coordena mal e oito pessoas de algum jeito terminam mais devagar que uma. Computadores são exatamente assim.</p>
  </div>
  <div>
    <h3>Onde meu trabalho de verdade está</h3>
    <p>Então o trabalho quase nunca é "compra mais máquinas". É fazer elas conversarem entre si sem tropeçar nos próprios pés: quem faz qual pedaço, quando dão notícia, e como manter todo mundo ocupado em vez de parado esperando.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# O número que importa mais que a velocidade pura

> O verdadeiro prêmio é encurtar a espera entre "tive uma ideia" e "consigo ver se funcionou", de uma pausa pro café pra um respiro.

Parece só uma comodidade. Mas na verdade muda o jeito como as pessoas pensam. Quando o retorno leva vários minutos, você fica cauteloso, junta seus palpites, para de experimentar porque cada tentativa custa um tempo real. Quando leva segundos, você simplesmente tenta.

Retorno rápido não deixa só as pessoas mais rápidas. Deixa elas mais corajosas. É essa a coisa que eu de fato vendo, e quase ninguém de fora desse mundo imaginaria que uma plataforma inteira é construída em torno de algo tão humano quanto o tempo que as pessoas topam esperar.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Por Que Modelos Apodrecem

## A parte que ninguém te avisa: o modelo que estava certo mês passado está calado e errado hoje.

---

# O mundo se mexe. O modelo não.

Um modelo aprende com o passado. É esse o truque inteiro e também o problema inteiro, porque o passado é a única coisa que ele vai conhecer, e o mundo se recusa a ficar parado.

Os padrões de fraude mudam na semana seguinte a você pegá-los. Preços mudam. As pessoas mudam de comportamento. O modelo não percebe nada disso. Ele continua aplicando com confiança as regras de ontem ao mundo de hoje, e todos os painéis dizem que está rodando perfeitamente enquanto as respostas dele escorregam devagar de úteis pra erradas.

> Isso se chama drift, e é o vilão silencioso do campo inteiro. Nada trava. Nenhum alarme dispara. O modelo só vai piorando em completo silêncio até alguém pensar em conferir.

Então o trabalho nunca é "lança e esquece". É ficar de olho, pegar o drift, retreinar, relançar, e fazer tudo de novo, pra sempre.

---

# Fazendo tudo isso, pra muitos modelos ao mesmo tempo

Agora imagina tudo do slide anterior, mas pra centenas de modelos ao mesmo tempo, e sem um exército de gente segurando na mão de cada um. Meu canto da área tem um nome feio pra isso, "MLOps", mas no fundo só quer dizer deixar as partes chatas e repetitivas automáticas e confiáveis.

<div class="card-row">
  <div class="card">
    <h3>Linhas de montagem</h3>
    <p>Em vez de uma pessoa clicando em cada atualização na mão, os passos chatos rodam sozinhos numa agenda. Um humano decide o que deve acontecer; a máquina cuida do trabalho tedioso de fazer acontecer.</p>
  </div>
  <div class="card">
    <h3>Uma receita escrita</h3>
    <p>O setup inteiro está escrito passo a passo, tipo manual de montar móvel, pra qualquer um conseguir reconstruir ou achar um erro. A alternativa é ele viver só na cabeça de uma pessoa e numa pasta de scripts frágeis que quebram se você olhar torto.</p>
  </div>
  <div class="card">
    <h3>Reconstruindo em pleno voo</h3>
    <p>Boa parte do meu trabalho recente é trocar as fundações enquanto centenas de pessoas continuam usando a coisa todo dia. É um pouco como trocar o motor de um avião sem pousar o avião.</p>
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Como Cheguei Aqui

## Eu tenho um diploma de economia e estudei numa escola de fazer videogame. Isso não era um plano.

---

# O caminho não fazia sentido até fazer

Eu me formei em economia na faculdade. Antes disso, um ensino técnico de fazer videogame. Nenhum dos dois é a pista de decolagem óbvia pra uma carreira em infraestrutura de machine learning, o que é mais ou menos o ponto.

<div class="split">
  <div>
    <h3>Onde começou</h3>
    <p>Meu primeiro trabalho de verdade foi ler texto aberto de pesquisas com um modelo de linguagem antigo, numa época em que explicar "IA" num jantar rendia um olhar vazio em vez de uma opinião. Depois anti-fraude, que é onde aprendi que um modelo só é tão bom quanto o sistema que o sustenta.</p>
  </div>
  <div>
    <h3>O que de fato foi pro ar</h3>
    <p>Aquele trabalho de anti-fraude barrou uma quantidade relevante de fraude a um custo minúsculo por checagem. O que ficou comigo foi a lição, não o número: o modelo importava, e a máquina em volta dele importava mais.</p>
  </div>
</div>

O fio condutor não é um diploma. É um gosto específico pela metade sem glamour do problema, a metade que decide se a parte esperta um dia chega numa pessoa de verdade.

---

<!-- _class: emphasis -->

# O que eu quero que meus amigos levem daqui

> Isso é um ofício, não um dom. É mais perto de ser um encanador teimoso do que um gênio solitário. O romance é opcional. A confiabilidade não é.

A área se enrola num mistério porque mistério vende, e por um tempo eu também quase acreditei. Mas tirando isso, é artesanato: constrói a coisa, deixa rápida, mantém honesta, e esteja lá quando quebrar. Dá pra aprender, é sem glamour, e é silenciosamente satisfatório do jeito que todo ofício de verdade é.

Você não precisa de doutorado nem da permissão de ninguém pra começar. Eu com certeza não tinha nenhum dos dois.

---

# O laboratório em casa, e por que ele existe

Tem duas placas de vídeo zumbindo no meu apartamento agora, sem ninguém pagando por isso. Eu montei essa maquininha de propósito.

<div class="split">
  <div>
    <h3>Não pra ser rápido</h3>
    <p>Ela nunca vai ganhar nenhuma competição de velocidade, e nunca foi essa a ideia. Ela está ali pra eu poder ver dois chips tentando aprender uma coisa juntos, bem na minha frente, e de fato entender por que fica lento em vez de só ler que fica.</p>
  </div>
  <div>
    <h3>Pra realmente entender</h3>
    <p>Esse trabalho recompensa curiosidade muito mais do que qualquer diploma. Você aprende como a versão gigante funciona construindo uma versão minúscula que você entende por inteiro, quebrando de propósito, e consertando. O aprendizado genuinamente nunca para, o que é a melhor e a mais cansativa parte.</p>
  </div>
</div>

Isso, numa única máquina que aquece o apartamento, é o trabalho inteiro. Construir a coisa sem glamour que faz a coisa esperta virar real, e continuar curioso o suficiente pra reconstruir de novo.

---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# Obrigado

## Perguntas são bem-vindas, principalmente as ingênuas

dan.rio | github.com/danielcavalli
