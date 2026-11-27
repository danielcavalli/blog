---
title: Como funciona o sistema de tradução v2
excerpt: O sistema de tradução v2 é a segunda tentativa séria de tornar este blog bilíngue sem fazer o português soar como inglês importado. Foi preciso mais do que um modelo melhor.
tags:
- tradução
- localização
- llms
- arquitetura de software
- pt-br
lang: pt-br
translation_of: how-translation-system-v2-works.md
source_digest: 67d0013eda90ad70d00d3ac94a8cc035803195254bdec8bcc3a058293de9c9e0
translated_by: openai/gpt-5.6-sol (high), via opencode
translated_at: '2026-09-05'
---

A versão original deste sistema foi construída em 2024, embora só tenha assumido de vez o blog em 2025. Isso importa porque 2024 era um momento muito diferente para projetar esse tipo de sistema. Os modelos eram mais fracos, fluxos de trabalho longos baseados em agentes eram menos confiáveis, e o instinto sensato era manter restrito o escopo do sistema. Traduza o post, preserve o Markdown, guarde o resultado em cache e siga em frente.

Aquele sistema fazia exatamente o que tinha sido projetado para fazer. Infelizmente, fui eu que o projetei.

Ele conseguia produzir traduções estruturalmente corretas e semanticamente compreensíveis. Se tudo o que eu quisesse fosse transportar o sentido, isso teria bastado. O problema é que nunca foi isso que eu quis. Eu queria que a versão em português do blog parecesse escrita de verdade, não uma prova de que um modelo identificou corretamente os substantivos.

É nessa diferença que começa o redesenho. É também aí que a versão anterior fica sem desculpas.

O sistema antigo muitas vezes preservava a informação e danificava o texto. O sentido sobrevivia. A voz, não. O tecido conectivo entre as ideias ficava mais fino. Empréstimos do inglês no português brasileiro eram tratados como se cada ocorrência fosse uma nova questão filosófica. Uma frase que, no original, estabelecia credibilidade, suavizava uma discordância e fazia uma piada ao mesmo tempo voltava em português dando conta de uma dessas funções com confiança comedida. Na maioria das vezes, da errada.

Em algum momento, parei de tratar isso como um problema de tradução. Era claramente um problema de sistema. A v2 não foi construída como um prompt melhor. Foi construída como outro sistema, com outras premissas sobre o que o trabalho realmente é.

## O pecado original não era a qualidade do modelo

Seria conveniente culpar os modelos disponíveis na época por tudo. Isso absolveria a arquitetura anterior com facilidade demais. Infelizmente, o próprio projeto fazia parte do problema.

O pipeline antigo se comportava como se a qualidade fosse emergir de um cuidado suficiente com a estrutura. Mantenha o Markdown intacto. Proteja blocos de código. Reutilize o cache. Peça ao modelo que soe natural. Talvez faça uma revisão. Tudo isso é defensável se a sua principal preocupação é não quebrar o artefato. É bem menos defensável se a sua principal preocupação é saber se um leitor brasileiro acreditaria que a versão em português foi escrita pela mesma pessoa.

A distinção importa porque "compreensível" é uma régua perigosamente baixa. Muito texto traduzido é compreensível. Um e-mail de suporte ao cliente gerado por máquina também é. Isso não diz quase nada sobre se o texto chegou vivo do outro lado.

O problema, em outras palavras, não era que o sistema antigo falhasse de um jeito espetacular. Ele falhava educadamente. Essas são as falhas perigosas. Um sistema que explode pelo menos costuma ter a gentileza de envergonhar você. Um sistema que produz uma saída plausível pode desperdiçar muito mais tempo.

## Tudo começa no build, não na prosa

A primeira mudança séria na v2 não é linguística. É operacional.

O build agora é orientado pelo original. Ele gera as páginas no idioma de origem antes de a tradução começar e persiste o trabalho de tradução aceito na fronteira do artefato, não no fim nebuloso do build inteiro. Isso parece trabalho de infraestrutura sem glamour, e é mesmo, mas também corrige um dos modos de falha mais irritantes do sistema anterior.

O contrato do build agora está mais próximo disto:

```text
parse -> build source output -> translate -> accept -> cache -> artifacts -> rendered output
```

É um contrato melhor do que "faça um monte de trabalho, mantenha parte dele na memória e torça para nada importante falhar depois".

A consequência prática é simples. Se é possível gerar uma página no idioma original, ela deve ser gerada. Se um artefato traduzido é aceito, ele deve ser persistido imediatamente. Uma falha posterior em alguma outra parte da execução não deveria apagar trabalho que já deu certo. Antes, isso acontecia com frequência suficiente para ser caro e ofensivo.

Isso também dá ao build uma estrutura mais clara. O conteúdo-fonte agora é uma saída de primeira classe, não algo que por acaso existe antes de a lógica de tradução se empolgar. Parece óbvio em retrospecto. As boas correções geralmente parecem.

## Seis estágios, principalmente porque o sistema antigo mentia sobre um deles

O caminho da tradução em si também é mais explícito do que costumava ser. Em vez de uma instrução geral para traduzir e talvez se comportar, a v2 divide o trabalho em seis estágios:

```text
source_analysis
terminology_policy
translate
critique
revise
final_review
```

Isso não é inflação de estágios. É admitir que o pipeline antigo tentava fazer vários trabalhos diferentes com uma instrução vaga e depois fingia surpresa quando alguns deles saíam mal.

Se isso parece complexo demais, eu entendo o instinto. Eu também tive esse instinto. A história mais limpa é sempre que um modelo forte deveria conseguir ler um post, traduzi-lo, perceber o que errou e se corrigir. É um instinto razoável. Também foi, grosso modo, até onde o sistema antigo chegou. O problema é que esses são trabalhos diferentes. Mais importante: eles falham de jeitos diferentes. Depois que você aceita isso, separá-los começa a parecer menos cerimônia e mais honestidade básica.

### Análise do original

O primeiro estágio tenta entender o original como escrita, não como conteúdo portátil. Ele extrai tom, registro, ritmo das frases, hábitos conectivos, movimentos retóricos, sinais de humor e as partes do texto que precisam absolutamente sobreviver à localização.

Isso pode soar suspeitamente literário para um pipeline de build. Também é verdade. Se o sistema não consegue distinguir entre uma frase que apenas afirma um fato e outra que, discretamente, argumenta, administra o tom e constrói credibilidade ao mesmo tempo, os estágios seguintes trabalham quase às cegas e cheios de confiança, o que não é uma melhoria.

O sistema antigo tratava isso quase como preferência estilística no prompt. O atual trata como memória de trabalho.

### Política terminológica

O segundo estágio resolve terminologia e empréstimos antes de qualquer rascunho ser escrito.

Isso é uma daquelas coisas que soam burocráticas até você ver o que acontece sem uma política assim. Na tradução técnica do inglês para o português brasileiro, há termos que devem permanecer em inglês, termos que obviamente devem ser localizados e termos que dependem de contexto, público e registro. Se o modelo toma essas decisões uma ocorrência por vez, a saída começa a soar socialmente errada mesmo quando o sentido está intacto.

Esse é um modo de falha muito comum em localização. Também é o tipo de coisa que falantes de inglês costumam subestimar, porque o texto continua legível para eles. Brasileiros, infelizmente para o sistema, também sabem ler, e alguns de nós ainda somos vingativos o bastante para notar quando "português natural" está fazendo uma imitação muito convincente de inglês traduzido.

Esse estágio decide o que deve ficar em inglês, o que deve ser localizado, o que continua dependente de contexto e o que não deve ser traduzido de jeito nenhum. Mais importante: resolve casos ambíguos no nível do artefato, em vez de espalhar dicas pelo prompt e esperar que o resultado tenha personalidade.

### Tradução

Só então o sistema produz um rascunho.

O estágio de tradução atualmente usa `GPT-5.4` com esforço de raciocínio alto. Não é porque eu goste de números caros. É porque esta é a parte do fluxo de trabalho que de fato precisa reescrever. Um modelo mais barato pode falhar de maneiras muito criativas aqui e ainda assim parecer útil.

A mudança principal, porém, não é só a escolha do modelo. O tradutor não recebe mais a tarefa de preservar a forma superficial, mas o efeito. Se uma frase precisa ser reconstruída para soar como português autoral, em vez de inglês atravessado pela fronteira com a papelada em dia, então a frase é reconstruída. A questão é preservar a escrita, não a cena do crime.

É aqui que a tradução começa a virar localização, em vez de cópia bilíngue.

### Crítica

A crítica agora existe como estágio diagnóstico real, não como carimbo educado.

Ela avalia o rascunho em várias dimensões: fidelidade factual, consistência terminológica, integridade do Markdown e dos trechos protegidos, naturalidade em PT-BR, consistência no uso de empréstimos e estrutura retórica.

Esse estágio roda em `GPT-5.2`. Eu prefiro essa divisão. Tradução e revisão são trabalhos gerativos. A crítica é um trabalho diagnóstico. Eles se beneficiam de hábitos diferentes, e não há motivo especial para obrigar o mesmo modelo a fazer tudo só porque ele consegue.

Além disso, se um pipeline vai mentir, eu prefiro que minta em menos vozes.

### Revisão

A revisão existe porque uma boa crítica não é a mesma coisa que uma boa reescrita.

Um problema de pipelines de tradução mais fracos é que eles assumem, silenciosamente, que o primeiro rascunho precisa estar quase certo para o fluxo de trabalho dar certo. Isso deixa o sistema inteiro frágil. A v2 trata a revisão como um estágio de reescrita de primeira classe. Se a crítica diz que o texto ainda soa traduzido, a resposta não é trocar alguns termos e se parabenizar por respeitar a estrutura. A resposta é reescrever a frase ou o parágrafo direito.

Tradução e revisão usam `GPT-5.4` com esforço de raciocínio alto exatamente por esse motivo. É aqui que o sistema faz o trabalho estilístico mais difícil.

### Revisão final

A revisão final é a aprovação que vale.

Esse estágio verifica se o artefato revisado é fiel, soa nativo no idioma de destino, mantém a consistência interna e a estrutura intacta e ainda é reconhecível como texto do autor. Também confere se os achados da crítica foram de fato resolvidos, em vez de apenas reconhecidos em tom confiante.

Isso torna a arquitetura mais entediante do que a expressão "fluxo de trabalho de tradução multiagente" talvez sugira. Para mim, isso é elogio. Sistemas melhoram quando a parte impressionante sai do nome e vai para o comportamento.

## O PT-BR precisava de uma camada de política, não de uma palestra motivacional

A maior melhoria recente do sistema é a camada de localização PT-BR.

Ela estava ausente havia tempo demais.

Versões anteriores dos prompts já continham variações de "soe natural em português brasileiro", uma daquelas instruções que conseguem ser verdadeiras e inúteis ao mesmo tempo. O sistema precisava de algo muito mais específico. Por isso, agora ele incorpora diretrizes de localização PT-BR como componente de primeira classe, além de convenções explícitas para empréstimos, pontuação, encadeamento discursivo, registro e critérios de revisão.

A política de empréstimos é a parte mais óbvia. O português técnico brasileiro não é simplesmente português com alguns substantivos em inglês deixados no meio. Ele tem convenções, hábitos e expectativas da comunidade. Alguns termos permanecem em inglês porque é assim que leitores técnicos brasileiros realmente os usam. Alguns são naturalmente localizados. Outros dependem do contexto. Nomes de produto e termos de marca formam outra categoria. Tratar tudo isso como uma sequência de escolhas lexicais isoladas produz um texto gramatical e ligeiramente constrangedor, uma das combinações menos úteis em software.

Pontuação e discurso importam tanto quanto. O português não se limita a traduzir orações do inglês. Muitas vezes, ele as reorganiza. Lida com pausas de outro jeito. Usa o travessão de outro jeito. Admite outros encadeamentos discursivos. Se um sistema preserva a ordem das orações em inglês e apenas troca o vocabulário, o resultado pode ser perfeitamente compreensível e ainda assim parecer importado.

É por isso que as diretrizes de localização agora codificam coisas que as versões anteriores deixavam ao instinto do modelo. É também por isso que a crítica e a revisão final pontuam explicitamente a naturalidade em PT-BR, a consistência dos empréstimos e a estrutura retórica, em vez de fingir que tudo isso cabe em um simpático número chamado fluência.

## O cache continua lá, mas agora se comporta como parte de um sistema

O cache de tradução ainda vive em `_cache/translation-cache.json`. Eu não o substituí por algo mais na moda porque não havia motivo real para isso. Trocar uma ideia quebrada por um termo da moda é um dos hábitos menos produtivos em software, e este sistema já tinha sofrido o bastante com ideias fingindo ser soluções.

O que mudou foi a relação do cache com o restante do pipeline.

Agora existem, na prática, três camadas de persistência: o cache de tradução, os artefatos de cada execução em `_cache/translation-runs/...` e a saída renderizada do site. Essas camadas fazem trabalhos diferentes. O cache existe para reuso. Os artefatos de execução existem para inspeção. A saída renderizada existe porque, em algum momento, um leitor precisa de uma página. Versões anteriores do sistema misturavam essas responsabilidades a ponto de um trabalho concluído ainda não parecer realmente preservado. A v2 é mais rígida quanto a essas fronteiras.

Também existe agora uma distinção mais sensata entre "acerto de cache" e "estado em que eu confio". Se há uma tradução no cache, mas o HTML traduzido e renderizado está ausente, o sistema não renderiza silenciosamente a página de novo a partir do cache e se dá por satisfeito. Ele marca o artefato para revisão e o envia de volta pelo fluxo de trabalho normal.

Esse é o comportamento certo. Uma saída ausente não é apenas uma inconveniência de renderização. É evidência de que o estado do artefato é inconsistente. Encobrir isso em silêncio faria o sistema parecer mais calmo enquanto o tornaria menos confiável. Sistemas calmos são maravilhosos. Sistemas que fingem calma geralmente não são.

## A divisão de modelos é prática, não mística

As atribuições atuais de modelo são:

- `GPT-5.4` com esforço de raciocínio alto para tradução
- `GPT-5.2` para crítica
- `GPT-5.4` com esforço de raciocínio alto para revisão
- `GPT-5.2` para revisão final

Isso não é uma declaração metafísica sobre qual modelo entende prosa com mais profundidade. É simplesmente uma declaração sobre como eu quero dividir o trabalho.

Tradução e revisão exigem capacidade sustentada de reescrita. Crítica e revisão final exigem julgamento estruturado, consistência e distância suficiente do rascunho para rejeitá-lo quando necessário. Não há motivo para que os dois tipos de trabalho sigam o mesmo caminho. Na prática, separá-los também torna o pipeline inteiro mais fácil de entender quando algo dá errado. Não tem glamour, mas costuma ser o que importa.

## O trabalho futuro começa onde sistemas no nível da frase ficam sem desculpas

A v2 é muito melhor do que o sistema que ela substituiu. Também não é o ponto final.

Há pelo menos quatro direções que levariam o sistema significativamente adiante, e nenhuma delas se resume a escrever um prompt ainda mais rígido.

### Coerência em nível de documento

A maioria dos sistemas práticos de tradução ainda se parece demais com tradutores de frases acompanhados de papelada extra. A pesquisa em tradução automática em nível de documento vem apontando para a mesma coisa há anos: um contexto mais amplo ajuda na coerência, na consistência e na interpretação discursiva, mesmo que usá-lo bem seja mais difícil do que simplesmente concatenar frases vizinhas.

Do ponto de vista do prompt, o sistema atual já trabalha no nível do artefato, o que é melhor do que isolar cada frase. Ainda assim, ele ainda não mantém um modelo interno robusto de coerência em nível de documento. Uma versão futura deveria tratar mais explicitamente da continuidade entre parágrafos, de estruturas argumentativas recorrentes, da resolução de pronomes e da maneira como a força retórica se acumula ao longo de um post inteiro, não apenas dentro de um trecho local.

### Avaliação ao estilo MQM

A qualidade de tradução tem o péssimo hábito de virar discussão baseada em achismo. MQM é útil justamente porque recusa essa saída de emergência. Ele oferece uma tipologia estruturada de erros e obriga a discussão a passar por categorias que podem ser comparadas, acompanhadas e debatidas direito.

Este sistema deveria, em algum momento, adotar algo parecido com MQM para sua camada interna de avaliação. Não o framework inteiro por obrigação religiosa, mas a disciplina básica de classificar os tipos de falha de qualidade. Hoje, o pipeline já pontua fidelidade, terminologia e naturalidade em PT-BR. O próximo passo é classificar os modos de falha com mais rigor:

- calque
- inconsistência de empréstimos
- falta de naturalidade em PT-BR
- achatamento retórico
- desvio estrutural
- falha de proteção

Isso tornaria o sistema muito mais fácil de melhorar, porque me diria não apenas que uma tradução falhou, mas que tipo de falha foi e se a mesma falha continua voltando nos mesmos lugares.

### Metadados de localização mais ricos no original

O trabalho de internacionalização e localização do W3C é útil aqui por um motivo simples. Ele trata a anotação de conteúdo como parte do sistema, em vez de fingir que todo localizador deveria reconstruir a intenção a partir da prosa e torcer.

Este blog não precisa de marcação industrial de localização amanhã de manhã, mas consigo imaginar facilmente uma versão futura com metadados mais ricos associados ao original: termos protegidos, candidatos a glossário, notas sobre o idioma de destino e indicações do autor sobre registro e empréstimos. Isso seria mais limpo do que forçar cada decisão posterior a ser inferida novamente a partir do mesmo texto.

### Memória de tradução confiável

A memória de tradução só é tão boa quanto aquilo que você permite entrar nela. Plataformas de localização entendem isso muito bem, e é por isso que saídas revisadas costumam receber tratamento privilegiado em comparação com rascunhos gerados por máquina.

O cache atual já se comporta muito melhor do que o antigo, mas ainda há uma distinção útil a fazer entre "aceito em uma execução" e "bom o suficiente para virar memória de localização durável". Uma política futura mais rigorosa poderia separar o cache temporário do fluxo de trabalho da memória de tradução aprovada. A segunda provavelmente deveria ser alimentada apenas por saídas que tenham passado por toda a cadeia de revisão com confiança suficiente para merecer reuso, não mera sobrevivência.

Isso tornaria a camada de memória menos permissiva e, como resultado, mais confiável.

## O que mudou foi o que o sistema acha que está fazendo

Essa, no fim, é a diferença real.

O pipeline original tratava a tradução como um problema restrito de transformação de texto. A v2 trata a tradução como trabalho de localização dentro de um sistema de build que precisa preservar a escrita autoral, sobreviver a falhas e continuar inspecionável quando algo dá errado. Não se trata do mesmo problema; portanto, não se chega à mesma arquitetura.

A reconstrução não aconteceu porque eu de repente me interessei por transformar um tradutor de blog em uma pequena burocracia. Ela aconteceu porque o sistema mais simples continuava falhando do mesmo jeito. Ele me entregava texto bom o bastante para um benchmark feito à própria imagem e ruim o bastante para um leitor que é uma pessoa de verdade. Depois de um tempo, isso deixa de parecer um problema de modelo e começa a parecer cumplicidade.

Esse não é um tipo muito útil de sucesso.

A v2 é melhor porque é mais explícita. Tem estágios mais claros, semântica de durabilidade mais clara, política de PT-BR mais clara, critérios de rejeição mais claros e ideias mais claras sobre o que ainda permanece sem solução. Essa última parte importa mais do que parece. Sistemas de tradução ficam perigosos justamente quando são bons o bastante para soar como se estivessem prontos, porque esse é o ponto em que as pessoas param de checá-los com cuidado e começam a perdoá-los profissionalmente.

Este aqui não está pronto. Mas finalmente é honesto sobre o trabalho que está fazendo. Por enquanto, isso basta. Não para as traduções, infelizmente. Para o sistema.

## Fontes e leituras complementares

- [Google Developer Documentation Style Guide, "Escreva para um público global"](https://developers.google.com/style/translation)
- [Microsoft Style Guide, "Dicas de escrita"](https://learn.microsoft.com/pt-br/style-guide/global-communications/writing-tips)
- [W3C, Requisitos de marcação para internacionalização e localização](https://www.w3.org/TR/itsreq/)
- [MQM, Métricas Multidimensionais de Qualidade](https://themqm.org/)
- [Zheng et al., "Rumo a aproveitar melhor o contexto na tradução automática neural"](https://www.ijcai.org/Proceedings/2020/551)
- [Nayak et al., "Investigando a influência contextual na tradução em nível de documento"](https://www.mdpi.com/2078-2489/13/5/249)
- [Tan, Zhang, Zhou, "Tradução automática neural em nível de documento com modelagem hierárquica de contexto global"](https://jcst.ict.ac.cn/article/cstr/32374.14.s11390-021-0286-3)
- [Transifex, "Introdução à memória de tradução"](https://help.transifex.com/en/articles/6224636-introduction-to-translation-memory)
