---
content_hash: 62e90a5c95b981a99c2c6e8ed30dc011
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
updated_at: '2025-11-05T02:28:38.749469'
---

A good network shouldn't be noticed nor demand attention, that was the main guiding principle of my quest to find the best network setup for my Home Server build. Not being an expert in networking myself, my goal was clear: create a network that is fast, secure and stable without having to keep tuning it from time to time. I also did not want enterprise complexity or a rack of blinking lights that would take up half of my shelf space, so this piece of hardware should be cheap, reliable, small and good in the eyes. Basically an impossible task.

## What Were the Options

When I started looking for what could actually build the kind of network I wanted, I found myself walking through three very different worlds: Omada, pfSense, and UniFi. Each one promised control and stability, but in its own language, and it didn’t take long to realize that those languages barely spoke to each other. Omada looked polished on the surface, with its clean interface and claims of seamless integration, yet the more I explored, the more I understood that it was built for enterprise environments. It’s stable, powerful, and well designed, but it assumes structure: controllers, gateways, switches, all managed through a centralized system that expects discipline and scale. You can configure VLANs and fine-tune access rules, but the whole experience feels like you’re setting up a small office, not a home. It works well, but it always seems to operate one layer above where you actually live.

pfSense stood at the opposite end of that spectrum, a kind of temple to precision. It offered everything Omada didn’t: transparency, depth, and almost surgical control over every packet that crossed your cables. But it also demanded something in return, something I wasn’t willing to give: time. You don’t just configure pfSense, you study it. You shape rules, manage subnets, and slowly realize you’ve turned your home into a small datacenter. It’s beautiful in its completeness, but heavy in its consequence. I admired it, but I didn’t want to live with it.

That left UniFi, sitting quietly in between the two, like a bridge between practicality and depth. It spoke in the same technical terms as pfSense but translated them into something usable. The interface felt coherent, the devices felt related, and the entire ecosystem carried the impression of having been designed by one mind. VLANs, routing, DHCP, everything connected in a way that didn’t feel abstract, it felt intentional. That’s what caught me. I didn’t want something perfect, I wanted something that made sense. UniFi actually did.

## Why UniFi was the obvious answer

What convinced me about UniFi wasn’t power or marketing, it was coherence. Everything about it feels like it was designed by someone who understands what living with a network actually means. The interface is clean but not shallow, the options are deep but never overwhelming, and the setup feels like a process you participate in rather than a battle you fight. You plug the device in, open the controller, and it starts making sense almost immediately. VLANs, DHCP, firewall rules, and routing are all there, arranged in a way that feels both familiar and deliberate. It’s one of those rare systems where things simply behave as they should, and that reliability changes how you relate to it. You stop checking if it’s working and start trusting that it is.

What really stands out, though, is how complete the ecosystem is. You can build an entire network without leaving UniFi’s world. Everything speaks the same language, everything integrates under the same logic, and that consistency removes the anxiety of guessing whether things will cooperate. It’s a kind of harmony that most brands promise but never quite reach. The hardware is well built, the software feels mature, and the updates come with purpose rather than disruption.

That completeness makes decision-making easier as well since you don’t have to piece things together from different manufacturers or worry about mismatched standards. You just pick the parts that fit your requirements and they click together. For someone like me, who wanted a reliable setup but doesn’t want to spend weekends buried in configuration menus, that matters more than raw performance. Better yet if that reliability and integration comes with a really good performance.


## The easiness of cost creep 

It always starts with something reasonable. For me, that was the UCG-Max: small, quiet, and strong enough to handle VLANs, DHCP, and IPS without issues. Four 2.5 GbE ports and capacity for a few hundred clients. A solid baseline.

Then you start thinking about what else is possible. The UCG-Fiber adds 10 Gb uplinks and a built-in four-port switch. Add NVMe storage for Protect, and suddenly you're not building a router, you're building a network core.

Once you're thinking that way, the E7 becomes obvious. Wi-Fi 7, 10 GbE uplink, enough capacity to make wireless feel real instead of convenient. Which means everything upstream needs to match, and you need proper PoE.

Then you need the Switch Enterprise 8 PoE to tie it together. Eight 2.5 GbE PoE+ ports, two 10 Gb SFP+ uplinks, Layer 3 routing. It makes everything feel complete. It also makes the budget real.

Each piece makes sense alone: UCG-Max as a solid start, UCG-Fiber for headroom, E7 for wireless, Enterprise 8 PoE to connect it all. Together, they're way more than a home network needs. That's when you realize restraint matters too.

## Why UniFi was the IMPOSSIBLE answer 

I kept trying to piece together the perfect setup in my head: a gateway, an access point, a switch to connect them. Then I found the UniFi Dream Router 7 (UDR7) and realized I didn't need to. It does everything those three boxes would do: handles VLANs and DHCP properly, has Wi-Fi 7 built in, and includes a few multi-gig ports for wired devices. It fits on a shelf, doesn't look like network equipment, and costs less than buying separate pieces that would do the same job worse.

What convinced me wasn't any single feature but how well it all works together. The 2.5 GbE ports give wired connections real speed, the built-in controller means setup is just configuration instead of stitching things together, and there's an SFP+ port if I ever need it. It's quiet, fast enough that it never gets in the way, and simple enough that I can actually maintain it without spending weekends troubleshooting.

It matched what I wanted by not overcomplicating things. I needed segmentation, decent wireless, and hardware that works without demanding attention. The UDR7 does all of that in one box for a reasonable price. That's why it felt impossible, not because it promised everything, but because it actually delivered what I'd been trying to build.

## The future setup with the UDR7

The ISP router goes into bridge mode and passes everything to the UDR7, which handles routing, DHCP, and keeps traffic separated where it needs to be. Wired devices connect through the 2.5 GbE ports so local transfers stay fast. Wi-Fi starts as a single network because there's no reason to complicate it yet.

```
[Internet] → [ISP router (bridge mode)] → [UDR7]
                                   ├─ LAN1: Desktop (VLAN 10)
                                   ├─ LAN2: Proxmox (VLAN 20)
                                   ├─ LAN3: TV (VLAN 30)
                                   └─ Wi-Fi: single SSID (maps to chosen VLAN, e.g., 30)
```

VLANs separate things by trust: my desktop and trusted devices go in VLAN 10, the server sits in VLAN 20 with static IPs, and IoT stuff lives in VLAN 30 where it can't talk to anything else. Inter-VLAN traffic is blocked by default and opens only where it makes sense, desktop to server for SSH and file access, TV to Jellyfin for streaming, IoT to internet only.

AdGuard Home runs on Proxmox and handles DNS for the whole network. Every DHCP scope points to it, with the UDR7 as backup so things keep working if the server reboots. For external access, I'm starting with Cloudflare Tunnel since keeping ports closed is easier to manage. If I need more control later, I'll switch to Traefik and forward ports 80 and 443.

The UDR7 has enough ports for now, so I'm not adding a switch until I actually need one. When that happens, I'll connect a small 2.5 GbE switch to one of the existing ports and keep going. IDS will run in alert mode first so I can see what normal traffic looks like, then I'll enable blocking only for things that are actually problems. The whole point is to have clear segmentation, reasonable rules, and hardware that just works without needing constant attention. T