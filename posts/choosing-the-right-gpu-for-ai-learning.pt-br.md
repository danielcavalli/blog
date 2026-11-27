---
title: Escolhendo a configuração certa de GPUs para engenharia de IA (e aprendizado)
excerpt: Uma configuração com duas GPUs intermediárias pode ensinar mais sobre CUDA, otimização e sistemas distribuídos do que uma única placa topo de linha, se o objetivo for aprender observando o sistema em funcionamento.
tags:
- engenharia de IA
- GPU
- CUDA
- sistemas distribuídos
- treinamento distribuído
- hardware
lang: pt-br
translation_of: choosing-the-right-gpu-for-ai-learning.md
source_digest: 8f4834a9c14409b8594561dbedc5d3b5aea4598a644768877d4b38a1ec25b8a4
translated_by: openai/gpt-5.5, via opencode
---

# Escolhendo a configuração certa de GPUs para engenharia de IA (e aprendizado)

Esta máquina não existe para vencer benchmarks. Ela é um laboratório para aprender CUDA, otimização e sistemas distribuídos por experiência direta. Isso muda o critério de escolha: FLOPs de pico importam menos do que a quantidade de fenômenos que você consegue observar antes que as limitações do hardware distorçam a lição. Sob esse critério, duas RTX 5070 Ti vencem uma única placa topo de linha.

## TL;DR

- Quer aprender CUDA + DDP/FSDP e observar comportamento distribuído real? Prefira duas GPUs de 16 GB (por exemplo, duas 5070 Ti). Você troca conforto de GPU única por visibilidade sobre operações coletivas, sobreposição e particionamento.
- Quer iteração mais rápida em GPU única e menos restrições de VRAM? Uma 4090/5090 é o caminho do conforto.
- Os números abaixo refletem fontes públicas e documentação, não medições originais de hardware.

## Para quem é isto

- Desenvolvedores que querem estudar kernels, hierarquia de memória e treinamento distribuído em uma workstation controlada.
- Profissionais que otimizam por amplitude de aprendizado por watt e por hora, não por resultados em rankings.

## Matriz de decisão

| Objetivo | Restrições | Configuração recomendada | Por quê |
|---|---|---|---|
| Aprender treinamento distribuído (DDP/FSDP), perfilar operações coletivas | Custo razoável, gabinete compacto | Duas 16 GB (5070 Ti ou 5080, se o preço fizer sentido) | Grupos de processos reais, sobreposição mensurável e comportamento de buckets |
| Maximizar folga em GPU única | Precisa de contexto/batch maior, atrito mínimo | 4090 ou 5090 | Mais VRAM e vazão, comportamento térmico mais simples |
| Algumas operações coletivas + conforto | Prefere uma GPU única grande, mas quer semântica NCCL real | 4090 + placa CUDA auxiliar (por exemplo, A2000/3060) | Operações coletivas educativas com escalabilidade modesta; limites heterogêneos se aplicam |

## O que o aprendizado exige do hardware

Uma workstation de aprendizado precisa ser capaz de operar em três modos. Ela deve permitir que você inspecione kernels e a hierarquia de memória sem escassez constante de recursos. Deve expor comportamento distribuído real, para que você raciocine sobre sincronização, particionamento e sobreposição de comunicação com evidência, não com intuição. E também precisa ser versátil o bastante para servir como máquina de uso diário; confiabilidade, comportamento térmico e alimentação elétrica fazem parte do currículo, porque instabilidade invalida resultados.

Dezesseis gigabytes de VRAM em uma GPU NVIDIA moderna são suficientes para fundamentos de CUDA, fluxos de trabalho com Nsight, experimentos com Triton e CUTLASS, e loops de treinamento relevantes com modelos médios. Vinte e quatro gigabytes aumentam bastante o conforto: batches maiores, contextos mais longos e menos contornos para limitações de memória. Duas GPUs fazem outra coisa. Elas substituem conforto por visibilidade. Tempo de all-reduce, dimensionamento de buckets, sobreposição com passagens backward, checkpoints particionados, reinicializações elásticas e tratamento de falhas deixam de ser teoria e viram medições que você consegue registrar e explicar.

### VRAM e dimensionamento de modelos (guia rápido)

- ~16 GB: confortável para kernels, Nsight, Triton/CUTLASS e modelos de ~0,7-1,0B parâmetros em BF16 com batches pequenos (o comprimento do contexto importa).
- ~24 GB: batches/contextos maiores; menos contornos de memória; ~1,0-1,3B é prático sem offload.
- 32 GB+: mais folga; ainda assim, algoritmos distribuídos pertencem a outro eixo, diferente de VRAM bruta.

## Arquiteturas, precisão e recursos

RTX 5070 Ti e RTX 5080 são peças da geração Blackwell, com Tensor Cores de quinta geração e suporte a FP4 e FP6 além de FP8/16/32/64. A RTX 4090 é Ada, com Tensor Cores de quarta geração, o que significa ausência de FP4/6, mas excelente vazão em FP8/16 e generosos 24 GB de VRAM. A RTX 5090 leva computação bruta e VRAM ainda mais longe, mas com tamanho e preço que entram em conflito com o objetivo de um laboratório compacto com duas GPUs. Recursos de precisão são interessantes quando você quer estudar estabilidade numérica e eficiência; VRAM é decisiva quando você quer observar trocas entre memória, computação e comunicação sem restrições artificiais.

> Notas sobre precisão e interconexão
>
> - FP4/FP6 aparecem no hardware Blackwell, mas o suporte de kernels/otimizadores nos frameworks ainda está amadurecendo. Espere habilitação gradual.
> - As séries RTX 40/50 de consumo normalmente não têm NVLink; operações coletivas multi-GPU rodam sobre PCIe. P2P pode variar conforme plataforma/BIOS. Use `nvidia-smi topo -m` para inspecionar a topologia quando tiver acesso ao hardware.

## Relações de desempenho que importam para aprender

Framerates exatos são irrelevantes aqui. Escalabilidade relativa basta para estruturar experimentos e verificações de razoabilidade de preço.

> Métodos e premissas (sem hardware local)
>
> - Fonte: dados públicos consolidados (reviews, documentação de fornecedores, benchmarks comunitários confiáveis). Sem medições originais.
> - Lente de carga de trabalho: vazão de treinamento de transformers em BF16; maturidade de kernels (FlashAttention, otimizadores fusionados), drivers e pressão de memória deslocam os números.
> - Interpretação: trate os valores como guias para desenho de experimentos, não como promessas de compra.

A partir de fontes públicas, um modelo prático de trabalho é este: a 5080 é cerca de 13-15% mais rápida que a 5070 Ti em cargas relevantes para treinamento; a 4090 entrega aproximadamente o dobro da 5070 Ti em matemática BF16/FP32 e fica cerca de 50% à frente da 5080; e a 5090 acrescenta mais 50-70% sobre a 5080, além de trazer mais VRAM.

| GPU | VRAM | Geração Tensor | Precisão notável | Vazão relativa de ML usada como referência |
|---|---:|---|---|---:|
| RTX 5070 Ti | 16 GB | 5ª (Blackwell) | FP4/FP6/FP8/FP16 | 1,00 × |
| RTX 5080 | 16 GB | 5ª (Blackwell) | FP4/FP6/FP8/FP16 | ~1,13-1,15 × vs 5070 Ti |
| RTX 4090 | 24 GB | 4ª (Ada) | FP8/FP16 (sem FP4/6) | ~2,0 × vs 5070 Ti; ~1,5 × vs 5080 |
| RTX 5090 | 32 GB | Blackwell | FP4/FP6/FP8/FP16 | ~1,5-1,7 × vs 5080 |

_Tabela: Vazão relativa para cargas orientadas a treinamento. Variação entre frameworks e kernels é esperada; os valores refletem fontes públicas da internet em 2025-10._

Os 8 GB adicionais da 4090 frequentemente importam mais que seus FLOPs. A capacidade de rodar transformers de 1-1,3B parâmetros ou contextos mais longos sem offload muda qualitativamente os tipos de pergunta que você pode fazer. Duas placas de 16 GB não aumentam a capacidade por rank, mas permitem estudar algoritmos distribuídos em hardware real, não por procuração.

## Treinamento distribuído local é o primeiro laboratório; a nuvem é o segundo

Duas GPUs em um único nó dão acesso a DDP e FSDP em condições que você controla. A comunicação acontece sobre PCIe. A latência é baixa, a largura de banda é limitada e o tempo de cada passo se decompõe de forma limpa em fatias de forward, backward, otimizador e comunicação que você consegue perfilar com Nsight Systems e PyTorch profiler. Você verá o efeito dos tamanhos de buckets de gradiente, do particionamento de parâmetros, das políticas de prefetch e reshard, e se computação e comunicação se sobrepõem como deveriam.

Esse conhecimento se transfere. Quando você passa para um nó na nuvem com NVLink ou para um cluster com NVSwitch ou EFA/RDMA, o código não muda. O transporte muda. Operações coletivas hierárquicas ficam mais atraentes, a largura de banda melhora em uma ordem de grandeza e os modos de falha se multiplicam. Esse é o momento correto para medir curvas de escalabilidade e sensibilidade à topologia. Sem o laboratório local, a nuvem só diz que algo ficou mais rápido ou mais lento; ela não diz por quê.

## Formato físico, comportamento térmico e por que uma placa topo de linha de 3 slots complica o aprendizado

Uma única 4090 é simples se você nunca pretende rodar uma segunda GPU. O cooler é grande, os transientes de potência são altos e ela ocupa o espaço físico de que uma segunda placa precisaria para respirar. Você consegue simular comportamento multiprocesso com CUDA MPS e pode praticar orquestração com fatiamento de tempo no Kubernetes, mas não consegue formar um comunicador multi-GPU significativo sem um segundo dispositivo físico ou MIG. Em compensação, a maioria das placas 5070 Ti usa designs de dois slots, deixando espaço para uma segunda placa e entrada de ar adequada. Se o objetivo é estudar sincronização, e não apenas acelerar um único fluxo, esse fato mecânico importa.

## Considerações de alimentação elétrica e estabilidade

Duas 5070 Ti e uma CPU moderna topo de linha consomem aproximadamente 770-860 W de forma sustentada, com envelope transitório de 1,0-1,1 kW. Uma fonte ATX 3.1 de 1000 W é o mínimo que funciona; uma unidade de 1200 W é a escolha correta para operação mais silenciosa e margem. Cada GPU deve estar em seu próprio cabo nativo 12V-2×6. Estabilidade não é métrica de vaidade. É a precondição para medições reproduzíveis e para depurar lógica em vez de perseguir ruído elétrico.

### Lista de materiais/BOM mínima para laboratório com duas GPUs (exemplo)

- CPU com lanes adequadas (por exemplo, classe 7950X/14900K)
- Placa-mãe com dois slots x16 mecânicos e bom espaçamento
- 64-128 GB RAM
- SSD NVMe Gen4/5 de 2 TB+ (útil para offload/checkpointing de FSDP)
- PSU ATX 3.1 de 1000-1200 W, dois 12V-2×6 nativos, cabos separados por GPU
- Gabinete com entrada frontal de ar; duas GPUs de 2 slots cabem sem improviso

Checklist de BIOS: Above 4G Decoding, Resizable BAR, habilitar PCIe P2P se disponível.

## Razoabilidade de preço por paridade de desempenho e elasticidade

Mesmo quando a economia não é o fator principal, o preço não deveria violar uma proporcionalidade básica. Uma verificação útil de paridade toma o preço da 5070 Ti como referência e escala os demais alvos pela vazão relativa. Com uma 5070 Ti perto de R$ 6.500, a paridade proporcional estrita coloca a 5080 em torno de R$ 7.400 e a 5090 em torno de R$ 11.300. A elasticidade então desconta os níveis superiores para refletir retornos educacionais decrescentes e penalidades de economia, produzindo alvos ajustados próximos de R$ 7.000 para a 5080 e R$ 11.500 para a 5090, com faixas de compra imediata e faixas de descarte em torno dessas âncoras. Não são mandamentos, mas convém tentar não pagar demais.

| GPU | Paridade pura vs 5070 Ti | Ótimo ajustado por elasticidade | Faixa de compra imediata | Faixa de descarte |
|---|---:|---:|---:|---:|
| RTX 5070 Ti | R$ 6.500 | R$ 6.500 | ≤ R$ 5.850 | ≥ R$ 7.150 |
| RTX 5080 | ~R$ 7.400 | ~R$ 7.000 | ≤ ~R$ 6.300 | ≥ ~R$ 7.700 |
| RTX 5090 | ~R$ 11.300 | ~R$ 11.500 | ≤ ~R$ 10.350 | ≥ ~R$ 12.650 |

_Tabela: Razoabilidade de preço em relação a uma 5070 Ti como referência. Preços praticados no varejo brasileiro em 2025-10; ajuste ao seu mercado._

Tetos cumprem outro papel. Eles impedem que produtos mais fracos escorreguem para regiões de preço de produtos mais fortes quando existe uma variante superior. Limitar toda a família 5080 a R$ 8.500 e a 5090 a R$ 12.000 preserva a ordenação de valor mesmo quando os preços de rua se movem.

## O compromisso assimétrico da placa auxiliar

Se uma placa grande de 24 GB é atraente pelo conforto, mas você ainda quer semântica NCCL genuína localmente, um arranjo assimétrico é viável. Uma 4090 pode ser combinada com uma placa CUDA curta, fria e de baixo consumo, como uma RTX A2000 ou uma 3060/4060 compacta. O dispositivo menor vira o gargalo e a escalabilidade será modesta, mas criação de grupos de processos, comportamento de all-reduce, estado particionado e tratamento de falhas serão todos reais. Quando os experimentos dependerem de comportamento de interconexão ou paralelismo de tensores, uma sessão na nuvem ainda será necessária.

## Kubernetes, fatiamento de tempo e por que particionar uma 4090 não é MIG

Placas de consumo não expõem MIG. Kubernetes com o NVIDIA device plugin consegue fatiar no tempo uma única GPU entre pods, mas isso não cria múltiplos dispositivos CUDA com VRAM isolada. É útil para ensaiar manifestos, logging e gestão de artefatos. Não substitui operações coletivas multi-GPU. Para algoritmos distribuídos reais, você precisa de pelo menos duas GPUs físicas ou de uma GPU de datacenter com MIG.

## A conclusão e sua lógica

Duas RTX 5070 Ti são o melhor laboratório. Elas maximizam a amplitude de aprendizado por watt e por hora. Permitem estudar CUDA em profundidade e depois subir a pilha até treinamento distribuído sem sair da workstation. Preservam espaço físico e folga elétrica suficientes para continuar confiáveis. Trazem recursos de precisão Blackwell para experimentos em treinamento em baixos bits. Trocam parte do conforto de GPU única por acesso à parte do sistema mais difícil de aprender a partir de um único dispositivo: como múltiplos processos coordenam um trabalho que não conseguem ver. Quando chegar a hora de estudar malhas de interconexão e escalabilidade multi-nó, o mesmo código roda em um nó na nuvem com outro transporte, e as diferenças são mensuráveis.

Uma única GPU grande continua sendo uma escolha legítima para outro objetivo: iteração rápida e menos restrições de memória. Ela é simplesmente outra classe de instrumento. Em um laboratório construído para entender como as peças se encaixam, e não apenas para acelerá-las, duas GPUs intermediárias são a ferramenta mais instrutiva.
