---
title: Como eu uso agentes de IA
excerpt: O que eu construí, o que quebrou e o que sobreviveu.
tags:
- agentes de IA
- Agent PM
- base de conhecimento
- pipeline de tradução
lang: pt-br
translation_of: how-i-use-ai-agents.md
source_digest: a09ba39b05fe3545d85a541341d87bbe17dc621062cb81cc9d66137c5ac1b90a
translated_by: openai/gpt-5.5, via opencode
---

<!-- presentation:slide id="title" layout="lead" density="normal" -->

# Como eu uso agentes de IA

## O que eu construí, o que quebrou e o que sobreviveu

Daniel Cavalli | dan.rio

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="dense" -->

# Daniel Cavalli

Engenheiro sênior de Machine Learning no Nubank

Formado em Economia pela UFRJ, com foco em modelagem causal. Nove anos de experiência em ML, passando por construção de modelos, plataformas de IA para várias empresas e, agora, brincando com agentes de IA e modelos comportamentais de mundo como linha de pesquisa.

![Daniel Cavalli](how-i-use-ai-agents.assets/profile-picture.png)

| # | Seção | Tese |
| - | ------- | ----- |
| 1 | Fundamentos | Continuidade é engenharia |
| 2 | Agent PM | Planejamento vence despacho |
| 3 | Base de conhecimento | Memória precisa de estrutura |
| 4 | Distribuição | Copiar não é adotar |
| 5 | Pipeline de tradução | Voz precisa de processo |

<!-- /presentation:slide -->

<!-- presentation:slide id="foundation" layout="divider" density="normal" -->

# Os Fundamentos

## Continuidade é uma ilusão que você constrói, não algo que o modelo entrega

<!-- /presentation:slide -->

<!-- presentation:slide id="stateless-model" layout="dark_content" density="dense" -->

# O modelo não mantém estado

Toda vez que você aperta Enter, o harness reconstrói o contexto inteiro do zero. O modelo responde. Depois, esquece tudo.

> A continuidade que você percebe é construída a partir de contexto que alguém, ou alguma coisa, decidiu colocar de volta. Não é memória. É reconstrução.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Sessões acumulam resíduo
Becos sem saída, objetivos misturados, restrições vencidas. O modelo se ancora no que veio primeiro, não no que veio por último.
<!-- /presentation:card -->
<!-- presentation:card -->
### Mais contexto pode piorar o resultado
O instinto da maioria das pessoas é manter mais histórico vivo. O modelo começa a se cercar de ressalvas, qualificar tudo, tentar reconciliar coisas que já não importam.
<!-- /presentation:card -->
<!-- presentation:card -->
### A habilidade real é remover
Não é expandir contexto. É saber o que condensar, o que descartar e o que levar adiante como artefato de passagem.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="four-rules" layout="card_grid" density="very_dense" -->

# Quatro Regras

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Uma sessão, uma tarefa
Sessões de pesquisa produzem notas de pesquisa. Sessões de especificação produzem pacotes de implementação. A implementação começa limpa, a partir do pacote. Elas nunca compartilham uma sessão.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Faça curadoria do que o modelo vê
Todo esquema de ferramenta, toda instrução MCP, todo fragmento vencido compete por atenção. Contexto irrelevante não apenas desperdiça tokens. Ele degrada ativamente o resultado.
<!-- /presentation:card -->
<!-- /presentation:block -->
<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 3. Isole tudo em sandbox
Capture erros fora da janela de contexto para que eles nunca consumam tokens de depuração. Um hook que formata código ao salvar ou valida YAML custa zero tokens e evita problemas que, sem isso, o modelo gastaria dezenas de mensagens corrigindo.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Multiagente é o próximo passo óbvio
Quando você aceita sessões isoladas, a pergunta passa a ser como dividir o trabalho entre elas. Cada agente recebe só o que precisa. Decompor, paralelizar, integrar.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="humans-job" layout="emphasis" density="dense" -->

# O Trabalho do Humano

> Agentes são notavelmente bons em trabalho de domínio único. Mas, no instante em que você precisa articular fios de vários domínios no mesmo argumento, eles desmoronam.

A vantagem humana não é "pensar" em geral. É síntese entre domínios: manter três contextos diferentes na cabeça, cruzá-los, saber quais restrições são reais e quais foram herdadas de uma conversa que já não se aplica.

O agente executa. Seu trabalho é decidir o que ele deve executar.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm" layout="divider" density="normal" -->

# Agent PM

## Porque eu tenho ideias demais e os agentes pioraram o problema

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-problem" layout="split" density="dense" -->

# O Problema

Eu me entusiasmo demais com ideias novas, o que me leva a explorar caminhos demais ao mesmo tempo.

Antes dos agentes, isso era limitado pela velocidade com que eu conseguia digitar. Com agentes, o limite desapareceu. Eu podia seguir várias direções ao mesmo tempo e só conferir os resultados depois.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### O que eu ganhei
Exploração paralela de verdade. Múltiplas hipóteses rodando ao mesmo tempo. Resultados me esperando quando eu voltava para conferir.
<!-- /presentation:column -->
<!-- presentation:column -->
### O que eu perdi
A capacidade de distinguir prioridades de distrações. Eu precisava de um sistema para decompor ideias, despachá-las para agentes e acompanhar o que voltava.
<!-- /presentation:column -->
<!-- /presentation:block -->

Agent PM começou como uma forma de gerenciar meu próprio foco. Virou um orquestrador porque os mesmos princípios que o tornavam útil para acompanhamento também o tornavam útil para despacho.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-what-it-is" layout="split" density="very_dense" -->

# O Que Ele É

Tudo é YAML em um diretório `.pm/`, versionado junto com o código. Distribuído como CLI global (`pm`), servidor MCP (14+ ferramentas) e um conjunto de comandos slash do Claude Code.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
.pm/
  project.yaml          # Definição do projeto
  index.yaml            # Resumo mantido automaticamente
  epics/
    E001-auth.yaml      # Épico com histórias embutidas
  reports/
    E001-S001-report.yaml
  agents/
    agent-abc.yaml      # Heartbeats + estado
  adrs/
    ADR-001.yaml        # Registros de decisão
```

<!-- /presentation:column -->
<!-- presentation:column -->

```yaml
stories:
  - id: S001
    title: "JWT middleware"
    acceptance_criteria:
      - "JWT tokens validated on every request"
      - "Expired tokens return 401"
    depends_on: []
    story_points: 3
    priority: high
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-flow" layout="card_grid" density="very_dense" -->

# O Fluxo

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Especificar
Eu escrevo. Estado atual, estado desejado, restrições, armadilhas, exclusões. A especificação é o resultado final da pesquisa, não o começo dela.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Refinar
`/pm-refine-epic` lê a especificação e examina o codebase. Produz épicos e histórias com dependências formando um DAG. O humano aprova antes da execução.
<!-- /presentation:card -->
<!-- presentation:card -->
### 3. Executar
`/pm-work-on-project` constrói um grafo de dependências, classifica em camadas e despacha agentes em paralelo por camada. O contexto de falha se propaga adiante.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Monitorar
`/supervisor` faz triagem: Bloqueado > Desatualizado > Concluído > Rodando. Decisões em lote entre agentes. Menos de 3 minutos por rodada.
<!-- /presentation:card -->
<!-- /presentation:block -->

A especificação é onde todo o pensamento real acontece. Tudo depois depende de quão bem você fez essa parte.

<!-- /presentation:slide -->

<!-- presentation:slide id="tiered-dispatch" layout="table" density="dense" -->

# Despacho em Camadas

`/pm-work-on-project` constrói o grafo de dependências e classifica as histórias:

- **Camada 1:** Nenhuma dependência pendente. Despachadas em paralelo.
- **Camada 2:** Dependências todas na Camada 1. Despachadas depois que a Camada 1 termina.
- **Camada N:** Dependências todas em camadas < N.

Cada subagente roda isolado. Ao concluir, ele registra um **relatório de execução** com decisões, premissas, tradeoffs e potenciais conflitos com agentes paralelos.

| Camada | Elegibilidade | Comportamento de despacho |
| ---- | ----------- | ----------------- |
| Camada 1 | Nenhuma dependência pendente | Despachada em paralelo imediatamente |
| Camada 2 | Dependências todas na Camada 1 | Despachada depois que a Camada 1 termina |
| Camada N | Dependências todas em camadas anteriores | Despachada depois que todas as camadas anteriores exigidas terminam |

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-comparison" layout="table" density="dense" -->

# Agent PM vs. Symphony vs. Agent Teams

| Dimensão             | Agent PM                          | OpenAI Symphony                   | Anthropic Agent Teams             |
| -------------------- | --------------------------------- | --------------------------------- | --------------------------------- |
| Camada de planejamento | Embutida (`/pm-refine-epic`)    | Nenhuma                           | Nenhuma                           |
| Fila de trabalho     | YAML local em `.pm/`              | Linear (externo)                  | Nativa do harness                 |
| Modelo de despacho   | Por camadas: conclui N, depois N+1 | Faz polling a cada 30s, preenche slots abertos | Gerenciado por sessão             |
| Identidade do agente | Papéis heterogêneos               | Homogênea (mesmo prompt)         | Homogênea                         |
| Persistência de estado | Filesystem (sobrevive a crashes) | Em memória + Linear              | Presa à sessão                    |

Symphony é elegante. Supervisão Elixir OTP, WORKFLOW.md hot-reloadable, Linear como plano de controle. Mas é um despachante, não um planejador. Agent Teams é profundamente integrado, mas menos customizável. Agent PM inclui a etapa de planejamento.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-lessons" layout="split" density="dense" -->

# O Que Eu Aprendi

Nas duas vezes, a solução customizada funcionou. Nas duas, provou o conceito. Nas duas, ficou obsoleta em poucas semanas.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Agent PM vs. Agent Teams
Agent PM existiu por dois meses antes de a Anthropic lançar Agent Teams (março de 2026). Orquestração multiagente nativa, com integração mais profunda.
<!-- /presentation:column -->
<!-- presentation:column -->
### IPC customizado vs. memória compartilhada
Eu construí escalonamento e contexto compartilhado usando a infraestrutura de tarefas do Agent PM. A Anthropic entregou memórias compartilhadas por sessão com hooks. A solução nativa substituiu a minha.
<!-- /presentation:column -->
<!-- /presentation:block -->

> A lição não é "não construa". É que qualquer coisa que você constrói em uma plataforma que se move tão rápido é uma prova de conceito, quer você tenha pretendido isso ou não.

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base" layout="divider" density="normal" -->

# A Base de Conhecimento

## Porque os agentes continuavam esquecendo o que outros agentes aprendiam

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-problem" layout="card_grid" density="dense" -->

# O Problema

Quando o Agent PM cresceu até virar um orquestrador completo, o conhecimento criado em uma sessão não tinha como sobreviver até a próxima.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Primeira tentativa: pacotes de trabalho
Comentários nas histórias, gerenciados pelo orquestrador depois de cada execução. Funcionava para passagens simples.
<!-- /presentation:card -->
<!-- presentation:card -->
### Onde quebrou
Agentes de pesquisa precisavam de uma fonte da verdade. Dois agentes investigando a mesma pergunta chegavam a conclusões diferentes porque nenhum conseguia ver o trabalho do outro.
<!-- /presentation:card -->
<!-- presentation:card -->
### No que virou
Uma base de conhecimento compartilhada. Grep simples sobre markdown parou de escalar depois de 50 notas, quando as relações entre elas começaram a importar.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="note-structure" layout="split" density="very_dense" -->

# Como É Uma Nota

Toda nota é um arquivo markdown com frontmatter estruturado. Agentes escrevem pelo servidor MCP (que valida esquemas, resolve tags e atualiza backlinks); humanos leem no Obsidian.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```yaml
---
title: AI Native Software Distribution
type: concept
project: kb-system
tags: [kb-system, architecture, open-source]
status: active
confidence:
  source_type: specification
  verified: false
depends_on:
  - kb-system-installer-ux-findings
aliases:
  - ai-native-distribution
---
```

<!-- /presentation:column -->
<!-- presentation:column -->
### 6 tipos de nota
**planos**, **pesquisas**, **conceitos**, **insights**, **decisões**, **referências**
### Relações são explícitas
`depends_on`, `parent`, `implements`, `supersedes` no frontmatter. `[[wikilinks]]` no corpo. Tags compartilhadas como conexões fracas.
### 80+ notas em 7 projetos
O servidor MCP roda como um processo HTTP compartilhado, então todas as sessões do Claude Code compartilham um índice.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-search" layout="card_grid" density="dense" -->

# Como a Busca Funciona

Recuperação baseada em embeddings (RAG) achata relações: duas notas sobre o mesmo assunto recebem embeddings parecidos, independentemente de uma substituir a outra. A base de conhecimento combina três sinais via Reciprocal Rank Fusion.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### BM25 (FTS5)
Busca textual completa com porter stemming. Encontra notas pelo que elas dizem.
<!-- /presentation:card -->
<!-- presentation:card -->
### Personalized PageRank
Percorre o grafo de notas a partir dos resultados textuais. Encontra notas pelo que elas conectam.
<!-- /presentation:card -->
<!-- presentation:card -->
### Ajustes de confiança
Notas verificadas ranqueiam mais alto. Notas cujas dependências foram atualizadas ranqueiam mais baixo até serem revisadas.
<!-- /presentation:card -->
<!-- /presentation:block -->

Sem embeddings significa sem dependência de modelo, sem deriva, e cada resultado explica por que foi ranqueado naquela posição.

<!-- /presentation:slide -->

<!-- presentation:slide id="consolidation-pipeline" layout="card_grid" density="dense" -->

# O Pipeline de Consolidação

Um sistema noturno de agentes (`/consolidate`) que transforma o trabalho disperso do dia em entradas duráveis de conhecimento.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Fase 0: Estrutura
3 agentes paralelos corrigem integridade de links, fazem triagem da inbox, reparam referências quebradas
<!-- /presentation:card -->
<!-- presentation:card -->
### Fase 1: Coleta
4 agentes paralelos extraem de logs de sessão, PRs, calendário, Slack
<!-- /presentation:card -->
<!-- presentation:card -->
### Fase 2: Síntese
Opus analisa em modo somente leitura, agentes Sonnet executam edições, Opus revisa o diff
<!-- /presentation:card -->
<!-- /presentation:block -->

O pipeline se alimenta de `kb_stale`: uma ferramenta que sinaliza notas por deriva de dependência, links quebrados, idade ou orfandade comunitária. Notas que precisam de atenção sobem automaticamente.

<!-- /presentation:slide -->

<!-- presentation:slide id="distribution" layout="divider" density="normal" -->

# Distribuição

## Construir o instalador da base de conhecimento mudou como eu penso sobre compartilhar software

<!-- /presentation:slide -->

<!-- presentation:slide id="copying-caveat" layout="emphasis" density="normal" -->

# Uma Ressalva

> Tudo o que eu mostrei hoje foi construído para a forma como eu penso. São minhas ferramentas, moldadas pelos meus problemas, meus hábitos e minha tolerância a overengineering.

O ponto não é copiá-las. É mostrar o que se torna possível quando você constrói para o seu próprio workflow, em vez de adotar a solução de outra pessoa para o problema de outra pessoa.

<!-- /presentation:slide -->

<!-- presentation:slide id="problem-with-copying" layout="content" density="dense" -->

# O Problema de Copiar

Há mais de 44.000 skills em plataformas de distribuição e mais de 36.900 estrelas no awesome-cursorrules. Pessoas compartilham arquivos de configuração, copiam e rodam sem mudar nada.

Nós estruturamos nosso trabalho de formas tão diferentes que isso só tende a produzir workflows subótimos. Tudo pode ser customizado, e a IA torna isso trivialmente fácil. Então, em vez de procurar o template certo, pegue a ideia e reconstrua até ela encaixar na forma como você pensa.

Mas isso levanta uma pergunta: se copiar é errado, como *deveríamos* distribuir software nativo de IA?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-core-setup" layout="code" density="dense" -->

# Dry Run: Fase A - Configuração Base

*O instalador faz uma pergunta por vez. Sem agrupar.*

```
Instalador do Sistema de KB
===========================

Isto vai configurar uma base de conhecimento pessoal com alguns ou todos estes itens:
- Um vault Markdown estruturado (compatível com Obsidian)
- Uma skill /kb para registrar conteúdo de qualquer sessão de codificação com IA
- Um pipeline noturno de consolidação
- Um servidor MCP para busca ranqueada e validação de escrita

Vou guiar você pelos componentes, pesquisar suas ferramentas e então instalar tudo.

Como devo chamar você?
> Sarah

Onde você quer deixar sua base de conhecimento? (caminho completo)
> ~/dev/kb

  Vou criar um novo vault em ~/dev/kb.

Quais fontes de informação você quer que o sistema colete?
Por exemplo: alterações de código (GitHub), mensagens (Slack), calendário, documentos.
> GitHub, Slack e Google Calendar
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-components" layout="code" density="dense" -->

# Dry Run: Fase B - Componentes

*Cada componente é apresentado com o que faz e o que você perde sem ele.*

```
A base é um vault Markdown estruturado com notas baseadas em frontmatter,
wikilinks, um índice e um log. Isso sempre é instalado.

A skill /kb permite que qualquer sessão do Claude Code registre conteúdo na sua KB
como tarefa em segundo plano. Você usaria assim: /kb <content> ou /kb context save <project>.
Sem ela, você escreveria notas manualmente.

  Incluir a skill /kb? (recomendado)
  > Sim

O pipeline de consolidação roda em uma agenda, coletando GitHub, Slack e
Google Calendar para dentro da KB. Sem ele, só entra o que você registrar explicitamente.

  Incluir o pipeline de consolidação? (recomendado)
  > Sim

  Python 3.12.8 detectado

O servidor MCP fornece busca ranqueada (BM25 + sinais de grafo), validação de escrita
e detecção de desatualização. Sem ele, agentes usam Glob/Grep sem ranqueamento.

  Incluir o servidor MCP? (recomendado)
  > Sim
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-research" layout="code" density="normal" -->

# Dry Run: Fase C - Pesquisa

*É aqui que um instalador tradicional não consegue acompanhar. Um agente paralelo por fonte, todos rodando ao mesmo tempo.*

```
Pesquisando integrações para suas 3 fontes...

  [Agente 1] Buscando: "GitHub MCP server" + "GitHub Claude Code integration"
  [Agente 2] Buscando: "Slack MCP server" + "Slack Claude Code integration"
  [Agente 3] Buscando: "Google Calendar MCP server" + "Google Calendar integration"

  Todos os 3 agentes de pesquisa concluíram.
```

Cada agente busca servidores MCP, ferramentas CLI e APIs REST. Para cada opção encontrada, ele verifica: vem de uma fonte confiável? Quais permissões exige? Está em manutenção ativa? Há preocupações de segurança conhecidas?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-findings" layout="code" density="dense" -->

# Dry Run: Fase D - Achados

*O instalador apresenta o que encontrou, verifica o que já está instalado e roda smoke tests.*

```
Fonte: GitHub
  Abordagem: gh CLI (oficial, já instalado)
  Smoke test: gh api user → PASS
  Status: Pronto

Fonte: Slack
  Abordagem: @anthropic/slack-mcp (MCP oficial da Anthropic)
  Status: Não instalado
  "Quer que eu ajude a configurar isso, ou pulamos por enquanto?"
  > Configurar

Fonte: Google Calendar
  Abordagem: google-workspace MCP (já configurado)
  Smoke test: calendar_listEvents → PASS
  Status: Pronto
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-source-configuration" layout="code" density="dense" -->

# Dry Run: Fase E - Configuração de Fontes

*Perguntas direcionadas por fonte, adaptadas às ferramentas encontradas na fase de pesquisa.*

```
Para GitHub: quais repositórios importam mais?
> Todos os repos sob my-org/

Para Slack: quais canais a consolidação deve varrer?
> #engineering, #incidents e qualquer DM com meu nome

Para Calendar: qual calendário?
> Primary. As notas de reunião ficam no Google Docs.


Aqui está o que temos até agora:
  - Vault em ~/dev/kb com tipos de nota: plan, research, concept,
    insight, decision, reference
  - skill /kb, consolidação e servidor MCP habilitados
  - Fontes: GitHub (gh), Slack (MCP), Calendar (MCP)

Há algo que você queira customizar?
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-customization" layout="code" density="dense" -->

# Dry Run: Fase F - Customização

*É aqui que o instalador deixa de ser um formulário. O usuário pode pedir recursos, e o instalador verifica a viabilidade contra o codebase real.*

```
> Quero um tipo de nota ADR para decisões de arquitetura. E queria
  que a consolidação marcasse notas por projeto automaticamente.

  Tipo de nota ADR: vou adicionar notes/adrs/ à estrutura do vault e
  registrar "adr" como tipo de nota com campos para status, contexto,
  decisão e consequências.

  Marcação automática por projeto: deixe-me verificar se o servidor suporta isso.

  [Agente avaliador criado → lendo o codebase do kb-server...]

  Avaliação: mudança apenas de configuração. O servidor já infere o projeto
  a partir do caminho do vault. Adicionar inferência de tags exige uma nova seção
  de configuração em kb-server.yaml. Nenhuma mudança de código necessária.

  As duas customizações serão incluídas. Mais alguma coisa?
> Só isso.
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-finalize-generate" layout="split" density="very_dense" -->

# Dry Run: Fases G-J - Finalizar e Gerar

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
Qual modelo para agentes de análise?
  (padrão: claude-opus-4-6)
> O padrão está bom

Qual modelo para agentes de execução?
  (padrão: claude-sonnet-4-6)
> Padrão

Quando a consolidação deve rodar?
> 2h, só em dias úteis

Prosseguir com a instalação?
> Sim
```

<!-- /presentation:column -->
<!-- presentation:column -->

```
Resumo da Instalação
====================

Componentes: vault, skill /kb,
  consolidação, servidor MCP
Fontes: GitHub (gh), Slack (MCP),
  Calendar (MCP)
Custom: tipo de nota ADR,
  marcação automática por projeto
Modelos: opus/sonnet
Agenda: 02:00 dias úteis

Gerando 9 artefatos...
  ✓ kb-protocol.md
  ✓ kb/skill.md
  ✓ consolidate.md
  ✓ kb-server.yaml
  ✓ consolidate-gather.sh
  ✓ com.kb-system.consolidate.plist
  ✓ intent.yaml
  ✓ CLAUDE.md injection
  ✓ installed.json

Concluído. Vault inicializado em ~/dev/kb
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="installer-reads-history" layout="card_grid" density="dense" -->

# O Instalador Lê Seu Histórico

Antes de a conversa começar, o instalador varre a telemetria de sessões do Claude Code: contagem de sessões, diversidade de ferramentas, uso de subagentes, servidores MCP configurados, diretórios de projetos, skills e hooks customizados. Ele usa isso para calibrar a conversa sem nunca revelar o profiling.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Profundidade da explicação
Um iniciante recebe descrições completas dos componentes, com tradeoffs. Um usuário experiente recebe uma tabela e um prompt de "quais destes?". A informação é a mesma; a entrega se adapta.
<!-- /presentation:card -->
<!-- presentation:card -->
### Sugestões proativas
O instalador não espera o usuário descrever seu workflow. Ele já vê 14 projetos em ~/dev/, MCPs configurados, hooks Python ativos. Sugere um registro de projetos, coleta apoiada por MCP e um vocabulário de tags semeado a partir dos projetos existentes.
<!-- /presentation:card -->
<!-- presentation:card -->
### Superfície de customização
Usuários avançados recebem opções mais profundas (intents customizados, extensões de tipos de nota, ajuste fino da consolidação) que esmagariam um iniciante. As opções não ficam escondidas; elas aparecem no nível certo para o usuário.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="two-users-same-installer" layout="split" density="very_dense" -->

# Dois Usuários, Mesmo Instalador

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Alguém com 10 sessões

```
A skill /kb permite que qualquer sessão
do Claude Code registre conteúdo na sua KB
como tarefa em segundo plano. Você usaria assim:
/kb <content> ou /kb context save.
Sem ela, você escreveria notas
manualmente.

Incluir a skill /kb? (recomendado)
> Sim
```

*Explicação completa. Exemplo concreto de uso. Recomendação clara.*

<!-- /presentation:column -->
<!-- presentation:column -->
### Alguém com 500 sessões

```
Componentes:

| Componente     | Exige        |
|----------------|--------------|
| Vault          | (sempre)     |
| skill /kb      | nada         |
| Consolidação   | agenda       |
| Servidor MCP   | Python 3.12+ |

Quais você quer?
> Todos.

Vejo que você trabalha em 3 projetos Kubernetes
com uso intenso de ADRs no seu histórico git.
Quer que eu adicione um tipo de nota ADR com campos
no estilo Nygard e semeie o vocabulário de tags
a partir dos nomes dos seus projetos existentes?
```

*Mesma informação, profundidade diferente. Sugestões proativas extraídas do que ele encontrou no ambiente do usuário.*

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="three-agents-one-conversation" layout="card_grid" density="dense" -->

# Três Agentes, Uma Conversa

O usuário vê uma única conversa. Por trás dela, três agentes com papéis diferentes.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Instalador
Voltado ao usuário, de longa duração. Conduz a conversa, gera artefatos padrão, cria subagentes quando necessário. O usuário nunca vê a orquestração.
<!-- /presentation:card -->
<!-- presentation:card -->
### Avaliador
Em segundo plano, de curta duração, criado por solicitação. Lê o codebase do servidor e avalia a viabilidade dos pedidos do usuário. Estritamente somente leitura.
<!-- /presentation:card -->
<!-- presentation:card -->
### Construtor
Em segundo plano, potencialmente de longa duração. Recebe uma especificação codesenhada pelo Instalador e pelo usuário. Planeja a implementação, escreve código, testa, valida.
<!-- /presentation:card -->
<!-- /presentation:block -->

O desenvolvedor constrói um codebase legível. A IA lê, entende e remodela para caber em cada usuário. O "produto" é o prompt de instalação e um codebase claro o bastante para uma IA navegar.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-pipeline" layout="divider" density="normal" -->

# O Pipeline de Tradução

## Mesmos padrões, outro domínio

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-problem" layout="content" density="normal" -->

# O Problema

Meu blog (dan.rio) é bilíngue. A primeira versão do sistema de tradução funcionava do jeito óbvio: entregar um post ao modelo e pedir uma versão em português.

O resultado estava sempre correto. Também estava sempre plano: aquele tipo de texto que comunica sem envolver. O significado atravessava; a voz, o ritmo e a textura retórica, não.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-insight" layout="code" density="dense" -->

# O Insight

A correção não veio de um modelo melhor nem de um prompt mais longo. Veio de ler o que institutos de tradução realmente recomendam.

Eles não dizem "traduza melhor". Dizem: analise a fonte como escrita autoral antes de mexer nela, resolva disputas terminológicas antes do rascunho, mantenha o crítico independente do tradutor e verifique se as revisões de fato resolveram o que a crítica encontrou.

Cada uma dessas recomendações virou uma etapa em um pipeline de 7.500 linhas, construído com Claude Code.

```
source_analysis → terminology_policy → translate → [critique → revise] × N → final_review
```

As etapas 1-2 rodam uma vez e produzem documentos de política vinculantes, que restringem tudo o que vem depois. Tradução e revisão usam GPT-5.4 high para trabalho generativo. Crítica e revisão final usam GPT-5.2 medium: um modelo deliberadamente diferente, para impedir que o tradutor corrija a própria prova.

<!-- /presentation:slide -->

<!-- presentation:slide id="terminology-policy" layout="code" density="dense" -->

# Como É Uma Política Terminológica

Antes de qualquer tradução começar, a Etapa 2 produz uma política terminológica para o artefato inteiro. Toda etapa posterior recebe esse documento e fica vinculada às suas decisões.

```json
{
  "keep_english": ["Claude Code", "MCP", "API", "Agent PM"],
  "localize": ["knowledge base" → "base de conhecimento",
               "pull request" → "pull request"],
  "resolved_decisions": [
    {
      "source_term": "AI Platform",
      "preferred_rendering": "AI Platform",
      "scope": "artifact-wide",
      "rationale": "nome de equipe, não conceito genérico"
    },
    {
      "source_term": "harness",
      "preferred_rendering": "harness",
      "scope": "artifact-wide",
      "rationale": "termo técnico usado ao longo do texto; localizar como 'arnês'
                    perderia a metáfora"
    }
  ]
}
```

<!-- /presentation:slide -->

<!-- presentation:slide id="critique-finding" layout="code" density="dense" -->

# Como É Um Achado de Crítica

A etapa de crítica não diz "a tradução está 78% boa". Ela produz achados por trecho: aqui está o texto-fonte, aqui está o que você escreveu, aqui está o problema e aqui está como corrigir.

```json
{
  "severity": "major",
  "category": "tone_flattening",
  "source_span": "the voice did not survive the trip",
  "target_span": "a voz não sobreviveu",
  "description": "Perdeu o peso retórico de 'the trip' como metáfora
                  para o próprio ato de traduzir",
  "fix_hint": "Restaure a metáfora da viagem: 'a voz não sobreviveu
              à travessia'"
}
```

A etapa de revisão recebe esses achados e precisa resolver cada um. A etapa de revisão final então verifica se a revisão de fato aplicou as correções ou apenas afirmou que aplicou: verifique, não confie.

<!-- /presentation:slide -->

<!-- presentation:slide id="quality-gate" layout="split" density="very_dense" -->

# O Gate de Qualidade

O pipeline não pergunta ao modelo se a tradução está boa o bastante. Ele usa uma rubrica determinística com dimensões ponderadas e limiares rígidos.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

| Dimensão              | Peso |
| --------------------- | ------ |
| Precisão              | 30%    |
| Terminologia          | 20%    |
| Fidelidade Markdown   | 20%    |
| Convenções linguísticas | 10%  |
| Estilo e registro     | 10%    |
| Convenções locais     | 5%     |
| Clareza para o público | 5%    |

<!-- /presentation:column -->
<!-- presentation:column -->
### Limiares de decisão
**Aceitar:** score >= 92, zero erros graves
**Refinar:** score 88-92, voltar para crítica
**Escalar:** score 75-88, ou travado por 2 loops
**Falhar:** score < 60, ou qualquer erro crítico
### Travas obrigatórias
Precisão >= 85, terminologia >= 80, fidelidade Markdown >= 95. Se qualquer uma falhar, o pipeline refina independentemente do score geral.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="where-this-goes-next" layout="card_grid" density="dense" -->

# Para Onde Isso Vai Agora

O pipeline funciona. As traduções leem como português, não como inglês fantasiado de português. Mas ainda há espaço para melhorar.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### GEPA para otimização de prompts
Exploração inicial do uso de GEPA para otimizar os prompts das etapas de forma sistemática, em vez de ajuste manual. Nada conclusivo ainda, mas os contratos tipados do pipeline o tornam um bom candidato: cada etapa tem entradas e saídas mensuráveis.
<!-- /presentation:card -->
<!-- presentation:card -->
### Coerência em nível de documento
Hoje, o pipeline traduz por post. A coerência entre parágrafos dentro de um post é tratada pela política terminológica, mas não há mecanismo para coerência entre posts de uma série.
<!-- /presentation:card -->
<!-- presentation:card -->
### Classificação de erros MQM
As categorias de crítica são definidas à mão. Migrar para MQM (Multidimensional Quality Metrics) alinharia o processo à forma como qualidade de tradução profissional é realmente medida.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Obrigado

## O agente executa. Seu trabalho é decidir o que ele deve executar.

dan.rio | github.com/danielcavalli

<!-- /presentation:slide -->
