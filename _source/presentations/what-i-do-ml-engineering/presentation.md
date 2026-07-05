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
        <tr><th></th><th>Section</th><th>The question it answers</th></tr>
        <tr><td>1</td><td>The Job Nobody Can Name</td><td>What is an ML Engineer, really</td></tr>
        <tr><td>2</td><td>What a Model Actually Is</td><td>The thing, without the mystique</td></tr>
        <tr><td>3</td><td>The Platform</td><td>What I build for a living</td></tr>
        <tr><td>4</td><td>Making Training Fast</td><td>Why waiting is the enemy</td></tr>
        <tr><td>5</td><td>Why Models Rot</td><td>The part nobody warns you about</td></tr>
        <tr><td>6</td><td>How I Got Here</td><td>An economics degree and a plan that didn't exist</td></tr>
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

# When people ask what I do

I say "Machine Learning Engineer." They hear "AI." They picture a robot, or ChatGPT, or someone in a dark room quietly training Skynet.

That instinct is fair. For most of the last decade the only people talking about this work were selling something, so the vocabulary got weird before it got useful. But the honest version of my job is less cinematic and more interesting than the marketing.

> I build the machinery that lets other people's models survive contact with reality.

The model is the famous part. The machinery is the part that decides whether the model is ever more than a demo.

---

# Two jobs everyone confuses

<div class="split">
  <div>
    <h3>Data Scientist</h3>
    <p>Asks: <em>what should this model learn, and is it any good?</em> Works with data, statistics, and experiments. Invents the recipe. Their output is a model that works once, on their machine, on a good day.</p>
  </div>
  <div>
    <h3>Machine Learning Engineer</h3>
    <p>Asks: <em>how does this run a million times a day, cheaply, reliably, and what happens at 3am when it breaks?</em> Their output is a system that keeps the recipe working forever, for everyone, without them in the room.</p>
  </div>
</div>

<div class="card-row">
  <div class="card">
    <h3>The kitchen analogy</h3>
    <p>The data scientist is the chef who invents a dish. I build the restaurant kitchen that serves that dish ten thousand times a night, at the same quality, without burning down. Inventing the recipe and running the kitchen are different skills. People assume they are the same job because both involve food.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# The line that explains everything

> A model in a notebook is a science project. A model in production is a promise you have to keep every second of every day.

The gap between those two sentences is the entire trade. Almost anyone can get a model working once. Keeping it working, for real users, while the world changes around it, is a different kind of problem, and it is mostly an engineering problem, not a maths one.

That gap is where I live.

---

<!-- _class: divider -->
<!-- _paginate: false -->

# What a Model Actually Is

## Before the job makes sense, the thing itself has to make sense

---

# A model is a function that learned its own rules

Normal software works like a recipe a human wrote. Someone sits down and types the rules: *if the income is above this and the age is below that, decline the loan.* Every rule is visible, chosen by a person, and blamed on a person when it is wrong.

A model works backwards. You do not write the rules. You show it millions of past examples, good outcomes and bad ones, and it finds the rules itself. It ends up making decisions no human explicitly wrote down, which is exactly why it is powerful and exactly why it is unsettling.

> You are not programming the answer. You are programming the thing that figures out the answer. And then you have to trust a system whose reasoning you cannot fully read back.

---

# Two phases, two completely different problems

<div class="card-row">
  <div class="card">
    <h3>Training</h3>
    <p>Teaching the model from historical data. Enormously expensive, done relatively rarely. This is where the fleet of GPUs lives, where a single run can take days, and where most of the electricity bill goes.</p>
  </div>
  <div class="card">
    <h3>Inference</h3>
    <p>Using the trained model to answer one real question, right now. Has to be fast, cheap, and constant. A fraud model might do this tens of thousands of times a minute, and each answer has to come back before the customer notices.</p>
  </div>
  <div class="card card-dark">
    <h3>Where I come in</h3>
    <p>Both phases are infrastructure problems dressed up as science problems. Someone has to make training fast enough to be usable and inference reliable enough to be trusted. That someone is the ML Engineer.</p>
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
    <h3>Deploy</h3>
    <p>Get it out of the notebook and into the real product, serving real people.</p>
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

<p style="margin-top: 20px;">The data scientist owns one box in that diagram. I own the arrows between all of them, and the fact that the loop keeps turning without anyone babysitting it.</p>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# The Platform

## My users are not customers. They are the people who build the models.

---

# I build tools for the people who build the models

Most engineers build software for the public. I build software for other engineers and scientists, the ones whose full-time job is inventing models. My work is the ground they stand on.

<div class="split">
  <div>
    <h3>The scale of it</h3>
    <p>A whole organisation's worth of data scientists and ML engineers, with a lot of models running in production at any moment. Each of them wants to train, ship, and monitor without becoming an infrastructure expert first.</p>
  </div>
  <div>
    <h3>The product is a platform</h3>
    <p>A shared foundation so that not every person has to reinvent how training runs, how deployment happens, how monitoring works. They bring the idea. The platform handles everything underneath it.</p>
  </div>
</div>

> If I do the job well, none of them ever think about me. If I do it badly, nothing ships. Being invisible is the goal, which is a strange thing to optimise a career around.

---

# What "platform" actually means

<div class="card-row">
  <div class="card">
    <h3>Training infrastructure</h3>
    <p>The compute, the GPUs, the pipelines that turn "run this experiment" into a result without the scientist ever touching a server.</p>
  </div>
  <div class="card">
    <h3>Deployment pipelines</h3>
    <p>The paved road from a model that works on a laptop to a model answering live requests, with safety rails so a bad version cannot quietly reach real users.</p>
  </div>
  <div class="card">
    <h3>Serving and monitoring</h3>
    <p>Keeping models fast and healthy in production, and raising a hand the moment one starts drifting away from reality.</p>
  </div>
  <div class="card">
    <h3>Expansion</h3>
    <p>Designing it so the same platform works in a new country without rebuilding it from scratch. Growth should be a config change, not a rewrite.</p>
  </div>
</div>

---

<!-- _class: divider -->
<!-- _paginate: false -->

# Making Training Fast

## The unglamorous number that quietly decides everything: how long you have to wait.

---

# One GPU is never enough

A large model trained on a single GPU can take weeks. A big part of my work is turning that kind of wait into something measured in days instead, so that training a model stops being a monthly event and becomes a normal Tuesday.

You would think you just add more GPUs and it goes faster, and that is where most people's intuition stops. It is a reasonable intuition. It is also where the actual problem begins, because GPUs do not naturally cooperate.

<div class="split">
  <div>
    <h3>The coordination problem</h3>
    <p>To use many GPUs at once you have to split the work: slice the model across them, or the data, or both. Then they all have to constantly compare notes and stay in sync. Get that coordination wrong and eight GPUs run slower than one.</p>
  </div>
  <div>
    <h3>Where the real work is</h3>
    <p>Most of the engineering is not "buy more hardware." It is making the hardware talk to itself efficiently: who holds which piece, when they synchronise, how to overlap the talking with the calculating so nothing sits idle.</p>
  </div>
</div>

---

<!-- _class: emphasis -->

# The number that matters more than raw speed

> The real prize is shrinking the wait between "I have an idea" and "I can see whether it worked" from a coffee break down to a breath.

That sounds like a convenience. It is actually a change in how people think. When feedback takes many minutes, you get careful and cautious, you batch up your guesses, you stop experimenting because each try costs real time. When it takes seconds, you just try things.

Fast feedback does not make people work faster. It makes them braver. That is the real product I am selling, and almost nobody outside the field would guess that developer patience is the metric a whole platform gets built around.

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

# MLOps: keeping the promise at scale

Everything from the last slide, done for hundreds of models at once without an army of people manually babysitting each one. The industry calls this MLOps. It is mostly the discipline of making the boring parts automatic and trustworthy.

<div class="card-row">
  <div class="card">
    <h3>Pipelines</h3>
    <p>Automated assembly lines that retrain, test, and redeploy models on their own, so a human is deciding what should happen, not clicking the buttons to make it happen.</p>
  </div>
  <div class="card">
    <h3>Infrastructure as code</h3>
    <p>The entire platform written down as code, not assembled by hand. It can be rebuilt, reviewed, and reasoned about, instead of living in one person's memory and a folder of fragile scripts.</p>
  </div>
  <div class="card">
    <h3>Rebuilding mid-flight</h3>
    <p>A large part of my recent work is replacing the platform's foundations while hundreds of people keep using it every day. Changing the engine without landing the plane.</p>
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
    <h3>Not for speed</h3>
    <p>It will never win a benchmark, and that was never the goal. It exists so I can watch distributed training happen on hardware I fully control, and actually see why it is slow instead of reading that it is.</p>
  </div>
  <div>
    <h3>For understanding</h3>
    <p>The trade rewards curiosity far more than credentials. You learn how the big pipes work by building small pipes you understand completely, breaking them, and fixing them. The learning never really stops, which is the best and worst part.</p>
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
