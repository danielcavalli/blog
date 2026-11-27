---
title: Como uso agentes de IA
excerpt: O que construí, o que quebrou e o que sobreviveu.
tags:
- Agentes de IA
- Fluxo de trabalho
- Ferramentas
lang: pt-br
translation_of: how-i-use-ai-agents.md
source_digest: 356b1e45354f1eb1cac97bf167b17495b7210569965286045565dc45233b26a4
translated_by: gpt-5.6-sol (high), via mare-hub
translated_at: '2026-11-27'
---

<!-- presentation:slide id="title" layout="lead" density="normal" -->

# Como uso agentes de IA

## O que construí, o que quebrou e o que sobreviveu

Daniel Cavalli · dan.rio · abril de 2026

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="normal" -->

# Daniel Cavalli

Engenheiro Sênior de Machine Learning · Nubank

Economia na UFRJ, modelagem causal. Nove anos em ML: modelos, plataformas de IA e, agora, agentes e modelos de mundo comportamentais.

![Daniel Cavalli](how-i-use-ai-agents.assets/profile-picture.png)

| # | Seção | Tese |
| - | ----- | ---- |
| 1 | Base | A continuidade é construída |
| 2 | Agent PM | Planejar importa mais que acionar |
| 3 | Base de conhecimento | Memória precisa de estrutura |
| 4 | Distribuição | Copiar não é adotar |
| 5 | Pipeline de tradução | Voz precisa de processo |

<!-- /presentation:slide -->

<!-- presentation:slide id="foundation" layout="divider" density="normal" -->

# A base

## A continuidade é uma ilusão que você constrói, não algo que o modelo entrega

<!-- /presentation:slide -->

<!-- presentation:slide id="stateless-model" layout="dark_content" density="normal" -->

# O modelo não tem estado

Sempre que você pressiona Enter, o harness reconstrói o contexto do zero. **Não é memória. É reconstrução.**

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Sessões acumulam resíduos
O modelo se prende ao que veio primeiro, não ao que veio por último.
<!-- /presentation:card -->
<!-- presentation:card -->
### Mais contexto, pior resposta
O modelo se cerca de ressalvas para conciliar coisas que já não importam.
<!-- /presentation:card -->
<!-- presentation:card -->
### A verdadeira habilidade está em remover
Saiba o que condensar, o que descartar e o que repassar.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="four-rules" layout="card_grid" density="normal" -->

# Quatro regras

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Uma sessão, uma tarefa
Pesquisa, especificação e implementação nunca compartilham uma sessão. Cada uma começa com o resultado da anterior.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Selecione o que o modelo vê
Contexto irrelevante não apenas desperdiça tokens. Ele piora a resposta.
<!-- /presentation:card -->
<!-- /presentation:block -->
<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 3. Coloque tudo em sandbox
Capture os erros fora da janela de contexto. Um hook que formata ao salvar não gasta token algum.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Só então use múltiplos agentes
Depois de isolar as sessões, divida o trabalho. Cada agente recebe apenas o necessário.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="humans-job" layout="emphasis" density="normal" -->

# O trabalho humano

> Agentes são extraordinariamente bons em tarefas restritas a um domínio. No instante em que você tenta costurar vários domínios numa só linha de raciocínio, eles desmoronam.

O agente executa. Seu trabalho é decidir o que ele deve executar.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm" layout="divider" density="normal" -->

# Agent PM

## Porque tenho ideias demais e os agentes pioraram o problema

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-problem" layout="split" density="normal" -->

# O problema

Antes dos agentes, minhas ideias eram limitadas pela velocidade com que eu conseguia digitar. **Com os agentes, esse limite desapareceu.**

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### O que ganhei
Várias hipóteses em andamento ao mesmo tempo.
<!-- /presentation:column -->
<!-- presentation:column -->
### O que perdi
A capacidade de distinguir prioridades de distrações.
<!-- /presentation:column -->
<!-- /presentation:block -->

O Agent PM nasceu para eu conseguir administrar meu próprio foco.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-what-it-is" layout="split" density="normal" -->

# O que é

YAML em um diretório `.pm/`, versionado com o código. Uma CLI, um servidor MCP e comandos do Claude Code.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
.pm/
  project.yaml      # the project
  index.yaml        # summary, kept by pm
  epics/
    E001-auth.yaml  # an epic, its stories
  reports/
    E001-S001-report.yaml
  agents/
    agent-abc.yaml  # heartbeat, state
  adrs/
    ADR-001.yaml    # a decision
```

<!-- /presentation:column -->
<!-- presentation:column -->

```yaml
stories:
  - id: S001
    title: "JWT middleware"
    acceptance_criteria:
      - "JWT validated on every request"
      - "Expired tokens return 401"
    depends_on: []
    story_points: 3
    priority: high
```

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-flow" layout="card_grid" density="normal" -->

# O fluxo

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### 1. Especificar
Eu escrevo. Estado atual, estado desejado, restrições, armadilhas e exclusões.
<!-- /presentation:card -->
<!-- presentation:card -->
### 2. Refinar
`/pm-refine-epic` produz épicos e histórias com dependências. A execução só começa após aprovação humana.
<!-- /presentation:card -->
<!-- presentation:card -->
### 3. Executar
`/pm-work-on-project` aciona agentes em paralelo por camada.
<!-- /presentation:card -->
<!-- presentation:card -->
### 4. Monitorar
`/supervisor` faz a triagem: Bloqueado > Estagnado > Concluído > Em execução.
<!-- /presentation:card -->
<!-- /presentation:block -->

Todo o trabalho intelectual de verdade acontece na especificação.

<!-- /presentation:slide -->

<!-- presentation:slide id="tiered-dispatch" layout="table" density="normal" -->

# Acionamento por camadas

`/pm-work-on-project` monta o grafo de dependências e classifica as histórias em camadas.

| Camada | Elegibilidade | Acionamento |
| ------ | ------------- | ----------- |
| Camada 1 | Nenhuma dependência pendente | Em paralelo, imediatamente |
| Camada 2 | Todas as dependências estão na Camada 1 | Depois que a Camada 1 termina |
| Camada N | Todas as dependências estão em camadas anteriores | Depois que essas camadas terminam |

Cada subagente roda isoladamente e registra um relatório de execução ao concluir.

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-comparison" layout="table" density="normal" -->

# Agent PM vs. Symphony vs. Agent Teams

Symphony e Agent Teams acionam agentes. O Agent PM também planeja.

|                 | Agent PM                     | OpenAI Symphony       | Anthropic Agent Teams |
| --------------- | ---------------------------- | --------------------- | --------------------- |
| Planejamento    | Nativo (`/pm-refine-epic`)    | Nenhum                | Nenhum                |
| Fila de trabalho | YAML local em `.pm/`         | Linear (externo)      | Nativa do harness     |
| Acionamento     | Por camada: termina N, depois N+1 | Consulta a cada 30 s | Gerenciado pela sessão |
| Agentes         | Funções diferentes            | Um prompt para todos  | Um prompt para todos  |
| Estado          | Arquivos: resiste a travamentos | Em memória + Linear | Termina com a sessão  |

<!-- /presentation:slide -->

<!-- presentation:slide id="agent-pm-lessons" layout="split" density="normal" -->

# O que aprendi

Nas duas ocasiões, a solução personalizada funcionou. **Nas duas, ficou obsoleta em questão de semanas.**

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Agent PM vs. Agent Teams
O Agent PM existia havia dois meses quando a Anthropic lançou o Agent Teams.
<!-- /presentation:column -->
<!-- presentation:column -->
### IPC personalizado vs. memória compartilhada
A Anthropic lançou memórias compartilhadas na sessão. A solução nativa substituiu a minha.
<!-- /presentation:column -->
<!-- /presentation:block -->

> A lição não é "não construa". É que tudo o que você construir sobre uma plataforma que evolui nessa velocidade será uma prova de conceito.

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base" layout="divider" density="normal" -->

# A base de conhecimento

## Porque os agentes continuavam esquecendo o que outros agentes haviam aprendido

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-problem" layout="card_grid" density="normal" -->

# O problema

O conhecimento criado em uma sessão não tinha como sobreviver até a seguinte.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Primeira tentativa: pacotes de trabalho
Comentários nas histórias, gerenciados pelo orquestrador. Funcionavam para repasses simples.
<!-- /presentation:card -->
<!-- presentation:card -->
### Onde quebrou
Dois agentes investigando a mesma questão chegavam a conclusões diferentes.
<!-- /presentation:card -->
<!-- presentation:card -->
### No que se transformou
Uma base de conhecimento compartilhada. Uma busca simples com grep nos arquivos Markdown deixou de escalar depois de 50 notas.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="note-structure" layout="split" density="normal" -->

# Como é uma nota

Cada nota é um arquivo Markdown com frontmatter estruturado. Os agentes escrevem por meio do servidor MCP; as pessoas leem no Obsidian.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```yaml
---
title: AI Native Software Distribution
type: concept
tags: [kb-system, architecture, open-source]
confidence:
  source_type: specification
  verified: false
depends_on:
  - kb-system-installer-ux-findings
---
```

<!-- /presentation:column -->
<!-- presentation:column -->
### 6 tipos de nota
plans, research, concepts, insights, decisions, references
### As relações são explícitas
`depends_on`, `parent`, `implements`, `supersedes` no frontmatter. `[[wikilinks]]` no corpo.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="knowledge-base-search" layout="card_grid" density="normal" -->

# Como funciona a busca

A recuperação baseada em embeddings (RAG) achata as relações. A KB combina três sinais por meio de Reciprocal Rank Fusion.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### BM25 (FTS5)
Encontra notas pelo que dizem.
<!-- /presentation:card -->
<!-- presentation:card -->
### Personalized PageRank
Encontra notas pelas relações que estabelecem.
<!-- /presentation:card -->
<!-- presentation:card -->
### Ajustes de confiança
Notas verificadas sobem no ranking. Notas cujas dependências foram atualizadas descem até serem revisadas.
<!-- /presentation:card -->
<!-- /presentation:block -->

Sem embeddings, não há dependência de modelo nem deriva, e a posição de cada resultado é explicável.

<!-- /presentation:slide -->

<!-- presentation:slide id="consolidation-pipeline" layout="card_grid" density="normal" -->

# O pipeline de consolidação

Um sistema de agentes que roda de madrugada (`/consolidate`) e transforma o trabalho disperso do dia em registros duradouros de conhecimento.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Fase 0: Estrutura
3 agentes em paralelo corrigem a integridade dos links, fazem a triagem da caixa de entrada e reparam referências quebradas
<!-- /presentation:card -->
<!-- presentation:card -->
### Fase 1: Coleta
4 agentes em paralelo extraem informações de logs de sessão, PRs, calendário e Slack
<!-- /presentation:card -->
<!-- presentation:card -->
### Fase 2: Síntese
Opus analisa em modo somente leitura, agentes Sonnet executam as edições, Opus revisa o diff
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="distribution" layout="divider" density="normal" -->

# Distribuição

## Construir o instalador da KB mudou minha forma de pensar sobre compartilhar software

<!-- /presentation:slide -->

<!-- presentation:slide id="copying-caveat" layout="emphasis" density="normal" -->

# Uma ressalva

> Tudo o que mostrei hoje foi construído de acordo com a maneira como penso. São minhas ferramentas, moldadas por meus problemas, meus hábitos e minha tolerância a excessos de engenharia.

A questão não é copiá-las.

<!-- /presentation:slide -->

<!-- presentation:slide id="problem-with-copying" layout="content" density="normal" -->

# O problema de copiar

Há mais de 44.000 skills nas plataformas de distribuição e mais de 36.900 estrelas no awesome-cursorrules. **As pessoas copiam esses recursos e os usam sem alterar nada.**

Isso só produz fluxos de trabalho aquém do ideal. Parta da ideia e reconstrua a solução até que ela se encaixe no seu jeito de pensar.

Se copiar não é o caminho, como *deveríamos* distribuir software nativo de IA?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-core-setup" layout="code" density="normal" -->

# Simulação: configuração básica

O instalador faz uma pergunta por vez.

```
Instalador do sistema de base de conhecimento

Vou apresentar os componentes,
pesquisar suas ferramentas e instalar tudo.

Como devo chamar você?
> Sarah

Onde você quer manter sua base de conhecimento?
> ~/dev/kb

De quais fontes o sistema deve coletar informações?
> GitHub, Slack e Google Calendar
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-components" layout="code" density="normal" -->

# Simulação: componentes

Cada componente é apresentado com o que faz e **o que você perde sem ele**.

```
O pipeline de consolidação roda em um agendamento
e coleta dados do GitHub, Slack e Google Calendar.
Sem ele, só entra o que você arquivar explicitamente.

  Incluir o pipeline de consolidação? (recomendado)
  > Sim

O servidor MCP oferece busca ranqueada e validação
de escrita. Sem ele, os agentes usam Glob/Grep sem
nenhum ranking.

  Incluir o servidor MCP? (recomendado)
  > Sim
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-research" layout="code" density="normal" -->

# Simulação: pesquisa

É aqui que um instalador tradicional não consegue acompanhar.

```
Pesquisando integrações para suas 3 fontes...

  [Agente 1] Pesquisando: "GitHub MCP server"
  [Agente 2] Pesquisando: "Slack MCP server"
  [Agente 3] Pesquisando: "Google Calendar MCP server"

  Os 3 agentes de pesquisa concluíram o trabalho.
```

Cada agente verifica todas as opções encontradas: a fonte é confiável? Quais são as permissões? A manutenção está ativa? Há problemas de segurança conhecidos?

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-findings" layout="code" density="normal" -->

# Simulação: resultados

O instalador apresenta o que encontrou, verifica o que já está instalado e executa smoke tests.

```
Fonte: GitHub
  Abordagem: gh CLI (oficial, já instalado)
  Smoke test: gh api user → PASS
  Status: Pronto

Fonte: Slack
  Abordagem: @anthropic/slack-mcp (MCP oficial da Anthropic)
  Status: Não instalado
  "Quer que eu ajude a configurar ou prefere pular por enquanto?"
  > Configurar
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-source-configuration" layout="code" density="normal" -->

# Simulação: configuração das fontes

Perguntas específicas para cada fonte, adaptadas às ferramentas encontradas durante a pesquisa.

```
Para o GitHub: quais repositórios são mais importantes?
> Todos os repositórios em my-org/

Para o Slack: quais canais a consolidação deve examinar?
> #engineering, #incidents e qualquer DM com meu nome

Para o Calendar: qual calendário?
> Principal. As notas das reuniões ficam no Google Docs.

Há algo que você gostaria de personalizar?
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-customization" layout="code" density="normal" -->

# Simulação: personalização

É aqui que o instalador deixa de ser um formulário.

```
> Quero que a consolidação marque automaticamente
  as notas por projeto.

  Marcação automática por projeto: vou verificar se
  o servidor oferece suporte.

  [Agente avaliador iniciado → lendo a base de código do kb-server...]

  Avaliação: mudança apenas de configuração. O servidor já
  infere o projeto pelo caminho do vault. Nenhuma alteração
  no código é necessária.
```

<!-- /presentation:slide -->

<!-- presentation:slide id="dry-run-finalize-generate" layout="split" density="normal" -->

# Simulação: finalizar e gerar

<!-- presentation:block type="split" -->
<!-- presentation:column -->

```
Qual modelo usar nos agentes de análise?
  (padrão: claude-opus-4-6)
> Pode usar o padrão

Quando a consolidação deve rodar?
> Às 2h, apenas em dias úteis

Prosseguir com a instalação?
> Sim
```

<!-- /presentation:column -->
<!-- presentation:column -->

```
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

<!-- presentation:slide id="installer-reads-history" layout="card_grid" density="normal" -->

# O instalador lê seu histórico

Antes da conversa começar, o instalador examina a telemetria das sessões do Claude Code. Com isso, calibra a conversa sem jamais revelar o perfil que traçou.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Nível de detalhe
A informação é a mesma; a forma de apresentá-la muda.
<!-- /presentation:card -->
<!-- presentation:card -->
### Sugestões proativas
O instalador não espera o usuário descrever seu fluxo de trabalho.
<!-- /presentation:card -->
<!-- presentation:card -->
### Opções de personalização
Usuários avançados recebem opções mais profundas que sobrecarregariam um iniciante.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="two-users-same-installer" layout="split" density="dense" -->

# Dois usuários, o mesmo instalador

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Alguém com 10 sessões

```
A skill /kb permite que qualquer sessão
do Claude Code arquive conteúdo na KB
como tarefa em segundo plano. Sem ela,
você escreveria as notas manualmente.

Incluir a skill /kb? (recomendado)
> Sim
```

*Explicação completa. Recomendação clara.*

<!-- /presentation:column -->
<!-- presentation:column -->
### Alguém com 500 sessões

```
Componentes:

| Componente     | Requer       |
|----------------|--------------|
| Vault          | (sempre)     |
| skill /kb      | nada         |
| Consolidação   | agendamento  |
| servidor MCP   | Python 3.12+ |

Quais você quer?
> Todos.
```

*As mesmas informações, em outro nível de detalhe.*

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="three-agents-one-conversation" layout="card_grid" density="normal" -->

# Três agentes, uma conversa

O usuário vê uma única conversa. Por trás dela, três agentes com papéis diferentes.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Instalador
Voltado ao usuário e persistente. Conduz a conversa e inicia subagentes quando necessário.
<!-- /presentation:card -->
<!-- presentation:card -->
### Avaliador
Opera em segundo plano e por pouco tempo. Avalia a viabilidade das solicitações do usuário. Estritamente somente leitura.
<!-- /presentation:card -->
<!-- presentation:card -->
### Implementador
Opera em segundo plano e pode durar bastante. Planeja a implementação, escreve código, testa e valida.
<!-- /presentation:card -->
<!-- /presentation:block -->

O "produto" é o prompt de instalação e uma base de código clara o bastante para uma IA navegar.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-pipeline" layout="divider" density="normal" -->

# O pipeline de tradução

## Os mesmos padrões em outro domínio

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-problem" layout="content" density="normal" -->

# O problema

Meu blog é bilíngue. A primeira versão do sistema de tradução funcionava do jeito óbvio: entregava um post ao modelo e pedia uma versão em português.

O resultado sempre estava correto. **E também sempre saía sem vida.** O sentido fazia a travessia; a voz, o ritmo e a textura retórica ficavam para trás.

<!-- /presentation:slide -->

<!-- presentation:slide id="translation-insight" layout="code" density="normal" -->

# A descoberta

A solução não foi um modelo melhor. Foi fazer o que os institutos de tradução recomendam.

```
source_analysis → terminology_policy → translate → [critique → revise] × N → final_review
```

Um modelo faz a crítica, outro traduz. Assim, o tradutor nunca corrige a própria prova.

<!-- /presentation:slide -->

<!-- presentation:slide id="terminology-policy" layout="code" density="normal" -->

# Como é uma política terminológica

Antes de qualquer tradução começar, a Etapa 2 produz uma política terminológica. **Todas as etapas seguintes ficam vinculadas às decisões dela.**

```json
{
  "keep_english": ["Claude Code", "MCP", "API", "Agent PM"],
  "localize": ["knowledge base" → "base de conhecimento"],
  "resolved_decisions": [{
    "source_term": "harness",
    "preferred_rendering": "harness",
    "scope": "artifact-wide",
    "rationale": "localizing to 'arnês' would lose
                  the metaphor"
  }]
}
```

<!-- /presentation:slide -->

<!-- presentation:slide id="critique-finding" layout="code" density="normal" -->

# Como é um apontamento da crítica

A etapa de crítica não diz "a tradução está 78% boa". **Ela produz apontamentos ancorados em trechos.**

```json
{
  "severity": "major",
  "category": "tone_flattening",
  "source_span": "the voice did not survive the trip",
  "target_span": "a voz não sobreviveu",
  "description": "Lost the rhetorical weight of 'the trip'
    as a metaphor for the act of translation itself",
  "fix_hint": "Restore the journey metaphor:
    'a voz não sobreviveu à travessia'"
}
```

A revisão final verifica se a versão revisada realmente incorporou as correções: verifique, não confie.

<!-- /presentation:slide -->

<!-- presentation:slide id="quality-gate" layout="split" density="dense" -->

# O controle de qualidade

Quem decide é uma rubrica fixa, não o modelo.

<!-- presentation:block type="split" -->
<!-- presentation:column -->

| Dimensão                  | Peso |
| ------------------------ | ---- |
| Fidelidade               | 30%  |
| Terminologia             | 20%  |
| Fidelidade ao Markdown   | 20%  |
| Convenções linguísticas  | 10%  |
| Estilo e registro        | 10%  |
| Convenções locais        | 5%   |
| Clareza para o público   | 5%   |

<!-- /presentation:column -->
<!-- presentation:column -->

| Pontuação                   | Ação        |
| -------------------------- | ----------- |
| ≥ 92, sem erro grave       | Aceitar     |
| 88–92                      | Nova crítica |
| 75–88, ou 2 ciclos travados | Escalar    |
| < 60, ou um erro crítico   | Reprovar    |

<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="where-this-goes-next" layout="card_grid" density="normal" -->

# O que vem pela frente

As traduções parecem escritas em português, não em inglês fantasiado de português. Mas ainda dá para melhorar.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Otimização de prompts com GEPA
Otimizar sistematicamente os prompts de cada etapa, não à mão. Ainda nada conclusivo.
<!-- /presentation:card -->
<!-- presentation:card -->
### Coerência documental
Não há nenhum mecanismo para manter a coerência entre os posts de uma série.
<!-- /presentation:card -->
<!-- presentation:card -->
### Classificação de erros com MQM
As categorias da crítica foram definidas à mão. Migrar para MQM as alinharia à forma como a qualidade de traduções profissionais é medida.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Obrigado

## O agente executa. Seu trabalho é decidir o que ele deve executar.

dan.rio · github.com/danielcavalli

<!-- /presentation:slide -->
