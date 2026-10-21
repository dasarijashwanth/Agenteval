# AgentEval

The evaluation harness for AI agents. Built as Week 3 of a weekly portfolio project series by [Jashwanth Dasari](https://github.com/dasarijashwanth), alongside the helpdesk agent it evaluates.

## Current status

**Day 3 complete** (2026-10-21). See [[Progress]] for the dated log.

- CLI runner (`eval.py`) with two agent types: FakeAgent (deterministic mock) and HttpAgent (scores any live HTTP agent API and passes retrieved evidence through for recall scoring).
- Metrics (`metrics.py`): token F1, action accuracy, retrieval recall@5, mock pricing ($0.15/1M input, $0.60/1M output tokens), latency p50/p99, cost per ticket.
- Golden set `helpdesk_v1.json`: 100 tickets (v3), covering how-tos, billing-policy questions, bug incidents, account actions, billing disputes, 8 prompt injections, 7 missing-doc cases, 3 contradictory-policy cases, and unanswerable tickets. Each ticket has an expected action, expected evidence, and notes.
- Threshold sweep (`evals/threshold_sweep.py`): operating-point table over the golden set, with results saved as JSON and Markdown.
- Failure demos (`evals/failure_demos.py`): 6 automated scenarios with pass/fail report.
- Regression gate: golden routing must match expected actions before a model or prompt change ships.

## Key numbers (Day 3)

- 18/18 tests passing.
- 100/100 golden tickets route as expected against the live pipeline.
- Retrieval recall@5: mean 1.0000 over 81 evidence-bearing tickets (in-vocabulary caveat applies).
- Threshold sweep: accuracy and answered precision 1.0000 from 0.0 through 0.94 at coverage 0.54; cliff at 0.97.

## Links

- [[Roadmap]] - what is planned for each day
- [[Progress]] - dated build log
- [[Metrics]] - what each metric means and why it matters
- [[Golden Sets]] - how the golden sets are built and labeled
