---
content_hash: 3f92d777acd9145659ff99a93e0886326d873e3cd1b2252f83de878a65a21e79
created_at: '2025-11-05T02:24:49.357749'
date: 2025-11-05
excerpt: A good network shouldn't be noticed nor demand attention, that was the main
  guiding principle of my quest to find the best network setup for my Home Server
  build.
order: 1
slug: a-network-setup-that-works-for-me
tags:
- home server
- networking
- unifi
title: Building a network setup that works for Me
updated_at: '2026-02-08T01:10:31.293312'
---

A good network should not demand attention. That was the guiding principle behind my Home Server build. My goal was clear: a network that is fast, secure and stable without constant tuning. I did not want enterprise complexity or a rack of blinking lights consuming half my shelf space. The hardware should be affordable, reliable, compact and pleasant to look at. An impossible task, or so it seemed.

## What Were the Options

Three ecosystems emerged as candidates: Omada, pfSense and UniFi. Each promised control and stability in its own language. Omada looked polished on the surface with its clean interface and claims of seamless integration. The more I explored, though, the more I understood it was built for enterprise environments. It is stable, powerful and well designed, but it assumes structure: controllers, gateways and switches all managed through a centralized system that expects discipline and scale. You can configure VLANs and fine-tune access rules, but the experience feels like setting up a small office rather than a home. It works well, yet always seems to operate one layer above where you actually live.

pfSense stood at the opposite end of that spectrum. It offered everything Omada did not: transparency, depth and almost surgical control over every packet crossing your cables. But it demanded something in return that I was not willing to give: time. You do not just configure pfSense. You study it. You shape rules, manage subnets and slowly realize you have turned your home into a small datacenter. It is beautiful in its completeness but heavy in its consequence. I admired it, but I did not want to live with it.

That left UniFi, sitting quietly between the two like a bridge between practicality and depth. It spoke in the same technical terms as pfSense but translated them into something usable. The interface felt coherent, the devices felt related and the entire ecosystem carried the impression of having been designed by one mind. VLANs, routing and DHCP all connected in a way that did not feel abstract. It felt intentional. That is what caught me. I did not want something perfect. I wanted something that made sense. UniFi delivered.

## Why UniFi was the obvious answer

What convinced me about UniFi was not power or marketing. It was coherence. Everything about it feels like it was designed by someone who understands what living with a network actually means. The interface is clean but not shallow. The options are deep but never overwhelming. The setup feels like a process you participate in rather than a battle you fight. You plug the device in, open the controller and it starts making sense almost immediately. VLANs, DHCP, firewall rules and routing are all there, arranged in a way that feels both familiar and deliberate. It is one of those rare systems where things simply behave as they should, and that reliability changes how you relate to it. You stop checking if it works and start trusting that it does.

What really stands out is how complete the ecosystem is. You can build an entire network without leaving UniFi's world. Everything speaks the same language. Everything integrates under the same logic. That consistency removes the anxiety of guessing whether things will cooperate. It is a kind of harmony that most brands promise but never quite reach. The hardware is well built, the software feels mature and the updates come with purpose rather than disruption.

That completeness makes decision-making easier as well since you don’t have to piece things together from different manufacturers or worry about mismatched standards. You just pick the parts that fit your requirements and they click together. For someone like me, who wanted a reliable setup but doesn’t want to spend weekends buried in configuration menus, that matters more than raw performance. Better yet if that reliability and integration comes with a really good performance.


## The easiness of cost creep 

It always starts with something reasonable. For me, that was the UCG-Max: small, quiet and strong enough to handle VLANs, DHCP and IPS without issues. Four 2.5 GbE ports and capacity for a few hundred clients. A solid baseline.

Then you start thinking about what else is possible. The UCG-Fiber adds 10 Gb uplinks and a built-in four-port switch. Add NVMe storage for Protect and suddenly you are not building a router. You are building a network core.

Once you are thinking that way, the E7 becomes obvious. Wi-Fi 7, 10 GbE uplink and enough capacity to make wireless feel real instead of convenient. Which means everything upstream needs to match, and you need proper PoE.

Then you need the Switch Enterprise 8 PoE to tie it together. Eight 2.5 GbE PoE+ ports, two 10 Gb SFP+ uplinks and Layer 3 routing. It makes everything feel complete. It also makes the budget real.

Each piece makes sense alone: UCG-Max as a solid start, UCG-Fiber for headroom, E7 for wireless, Enterprise 8 PoE to connect it all. Together, they're way more than a home network needs. That's when you realize restraint matters too.

## Why UniFi was the IMPOSSIBLE answer 

I kept trying to piece together the perfect setup in my head: a gateway, an access point and a switch to connect them. Then I found the UniFi Dream Router 7 (UDR7) and realized I did not need to. It does everything those three boxes would do: handles VLANs and DHCP properly, has Wi-Fi 7 built in and includes a few multi-gig ports for wired devices. It fits on a shelf, does not look like network equipment and costs less than buying separate pieces that would do the same job worse.

What convinced me was not any single feature but how well it all works together. The 2.5 GbE ports give wired connections real speed. The built-in controller means setup is just configuration instead of stitching things together. There is an SFP+ port if I ever need it. It is quiet, fast enough that it never gets in the way and simple enough that I can actually maintain it without spending weekends troubleshooting.

It matched what I wanted by not overcomplicating things. I needed segmentation, decent wireless and hardware that works without demanding attention. The UDR7 does all of that in one box for a reasonable price. That is why it felt impossible: not because it promised everything, but because it actually delivered what I had been trying to build.

## The future setup with the UDR7

The ISP router goes into bridge mode and passes everything to the UDR7, which handles routing and DHCP while keeping traffic separated where it needs to be. Wired devices connect through the 2.5 GbE ports so local transfers stay fast. Wi-Fi starts as a single network because there is no reason to complicate it yet.

```
[Internet] → [ISP router (bridge mode)] → [UDR7]
                                   ├─ LAN1: Desktop (VLAN 10)
                                   ├─ LAN2: Proxmox (VLAN 20)
                                   ├─ LAN3: TV (VLAN 30)
                                   └─ Wi-Fi: single SSID (maps to chosen VLAN, e.g., 30)
```

VLANs separate things by trust: my desktop and trusted devices go in VLAN 10, the server sits in VLAN 20 with static IPs and IoT devices live in VLAN 30 where they cannot talk to anything else. Inter-VLAN traffic is blocked by default and opens only where it makes sense. Desktop to server for SSH and file access. TV to Jellyfin for streaming. IoT to internet only.

AdGuard Home runs on Proxmox and handles DNS for the whole network. Every DHCP scope points to it, with the UDR7 as backup so things keep working if the server reboots. For external access, I'm starting with Cloudflare Tunnel since keeping ports closed is easier to manage. If I need more control later, I'll switch to Traefik and forward ports 80 and 443.

The UDR7 has enough ports for now, so I am not adding a switch until I actually need one. When that happens, I will connect a small 2.5 GbE switch to one of the existing ports and keep going. IDS will run in alert mode first so I can see what normal traffic looks like. Then I will enable blocking only for things that are actually problems. The whole point is to have clear segmentation, reasonable rules and hardware that just works without needing constant attention.