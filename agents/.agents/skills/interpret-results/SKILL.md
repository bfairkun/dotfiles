---
name: interpret-results
description: >
  Discuss analysis results through candidate readings and clarifying questions. Invoke when
  the user wants to interpret a figure or result, get on the same page mid-analysis, choose
  a next analysis based on a finding, or resolve unconfirmed interpretations before writing
  notebook prose or rendering. Works with or without a notebook.
---

# Interpret Results

Help the user decide what the evidence means with minimal typing. Work on the current result
or a small related group; do not require a whole-notebook review.

## Discuss the evidence

1. Show or link the relevant figure/result and briefly state the measured observation. Inspect
   the evidence before proposing readings; separate observations from explanations.
2. Lead with a few concise, evidence-grounded candidate readings in plain language. Readings
   often complement each other: default to multiple selection and explicitly enable it when
   the question interface supports it. Invite the user to select all that apply. If the
   interface only supports single selection, use a numbered chat checklist with combinations
   by number instead of forcing a single choice. Include a cautious or unresolved reading
   when warranted; do not equate uncertainty with no effect.
3. Always offer **"Chat about this / another explanation"**. Allow additions or qualifications
   to selected readings, not just replacement answers. If interface limits constrain the
   options, offer fewer candidate readings and retain the discussion option.
4. When the user chooses discussion, explore their alternative or uncertainty, then offer
   revised candidates or briefly check the resulting reading. A selected reading or clear
   conversational agreement is enough; do not ask for a separate formal endorsement. Silence,
   a preselected default, or permission to continue computation does not confirm a reading.
   Combine compatible selections, retaining their qualifications. If selected readings truly
   conflict, ask a focused follow-up rather than silently choosing one or combining them.
5. If the reading changes what to analyze next, clarify the consequential choice before
   pursuing that branch. An unresolved interpretation is a valid outcome; propose a check
   that could distinguish explanations rather than inventing a conclusion.

Do not offer unsupported mechanisms as established findings. If a chosen explanation exceeds
the evidence, explain the limitation and distinguish a hypothesis from a supported conclusion.

## Carry the interpretation forward

- Preserve the user's qualifications and uncertainty when paraphrasing; do not add stronger
  claims or an explanatory narrative they did not select or state.
- Keep a short record in existing session state of the result, agreed reading, unresolved or
  agent-only alternatives, and any next step. Revisit only when evidence or claims change.
- For notebook prose, follow [new-notebook](../new-notebook/SKILL.md#interpretation-and-attribution).
  Keep the discussion record out of the notebook's scientific narrative.

## Pre-render catch-up

Review the draft's interpretations against the conversation and session state. Apply the
questions above only to new, changed, or unresolved claims; carry unchanged agreed readings
forward without asking again. For existing agent-only prose, offer the choices to adopt the
reading, retain a useful AI-signed note, delete it, or discuss it. Omit unneeded agent prose by
default. Include any relevant user conclusions missing from the draft, then update the preview.
