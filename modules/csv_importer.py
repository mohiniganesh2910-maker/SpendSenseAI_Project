import csv
from datetime import datetime
from pathlib import Path
import pandas as pd
from modules.categorizer import categorize

ALIASES = {
    "date": ["date", "transaction date", "txn date", "posted date"],
    "description": ["description", "details", "merchant", "narration", "transaction", "name"],
    "amount": ["amount", "value", "transaction amount", "total"],
    "type": ["type", "transaction_type", "transaction type", "kind"],
    "category": ["category", "expense category", "group"],
    "payment_method": ["payment_method", "payment method", "method", "payment"]
}

def _column_map(columns):
    normalized = {str(c).strip().lower(): c for c in columns}
    result = {}
    for target, aliases in ALIASES.items():
        for alias in aliases:
            if alias in normalized:
                result[target] = normalized[alias]
                break
    return result

def preview_csv(path):
    frame = pd.read_csv(path)
    mapping = _column_map(frame.columns)
    missing = [key for key in ("date", "description", "amount") if key not in mapping]
    if missing:
        raise ValueError("CSV must include columns for: " + ", ".join(missing))
    rows, errors = [], []
    for idx, record in frame.iterrows():
        try:
            raw_date = str(record[mapping["date"]]).strip()
            parsed = pd.to_datetime(raw_date, errors="raise")
            date_text = parsed.strftime("%Y-%m-%d")
            description = str(record[mapping["description"]]).strip()
            amount = float(str(record[mapping["amount"]]).replace(",", "").replace("₹", "").strip())
            if not description or description.lower() == "nan":
                raise ValueError("description is empty")
            if amount < 0:
                raise ValueError("amount must not be negative")
            raw_type = str(record[mapping["type"]]).strip().lower() if "type" in mapping else "expense"
            if raw_type in ("income", "credit", "deposit", "salary"):
                tx_type = "income"
            elif raw_type in ("expense", "debit", "withdrawal", "payment", "nan", ""):
                tx_type = "expense"
            else:
                raise ValueError("type must be income or expense")
            category = str(record[mapping["category"]]).strip() if "category" in mapping else ""
            if not category or category.lower() == "nan":
                category = categorize(description, tx_type)
            method = str(record[mapping["payment_method"]]).strip() if "payment_method" in mapping else "Other"
            if not method or method.lower() == "nan":
                method = "Other"
            rows.append({"date": date_text, "description": description, "amount": amount,
                         "transaction_type": tx_type, "category": category, "payment_method": method})
        except Exception as exc:
            errors.append(f"Row {idx + 2}: {exc}")
    return rows, errors

def import_csv(path, db):
    rows, errors = preview_csv(path)
    processed, skipped = 0, len(errors)
    for row in rows:
        if db.exists_transaction(row["date"], row["description"], row["amount"], row["transaction_type"]):
            skipped += 1
            continue
        db.add_transaction(**row)
        processed += 1
    db.record_import(Path(path).name, processed, skipped)
    return processed, skipped, errors
