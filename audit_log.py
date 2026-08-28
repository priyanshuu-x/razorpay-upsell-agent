import json
from datetime import datetime, timezone

LOG_FILE = "audit_log.jsonl"  

def log_event(original_item: str, proposal: dict | None, razorpay_order_id: str | None,
              payment_status: str | None, error: str | None = None):
    """
    Writes one structured entry to the audit log.
    Every agent action - proposed, executed, or failed - goes through this function.
    """
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_item": original_item,
        "proposal": proposal,           
        "razorpay_order_id": razorpay_order_id,  
        "payment_status": payment_status,        
        "error": error                  
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")

    print(f"[audit log] {entry}")