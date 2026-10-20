"""TriageBot: an agent that classifies, prioritizes and drafts replies for support emails.

Pipeline (each step is a small, testable function):
  1. classify()  -> category (bug, billing, feature_request, account, spam, other)
  2. prioritize() -> priority (urgent, high, normal, low)
  3. draft_reply() -> a reply a human can approve or edit
  4. triage()    -> runs all steps on one email and returns a ticket

Works offline with rule-based logic. If ANTHROPIC_API_KEY is set and the
`anthropic` package is installed, the reply drafting step uses an LLM instead.
"""
import argparse
import json
import os
import sys

CATEGORY_KEYWORDS = {
    "spam": ["win a prize", "free money", "click here now", "limited offer", "crypto giveaway"],
    "billing": ["invoice", "refund", "charged", "payment", "billing", "subscription", "receipt"],
    "bug": ["error", "crash", "bug", "broken", "not working", "doesn't work", "fails", "exception"],
    "account": ["password", "login", "log in", "locked out", "sign in", "account", "2fa"],
    "feature_request": ["feature", "would be great", "please add", "wish", "suggestion", "support for"],
}

# Order matters: spam is checked first, then the rest by specificity.
CATEGORY_ORDER = ["spam", "billing", "bug", "account", "feature_request"]

URGENT_WORDS = ["urgent", "asap", "immediately", "outage", "down", "data loss", "security", "charged twice"]
HIGH_WORDS = ["cannot", "can't", "unable", "blocked", "deadline", "crash", "locked out"]

REPLY_TEMPLATES = {
    "bug": "Hi {name},\n\nThanks for reporting this, and sorry for the trouble. I've logged it with our engineering team. Could you share your device/browser and the steps that led to the problem so we can reproduce it?\n\nBest,\nSupport Team",
    "billing": "Hi {name},\n\nThanks for reaching out about your billing question. I'm checking your account and will confirm the details shortly. If a refund is due, we'll process it right away.\n\nBest,\nSupport Team",
    "account": "Hi {name},\n\nSorry you're having trouble with your account. For security, please use the 'Forgot password' link on the login page. If that doesn't work, reply here and we'll verify your identity and help you get back in.\n\nBest,\nSupport Team",
    "feature_request": "Hi {name},\n\nThanks for the suggestion! I've passed it to our product team. We can't promise a timeline, but requests like yours directly shape our roadmap.\n\nBest,\nSupport Team",
    "other": "Hi {name},\n\nThanks for contacting us. I'm looking into this and will get back to you shortly.\n\nBest,\nSupport Team",
}


def classify(subject: str, body: str) -> str:
    text = f"{subject} {body}".lower()
    for category in CATEGORY_ORDER:
        if any(k in text for k in CATEGORY_KEYWORDS[category]):
            return category
    return "other"


def prioritize(subject: str, body: str, category: str) -> str:
    if category == "spam":
        return "low"
    text = f"{subject} {body}".lower()
    if any(w in text for w in URGENT_WORDS):
        return "urgent"
    if any(w in text for w in HIGH_WORDS):
        return "high"
    if category == "feature_request":
        return "low"
    return "normal"


def _llm_reply(name: str, subject: str, body: str, category: str):
    """Optional LLM drafting. Returns None if unavailable so we fall back to templates."""
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return None
    try:
        import anthropic  # type: ignore

        client = anthropic.Anthropic()
        msg = client.messages.create(
            model=os.environ.get("TRIAGEBOT_MODEL", "claude-sonnet-4-5"),
            max_tokens=400,
            messages=[{
                "role": "user",
                "content": (
                    f"Draft a short, friendly support reply to {name}. Category: {category}.\n"
                    f"Subject: {subject}\nMessage: {body}\nSign off as 'Support Team'."
                ),
            }],
        )
        return msg.content[0].text
    except Exception:
        return None


def draft_reply(name: str, subject: str, body: str, category: str):
    if category == "spam":
        return None  # never reply to spam
    llm = _llm_reply(name, subject, body, category)
    if llm:
        return llm
    return REPLY_TEMPLATES.get(category, REPLY_TEMPLATES["other"]).format(name=name or "there")


def triage(email: dict) -> dict:
    subject = email.get("subject", "")
    body = email.get("body", "")
    category = classify(subject, body)
    priority = prioritize(subject, body, category)
    return {
        "id": email.get("id"),
        "from": email.get("from"),
        "subject": subject,
        "category": category,
        "priority": priority,
        "draft_reply": draft_reply(email.get("name", ""), subject, body, category),
        "needs_human_approval": category != "spam",
    }


PRIORITY_RANK = {"urgent": 0, "high": 1, "normal": 2, "low": 3}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Triage support emails from a JSON file.")
    parser.add_argument("input", help="Path to a JSON file containing a list of emails")
    parser.add_argument("-o", "--output", help="Write tickets to this JSON file")
    args = parser.parse_args(argv)

    with open(args.input, encoding="utf-8") as f:
        emails = json.load(f)

    tickets = sorted((triage(e) for e in emails), key=lambda t: PRIORITY_RANK[t["priority"]])

    for t in tickets:
        print(f"[{t['priority'].upper():6}] {t['category']:15} #{t['id']} {t['subject']}")

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(tickets, f, indent=2)
        print(f"\nSaved {len(tickets)} tickets to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
