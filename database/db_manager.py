from __future__ import annotations
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Any

APP_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = APP_ROOT / "data" / "spendsense.db"

class Database:
    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else DEFAULT_DB
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize(self):
        with self.connect() as conn:
            conn.executescript("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount >= 0),
                transaction_type TEXT NOT NULL CHECK(transaction_type IN ('income','expense')),
                category TEXT NOT NULL DEFAULT 'Uncategorized',
                payment_method TEXT NOT NULL DEFAULT 'Other',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                category TEXT NOT NULL DEFAULT 'Overall',
                budget_limit REAL NOT NULL CHECK(budget_limit >= 0),
                UNIQUE(month, year, category)
            );
            CREATE TABLE IF NOT EXISTS ai_insights (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                month INTEGER NOT NULL,
                year INTEGER NOT NULL,
                summary TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS import_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                imported_at TEXT NOT NULL,
                rows_processed INTEGER NOT NULL DEFAULT 0,
                rows_skipped INTEGER NOT NULL DEFAULT 0
            );
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
            """)

    def add_transaction(self, date, description, amount, transaction_type, category="Uncategorized", payment_method="Other"):
        with self.connect() as conn:
            cur = conn.execute("""INSERT INTO transactions
                (date, description, amount, transaction_type, category, payment_method, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (date, description.strip(), float(amount), transaction_type, category.strip() or "Uncategorized",
                 payment_method.strip() or "Other", datetime.now().isoformat(timespec="seconds")))
            return cur.lastrowid

    def update_transaction(self, transaction_id, date, description, amount, transaction_type, category, payment_method):
        with self.connect() as conn:
            conn.execute("""UPDATE transactions SET date=?, description=?, amount=?, transaction_type=?,
                category=?, payment_method=? WHERE id=?""",
                (date, description.strip(), float(amount), transaction_type, category.strip() or "Uncategorized",
                 payment_method.strip() or "Other", int(transaction_id)))

    def delete_transaction(self, transaction_id):
        with self.connect() as conn:
            conn.execute("DELETE FROM transactions WHERE id=?", (int(transaction_id),))

    def get_transactions(self, start_date=None, end_date=None, category=None, transaction_type=None, search=None):
        sql = "SELECT * FROM transactions WHERE 1=1"
        params: list[Any] = []
        if start_date:
            sql += " AND date >= ?"; params.append(start_date)
        if end_date:
            sql += " AND date <= ?"; params.append(end_date)
        if category and category != "All":
            sql += " AND category = ?"; params.append(category)
        if transaction_type and transaction_type != "all":
            sql += " AND transaction_type = ?"; params.append(transaction_type)
        if search:
            sql += " AND (description LIKE ? OR category LIKE ? OR payment_method LIKE ?)"
            params.extend([f"%{search}%"] * 3)
        sql += " ORDER BY date DESC, id DESC"
        with self.connect() as conn:
            return [dict(row) for row in conn.execute(sql, params).fetchall()]

    def get_categories(self):
        with self.connect() as conn:
            rows = conn.execute("SELECT DISTINCT category FROM transactions ORDER BY category").fetchall()
        return [r["category"] for r in rows]

    def totals(self, start_date=None, end_date=None):
        sql = """SELECT
            COALESCE(SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END),0) income,
            COALESCE(SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END),0) expenses
            FROM transactions WHERE 1=1"""
        params = []
        if start_date:
            sql += " AND date >= ?"; params.append(start_date)
        if end_date:
            sql += " AND date <= ?"; params.append(end_date)
        with self.connect() as conn:
            row = conn.execute(sql, params).fetchone()
        return {"income": float(row["income"]), "expenses": float(row["expenses"]),
                "balance": float(row["income"] - row["expenses"])}

    def category_totals(self, start_date=None, end_date=None):
        sql = """SELECT category, SUM(amount) total FROM transactions
                 WHERE transaction_type='expense'"""
        params = []
        if start_date:
            sql += " AND date >= ?"; params.append(start_date)
        if end_date:
            sql += " AND date <= ?"; params.append(end_date)
        sql += " GROUP BY category ORDER BY total DESC"
        with self.connect() as conn:
            return [{"category": r["category"], "total": float(r["total"])}
                    for r in conn.execute(sql, params).fetchall()]

    def monthly_totals(self, year):
        with self.connect() as conn:
            rows = conn.execute("""SELECT substr(date,1,7) month,
                SUM(CASE WHEN transaction_type='income' THEN amount ELSE 0 END) income,
                SUM(CASE WHEN transaction_type='expense' THEN amount ELSE 0 END) expenses
                FROM transactions WHERE substr(date,1,4)=?
                GROUP BY substr(date,1,7) ORDER BY month""", (str(year),)).fetchall()
        return [dict(r) for r in rows]

    def set_budget(self, month, year, category, amount):
        with self.connect() as conn:
            conn.execute("""INSERT INTO budgets(month,year,category,budget_limit) VALUES(?,?,?,?)
                ON CONFLICT(month,year,category) DO UPDATE SET budget_limit=excluded.budget_limit""",
                (int(month), int(year), category.strip() or "Overall", float(amount)))

    def get_budgets(self, month, year):
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM budgets WHERE month=? AND year=? ORDER BY category",
                                (int(month), int(year))).fetchall()
        return [dict(r) for r in rows]

    def add_insight(self, month, year, summary):
        with self.connect() as conn:
            conn.execute("INSERT INTO ai_insights(month,year,summary,created_at) VALUES(?,?,?,?)",
                         (int(month), int(year), summary, datetime.now().isoformat(timespec="seconds")))

    def get_insights(self, limit=30):
        with self.connect() as conn:
            rows = conn.execute("SELECT * FROM ai_insights ORDER BY id DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]

    def record_import(self, filename, processed, skipped):
        with self.connect() as conn:
            conn.execute("INSERT INTO import_history(filename,imported_at,rows_processed,rows_skipped) VALUES(?,?,?,?)",
                         (filename, datetime.now().isoformat(timespec="seconds"), int(processed), int(skipped)))

    def exists_transaction(self, date, description, amount, transaction_type):
        with self.connect() as conn:
            row = conn.execute("""SELECT 1 FROM transactions WHERE date=? AND lower(description)=lower(?)
                AND amount=? AND transaction_type=? LIMIT 1""",
                (date, description.strip(), float(amount), transaction_type)).fetchone()
        return row is not None
