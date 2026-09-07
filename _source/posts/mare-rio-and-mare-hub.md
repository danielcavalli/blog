---
title: "Maré Rio: The Software I Want to Exist"
slug: mare-rio-and-mare-hub
date: 2026-09-06
lang: en-us
readingTime: 6
excerpt: "My agents can build apps around my own needs. I'm building Maré Rio so those apps can share their engineering and, increasingly, do useful work together."
tags:
- Maré
- Personal Software
- Software Architecture
---

Choosing an app usually means choosing which of somebody else's decisions I can live with. A notes app may organize information perfectly sensibly and still require me to fit my thinking into categories I would never have chosen.

With my coding agents doing the implementation, I can have an app built around the way I want to work. It can justify the effort by being useful to me, even if nobody else would want to use it.

Once the apps are mine to change, I can also reconsider the work I do between them. If a task needs information from one app and an action in another, I can have the two built to cooperate, giving an agent the means to carry the task through.

Maré Rio is the personal, self-hosted environment I'm building for that purpose. It gives my coding agents a shared platform for the apps they create, so the engineering done for one can support the next.

I use those apps through Maré Hub, the browser interface that brings them together with their shared settings.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/hub-day.jpg"><img src="/static/images/mare-rio/hub-day.jpg" alt="Maré Hub in Day mode, listing Notes, Finance, Moon, and Library with their readiness states." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/hub-night.jpg"><img src="/static/images/mare-rio/hub-night.jpg" alt="Maré Hub in Night mode, listing Notes, Finance, Moon, and Library with their readiness states." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <figcaption>Maré Hub's home. All screenshots in this post come from the actual local frontends, with sample data.</figcaption>
</figure>

## Make the next idea easier to build

Software I can rely on needs to retain its data, run work after I've closed the browser, survive changes, and remain understandable when another coding session returns to it. An agent can write the machinery for all of that, but asking it to make those decisions afresh for every app spends both tokens and engineering effort on variations I will then have to maintain.

Maré gives those decisions a durable form. The platform supplies identity, storage, background execution, and an agent runtime through contracts the coding agent can discover and validate against. The shared design system does the same for the interface. My agent can find out what is available and how to use it while it works on the feature, without depending on me to reconstruct the platform in every conversation.

The value of that work reaches beyond the application that first needed it. Once Maré can run a certain kind of job or give an agent a tool, a later app can use the same machinery for a purpose I hadn't considered when it was built. New requirements will call for new engineering, and that work can enter the shared foundation too. This is why I'm willing to build a substantial platform for personal software: I want each investment to expand the range of things I can ask for next.

## Let the applications work together

An app can also contribute something the rest of the environment can use. A search function, for example, is useful in its own interface; exposed through a contract, it can become a tool another app or an agent calls as part of a larger task. Information I have already recorded can do useful work beyond the screen where I entered it.

This was present in Maré's early design too. Apps needed a way to describe what they offered, and agents needed a way to discover what they could use. Treating those as one engineering problem gives integration a common basis. An app declares an operation with defined inputs, outputs, and effects; consumers can work through that interface while the app retains responsibility for its records and behavior.

Notes, for example, gives me somewhere to capture a thought while it is still rough. I want an agent working elsewhere in Maré to be able to recover the relevant material through a defined interface, while Notes remains the place where I keep and revise it.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/notes-day.jpg"><img src="/static/images/mare-rio/notes-day.jpg" alt="Notes in Day mode, with navigation, a list of sample notes, and an open note in the editor." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/notes-night.jpg"><img src="/static/images/mare-rio/notes-night.jpg" alt="Notes in Night mode, with navigation, a list of sample notes, and an open note in the editor." width="1440" height="1060" loading="lazy" decoding="async"></a>
  <figcaption>Notes keeps navigation and the current thought on the same working surface. The notes shown are examples.</figcaption>
</figure>

Moon, my film and television app, shows the other direction: an application putting an agent to work. Its viewing history and ratings give the agent context for recommendations, and the answer returns to a feature where I can use it. The platform runs the agent; Moon decides what to ask and how to handle the result. I've followed that mechanism in [An Agent in a JSON File](_source/posts/adding-an-agent-to-a-mare-app.md).

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/moon-day.jpg"><img src="/static/images/mare-rio/moon-day.jpg" alt="Moon in Day mode, showing a sample film and television watchlist alongside recommendations and catalog titles." width="1440" height="1494" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/moon-night.jpg"><img src="/static/images/mare-rio/moon-night.jpg" alt="Moon in Night mode, showing a sample film and television watchlist alongside recommendations and catalog titles." width="1440" height="1494" loading="lazy" decoding="async"></a>
  <figcaption>Moon's watchlist and recommendation surfaces, populated with sample catalog entries rather than my viewing history or a live agent's suggestions.</figcaption>
</figure>

What I want to develop from this is software that can carry a task across the applications involved in it. A task may require information from several places, an agent's judgment, and a change recorded somewhere else. Because I can change the applications themselves, I can design their cooperation around the result I'm after.

Predictable software gives an agent dependable tools to work with. Finance calculates from its records; Notes saves what I write. An agent can use such operations while handling the parts of a task that need interpretation, with the application defining which work belongs to each. I want the freedom to delegate larger tasks to rest on ordinary operations I can continue to understand and use myself.

## An environment I can keep shaping

Maré Hub gives this growing system a place in daily use. I can enter through one account, open an installed app, or add another from the environment's catalog. The apps keep interfaces suited to their work, with common controls and a shared visual language. A notes editor and a watchlist can feel like parts of the same place without making me use them in the same way.

I want to keep adding what the software can do without making the experience increasingly cumbersome. The engineering behind a feature can become quite involved while the act of using it remains simple. The Hub's Day and Night themes, its navigation, and the quieter working surfaces are part of making this somewhere I want to spend time, as well as somewhere my agents can ship code.

<figure class="post-figure theme-media">
  <a data-theme-variant="light" href="/static/images/mare-rio/settings-day.jpg"><img src="/static/images/mare-rio/settings-day.jpg" alt="Hub settings in Day mode, showing a sample account, appearance controls, agent provider connections, and installation entitlements." width="1440" height="1311" loading="lazy" decoding="async"></a>
  <a data-theme-variant="dark" href="/static/images/mare-rio/settings-night.jpg"><img src="/static/images/mare-rio/settings-night.jpg" alt="Hub settings in Night mode, showing a sample account, appearance controls, agent provider connections, and installation entitlements." width="1440" height="1311" loading="lazy" decoding="async"></a>
  <figcaption>Settings gathers account information, appearance, and agent connections. The identity and connection states shown are sample data.</figcaption>
</figure>

The provider connections in settings are shared in the same way. Once I have connected an account for the platform's agent runtime, another app can use that service without having to invent its own way to authenticate and execute an agent.

I also get to change my mind. A feature that looked sensible in a plan may turn out to be awkward in use, or suggest something better once I have it in front of me. Those observations can become another conversation with my coding agents and another change to the software. I still have to decide what is worth doing and what a good result looks like, as I argued in [Don't Outsource the Thinking](_source/posts/dont-outsource-the-thinking.md), but I have a way to act on that judgment.

The prospect that interests me is being able to recognize a better way to do something and have the means to put it into practice. Sometimes that will require a new app; sometimes it will mean connecting what already exists, or having an agent carry out work I currently do myself. I want those possibilities to keep widening as Maré grows. I have no intention of running out of things to ask of it.
