# AgentEval

Eval + cost harness for LLM agents: accuracy, cost per run, latency, token
usage, and a regression gate. Built to score the Week 3 helpdesk agent, but
works against any agent through the small agent interface in `eval.py`.

## Day 1 scope

- `eval.py`: CLI harness. Loads a golden set, calls an agent, computes
  metrics, emits a JSON report.
- `metrics.py`: answer quality (token F1 against expected keywords, action
  accuracy), mock token pricing (input $0.15/1M, output $0.60/1M), latency
  p50/p99, token counts, cost per ticket.
- `golden_sets/helpdesk_v1.json`: 5 golden StyleDesk helpdesk tickets.
- `FakeAgent`: deterministic mock so the harness runs end to end with no
  services up. `HttpAgent` plugs in the real helpdesk API later.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
python eval.py                                   # baseline run, prints report
python eval.py --out report.json                 # also save the report
python eval.py --agent http://localhost:8000     # score the real helpdesk API
```

## Tests

```bash
pytest -q
```

## Roadmap

Day 2: golden set of ~30 tickets + regression gate. Day 3: first full eval
report on the helpdesk agent. Day 4: cost-aware routing analysis. Day 5:
full README + demo story.
