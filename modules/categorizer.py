import re

RULES = {
    "Groceries": ["grocery", "supermarket", "vegetable", "fruit", "mart", "milk", "bakery"],
    "Food & Dining": ["restaurant", "cafe", "coffee", "pizza", "food", "swiggy", "zomato", "dining"],
    "Transport": ["uber", "ola", "fuel", "petrol", "diesel", "bus", "train", "metro", "taxi", "parking"],
    "Shopping": ["amazon", "flipkart", "shopping", "clothing", "clothes", "shoes", "store"],
    "Utilities": ["electricity", "water bill", "internet", "wifi", "mobile recharge", "gas bill", "utility"],
    "Healthcare": ["hospital", "doctor", "pharmacy", "medicine", "medical", "clinic"],
    "Entertainment": ["movie", "cinema", "netflix", "spotify", "game", "concert"],
    "Education": ["course", "book", "tuition", "education", "training"],
    "Housing": ["rent", "maintenance", "mortgage"],
    "Salary": ["salary", "payroll", "wages"],
    "Investment": ["investment", "dividend", "mutual fund", "interest"]
}

def categorize(description: str, transaction_type: str = "expense") -> str:
    text = re.sub(r"\s+", " ", (description or "").lower())
    if transaction_type == "income":
        for category in ("Salary", "Investment"):
            if any(word in text for word in RULES[category]):
                return category
        return "Other Income"
    for category, keywords in RULES.items():
        if category in ("Salary", "Investment"):
            continue
        if any(word in text for word in keywords):
            return category
    return "Uncategorized"
