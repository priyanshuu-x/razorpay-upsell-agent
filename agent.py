# agent.py
from catalog import UPSELL_RULES, MAX_UPSELL_PRICE_PAISE

def propose_upsell(order_item: str) -> dict | None:
    """
    Looks up the order_item in the merchant's rulebook.
    Returns a proposal dict if a bounded, approved upsell exists.
    Returns None if there's no match, or if it fails the safety check.
    """
    # Look up the item (case-insensitive, so "Phone Case" and "phone case" both match)
    rule = UPSELL_RULES.get(order_item.lower())

    if rule is None:
        return None  # No upsell rule exists for this item - agent does nothing

    # Safety check - even a pre-approved rule can never exceed the price ceiling
    if rule["price_paise"] > MAX_UPSELL_PRICE_PAISE:
        return None

    return {
        "original_item": order_item,
        "proposed_item": rule["suggest"],
        "price_paise": rule["price_paise"],
        "reason": rule["reason"]
    }


# --- Quick manual test, so we can see it working before wiring it to anything else ---
if __name__ == "__main__":
    test_orders = ["phone case", "coffee mug", "yoga mat", "laptop"]

    for item in test_orders:
        proposal = propose_upsell(item)
        print(f"\nOrder: {item}")
        if proposal:
            print(f"  Proposal: {proposal['proposed_item']} (₹{proposal['price_paise']/100})")
            print(f"  Reason: {proposal['reason']}")
        else:
            print("  No upsell proposed.")