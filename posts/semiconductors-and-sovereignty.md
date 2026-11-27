---
date: 2026-03-11
lang: pt-br
excerpt: Uma resposta técnica ao debate sobre política industrial para semicondutores no Brasil
slug: semiconductors-and-sovereignty
tags:
- semiconductors
- economics
- geopolitics
- brazil
title: 'A cadeia de semicondutores elo por elo e por que tarifas não endereçam nenhum deles'
---

Em coluna recente na CartaCapital, Felipe Augusto Machado e James Görgen publicaram ["Lições do passado"](https://www.cartacapital.com.br/economia/licoes-do-passado/), revisitando a reserva de mercado de informática dos anos 1980 e propondo um conjunto de instrumentos para recuperar soberania produtiva e tecnológica: tarifas estratégicas, golden shares, fortalecimento de estatais, e revisão da diferenciação de empresas por origem de capital. A [thread no X](https://x.com/FelipeAugMac/status/2029881064760488100) trouxe dados de apoio detalhados sobre o desempenho da reserva e o declínio posterior.

Respondi publicamente [no X](https://x.com/dancavlli/status/2029891729080369536), e [recebi uma réplica cuidadosa e bem fundamentada de Machado](https://x.com/FelipeAugMac/status/2030344975272042647). A qualidade da resposta merecia mais do que um fio de tweets, então escrevo aqui com mais espaço para estruturar o argumento. Saliento que escrevo como alguém que vive na intersecção entre economia e infraestrutura de machine learning: formado em Economia pela UFRJ e trabalhando como Senior ML Infrastructure Engineer, lido diariamente com a dependência concreta de hardware que esse debate tenta endereçar.

Contextualizando o leitor, a coluna de Machado e Görgen apresenta dados sobre o desempenho da reserva de mercado como evidência de sucesso. Na minha visão, diria que esses dados são contestáveis: a literatura comparativa sobre liberalização do setor de informática em países em desenvolvimento, como o trabalho de [Dedrick, Kraemer et al. (2001)][17] comparando Brasil e México, conclui que a proteção de uma indústria doméstica de computadores por trás de barreiras não era sustentável em um setor marcado por mudança tecnológica rápida e dominado por multinacionais que definem padrões globais. No entanto, não pretendo entrar nesse debate historiográfico aqui. *O ponto central é outro: mesmo que os dados da reserva fossem inteiramente corretos, a proposta de política que se segue deles não se sustenta quando confrontada com a estrutura técnica da cadeia de semicondutores em 2026.*

O desacordo é sobre os instrumentos propostos e, mais fundamentalmente, sobre o diagnóstico técnico da cadeia que esses instrumentos pretendem endereçar. A cadeia de semicondutores não é uma indústria genérica que responde a incentivos tarifários convencionais. Cada elo tem barreiras de natureza distinta, e nenhuma delas é solucionável por proteção comercial ou participação acionária estatal. Vale desmontá-la elo por elo.

## O elo de design

Projetar um chip moderno não é análogo a escrever software. É definir, em camadas físicas sobrepostas com precisão de nanômetros, como bilhões de transistores se organizam em silício para executar uma função. Esse processo, chamado de [fluxo RTL-to-GDSII][1], começa com uma descrição de hardware em linguagem especializada (Verilog ou VHDL) e termina com um arquivo binário que contém a representação geométrica completa de cada camada do chip, pronto para ser enviado à foundry.

Entre a concepção inicial e esse arquivo final há dezenas de etapas interdependentes, cada uma com seus próprios problemas de otimização: [síntese lógica][2] (tradução da descrição RTL em portas lógicas, um problema NP-hard que depende de heurísticas), [floorplanning e placement][3] (definição da posição física de cada bloco e célula no die, otimizando área, timing e consumo de energia), [clock tree synthesis][3] (distribuição do sinal de clock com variação mínima para bilhões de transistores), [roteamento][3] (conexão física de todos os sinais respeitando regras de espaçamento e integridade de sinal), e [verificação de timing, DRC e LVS][3] (validação de que o layout físico corresponde ao esquemático e atende as limitações de velocidade e regras de fabricação da foundry). Cada etapa exige ferramentas especializadas de EDA (Electronic Design Automation), um mercado que é um [oligopólio por sí só][4]: Synopsys (31% do mercado global), Cadence (30%) e Siemens EDA (13%) detêm juntas mais de 85% da receita global de EDA, segundo dados da TrendForce e Griffin Securities.

Mas a barreira técnica mais crítica não está nas ferramentas. Está no PDK.

Um [Process Design Kit][5] é o conjunto de arquivos que uma foundry fornece a seus clientes para que projetem chips dentro daquele processo específico. O PDK não é documentação genérica. É o mapa proprietário de como aquela foundry deposita materiais, realiza dopagem, define espessuras de camada, tolera variações de processo e organiza suas regras de design. Contém [bibliotecas de standard cells, modelos de transistor (tipicamente BSIM), parâmetros físicos de cada camada e regras de verificação DRC][6]. Sem ele, um time de design não tem como garantir que o que projetou vai corresponder ao que será fabricado. Cada foundry tem o seu, incompatível com as demais.

O PDK encapsula décadas de aprendizado de processo acumulado pela foundry. É [atualizado com frequência e essa atualização é sincronizada com os servidores de licença das ferramentas EDA][7]. Se o designer não tiver licença ativa e PDK atualizado, não consegue verificar se o design está compatível com o processo atual da foundry.

Aqui entra a barreira geopolítica. PDKs de nós avançados são licenciados pelas foundries sob NDA e [classificados pelo Bureau of Industry and Security americano como itens de controle de exportação, sob o ECCN 3E001 da Commerce Control List][8]. Qualquer universidade ou empresa fora dos EUA que queira receber um PDK controlado precisa de um Technology Control Plan aprovado e, dependendo do país, de uma licença do Department of Commerce. Em outubro de 2023, [o BIS expandiu essas restrições para cobrir explicitamente software EDA e ferramentas de design para chips abaixo de 16/14nm][9], buscando impedir que empresas enviassem arquivos de design avançados para foundries externas.

A relação entre um time de design e uma foundry, portanto, não é uma transação de mercado que uma tarifa doméstica possa replicar ou substituir. É uma parceria tecnológica bilateral, controlada por regulação americana, que exige confiança estabelecida, NDA, licenciamento formal e vínculo operacional contínuo com o processo físico daquela foundry específica. Nenhum instrumento de proteção comercial cria esse vínculo, e nenhuma golden share o desbloqueia.

E o custo de chegar ao fim desse processo é estruturalmente alto. Segundo a [IBS (International Business Strategies)][10], o custo total de design de um chip em 5nm atinge US$416 milhões, com o tapeout isolado custando entre US$40 e US$50 milhões, chegando a US$100 milhões no nó de 2nm. Esses custos não garantem sucesso: a [taxa de falha no primeiro tapeout fica entre 15% e 35%][11], exigindo iterações ("spins") que multiplicam tempo e capital. Há casos documentados em que um único IP analógico exigiu 18 tapeouts ao longo de 8 anos para ser validado.

## O elo de front-end de fabricação

Aqui a barreira muda de natureza. Não é apenas o equipamento, embora a ASML seja o [único fornecedor mundial de litografia EUV][12] para nós abaixo de 7nm. A barreira é o conhecimento de processo acumulado iterativamente ao longo de gerações, dado que a fabricação de um chip em nó avançado exige [mais de 1.000 etapas sequenciais de processo][13] (deposição, dopagem, etching, litografia, planarização, inspeção), cada uma calibrada por um feedback loop entre equipamento, yield real em volume e as características físicas específicas daquele processo. Como descreve a [literatura de engenharia de fabricação][14], cada etapa adicional aumenta tempo, custo e probabilidade de formação de defeitos que matam o dispositivo. Esse acúmulo de conhecimento de iterativo não pode ser comprado nem licenciado. Ele só existe como resultado de décadas de operação em volume.

É por isso que mesmo a China, com [mais de US$150 bilhões de investimento público][15] via o Big Fund e fundos locais desde 2014, e mobilização nacional explícita, opera hoje com um gap de pelo menos uma geração inteira em relação à TSMC. Se subsídio massivo e vontade política fossem suficientes, a China já teria resolvido o problema. [Não resolveu][16]. Esse dado empírico é mais eloquente do que qualquer modelo teórico sobre política industrial.

## O elo de back-end e OSAT

Esse é o elo mais acessível da cadeia mas, antes de discutir como países estão entrando nele, vale examinar o que exatamente se fabrica em nós maduros (28nm e acima) e por que dominar essa fatia da cadeia *não endereça nenhuma preocupação real de soberania tecnológica*.

Chips fabricados em nós maduros são usados em [dispositivos analógicos, semicondutores de potência, display drivers, chips automotivos, MEMS, produtos de RF e sensores][24]. São componentes essenciais, mas são commodities industriais com margens em compressão. A China está expandindo agressivamente sua capacidade nesses nós: segundo a [TrendForce, a China deve ultrapassar Taiwan em capacidade de foundry em nós maduros até 2027][25], e a [projeção é de 31% da capacidade global de 28nm até aquele ano][26]. Essa expansão, subsidiada pelo Estado chinês, já está gerando [sobrecapacidade e pressão de preços][24]: a utilização média de capacidade em nós maduros ficou abaixo de 80% em 2024 e a Hua Hong Semiconductor, segunda maior foundry chinesa, [operou com margem bruta de 10,9% e prejuízo líquido no segundo trimestre de 2025][27]. É um mercado que caminha para commoditização acelerada, não para margens estratégicas.

Os chips que de fato importam para soberania tecnológica operam em nós completamente diferentes. Aceleradores de IA como as GPUs da NVIDIA (H100, B200, Blackwell), os TPUs da Google (Ironwood) e os chips custom da Microsoft (Maia), Amazon (Trainium) e OpenAI são todos fabricados em [processos de 7nm, 5nm ou abaixo, exclusivamente pela TSMC][28]. A TSMC detém [essencialmente 100% do market share em semicondutores lógicos para data centers de IA][29]. Mesmo em aplicações militares, onde se poderia imaginar que nós maduros bastariam, a [realidade é mais nuançada][30]: sistemas legados de fato usam nós de 45nm a 250nm por razões de confiabilidade e resistência a radiação, mas as aplicações emergentes de IA em defesa (sistemas autônomos, guerra eletrônica, processamento de dados em tempo real) dependem de nós sub-5nm.

Ou seja: investir em capacidade de fabricação de 28nm no Brasil não endereça a dependência que importa: os chips que fariam falta num cenário real de restrição à soberania nacional, como aceleradores de IA, processadores de alta performance e chips de comunicação 5G avançados, não podem ser fabricados em nós maduros e os chips que podem ser fabricados em nós maduros estão em processo de commoditização global acelerada pela China, com margens que não justificam o investimento.

Dito isso, a Índia entrou no elo de back-end/OSAT, e o caso merece atenção porque o mecanismo foi o oposto do protecionismo. A mudança de política que viabilizou os investimentos foi a [revisão do Semicon India Programme em dezembro de 2022][31], quando o gabinete de Modi uniformizou o subsídio em 50% do custo do projeto para qualquer nó de processo (o esquema original graduava de 30% a 50% conforme o nó), removeu a janela de 45 dias para submissão de propostas, e abriu o incentivo para nós maduros.

Os resultados vieram rápido. Seis meses depois, a Micron anunciou [US$2,75 bilhões para uma planta ATMP em Gujarat][18], com o governo federal cobrindo 50% do custo. A [Tata entrou com joint venture com a PSMC de Taiwan para um fab de 28nm em Dholera][19], e o [CG Power firmou parceria tripartite com a Renesas e a Stars Microelectronics da Tailândia][19]. Em todos os casos, o instrumento foi atração de capital e parceiro tecnológico externo com abertura de mercado, não barreira tarifária.

## O que é mais importante: Setor de serviços avançados ou indústria sem margem?

A concentração de mercado em ARM e NVIDIA, que Machado e Görgen corretamente identificam, é real. Mas vale entender o que essas empresas de fato fazem, porque isso ilumina onde está o valor na cadeia.

A NVIDIA, uma das empresas mais valiosas do mundo em capitalização de mercado, não fabrica um único chip. É uma empresa [fabless][22]: projeta GPUs e aceleradores de IA e terceiriza 100% da fabricação para a TSMC. A ARM vai além: não projeta chips e não fabrica nada. Licencia um conjunto de instruções (ISA) e arquiteturas de referência para que outros projetem seus próprios processadores. A Qualcomm, que licencia a ISA da ARM para seus processadores Snapdragon, é ela mesma fabless e [depende da TSMC e da Samsung Foundry para toda a fabricação][32]. Broadcom, AMD, MediaTek: todas fabless, todas dependentes de foundries asiáticas.

O padrão é claro: as empresas que dominam a cadeia de semicondutores não possuem fábricas. Possuem IP, arquiteturas, ecossistemas de software e relações contratuais com foundries. O valor está na camada de design e na propriedade intelectual, não na posse de capacidade fabril. Tarifas e golden shares não criam nada disso porque não criam IP, não acumulam conhecimento de processo, não desbloqueiam acesso a PDKs controlados geopoliticamente e não geram a escala de mercado que torna um OSAT viável internacionalmente. Mais importante: não atraem o parceiro tecnológico externo sem o qual nenhum elo dessa cadeia se constrói hoje.

Vale notar que mesmo os países que decidiram investir pesado em capacidade doméstica de semicondutores não usaram tarifas para fazê-lo. O [CHIPS Act americano][20] mobiliza US$52 bilhões em subsídios diretos e incentivos fiscais, o [EU Chips Act][21] mobiliza €43 bilhões, e o [Semicon India Programme][18] oferece matching de 50% para atrair parceiros tecnológicos. O instrumento em todos os casos é investimento direto em P&D e infraestrutura vinculado a compromissos de produção e transferência de conhecimento, não proteção comercial.

## O que o debate ainda precisa responder

A pergunta que o debate precisa enfrentar é objetiva: qual instrumento (econômico) específico endereça qual barreira específica, em qual elo da cadeia, com qual parceiro tecnológico e para qual mercado de saída?

Para o elo de design, a barreira é acesso a PDKs, ferramentas EDA e relação contratual com foundries. O instrumento relevante seria formação de capital humano, acordos bilaterais de acesso tecnológico, e investimento em design houses com vínculo a foundries existentes. E é aqui, na minha leitura, que está a oportunidade real do Brasil.

O  [modelo fabless][22] ilustra bem esse ponto. As maiores empresas de semicondutores do mundo, com a NVIDIA à frente seguida por Qualcomm, Broadcom, AMD e MediaTek, não possuem fábricas: projetam chips e terceirizam a fabricação para foundries como TSMC e Samsung. [Empresas americanas detêm cerca de 71% desse mercado][23], e o fazem competindo em arquitetura, propriedade intelectual e ecossistema de software, não em capacidade fabril. Uma design house é, no fundo, uma empresa de serviços de alta complexidade com margens que refletem isso: a NVIDIA opera com margem bruta acima de 70%, enquanto foundries de nós maduros como a Hua Hong lutam para manter 11%.

Para o elo de fabricação front-end, a barreira é conhecimento de processo acumulado em décadas de operação em volume. A resposta realista passa por investimento em P&D de processo em parceria com foundries existentes e formação de engenheiros capazes de operar dentro desses ecossistemas, não por tentar replicar fabs em território nacional via subsídio estatal.

Para o elo de OSAT, a barreira é menor, mas ainda exige integração com cadeias globais de fornecedores e clientes. O caminho mais direto é facilitar a operação de OSATs internacionais no país via ambiente regulatório competitivo e acordos de cooperação tecnológica, como a Índia fez ao atrair a Micron para Gujarat.

Essa distinção é central para o debate sobre o Brasil. A economia do século XXI recompensa desproporcionalmente *serviços* intensivos em conhecimento e o país já demonstrou capacidade nesse tipo de atividade, da automação bancária dos anos 80 ao ecossistema de fintechs atual. O debate sobre desenvolvimento econômico no Brasil tende a tratar soberania como sinônimo de capacidade fabril instalada, o que leva naturalmente a propostas de tarifas e estatais. Porém, na cadeia de semicondutores, insistir em capacidade fabril de semicondutores como caminho para soberania é perseguir o elo de menor margem e maior barreira de capital da cadeia, quando a camada de maior valor agregado e menor barreira de capital é justamente a de design, que é uma atividade de serviços intensiva em conhecimento. Formar engenheiros, viabilizar acesso a PDKs e ferramentas EDA via acordos com foundries e criar condições para que design houses operem no país com acesso a mercados globais seria uma estratégia mais alinhada tanto com as vantagens comparativas brasileiras quanto com a estrutura real da cadeia.

E escrevo tudo isso sem sequer entrar na cadeia de insumos críticos por trás da fabricação: os photoresists são dominados por um punhado de empresas japonesas (Tokyo Ohka Kogyo, JSR, Shin-Etsu), as lentes e espelhos dos equipamentos de litografia são fornecidos exclusivamente pela Zeiss, o hélio ultrapuro necessário para os processos de deposição e refrigeração é um recurso geologicamente escasso com oferta concentrada em poucos países e as fotomáscaras para nós avançados são produzidas por um oligopólio que inclui Photronics e Toppan. Cada um desses elos tem suas próprias barreiras de entrada e nenhum deles responde a tarifas.

Na minha análise dessa cadeia, diria que tarifas e golden shares não endereçam as barreiras reais de nenhum desses elos. Machado e Görgen atribuem os problemas das últimas décadas a ausência dessas políticas. Discordo do diagnóstico. Se esses mecanismos funcionam ou não em outros setores é um debate legítimo e mais amplo do que cabe neste texto porém meu objetivo aqui é elucidar a complexidade e maturidade desse setor, além do nível de integração internacional necessário para a manufatura de chips. O que me parece importante, independentemente da leitura que se faça dos anos 80/90, é que os instrumentos propostos não se encaixam na estrutura técnica da cadeia que pretendem endereçar. Tarifas sobre semicondutores e eletrônicos encarecem os insumos de quem mais depende deles: a indústria de serviços digitais, o agronegócio que precisa de IoT e automação, o sistema financeiro que roda sobre chips importados, o SUS que depende de equipamentos eletrônicos. Sem parceiro tecnológico e sem endereçar as barreiras reais de cada elo, o efeito prático seria tributar a competitividade dos setores que o Brasil já tem.

A cadeia de semicondutores exige instrumentos tão sofisticados quanto a tecnologia que se pretende dominar. Sem essa granularidade técnica, qualquer proposta de política corre o risco de repetir o erro simétrico: mobilizar recursos nacionais na direção errada, novamente.

---

**Fontes:**

[1] MDPI Electronics, *Comprehensive RTL-to-GDSII Workflow for Custom Embedded FPGA Architectures Using Open-Source Tools*, 2025. [mdpi.com/2079-9292/14/19/3866](https://mdpi.com/2079-9292/14/19/3866)

[2] ScienceDirect, *Logic Synthesis* (overview). Cobre a complexidade NP-hard dos problemas de síntese lógica e as limitações de escalabilidade das ferramentas atuais. [sciencedirect.com/topics/computer-science/logic-synthesis](https://www.sciencedirect.com/topics/computer-science/logic-synthesis)

[3] Kahng, A.B., Lienig, J., Markov, I.L., Hu, J., *VLSI Physical Design: From Graph Partitioning to Timing Closure*, Springer, 2011. Referência canônica cobrindo floorplanning, placement, CTS, roteamento e verificação. Também referenciado em: Bharadwaj, V. et al., *Physical Design: Methodologies and Developments*, arXiv:2409.04726, 2024. [arxiv.org/html/2409.04726v1](https://arxiv.org/html/2409.04726v1)

[4] TrendForce e Griffin Securities (DAC 2024). Synopsys 31%, Cadence 30%, Siemens EDA 13%, combinando mais de 85% da receita global de EDA. Reportado em: Embedded.com, *Taking Stock of the EDA Industry*, 2025. [embedded.com/taking-stock-of-the-eda-industry](https://www.embedded.com/taking-stock-of-the-eda-industry/)

[5] Wikipedia, *Process Design Kit*. [en.wikipedia.org/wiki/Process_design_kit](https://en.wikipedia.org/wiki/Process_design_kit)

[6] Semionics, *Mastering the PDK/TDK: Essential Knowledge for Every VLSI Engineer*, 2025. Detalha o conteúdo do PDK (standard cells, modelos BSIM, techfiles, decks DRC/LVS) e sua função por perfil de engenheiro. [semionics.com/mastering-the-pdk-tdk-essential-knowledge-for-every-vlsi-engineer](https://semionics.com/mastering-the-pdk-tdk-essential-knowledge-for-every-vlsi-engineer/)

[7] ChinaTalk, *Holes In the Chip Design Software Export Controls*, 2024. [chinatalk.media/p/holes-in-the-chip-design-software](https://chinatalk.media/p/holes-in-the-chip-design-software)

[8] Stony Brook University / Office of Research Security, *Using Process Design Kits (PDK) in Research Projects*. [stonybrook.edu/commcms/ors/export_controls/Guidance_and_Procedures/PDK](https://stonybrook.edu/commcms/ors/export_controls/Guidance_and_Procedures/PDK)

[9] Congressional Research Service, *U.S. Export Controls and China: Advanced Semiconductors*, atualizado 2025. [congress.gov/crs-product/R48642](https://congress.gov/crs-product/R48642)

[10] IBS (International Business Strategies), citado por Handel Jones (CEO). Dados reportados em: Semiconductor Engineering, *What Will That Chip Cost?*, 2023. [semiengineering.com/what-will-that-chip-cost](https://semiengineering.com/what-will-that-chip-cost/); Andy Lin's Investment Blog. [granitefirm.com/blog/us/2023/04/29/cost-of-chip-foundry](https://granitefirm.com/blog/us/2023/04/29/cost-of-chip-foundry)

[11] AllPCB / AllElectroHub, *Chip Design and Tapeout: Key Processes Explained*. [allpcb.com/allelectrohub/chip-design-and-tapeout-key-processes-explained](https://allpcb.com/allelectrohub/chip-design-and-tapeout-key-processes-explained)

[12] ASML detém 100% do mercado de litografia EUV e mais de 80% do mercado total de litografia. Wikipedia, *ASML Holding*. [en.wikipedia.org/wiki/ASML_Holding](https://en.wikipedia.org/wiki/ASML_Holding); TrendForce, *ASML EUV Dominance & China's Semiconductor Equipment Push*, 2025. [trendforce.com/insights/asml-euv](https://www.trendforce.com/insights/asml-euv)

[13] Newport Corporation, *Semiconductor Manufacturing*. O nó de 7nm exige mais de 1.000 etapas de processo; o nó de 45nm exigia 500. [newport.com/n/semiconductor-manufacturing](https://www.newport.com/n/semiconductor-manufacturing)

[14] May, G.S. e Spanos, C.J., *Fundamentals of Semiconductor Manufacturing and Process Control*, Wiley, 2006. Cobre a relação entre número de etapas, yield e custo. Também: KLA, *Semiconductor Chip Manufacturing 101*. [kla.com/advance/education/chip-manufacturing-101](https://www.kla.com/advance/education/chip-manufacturing-101)

[15] Semiconductor Industry Association, *Taking Stock of China's Semiconductor Industry*, 2021. Estima investimento público chinês acima de US$150 bilhões entre 2014 e 2030. [semiconductors.org/taking-stock-of-chinas-semiconductor-industry](https://www.semiconductors.org/taking-stock-of-chinas-semiconductor-industry/); Bruegel, *Lessons for Europe from China's quest for semiconductor self-reliance*. [bruegel.org/policy-brief/lessons-europe-chinas-quest-semiconductor-self-reliance](https://www.bruegel.org/policy-brief/lessons-europe-chinas-quest-semiconductor-self-reliance)

[16] Tom's Hardware, *The state of China's decade-long semiconductor push: still a decade behind, despite hundreds of billions spent*, 2026. [tomshardware.com/tech-industry/semiconductors/the-state-of-chinas-decade-long-semiconductor-push](https://www.tomshardware.com/tech-industry/semiconductors/the-state-of-chinas-decade-long-semiconductor-push-still-a-decade-behind-despite-hundreds-of-billions-spent-and-significant-progress-examining-the-original-made-in-china-2025-initiative)

[17] Dedrick, J., Kraemer, K.L., Palacios, J., Tigre, P.B., Botelho, A.J.J., *Economic Liberalization and the Computer Industry: Comparing Outcomes in Brazil and Mexico*, World Development, vol. 29/7, 2001. [sciencedirect.com/science/article/abs/pii/S0305750X01000389](https://www.sciencedirect.com/science/article/abs/pii/S0305750X01000389)

[18] ITIF, *Assessing India's Readiness to Assume a Greater Role in Global Semiconductor Value Chains*, 2024. [itif.org/publications/2024/02/14/india-semiconductor-readiness](https://itif.org/publications/2024/02/14/india-semiconductor-readiness/)

[19] Carnegie Endowment, *The U.S.–India Initiative on Critical and Emerging Technology (iCET) from 2022 to 2025*, 2024. Detalha Tata-PSMC (Dholera), CG Power-Renesas-Stars Microelectronics (Sanand), e Micron ATMP (Gujarat). [carnegieendowment.org/research/2024/10/the-us-india-initiative-on-critical-and-emerging-technology-icet](https://carnegieendowment.org/research/2024/10/the-us-india-initiative-on-critical-and-emerging-technology-icet-from-2022-to-2025-assessment-learnings-and-the-way-forward)

[20] CHIPS and Science Act. US$52 bilhões em investimentos federais para semicondutores. Via SIA Whitepaper, 2021. [semiconductors.org/wp-content/uploads/2021/07/Taking-Stock-of-China's-Semiconductor-Industry_final.pdf](https://www.semiconductors.org/wp-content/uploads/2021/07/Taking-Stock-of-China%E2%80%99s-Semiconductor-Industry_final.pdf)

[21] European Commission, *European Chips Act*. €43 bilhões em investimentos públicos e privados. [commission.europa.eu/strategy-and-policy/priorities-2019-2024/europe-fit-digital-age/european-chips-act_en](https://commission.europa.eu/strategy-and-policy/priorities-2019-2024/europe-fit-digital-age/european-chips-act_en)

[22] TrendForce, via EE News Europe, *How Nvidia dominated the 2024 fabless chip market*, 2025. NVIDIA liderou com receita igual à soma das outras nove do top 10. [eenewseurope.com/en/how-nvidia-dominated-the-2024-fabless-chip-market](https://www.eenewseurope.com/en/how-nvidia-dominated-the-2024-fabless-chip-market/)

[23] Valuates Reports, *Fabless Semiconductor Market 2024-2030*. Empresas americanas detêm ~71% do mercado global de IC fabless em 2023. [reports.valuates.com/market-reports/QYRE-Auto-4L17956/global-fabless-semiconductor](https://reports.valuates.com/market-reports/QYRE-Auto-4L17956/global-fabless-semiconductor)

[24] Bureau of Industry and Security (BIS), U.S. Department of Commerce, *Public Report on the Use of Mature-Node Semiconductors*, dezembro 2024. Documenta overcapacidade chinesa, pressão de preços e usos típicos de nós maduros (analógico, discreto, optoeletrônico, automotivo). [bis.gov/media/documents/public-report-use-mature-node-semiconductors-december-2024](https://www.bis.gov/media/documents/public-report-use-mature-node-semiconductors-december-2024)

[25] The Economy, *With Advanced Nodes Blocked, China Opens a Detour: Seizing Control of the $56 Billion Semiconductor Market's "Midsection"*, janeiro 2026. TrendForce: Taiwan 43% vs. China 34% em capacidade de nós maduros em 2024; China deve ultrapassar Taiwan até 2027. [economy.ac/news/2026/01/202601286396](https://economy.ac/news/2026/01/202601286396)

[26] Mordor Intelligence, *China Semiconductor Device Market*, 2025. Projeção de 31% da capacidade global de 28nm pela China até 2027. [mordorintelligence.com/industry-reports/china-semiconductor-device-market](https://www.mordorintelligence.com/industry-reports/china-semiconductor-device-market)

[27] AInvest, *Hua Hong Semiconductor's Profit Slump*, 2025. Margem bruta de 10,9% e prejuízo líquido de US$32,8 milhões no Q2 2025; capex de US$2,7 bilhões em 2024 para nós 28nm/22nm com risco de perdas operacionais em 2025. [ainvest.com/news/hua-hong-semiconductor-profit-slump-cautionary-tale-semiconductor-investors-2025-2508](https://www.ainvest.com/news/hua-hong-semiconductor-profit-slump-cautionary-tale-semiconductor-investors-2025-2508/)

[28] Tom's Hardware, *Inside the AI accelerator arms race*, 2025. Todos os aceleradores de IA de NVIDIA, Google, Amazon, Microsoft e OpenAI são fabricados pela TSMC em 5nm/3nm. [tomshardware.com/tech-industry/artificial-intelligence/inside-the-ai-accelerator-arms-race](https://www.tomshardware.com/tech-industry/artificial-intelligence/inside-the-ai-accelerator-arms-race-amd-nvidia-and-hyperscalers-commit-to-annual-releases-through-the-decade)

[29] Semiconductor Engineering, *TSMC: King Of Data Center AI*, 2025. TSMC detém essencialmente 100% do market share em semicondutores lógicos para data centers de IA. [semiengineering.com/tsmc-king-of-data-center-ai](https://semiengineering.com/tsmc-king-of-data-center-ai/)

[30] Geopolitics Unplugged, *Tiny Chips, Big Myths: How Military Systems Actually Use Semiconductors*, 2024. Sistemas militares usam predominantemente nós de 45nm-250nm por durabilidade; aplicações emergentes de IA em defesa exigem sub-5nm. [geopoliticsunplugged.substack.com/p/ep103-tiny-chips-big-myths-how-military](https://geopoliticsunplugged.substack.com/p/ep103-tiny-chips-big-myths-how-military)

[31] DGA Group, *2023 A Key Year For India's Semiconductor Industry Strategy*, 2023. Detalha a revisão do Semicon India Programme em dezembro de 2022: subsídio uniformizado em 50% para qualquer nó, remoção da janela de 45 dias, abertura para nós maduros. [dgagroup.com/insight/asg-analysis-2023-key-year-indias-semiconductor-industry-strategy](https://dgagroup.com/insight/asg-analysis-2023-key-year-indias-semiconductor-industry-strategy/); PIB (Press Information Bureau), Government of India, *Modified Semicon India Programme*, junho 2023. [pib.gov.in/PressReleasePage.aspx?PRID=2039638](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2039638)

[32] SlashGear, *Who Makes Snapdragon Chips & Where Are They Built?*, 2025. Qualcomm é fabless e depende da TSMC e Samsung Foundry para fabricação de todos os seus chips Snapdragon. [slashgear.com/1884245/snapdragon-chips-who-makes-where-built-explained](https://www.slashgear.com/1884245/snapdragon-chips-who-makes-where-built-explained/); TechSpot, *Samsung loses Qualcomm contract to TSMC for Snapdragon 8 Elite Gen 2*, 2024. [techspot.com/news/106129-samsung-faces-challenges-tsmc-secures-exclusive-contract-qualcomm](https://www.techspot.com/news/106129-samsung-faces-challenges-tsmc-secures-exclusive-contract-qualcomm.html)
