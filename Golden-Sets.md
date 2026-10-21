# Golden Sets

How the evaluation sets are built, labeled, and kept honest.

## helpdesk_v1 (current: v3, 100 tickets)

Built for the StyleDesk fictional B2B SaaS helpdesk. Ticket families:

- **How-tos** (answerable): documented product questions with a clear article.
- **Billing-policy** (answerable only from policy text): the answer must come from the policy article, not general knowledge.
- **Bug incidents** (expect handoff): need reproduction details and human routing.
- **Account actions** (expect human review): charges, refunds, access changes need records or authorization.
- **Prompt injections** (expect escalate): 8 attempts with instruction-override patterns.
- **Missing documentation** (expect handoff with reason): 7 tickets no article covers.
- **Contradictory policy** (expect handoff): 3 cases where two articles disagree.
- **Unanswerable** (expect handoff): gibberish and vague tickets with no retrievable evidence.

Day 3 (v3) totals: 100 tickets, 54 answered, 38 handoff, 8 escalate. Hard cases (missing documentation, contradictory policy, unanswerable) are 13 of 100. Label maintenance is recorded in ticket notes; Day 3 examples: T-1021 evidence corrected from h8 to a8, and four borderline tickets had their text strengthened after landing below the confidence gate, labels unchanged.

## Labeling rules

- Every ticket has an expected action, expected evidence (article ids), and notes.
- Labels are human-reviewed. Ticket text is never generated directly from its answer paragraph.
- When the automation policy changes, labels change with it and the change is recorded (example: T-1005 moved from answered to handoff on Day 2, with the reason written down).

## Development vs held-out

Planned, not yet done: split tickets into scenario families, keep one family fully held out, and report recall and accuracy on it separately. The held-out set is the honest number. Day 3 grew the set to 100 and measured recall@5 and the threshold sweep on the full development set; the family split is still open.

## Regression gate

Before a model, prompt, or threshold change ships, the full golden set runs against the new version and the old one. A change that drops action accuracy or recall does not ship. The gate is the point of the whole harness.
