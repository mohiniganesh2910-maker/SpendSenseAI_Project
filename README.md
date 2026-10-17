# SpendSense AI
### Intelligent Expense Analysis & Budget Assistant

A Python desktop application for managing income and expenses, importing CSV transactions, tracking budgets, viewing charts, generating PDF reports, and optionally using an AI API for categorization and spending summaries.

## Features
- Modern desktop interface using CustomTkinter (falls back to Tkinter if unavailable).
- SQLite database with persistent transaction, budget, and AI insight history.
- Add, edit, delete, search, and filter transactions.
- CSV import with column mapping, validation, and duplicate checking.
- Monthly and category budgets with 80% warning and over-budget alerts.
- Dashboard cards and Matplotlib charts.
- Optional AI expense categorization and data-grounded monthly summaries.
- PDF report generation and CSV export.
- No AI key required for core functionality; local categorization and summaries are provided.

## Requirements
- Python 3.10+
- Windows, macOS, or Linux with a desktop environment
- Internet/API key only for optional AI features

## Setup (Windows)
1. Extract the ZIP file.
2. Open the extracted `SpendSenseAI` folder in VS Code.
3. Open a terminal in that folder.
4. Create a virtual environment:
   ```bash
   python -m venv .venv
   .venv\\Scripts\\activate
   ```
5. Install packages:
   ```bash
   pip install -r requirements.txt
   ```
6. Optional: copy `.env.example` to `.env` and add your AI API key.
7. Run:
   ```bash
   python main.py
   ```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## CSV import format
Recommended columns (column names are case-insensitive; common alternatives are accepted):
- `date` (e.g. `2026-10-15`)
- `description`
- `amount`
- `type` or `transaction_type` (`expense` or `income`)
- optional `category`
- optional `payment_method`

Example:
```csv
date,description,amount,type,category,payment_method
2026-10-01,Supermarket,1250,expense,Groceries,Card
2026-10-02,Salary,35000,income,Salary,Bank transfer
2026-10-03,Bus pass,600,expense,Transport,Cash
```

Negative amounts are not accepted; choose `income` or `expense` in the type column. Import preview and validation happen before database insertion.

## Database and generated files
- Database is created automatically at `data/spendsense.db`.
- Exported PDF/CSV reports can be saved wherever you choose.
- Do not commit `.env` or real financial data to public repositories.

## AI configuration
AI is optional. Set `AI_API_KEY`, `AI_BASE_URL`, and `AI_MODEL` in `.env` for an OpenAI-compatible Chat Completions endpoint. The app sends only the transaction descriptions and amounts needed for the requested AI task; avoid including sensitive personal information in descriptions. If the endpoint is unavailable, local categorization and summary remain available.

## Testing
```bash
pytest -q
```

## Notes
This app is an educational budgeting tool, not professional financial advice. Verify imported data and AI suggestions before relying on them.
