# AgentEval

Eval + cost harness for LLM agents: accuracy, cost per run, latency, token
usage, retrieval recall, and a regression gate. Works against any agent
through the small agent interface in `eval.py`.

## What is here

- `eval.py`: CLI harness. Loads a golden set, calls an agent, computes
  metrics, emits a JSON report.
- `metrics.py`: answer quality (token F1 against expected keywords, action
  accuracy), retrieval recall@k, mock token pricing (input $0.15/1M,
  output $0.60/1M), latency p50/p99, token counts, cost per ticket.
- `golden_sets/helpdesk_v1.json`: golden set, currently v3 with 100
  StyleDesk tickets (how-tos, billing-policy questions, bug incidents,
  account actions, billing disputes, prompt injections, missing
  documentation, contradictory policy, vague and gibberish tickets).
  Every ticket carries an expected action, expected evidence, and notes.
- `FakeAgent`: deterministic mock with canned answers for all 100 golden
  tickets, so the harness runs end to end with no services up.
  `HttpAgent` scores a live agent API and passes its retrieved evidence
  through for recall scoring.
- `evals/verify_golden.py`: dev tool that checks golden routing against
  the live pipeline (100/100 match).
- `evals/threshold_sweep.py`: sweeps the pipeline confidence threshold
  over the golden set and reports coverage, action accuracy, answered
  precision, and escalation recall per threshold, plus recall@5.
  Results land in `evals/threshold_sweep_results.json` and
  `evals/threshold_sweep_results.md`.
- `evals/failure_demos.py`: six failure and recovery scenarios with a
  pass/fail report.
- `evals/run_day4.py`: Day 4 analyses (quality-vs-coverage curve,
  cost-aware acceptance gate, reviewer-effort measurement) over the
  harness's scored output, in `evals/quality_coverage.py`,
  `evals/cost_routing.py`, and `evals/reviewer_effort.py`. Results land
  in `evals/quality_coverage_results.*`, `evals/cost_routing_results.*`,
  and `evals/reviewer_effort_results.*`.

## Day 3 results

- Golden set v3: 100 tickets (54 answered, 38 handoff, 8 escalate).
  Hard cases (missing documentation, contradictory policy, unanswerable)
  are 13 of 100. One label fix: T-1021 expected evidence corrected from
  h8 to a8, the workspace-profile article id in the KB.
- Retrieval recall@5: mean 1.0000 over the 81 evidence-bearing tickets,
  full-hit rate 1.0000. The golden tickets paraphrase the documented
  vocabulary, so read this as an in-vocabulary result.
- Threshold sweep: action accuracy and answered precision stay at
  1.0000 from threshold 0.0 through 0.94 at coverage 0.54, then fall off
  a cliff at 0.97 (coverage 0.14, accuracy 0.6000). The confidence score
  is a normalized BM25 score, not a calibrated probability; the sweep
  is an operating-point analysis, not a calibration measurement.
- FakeAgent baseline over 100 tickets: action accuracy 1.0, mean answer
  F1 0.238, cost per ticket about $0.00001 at mock prices.
- 18 tests passing.

## Day 4 results

Run with `python evals/run_day4.py`. The analysis gates auto-acceptance
of an answered result on its measured answer-quality score (token F1);
offline the score is exact, and a live agent would expose a runtime
proxy for it.

- Quality-vs-coverage curve: with the gate open, coverage is 0.54 at a
  mean accepted F1 of 0.4408. Raising the gate trades coverage for
  accepted quality smoothly: gate 0.35 ships 0.42 coverage at F1 0.4747,
  gate 0.50 ships 0.12 at F1 0.6023, gate 0.80 ships 0.01 at F1 0.8462.
  Accepted action accuracy is 1.0000 at every gate on this baseline:
  the mock agent never misroutes, so the gate trades answer quality,
  not routing errors.
- Cost-aware routing: outcomes are priced in dollars (spot audit of an
  accepted answer $0.30, reviewer decision $1.20, handoff $4.80,
  escalation $8.00, wrong auto-accept penalty $6.00, plus the measured
  inference cost). The cheapest gate whose accepted work clears the
  quality floor (mean accepted F1 at or above 0.45) is 0.35, at an
  expected $2.7340 per ticket. The gate just below it (0.30) misses the
  floor at F1 0.4444.
- Reviewer effort: at gate 0.35 the 100 golden tickets take 429 human
  minutes (42 auto-accepted audits, 12 reviewer decisions, 38 handoffs,
  8 escalations) against a fully manual baseline of 800 minutes, a
  46.4 percent saving. Estimates under the stated minute assumptions,
  not a time study.
- 25 tests passing (7 new Day 4 tests cover the curve math, the cost
  branches, and the effort accounting).

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python eval.py                                   # baseline run, prints report
python eval.py --out report.json                 # also save the report
python eval.py --agent http://localhost:8000     # score a live agent API
python evals/threshold_sweep.py                  # threshold + recall@5 report
```

## Tests

```bash
pytest -q
```

## Roadmap

Day 1: harness, metrics, 5-ticket golden set. Day 2: golden set of 40,
failure demos, regression gate. Day 3: golden set of 100, recall@5,
threshold operating-point sweep. Day 4: quality-vs-coverage curve,
cost-aware acceptance gate, reviewer-effort measurement (done).
Day 5: full README + demo story.
