import json
import os
from datetime import date
from dotenv import load_dotenv
import requests
from modules.categorizer import categorize

load_dotenv()

def _call_ai(system_prompt, user_content):
    api_key = os.getenv("AI_API_KEY", "").strip()
    if not api_key:
        return None
    base_url = os.getenv("AI_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    model = os.getenv("AI_MODEL", "gpt-4o-mini")
    try:
        response = requests.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "temperature": 0.2, "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]}, timeout=30
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        return None

def ai_categorize(description, transaction_type="expense"):
    categories = ["Groceries", "Food & Dining", "Transport", "Shopping", "Utilities",
                  "Healthcare", "Entertainment", "Education", "Housing", "Salary",
                  "Investment", "Other Income", "Uncategorized"]
    prompt = "Choose exactly one category from this list: " + ", ".join(categories) + ". Return only the category name."
    answer = _call_ai(prompt, f"Transaction type: {transaction_type}\nDescription: {description}")
    if answer:
        answer = answer.strip().strip('"').strip("'")
        if answer in categories:
            return answer
    return categorize(description, transaction_type)

def generate_summary(month, year, totals, category_totals, budgets):
    payload = {
        "period": f"{year}-{month:02d}",
        "income": round(totals["income"], 2),
        "expenses": round(totals["expenses"], 2),
        "net_balance": round(totals["balance"], 2),
        "expense_categories": [{"category": x["category"], "amount": round(x["total"], 2)} for x in category_totals],
        "budgets": budgets
    }
    prompt = ("You are a careful personal budgeting assistant. Summarize only the supplied data. "
              "Mention notable categories and budget usage if available. Do not invent values, "
              "do not claim certainty about causes, and do not give investment advice. "
              "Keep the response concise, practical, and informational.")
    result = _call_ai(prompt, json.dumps(payload, ensure_ascii=False))
    if result:
        return result
    # Useful offline fallback, calculated only from actual data.
    lines = [f"Summary for {year}-{month:02d}: income {totals['income']:.2f}, "
             f"expenses {totals['expenses']:.2f}, net balance {totals['balance']:.2f}."]
    if category_totals:
        top = category_totals[0]
        lines.append(f"Highest recorded expense category: {top['category']} ({top['total']:.2f}).")
    if budgets:
        for b in budgets:
            used = sum(x["total"] for x in category_totals) if b["category"] == "Overall" else next(
                (x["total"] for x in category_totals if x["category"] == b["category"]), 0)
            if b["budget_limit"] > 0:
                pct = used / b["budget_limit"] * 100
                if pct >= 100:
                    lines.append(f"{b['category']} budget is over limit ({pct:.0f}% used).")
                elif pct >= 80:
                    lines.append(f"{b['category']} budget has reached {pct:.0f}% usage.")
    lines.append("Offline summary: configure an AI API in .env for natural-language AI analysis.")
    return " ".join(lines)
