# AgentEval

An eval and cost harness for LLM agents. AgentEval scores an agent
against a human-reviewed golden set and reports answer quality, action
accuracy, retrieval recall, latency, token usage, and cost per case,
then turns those measurements into a deployment decision: an acceptance
gate a build must clear before it ships.

The harness works against any agent through the small agent interface in
`eval.py`. It ships with a deterministic mock agent, so the full
pipeline runs end to end with no services up and no API keys, and every
number in this README can be regenerated with the commands shown.

## Features

- `eval.py`: CLI harness. Loads a golden set, calls an agent, computes
  metrics, prints a scorecard, and can save a JSON report.
- `metrics.py`: answer quality (token F1 against expected keywords),
  action accuracy, retrieval recall@k, mock token pricing (input
  $0.15/1M, output $0.60/1M), latency p50/p99, token counts, cost per
  case.
- A 100-case golden set (v3): every case carries an expected action
  (answered, handoff, or escalate), expected evidence, and notes. The
  mix is 54 answered, 38 handoff, and 8 escalate, with 13 hard cases:
  missing documentation, contradictory policy, and unanswerable inputs
  alongside documented how-tos, policy questions, bug incidents, account
  actions, disputes, and prompt injections.
- `FakeAgent`: deterministic mock with canned answers for all 100 golden
  cases. `HttpAgent`: scores a live agent API over HTTP and passes its
  retrieved evidence through for recall scoring.
- `evals/threshold_sweep.py`: sweeps an agent's confidence threshold
  over the golden set and reports coverage, action accuracy, answered
  precision, and escalation recall per threshold, plus recall@5.
- `evals/run_day4.py`: the Day 4 analyses, a quality-vs-coverage curve
  for an acceptance gate on measured answer quality
  (`evals/quality_coverage.py`), a cost-aware gate choice
  (`evals/cost_routing.py`), and a reviewer-effort measurement
  (`evals/reviewer_effort.py`). Results land in
  `evals/quality_coverage_results.*`, `evals/cost_routing_results.*`,
  and `evals/reviewer_effort_results.*`.

## How it works

```
golden set (100 labeled cases)
  -> agent under test (FakeAgent, or HttpAgent against a live API)
  -> per-case scoring: action match, token F1, recall@5 on evidence
  -> summary scorecard: accuracy, mean F1, cost, latency, tokens
  -> acceptance gate on measured answer quality (Day 4)
  -> ship / review / reject decision with a priced cost model
```

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python eval.py                                   # baseline run, prints the scorecard
python eval.py --out report.json                 # also save the JSON report
python eval.py --agent http://localhost:8000     # score a live agent API
python evals/threshold_sweep.py                  # threshold + recall@5 report
python evals/run_day4.py                         # gate curve + cost + effort
pytest -q                                        # 25 tests
```

## Eval results

Day 3, golden set and sweep (`evals/threshold_sweep_results.md`):

- Golden set v3: 100 cases (54 answered, 38 handoff, 8 escalate), 13 of
  them hard cases. Golden routing verification: 100 of 100 cases match
  their labels at the 0.94 confidence setting.
- Retrieval recall@5: mean 1.0000 over the 81 evidence-bearing cases,
  full-hit rate 1.0000. Honest framing: the golden cases paraphrase the
  documented vocabulary, so read this as an in-vocabulary result, not a
  promise about unseen phrasings.
- Threshold sweep: action accuracy and answered precision hold at
  1.0000 from threshold 0.0 through 0.94 at coverage 0.54, then fall off
  a cliff at 0.97 (coverage 0.14, accuracy 0.6000). The confidence score
  being swept is a normalized retrieval score, not a calibrated
  probability; the sweep is an operating-point analysis.
- FakeAgent baseline over the 100 cases: action accuracy 1.0, mean
  answer F1 0.238, cost per case about $0.00001 at mock prices.

Day 4, the acceptance gate (`evals/quality_coverage_results.md`,
`evals/cost_routing_results.md`, `evals/reviewer_effort_results.md`):

- The gate auto-accepts an answered result only when its measured
  answer-quality score (token F1 against expected keywords) clears the
  gate. Offline the score is exact; a live agent would expose a runtime
  proxy for it.
- Quality-vs-coverage curve: with the gate open, coverage is 0.54 at a
  mean accepted F1 of 0.4408. Raising the gate trades coverage for
  accepted quality smoothly: gate 0.35 gives 0.42 coverage at F1 0.4747,
  gate 0.50 gives 0.12 at F1 0.6023, gate 0.80 gives 0.01 at F1 0.8462.
- Cost-aware gate choice: outcomes are priced in dollars (spot audit of
  an accepted answer $0.30, reviewer decision $1.20, handoff $4.80,
  escalation $8.00, wrong auto-accept penalty $6.00, plus the measured
  inference cost). The chosen gate is 0.35, at an expected $2.7340 per
  case: the cheapest gate whose accepted work clears the quality floor
  of mean accepted F1 at or above 0.45. The gate just below it, 0.30,
  misses the floor at F1 0.4444.
- Reviewer effort: at gate 0.35, the 100 golden cases take 429 human
  minutes (42 auto-accepted audits, 12 reviewer decisions, 38 handoffs,
  8 escalations) against a fully manual baseline of 800 minutes, a 46.4
  percent saving. Estimates under the stated minute assumptions, not a
  time study.
- Accepted action accuracy is 1.0000 at every gate. Read the caveat in
  the next section before quoting that number.
- Tests: 25 passing.

## Automation policy

AgentEval exists to make one decision defensible: whether an agent
build is allowed to ship. This section states what that decision means.

**The gate is a deployment rule, not a report.** An agent build ships
only if it clears the acceptance gate on the golden set: its accepted
work must hold a mean answer-quality score (token F1) at or above the
quality floor of 0.45, at an operating gate chosen by the cost model
(0.35 on the current baseline, $2.7340 per case). A build that misses
the floor does not ship, however good its other numbers look. Gate 0.30
is the standing example: it is cheaper per case and accepts more work,
and it is rejected because its accepted work scores F1 0.4444, under
the floor.

**What the gate proves.** On these 100 labeled cases, with these
expected actions and this evidence, the agent routes every case
correctly (action accuracy 1.0000), retrieves the expected evidence
(recall@5 1.0000), and its accepted answers clear a measured quality
bar at a known cost and a known reviewer-effort budget. That is a real,
reproducible regression check: rerun the harness after any change and a
worse build shows up as a worse scorecard.

**What the gate does not prove.** It does not prove the agent is right
on inputs unlike the golden set. The golden cases paraphrase the
documented vocabulary, so the perfect recall@5 is an in-vocabulary
result. It does not prove the confidence score is calibrated; it is a
normalized retrieval score, and the sweep treats it as an operating
point, not a probability. And it does not prove production behavior:
the golden set is a single development set, with no held-out split yet,
so these numbers are development measurements, not a generalization
guarantee.

**The honest mock-agent caveat.** The baseline agent is a deterministic
mock that never misroutes. That is why accepted action accuracy is
1.0000 at every gate: on this baseline there are no routing errors for
the gate to catch, so the gate trades answer quality against coverage,
not routing errors against coverage. Against a real agent that
sometimes answers what it should hand off, the same gate would also be
spending its penalty budget on wrong auto-accepts, and the curve would
look different. The harness supports that test today via `HttpAgent`;
the mock numbers should never be quoted without this caveat.

**When a human reviews.** Auto-acceptance is not the end of oversight.
Accepted answers get spot audits (priced at $0.30 and 0.5 minutes each
in the Day 4 models; 42 of them at gate 0.35). Every below-gate answer
goes to a reviewer for a decision (12 cases at gate 0.35). Handoffs and
escalations are always human work (38 and 8 cases). A human also owns
the golden set itself: labels, evidence, and the quality floor are
human judgments, and changing them changes what the gate enforces.

## Demo story

**1. Run the baseline.** `python eval.py` scores the mock agent against
all 100 golden cases and prints the scorecard: action accuracy 1.0,
mean answer F1 0.238 across all answered cases, cost per case at mock
prices, latency p50/p99. Add `--out report.json` to keep the full
per-case report.

**2. Read the scorecard like a reviewer.** The summary is the contract:
how many cases were answered, handed off, and escalated versus their
labels; what the answered ones scored; what each case cost. A build
that regresses shows up here first, before any gate math.

**3. Sweep the operating point.** `python evals/threshold_sweep.py`
shows accuracy and precision flat at 1.0000 from threshold 0.0 through
0.94, then falling off a cliff at 0.97. That table is why the harness
treats threshold choice as a measured decision: near the cliff, a small
move swings coverage from 0.54 to 0.14.

**4. Apply the gate.** `python evals/run_day4.py` regenerates the Day 4
results. Open `evals/quality_coverage_results.md`: with the gate open,
all 54 answered cases are auto-accepted at a mean F1 of 0.4408, under
the 0.45 quality floor, so that build configuration is rejected. At
gate 0.35, 42 cases auto-accept at F1 0.4747 and 12 go to a reviewer:
the floor clears, and `evals/cost_routing_results.md` prices it at
$2.7340 per case, the cheapest passing configuration. Push the gate to
0.80 and only 1 case ships without review: quality 0.8462, coverage
0.01, and a cost of $3.1030 per case, because nearly everything now
pays reviewer or handoff prices. Same agent, three gates, three
different ship decisions. That is the demo.

**5. Check the human bill.** `evals/reviewer_effort_results.md` shows
what the chosen gate asks of people: 429 minutes per 100 cases instead
of 800 fully manual, a 46.4 percent saving, with the audit and review
load itemized rather than hidden.

## Tests

```bash
pytest -q
```

Current state: 25 passing, covering the metrics math, the CLI report
shape, the gate curve, the cost branches, and the effort accounting.

## Roadmap

Week 3 is complete.

- Day 1: harness, metrics, 5-case golden set (done).
- Day 2: golden set of 40, failure demos, regression gate concept
  (done).
- Day 3: golden set of 100, recall@5, threshold operating-point sweep
  (done).
- Day 4: quality-vs-coverage curve, cost-aware acceptance gate,
  reviewer-effort measurement (done).
- Day 5: this final README, with the automation policy and demo story
  written out (done).

Possible future work, none of it scheduled: a held-out golden set split
so gate numbers can be reported on unseen cases, a model-as-grader
quality score alongside token F1, and gate runs against a live agent
build as part of a release checklist.
