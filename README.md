# Upsell Agent — Razorpay AI Buildathon (Track 01)

An AI agent that grows merchant revenue by proposing bounded, explainable
upsells on real orders — using Razorpay's test-mode Orders and Payments APIs,
with a full audit trail and graceful handling of payment failures.

Built for **Track 01: AI Growth & Agentic Commerce**.

---

## What It Does

```
Order comes in (e.g. "phone case")
        |
        v
Agent checks the merchant's pre-approved rulebook (catalog.py)
        |
        v
If a match exists: proposes ONE bounded upsell (fixed price, whitelisted item)
        |
        v
Creates a real Razorpay order for the upsell
        |
        v
Payment is completed via Razorpay's test-mode checkout
        |
        v
Payment status is fetched and confirmed
        |
        v
Every step is logged: what was proposed, why, and what happened
```

## How This Satisfies the Track 01 Bar

**"Every money action must be bounded, explainable, and human-gated/permissioned"**

- **Bounded** — the agent can only ever suggest items from a merchant-defined
  whitelist (`catalog.py`), each with a fixed price. A hard-coded price
  ceiling (`MAX_UPSELL_PRICE_PAISE`) acts as a second safety check even if
  the whitelist is ever misconfigured.
- **Explainable** — every proposal includes a plain-language reason. No
  black-box scoring model is used; the entire decision logic is a readable
  lookup table.
- **Human-gated** — the merchant is the human-in-the-loop here: they define
  and approve the entire rulebook the agent operates inside, ahead of time.
  The agent has zero authority to invent new products or prices beyond what
  a human has explicitly pre-approved.

**"Show the audit trail and one failure handled gracefully"**

- Every agent decision — whether it proposed an upsell or not, and whether
  the resulting payment succeeded, failed, or errored — is logged to
  `audit_log.jsonl` with a timestamp, the proposal, the reasoning, and the
  outcome.
- Three failure modes are explicitly handled with no crashes and no blind
  retries:
  1. A successful payment logs `"captured"`.
  2. An abandoned/failed checkout (no `payment_id` returned) logs `"failed"`
     with a clear reason.
  3. An invalid or unreachable payment lookup is caught and logs `"error"`
     with the real error message from Razorpay's API.

---

## Architecture

- **`catalog.py`** — the merchant's rulebook: which items unlock which
  upsell, at what price, with what reasoning. Nothing outside this file can
  ever be proposed.
- **`agent.py`** — the decision logic. Given an order item, looks it up
  against the rulebook and returns a bounded proposal (or nothing).
- **`api.py`** — FastAPI wrapper exposing the agent over HTTP:
  - `POST /orders` — takes an order item, runs the agent, creates a real
    Razorpay order for any proposed upsell.
  - `POST /orders/{order_id}/confirm-payment` — takes a payment ID (from
    the browser checkout step), fetches its real status from Razorpay, and
    logs the outcome.
- **`audit_log.py`** — writes every agent action to `audit_log.jsonl`, one
  structured JSON entry per line.
- **`checkout_test.html`** — a minimal page that triggers Razorpay's actual
  test-mode checkout popup. (Payment always requires a human-authorized
  checkout step, even in test mode — no legitimate agent bypasses this.)

---

## Setup

1. Clone this repo and install dependencies:
   ```bash
   uv sync
   ```

2. Create a `.env` file with your Razorpay test-mode keys:
   ```
   RAZORPAY_KEY_ID=rzp_test_xxxxxxxxxxxx
   RAZORPAY_KEY_SECRET=your_secret_here
   ```

3. Run the API:
   ```bash
   uv run uvicorn api:app --reload
   ```

4. Open `http://localhost:8000/docs` to test the endpoints interactively.

## Trying the Full Flow

1. **Propose an upsell:** `POST /orders` with `{"item": "phone case"}`.
   Note the returned `razorpay_order_id`.

2. **Pay it:** open `checkout_test.html` (served separately, e.g. via
   `python -m http.server 8080` — use a different port than the API), paste
   in the `razorpay_order_id`, and complete checkout using Razorpay's test
   Netbanking flow (`Success Test Bank` or `Failure Test Bank`).

3. **Confirm the outcome:** `POST /orders/{order_id}/confirm-payment` with
   the `payment_id` from the checkout popup (or an empty body if checkout
   failed). Check `audit_log.jsonl` for the logged result.

## Known Limitation

Razorpay payments always require a human-authorized checkout step (even in
test mode) — there is no server-side way to fake a payment. This means the
agent automates *proposal, decision, and order creation*, while the actual
payment authorization step still requires a real checkout interaction. This
mirrors real-world agentic commerce: an agent can initiate a transaction,
but a payment instrument still requires explicit authorization.
