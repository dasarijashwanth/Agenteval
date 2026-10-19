"""AgentEval Day 1: eval + cost harness for LLM agents.

Runs a golden set against an agent, computes answer quality, cost,
latency, and token metrics, and emits a JSON report. Day 1 ships with a
FakeAgent so the harness runs end to end with no services up and no API
keys. A HttpAgent stub shows how the real helpdesk API plugs in later.

Usage:
    python eval.py                                   # baseline run, prints report
    python eval.py --golden golden_sets/helpdesk_v1.json --out report.json
    python eval.py --agent http://localhost:8000    # real helpdesk API
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import httpx

from metrics import (
    action_match,
    cost_usd,
    estimate_tokens,
    summarize,
    token_f1,
)

DEFAULT_GOLDEN = Path(__file__).parent / "golden_sets" / "helpdesk_v1.json"


class FakeAgent:
    """Deterministic mock agent: canned answers, zero network."""

    _ANSWERS = {
        "T-1001": (
            "Go to Settings, Billing, Payment method and click Replace card. "
            "We accept Visa, Mastercard, and American Express.",
            "answered",
        ),
        "T-1002": (
            "Click Forgot password on the sign-in page. The reset link expires "
            "after 24 hours, so check spam if it has not arrived.",
            "answered",
        ),
        "T-1003": (
            "Attachments are limited to 25 MB per file. Allowed types include "
            "PDF, PNG, JPG, DOCX, XLSX, CSV, and TXT.",
            "answered",
        ),
        "T-1004": ("", "handoff"),
        "T-1005": (
            "Refunds are available within 14 days of a charge for monthly "
            "plans. Write to billing with the invoice number.",
            "answered",
        ),
    }

    def answer(self, ticket_id: str, subject: str, body: str) -> dict:
        text, action = self._ANSWERS.get(ticket_id, ("", "handoff"))
        return {"answer": text, "action": action}


class HttpAgent:
    """Calls the real helpdesk-agent FastAPI service."""

    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        # trust_env=False: ignore proxy env vars (some runtimes ship a
        # no_proxy value that older httpx versions cannot parse).
        self._client = httpx.Client(trust_env=False)

    def answer(self, ticket_id: str, subject: str, body: str) -> dict:
        resp = self._client.post(
            f"{self.base_url}/tickets/answer",
            json={"ticket_id": ticket_id, "subject": subject, "body": body},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"answer": data.get("answer", ""), "action": data.get("action", "handoff")}


def run_eval(agent, golden: list[dict]) -> dict:
    items = []
    for ticket in golden:
        subject = ticket["ticket_subject"]
        body = ticket["body"]
        start = time.perf_counter()
        result = agent.answer(ticket["ticket_id"], subject, body)
        latency = time.perf_counter() - start

        answer_text = result.get("answer", "")
        action = result.get("action", "handoff")
        input_tokens = estimate_tokens(subject + " " + body)
        output_tokens = estimate_tokens(answer_text)

        items.append({
            "ticket_id": ticket["ticket_id"],
            "action": action,
            "action_correct": action_match(ticket["expected_action"], action),
            "answer_f1": round(token_f1(ticket["expected_answer_keywords"], answer_text), 4),
            "latency_s": round(latency, 4),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd(input_tokens, output_tokens), 8),
        })
    return {"summary": summarize(items), "items": items}


def main() -> None:
    parser = argparse.ArgumentParser(description="AgentEval: eval + cost harness")
    parser.add_argument("--agent", default="fake",
                        help="'fake' for the mock agent or a base URL like http://localhost:8000")
    parser.add_argument("--golden", default=str(DEFAULT_GOLDEN),
                        help="path to golden set JSON")
    parser.add_argument("--out", default=None, help="write JSON report to this path")
    args = parser.parse_args()

    with open(args.golden, encoding="utf-8") as f:
        golden = json.load(f)["items"]

    agent = HttpAgent(args.agent) if args.agent != "fake" else FakeAgent()
    report = run_eval(agent, golden)

    text = json.dumps(report, indent=2)
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"Wrote report to {args.out}")
    print(text)


if __name__ == "__main__":
    main()
