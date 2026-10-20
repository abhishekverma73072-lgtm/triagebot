# TriageBot

An agent that triages support emails for small teams: it **classifies** each message, **prioritizes** it, and **drafts a reply** for a human to approve.

## Who it's for
Small teams and solo founders who get a steady stream of support email and want the urgent items (outages, double charges) at the top instead of buried in the inbox.

## How it works
1. **Classify**: bug, billing, account, feature request, spam, or other.
2. **Prioritize**: urgent, high, normal, or low, based on the wording and category.
3. **Draft reply**: a ready-to-edit response. Spam never gets a reply.
4. **Human approval**: every non-spam ticket is flagged `needs_human_approval`, so nothing is sent automatically.

It runs fully offline with rule-based logic. If `ANTHROPIC_API_KEY` is set (and `anthropic` is installed), reply drafting uses an LLM instead, with templates as the fallback.

## Quick start
```bash
git clone https://github.com/<your-username>/triagebot.git
cd triagebot
python triagebot.py sample_emails.json -o tickets.json
```

Example output:
```
[URGENT] bug             #1 App crashes on startup
[URGENT] billing         #2 Charged twice this month
[HIGH  ] account         #3 Can't log in
[NORMAL] other           #6 Question about opening hours
[LOW   ] feature_request #4 Dark mode suggestion
[LOW   ] spam            #5 WIN A PRIZE
```

## Input format
A JSON list of emails with `id`, `name`, `from`, `subject`, `body`. See `sample_emails.json`.

## Tests
```bash
pip install pytest
pytest
```

## How I built it with OmniRush
> Replace this section with your real sessions, for example:
> - **Session 1:** designed the categories and classification logic
> - **Session 2:** added priority scoring
> - **Session 3:** added reply drafting and the optional LLM mode
> - **Session 4:** wrote tests and this README

## Roadmap
- Connect to a real inbox (IMAP or Gmail API)
- Learn from corrected categories
- Slack notifications for urgent tickets
