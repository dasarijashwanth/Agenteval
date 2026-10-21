"""AgentEval: eval + cost harness for LLM agents.

Runs a golden set against an agent, computes answer quality, cost,
latency, and token metrics, and emits a JSON report. Ships with a
FakeAgent so the harness runs end to end with no services up and no API
keys. A HttpAgent plugs in a live agent API. Day 3: when an agent result
includes retrieved evidence, each item also scores recall@5 against the
ticket's expected evidence, and the summary reports mean recall@5.

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
    recall_at_k,
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
        "T-1041": (
            "StyleDesk bills monthly on the anniversary of your signup date. "
            "Under Settings, Billing, Upcoming invoice you can see the plan, seat "
            "count, and any usage overage before the billing date.",
            "answered",
        ),
        "T-1042": (
            "We accept Visa, Mastercard, and American Express. Go to Settings, "
            "Billing, Payment method and click Replace card to update the card on "
            "file.",
            "answered",
        ),
        "T-1043": (
            "If your card is declined we retry the charge automatically on day 3 "
            "and day 7 and email you each time. Update the card before the third "
            "retry fails or your workspace is paused.",
            "answered",
        ),
        "T-1044": (
            "Refunds are available within 14 days of a charge for monthly plans. "
            "Refunds go back to the original card within 5 to 10 business days.",
            "answered",
        ),
        "T-1045": (
            "Open Settings, Billing, Invoices and set a billing email so finance "
            "gets copies of every receipt automatically.",
            "answered",
        ),
        "T-1046": (
            "Upgrades take effect immediately and are prorated for the rest of "
            "the cycle.",
            "answered",
        ),
        "T-1047": (
            "Annual plans cost 20 percent less than paying monthly. The full year "
            "is charged up front and is refundable within the first 30 days.",
            "answered",
        ),
        "T-1048": (
            "Add your tax ID under Settings, Billing, Tax details and it appears "
            "on every invoice. Tax-exempt organizations can upload a certificate "
            "for review.",
            "answered",
        ),
        "T-1049": (
            "Click Forgot password on the sign-in page and enter your work email. "
            "The reset link expires after 24 hours and can be used once, so check "
            "spam if it has not arrived.",
            "answered",
        ),
        "T-1050": (
            "Go to Settings, Security and turn on two-factor authentication. Scan "
            "the QR code with any authenticator app and save the backup codes "
            "somewhere safe.",
            "answered",
        ),
        "T-1051": (
            "Open Settings, Profile and enter the new email address. We send a "
            "verification link to the new address and the change completes after "
            "you click it.",
            "answered",
        ),
        "T-1052": (
            "Admins invite people from Admin, Team, Invite and assign a role. "
            "Invites expire after 7 days and can be resent from the same page.",
            "answered",
        ),
        "T-1053": (
            "Go to Admin, Team, click the member and choose Remove. Their open "
            "tickets are reassigned to the queue owner and their replies stay in "
            "ticket history.",
            "answered",
        ),
        "T-1054": (
            "Account deletion is permanent after a 30-day grace period. During "
            "the grace period you can sign in to cancel the deletion and restore "
            "everything.",
            "answered",
        ),
        "T-1055": (
            "If Okta sign-in fails, confirm with your IT admin that the StyleDesk "
            "app is assigned to you. SSO logins use your work email exactly as "
            "provisioned; personal Gmail addresses will not match.",
            "answered",
        ),
        "T-1056": (
            "Admins can edit the workspace name, timezone, and logo under Admin, "
            "Workspace.",
            "answered",
        ),
        "T-1057": (
            "If the dashboard shows a blank page, hard-refresh with Ctrl Shift R. "
            "If only your account is affected, clearing site data for the site "
            "usually fixes it.",
            "answered",
        ),
        "T-1058": (
            "Check your notification settings under Profile, Notifications and "
            "confirm the channel is enabled. Email alerts can land in spam, so "
            "add the sender to your allowlist.",
            "answered",
        ),
        "T-1059": (
            "Search indexes new tickets within about 15 minutes, so very new "
            "tickets may not appear yet. Try fewer keywords or clear your "
            "filters; an admin can trigger a reindex from Admin, Search.",
            "answered",
        ),
        "T-1060": (
            "Queues with more than 10,000 open tickets load slowly. Archive "
            "resolved tickets and use saved filters to narrow the view. The bulk "
            "archive tool handles 500 tickets at a time.",
            "answered",
        ),
        "T-1061": (
            "Update the app to version 4.2 or newer, which fixed a login crash on "
            "both iOS and Android. If it still crashes, uninstall and reinstall "
            "the app.",
            "answered",
        ),
        "T-1062": (
            "Go to Queues, New queue and name it for the team. Assign agents and "
            "set the default priority. New tickets route to the queue whose rules "
            "match first.",
            "answered",
        ),
        "T-1063": (
            "Open Automations, New rule and choose the trigger Ticket created. "
            "Limit one auto-reply per ticket to avoid loops.",
            "answered",
        ),
        "T-1064": (
            "Create canned responses under Settings, Canned responses and insert "
            "one with the # shortcut while typing a reply.",
            "answered",
        ),
        "T-1065": (
            "Go to Reports, Custom and pick metrics like tickets solved, median "
            "first response, and CSAT. Add a weekly schedule and the PDF is "
            "emailed every Monday.",
            "answered",
        ),
        "T-1066": (
            "Open Apps, Slack and click Connect. You can create tickets from "
            "Slack with the /styledesk command and get notified on replies.",
            "answered",
        ),
        "T-1067": (
            "Tickets arriving outside hours follow the after-hours automation you "
            "configure. Set each queue schedule under Queues, Settings, Business "
            "hours.",
            "answered",
        ),
        "T-1068": (
            "Select the tickets, click Merge and choose which ticket survives. "
            "All replies, attachments, and history move to the surviving ticket, "
            "and merged tickets keep the oldest creation date for SLA math.",
            "answered",
        ),
        "T-1069": (
            "You can view upcoming charges under Settings, Billing, Upcoming "
            "invoice. Your invoice is emailed on each billing date.",
            "answered",
        ),
        "T-1070": (
            "Attachments are limited to 25 MB per file. If a valid file still "
            "fails, try renaming it without special characters and upload again.",
            "answered",
        ),
        "T-1071": (
            "Go to Reports, Custom and pick metrics like tickets solved. Add a "
            "weekly schedule and the weekly report PDF is emailed every Monday.",
            "answered",
        ),
        "T-1072": (
            "Downgrades take effect at the end of the current cycle so you keep "
            "what you paid for.",
            "answered",
        ),
        "T-1073": ("", "handoff"),
        "T-1074": ("", "handoff"),
        "T-1075": ("", "handoff"),
        "T-1076": ("", "handoff"),
        "T-1077": ("", "handoff"),
        "T-1078": ("", "handoff"),
        "T-1079": ("", "handoff"),
        "T-1080": ("", "handoff"),
        "T-1081": ("", "handoff"),
        "T-1082": ("", "handoff"),
        "T-1083": ("", "handoff"),
        "T-1084": ("", "handoff"),
        "T-1085": ("", "handoff"),
        "T-1086": ("", "handoff"),
        "T-1087": ("", "handoff"),
        "T-1088": ("", "handoff"),
        "T-1089": ("", "handoff"),
        "T-1090": ("", "handoff"),
        "T-1091": ("", "handoff"),
        "T-1092": ("", "handoff"),
        "T-1093": ("", "handoff"),
        "T-1094": ("", "handoff"),
        "T-1095": ("", "handoff"),
        "T-1096": ("", "escalate"),
        "T-1097": ("", "escalate"),
        "T-1098": ("", "escalate"),
        "T-1099": ("", "escalate"),
        "T-1100": ("", "escalate"),
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
        return {
            "answer": data.get("answer", ""),
            "action": data.get("action", "handoff"),
            "retrieved": data.get("retrieved", []),
        }


def retrieved_ids(result: dict) -> list[str] | None:
    """Normalize an agent result's retrieved evidence to a list of ids.

    Agents may return article ids as plain strings or as dicts with an
    "article_id" key. Returns None when the agent reports no retrieval,
    so recall is only scored for agents that expose their evidence.
    """
    retrieved = result.get("retrieved")
    if not retrieved:
        return None
    ids = []
    for entry in retrieved:
        if isinstance(entry, dict):
            ids.append(str(entry.get("article_id", "")))
        else:
            ids.append(str(entry))
    ids = [i for i in ids if i]
    return ids or None


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

        item = {
            "ticket_id": ticket["ticket_id"],
            "action": action,
            "action_correct": action_match(ticket["expected_action"], action),
            "answer_f1": round(token_f1(ticket["expected_answer_keywords"], answer_text), 4),
            "latency_s": round(latency, 4),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost_usd": round(cost_usd(input_tokens, output_tokens), 8),
        }
        # Day 3: retrieval recall@5 when the agent exposes its evidence.
        ids = retrieved_ids(result)
        if ids is not None:
            item["retrieved_top5"] = ids[:5]
            recall = recall_at_k(ticket.get("expected_evidence", []), ids, k=5)
            if recall is not None:
                item["recall_at_5"] = round(recall, 4)
        items.append(item)
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
