---
title: O Sistema Estático Vivo
excerpt: 'Por dentro de um site estático bilíngue que se move como uma superfície única: um build em Python, um pipeline de tradução e transições nativas que mantêm o espaço contínuo.'
tags:
- Desenvolvimento Web
- View Transitions API
- Sites Estáticos
- Python
lang: pt-br
translation_of: the-living-static-system.md
source_digest: 7e8a1b91b77eb4e1c0a10b39f65c85a6ba24a297152e2db46709cf552aef8165
translated_by: openai/gpt-5.4, via opencode
---

O sistema começou com uma pergunta: quão pouco um blog precisa para parecer vivo. Não animado por mero capricho, mas vivo como a maré avança: inevitável, contínuo, sem bordas. O que surgiu daí foi um gerador estático que escreve dois espelhos de si mesmo, um em inglês e outro em português, e uma camada fina de movimento que jamais rompe a superfície. As páginas não são trocadas. O espaço se reorganiza.

## O Pipeline de Build

O build é um único passe deliberado. O Markdown entra por uma porta estreita. O front matter é lido, o conteúdo é analisado e um modelo de página é montado com estrutura suficiente para renderizar exatamente o que é necessário e nada além disso. O script não orquestra um framework. Ele compõe arquivos.

Dentro de `_source/build.py`, os posts são descobertos percorrendo o diretório `_source/posts`. Cada arquivo Markdown é analisado com a biblioteca `frontmatter`, que separa os metadados YAML do corpo do conteúdo. O corpo passa pela biblioteca `markdown` do Python, com extensões para blocos de código delimitados e tabelas. O que sai do outro lado é HTML limpo, envolto em um template que sabe exatamente onde o título entra, onde a data repousa e como a navegação deve respirar.

O único cache que importa é o que respeita a mudança. Um hash de conteúdo é calculado a partir da fonte em inglês com MD5, e toda transformação que vem depois herda essa decisão. O hash vive no próprio front matter, regravado no arquivo Markdown depois da análise:

```python
def parse_markdown_post(filepath):
    post = frontmatter.load(filepath)
    content_hash = calculate_content_hash(post.content)
    
    stored_hash = post.get('content_hash')
    needs_update = False
    
    if not created_at:
        # New post - set creation date
        post['created_at'] = now
        post['content_hash'] = content_hash
        needs_update = True
    elif stored_hash != content_hash:
        # Content changed - update timestamp
        post['updated_at'] = now
        post['content_hash'] = content_hash
        needs_update = True
```

Quando nada muda, nada é refeito. Quando uma frase se desloca, o pipeline desperta e se move com ela. O script de build escreve em dois diretórios de saída, `/en` e `/pt`, ambos na raiz do projeto. Os dois são sites completos. Os dois têm o mesmo estatuto. Não há fallback nem requisição em tempo de execução.

## Tradução como Espelho

Tradução não é decoração. É uma segunda superfície traçada pela mesma mão. O inglês entra, e o português sai pelo Gemini, sob restrições que preservam blocos de código, terminologia técnica e o tom do original.

O tradutor é inicializado com uma chave de API vinda do ambiente. Ele mantém um arquivo de cache JSON em `_cache/translation-cache.json`, indexado pelo slug de cada post e pelo hash de conteúdo. A regra é simples: se o texto-fonte não mudou, a tradução continua valendo. Se o hash diverge, uma nova tradução é solicitada e o cache é atualizado de forma atômica.

O prompt de tradução não é uma instrução simples. É um contrato:

> Você é um redator técnico brasileiro bilíngue traduzindo um post de blog em inglês para um português brasileiro natural e localizado. Sua tarefa não é fazer uma tradução literal, mas localizar o texto, transformando-o em algo que soe como se tivesse sido escrito originalmente em português pelo mesmo autor.

O prompt segue com princípios: preservar termos técnicos que brasileiros usam em inglês, como `framework`, `build`, `pipeline` e `deploy`, mas localizar o conteúdo narrativo e pessoal para soar fluente e culturalmente preciso. O tradutor respeita o veio do original enquanto faz cada frase respirar com naturalidade na segunda língua.

```python
translated = translator.translate_post(
    slug, frontmatter, content
)
```

O resultado vai para o cache, e o build seguinte pula completamente a chamada à API. É assim que um site bilíngue pode ser refeito em segundos, e não em minutos. O cache é a memória do que já foi dito.

## Navegação como Espaço Contínuo

A navegação se comporta como se o documento fosse um único plano aprendendo novas formas. No navegador, a View Transitions API não é um efeito especial. É a memória do antes e do depois. O novo HTML é buscado com antecedência. A troca acontece dentro de um único callback síncrono, e o navegador captura dois estados do mesmo espaço. O código é pequeno porque o navegador faz exatamente aquilo para o qual foi feito.

A função `navigateTo` em `static/js/transitions.js` intercepta cliques em links internos. Ela busca a nova página, a analisa como um fragmento de documento e prepara a troca. Antes de a transição começar, remove os atributos `view-transition-name` dos cards de post no novo documento. Isso impede que o navegador crie pseudo-elementos extras que piscariam durante a limpeza. Então a transição começa:

```javascript
const transition = document.startViewTransition(() => {
  document.title = newDoc.title;
  
  const main = document.querySelector('main');
  const newMain = newDoc.querySelector('main');
  if (main && newMain) main.replaceWith(newMain);
  
  history.pushState(null, '', url);
  window.scrollTo({ top: 0, behavior: 'instant' });
});

await transition.finished;
```

A coreografia está escrita em CSS, não em JavaScript. O código acima apenas decide quando a superfície deve se lembrar. Todo o resto mora nos estilos: curvas de easing compartilhadas entre interações, durações que rimam entre si e pseudo-elementos `::view-transition` que permitem aos títulos mudar de forma sem nunca desaparecer. As constantes de movimento ficam reunidas num só lugar e não entram em negociação com o resto do design:

```css
:root {
  --motion-duration-core: 500ms;
  --motion-duration-quick: 300ms;
  --motion-duration-ripple: 600ms;
  --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}
```

Toda interação no site usa essas variáveis. Cards de post se erguem no hover por 300ms. Transições de tema ondulam por 600ms. Transições de página se transformam em 500ms. Essa consistência não é acidente. É o som do mesmo relógio marcando o tempo em toda parte.

## Filtragem sem Sobressaltos

Os cards da página inicial aprendem a se comportar como bons cidadãos. Sua primeira obrigação é aparecer e depois ficar parados. Ordenação e filtragem são feitas com FLIP, não no susto. FLIP significa First, Last, Invert, Play: medir onde cada card começa, aplicar o filtro ou a ordenação, medir onde cada card termina e então animar a diferença.

A implementação em `static/js/filter.js` captura os retângulos iniciais de todos os cards visíveis, aplica a lógica de filtro para esconder ou mostrar cards e depois captura as posições finais. Cada card que se moveu recebe um `transform` em CSS para ser invertido de volta à posição inicial, e então esse `transform` é removido ao longo da duração da animação. O card parece deslizar com suavidade da posição antiga para a nova.

```javascript
const rects = new Map();
cards.forEach(card => {
  rects.set(card, card.getBoundingClientRect());
});

// Apply filter (hides/shows cards, layout reflows)
applyFilter();

cards.forEach(card => {
  const oldRect = rects.get(card);
  const newRect = card.getBoundingClientRect();
  const dx = oldRect.left - newRect.left;
  const dy = oldRect.top - newRect.top;
  
  card.style.transform = `translate(${dx}px, ${dy}px)`;
  requestAnimationFrame(() => {
    card.style.transition = 'transform 500ms var(--motion-easing)';
    card.style.transform = 'none';
  });
});
```

O grid nunca salta. Ele exala. Quando a navegação chega de outro lugar, a revelação inicial em keyframes é pulada por completo. O script detecta esse caso verificando se `document.referrer` aponta para a mesma origem. Se aponta, assume que o usuário veio de outra página do próprio site e desativa imediatamente a animação de entrada ao adicionar `disable-animation` ao grid de posts e definir `animation: none` em cada card. O resultado é silencioso: nada pisca, nada reinicia, nada tenta se impor depois do fato.

## Troca de Idioma como Camada de Tradução

Uma das continuidades mais sutis do sistema está na sensação da troca de idioma. Quando você clica no alternador de idioma, não está saindo da página. Está traduzindo a superfície que já estava lendo. A posição de rolagem é preservada. O estado do filtro é preservado. A URL muda de `/en/index.html` para `/pt/index.html`, mas o seu lugar no documento não.

Isso é tratado em `transitions.js` detectando uma troca de idioma: a estrutura do caminho é idêntica, com exceção do segmento `en` ou `pt`. Se esse padrão é detectado, a posição de rolagem é capturada antes do fetch e restaurada depois da troca no DOM. Se você estava no meio de um artigo longo em inglês e muda para português, continua no meio do mesmo artigo. O conteúdo muda, mas o espaço não.

O mesmo princípio se estende ao estado de filtro na página inicial. Se você filtrou posts por ano ou por tag e troca de idioma, o filtro continua ativo. Os posts traduzidos aparecem, mas os critérios de seleção são preservados. É assim que um site bilíngue passa a parecer um único documento visto por duas lentes, e não dois sites separados.

## Personalização sem Estrutura Inicial

A personalização respeita o veio do sistema. A porta de entrada é configuração e texto, não estrutura inicial. Abra `_source/config.py` e você encontrará tudo o que pode mudar: caminho base, definições de idioma, metadados do site e strings de interface para os dois idiomas. Mude o caminho base, e o build passa a escrever links de acordo com ele. Ajuste as variáveis tipográficas em `static/css/styles.css`, e a superfície inteira se fecha ou se abre com a mesma medida.

O conjunto de idiomas é a única suposição realmente embutida. O inglês é a referência canônica. O português é uma tradução fiel. Se um terceiro idioma for necessário, a regra se estende: adicione um segundo espelho, dê a ele um cache, mantenha os hashes honestos. O builder é um script que se lê de uma vez só. Se você consegue lê-lo, consegue mudá-lo. Não há mágica. Não há camadas escondidas. O sistema tem exatamente a complexidade do problema que resolve.

## Por que não usar um framework

Recusar um framework aqui não é nostalgia. É alinhamento com o problema. Um blog é texto, algumas imagens e a sensação de que atravessá-lo deve parecer virar uma página sem perder a linha que você estava lendo. As capacidades nativas do navegador já bastam. Python já basta. As dependências são escolhidas como ferramentas sobre uma bancada pequena: se uma delas não deixa o corte mais limpo, fica na gaveta.

A ausência de maquinário não é ideologia. É manutenção praticada de antemão. Cada linha de código neste sistema é uma linha que eu vou precisar reler daqui a seis meses ou seis anos. Cada dependência é uma incompatibilidade futura em potencial. Toda abstração cobra um imposto da compreensão. Por isso o sistema permanece pequeno. Permanece legível. Permanece mutável.

A View Transitions API é nativa do Chromium. Não exige polyfill, wrapper nem etapa de build. O navegador já sabe capturar dois estados do DOM e animar entre eles. Meu trabalho é decidir quando isso deve acontecer e impedir que o resto da página interfira. O CSS que descreve o movimento é declarativo. Ele se lê como uma partitura de coreografia, não como um programa.

As bibliotecas `frontmatter` e `markdown` do Python fazem exatamente uma coisa cada uma: analisar YAML e converter Markdown em HTML. Fazem isso bem. Não tentam ser sistemas de build. Não tentam ser roteadores. Elas analisam texto. É tudo o que eu preciso que façam.

## A Filosofia do Movimento

A filosofia do movimento é a filosofia da atenção. Nada deve se impor. As transições respondem a três perguntas: de onde, para onde e como este estado se relaciona com o anterior. Mudanças de tema passam como uma nuvem diante do sol. Um card se ergue alguns pixels no hover e depois volta ao repouso. A superfície nunca mente sobre o que se moveu, nem sobre o motivo.

Quando algo precisa ser removido, se dissolve ao longo de 500 milissegundos. Quando algo precisa chegar, surge de um lugar de onde plausivelmente poderia ter vindo. O card de post no índice se expande até virar o artigo completo. O título permanece no lugar e cresce. A data se ancora no canto. O layout respira para fora sem quebrar a continuidade. Quando você volta, o artigo se recolhe de novo no card. O espaço se conserva.

A curva de easing é a mesma em toda parte: `cubic-bezier(0.4, 0, 0.2, 1)`. Isso não é uma escolha aleatória. É o easing padrão do Material Design, escolhido porque parece natural à percepção humana. O movimento começa com intenção, acelera com suavidade e desacelera ao concluir. Nada estala. Nada desliza em velocidade constante. Tudo se move como se tivesse peso.

## O Contrato com o Leitor

Para quem quiser adaptá-lo, o contrato é pequeno e explícito. Markdown entra, HTML sai. Um tradutor que respeita código e voz. Uma camada de navegação que nunca bloqueia a renderização com trabalho que poderia ter sido feito antes. Estilos que codificam o ritmo uma vez e o reutilizam em toda parte. Se você mudar uma coisa, a sensação deve ser a de ter mudado exatamente uma coisa, e o resto do sistema deve responder com calma proporcional.

A única astúcia está em saber a hora de parar. O sistema poderia fazer mais. Poderia ter um CMS. Poderia ter preview em tempo real. Poderia ter analytics, A/B testing e widgets de compartilhamento social. Não faz nada disso porque nada disso melhora a experiência de leitura. O objetivo não é construir uma plataforma. O objetivo é escrever e deixar que a escrita seja lida sem interferência.

## O que o Sistema Sabe

Isto não é uma demonstração. É a versão mais simples de um documento vivo que consegui fazer sem mentir sobre o que a web já sabe fazer. Na maioria das noites, escrevo com as janelas abertas em Copacabana e o som da avenida se dobrando até o mar. O sistema aprende esse ritmo e o guarda. As coisas fluem não porque sejam rápidas, mas porque não criam obstáculos para si mesmas.

O cache se lembra do que não mudou. O tradutor preserva aquilo que não deve ser traduzido. A navegação mantém o ponto da página em que você estava quando o idioma muda. O sistema de movimento codifica quanto tempo as coisas devem levar e se recusa a discutir isso. Cada decisão que o sistema toma está a serviço de uma única ideia: o documento é contínuo. Quando você se move por ele, o espaço se reorganiza, mas nunca se rompe.

É isso que faz um site estático parecer vivo.
