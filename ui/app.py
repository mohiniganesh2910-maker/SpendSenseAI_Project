from __future__ import annotations
import csv
import os
import calendar
from datetime import date, datetime
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import customtkinter as ctk
    CTK_AVAILABLE = True
except Exception:
    ctk = None
    CTK_AVAILABLE = False

from database.db_manager import Database
from modules.categorizer import categorize
from modules.csv_importer import preview_csv, import_csv
from modules.ai_insights import ai_categorize, generate_summary
from modules.report_generator import export_pdf

CATEGORIES = ["Groceries", "Food & Dining", "Transport", "Shopping", "Utilities", "Healthcare",
              "Entertainment", "Education", "Housing", "Salary", "Investment", "Other Income",
              "Uncategorized", "Other"]

class SpendSenseApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SpendSense AI | Expense & Budget Assistant")
        self.geometry("1220x780")
        self.minsize(1000, 650)
        self.db = Database()
        self.selected_id = None
        self.current_month = date.today().month
        self.current_year = date.today().year
        self._setup_theme()
        self._build_ui()
        self.refresh_all()

    def _setup_theme(self):
        if CTK_AVAILABLE:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("blue")
            self.configure(bg="#111827")
        else:
            self.configure(bg="#111827")
            style = ttk.Style(self)
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
            style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
            style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        # Use standard Tk widgets for reliable table/file-dialog compatibility; CTk is used for shell when installed.
        shell_bg = "#111827"
        header = tk.Frame(self, bg="#172033", padx=22, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="SpendSense AI", bg="#172033", fg="#F8FAFC",
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(header, text="INTELLIGENT EXPENSE ANALYSIS", bg="#172033", fg="#94A3B8",
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=16, pady=(8,0))
        tk.Button(header, text="＋ Add transaction", command=self.new_transaction,
                  bg="#2563EB", fg="white", activebackground="#1D4ED8", relief="flat",
                  padx=14, pady=8, font=("Segoe UI", 10, "bold")).pack(side="right")
        nav = tk.Frame(self, bg="#111827", padx=16, pady=10)
        nav.pack(fill="x")
        self.tabs = ttk.Notebook(nav)
        self.tabs.pack(fill="both", expand=True)
        self.dashboard_tab = tk.Frame(self.tabs, bg=shell_bg)
        self.transactions_tab = tk.Frame(self.tabs, bg=shell_bg)
        self.budget_tab = tk.Frame(self.tabs, bg=shell_bg)
        self.insights_tab = tk.Frame(self.tabs, bg=shell_bg)
        self.tabs.add(self.dashboard_tab, text="  Dashboard  ")
        self.tabs.add(self.transactions_tab, text="  Transactions  ")
        self.tabs.add(self.budget_tab, text="  Budgets  ")
        self.tabs.add(self.insights_tab, text="  AI Insights & Reports  ")
        self._build_dashboard()
        self._build_transactions()
        self._build_budgets()
        self._build_insights()
        footer = tk.Label(self, text="Your data stays on this computer unless you explicitly use optional AI features.",
                          bg="#111827", fg="#64748B", font=("Segoe UI", 9), anchor="w", padx=22, pady=7)
        footer.pack(fill="x", side="bottom")

    def _label(self, parent, text, **kwargs):
        defaults = {"bg": "#111827", "fg": "#E2E8F0", "font": ("Segoe UI", 10)}
        defaults.update(kwargs)
        return tk.Label(parent, text=text, **defaults)

    def _entry(self, parent, width=18):
        return tk.Entry(parent, width=width, font=("Segoe UI", 10), relief="flat",
                        bg="#1E293B", fg="#F8FAFC", insertbackground="white")

    def _button(self, parent, text, command, primary=False):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         bg="#2563EB" if primary else "#263449", fg="white",
                         activebackground="#1D4ED8" if primary else "#334155",
                         activeforeground="white", padx=11, pady=7, cursor="hand2",
                         font=("Segoe UI", 9, "bold" if primary else "normal"))

    def _build_dashboard(self):
        top = tk.Frame(self.dashboard_tab, bg="#111827", padx=10, pady=10)
        top.pack(fill="x")
        self.period_label = self._label(top, "", font=("Segoe UI", 15, "bold"))
        self.period_label.pack(side="left")
        self._button(top, "Refresh", self.refresh_all).pack(side="right")
        self.metric_frame = tk.Frame(self.dashboard_tab, bg="#111827")
        self.metric_frame.pack(fill="x", padx=10)
        self.chart_frame = tk.Frame(self.dashboard_tab, bg="#111827")
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.alert_frame = tk.Frame(self.dashboard_tab, bg="#111827")
        self.alert_frame.pack(fill="x", padx=16, pady=(0,10))

    def _build_transactions(self):
        controls = tk.Frame(self.transactions_tab, bg="#111827", padx=10, pady=10)
        controls.pack(fill="x")
        self.search_var = tk.StringVar()
        self.type_var = tk.StringVar(value="all")
        self._label(controls, "Search").pack(side="left", padx=(0,5))
        search = self._entry(controls, 24); search.pack(side="left", padx=(0,10))
        search.configure(textvariable=self.search_var)
        search.bind("<Return>", lambda e: self.refresh_transactions())
        self._label(controls, "Type").pack(side="left", padx=(0,5))
        type_box = ttk.Combobox(controls, textvariable=self.type_var, values=["all","expense","income"],
                                width=12, state="readonly")
        type_box.pack(side="left", padx=(0,10))
        type_box.bind("<<ComboboxSelected>>", lambda e: self.refresh_transactions())
        self._button(controls, "Search", self.refresh_transactions, True).pack(side="left", padx=3)
        self._button(controls, "Import CSV", self.do_import).pack(side="left", padx=3)
        self._button(controls, "Export CSV", self.export_csv).pack(side="left", padx=3)
        self._button(controls, "Edit selected", self.edit_selected).pack(side="right", padx=3)
        self._button(controls, "Delete selected", self.delete_selected).pack(side="right", padx=3)
        cols = ("id","date","description","type","category","payment","amount")
        self.tx_tree = ttk.Treeview(self.transactions_tab, columns=cols, show="headings", selectmode="browse")
        headings = {"id":"ID","date":"Date","description":"Description","type":"Type","category":"Category",
                    "payment":"Payment","amount":"Amount"}
        widths = {"id":55,"date":100,"description":300,"type":95,"category":150,"payment":110,"amount":120}
        for col in cols:
            self.tx_tree.heading(col, text=headings[col])
            self.tx_tree.column(col, width=widths[col], anchor="w" if col in ("description","category") else "center")
        self.tx_tree.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.tx_tree.tag_configure("income", foreground="#16A34A")
        self.tx_tree.tag_configure("expense", foreground="#F87171")

    def _build_budgets(self):
        form = tk.Frame(self.budget_tab, bg="#111827", padx=16, pady=16)
        form.pack(fill="x")
        self._label(form, "Set a monthly budget", font=("Segoe UI", 16, "bold")).grid(row=0,column=0,columnspan=8,sticky="w",pady=(0,14))
        self._label(form, "Month (1-12)").grid(row=1,column=0,sticky="w",padx=4)
        self.budget_month = tk.StringVar(value=str(self.current_month))
        tk.Entry(form,textvariable=self.budget_month,width=8).grid(row=2,column=0,padx=4,pady=5)
        self._label(form, "Year").grid(row=1,column=1,sticky="w",padx=4)
        self.budget_year = tk.StringVar(value=str(self.current_year))
        tk.Entry(form,textvariable=self.budget_year,width=10).grid(row=2,column=1,padx=4,pady=5)
        self._label(form, "Category").grid(row=1,column=2,sticky="w",padx=4)
        self.budget_category = tk.StringVar(value="Overall")
        ttk.Combobox(form,textvariable=self.budget_category,values=["Overall"]+CATEGORIES,width=18,state="readonly").grid(row=2,column=2,padx=4,pady=5)
        self._label(form, "Budget amount (₹)").grid(row=1,column=3,sticky="w",padx=4)
        self.budget_amount = tk.StringVar()
        tk.Entry(form,textvariable=self.budget_amount,width=16).grid(row=2,column=3,padx=4,pady=5)
        self._button(form, "Save budget", self.save_budget, True).grid(row=2,column=4,padx=10)
        self._button(form, "Refresh", self.refresh_budgets).grid(row=2,column=5,padx=4)
        self.budget_list = tk.Frame(self.budget_tab,bg="#111827",padx=16,pady=8)
        self.budget_list.pack(fill="both",expand=True)

    def _build_insights(self):
        controls = tk.Frame(self.insights_tab,bg="#111827",padx=14,pady=14)
        controls.pack(fill="x")
        self._label(controls,"Monthly AI spending summary",font=("Segoe UI",16,"bold")).pack(side="left")
        self._button(controls,"Generate summary",self.make_summary,True).pack(side="right",padx=4)
        self._button(controls,"Export PDF report",self.make_pdf).pack(side="right",padx=4)
        self._button(controls,"Export CSV",self.export_csv).pack(side="right",padx=4)
        self.summary_text = tk.Text(self.insights_tab,height=9,wrap="word",bg="#1E293B",fg="#E2E8F0",
                                    insertbackground="white",relief="flat",font=("Segoe UI",11),padx=12,pady=12)
        self.summary_text.pack(fill="x",padx=14,pady=(0,12))
        self._label(self.insights_tab,"Saved summaries",font=("Segoe UI",12,"bold")).pack(anchor="w",padx=14)
        self.insight_history = tk.Listbox(self.insights_tab,bg="#1E293B",fg="#E2E8F0",selectbackground="#2563EB",
                                          relief="flat",font=("Segoe UI",10),height=8)
        self.insight_history.pack(fill="both",expand=True,padx=14,pady=10)

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_transactions()
        self.refresh_budgets()
        self.refresh_insight_history()

    def _period(self):
        return f"{self.current_year}-{self.current_month:02d}"

    def _month_range(self):
        start = f"{self.current_year}-{self.current_month:02d}-01"
        last = calendar.monthrange(self.current_year,self.current_month)[1]
        return start, f"{self.current_year}-{self.current_month:02d}-{last:02d}"

    def refresh_dashboard(self):
        for w in self.metric_frame.winfo_children(): w.destroy()
        for w in self.chart_frame.winfo_children(): w.destroy()
        for w in self.alert_frame.winfo_children(): w.destroy()
        start,end = self._month_range()
        totals = self.db.totals(start,end)
        self.period_label.configure(text=f"Overview  /  {calendar.month_name[self.current_month]} {self.current_year}")
        metrics = [("Income",totals["income"],"#22C55E"),("Expenses",totals["expenses"],"#F87171"),
                   ("Net balance",totals["balance"],"#60A5FA")]
        for title,amount,color in metrics:
            card = tk.Frame(self.metric_frame,bg="#1E293B",padx=20,pady=16)
            card.pack(side="left",fill="x",expand=True,padx=5,pady=5)
            tk.Label(card,text=title,bg="#1E293B",fg="#94A3B8",font=("Segoe UI",10)).pack(anchor="w")
            tk.Label(card,text=f"₹{amount:,.2f}",bg="#1E293B",fg=color,font=("Segoe UI",20,"bold")).pack(anchor="w",pady=(5,0))
        self._draw_charts(start,end)
        budgets = self.db.get_budgets(self.current_month,self.current_year)
        cats = self.db.category_totals(start,end)
        alerts=[]
        for b in budgets:
            spent = totals["expenses"] if b["category"]=="Overall" else next((x["total"] for x in cats if x["category"]==b["category"]),0)
            if b["budget_limit"] > 0:
                pct=spent/b["budget_limit"]*100
                if pct>=100: alerts.append(f"⚠ {b['category']} budget exceeded: {pct:.0f}% used.")
                elif pct>=80: alerts.append(f"Budget alert: {b['category']} is {pct:.0f}% used.")
        for alert in alerts:
            tk.Label(self.alert_frame,text=alert,bg="#422006",fg="#FDE68A",anchor="w",padx=10,pady=5).pack(fill="x",pady=2)

    def _draw_charts(self,start,end):
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
            cats=self.db.category_totals(start,end)
            monthly=self.db.monthly_totals(self.current_year)
            fig=Figure(figsize=(8.4,3.0),dpi=95,facecolor="#111827")
            ax1=fig.add_subplot(121); ax2=fig.add_subplot(122)
            for ax in (ax1,ax2):
                ax.set_facecolor("#1E293B")
                ax.tick_params(colors="#CBD5E1",labelsize=8)
                for spine in ax.spines.values(): spine.set_color("#475569")
            if cats:
                ax1.pie([x["total"] for x in cats],labels=[x["category"] for x in cats],
                        autopct="%1.0f%%",textprops={"color":"#E2E8F0","fontsize":7},startangle=90)
                ax1.set_title("Expense categories",color="#F8FAFC",fontsize=10)
            else:
                ax1.text(.5,.5,"No expense data yet",ha="center",va="center",color="#CBD5E1")
                ax1.set_title("Expense categories",color="#F8FAFC",fontsize=10)
            if monthly:
                labels=[r["month"][5:] for r in monthly]
                vals=[r["expenses"] or 0 for r in monthly]
                ax2.bar(labels,vals,color="#60A5FA")
                ax2.set_title("Monthly expenses",color="#F8FAFC",fontsize=10)
                ax2.tick_params(axis="x",rotation=0)
            else:
                ax2.text(.5,.5,"No monthly data yet",ha="center",va="center",color="#CBD5E1")
                ax2.set_title("Monthly expenses",color="#F8FAFC",fontsize=10)
            fig.tight_layout()
            canvas=FigureCanvasTkAgg(fig,master=self.chart_frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both",expand=True)
        except Exception as exc:
            tk.Label(self.chart_frame,text=f"Charts unavailable. Install matplotlib to enable charts. ({exc})",
                     bg="#111827",fg="#CBD5E1").pack(pady=20)

    def refresh_transactions(self):
        if not hasattr(self,"tx_tree"): return
        for item in self.tx_tree.get_children(): self.tx_tree.delete(item)
        for t in self.db.get_transactions(transaction_type=self.type_var.get() if hasattr(self,"type_var") else "all",
                                          search=self.search_var.get().strip() if hasattr(self,"search_var") else ""):
            self.tx_tree.insert("", "end", values=(t["id"],t["date"],t["description"],t["transaction_type"],
                                t["category"],t["payment_method"],f"₹{t['amount']:,.2f}"),
                                tags=(t["transaction_type"],))

    def new_transaction(self):
        self._transaction_dialog()

    def edit_selected(self):
        selected=self.tx_tree.selection()
        if not selected:
            messagebox.showinfo("Select transaction","Select a transaction to edit."); return
        values=self.tx_tree.item(selected[0],"values")
        tx=next((x for x in self.db.get_transactions() if x["id"]==int(values[0])),None)
        if tx: self._transaction_dialog(tx)

    def _transaction_dialog(self, tx=None):
        win=tk.Toplevel(self); win.title("Edit transaction" if tx else "Add transaction")
        win.configure(bg="#111827"); win.resizable(False,False); win.transient(self); win.grab_set()
        fields={}
        labels=[("Date (YYYY-MM-DD)", "date", tx["date"] if tx else date.today().isoformat()),
                ("Description","description",tx["description"] if tx else ""),
                ("Amount (₹)","amount",str(tx["amount"]) if tx else ""),
                ("Type","transaction_type",tx["transaction_type"] if tx else "expense"),
                ("Category","category",tx["category"] if tx else ""),
                ("Payment method","payment_method",tx["payment_method"] if tx else "Other")]
        for i,(label,key,value) in enumerate(labels):
            tk.Label(win,text=label,bg="#111827",fg="#E2E8F0",anchor="w").grid(row=i,column=0,padx=14,pady=7,sticky="w")
            if key=="transaction_type":
                var=tk.StringVar(value=value); widget=ttk.Combobox(win,textvariable=var,values=["expense","income"],state="readonly",width=27)
                widget.grid(row=i,column=1,padx=14,pady=7); fields[key]=var
            elif key=="category":
                var=tk.StringVar(value=value or "Uncategorized")
                widget=ttk.Combobox(win,textvariable=var,values=CATEGORIES,state="normal",width=27)
                widget.grid(row=i,column=1,padx=14,pady=7); fields[key]=var
            else:
                ent=tk.Entry(win,width=30,bg="#1E293B",fg="#F8FAFC",insertbackground="white",relief="flat")
                ent.insert(0,value); ent.grid(row=i,column=1,padx=14,pady=7); fields[key]=ent
        def save():
            try:
                date_text=fields["date"].get().strip()
                datetime.strptime(date_text,"%Y-%m-%d")
                description=fields["description"].get().strip()
                amount=float(fields["amount"].get().replace(",",""))
                typ=fields["transaction_type"].get()
                category=fields["category"].get().strip()
                payment=fields["payment_method"].get().strip() or "Other"
                if not description: raise ValueError("Description is required.")
                if amount < 0: raise ValueError("Amount must be zero or greater.")
                if not category:
                    category=ai_categorize(description,typ)
                if tx:
                    self.db.update_transaction(tx["id"],date_text,description,amount,typ,category,payment)
                else:
                    self.db.add_transaction(date_text,description,amount,typ,category,payment)
                win.destroy(); self.refresh_all()
            except Exception as exc:
                messagebox.showerror("Could not save transaction",str(exc),parent=win)
        tk.Button(win,text="Save transaction",command=save,bg="#2563EB",fg="white",relief="flat",padx=16,pady=8).grid(row=len(labels),column=0,columnspan=2,pady=15)

    def delete_selected(self):
        selected=self.tx_tree.selection()
        if not selected:
            messagebox.showinfo("Select transaction","Select a transaction to delete."); return
        values=self.tx_tree.item(selected[0],"values")
        if messagebox.askyesno("Confirm deletion",f"Delete transaction #{values[0]} — {values[2]}?"):
            self.db.delete_transaction(int(values[0])); self.refresh_all()

    def do_import(self):
        path=filedialog.askopenfilename(title="Import transaction CSV",filetypes=[("CSV files","*.csv"),("All files","*.*")])
        if not path: return
        try:
            rows,errors=preview_csv(path)
            preview="\\n".join(f"{r['date']} | {r['description'][:25]} | ₹{r['amount']:.2f} | {r['transaction_type']}" for r in rows[:8])
            msg=f"Valid rows: {len(rows)}\\nInvalid rows: {len(errors)}\\n\\nPreview:\\n{preview or '(no valid rows)'}"
            if errors: msg+="\\n\\nFirst errors:\\n"+"\\n".join(errors[:5])
            if not messagebox.askyesno("Review CSV import",msg+"\\n\\nImport valid rows now?"): return
            processed,skipped,errors=import_csv(path,self.db)
            messagebox.showinfo("Import complete",f"Imported: {processed}\\nSkipped/invalid/duplicate: {skipped}")
            self.refresh_all()
        except Exception as exc:
            messagebox.showerror("CSV import failed",str(exc))

    def export_csv(self):
        path=filedialog.asksaveasfilename(defaultextension=".csv",filetypes=[("CSV files","*.csv")],initialfile=f"spendsense_transactions_{self._period()}.csv")
        if not path: return
        rows=self.db.get_transactions()
        try:
            with open(path,"w",newline="",encoding="utf-8-sig") as f:
                writer=csv.DictWriter(f,fieldnames=["date","description","amount","transaction_type","category","payment_method"])
                writer.writeheader()
                for r in rows: writer.writerow({k:r[k] for k in writer.fieldnames})
            messagebox.showinfo("Export complete",f"Exported {len(rows)} transactions.")
        except Exception as exc: messagebox.showerror("Export failed",str(exc))

    def save_budget(self):
        try:
            month=int(self.budget_month.get()); year=int(self.budget_year.get()); amount=float(self.budget_amount.get().replace(",",""))
            category=self.budget_category.get().strip() or "Overall"
            if not 1<=month<=12: raise ValueError("Month must be between 1 and 12.")
            if not 2000<=year<=2200: raise ValueError("Enter a valid year.")
            if amount<0: raise ValueError("Budget cannot be negative.")
            self.db.set_budget(month,year,category,amount)
            self.current_month,self.current_year=month,year
            self.refresh_all()
            messagebox.showinfo("Budget saved",f"{category} budget saved for {year}-{month:02d}.")
        except Exception as exc: messagebox.showerror("Invalid budget",str(exc))

    def refresh_budgets(self):
        if not hasattr(self,"budget_list"): return
        for w in self.budget_list.winfo_children(): w.destroy()
        try:
            month=int(self.budget_month.get()); year=int(self.budget_year.get())
        except ValueError:
            month,year=self.current_month,self.current_year
        budgets=self.db.get_budgets(month,year)
        start=f"{year}-{month:02d}-01"; end=f"{year}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}"
        totals=self.db.totals(start,end); cats=self.db.category_totals(start,end)
        if not budgets:
            self._label(self.budget_list,"No budgets set for this month. Add an overall or category budget above.",
                        fg="#94A3B8").pack(anchor="w",pady=12)
            return
        for b in budgets:
            spent=totals["expenses"] if b["category"]=="Overall" else next((x["total"] for x in cats if x["category"]==b["category"]),0)
            pct=spent/b["budget_limit"]*100 if b["budget_limit"] else 0
            color="#22C55E" if pct<80 else "#FBBF24" if pct<100 else "#F87171"
            row=tk.Frame(self.budget_list,bg="#1E293B",padx=12,pady=10)
            row.pack(fill="x",pady=4)
            tk.Label(row,text=b["category"],bg="#1E293B",fg="#F8FAFC",font=("Segoe UI",11,"bold"),width=18,anchor="w").pack(side="left")
            tk.Label(row,text=f"₹{spent:,.2f} / ₹{b['budget_limit']:,.2f}",bg="#1E293B",fg="#CBD5E1",width=28,anchor="w").pack(side="left")
            canvas=tk.Canvas(row,width=230,height=14,bg="#334155",highlightthickness=0)
            canvas.pack(side="left",padx=10)
            canvas.create_rectangle(0,0,min(230,230*pct/100),14,fill=color,outline="")
            tk.Label(row,text=f"{pct:.0f}%",bg="#1E293B",fg=color,width=7).pack(side="left")

    def make_summary(self):
        try:
            month,year=self.current_month,self.current_year
            start=f"{year}-{month:02d}-01"; end=f"{year}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}"
            totals=self.db.totals(start,end); cats=self.db.category_totals(start,end); budgets=self.db.get_budgets(month,year)
            summary=generate_summary(month,year,totals,cats,budgets)
            self.summary_text.delete("1.0","end"); self.summary_text.insert("1.0",summary)
            self.db.add_insight(month,year,summary); self.refresh_insight_history()
        except Exception as exc: messagebox.showerror("Summary failed",str(exc))

    def refresh_insight_history(self):
        if not hasattr(self,"insight_history"): return
        self.insight_history.delete(0,"end")
        for item in self.db.get_insights():
            self.insight_history.insert("end",f"{item['year']}-{item['month']:02d} | {item['created_at'][:16]} | {item['summary'][:100]}")

    def make_pdf(self):
        path=filedialog.asksaveasfilename(defaultextension=".pdf",filetypes=[("PDF files","*.pdf")],
                                          initialfile=f"spendsense_report_{self._period()}.pdf")
        if not path: return
        try:
            start,end=self._month_range()
            export_pdf(path,self.current_month,self.current_year,self.db.totals(start,end),
                       self.db.category_totals(start,end),self.db.get_transactions(start,end),self.db.get_budgets(self.current_month,self.current_year))
            messagebox.showinfo("PDF report created",f"Report saved to:\\n{path}")
        except Exception as exc: messagebox.showerror("PDF export failed",str(exc))
