---
name: grant-writing
description: Draft, revise, or critique a research grant proposal — Specific Aims, Research Strategy, abstract, project narrative, or a foundation/prize equivalent. Also invoke when brainstorming an idea that is headed for a proposal, because the reasoning has to hold up before the prose is written. Covers what to read first, how to structure each section, the writing register to use, and the duty to say out loud when the science does not connect.
---

# Grant writing

Two failure modes kill a draft. The prose sounds machine-written, or the argument has a hole that
prose is being used to cover. Guard against both, and treat the second as the more important one.

## Before drafting anything

1. **Get the container right.** Which NOFO, which deadline, how many pages, which sections. For
   NIH R21s (including PAR-25-442, the current target) all of this is in the knowledge-base note
   `nih-r21-application-mechanics` — page and line limits, formatting rules that cause an
   application to be returned unreviewed, the three scored factors, the NOFO's own required
   content, and policy deadlines. Read it rather than re-deriving it. For anything else, find the
   sponsor's own instructions and write the limits down before writing prose.
2. **Read two real exemplars in the target genre.** A funded application's Specific Aims and
   Significance, or a recent review in the field. This is not optional; it is what pulls the
   register away from the terse, bulleted default. `nih-r21-application-mechanics` lists funded
   R21s and what each does structurally, and points at the funded competition under the same NOFO.
3. **Read the voice note.** `outline-to-prose-style` holds the specific register, the AI tells the
   user has flagged, and an approved voice anchor. Follow it; do not restate it here.
4. **Find out where the text will live** before creating files — an existing doc, a new markdown
   draft, LaTeX. Do not invent a location or a toolchain.

## Order of work

Write in the order that keeps the parts consistent, not the order they are read in.

Significance and Innovation → Approach → back to Specific Aims → check scope against the budget and
project period → abstract and narrative last, as a compression of the aims page.

Do not start prose until the aims skeleton is agreed with the user: the hypothesis, the two or three
aims, and one sentence per aim on what result would count as success. Everything downstream inherits
mistakes made here.

## What each section has to do

**Specific Aims** (one page, no figures). The arc that funded applications use: field-level problem
with real numbers → the specific gap, named → why it is now tractable → one or two sentences of
your own preliminary evidence → the objective of *this* application, with the mechanism named →
explicit hypothesis → the aims as bold lead-ins → what the project delivers and what it enables.

**Aim design.** Two aims, three at most. An aim whose value depends on one outcome is a liability —
design it so both outcomes are informative. Aims must not depend on each other; if Aim 2 is dead
when Aim 1 fails, that is one aim. Purely descriptive aims belong in preliminary data.

**Significance.** Put the case for importance in the context of the field's state, the long-term
plan, and the preliminary data. Attribute each limitation of prior work to a specific citation.
State the strengths *and weaknesses* of the prior work you are building on — that is a scored item,
not a courtesy.

**Innovation.** Write it as obstacles removed, not as adjectives. The pattern that works: name the
specific limitations that have blocked progress, then enumerate how this project removes each one.
Every novelty claim should be the direct negation of a limitation stated earlier.

**Approach.** Organize around the aims, with a header per aim. Per aim: rationale, the experiments,
expected outcomes, then alternatives if the result is negative or surprising. Include the controls,
replicates, sample-size logic, and analysis plan. Say what you will do if the first branch fails.
State scope limits out loud — naming what is deliberately outside a two-year project reads as
judgement, not as a gap.

**Abstract and narrative.** Compress the aims page and simplify the language. These are public
after award and are used to route the application to an institute, so the keywords matter.

## Register

Governed by `outline-to-prose-style`. The short version: flowing paragraphs, plain descriptive
headers, short sentences, no antithesis constructions, few em-dashes, no enumerated
"Reason 1 / Reason 2" scaffolding, no long clause-stacked sentences. Bold sparingly, on the
sentences you most need a skimming reviewer to catch.

Cut anything that does not make the case. Extra material is not neutral — it gives a reviewer more
surface to find fault with, and it costs page budget that Approach needs.

Track the budget as you write: pages for the Research Strategy, and an actual line count for a
line-limited abstract. Report how much is used when you hand a draft back.

## Challenge the science as you go

This is part of the job, not an interruption of it. The user has asked for it explicitly.

- **Say it when the argument does not connect.** If a claim does not follow from the evidence, if an
  aim does not test the stated hypothesis, if two sections assume different things, if a control is
  missing, if the readout cannot detect the effect being claimed — stop and say so plainly, in one
  or two sentences, then keep working. Do not smooth it over with better phrasing. Confident prose
  over a broken argument is worse than an obvious hole, because the hole gets found in review.
- **Distinguish the two cases.** "I cannot follow the step from X to Y" is different from "this is
  wrong because Z." Say which one you mean. Not following something is still worth raising: if it
  does not connect for you, it will not connect for a reviewer outside the subfield.
- **Keep a running open-questions list** alongside the draft, and surface it with each handoff.
  Numbers not yet sourced, feasibility assumptions, claims resting on one unpublished result, the
  weakest link in each aim. Empty is a fine state; silently dropped is not.
- **Never fill a hole with invention.** No fabricated citations, effect sizes, timelines, costs, or
  preliminary results. Mark the slot — `[N =?]`, `[cite]` — and ask. A number in a draft will be
  believed later.
- **Anticipate the reviewer's questions.** Is this important? Can this team do it? Can it be done in
  the time and money available? Is someone already doing it, or has it been done? Is the framing
  going to trip a stated low-priority or non-responsiveness rule in the NOFO? Raise these while
  there is still time to restructure.

## The limit on what an agent should write

NIH policy (NOT-OD-25-132, in force since the September 2025 receipt date) states that NIH will not
consider applications substantially developed by AI, or containing sections substantially developed
by AI, to be the applicant's original ideas; enforcement can reach the Office of Research Integrity.
Other sponsors are converging on similar language.

So the working division is: the science, the argument, and the final voice are the PI's. Useful
contributions are structuring an outline the PI has supplied, tightening and cutting, checking
against the sponsor's rules, hunting inconsistencies, drafting from the PI's own material and
prior text, and asking the questions a reviewer would. Generating a proposal from a one-line idea
is not one of them. If a request drifts that way, say so and offer the version that does not.
