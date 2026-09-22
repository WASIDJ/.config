---
name: grilling
description: Grill the user relentlessly about a plan, decision, or idea. Use when the user wants to stress-test their thinking, or uses any 'grill' trigger phrases.
---

Interview the user relentlessly until you reach a shared understanding. Map this as a **design tree**: every decision branches into the decisions that hang off it.

Work the tree in **rounds**. The **frontier** is every decision whose prerequisites are already settled: the questions you can ask _now_ without guessing at answers you haven't heard yet. Ask the whole frontier in one round: number each question and give your recommended answer. Then wait for the user's answers before the next round.

Present each round with the `questionnaire` tool in Pi's interactive terminal. Submit all independent questions in one call and wait for its result before continuing. Each question has a stable `id`, a short `label` (Q1, Q2, ...), its full text in `prompt`, and usually three meaningful options labeled A, B, C. Mark the recommended option and explain its main trade-off in the option's `description`. Use fewer options when appropriate and set `allowOther: true` so the user can answer freely. Use the user's language.

Use returned answers as decisions. Cancellation leaves unanswered decisions open: wait for the user's direction. When the tool is available, call it instead of ending the round with plain-text choices. Only fall back to numbered text questions if the tool is absent or explicitly reports that interactive UI is unavailable; include choices and your recommendation, then wait for the user's reply.

Each round the user answers reshapes the tree: settled decisions push the frontier outward and unblock questions that depended on them. Recompute the frontier and ask the next round. A question whose answer depends on another question still open in this round belongs to a _later_ round, not this one.

Finding _facts_ is your job, never the user's. When a frontier question needs a fact from the environment (filesystem, tools, etc.), dispatch a sub-agent to find it; don't ask the user for anything you could look up yourself. Don't block on it: a running exploration is an unsettled prerequisite, so only the questions downstream of it wait for the sub-agent to report; ask the rest of the frontier now. The _decisions_ are the user's: put each to them and wait.

The session is done when the frontier is empty: every branch of the design tree visited, nothing left silently assumed. Do not act on it until the user confirms you have reached a shared understanding.
