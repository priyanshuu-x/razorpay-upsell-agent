from fastapi import FastAPI
from pydantic import BaseModel
import os
from dotenv import load_dotenv
import razorpay

from agent import propose_upsell
from audit_log import log_event

load_dotenv()

app = FastAPI(title="Upsell Agent API")

client = razorpay.Client(
    auth=(os.getenv("RAZORPAY_KEY_ID"), os.getenv("RAZORPAY_KEY_SECRET"))
)


pending_upsells = {}


class OrderRequest(BaseModel):
    item: str


class PaymentConfirmation(BaseModel):
    payment_id: str | None = None  


@app.get("/")
def root():
    """Simple health-check so visiting the base URL doesn't 404."""
    return {"message": "Upsell Agent API is running", "docs": "/docs"}


@app.post("/orders")
def create_order(order: OrderRequest):
    """
    Given an order item, the agent decides whether to propose an upsell.
    If it does, a real Razorpay order is created for it.
    """
    proposal = propose_upsell(order.item)

    if proposal is None:
        log_event(
            original_item=order.item,
            proposal=None,
            razorpay_order_id=None,
            payment_status=None
        )
        return {"upsell_proposed": False, "message": f"No upsell found for '{order.item}'"}

    upsell_order = client.order.create({
        "amount": proposal["price_paise"],
        "currency": "INR",
        "notes": {
            "created_by": "upsell-agent",
            "original_item": proposal["original_item"],
            "reason": proposal["reason"]
        }
    })


    pending_upsells[upsell_order["id"]] = proposal

    return {
        "upsell_proposed": True,
        "proposal": proposal,
        "razorpay_order_id": upsell_order["id"],
        "razorpay_key_id": os.getenv("RAZORPAY_KEY_ID"),
        "amount_paise": proposal["price_paise"]
    }


@app.post("/orders/{order_id}/confirm-payment")
def confirm_payment(order_id: str, confirmation: PaymentConfirmation):
    """
    Call this after completing checkout in the browser.
    Fetches the real payment status from Razorpay, logs it, and reports it back.
    Handles all 3 outcomes: success, no payment_id (failed checkout), invalid id (API error).
    """
    proposal = pending_upsells.get(order_id)

    if confirmation.payment_id is None:
        log_event(
            original_item=proposal["original_item"] if proposal else "unknown",
            proposal=proposal,
            razorpay_order_id=order_id,
            payment_status="failed",
            error="Checkout did not complete - no payment_id returned"
        )
        return {"status": "failed", "message": "No payment_id provided - checkout likely failed"}

    try:
        fetched_payment = client.payment.fetch(confirmation.payment_id)
        log_event(
            original_item=proposal["original_item"] if proposal else "unknown",
            proposal=proposal,
            razorpay_order_id=order_id,
            payment_status=fetched_payment["status"]
        )
        return {"status": fetched_payment["status"], "payment": fetched_payment}

    except Exception as e:
        log_event(
            original_item=proposal["original_item"] if proposal else "unknown",
            proposal=proposal,
            razorpay_order_id=order_id,
            payment_status="error",
            error=str(e)
        )
        return {"status": "error", "message": str(e)}