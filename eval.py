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
        # Day 2: account-specific charge disputes need billing records.
        "T-1005": ("", "handoff"),
        "T-1006": (
            "Go to Settings, Security and turn on two-factor authentication. "
            "Scan the QR code with your authenticator app and save the backup "
            "codes.",
            "answered",
        ),
        "T-1007": (
            "Open Apps, Slack and click Connect. Approve the OAuth scopes and "
            "choose the channel for ticket alerts.",
            "answered",
        ),
        "T-1008": (
            "Go to Queues, New queue, name it, assign agents and set the "
            "default priority.",
            "answered",
        ),
        "T-1009": (
            "Go to Reports, Custom and pick metrics like tickets solved. Add "
            "a weekly schedule and the PDF is emailed every Monday.",
            "answered",
        ),
        "T-1010": (
            "Create canned responses under Settings, Canned responses and "
            "insert one with the # shortcut while typing.",
            "answered",
        ),
        "T-1011": (
            "Set business hours under Queues, Settings, Business hours and add "
            "holiday exceptions so SLAs pause correctly.",
            "answered",
        ),
        "T-1012": (
            "Select the tickets, click Merge and choose which ticket survives. "
            "All replies and history move to the surviving ticket.",
            "answered",
        ),
        "T-1013": (
            "Open Automations, New rule, choose the Ticket created trigger and "
            "add the Send auto-reply action.",
            "answered",
        ),
        "T-1014": (
            "StyleDesk bills you monthly on the anniversary of your signup "
            "date, and the invoice is emailed on each billing date.",
            "answered",
        ),
        "T-1015": (
            "Annual plans cost 20 percent less than paying monthly. The full "
            "year is charged up front.",
            "answered",
        ),
        "T-1016": (
            "Add your tax ID under Settings, Billing, Tax details and it "
            "appears on every invoice.",
            "answered",
        ),
        "T-1017": (
            "Open Settings, Billing, Invoices to download a PDF receipt for "
            "any invoice.",
            "answered",
        ),
        "T-1018": (
            "A failed charge is retried on day 3 and day 7. Update the card "
            "before the third retry fails or the workspace is paused.",
            "answered",
        ),
        "T-1019": (
            "Upgrades take effect immediately and are prorated. Downgrades "
            "take effect at the end of the current cycle.",
            "answered",
        ),
        "T-1020": (
            "Admins can invite people from Admin, Team, Invite and assign a "
            "role: viewer, agent, or admin.",
            "answered",
        ),
        "T-1021": (
            "Admins can edit the workspace name and timezone under Admin, "
            "Workspace.",
            "answered",
        ),
        "T-1022": ("", "handoff"),
        "T-1023": ("", "handoff"),
        "T-1024": ("", "handoff"),
        "T-1025": ("", "handoff"),
        "T-1026": ("", "handoff"),
        "T-1027": ("", "handoff"),
        "T-1028": ("", "handoff"),
        "T-1029": ("", "handoff"),
        "T-1030": ("", "handoff"),
        "T-1031": ("", "escalate"),
        "T-1032": ("", "escalate"),
        "T-1033": ("", "escalate"),
        "T-1034": ("", "handoff"),
        "T-1035": ("", "handoff"),
        "T-1036": ("", "handoff"),
        "T-1037": (
            "Export your tickets from Settings, Data, Export first. Account "
            "deletion is permanent after a 30-day grace period.",
            "answered",
        ),
        "T-1038": (
            "Attachments are limited to 25 MB per file. Allowed types include "
            "PDF, PNG, JPG, DOCX, XLSX, CSV, and TXT.",
            "answered",
        ),
        "T-1039": ("", "handoff"),
        "T-1040": (
            "Open Settings, Profile and enter the new email address. Click "
            "the verification link sent to the new address.",
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
