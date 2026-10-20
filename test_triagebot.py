import json

from triagebot import classify, prioritize, triage


def test_bug_classified():
    assert classify("App crashes", "it crashes on startup") == "bug"


def test_billing_urgent():
    t = triage({"id": 1, "name": "A", "subject": "Charged twice", "body": "urgent refund please"})
    assert t["category"] == "billing"
    assert t["priority"] == "urgent"
    assert t["draft_reply"]


def test_account():
    assert classify("Login help", "I forgot my password") == "account"


def test_feature_request_low_priority():
    cat = classify("Idea", "It would be great if you could add dark mode")
    assert cat == "feature_request"
    assert prioritize("Idea", "add dark mode", cat) == "low"


def test_spam_gets_no_reply():
    t = triage({"id": 5, "subject": "WIN A PRIZE", "body": "click here now free money"})
    assert t["category"] == "spam"
    assert t["draft_reply"] is None
    assert t["needs_human_approval"] is False


def test_other_fallback():
    assert classify("Hello", "what are your opening hours?") == "other"


def test_sample_file_loads():
    with open("sample_emails.json", encoding="utf-8") as f:
        emails = json.load(f)
    assert len(emails) == 6
    assert all(triage(e)["category"] for e in emails)
