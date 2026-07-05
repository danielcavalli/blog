---
title: What I Actually Do All Day
slug: what-i-do-ml-engineering
date: 2026-07-05
excerpt: Machine Learning Engineering, explained to my friends.
tags:
- Machine Learning
- Engineering
- Career
lang: en-us
content_type: presentation
---

<!-- presentation:slide id="title" layout="lead" density="normal" -->

# What I Actually Do All Day

## Machine Learning Engineering, explained to my friends

Daniel Cavalli | dan.rio

<!-- /presentation:slide -->

<!-- presentation:slide id="bio-and-agenda" layout="bio" density="dense" -->

# Daniel Cavalli

Senior Machine Learning Engineer

Nine years building machine learning systems. Studied economics, went to a game-development school, and somehow ended up here. Writes at dan.rio.

![Daniel Cavalli](/static/images/presentations/what-i-do-ml-engineering/profile-picture.png)

| # | Section | What you'll actually get |
| - | ------- | ------------------------ |
| 1 | The Job Nobody Can Name | "So, what is it you do again?" |
| 2 | What a Model Actually Is | The thing, minus the mystery |
| 3 | The Platform | What I'm doing while you text me |
| 4 | Making Training Fast | Why I'm obsessed with waiting less |
| 5 | Why Models Rot | Why the job never actually ends |
| 6 | How I Got Here | How an economics kid wound up here |

<!-- /presentation:slide -->

<!-- presentation:slide id="job-nobody-can-name" layout="divider" density="normal" -->

# The Job Nobody Can Name

## Everyone says "AI" now. Almost no one can tell you who builds the plumbing underneath it.

<!-- /presentation:slide -->

<!-- presentation:slide id="when-you-ask" layout="content" density="dense" -->

# When you ask what I do

I say "Machine Learning Engineer." You hear "AI." You picture a robot, or ChatGPT, or me in a dark room quietly training Skynet. Then you nod politely and we talk about something else.

That is completely fair, because for years the only people explaining this stuff were trying to sell you something, so the words got strange before they got useful. Here is the version I would actually tell you over a beer.

> You know the AI everyone talks about? I build the boring, invisible machinery that keeps it from falling over the second a real person uses it.

The clever model is the famous part. The machinery is the part that decides whether that model ever leaves someone's laptop.

<!-- /presentation:slide -->

<!-- presentation:slide id="two-jobs" layout="split" density="dense" -->

# Two jobs everyone confuses

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### The Data Scientist
Their question: *what should this thing learn, and is it any good?* They invent the recipe. What they hand over is something that worked once, on their laptop, on a good day.
<!-- /presentation:column -->
<!-- presentation:column -->
### The ML Engineer (me)
My question: *okay, but how does this run millions of times a day without breaking, and who gets the 3am phone call when it does?* I keep the recipe working forever, for everyone, with nobody watching over it.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### The restaurant, basically
The data scientist is the chef who dreams up a dish. I build the kitchen that cooks that same dish ten thousand times a night, tasting the same every time, without setting the place on fire. Inventing a recipe and running a kitchen are just different jobs. People mix them up because both involve food.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="notebook-vs-production" layout="emphasis" density="normal" -->

# The line that explains everything

> A model on someone's laptop is a cool science-fair project. The same model out in the real world is a promise you have to keep every single second of every day.

The whole trade lives in the gap between those two sentences. Getting something to work once is the easy, fun part almost anyone can do. Keeping it working, for real people, while the world keeps changing underneath it, is the hard part. And it turns out that hard part is mostly plumbing, not maths.

That gap is where I spend my days.

<!-- /presentation:slide -->

<!-- presentation:slide id="what-a-model-is" layout="divider" density="normal" -->

# What a Model Actually Is

## Before the job makes sense, the thing itself has to make sense

<!-- /presentation:slide -->

<!-- presentation:slide id="model-learns-rules" layout="content" density="dense" -->

# A model teaches itself the rules

Normal software is just a list of rules a person wrote down by hand: *if the customer earns more than this and is younger than that, say no to the loan.* Every rule was typed by a human, and when it gets something wrong, you can point at the human who typed it.

A model flips that around. Nobody writes the rules. You show it millions of past examples, the good and the bad, and it works out its own rules from the patterns. Think of how you can spot a friend's face in a crowd without being able to explain exactly how. It ends up making calls that no person ever spelled out, which is the whole reason it is so powerful and also faintly unsettling.

> You are not writing down the answer. You are building the thing that comes up with the answer. And then you have to trust something whose reasoning you cannot fully read back.

<!-- /presentation:slide -->

<!-- presentation:slide id="two-phases" layout="card_grid" density="dense" -->

# Two phases, two completely different problems

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Training (the studying)
The model sits down with mountains of past examples and slowly learns. This is the expensive, slow part: rooms full of special chips running for days, quietly burning through an electricity bill that would make you wince. You do it rarely.
<!-- /presentation:card -->
<!-- presentation:card -->
### Using it (the exam)
Once it has studied, you ask it one real question and it answers on the spot. This has to be instant and cheap, because it might happen tens of thousands of times a minute, and each answer has to land before anyone notices they waited.
<!-- /presentation:card -->
<!-- presentation:card -->
### Where I come in
Both parts are really plumbing problems wearing a lab coat. Someone has to make the studying fast enough to bother with and the answering reliable enough to trust. That someone is me.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="lifecycle" layout="card_grid" density="very_dense" -->

# The lifecycle, and where each of us lives

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Data
Collect it, clean it, make it trustworthy. Boring, unglamorous, and the single biggest reason models fail.
<!-- /presentation:card -->
<!-- presentation:card -->
### Train
Where the data scientist mostly lives. Turn data into a model that works.
<!-- /presentation:card -->
<!-- presentation:card -->
### Ship it
Get it off the laptop and into the actual app that real people use.
<!-- /presentation:card -->
<!-- presentation:card -->
### Monitor
Watch it in the wild. Catch it the moment it starts to quietly get worse.
<!-- /presentation:card -->
<!-- presentation:card -->
### Retrain
The world moved, so the model has to. Then the whole loop runs again.
<!-- /presentation:card -->
<!-- /presentation:block -->

The data scientist mostly owns one of those boxes. I own the arrows between all of them, and the fact that this whole circle keeps spinning on its own while everyone sleeps.

<!-- /presentation:slide -->

<!-- presentation:slide id="the-platform" layout="divider" density="normal" -->

# The Platform

## My users are not customers. They are the people who build the models.

<!-- /presentation:slide -->

<!-- presentation:slide id="tools-for-builders" layout="split" density="dense" -->

# I make the tools for the people who make the AI

Most apps are built for regular people like you. I build tools for the people who build the AI, the folks whose entire job is dreaming up new models. I am the ground they stand on, which mostly means they only notice me when the ground shakes.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Who I'm building for
A whole company's worth of these model-builders, with piles of models running live at any given moment. Every one of them wants to build and ship without first having to become a plumbing expert. My job is to spare them that.
<!-- /presentation:column -->
<!-- presentation:column -->
### What I'm actually building
A shared foundation, so nobody has to reinvent the boring machinery from scratch every single time. They bring the clever idea. The platform quietly handles everything underneath it.
<!-- /presentation:column -->
<!-- /presentation:block -->

> Do it well and nobody ever thinks about me. Do it badly and nothing works. My whole job is to be invisible, which is a genuinely weird thing to build a career around.

<!-- /presentation:slide -->

<!-- presentation:slide id="what-platform-means" layout="card_grid" density="very_dense" -->

# What "platform" actually means

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### A place to train
All the heavy computers and chips, wired up so someone can say "run my experiment" and just get an answer back, without ever wrestling with a server themselves.
<!-- /presentation:card -->
<!-- presentation:card -->
### A safe way to ship
A paved road from "works on my laptop" to "live for everyone," with guardrails so a broken version can't quietly sneak out to real people.
<!-- /presentation:card -->
<!-- presentation:card -->
### A way to keep watch
Keeping the live models quick and healthy, and tapping me on the shoulder the moment one starts drifting away from reality.
<!-- /presentation:card -->
<!-- presentation:card -->
### Room to grow
Building it so the same setup works in a new place without tearing it all down and starting over. Growing should be a small tweak, not a full rebuild.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="making-training-fast" layout="divider" density="normal" -->

# Making Training Fast

## The unglamorous number that quietly decides everything: how long you have to wait.

<!-- /presentation:slide -->

<!-- presentation:slide id="one-computer" layout="split" density="dense" -->

# One computer is never enough

Teaching a big model on a single machine can take weeks. A lot of my job is turning "weeks" into "a few days," so that training a model stops being a rare event you plan your month around and becomes a normal Tuesday.

You would think you just add more computers and it goes faster. That is exactly where most people's guess stops, and it is a perfectly sensible guess. It is also where the real problem starts, because computers, like people, are terrible at working together without a lot of help.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### The group-project problem
Picture a group project where everyone has to end up on the same page, constantly. You split the work up, but now they all have to stop and compare notes over and over. Coordinate it badly and eight people somehow finish slower than one. Computers are exactly like this.
<!-- /presentation:column -->
<!-- presentation:column -->
### Where my actual work is
So the job is almost never "buy more machines." It is getting them to talk to each other without tripping over their own feet: who does which piece, when they check in, and how to keep everyone busy instead of standing around waiting.
<!-- /presentation:column -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="wait-time" layout="emphasis" density="dense" -->

# The number that matters more than raw speed

> The real prize is shrinking the wait between "I have an idea" and "I can see whether it worked" from a coffee break down to a breath.

That sounds like a convenience. It is actually a change in how people think. When feedback takes many minutes, you get careful and cautious, you batch up your guesses, you stop experimenting because each try costs real time. When it takes seconds, you just try things.

Quick feedback does not just make people work faster. It makes them braver. That is the real thing I am selling, and almost nobody outside this world would guess that a whole platform gets built around something as human as how long people are willing to wait.

<!-- /presentation:slide -->

<!-- presentation:slide id="why-models-rot" layout="divider" density="normal" -->

# Why Models Rot

## The part nobody warns you about: the model that was right last month is quietly wrong today.

<!-- /presentation:slide -->

<!-- presentation:slide id="world-moves" layout="content" density="dense" -->

# The world moves. The model doesn't.

A model learns from the past. That is the whole trick and also the whole problem, because the past is the only thing it will ever know, and the world refuses to hold still.

Fraud patterns change the week after you catch them. Prices move. People change how they behave. The model does not notice any of this. It keeps confidently applying yesterday's rules to today's world, and every dashboard says it is running perfectly while its answers slowly drift from useful to wrong.

> This is called drift, and it is the quiet villain of the whole field. Nothing crashes. No alarm goes off. The model just gets worse in complete silence until someone thinks to check.

So the job is never "ship it and move on." It is watch it, catch the drift, retrain, redeploy, and do it again, forever.

<!-- /presentation:slide -->

<!-- presentation:slide id="mlops" layout="card_grid" density="very_dense" -->

# Doing all of that, for a lot of models at once

Now imagine everything on the last slide, but for hundreds of models at the same time, and without an army of people hand-holding each one. My corner of the field has an unlovely name for this, "MLOps," but really it just means making the boring, repetitive parts automatic and trustworthy.

<!-- presentation:block type="card_grid" -->
<!-- presentation:card -->
### Assembly lines
Instead of a person clicking through every update by hand, the boring steps run themselves on a schedule. A human decides what should happen; the machine handles the tedious business of making it happen.
<!-- /presentation:card -->
<!-- presentation:card -->
### A written-down recipe
The whole setup is written down step by step, like flat-pack furniture instructions, so anyone can rebuild it or spot a mistake. The alternative is it living only in one person's head and a folder of fragile scripts that break if you look at them wrong.
<!-- /presentation:card -->
<!-- presentation:card -->
### Rebuilding mid-flight
A lot of my recent work is replacing the foundations while hundreds of people keep using the thing every day. It is a bit like changing a plane's engine without landing the plane.
<!-- /presentation:card -->
<!-- /presentation:block -->

<!-- /presentation:slide -->

<!-- presentation:slide id="how-i-got-here" layout="divider" density="normal" -->

# How I Got Here

## I have an economics degree and went to a game-development school. This was not a plan.

<!-- /presentation:slide -->

<!-- presentation:slide id="path-made-no-sense" layout="split" density="dense" -->

# The path made no sense until it did

I studied economics at university. Before that, a technical high school for making video games. Neither is the obvious runway for a career in machine learning infrastructure, which is rather the point.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Where it started
My first real job was reading open-ended survey text with an early language model, back when explaining "AI" at a dinner table got you a blank stare rather than an opinion. Then anti-fraud, which is where I learned that a model is only as good as the system holding it up.
<!-- /presentation:column -->
<!-- presentation:column -->
### What actually shipped
That anti-fraud work stopped a meaningful amount of fraud at a tiny cost per check. What stuck with me was the lesson, not the number: the model mattered, and the machinery around it mattered more.
<!-- /presentation:column -->
<!-- /presentation:block -->

The through-line is not a degree. It is a specific taste for the unglamorous half of the problem, the half that decides whether any of the clever part ever reaches a real person.

<!-- /presentation:slide -->

<!-- presentation:slide id="trade-not-talent" layout="emphasis" density="normal" -->

# What I want my friends to take away

> This is a trade, not a talent. It is closer to being a very stubborn plumber than a lone genius. The romance is optional. The reliability is not.

The field wraps itself in mystique because mystique sells, and for a while I half-believed it too. But strip that away and it is craft: build the thing, make it fast, keep it honest, and be there when it breaks. Learnable, unglamorous, and quietly satisfying in the way any real trade is.

You do not need a PhD or anyone's permission to start. I certainly didn't have either.

<!-- /presentation:slide -->

<!-- presentation:slide id="home-lab" layout="split" density="dense" -->

# The home lab, and why it's there

There are two graphics cards humming in my apartment right now, doing nothing anyone is paying for. I built that little machine on purpose.

<!-- presentation:block type="split" -->
<!-- presentation:column -->
### Not to be fast
It will never win any speed contest, and that was never the point. It is there so I can watch two chips try to learn one thing together, right in front of me, and actually see why it gets slow instead of just reading that it does.
<!-- /presentation:column -->
<!-- presentation:column -->
### To actually get it
This job rewards curiosity way more than any diploma. You learn how the giant version works by building a tiny version you fully understand, breaking it on purpose, and fixing it. The learning genuinely never stops, which is the best and the most exhausting part.
<!-- /presentation:column -->
<!-- /presentation:block -->

That, in one apartment-heating machine, is the whole job. Build the unglamorous thing that makes the clever thing real, and stay curious enough to keep rebuilding it.

<!-- /presentation:slide -->

<!-- presentation:slide id="thanks" layout="lead" density="normal" -->

# Thanks

## Questions welcome, especially the naive ones

dan.rio | github.com/danielcavalli

<!-- /presentation:slide -->
