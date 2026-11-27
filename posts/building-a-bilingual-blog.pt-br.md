---
title: O sistema estático vivo
excerpt: Um blog estático pode parecer vivo quando movimento, idioma, estado e manutenção são desenhados em torno da continuidade.
tags: []
lang: pt-br
translation_of: building-a-bilingual-blog.md
source_digest: 9c90eb0febc02c37cb7388234682e1d7a8bdb44ddfd5435a5be84613b9d0ea1a
translated_by: openai/gpt-5.5, via opencode
---

Este blog é uma plataforma construída com geração de site estático em Python, tradução automática via Gemini AI e transições de página fluidas usando a View Transitions API. Sem frameworks, sem dependências pesadas. Só padrões nativos da web fazendo trabalho de verdade. A arquitetura é simples o bastante para ser entendida em uma tarde, potente o bastante para parecer contínua em uso e pequena o bastante para ser mantida por uma pessoa só.

O objetivo do design não era criar o sistema de blog mais completo em recursos. Era criar o mais silencioso. Um lugar onde a escrita apareça sem cerimônia, onde navegar pareça reorganizar um espaço em vez de carregar novas páginas, e onde um segundo idioma surja com a mesma naturalidade do primeiro. Toda decisão técnica serve a esse objetivo.

## Geração Estática com Propósito

No centro há um script Python que lê arquivos markdown de `_source/posts` e escreve HTML em dois diretórios de saída: `/en` para inglês e `/pt` para português. O script usa `frontmatter` para interpretar metadados YAML e `markdown` para converter o conteúdo do corpo. Não há sistema de plugins, não há marketplace de temas, não há abstrações sobre abstrações. O script compõe arquivos. É só isso que ele precisa fazer.

Cada arquivo markdown contém front matter com título, data, excerpt e tags opcionais. O script percorre o diretório de posts, carrega cada arquivo, extrai os metadados, converte o markdown para HTML e injeta tudo em um template. O template não é um sistema separado. É uma f-string de Python que sabe onde fica a navegação, onde entra o título do post e como o rodapé deve fechar. O HTML de saída é escrito em disco com nomes de arquivo determinísticos derivados do slug do post.

```python
def generate_post_html(post, post_number, lang='en'):
    lang_dir = LANGUAGES[lang]['dir']
    current_page = f"blog/{post['slug']}.html"
    
    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
    <title>{post['title']} - dan.rio</title>
    <link rel="stylesheet" href="{BASE_PATH}/static/css/styles.css">
</head>
<body>
    <nav class="nav">...</nav>
    <main class="container">
        <article class="post">
            <h1>{post['title']}</h1>
            <div class="post-body">{post['content']}</div>
        </article>
    </main>
</body>
</html>"""
```

O build é determinístico. Rode duas vezes com a mesma entrada e você obtém uma saída byte a byte idêntica. Isso torna o cache trivial e os rebuilds previsíveis. O único estado que persiste entre builds é o cache de tradução, que vamos discutir daqui a pouco.

## Tradução como Conteúdo de Primeira Classe

Todo post é escrito em inglês. Todo post é traduzido automaticamente para português brasileiro usando o modelo Gemini 2.0 Flash, do Google. A tradução não é um detalhe posterior. Ela faz parte do processo de build, fica em cache por hash do conteúdo e só é regenerada quando a fonte em inglês muda.

O tradutor fica em `_source/translator.py`. Ele mantém um cache JSON em `_cache/translation-cache.json`, indexado por slug do post e hash do conteúdo. Antes de pedir uma tradução, o script verifica se o hash atual do conteúdo corresponde ao hash em cache. Se corresponder, a tradução em cache é usada. Se não, uma nova tradução é solicitada via Gemini API, e o cache é atualizado.

O prompt de tradução é cuidadoso. Ele instrui o modelo a localizar, não a traduzir literalmente. Termos técnicos que brasileiros usam em inglês, como `framework`, `backend`, `API`, `deploy` e `commit`, são preservados. Blocos de código ficam intocados. A voz narrativa é adaptada para soar natural em português, mantendo o mesmo tom e o mesmo ritmo do original.

```python
def translate_post(self, slug: str, frontmatter: Dict, content: str):
    content_hash = self._calculate_content_hash(content)
    cached = self.cache.get_translation(slug, content_hash)
    if cached:
        return cached
    
    prompt = self._build_translation_prompt(frontmatter, content)
    response = self.model.generate_content(prompt)
    translated = self._parse_translation_response(response.text)
    
    self.cache.set_translation(slug, content_hash, translated)
    return translated
```

O resultado são dois sites completos e paralelos. Ambos são HTML estático. Ambos são autocontidos. Ambos podem ser servidos por uma CDN sem infraestrutura de backend. O site em inglês vive em `/en`, o site em português em `/pt`, e o usuário pode alternar entre os dois com um único clique. O seletor de idioma não recarrega a página. Ele navega com uma View Transition que preserva a posição de rolagem e o estado dos filtros, fazendo a troca parecer uma camada sobreposta, não um salto.

## Navegação que Lembra

O site usa a View Transitions API para animar a passagem entre páginas. Essa API é exclusiva do Chromium, o que significa que o site mira Chrome, Edge, Brave e outros browsers baseados em Chromium. Não há polyfill. Não há animação de fallback. Se a API não estiver disponível, a navegação funciona normalmente, sem transições. Esta é uma troca deliberada: recursos de ponta para usuários em browsers modernos, degradação elegante para todo o resto.

O script que cuida da navegação é pequeno. Ele fica em `static/js/transitions.js`. Quando você clica em um link interno, o script intercepta o clique, busca o HTML da nova página, interpreta esse HTML como um fragmento de documento e inicia uma View Transition. Dentro do callback da transição, o script troca o título do documento, as folhas de estilo, o conteúdo principal e a navegação, e então atualiza a URL com `history.pushState`. O browser captura o estado de “antes”, executa o callback para atualizar o DOM, captura o estado de “depois” e anima a diferença.

```javascript
async function navigateTo(url) {
  const response = await fetch(url, { cache: 'no-cache' });
  const html = await response.text();
  const newDoc = new DOMParser().parseFromString(html, 'text/html');
  
  const transition = document.startViewTransition(() => {
    document.title = newDoc.title;
    const main = document.querySelector('main');
    const newMain = newDoc.querySelector('main');
    if (main && newMain) main.replaceWith(newMain);
    history.pushState(null, '', url);
  });
  
  await transition.finished;
}
```

Todo o comportamento de animação é definido em CSS usando pseudoelementos `::view-transition-*`. O JavaScript apenas aciona a API. O CSS define como o conteúdo antigo desaparece, como o novo conteúdo aparece e como elementos compartilhados se transformam entre estados. Cards de posts na página de índice se expandem em artigos completos. Títulos permanecem no lugar e crescem. O fundo muda suavemente. A sensação não é a de trocar de página, mas a de reorganizar uma única superfície contínua.

A curva de easing é a mesma em todos os lugares: `cubic-bezier(0.4, 0, 0.2, 1)`. As durações são compartilhadas por todas as interações: 300ms para efeitos rápidos de hover, 500ms para transições centrais, 600ms para mudanças de tema. Essas constantes vivem em propriedades customizadas de CSS e se propagam por todas as animações do site. A consistência não é imposta por um framework. Ela está codificada no próprio sistema de design.

## Troca de Idioma como Tradução Espacial

Uma das continuidades sutis do sistema está na forma como a troca de idioma se comporta. Quando você alterna de inglês para português, você não sai da página. Você traduz a superfície que já está lendo. A posição de rolagem é preservada. O estado dos filtros na página de índice é preservado. A URL muda de `/en/index.html` para `/pt/index.html`, mas o seu lugar no documento não muda.

Esse comportamento é detectado no script de navegação. Se a estrutura do caminho é idêntica exceto pelo segmento `en` ou `pt`, a navegação é classificada como uma troca de idioma. A posição de rolagem é capturada antes do fetch e restaurada depois da troca do DOM. Se você estava no meio de um artigo em inglês e muda para português, continua no meio do mesmo artigo em português. O conteúdo muda, mas o espaço não.

O mesmo princípio se aplica aos filtros na página de índice. Se você filtrou posts por ano ou tag e troca de idioma, o filtro continua ativo. Os posts traduzidos aparecem com os mesmos critérios de seleção. Isso faz a experiência bilíngue parecer um único documento visto por duas lentes, não dois sites separados.

## Filtragem com FLIP

A página de índice lista todos os posts com um painel de filtros para ano, mês e tags. A filtragem é instantânea. Quando você seleciona um ano, os posts que não correspondem desaparecem gradualmente, e os posts restantes se reorganizam em uma grade mais compacta. A reorganização é animada usando a técnica FLIP: First, Last, Invert, Play.

O script captura a posição inicial de cada card visível. Ele aplica o filtro, o que oculta os cards que não correspondem e força o recálculo do layout. Em seguida, captura a posição final de cada card que permanece visível. Para cada card, calcula a diferença entre a posição antiga e a nova, aplica um transform CSS para inverter o card de volta à posição inicial e então anima o transform de volta para zero.

```javascript
const rects = new Map();
cards.forEach(card => {
  rects.set(card, card.getBoundingClientRect());
});

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

A grade nunca dá um tranco. Ela exala. Os cards se dissolvem e deslizam para novas posições dentro da mesma janela de 500ms. O resultado parece deliberado, não surpreendente. O layout permanece sempre legível. O movimento explica o que mudou.

## Transições de Tema e Engenharia Antiflicker

O site oferece temas claro e escuro. O seletor é um botão simples na barra de navegação. Quando você clica, o tema se espalha pela página inteira ao longo de 600 milissegundos. Cores de fundo mudam, cores de texto se ajustam, bordas suavizam ou ficam mais marcadas, e sombras são recalculadas. A transição é suave porque é definida uma única vez, em CSS, com uma única classe aplicada ao body.

Um desafio durante o desenvolvimento foi evitar flicker visual quando transições de tema se sobrepunham a View Transitions. Se os dois sistemas animassem os mesmos elementos ao mesmo tempo, o resultado era um flash breve. A solução foi remover classes CSS conflitantes antes de iniciar uma View Transition e evitar seletores universais que aplicassem transições a todos os elementos de uma vez.

A transição de tema é condicionada. Ela só se aplica quando `theme-transitioning` está presente no body. Quando você alterna o tema, a classe é adicionada, o atributo do tema é atualizado e a classe é removida depois que a transição termina. Isso garante que mudanças de tema sejam animadas, mas que a navegação não dispare transições de tema redundantes.

Outra origem de flicker era a remoção tardia de animações CSS nos cards de posts. Na página de índice, os cards aparecem com uma animação de entrada escalonada quando a página carrega pela primeira vez. Em navegações posteriores, essa animação não deve rodar. O script detecta a navegação verificando `document.referrer`. Se o referrer corresponde à origem do site, o script assume que o usuário veio de outra página e desativa imediatamente a animação de entrada adicionando `disable-animation` à grade de posts. Os cards aparecem na hora, sem piscar e sem reiniciar.

## Filosofia da Simplicidade

A arquitetura não é minimalista por amor ao minimalismo. Ela é mínima porque o problema é simples. Um blog é texto, algumas imagens e a sensação de que percorrê-lo deveria parecer virar uma página sem perder o lugar. As capacidades nativas do browser são suficientes. Python é suficiente. Dependências são escolhidas com cuidado. Se uma ferramenta não torna o corte mais limpo, ela não entra no codebase.

A View Transitions API é nativa do Chromium. Ela não exige polyfill, wrapper nem etapa de build. O browser já sabe capturar dois estados do DOM e animar a passagem entre eles. Meu trabalho é decidir quando isso deve acontecer e impedir que o resto da página atrapalhe. O CSS que descreve o movimento é declarativo. Ele se lê como uma partitura de coreografia, não como um programa.

As bibliotecas `frontmatter` e `markdown` do Python fazem exatamente uma coisa cada: interpretam YAML e convertem Markdown em HTML. E fazem isso bem. Elas não tentam ser sistemas de build nem routers. Elas interpretam texto. É só disso que eu preciso. O script de build inteiro tem menos de 600 linhas de Python. Você consegue lê-lo de uma vez. Se consegue lê-lo, consegue alterá-lo.

## Manutenção por Antecipação

Recusar um framework aqui não é nostalgia. É alinhamento com o problema. Cada linha de código neste sistema é código que eu vou ter que ler de novo daqui a seis meses ou seis anos. Cada dependência é uma possível incompatibilidade futura. Cada abstração cobra imposto sobre a compreensão. Então o sistema permanece pequeno. Permanece legível. Permanece alterável.

A ausência de maquinário não é uma ideologia. É manutenção praticada por antecipação. Quando adiciono um novo post, escrevo markdown e rodo o script de build. A tradução acontece automaticamente. O HTML é gerado. O cache é atualizado. O site fica pronto para deploy. Não há servidor com hot reload. Não há configuração de webpack. Não há package.json com 300 dependências. Há um script Python, um arquivo markdown e uma pasta de HTML estático.

## O Contrato com o Leitor

Para quem quiser adaptar o sistema, o contrato é pequeno e explícito. Markdown entra, HTML sai. Um tradutor que respeita código e voz. Uma camada de navegação que nunca bloqueia pinturas com trabalho que poderia ter feito antes. Estilos que codificam ritmo uma vez e o reutilizam em todos os lugares. Se você muda uma coisa, deveria parecer que mudou exatamente uma coisa, e o resto do sistema deveria responder com calma proporcional.

A única esperteza está em saber quando parar. O sistema poderia fazer mais. Poderia ter um CMS. Poderia ter pré-visualização em tempo real. Poderia ter analytics, teste A/B e widgets de compartilhamento social. Ele não faz nada disso porque nada disso melhora a experiência de leitura. O objetivo não é construir uma plataforma. O objetivo é escrever e deixar que a escrita seja lida sem interferência.

Isto não é uma demonstração. É a versão mais simples de um documento vivo que eu consegui construir sem mentir sobre o que a web já é capaz de fazer. O cache lembra o que não mudou. O tradutor preserva o que não deve ser traduzido. A navegação mantém o ponto para onde você estava olhando quando o idioma mudou. O sistema de movimento codifica quanto tempo as coisas devem levar e se recusa a discutir o assunto. Cada decisão que o sistema toma está a serviço de uma única ideia: o documento é contínuo. Quando você se move por ele, o espaço se reorganiza, mas nunca se rompe.

É isso que significa um site estático parecer vivo.
