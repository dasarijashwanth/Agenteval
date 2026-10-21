# Threshold sweep results (Day 3)

Golden set: helpdesk_v3, 100 tickets. The pipeline confidence is a
normalized BM25 score, not a calibrated probability, so this table is
an operating-point analysis: it shows what each threshold buys and
what it costs. It is not a calibration measurement.

## Retrieval recall@5 (threshold independent)

- Mean recall@5 over 81 evidence-bearing tickets: **1.0**
- Full-hit rate (all expected evidence inside the top 5): **1.0**

## Operating points

| Threshold | Coverage (answered) | Action accuracy | Answered precision | Escalate recall |
|---|---|---|---|---|
| 0.00 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.20 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.35 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.50 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.60 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.70 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.80 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.85 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.90 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.94 | 0.5400 | 1.0000 | 1.0000 | 1.0000 |
| 0.97 | 0.1400 | 0.6000 | 1.0000 | 1.0000 |
| 0.99 | 0.0000 | 0.4600 | n/a | 1.0000 |

## Reading the table

- At the Day 2 threshold of 0.35: coverage 0.54, action accuracy 1.0000, answered precision 1.0000.
- At 0.94 (the operating point the pipeline currently ships): coverage 0.54, action accuracy 1.0000, answered precision 1.0000. On this golden set the two operating points land on the same plateau: identical routing, so the choice between them is about headroom against future, harder tickets, not about today's numbers.
- The plateau ends in a cliff: at 0.97 coverage falls to 0.14 and action accuracy to 0.6000. Answered-ticket confidence is clustered in a narrow band, so a small threshold move near the cliff swings coverage a lot. That clustering is a property of the normalized score, and one more reason not to read it as a probability.
- Answered precision is 1.0000 at every threshold on this set: the guardrails and the evidence-overlap gate reject bad retrievals before the confidence gate is the deciding factor. What the threshold trades on this data is coverage, not wrong answers.
- Escalation recall stays at 1.0000 at every threshold: injection detection runs before the confidence gate, so the gate never trades away safety.
- A threshold cannot fix retrieval. Where recall@5 misses, the evidence was never in the candidate set, and no operating point answers those tickets correctly. On this set recall@5 has no misses; the golden tickets paraphrase the documented vocabulary, so treat the perfect score as an in-vocabulary result, not a promise about unseen phrasings.

Regenerate with: `python evals/threshold_sweep.py`
