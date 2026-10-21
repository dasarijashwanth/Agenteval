# Roadmap

Week 3 plan for AgentEval, paired with the helpdesk agent it evaluates.

## Day 1 (done 2026-10-19)

- `eval.py` CLI with FakeAgent and HttpAgent.
- `metrics.py`: token F1, action accuracy, latency p50/p99, mock cost model.
- Golden set v1: 5 tickets. Baseline: FakeAgent action_accuracy 1.0, mean F1 0.337.
- Wired to the live helpdesk API: action_accuracy 1.0.

## Day 2 (done 2026-10-19)

- Golden set v2: 40 tickets with expected actions, expected evidence, and notes.
- `evals/failure_demos.py`: 6 failure scenarios against the live server, all passing.
- Regression gate concept in place: golden routing compared before and after changes.

## Day 3 (done 2026-10-21)

- Golden set v3: 100 tickets, human-reviewed labels, hard cases at 13 of 100.
- Retrieval recall@5 measured on the golden set: mean 1.0000 over 81 evidence-bearing tickets.
- Threshold operating-point sweep (`evals/threshold_sweep.py`): plateau through 0.94, cliff at 0.97.
- Still open from the original sketch: separate development and held-out scenario families, with recall reported on the held-out family.

## Day 4 (next)

- Quality-vs-coverage curve support: score the helpdesk at multiple confidence thresholds.
- Cost tracking per ticket: tokens, latency, and reviewer time side by side.
- Model-as-grader experiment on a sample, checked against human review.

## Day 5 (next)

- Final eval report with counts and percentages, baselines included.
- README with the full methodology.
