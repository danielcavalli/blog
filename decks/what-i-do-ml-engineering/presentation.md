---
marp: true
theme: default
paginate: true
size: 16:9
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');
  section {
    background: #ffffff;
    color: #111111;
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    font-size: 22px;
    line-height: 1.5;
    padding: 48px 64px;
  }
  h1, h2, h3 {
    font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
    color: #1A6B7A;
    letter-spacing: -0.03em;
  }
  h1 {
    font-size: 1.8em;
    font-weight: 600;
    margin-bottom: 0.5em;
  }
  h2 {
    font-size: 1.3em;
    font-weight: 500;
    letter-spacing: -0.02em;
    margin-top: 0;
  }
  code {
    background: #F4F4F4;
    color: #1A6B7A;
    padding: 2px 8px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 0.9em;
  }
  pre {
    background: #1A1A1A !important;
    border-radius: 8px;
    padding: 16px 24px !important;
    font-size: 0.78em;
    margin: 8px 0;
    border: none !important;
    outline: none !important;
    box-shadow: none !important;
  }
  figure, img { border: none !important; outline: none !important; }
  pre code {
    background: transparent;
    color: #e0e0e0;
    padding: 0;
  }
  a { color: #1A6B7A; }
  table { font-size: 0.78em; width: 100%; margin: 12px 0; border-collapse: collapse; border-spacing: 0; }
  table, thead, tbody, tr, th, td { border: none !important; outline: none !important; border-style: none !important; }
  th {
    background: #1A6B7A;
    color: #ffffff;
    font-weight: 600;
    padding: 8px 16px;
  }
  th:first-child { border-radius: 8px 0 0 0; }
  th:last-child { border-radius: 0 8px 0 0; }
  td {
    background: #F5F5F5;
    padding: 8px 16px;
  }
  blockquote {
    border-left: 3px solid #1A6B7A;
    background: #F4F4F4;
    padding: 12px 24px;
    margin: 12px 0;
    font-size: 0.95em;
    color: #333333;
    border-radius: 0 8px 8px 0;
  }
  ul, ol { margin: 6px 0; }
  li { margin: 4px 0; }
  p { margin: 10px 0; }
  section::after { color: #6B6B6B; }
  strong { color: #1A1A1A; }
  section.lead {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.lead h1 {
    font-size: 2.6em;
    text-align: center;
    color: #ffffff;
  }
  section.lead h2 {
    text-align: center;
    font-size: 1.2em;
    color: #8CC8D4;
    font-weight: 400;
  }
  section.lead p {
    text-align: center;
    color: #B8DEE6;
    font-size: 1.05em;
  }
  section.divider {
    background: #152D38;
    color: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  section.divider h1 {
    font-size: 2.4em;
    text-align: center;
    color: #ffffff;
  }
  section.divider h2 {
    text-align: center;
    color: #8CC8D4;
    font-size: 1.1em;
    font-weight: 400;
  }
  section.emphasis {
    background: #F4F4F4;
  }
  section.emphasis blockquote {
    background: #ffffff;
    font-size: 1.15em;
    padding: 24px 32px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  }
  .bio-layout {
    display: flex;
    gap: 48px;
    align-items: flex-start;
    margin-top: 0;
  }
  .bio-content { flex: 1; }
  .bio-content h1 { margin-bottom: 4px; }
  .bio-photo {
    flex-shrink: 0;
    margin-top: 8px;
  }
  .bio-photo img {
    width: 260px;
    height: 260px;
    border-radius: 16px;
    object-fit: cover;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
  }
  .bio-detail {
    color: #6B6B6B;
    font-size: 0.88em;
    margin: 2px 0;
  }
  .card-row {
    display: flex;
    gap: 20px;
    margin-top: 16px;
  }
  .card {
    flex: 1;
    background: #F5F5F5;
    border-radius: 10px;
    padding: 20px 24px;
    border-left: 3px solid #1A6B7A;
  }
  .card h3 {
    font-size: 0.95em;
    margin: 0 0 8px 0;
  }
  .card p {
    font-size: 0.82em;
    color: #555;
    margin: 0;
    line-height: 1.45;
  }
  .card-dark {
    background: #152D38;
    border-left: 3px solid #8CC8D4;
  }
  .card-dark h3 { color: #8CC8D4; }
  .card-dark p { color: #B8DEE6; }
  .split {
    display: flex;
    gap: 40px;
    align-items: flex-start;
  }
  .split > div { flex: 1; }
  .split > div + div { border-left: 2px solid #E0E0E0; padding-left: 40px; }
  .dim { color: #6B6B6B; font-size: 0.85em; }
  .small { font-size: 0.8em; }
  section.dark-content {
    background: #1A1A1A;
    color: #E0E0E0;
    padding: 36px 56px 28px;
  }
  section.dark-content h1 {
    color: #ffffff;
    font-size: 1.5em;
    margin: 0 0 20px 0;
  }
  section.dark-content blockquote {
    background: #252525;
    color: #B8DEE6;
    border-left-color: #1A6B7A;
  }
  footer {
    color: #6B6B6B;
    font-size: 0.65em;
  }
footer: Daniel Cavalli | dan.rio
---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# What I Actually Do All Day

## Machine Learning Engineering, explained to my friends

Daniel Cavalli | dan.rio

---

<!-- _paginate: false -->
<!-- _footer: '' -->

<div class="bio-layout">
  <div class="bio-content">
    <h1 style="margin-bottom: 4px;">Daniel Cavalli</h1>
    <p class="bio-detail">Senior Machine Learning Engineer</p>
    <p class="bio-detail">9 years in ML. Studied economics. Writes at dan.rio</p>
    <div style="margin-top: 28px;">
      <table>
        <tr><th></th><th>Section</th><th>What you'll actually get</th></tr>
        <tr><td>1</td><td>The Job Nobody Can Name</td><td>"So, what is it you do again?"</td></tr>
        <tr><td>2</td><td>What a Model Actually Is</td><td>The thing, minus the mystery</td></tr>
        <tr><td>3</td><td>The Platform</td><td>What I'm doing while you text me</td></tr>
        <tr><td>4</td><td>Making Training Fast</td><td>Why I'm obsessed with waiting less</td></tr>
        <tr><td>5</td><td>Why Models Rot</td><td>Why the job never actually ends</td></tr>
        <tr><td>6</td><td>How I Got Here</td><td>How an economics kid wound up here</td></tr>
      </table>
    </div>
  </div>
  <div class="bio-photo">
    <img src="./assets/profile-picture.png" />
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Job Nobody Can Name

## Everyone says "AI" now. Almost no one can tell you who builds the plumbing underneath it.

---

# When you ask what I do

I say "Machine Learning Engineer." You hear "AI." You picture a robot, or ChatGPT, or me in a dark room quietly training Skynet. Then you nod politely and we talk about something else.

That is completely fair, because for years the only people explaining this stuff were trying to sell you something, so the words got strange before they got useful. Here is the version I would actually tell you over a beer.

> You know the AI everyone talks about? I build the boring, invisible machinery that keeps it from falling over the second a real person uses it.

The clever model is the famous part. The machinery is the part that decides whether that model ever leaves someone's laptop.

---

# Two jobs everyone confuses

<div class="split">
  <div>
    <h3>The Data Scientist</h3>
    <p>Their question: <em>what should this thing learn, and is it any good?</em> They invent the recipe. What they hand over is something that worked once, on their laptop, on a good day.</p>
  </div>
  <div>
    <h3>The ML Engineer (me)</h3>
    <p>My question: <em>okay, but how does this run millions of times a day without breaking, and who gets the 3am phone call when it does?</em> I keep the recipe working forever, for everyone, with nobody watching over it.</p>
  </div>
</div>

<div class="card-row">
  <div class="card">
    <h3>The restaurant, basically</h3>
    <p>The data scientist is the chef who dreams up a dish. I build the kitchen that cooks that same dish ten thousand times a night, tasting the same every time, without setting the place on fire. Inventing a recipe and running a kitchen are just different jobs. People mix them up because both involve food.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# The line that explains everything

> A model on someone's laptop is a cool science-fair project. The same model out in the real world is a promise you have to keep every single second of every day.

The whole trade lives in the gap between those two sentences. Getting something to work once is the easy, fun part almost anyone can do. Keeping it working, for real people, while the world keeps changing underneath it, is the hard part. And it turns out that hard part is mostly plumbing, not maths.

That gap is where I spend my days.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# What a Model Actually Is

## Before the job makes sense, the thing itself has to make sense

---

# A model teaches itself the rules

Normal software is just a list of rules a person wrote down by hand: *if the customer earns more than this and is younger than that, say no to the loan.* Every rule was typed by a human, and when it gets something wrong, you can point at the human who typed it.

A model flips that around. Nobody writes the rules. You show it millions of past examples, the good and the bad, and it works out its own rules from the patterns. Think of how you can spot a friend's face in a crowd without being able to explain exactly how. It ends up making calls that no person ever spelled out, which is the whole reason it is so powerful and also faintly unsettling.

> You are not writing down the answer. You are building the thing that comes up with the answer. And then you have to trust something whose reasoning you cannot fully read back.

---

# Two phases, two completely different problems

<div class="card-row">
  <div class="card">
    <h3>Training (the studying)</h3>
    <p>The model sits down with mountains of past examples and slowly learns. This is the expensive, slow part: rooms full of special chips running for days, quietly burning through an electricity bill that would make you wince. You do it rarely.</p>
  </div>
  <div class="card">
    <h3>Using it (the exam)</h3>
    <p>Once it has studied, you ask it one real question and it answers on the spot. This has to be instant and cheap, because it might happen tens of thousands of times a minute, and each answer has to land before anyone notices they waited.</p>
  </div>
  <div class="card card-dark">
    <h3>Where I come in</h3>
    <p>Both parts are really plumbing problems wearing a lab coat. Someone has to make the studying fast enough to bother with and the answering reliable enough to trust. That someone is me.</p>
  </div>
</div>

---

# The lifecycle, and where each of us lives

<div class="card-row">
  <div class="card" style="text-align: center;">
    <h3>Data</h3>
    <p>Collect it, clean it, make it trustworthy. Boring, unglamorous, and the single biggest reason models fail.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Train</h3>
    <p>Where the data scientist mostly lives. Turn data into a model that works.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Ship it</h3>
    <p>Get it off the laptop and into the actual app that real people use.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Monitor</h3>
    <p>Watch it in the wild. Catch it the moment it starts to quietly get worse.</p>
  </div>
  <div class="card" style="text-align: center;">
    <h3>Retrain</h3>
    <p>The world moved, so the model has to. Then the whole loop runs again.</p>
  </div>
</div>

<p style="margin-top: 20px;">The data scientist mostly owns one of those boxes. I own the arrows between all of them, and the fact that this whole circle keeps spinning on its own while everyone sleeps.</p>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Platform

## My users are not customers. They are the people who build the models.

---

# I make the tools for the people who make the AI

Most apps are built for regular people like you. I build tools for the people who build the AI, the folks whose entire job is dreaming up new models. I am the ground they stand on, which mostly means they only notice me when the ground shakes.

<div class="split">
  <div>
    <h3>Who I'm building for</h3>
    <p>A whole company's worth of these model-builders, with piles of models running live at any given moment. Every one of them wants to build and ship without first having to become a plumbing expert. My job is to spare them that.</p>
  </div>
  <div>
    <h3>What I'm actually building</h3>
    <p>A shared foundation, so nobody has to reinvent the boring machinery from scratch every single time. They bring the clever idea. The platform quietly handles everything underneath it.</p>
  </div>
</div>

> Do it well and nobody ever thinks about me. Do it badly and nothing works. My whole job is to be invisible, which is a genuinely weird thing to build a career around.

---

# What "platform" actually means

<div class="card-row">
  <div class="card">
    <h3>A place to train</h3>
    <p>All the heavy computers and chips, wired up so someone can say "run my experiment" and just get an answer back, without ever wrestling with a server themselves.</p>
  </div>
  <div class="card">
    <h3>A safe way to ship</h3>
    <p>A paved road from "works on my laptop" to "live for everyone," with guardrails so a broken version can't quietly sneak out to real people.</p>
  </div>
  <div class="card">
    <h3>A way to keep watch</h3>
    <p>Keeping the live models quick and healthy, and tapping me on the shoulder the moment one starts drifting away from reality.</p>
  </div>
  <div class="card">
    <h3>Room to grow</h3>
    <p>Building it so the same setup works in a new country without tearing it all down and starting over. Growing should be a small tweak, not a full rebuild.</p>
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Making Training Fast

## The unglamorous number that quietly decides everything: how long you have to wait.

---

# One computer is never enough

Teaching a big model on a single machine can take weeks. A lot of my job is turning "weeks" into "a few days," so that training a model stops being a rare event you plan your month around and becomes a normal Tuesday.

You would think you just add more computers and it goes faster. That is exactly where most people's guess stops, and it is a perfectly sensible guess. It is also where the real problem starts, because computers, like people, are terrible at working together without a lot of help.

<div class="split">
  <div>
    <h3>The group-project problem</h3>
    <p>Picture a group project where everyone has to end up on the same page, constantly. You split the work up, but now they all have to stop and compare notes over and over. Coordinate it badly and eight people somehow finish slower than one. Computers are exactly like this.</p>
  </div>
  <div>
    <h3>Where my actual work is</h3>
    <p>So the job is almost never "buy more machines." It is getting them to talk to each other without tripping over their own feet: who does which piece, when they check in, and how to keep everyone busy instead of standing around waiting.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# The number that matters more than raw speed

> The real prize is shrinking the wait between "I have an idea" and "I can see whether it worked" from a coffee break down to a breath.

That sounds like a convenience. It is actually a change in how people think. When feedback takes many minutes, you get careful and cautious, you batch up your guesses, you stop experimenting because each try costs real time. When it takes seconds, you just try things.

Quick feedback does not just make people work faster. It makes them braver. That is the real thing I am selling, and almost nobody outside this world would guess that a whole platform gets built around something as human as how long people are willing to wait.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Why Models Rot

## The part nobody warns you about: the model that was right last month is quietly wrong today.

---

# The world moves. The model doesn't.

A model learns from the past. That is the whole trick and also the whole problem, because the past is the only thing it will ever know, and the world refuses to hold still.

Fraud patterns change the week after you catch them. Prices move. People change how they behave. The model does not notice any of this. It keeps confidently applying yesterday's rules to today's world, and every dashboard says it is running perfectly while its answers slowly drift from useful to wrong.

> This is called drift, and it is the quiet villain of the whole field. Nothing crashes. No alarm goes off. The model just gets worse in complete silence until someone thinks to check.

So the job is never "ship it and move on." It is watch it, catch the drift, retrain, redeploy, and do it again, forever.

---

# Doing all of that, for a lot of models at once

Now imagine everything on the last slide, but for hundreds of models at the same time, and without an army of people hand-holding each one. My corner of the field has an unlovely name for this, "MLOps," but really it just means making the boring, repetitive parts automatic and trustworthy.

<div class="card-row">
  <div class="card">
    <h3>Assembly lines</h3>
    <p>Instead of a person clicking through every update by hand, the boring steps run themselves on a schedule. A human decides what should happen; the machine handles the tedious business of making it happen.</p>
  </div>
  <div class="card">
    <h3>A written-down recipe</h3>
    <p>The whole setup is written down step by step, like flat-pack furniture instructions, so anyone can rebuild it or spot a mistake. The alternative is it living only in one person's head and a folder of fragile scripts that break if you look at them wrong.</p>
  </div>
  <div class="card">
    <h3>Rebuilding mid-flight</h3>
    <p>A lot of my recent work is replacing the foundations while hundreds of people keep using the thing every day. It is a bit like changing a plane's engine without landing the plane.</p>
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# How I Got Here

## I have an economics degree and went to a game-development school. This was not a plan.

---

# The path made no sense until it did

I studied economics at university. Before that, a technical high school for making video games. Neither is the obvious runway for a career in machine learning infrastructure, which is rather the point.

<div class="split">
  <div>
    <h3>Where it started</h3>
    <p>My first real job was reading open-ended survey text with an early language model, back when explaining "AI" at a dinner table got you a blank stare rather than an opinion. Then anti-fraud, which is where I learned that a model is only as good as the system holding it up.</p>
  </div>
  <div>
    <h3>What actually shipped</h3>
    <p>That anti-fraud work stopped a meaningful amount of fraud at a tiny cost per check. What stuck with me was the lesson, not the number: the model mattered, and the machinery around it mattered more.</p>
  </div>
</div>

The through-line is not a degree. It is a specific taste for the unglamorous half of the problem, the half that decides whether any of the clever part ever reaches a real person.

---

<!-- _class: emphasis -->

# What I want my friends to take away

> This is a trade, not a talent. It is closer to being a very stubborn plumber than a lone genius. The romance is optional. The reliability is not.

The field wraps itself in mystique because mystique sells, and for a while I half-believed it too. But strip that away and it is craft: build the thing, make it fast, keep it honest, and be there when it breaks. Learnable, unglamorous, and quietly satisfying in the way any real trade is.

You do not need a PhD or anyone's permission to start. I certainly didn't have either.

---

# The home lab, and why it's there

There are two graphics cards humming in my apartment right now, doing nothing anyone is paying for. I built that little machine on purpose.

<div class="split">
  <div>
    <h3>Not to be fast</h3>
    <p>It will never win any speed contest, and that was never the point. It is there so I can watch two chips try to learn one thing together, right in front of me, and actually see why it gets slow instead of just reading that it does.</p>
  </div>
  <div>
    <h3>To actually get it</h3>
    <p>This job rewards curiosity way more than any diploma. You learn how the giant version works by building a tiny version you fully understand, breaking it on purpose, and fixing it. The learning genuinely never stops, which is the best and the most exhausting part.</p>
  </div>
</div>

That, in one apartment-heating machine, is the whole job. Build the unglamorous thing that makes the clever thing real, and stay curious enough to keep rebuilding it.

---

<!-- _class: lead -->
<!-- _paginate: false -->
<!-- _footer: '' -->

# Thanks

## Questions welcome, especially the naive ones

dan.rio | github.com/danielcavalli
