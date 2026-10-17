from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import mm

def export_pdf(path, month, year, totals, category_totals, transactions, budgets):
    doc = SimpleDocTemplate(str(path), pagesize=A4, rightMargin=18*mm, leftMargin=18*mm,
                            topMargin=16*mm, bottomMargin=16*mm)
    styles = getSampleStyleSheet()
    story = [Paragraph("SpendSense AI - Monthly Financial Report", styles["Title"]),
             Paragraph(f"Reporting period: {year}-{month:02d}", styles["Normal"]), Spacer(1, 8*mm)]
    summary = [["Metric", "Amount"], ["Income", f"₹{totals['income']:,.2f}"],
               ["Expenses", f"₹{totals['expenses']:,.2f}"], ["Net balance", f"₹{totals['balance']:,.2f}"]]
    table = Table(summary, colWidths=[80*mm, 65*mm])
    table.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#26354A")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.lightgrey),
        ("PADDING",(0,0),(-1,-1),7)]))
    story += [table, Spacer(1, 7*mm), Paragraph("Expense categories", styles["Heading2"])]
    cat_rows = [["Category", "Total"]] + [[x["category"], f"₹{x['total']:,.2f}"] for x in category_totals]
    if len(cat_rows) == 1:
        cat_rows.append(["No expense records", "₹0.00"])
    ct = Table(cat_rows, colWidths=[80*mm, 65*mm], repeatRows=1)
    ct.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#26354A")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.lightgrey),
        ("PADDING",(0,0),(-1,-1),6)]))
    story += [ct, Spacer(1, 7*mm), Paragraph("Budgets", styles["Heading2"])]
    budget_rows = [["Category", "Limit", "Spent", "Usage"]]
    for b in budgets:
        spent = totals["expenses"] if b["category"] == "Overall" else next(
            (x["total"] for x in category_totals if x["category"] == b["category"]), 0)
        pct = spent / b["budget_limit"] * 100 if b["budget_limit"] else 0
        budget_rows.append([b["category"], f"₹{b['budget_limit']:,.2f}", f"₹{spent:,.2f}", f"{pct:.0f}%"])
    if len(budget_rows) == 1:
        budget_rows.append(["No budgets set", "-", "-", "-"])
    bt = Table(budget_rows, colWidths=[48*mm, 40*mm, 40*mm, 25*mm], repeatRows=1)
    bt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#26354A")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.4,colors.lightgrey),
        ("PADDING",(0,0),(-1,-1),5)]))
    story += [bt, Spacer(1, 7*mm), Paragraph("Recent transactions", styles["Heading2"])]
    tx_rows = [["Date", "Description", "Type", "Category", "Amount"]]
    for t in transactions[:100]:
        tx_rows.append([t["date"], str(t["description"])[:28], t["transaction_type"], t["category"][:18],
                        f"₹{t['amount']:,.2f}"])
    if len(tx_rows) == 1:
        tx_rows.append(["-", "No transactions", "-", "-", "-"])
    tt = Table(tx_rows, colWidths=[25*mm, 55*mm, 22*mm, 35*mm, 28*mm], repeatRows=1)
    tt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#26354A")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),("GRID",(0,0),(-1,-1),0.3,colors.lightgrey),
        ("FONTSIZE",(0,0),(-1,-1),7),("PADDING",(0,0),(-1,-1),4)]))
    story.append(tt)
    doc.build(story)
