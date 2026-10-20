"""Verify pipeline routing against the golden set expectations (dev tool)."""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "week-03-helpdesk-agent"))

from app.answer import pipeline_ticket
from app.kb import KnowledgeBase

AGENT_DIR = Path(__file__).resolve().parent.parent.parent / "week-03-helpdesk-agent"
EVAL_DIR = Path(__file__).resolve().parent.parent


def main() -> int:
    kb = KnowledgeBase.load()
    whitelist = json.loads((AGENT_DIR / "data" / "auto_whitelist.json").read_text())
    golden = json.loads((EVAL_DIR / "golden_sets" / "helpdesk_v1.json").read_text())["items"]

    failures = []
    for ticket in golden:
        result = pipeline_ticket(
            kb, ticket["ticket_subject"], ticket["body"], whitelist=whitelist
        )
        expected = ticket["expected_action"]
        ok = result["action"] == expected
        flag = "OK  " if ok else "FAIL"
        print(f"{flag} {ticket['ticket_id']}: expected={expected} got={result['action']}"
              f" reason={result['routing_reason']} conf={result['confidence']}"
              f" top={[r['article_id'] for r in result['retrieved']][:2]}")
        if not ok:
            failures.append(ticket["ticket_id"])
    print(f"\n{len(golden) - len(failures)}/{len(golden)} match")
    if failures:
        print("mismatches:", failures)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
