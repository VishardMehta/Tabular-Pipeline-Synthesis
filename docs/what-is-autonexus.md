# AutoNexus, explained

For anyone joining the project or seeing it for the first time. No ML background
assumed.

---

## The one-liner

**Upload a spreadsheet, get back a machine-learning pipeline written for it -
plus an honest account of why, and what we checked.**

---

## The 30-second version

Say you have a CSV of customers and you want to predict who will cancel.

Normally a data scientist spends a day looking at the file, deciding how to
clean it, which model to try, and how to measure success. AutoNexus does that
first pass in about ten seconds.

You upload the file, point at the column you want to predict, and you get:

- **A profile** of your data: what's missing, what's duplicated, what looks
  broken, and which columns might be cheating.
- **A strategy**: what to do with each column, which models are worth trying,
  and how to evaluate them - each with a reason.
- **The actual Python code**, ready to run.
- **A checklist** of what we verified about that code.

You take the code and run it yourself.

---

## How it works, in five steps

```
  Upload  ->  Pick target  ->  Profile  ->  Strategy  ->  Pipeline
   CSV        the column       Python       the plan      the code
              to predict       measures     + reasons     + checks
```

1. **Upload** - a CSV. We check it's usable and reject it clearly if not
   (empty, duplicate column names, too big, and so on).

2. **Pick the target** - the one column you want to predict. Everything else
   becomes a possible input. You can also tick columns to leave out entirely.

3. **Profile** - this is all plain Python, no AI. We measure every column:
   type, how much is missing, how many distinct values, how it relates to your
   target. We work out whether this is a yes/no question, a
   pick-one-of-many question, or a predict-a-number question, and which
   scoring measure fits.

4. **Strategy** - *now* the AI comes in. It reads the measurements and writes a
   plan: which columns to drop and why, how to prepare each one, which two to
   four models to consider, and how to validate.

5. **Pipeline** - the AI writes the code, and we run a dozen automated checks
   over it before showing it to you.

---

## The one thing that makes this different

**We never run the generated code, and we never show you a score.**

Most AutoML tools train a model and show you "94% accurate". That number is
only trustworthy if you trust everything that happened upstream, invisibly.

We deliberately stop short. The product's job is to give you a **defensible
starting point you can read**, not a black box with a number on it. So:

- No accuracy figures, no leaderboards, no "best model" badge.
- A banner on the code screen that says, in as many words:
  *"This pipeline has not been executed. Static checks only."*
- If we can't measure something honestly, we say so instead of estimating it.

This is a design decision, not a missing feature. It's enforced in the code:
the data structure that holds the AI's answer has **no field that can hold a
score**, so one cannot be added by accident.

---

## The rule the whole system is built on

> **Python computes the facts. The AI reasons about the facts.
> The AI never sees your raw data.**

Your actual rows never leave the server. What goes to the AI is a summary:
column names, types, and statistics. Nothing else.

That matters for three reasons:

- **Privacy** - your customer records aren't sent to a third party.
- **Cost** - a summary is small, so each request is cheap and fast.
- **Trust** - the AI can't invent a fact about your data, because it was only
  ever given facts we measured ourselves.

---

## What are the "checks"?

Before you see the code, we parse it and verify twelve things. The important
ones, in plain terms:

| We check | Because |
|---|---|
| It's valid Python | Obvious, but worth confirming |
| It only imports approved libraries | So it can't reach the network or the file system |
| No dangerous commands | No `eval`, no shell access, no downloads |
| Every column it names really exists | AI models sometimes invent plausible-looking column names |
| It actually uses your target column | A pipeline that ignores what you asked for is useless |
| It matches the plan it just wrote | Catches the AI contradicting itself |
| It evaluates on held-out data | Otherwise the results would be meaningless |
| It sets a random seed | So you get the same answer twice |
| Columns it said it dropped, it really dropped | Including the ones *you* excluded |

Failures don't hide the code. You see what was generated **and** what's wrong
with it, and you decide.

---

## What it's built with

- **Backend**: Python, FastAPI. The profiling is pandas. The AI is Google
  Gemini.
- **Frontend**: React and TypeScript.
- **Storage**: SQLite. Uploads are deleted automatically after 24 hours.
- **Tests**: 212, and they run without touching the network - real AI responses
  are recorded once and replayed.

---

## Honest current limits

Worth saying out loud so nobody is surprised:

- **One target column at a time.** No multi-output prediction.
- **Supervised learning only.** No clustering or anomaly detection.
- **No training or execution.** By design, see above - but it does mean you
  need somewhere to run the code.
- **CSV only.** No Excel, Parquet or database connections.
- **No accounts or history.** Datasets are anonymous and expire after a day.
- **Local use only for now.** There's no login or rate limiting yet, so it
  shouldn't be put on the public internet as-is.

The full list, with reasoning for each, is in `docs/not-building.md`.

---

## Likely questions

**"Is this replacing data scientists?"**
No. It's replacing the first hour of a data scientist's day - the part that's
the same on every dataset. The judgement calls are still handed back to a
person, in writing.

**"How do I know the AI didn't make it up?"**
That's what the checks are for, and why we show the plan before the code. The
AI is also constrained to copy the task type and scoring metric that Python
worked out - if it disagrees, it has to say so in the "risks" section rather
than quietly changing the answer.

**"What if it gets it wrong?"**
Then you've lost ten seconds and you can see exactly where it went wrong,
because the reasoning is on screen next to the code. That's the whole point of
not hiding it behind a score.

**"Can I use my own preprocessing / model choice?"**
Not directly - the AI choosing an approach *and justifying it* is the product.
But you can exclude any columns you don't want used, and you can override the
task type when the data is genuinely ambiguous (a 1-5 rating could reasonably
be treated as categories or as a number).
