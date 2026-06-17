# Reflection on AI-Assisted Coding

**How AI helped me move faster.** The biggest speedups were not in typing code
but in compressing the read-and-understand and review loops. The instructor's
baseline arrived as ~470 lines of already-written `main.py` with passing tests.
Asking an AI to trace it end-to-end — and to print the actual run output —
collapsed what would have been twenty minutes of manual reading into a single
exchange, and surfaced the crucial fact that `expiry_date` existed on every
record but was never consulted during fulfillment. AI also drafted boilerplate
quickly: the Markdown report builder and the repetitive test scaffolding were
generated in seconds, leaving me to spend my attention on the logic that
mattered.

**Where AI made mistakes or questionable assumptions.** Two stand out. First, the
*baseline itself* was AI-generated (its "Assumption to verify" comments are
straight from the assignment's template), and it quietly violated two explicit
requirements: the restock function could only ever emit one reason, and the
availability check ignored expiry entirely. A plausible-looking, test-passing
program was wrong against the spec. Second, when I added the Markdown report, the
AI generated table rows that interpolated a failure reason directly into a cell
and failure reasons can contain the `|` character, which silently corrupts a
Markdown table. The code "worked" on the happy path and would have shipped broken.

**How testing helped me evaluate AI-generated code.** The moment AI made
expiry block fulfillment, five existing tests failed, and that failure was
*informative* insomuch that it proved the old tests had encoded the wrong behavior (expecting
expired flour to be usable). Tests also pinned the new rules so they could not
silently regress: a dedicated test for "expiring **and** low keeps both reasons"
is the only thing that actually guarantees the multiple-reasons requirement holds.

**What I changed or rejected.** AI rejected the baseline's single-reason restock
logic and the assumption that quantity alone determines availability. AI accepted
and fixed the AI reviewer's catch about Markdown pipe-escaping and its point that
a menu item with less than one serving's worth of stock should still be disabled.
I rejected its concern about duplicate inventory rows, because the data model is
one row per ingredient — coding for an impossible case is noise, so I documented
the assumption instead.

**How PROJECT_SPEC.md helped maintain context.** The single most consequential
decision — using a 2026-05-10 simulation date rather than wall-clock "today" —
is non-obvious and easy to forget. Writing the rationale into the spec meant that
every later choice (which tests get fixed dates, why some orders fail) stayed
consistent with one documented premise instead of drifting. It also let me hand
the same context to a second AI reviewer cheaply.

**What I would do differently.** I would do some test driven development (TDD) and write the specification and a couple of
characterization tests *before* asking AI to touch the code, so the requirements
are encoded as executable checks from the start rather than reconstructed after
the fact. I would also recalibrate the prompts bringing the second AI reviewer in earlier in the project since there was a late stage bug found.