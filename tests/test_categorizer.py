from modules.categorizer import categorize

def test_grocery_categorization():
    assert categorize("Supermarket purchase") == "Groceries"

def test_transport_categorization():
    assert categorize("Uber ride") == "Transport"

def test_income_categorization():
    assert categorize("Monthly salary", "income") == "Salary"

def test_unknown_category():
    assert categorize("miscellaneous xyz") == "Uncategorized"
