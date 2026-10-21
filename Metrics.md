# Metrics

What AgentEval measures, and why each one matters for the helpdesk story.

## Action accuracy

The fraction of golden tickets where the agent's action (answer, handoff, escalate) matches the expected action. This is the primary metric: for a helpdesk, choosing the right action matters more than wording the answer well. A correct handoff beats a confident wrong answer.

## Token F1

Overlap between the agent's answer and the reference answer, measured on tokens. Useful for answer quality, but extractive answers dilute keyword precision, so it is reported alongside action accuracy, never alone. Day 2 live result: mean F1 0.1111 with action_accuracy 1.0, which is expected for extractive answers.

## Latency p50/p99

Median and 99th-percentile response time per ticket. Day 1 live result: p50 0.0024s. Reported per run so regressions in speed are visible.

## Cost per ticket

Mock pricing model: $0.15 per 1M input tokens, $0.60 per 1M output tokens. Day 1 baseline: $0.000013 per ticket. The point is the shape of the accounting, not the absolute number: every eval run reports accuracy and cost side by side, so a "better" model that costs 50x more has to justify itself.

## Retrieval recall@5 (Day 3, measured)

The fraction of expected evidence that appears in the top 5 retrieved articles, averaged over evidence-bearing tickets. Measured on golden set v3: mean recall@5 1.0000 over 81 evidence-bearing tickets, full-hit rate 1.0000. Caveat: the golden tickets paraphrase the documented vocabulary, so this is an in-vocabulary result. The held-out family split that would make this the honest generalization number is still planned. Recall separates retrieval failures from generation failures: a ticket can only be answered well if its evidence was retrieved first.

## Threshold operating points (Day 3)

`evals/threshold_sweep.py` sweeps the pipeline confidence threshold and reports coverage, action accuracy, answered precision, and escalation recall per threshold. On golden set v3, accuracy and answered precision hold at 1.0000 from 0.0 through 0.94 at coverage 0.54, then fall off a cliff at 0.97 (coverage 0.14). The confidence is a normalized BM25 score, not a calibrated probability, so the sweep is an operating-point analysis: it prices each threshold in coverage, it does not estimate the chance that an answer is right.

## What is not measured yet

Human-judged answer quality on a sample (Day 4 experiment), reviewer time saved (Day 4), and probability calibration of the confidence score (would need labeled outcome data and a method like Platt scaling or isotonic regression; the Day 3 sweep deliberately does not claim it).
