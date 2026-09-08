---
title: "Maré Rio: The Software I Want to Exist"
slug: mare-rio-and-mare-hub
date: 2026-09-06
lang: en-us
readingTime: 6
excerpt: "I got tired of every app I wanted arriving with its own plumbing, so I built the plumbing once. Maré Rio is that platform, three apps prove it holds, and the list of what I want to build on it is where this gets ambitious."
tags:
- Maré
- Personal Software
- Software Architecture
---

Choosing an app usually means choosing which of somebody else's decisions I can live with. For most of my life that was fine, because the alternative was writing the thing myself and, [as I've admitted before](_source/posts/dont-outsource-the-thinking.md), I was never much of a programmer, so I'd focus on things that no one could offer me in a box. Then the agents got good enough that I stopped being the bottleneck, and the alternative got cheap. I wanted a notes app that works the way I think, a finance app that reads my accounts the way I read them, a watchlist that knows why I liked a film, and for the first time all three were a conversation away.

The thing is, the problem showed up right after the excitement... Each app comes with its own login, its own database, its own job runner, its own way of calling a model, and even its own Design! And every one of those is a decision I have already made once and have no interest in making again, let alone maintaining in a handful of slightly different flavors. I don't mind paying agents to build things for me, but I do mind having to re-explain to them choices that were already made (and even then seeing them drift apart).

So I decided what I wanted to do next: build the plumbing once.

Maré Rio is a platform I host on Kubernetes, and every app I ask for runs on it. All the Engineering and Design decisions are the platform's job, so that an app declares what it needs as Kubernetes custom resources and gets on with being an app. The coding agent building it never asks me how any of this works, because the platform's contracts are readable from a CLI, and I use whatever comes out through Maré Hub: one login, one catalog, all my apps.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/hub-day.jpg"><img src="/static/images/mare-rio/hub-day.jpg" alt="Maré Hub in Day mode, listing Notes, Finance, Moon, and Library with their readiness states." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/hub-night.jpg"><img src="/static/images/mare-rio/hub-night.jpg" alt="Maré Hub in Night mode, listing Notes, Finance, Moon, and Library with their readiness states." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <figcaption>Maré Hub's home. All screenshots in this post come from the actual local frontends, with sample data.</figcaption>
</figure>

## Three apps as probes

The keen-eyed might have noticed some fairly simple-looking apps in the screenshot above, but rest assured: Notes, Finance, and Moon are not the point of Maré. Their existence is how I find out whether the platform can carry the next thing I want, and each one was chosen to push a little harder than the one before.

Notes came first because it was the easiest target I could think of: an editor, a list, storage and identity from the platform, done. It proved the loop works. I describe an app, my agent builds it against the contracts, and it runs on the same cluster as everything else. Nothing about that is impressive, which is exactly what I wanted from a first app.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/notes-day.jpg"><img src="/static/images/mare-rio/notes-day.jpg" alt="Notes in Day mode, with navigation, a list of sample notes, and an open note in the editor." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/notes-night.jpg"><img src="/static/images/mare-rio/notes-night.jpg" alt="Notes in Night mode, with navigation, a list of sample notes, and an open note in the editor." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <figcaption>Notes, the first app built on the platform. The notes shown are examples.</figcaption>
</figure>

Finance's first phase was the step up, with more entities, real calculation, and background work to schedule, and it was still easy. That was the result that mattered, because a platform is only worth building if the second app costs less than the first, and it did.

Moon, the watchlist[^moon], was a bit different though... It was a case of: I want this, how long will it take? The answer that came from it was great as well, at least for a foundation: it showed me the platform wasn't ready for it, yet. So then I began the work to get the backend to where Moon could exist and, while it may have taken longer than I'd like, Moon works now! That meant it was the perfect application to show capabilities I've built onto the core of Maré Rio, such as apps being able to expose endpoints to other apps, agents that are just a [JSON away](_source/posts/adding-an-agent-to-a-mare-app.md) from existing and things like that. 

I've been avoiding sharing much about Maré Rio publicly because I believe it still has a long way to go before it becomes stable, but Moon showed me that there are stable bits around the unstable ones, so you'll likely see more posts about the engineering behind Maré and Moon soon.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/moon-day.jpg"><img src="/static/images/mare-rio/moon-day.jpg" alt="Moon in Day mode, showing a sample film and television watchlist alongside recommendations and catalog titles." width="1440" height="1494" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/moon-night.jpg"><img src="/static/images/mare-rio/moon-night.jpg" alt="Moon in Night mode, showing a sample film and television watchlist alongside recommendations and catalog titles." width="1440" height="1494" loading="lazy" decoding="async"></a>
  <figcaption>Moon's watchlist and recommendations, populated with sample catalog entries rather than my viewing history or a live agent's suggestions.</figcaption>
</figure>

## What every app gets

At the risk of repeating myself, what Maré means is that a new house connects to the grid instead of building a power plant in the backyard:

- **Identity and tenancy.** One account, and behind it the household whose data an app is touching. An agent run belongs to the household, not to the app that requested it, which is the difference between a platform and a pile of apps sharing a password.
- **Storage and background execution** on the cluster, declared by the app rather than provisioned by hand.
- **An agent runtime.** An app says what it wants from a model in a JSON file: purpose, tools, output schema, token budget. The platform picks a model from the providers I connected once in the Hub, runs the job, checks the answer against the schema, and writes down what happened. No app on Maré will ever have to choose an agent framework again.
- **A design system.** New apps don't get to invent their own look. Day and Night themes, navigation, and controls come from the platform, which is why Notes and Moon feel like rooms in the same house without pretending to be the same room.
- **Contracts the coding agent can read.** The CLI describes every command as JSON, with its inputs, its effects, and whether it needs a human in the loop, so the agent learns how Maré works while it is building the app and validates against the same compiler that deploys it. I don't explain the platform anymore. It explains itself.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/settings-day.jpg"><img src="/static/images/mare-rio/settings-day.jpg" alt="Hub settings in Day mode, showing a sample account, appearance controls, agent provider connections, and installation entitlements." width="1440" height="1311" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/settings-night.jpg"><img src="/static/images/mare-rio/settings-night.jpg" alt="Hub settings in Night mode, showing a sample account, appearance controls, agent provider connections, and installation entitlements." width="1440" height="1311" loading="lazy" decoding="async"></a>
  <figcaption>Hub settings: account, appearance, and the provider connections every app's agents share. The identity and connection states shown are sample data.</figcaption>
</figure>

The contract runs the other way too. An app declares the operations it offers, with inputs, outputs, and effects, and an agent in another app can name one of them as a tool. Pointing Moon's agent at Notes search is an entry in a tool list, not an integration project, and Notes stays in charge of the notes.

This has the added benefit of each application not needing to rely on, or even understand, an MCP contract from another vendor. For example, once the Finance app is connected to Pluggy, if I want to expose Pluggy's Open Finance data[^pluggy] to other applications besides itself, those applications can just take advantage of Finance's Open Finance tool to gather that data, never holding any credentials or access to the Pluggy endpoint themselves.

That is what an app gets for plugging into the grid, and none of the three above had to think about any of it. It is also as far as this post goes on what Maré is. How Maré is, the architecture behind all of this, deserves a post of its own once it is more mature, but the agent post linked above already gives away a few spoilers.

## Where this is going

This is where I stop describing what exists and start describing what I actually want, because the three apps above are proofs of the platform and none of them is why I built it.

- **A memory system for the models I work with that is actually good.** I don't think anything on the market gets this right. I want a shared record that humans and machines both read and write, so that what I know and what my agents know stop drifting apart.
- **A supermarket scout** that takes my grocery list, works out which market is the best deal for the whole list, and gets it delivered to my door.
- **Finance on Open Finance,** so the app reads my accounts directly and automates the routine I still do by hand. If that holds up, next year I want it doing my taxes.
- **An assistant that lives on my hardware** and talks to every app on Maré. Alexa and Google's assistant ship what they hear to the highest bidder, which, I'm sure, is a reasonable trade for setting a timer or turning the lights on.
- **My devices on an operating system I control,** custom firmware included, so that assistant reaches everything without asking a vendor's permission.
- **Learning tools** that put the frankly incredible models we have now to work teaching me something every day.

None of this is small, and every item on the list will need something Maré doesn't have yet, the same way Moon did. That is fine. The whole reason the platform exists is so that when the next app needs something new, the work goes into Maré once, every app after it gets it for free, and nothing stops the one after that from extending it further.

[^moon]: To simplify a lot, Moon is a place where I can mark movies and TV shows as watched and receive recommendations as to what to watch next. Plus some playback features...

[^pluggy]: Open Finance is Brazil's open banking standard, and Pluggy is an aggregator that gives apps access to it.
