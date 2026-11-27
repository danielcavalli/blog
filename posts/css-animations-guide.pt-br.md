---
title: A arte das animações em CSS
excerpt: Criando animações fluidas e performáticas usando apenas CSS. Um mergulho profundo na construção de sistemas de movimento coerentes para a web moderna.
tags:
- CSS
- web
- animações
- desempenho
lang: pt-br
translation_of: css-animations-guide.md
source_digest: b985147044fb5fee1f1984a5dcb195535b3a31e01d71529424b821289ee7f3be
translated_by: openai/gpt-5.5, via opencode
---

## Por que animações em CSS?

Animações em CSS têm várias vantagens sobre animações baseadas em JavaScript. Elas são aceleradas por hardware, têm melhor desempenho e mantêm taxas fluidas de 60fps mesmo em dispositivos mais modestos. Mais importante que isso, elas permitem uma **abordagem declarativa para movimento**: você define o que deve acontecer, e o navegador cuida de como fazer.

Este blog é construído inteiramente com animações em CSS como primeira escolha. JavaScript entra apenas para disparar mudanças de estado; o comportamento visual vive nas folhas de estilo.

## A filosofia do movimento

Antes de escolher técnicas de animação, vale considerar o que o movimento *significa*. Toda transição deve responder a três perguntas: **De onde vem? Para onde vai? Como isso se relaciona com o que veio antes?**

Neste site, as animações servem a três princípios centrais:
1. **Continuidade**: tudo existe em uma única superfície ininterrupta
2. **Plausibilidade física**: o movimento ecoa dinâmicas do mundo real sem imitá-las
3. **Energia calma**: movimento intencional, sem agitação

Movimento nunca é decoração. Ele estabelece relações espaciais e reconhece mudanças de estado. A interface respira.

## Os blocos de construção

CSS oferece três formas principais de criar animações:

### Transitions

Interpolações fluidas entre estados. Usadas para efeitos de hover, mudanças de tema e expansões de dropdown. O ponto central é usar constantes compartilhadas de movimento. Todas as transições deste site usam a mesma curva de easing: `cubic-bezier(0.4, 0, 0.2, 1)`.

```css
:root {
    --motion-duration-core: 500ms;
    --motion-duration-quick: 300ms;
    --motion-duration-ripple: 600ms;
    --motion-easing: cubic-bezier(0.4, 0, 0.2, 1);
}

.custom-select {
    transition: all var(--motion-duration-core) var(--motion-easing);
}
```

Isso cria um ritmo temporal compartilhado. Cada interação parece parte da mesma coreografia.

### Keyframe Animations

Coreografia em múltiplas etapas para movimentos mais complexos. Este blog usa keyframes com parcimônia: apenas nas animações de carregamento inicial da página, quando elementos aparecem gradualmente e sobem.

```css
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
```

### Transform Properties

A base de desempenho. `translateY`, `scale` e `rotate` são acelerados por hardware e não disparam recálculos de layout caros. Quando o cabeçalho desliza por trás da barra de navegação, ele usa `translateY(-120%)` com duração de 500ms, alinhada ao tempo central do movimento.

## View Transitions API

Navegadores modernos têm suporte à **View Transitions API**, que permite transformações contínuas entre navegações de página. Este blog a usa para transformar cards de posts em artigos completos:

```css
::view-transition-old(post-container-1),
::view-transition-new(post-container-1) {
    animation-duration: var(--motion-duration-core);
    animation-timing-function: var(--motion-easing);
}
```

O ponto crucial: **faça o fetch do conteúdo ANTES de chamar `startViewTransition()`**. Altere o DOM de forma síncrona dentro do callback. Isso garante que o navegador capture corretamente os estados antigo e novo, evitando problemas de piscar conteúdo.

```javascript
async function navigateTo(url) {
    const response = await fetch(url);
    const html = await response.text();
    
    document.startViewTransition(() => {
        // Synchronous DOM swap here
        updateDOM(html);
    });
}
```

## Desempenho importa

Nem toda propriedade CSS se comporta da mesma forma quando o assunto é desempenho de animação. 

**Aceleradas por hardware (GPU):**
- `transform` (translate, scale, rotate)
- `opacity`
- `filter` (com cuidado: pode ser caro)

**Evite animar:**
- `width`, `height`, `margin`, `padding` (disparam layout)
- `color`, `background-color` isoladamente (disparam pintura)
- `box-shadow` (caro, mas aceitável em estados sutis de hover)

Use `will-change` com parcimônia e apenas durante animações ativas:

```css
.post-card.filtering-out {
    opacity: 0;
    will-change: opacity;
}

.post-card:not(.filtering-out) {
    will-change: auto; /* Reset after animation */
}
```

Isso instrui o navegador a otimizar a composição na GPU, mas só quando necessário. Deixar `will-change` ativo desperdiça memória.

## O ritmo da interação

Todas as animações deste site seguem um ritmo temporal consistente, definido por propriedades customizadas de CSS:
- **500ms (core)** para a maioria das transições (morphing, deslizamento, expansão)
- **300ms (quick)** para microinterações (feedback de hover)
- **600ms (ripple)** para mudanças atmosféricas (transições de tema)
- **O mesmo easing em todos os lugares**: `cubic-bezier(0.4, 0, 0.2, 1)`

Essa consistência cria uma sensação unificada de respiração. Quando filtros se expandem, dropdowns abrem e cards se dissolvem, todos se movem no mesmo pulso.

## Revelações escalonadas

Ao mostrar vários elementos, escalone sua aparição com atrasos de transition em CSS:

```css
.filter-row {
    transition: all var(--motion-duration-core) var(--motion-easing) 0.1s;
}

.filter-tags {
    transition: all var(--motion-duration-core) var(--motion-easing) 0.2s;
}
```

Os controles de filtro aparecem 100ms antes das pílulas de tag, criando uma cascata que guia o olhar naturalmente para baixo. Essa expansão orgânica faz a interface parecer que está se desdobrando a partir de uma única superfície.

## Limites orgânicos

Um padrão particular usado neste blog: **ajuste por overflow**. Quando uma lista de dropdown passa do limite do painel de filtros, o bloco inteiro se expande a partir da borda inferior, abrindo espaço de forma orgânica:

```css
.filters.expanded.dropdown-active {
    padding-bottom: 5rem;
}
```

JavaScript mede o overflow real do DOM usando `getBoundingClientRect()` e aplica a classe quando necessário. CSS cuida da expansão fluida. O resultado parece uma página consciente da própria geometria, respondendo fisicamente a ela.

## Transições de tema

Alternar entre modo claro e modo escuro não é apenas trocar cores. É uma **mudança atmosférica de iluminação**. O segredo é mudar o tema PRIMEIRO e só então habilitar as transições:

```javascript
function applyTheme(theme, animated) {
    if (animated) {
        // Change theme immediately
        document.documentElement.setAttribute('data-theme', theme);
        
        // Force reflow
        document.body.offsetHeight;
        
        // Enable smooth transitions for 600ms
        document.body.classList.add('theme-transitioning');
        
        setTimeout(() => {
            document.body.classList.remove('theme-transitioning');
        }, 600);
    }
}
```

```css
body.theme-transitioning * {
    transition: background-color var(--motion-duration-ripple) var(--motion-easing),
                color var(--motion-duration-ripple) var(--motion-easing),
                border-color var(--motion-duration-ripple) var(--motion-easing);
}
```

O efeito: a página inteira atravessa um novo estado de iluminação em uma ondulação de 600ms, mantendo a ilusão de uma única superfície contínua. Sem flashes, sem saltos bruscos.

## FLIP: animando mudanças de layout

Ao filtrar posts do blog, os cards precisam se reorganizar de forma fluida. A **técnica FLIP** (First, Last, Invert, Play) faz mudanças de layout parecerem animadas:

**Coreografia em duas fases:**
1. **Dissolver**: cards que perdem relevância desaparecem gradualmente ao longo de 500ms
2. **Reorganizar**: os cards restantes deslizam para suas novas posições usando FLIP

```javascript
// Phase 1: Capture initial positions
const initialPositions = new Map();
cards.forEach(card => {
    const rect = card.getBoundingClientRect();
    initialPositions.set(card, { top: rect.top, left: rect.left });
});

// Apply filter changes (cards removed from layout)
cardsToHide.forEach(card => card.classList.add('filtering-out'));

// Wait for dissolve to complete via transitionend event
grid.addEventListener('transitionend', () => {
    // Phase 2: Capture final positions
    const finalPositions = new Map();
    visibleCards.forEach(card => {
        const rect = card.getBoundingClientRect();
        finalPositions.set(card, { top: rect.top, left: rect.left });
    });
    
    // FLIP: Calculate deltas and animate
    visibleCards.forEach(card => {
        const deltaY = initial.top - final.top;
        const deltaX = initial.left - final.left;
        
        card.style.setProperty('--flip-x', `${deltaX}px`);
        card.style.setProperty('--flip-y', `${deltaY}px`);
        card.classList.add('flip-animating');
    });
});
```

```css
.post-card.flip-animating {
    transition: transform var(--motion-duration-core) var(--motion-easing);
    transform: translate(var(--flip-x, 0), var(--flip-y, 0));
    will-change: transform;
}
```

O resultado: os cards se dissolvem, e então o grid se contrai suavemente. Sem saltos bruscos. JavaScript controla o estado; CSS controla o visual.

## Exemplos práticos

Cada interação neste blog demonstra esses princípios:

- **Hover no card**: elevação com `translateY(-2px)` e abertura de sombra (duração quick de 300ms)
- **Pílulas de tag**: fundos em gradiente com elevação de 3px e sombras em expansão (duração core de 500ms)
- **Abertura de dropdown**: `max-height: 0 to 300px` com fade de opacity (500ms)
- **Expansão de filtros**: revelações escalonadas (atrasos de 100ms, 200ms) com crescimento pela borda inferior
- **Morphing de post**: View Transitions API para a transformação de card em artigo (500ms)
- **Ondulação de tema**: todas as propriedades de cor transitam juntas (mudança atmosférica de 600ms)
- **Filtragem de cards**: dissolução em duas fases (500ms), seguida de reorganização com FLIP (500ms)

Cada animação responde: De onde vem? Para onde vai? Como isso se relaciona com o que veio antes? Nada aparece ou desaparece sem contexto espacial.

## Acessibilidade primeiro

Sempre respeite as preferências do usuário com a media query `prefers-reduced-motion`. Para algumas pessoas, animações podem distrair ou desorientar:

```css
@media (prefers-reduced-motion: reduce) {
    * {
        animation-duration: 0.01ms !important;
        transition-duration: 0.01ms !important;
    }
}
```

Movimento deve ajudar, nunca atrapalhar. Quando o usuário sinaliza que precisa de movimento reduzido, respeite isso imediatamente.

## A conclusão

Animações em CSS, quando tratadas de forma sistemática, criam interfaces que parecem **vivas, mas calmas**. O objetivo não é impressionar com transições chamativas, e sim construir confiança por coerência espacial. O objetivo também não era apenas desempenho, mas a interface deve parecer performática pela ideia por trás das transições: fluidez. Uma transição engasgada prejudica esta interface. Embora fosse possível implementar tudo em JS puro, eu não sou um bom programador JS (nem quero ser). Usar intensamente os recursos do CSS para abstrair a lógica de implementação acelera o desenvolvimento e ainda entrega ao próprio navegador a responsabilidade por otimizações de desempenho.

Cada animação neste blog serve à mesma filosofia:
- **Continuidade**: uma única superfície ininterrupta
- **Plausibilidade física**: movimento que ecoa dinâmicas reais
- **Energia calma**: intencional, nunca agitada

Use propriedades customizadas de CSS para tempos compartilhados. Deixe o navegador cuidar do sequenciamento por meio de eventos `transitionend`. Aplique `will-change` apenas durante animações ativas. Pergunte sempre: De onde vem? Para onde vai? Como isso se relaciona com o que veio antes?

A interface não faz espetáculo. Ela responde.
