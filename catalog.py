# catalog.py
# This is the merchant's pre-approved rulebook.
# The agent can ONLY suggest items listed here - nothing else, ever.

UPSELL_RULES = {
    "phone case": {
        "suggest": "screen protector",
        "price_paise": 29900,  # ₹299, in paise (Razorpay's required unit)
        "reason": "Customers who buy phone cases often add a screen protector"
    },
    "coffee mug": {
        "suggest": "coffee beans (250g)",
        "price_paise": 39900,  # ₹399
        "reason": "Completes the coffee combo"
    },
    "yoga mat": {
        "suggest": "resistance bands",
        "price_paise": 49900,  # ₹499
        "reason": "Popular add-on for home workouts"
    },
}

# Safety ceiling - even if someone edits the table above and makes a mistake,
# the agent will refuse to propose anything above this price.
MAX_UPSELL_PRICE_PAISE = 50000  # ₹500