---
title: Uma configuração de rede que funciona para mim
excerpt: 'Uma escolha pragmática de rede doméstica: menos complexidade de datacenter, mais coerência, segmentação clara e hardware que para de exigir atenção.'
tags:
- rede
- Home Server
- UniFi
- UDR7
lang: pt-br
translation_of: a-network-setup-that-works-for-me.md
source_digest: 6088c6e47b5b8831f57884205873c3f12bca5148a829a0d75a2de697bbbc6f34
translated_by: openai/gpt-5.5, via opencode
---

Uma boa rede não deveria exigir atenção. Esse foi o princípio por trás da montagem do meu Home Server. O objetivo era claro: uma rede rápida, segura e estável, sem ajuste constante. Eu não queria complexidade corporativa nem um rack de luzes piscando ocupando metade da minha prateleira. O hardware precisava ser acessível, confiável, compacto e agradável de ver. Uma tarefa impossível, ou assim parecia.

## Quais eram as opções

Três ecossistemas apareceram como candidatos: Omada, pfSense e UniFi. Cada um prometia controle e estabilidade no próprio idioma. O Omada parecia polido à primeira vista, com uma interface limpa e promessas de integração sem atrito. Quanto mais eu explorava, porém, mais ficava claro que ele tinha sido feito para ambientes corporativos. É estável, poderoso e bem desenhado, mas pressupõe estrutura: controladores, gateways e switches, todos gerenciados por um sistema centralizado que espera disciplina e escala. Dá para configurar VLANs e ajustar regras de acesso com precisão, mas a experiência se parece mais com montar um pequeno escritório do que uma casa. Funciona bem, só que parece sempre operar uma camada acima do lugar onde você de fato vive.

O pfSense ficava no extremo oposto desse espectro. Ele oferecia tudo que o Omada não oferecia: transparência, profundidade e um controle quase cirúrgico sobre cada pacote que passa pelos seus cabos. Mas cobrava algo em troca que eu não estava disposto a entregar: tempo. Você não apenas configura o pfSense. Você estuda o pfSense. Você molda regras, gerencia sub-redes e, aos poucos, percebe que transformou sua casa em um pequeno datacenter. Ele é bonito pela completude, mas pesado pelas consequências. Eu admirava, mas não queria conviver com isso.

Sobrava o UniFi, discreto entre os dois, como uma ponte entre praticidade e profundidade. Ele falava nos mesmos termos técnicos do pfSense, mas os traduzia para algo usável. A interface parecia coerente, os dispositivos pareciam pertencer ao mesmo conjunto e o ecossistema inteiro dava a impressão de ter sido desenhado por uma única cabeça. VLANs, roteamento e DHCP se conectavam de um jeito que não parecia abstrato. Parecia intencional. Foi isso que me chamou atenção. Eu não queria algo perfeito. Queria algo que fizesse sentido. O UniFi entregou.

## Por que UniFi era a resposta óbvia

O que me convenceu no UniFi não foi potência nem marketing. Foi coerência. Tudo nele parece ter sido desenhado por alguém que entende o que significa conviver com uma rede. A interface é limpa, mas não rasa. As opções são profundas, mas nunca excessivas. A configuração parece um processo do qual você participa, não uma batalha que precisa vencer. Você conecta o aparelho, abre o controlador e quase imediatamente as coisas começam a fazer sentido. VLANs, DHCP, regras de firewall e roteamento estão todos ali, organizados de um jeito ao mesmo tempo familiar e deliberado. É um daqueles sistemas raros em que as coisas simplesmente se comportam como deveriam, e essa confiabilidade muda a relação que você tem com ele. Você para de verificar se funciona e começa a confiar que funciona.

O que realmente se destaca é a completude do ecossistema. Dá para montar uma rede inteira sem sair do mundo UniFi. Tudo fala a mesma língua. Tudo se integra sob a mesma lógica. Essa consistência remove a ansiedade de tentar adivinhar se as peças vão cooperar. É um tipo de harmonia que a maioria das marcas promete, mas quase nunca alcança. O hardware é bem construído, o software parece maduro e as atualizações chegam com propósito, não como interrupção.

Essa completude também facilita a tomada de decisão, porque você não precisa juntar peças de fabricantes diferentes nem se preocupar com padrões desencontrados. Você escolhe as partes que atendem aos seus requisitos e elas se encaixam. Para alguém como eu, que queria uma configuração confiável mas não quer passar fins de semana enterrado em menus, isso importa mais do que desempenho bruto. Melhor ainda quando essa confiabilidade e essa integração vêm acompanhadas de um desempenho realmente bom.


## A facilidade com que os custos sobem 

Tudo sempre começa com algo razoável. Para mim, era o UCG-Max: pequeno, silencioso e forte o bastante para lidar com VLANs, DHCP e IPS sem problemas. Quatro portas 2.5 GbE e capacidade para algumas centenas de clientes. Uma base sólida.

Aí você começa a pensar no que mais seria possível. O UCG-Fiber adiciona uplinks de 10 Gb e um switch integrado de quatro portas. Coloque armazenamento NVMe para o Protect e, de repente, você não está montando um roteador. Está montando o núcleo da rede.

Quando você começa a pensar assim, o E7 vira o caminho óbvio. Wi-Fi 7, uplink de 10 GbE e capacidade suficiente para fazer a rede sem fio parecer real, não apenas conveniente. O que significa que tudo acima dele precisa acompanhar, e você precisa de PoE de verdade.

Aí você precisa do Switch Enterprise 8 PoE para amarrar tudo. Oito portas 2.5 GbE PoE+, dois uplinks SFP+ de 10 Gb e roteamento Layer 3. Ele faz tudo parecer completo. Também torna o orçamento real.

Cada peça faz sentido sozinha: UCG-Max como começo sólido, UCG-Fiber para margem de crescimento, E7 para a rede sem fio, Enterprise 8 PoE para conectar tudo. Juntas, elas são muito mais do que uma rede doméstica precisa. É aí que você percebe que contenção também importa.

## Por que UniFi era a resposta IMPOSSÍVEL 

Eu continuava tentando montar a configuração perfeita na cabeça: um gateway, um ponto de acesso e um switch para conectá-los. Então encontrei o UniFi Dream Router 7 (UDR7) e percebi que não precisava disso. Ele faz tudo que aquelas três caixas fariam: lida corretamente com VLANs e DHCP, traz Wi-Fi 7 integrado e inclui algumas portas multi-gig para dispositivos cabeados. Cabe em uma prateleira, não parece equipamento de rede e custa menos do que comprar peças separadas que fariam o mesmo trabalho pior.

O que me convenceu não foi um recurso específico, mas a forma como tudo funciona junto. As portas 2.5 GbE dão velocidade real às conexões cabeadas. O controlador integrado faz a configuração ser apenas configuração, em vez de uma costura de peças. Há uma porta SFP+ se eu um dia precisar. Ele é silencioso, rápido o suficiente para nunca atrapalhar e simples o bastante para eu realmente conseguir manter sem passar fins de semana resolvendo problema.

Ele encaixava no que eu queria justamente por não complicar as coisas. Eu precisava de segmentação, uma rede sem fio decente e hardware que funcionasse sem exigir atenção. O UDR7 faz tudo isso em uma caixa, por um preço razoável. Foi por isso que pareceu impossível: não porque prometia tudo, mas porque de fato entregava o que eu estava tentando montar.

## A configuração futura com o UDR7

O roteador do provedor entra em modo bridge e passa tudo para o UDR7, que cuida do roteamento e do DHCP enquanto mantém o tráfego separado onde precisa estar. Os dispositivos cabeados se conectam pelas portas 2.5 GbE para que as transferências locais continuem rápidas. O Wi-Fi começa como uma rede única, porque ainda não há motivo para complicar.

```
[Internet] → [ISP router (bridge mode)] → [UDR7]
                                   ├─ LAN1: Desktop (VLAN 10)
                                   ├─ LAN2: Proxmox (VLAN 20)
                                   ├─ LAN3: TV (VLAN 30)
                                   └─ Wi-Fi: single SSID (maps to chosen VLAN, e.g., 30)
```

As VLANs separam as coisas por confiança: meu desktop e os dispositivos confiáveis ficam na VLAN 10, o servidor fica na VLAN 20 com IPs estáticos e os dispositivos IoT vivem na VLAN 30, onde não conseguem falar com mais nada. O tráfego entre VLANs é bloqueado por padrão e só abre onde faz sentido. Desktop para servidor para SSH e acesso a arquivos. TV para Jellyfin para streaming. IoT apenas para a internet.

O AdGuard Home roda no Proxmox e cuida do DNS da rede inteira. Cada escopo DHCP aponta para ele, com o UDR7 como backup para que tudo continue funcionando se o servidor reiniciar. Para acesso externo, vou começar com Cloudflare Tunnel, já que manter as portas fechadas é mais fácil de gerenciar. Se eu precisar de mais controle depois, migro para Traefik e encaminho as portas 80 e 443.

O UDR7 tem portas suficientes por enquanto, então não vou adicionar um switch até realmente precisar de um. Quando isso acontecer, vou conectar um pequeno switch 2.5 GbE a uma das portas existentes e seguir em frente. O IDS vai rodar primeiro em modo de alerta, para eu enxergar como é o tráfego normal. Depois, vou habilitar bloqueio apenas para o que for de fato problema. A ideia toda é ter segmentação clara, regras razoáveis e hardware que simplesmente funcione sem precisar de atenção constante.
