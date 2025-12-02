"""Transaction data exporter to CSV and HTML formats."""

import csv
import io
import json
from collections import defaultdict
from datetime import datetime
from typing import Optional

from src.models.transaction import Transaction


class TransactionExporter:
    """Export transactions to various formats."""
    
    @staticmethod
    def to_csv(transactions: list[Transaction], include_header: bool = True) -> str:
        """Export transactions to CSV format."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        if include_header:
            writer.writerow([
                "ID", "Tanggal", "Tipe", "Kategori", "Jumlah", "Keterangan"
            ])
        
        for t in transactions:
            date_str = t.created_at.strftime("%Y-%m-%d %H:%M")
            tipe = "Pemasukan" if t.type == "income" else "Pengeluaran"
            writer.writerow([
                t.id,
                date_str,
                tipe,
                t.category.title(),
                t.amount,
                t.description
            ])
        
        return output.getvalue()
    
    @staticmethod
    def _calculate_category_breakdown(transactions: list[Transaction]) -> dict:
        """Calculate breakdown by category."""
        expense_by_cat = defaultdict(float)
        income_by_cat = defaultdict(float)
        
        for t in transactions:
            if t.type == "expense":
                expense_by_cat[t.category.title()] += t.amount
            else:
                income_by_cat[t.category.title()] += t.amount
        
        return {
            "expense": dict(sorted(expense_by_cat.items(), key=lambda x: -x[1])),
            "income": dict(sorted(income_by_cat.items(), key=lambda x: -x[1]))
        }
    
    @staticmethod
    def to_html(
        transactions: list[Transaction],
        title: str = "Laporan Keuangan",
        summary: Optional[dict] = None
    ) -> str:
        """Export transactions to HTML format with charts and category breakdown."""
        
        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        balance = total_income - total_expense
        
        if summary:
            total_income = summary.get("income", total_income)
            total_expense = summary.get("expense", total_expense)
            balance = summary.get("balance", balance)
        
        # Calculate category breakdown
        breakdown = TransactionExporter._calculate_category_breakdown(transactions)
        
        # Format currency
        def fmt(amount: float) -> str:
            return f"Rp {amount:,.0f}".replace(",", ".")
        
        # Generate expense category cards
        expense_cards = ""
        for cat, amount in breakdown["expense"].items():
            pct = (amount / total_expense * 100) if total_expense > 0 else 0
            expense_cards += f"""
            <div class="category-card expense">
                <div class="cat-header">
                    <span class="cat-name">{cat}</span>
                    <span class="cat-pct">{pct:.1f}%</span>
                </div>
                <div class="cat-amount">-{fmt(amount)}</div>
                <div class="cat-bar"><div class="cat-fill expense" style="width:{pct}%"></div></div>
            </div>"""
        
        # Generate income category cards
        income_cards = ""
        for cat, amount in breakdown["income"].items():
            pct = (amount / total_income * 100) if total_income > 0 else 0
            income_cards += f"""
            <div class="category-card income">
                <div class="cat-header">
                    <span class="cat-name">{cat}</span>
                    <span class="cat-pct">{pct:.1f}%</span>
                </div>
                <div class="cat-amount">+{fmt(amount)}</div>
                <div class="cat-bar"><div class="cat-fill income" style="width:{pct}%"></div></div>
            </div>"""
        
        # Generate transaction rows
        tx_rows = ""
        for t in transactions:
            date_str = t.created_at.strftime("%d/%m/%y")
            time_str = t.created_at.strftime("%H:%M")
            tipe_class = "income" if t.type == "income" else "expense"
            sign = "+" if t.type == "income" else "-"
            emoji = "💰" if t.type == "income" else "💸"
            tx_rows += f"""
            <div class="tx-card {tipe_class}">
                <div class="tx-icon">{emoji}</div>
                <div class="tx-info">
                    <div class="tx-desc">{t.description}</div>
                    <div class="tx-meta">
                        <span class="tx-cat">{t.category.title()}</span>
                        <span class="tx-date">{date_str} {time_str}</span>
                    </div>
                </div>
                <div class="tx-amount {tipe_class}">{sign}{fmt(t.amount)}</div>
            </div>"""
        
        # Prepare chart data
        expense_labels = json.dumps(list(breakdown["expense"].keys()))
        expense_values = json.dumps(list(breakdown["expense"].values()))
        income_labels = json.dumps(list(breakdown["income"].keys()))
        income_values = json.dumps(list(breakdown["income"].values()))
        
        balance_class = "positive" if balance >= 0 else "negative"
        balance_sign = "+" if balance >= 0 else ""
        
        html = f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="theme-color" content="#1a1a2e">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #6366f1;
            --income: #10b981;
            --expense: #ef4444;
            --bg: #0f0f1a;
            --card: #1a1a2e;
            --card-hover: #252542;
            --text: #ffffff;
            --text-muted: #9ca3af;
            --border: #2d2d4a;
        }}
        
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg);
            color: var(--text);
            min-height: 100vh;
            line-height: 1.5;
            -webkit-font-smoothing: antialiased;
        }}
        
        .container {{
            max-width: 100%;
            margin: 0 auto;
            padding: 0;
        }}
        
        /* Header */
        .header {{
            background: linear-gradient(135deg, var(--card) 0%, #16213e 100%);
            padding: 24px 20px;
            text-align: center;
            position: sticky;
            top: 0;
            z-index: 100;
            border-bottom: 1px solid var(--border);
        }}
        .header h1 {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .header .subtitle {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        
        /* Summary Cards */
        .summary {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 12px;
            padding: 16px;
        }}
        .summary-card {{
            background: var(--card);
            border-radius: 16px;
            padding: 16px 12px;
            text-align: center;
            border: 1px solid var(--border);
        }}
        .summary-card .label {{
            font-size: 11px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }}
        .summary-card .value {{
            font-size: 16px;
            font-weight: 700;
        }}
        .summary-card.income .value {{ color: var(--income); }}
        .summary-card.expense .value {{ color: var(--expense); }}
        .summary-card.balance .value.positive {{ color: var(--income); }}
        .summary-card.balance .value.negative {{ color: var(--expense); }}
        
        /* Navigation Tabs */
        .nav-tabs {{
            display: flex;
            background: var(--card);
            padding: 8px;
            margin: 0 16px;
            border-radius: 12px;
            gap: 8px;
        }}
        .nav-tab {{
            flex: 1;
            padding: 12px;
            text-align: center;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            color: var(--text-muted);
        }}
        .nav-tab:hover {{ background: var(--card-hover); }}
        .nav-tab.active {{
            background: var(--primary);
            color: white;
        }}
        
        /* Tab Content */
        .tab-content {{ display: none; padding: 16px; }}
        .tab-content.active {{ display: block; }}
        
        /* Section Title */
        .section-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        /* Charts */
        .charts-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 16px;
            margin-bottom: 24px;
        }}
        .chart-card {{
            background: var(--card);
            border-radius: 16px;
            padding: 16px;
            border: 1px solid var(--border);
        }}
        .chart-card h3 {{
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 16px;
            text-align: center;
        }}
        .chart-container {{
            position: relative;
            height: 200px;
        }}
        
        /* Category Cards */
        .category-section {{
            margin-bottom: 24px;
        }}
        .category-grid {{
            display: grid;
            grid-template-columns: 1fr;
            gap: 12px;
        }}
        .category-card {{
            background: var(--card);
            border-radius: 12px;
            padding: 16px;
            border: 1px solid var(--border);
        }}
        .cat-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }}
        .cat-name {{
            font-size: 14px;
            font-weight: 500;
        }}
        .cat-pct {{
            font-size: 12px;
            color: var(--text-muted);
        }}
        .cat-amount {{
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 12px;
        }}
        .category-card.expense .cat-amount {{ color: var(--expense); }}
        .category-card.income .cat-amount {{ color: var(--income); }}
        .cat-bar {{
            height: 6px;
            background: var(--border);
            border-radius: 3px;
            overflow: hidden;
        }}
        .cat-fill {{
            height: 100%;
            border-radius: 3px;
            transition: width 0.5s ease;
        }}
        .cat-fill.expense {{ background: linear-gradient(90deg, var(--expense), #f87171); }}
        .cat-fill.income {{ background: linear-gradient(90deg, var(--income), #34d399); }}
        
        /* Transaction Cards */
        .tx-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        .tx-card {{
            background: var(--card);
            border-radius: 12px;
            padding: 14px 16px;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid var(--border);
            transition: background 0.2s;
        }}
        .tx-card:active {{ background: var(--card-hover); }}
        .tx-icon {{
            font-size: 24px;
            width: 40px;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            background: var(--bg);
        }}
        .tx-info {{
            flex: 1;
            min-width: 0;
        }}
        .tx-desc {{
            font-size: 14px;
            font-weight: 500;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .tx-meta {{
            display: flex;
            gap: 8px;
            margin-top: 4px;
            font-size: 12px;
            color: var(--text-muted);
        }}
        .tx-cat {{
            background: var(--bg);
            padding: 2px 8px;
            border-radius: 4px;
        }}
        .tx-amount {{
            font-size: 14px;
            font-weight: 700;
            white-space: nowrap;
        }}
        .tx-amount.income {{ color: var(--income); }}
        .tx-amount.expense {{ color: var(--expense); }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 24px 16px;
            color: var(--text-muted);
            font-size: 12px;
            border-top: 1px solid var(--border);
            margin-top: 16px;
        }}
        
        /* Empty State */
        .empty-state {{
            text-align: center;
            padding: 40px 20px;
            color: var(--text-muted);
        }}
        .empty-state .icon {{ font-size: 48px; margin-bottom: 16px; }}
        
        /* Desktop Styles */
        @media (min-width: 768px) {{
            .container {{
                max-width: 800px;
                margin: 20px auto;
                border-radius: 24px;
                overflow: hidden;
                box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
            }}
            .header {{ padding: 32px; }}
            .header h1 {{ font-size: 28px; }}
            .summary {{ padding: 24px; gap: 16px; }}
            .summary-card {{ padding: 24px; }}
            .summary-card .label {{ font-size: 12px; }}
            .summary-card .value {{ font-size: 24px; }}
            .nav-tabs {{ margin: 0 24px; }}
            .tab-content {{ padding: 24px; }}
            .charts-grid {{ grid-template-columns: repeat(2, 1fr); }}
            .chart-container {{ height: 250px; }}
            .category-grid {{ grid-template-columns: repeat(2, 1fr); }}
        }}
        
        @media (min-width: 1024px) {{
            .container {{ max-width: 1000px; }}
        }}
        
        /* Print Styles */
        @media print {{
            body {{ background: white; color: black; }}
            .container {{ box-shadow: none; margin: 0; max-width: 100%; }}
            .nav-tabs {{ display: none; }}
            .tab-content {{ display: block !important; }}
            .header {{ background: #f3f4f6; color: black; }}
            .summary-card, .chart-card, .category-card, .tx-card {{
                background: #f9fafb;
                border-color: #e5e7eb;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 {title}</h1>
            <div class="subtitle">Diekspor {datetime.now().strftime("%d %B %Y, %H:%M")}</div>
        </div>
        
        <div class="summary">
            <div class="summary-card income">
                <div class="label">Pemasukan</div>
                <div class="value">+{fmt(total_income)}</div>
            </div>
            <div class="summary-card expense">
                <div class="label">Pengeluaran</div>
                <div class="value">-{fmt(total_expense)}</div>
            </div>
            <div class="summary-card balance">
                <div class="label">Saldo</div>
                <div class="value {balance_class}">{balance_sign}{fmt(balance)}</div>
            </div>
        </div>
        
        <div class="nav-tabs">
            <div class="nav-tab active" onclick="showTab('overview')">📊 Ringkasan</div>
            <div class="nav-tab" onclick="showTab('transactions')">📋 Transaksi</div>
        </div>
        
        <div id="overview" class="tab-content active">
            <div class="charts-grid">
                <div class="chart-card">
                    <h3>💸 Pengeluaran</h3>
                    <div class="chart-container">
                        <canvas id="expenseChart"></canvas>
                    </div>
                </div>
                <div class="chart-card">
                    <h3>💰 Pemasukan</h3>
                    <div class="chart-container">
                        <canvas id="incomeChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="category-section">
                <div class="section-title">💸 Detail Pengeluaran</div>
                <div class="category-grid">
                    {expense_cards if expense_cards else '<div class="empty-state"><div class="icon">📭</div><div>Tidak ada pengeluaran</div></div>'}
                </div>
            </div>
            
            <div class="category-section">
                <div class="section-title">💰 Detail Pemasukan</div>
                <div class="category-grid">
                    {income_cards if income_cards else '<div class="empty-state"><div class="icon">📭</div><div>Tidak ada pemasukan</div></div>'}
                </div>
            </div>
        </div>
        
        <div id="transactions" class="tab-content">
            <div class="section-title">📋 Semua Transaksi ({len(transactions)})</div>
            <div class="tx-list">
                {tx_rows if tx_rows else '<div class="empty-state"><div class="icon">📭</div><div>Tidak ada transaksi</div></div>'}
            </div>
        </div>
        
        <div class="footer">
            <p>💰 Money Tracker Bot</p>
            <p>{len(transactions)} transaksi tercatat</p>
        </div>
    </div>
    
    <script>
        function showTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
            document.getElementById(tabId).classList.add('active');
            event.target.classList.add('active');
        }}
        
        const chartColors = [
            '#ef4444', '#f97316', '#f59e0b', '#84cc16', '#22c55e',
            '#14b8a6', '#06b6d4', '#3b82f6', '#6366f1', '#8b5cf6',
            '#a855f7', '#d946ef', '#ec4899', '#f43f5e'
        ];
        
        const chartOptions = {{
            responsive: true,
            maintainAspectRatio: false,
            plugins: {{
                legend: {{
                    position: 'bottom',
                    labels: {{
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle',
                        font: {{ size: 11 }},
                        color: '#9ca3af'
                    }}
                }}
            }},
            cutout: '60%'
        }};
        
        const expenseLabels = {expense_labels};
        const expenseValues = {expense_values};
        if (expenseLabels.length > 0) {{
            new Chart(document.getElementById('expenseChart'), {{
                type: 'doughnut',
                data: {{
                    labels: expenseLabels,
                    datasets: [{{
                        data: expenseValues,
                        backgroundColor: chartColors.slice(0, expenseLabels.length),
                        borderWidth: 0
                    }}]
                }},
                options: chartOptions
            }});
        }}
        
        const incomeLabels = {income_labels};
        const incomeValues = {income_values};
        if (incomeLabels.length > 0) {{
            new Chart(document.getElementById('incomeChart'), {{
                type: 'doughnut',
                data: {{
                    labels: incomeLabels,
                    datasets: [{{
                        data: incomeValues,
                        backgroundColor: ['#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5'],
                        borderWidth: 0
                    }}]
                }},
                options: chartOptions
            }});
        }}
    </script>
</body>
</html>"""
        
        return html
