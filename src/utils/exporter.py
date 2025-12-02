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
            writer.writerow(["ID", "Tanggal", "Tipe", "Kategori", "Jumlah", "Keterangan"])
        
        for t in transactions:
            date_str = t.created_at.strftime("%Y-%m-%d %H:%M")
            tipe = "Pemasukan" if t.type == "income" else "Pengeluaran"
            writer.writerow([t.id, date_str, tipe, t.category.title(), t.amount, t.description])
        
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
    def to_html(transactions: list[Transaction], title: str = "Laporan Keuangan", 
                summary: Optional[dict] = None) -> str:
        """Export transactions to interactive HTML with filters."""
        return TransactionExporter._generate_html(transactions, title, summary)

    @staticmethod
    def _generate_html(transactions: list[Transaction], title: str, summary: Optional[dict]) -> str:
        # Calculate totals
        total_income = sum(t.amount for t in transactions if t.type == "income")
        total_expense = sum(t.amount for t in transactions if t.type == "expense")
        balance = total_income - total_expense
        
        if summary:
            total_income = summary.get("income", total_income)
            total_expense = summary.get("expense", total_expense)
            balance = summary.get("balance", balance)
        
        breakdown = TransactionExporter._calculate_category_breakdown(transactions)
        
        def fmt(amount: float) -> str:
            return f"Rp {amount:,.0f}".replace(",", ".")
        
        # Get unique categories
        all_categories = sorted(set(t.category.title() for t in transactions))
        category_options = "".join(f'<option value="{c}">{c}</option>' for c in all_categories)
        
        # Generate transaction data as JSON for JavaScript filtering
        tx_data = []
        for t in transactions:
            tx_data.append({
                "id": t.id,
                "date": t.created_at.isoformat(),
                "type": t.type,
                "category": t.category.title(),
                "amount": t.amount,
                "description": t.description
            })
        tx_json = json.dumps(tx_data)
        
        # Chart data
        expense_labels = json.dumps(list(breakdown["expense"].keys()))
        expense_values = json.dumps(list(breakdown["expense"].values()))
        income_labels = json.dumps(list(breakdown["income"].keys()))
        income_values = json.dumps(list(breakdown["income"].values()))
        
        balance_class = "positive" if balance >= 0 else "negative"
        balance_sign = "+" if balance >= 0 else ""
        
        html_part1 = f'''<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
    <meta name="theme-color" content="#0f0f1a">
    <title>{title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
'''
        return html_part1 + TransactionExporter._get_styles() + TransactionExporter._get_body(
            title, total_income, total_expense, balance, balance_class, balance_sign, 
            fmt, category_options, len(transactions), tx_json, expense_labels, 
            expense_values, income_labels, income_values
        )

    @staticmethod
    def _get_styles() -> str:
        return '''<style>
:root{--primary:#6366f1;--income:#10b981;--expense:#ef4444;--bg:#0f0f1a;--card:#1a1a2e;--card-hover:#252542;--text:#fff;--text-muted:#9ca3af;--border:#2d2d4a}
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh;line-height:1.5}
.container{max-width:100%;margin:0 auto}
.header{background:linear-gradient(135deg,var(--card),#16213e);padding:20px;text-align:center;position:sticky;top:0;z-index:100;border-bottom:1px solid var(--border)}
.header h1{font-size:18px;margin-bottom:4px}
.header .subtitle{font-size:11px;color:var(--text-muted)}
.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:12px}
.summary-card{background:var(--card);border-radius:12px;padding:14px 10px;text-align:center;border:1px solid var(--border)}
.summary-card .label{font-size:10px;color:var(--text-muted);text-transform:uppercase;margin-bottom:6px}
.summary-card .value{font-size:14px;font-weight:700}
.summary-card.income .value{color:var(--income)}
.summary-card.expense .value{color:var(--expense)}
.summary-card.balance .value.positive{color:var(--income)}
.summary-card.balance .value.negative{color:var(--expense)}
.filters{padding:12px;background:var(--card);margin:12px;border-radius:12px;border:1px solid var(--border)}
.filter-row{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
.filter-row:last-child{margin-bottom:0}
.filter-group{flex:1;min-width:120px}
.filter-label{font-size:10px;color:var(--text-muted);margin-bottom:4px;text-transform:uppercase}
select,input[type="date"]{width:100%;padding:10px;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text);font-size:13px}
.filter-btn{padding:10px 16px;border-radius:8px;border:none;font-size:12px;font-weight:600;cursor:pointer;transition:all .2s}
.filter-btn.active{background:var(--primary);color:#fff}
.filter-btn:not(.active){background:var(--bg);color:var(--text-muted);border:1px solid var(--border)}
.type-filters{display:flex;gap:6px}
.type-btn{flex:1;padding:8px;border-radius:8px;border:1px solid var(--border);background:var(--bg);color:var(--text-muted);font-size:11px;cursor:pointer;text-align:center}
.type-btn.active{border-color:var(--primary);color:var(--primary);background:rgba(99,102,241,.1)}
.type-btn.income.active{border-color:var(--income);color:var(--income);background:rgba(16,185,129,.1)}
.type-btn.expense.active{border-color:var(--expense);color:var(--expense);background:rgba(239,68,68,.1)}
.stats-bar{display:flex;justify-content:space-between;padding:12px;background:var(--card);margin:0 12px;border-radius:8px;font-size:11px;color:var(--text-muted)}
.stats-bar span{display:flex;align-items:center;gap:4px}
.nav-tabs{display:flex;background:var(--card);padding:6px;margin:12px;border-radius:10px;gap:6px}
.nav-tab{flex:1;padding:10px;text-align:center;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;color:var(--text-muted)}
.nav-tab.active{background:var(--primary);color:#fff}
.tab-content{display:none;padding:12px}
.tab-content.active{display:block}
.section-title{font-size:14px;font-weight:600;margin-bottom:12px;display:flex;align-items:center;gap:6px}
.charts-grid{display:grid;grid-template-columns:1fr;gap:12px;margin-bottom:16px}
.chart-card{background:var(--card);border-radius:12px;padding:14px;border:1px solid var(--border)}
.chart-card h3{font-size:13px;margin-bottom:12px;text-align:center}
.chart-container{height:180px;position:relative}
.category-grid{display:grid;grid-template-columns:1fr;gap:8px}
.cat-card{background:var(--card);border-radius:10px;padding:12px;border:1px solid var(--border);cursor:pointer;transition:all .2s}
.cat-card:hover{background:var(--card-hover)}
.cat-card.selected{border-color:var(--primary)}
.cat-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px}
.cat-name{font-size:13px;font-weight:500}
.cat-pct{font-size:11px;color:var(--text-muted)}
.cat-amount{font-size:16px;font-weight:700;margin-bottom:8px}
.cat-card.expense .cat-amount{color:var(--expense)}
.cat-card.income .cat-amount{color:var(--income)}
.cat-bar{height:4px;background:var(--border);border-radius:2px;overflow:hidden}
.cat-fill{height:100%;border-radius:2px}
.cat-fill.expense{background:linear-gradient(90deg,var(--expense),#f87171)}
.cat-fill.income{background:linear-gradient(90deg,var(--income),#34d399)}
.tx-list{display:flex;flex-direction:column;gap:6px}
.tx-card{background:var(--card);border-radius:10px;padding:12px;display:flex;align-items:center;gap:10px;border:1px solid var(--border)}
.tx-icon{font-size:20px;width:36px;height:36px;display:flex;align-items:center;justify-content:center;border-radius:8px;background:var(--bg)}
.tx-info{flex:1;min-width:0}
.tx-desc{font-size:13px;font-weight:500;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.tx-meta{display:flex;gap:6px;margin-top:3px;font-size:11px;color:var(--text-muted);flex-wrap:wrap}
.tx-tag{background:var(--bg);padding:2px 6px;border-radius:4px;font-size:10px}
.tx-amount{font-size:13px;font-weight:700;white-space:nowrap}
.tx-amount.income{color:var(--income)}
.tx-amount.expense{color:var(--expense)}
.empty-state{text-align:center;padding:30px;color:var(--text-muted)}
.empty-state .icon{font-size:40px;margin-bottom:12px}
.footer{text-align:center;padding:20px;color:var(--text-muted);font-size:11px;border-top:1px solid var(--border);margin-top:12px}
@media(min-width:768px){.container{max-width:900px;margin:20px auto;border-radius:20px;overflow:hidden;box-shadow:0 25px 50px -12px rgba(0,0,0,.5)}.header{padding:28px}.header h1{font-size:24px}.summary{padding:20px;gap:16px}.summary-card{padding:20px}.summary-card .value{font-size:20px}.filters{margin:16px 20px}.charts-grid{grid-template-columns:repeat(2,1fr)}.chart-container{height:220px}.category-grid{grid-template-columns:repeat(2,1fr)}.tab-content{padding:20px}}
@media print{body{background:#fff;color:#000}.container{box-shadow:none}.header{background:#f3f4f6;color:#000}.filters{display:none}.nav-tabs{display:none}.tab-content{display:block!important}}
</style>'''

    @staticmethod
    def _get_body(title, total_income, total_expense, balance, balance_class, balance_sign, 
                  fmt, category_options, tx_count, tx_json, expense_labels, expense_values, 
                  income_labels, income_values) -> str:
        now = datetime.now()
        return f'''</head>
<body>
<div class="container">
    <div class="header">
        <h1>💰 {title}</h1>
        <div class="subtitle">Diekspor {now.strftime("%d %B %Y, %H:%M")}</div>
    </div>
    
    <div class="summary">
        <div class="summary-card income">
            <div class="label">Pemasukan</div>
            <div class="value" id="filteredIncome">+{fmt(total_income)}</div>
        </div>
        <div class="summary-card expense">
            <div class="label">Pengeluaran</div>
            <div class="value" id="filteredExpense">-{fmt(total_expense)}</div>
        </div>
        <div class="summary-card balance">
            <div class="label">Saldo</div>
            <div class="value {balance_class}" id="filteredBalance">{balance_sign}{fmt(balance)}</div>
        </div>
    </div>
    
    <div class="filters">
        <div class="filter-row">
            <div class="filter-group">
                <div class="filter-label">Periode</div>
                <select id="periodFilter" onchange="applyFilters()">
                    <option value="all">Semua Waktu</option>
                    <option value="today">Hari Ini</option>
                    <option value="week">Minggu Ini</option>
                    <option value="month">Bulan Ini</option>
                    <option value="year">Tahun Ini</option>
                    <option value="custom">Kustom...</option>
                </select>
            </div>
            <div class="filter-group">
                <div class="filter-label">Kategori</div>
                <select id="categoryFilter" onchange="applyFilters()">
                    <option value="all">Semua Kategori</option>
                    {category_options}
                </select>
            </div>
        </div>
        <div class="filter-row" id="customDateRow" style="display:none">
            <div class="filter-group">
                <div class="filter-label">Dari</div>
                <input type="date" id="dateFrom" onchange="applyFilters()">
            </div>
            <div class="filter-group">
                <div class="filter-label">Sampai</div>
                <input type="date" id="dateTo" onchange="applyFilters()">
            </div>
        </div>
        <div class="filter-row">
            <div class="type-filters" style="width:100%">
                <div class="type-btn active" data-type="all" onclick="setTypeFilter('all')">📊 Semua</div>
                <div class="type-btn income" data-type="income" onclick="setTypeFilter('income')">💰 Pemasukan</div>
                <div class="type-btn expense" data-type="expense" onclick="setTypeFilter('expense')">💸 Pengeluaran</div>
            </div>
        </div>
    </div>
    
    <div class="stats-bar">
        <span>📝 <span id="txCount">{tx_count}</span> transaksi</span>
        <span id="dateRange"></span>
    </div>
    
    <div class="nav-tabs">
        <div class="nav-tab active" onclick="showTab('overview')">📊 Ringkasan</div>
        <div class="nav-tab" onclick="showTab('transactions')">📋 Transaksi</div>
    </div>
    
    <div id="overview" class="tab-content active">
        <div class="charts-grid">
            <div class="chart-card">
                <h3>💸 Pengeluaran</h3>
                <div class="chart-container"><canvas id="expenseChart"></canvas></div>
            </div>
            <div class="chart-card">
                <h3>💰 Pemasukan</h3>
                <div class="chart-container"><canvas id="incomeChart"></canvas></div>
            </div>
        </div>
        <div class="section-title">💸 Pengeluaran per Kategori</div>
        <div class="category-grid" id="expenseCategories"></div>
        <div class="section-title" style="margin-top:16px">💰 Pemasukan per Kategori</div>
        <div class="category-grid" id="incomeCategories"></div>
    </div>
    
    <div id="transactions" class="tab-content">
        <div class="section-title">📋 Daftar Transaksi</div>
        <div class="tx-list" id="txList"></div>
    </div>
    
    <div class="footer">
        <p>💰 Money Tracker Bot</p>
        <p>Total {tx_count} transaksi tercatat</p>
    </div>
</div>

<script>
const allTransactions = {tx_json};
let filteredTx = [...allTransactions];
let currentTypeFilter = 'all';
let expenseChart, incomeChart;

const chartColors = ['#ef4444','#f97316','#f59e0b','#84cc16','#22c55e','#14b8a6','#06b6d4','#3b82f6','#6366f1','#8b5cf6'];
const incomeColors = ['#10b981','#34d399','#6ee7b7','#a7f3d0','#d1fae5'];

function fmt(n) {{ return 'Rp ' + n.toLocaleString('id-ID').replace(/,/g, '.'); }}

function showTab(id) {{
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.nav-tab').forEach(t => t.classList.remove('active'));
    document.getElementById(id).classList.add('active');
    event.target.classList.add('active');
}}

function setTypeFilter(type) {{
    currentTypeFilter = type;
    document.querySelectorAll('.type-btn').forEach(b => {{
        b.classList.toggle('active', b.dataset.type === type);
    }});
    applyFilters();
}}

function applyFilters() {{
    const period = document.getElementById('periodFilter').value;
    const category = document.getElementById('categoryFilter').value;
    const customRow = document.getElementById('customDateRow');
    
    customRow.style.display = period === 'custom' ? 'flex' : 'none';
    
    const now = new Date();
    let startDate = null, endDate = new Date(now);
    
    if (period === 'today') {{
        startDate = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    }} else if (period === 'week') {{
        startDate = new Date(now);
        startDate.setDate(now.getDate() - now.getDay());
    }} else if (period === 'month') {{
        startDate = new Date(now.getFullYear(), now.getMonth(), 1);
    }} else if (period === 'year') {{
        startDate = new Date(now.getFullYear(), 0, 1);
    }} else if (period === 'custom') {{
        const from = document.getElementById('dateFrom').value;
        const to = document.getElementById('dateTo').value;
        if (from) startDate = new Date(from);
        if (to) endDate = new Date(to + 'T23:59:59');
    }}
    
    filteredTx = allTransactions.filter(t => {{
        const txDate = new Date(t.date);
        if (startDate && txDate < startDate) return false;
        if (endDate && txDate > endDate) return false;
        if (category !== 'all' && t.category !== category) return false;
        if (currentTypeFilter !== 'all' && t.type !== currentTypeFilter) return false;
        return true;
    }});
    
    updateDisplay();
}}

function updateDisplay() {{
    const income = filteredTx.filter(t => t.type === 'income').reduce((s, t) => s + t.amount, 0);
    const expense = filteredTx.filter(t => t.type === 'expense').reduce((s, t) => s + t.amount, 0);
    const balance = income - expense;
    
    document.getElementById('filteredIncome').textContent = '+' + fmt(income);
    document.getElementById('filteredExpense').textContent = '-' + fmt(expense);
    const balEl = document.getElementById('filteredBalance');
    balEl.textContent = (balance >= 0 ? '+' : '') + fmt(balance);
    balEl.className = 'value ' + (balance >= 0 ? 'positive' : 'negative');
    document.getElementById('txCount').textContent = filteredTx.length;
    
    updateCharts();
    updateCategories();
    updateTransactionList();
}}

function updateCharts() {{
    const expenseByCategory = {{}};
    const incomeByCategory = {{}};
    
    filteredTx.forEach(t => {{
        if (t.type === 'expense') expenseByCategory[t.category] = (expenseByCategory[t.category] || 0) + t.amount;
        else incomeByCategory[t.category] = (incomeByCategory[t.category] || 0) + t.amount;
    }});
    
    const expLabels = Object.keys(expenseByCategory);
    const expValues = Object.values(expenseByCategory);
    const incLabels = Object.keys(incomeByCategory);
    const incValues = Object.values(incomeByCategory);
    
    if (expenseChart) expenseChart.destroy();
    if (incomeChart) incomeChart.destroy();
    
    const opts = {{responsive:true,maintainAspectRatio:false,plugins:{{legend:{{position:'bottom',labels:{{padding:8,usePointStyle:true,font:{{size:10}},color:'#9ca3af'}}}}}},cutout:'55%'}};
    
    if (expLabels.length) {{
        expenseChart = new Chart(document.getElementById('expenseChart'), {{
            type:'doughnut',data:{{labels:expLabels,datasets:[{{data:expValues,backgroundColor:chartColors.slice(0,expLabels.length),borderWidth:0}}]}},options:opts
        }});
    }}
    if (incLabels.length) {{
        incomeChart = new Chart(document.getElementById('incomeChart'), {{
            type:'doughnut',data:{{labels:incLabels,datasets:[{{data:incValues,backgroundColor:incomeColors.slice(0,incLabels.length),borderWidth:0}}]}},options:opts
        }});
    }}
}}

function updateCategories() {{
    const expenseByCategory = {{}};
    const incomeByCategory = {{}};
    let totalExp = 0, totalInc = 0;
    
    filteredTx.forEach(t => {{
        if (t.type === 'expense') {{ expenseByCategory[t.category] = (expenseByCategory[t.category] || 0) + t.amount; totalExp += t.amount; }}
        else {{ incomeByCategory[t.category] = (incomeByCategory[t.category] || 0) + t.amount; totalInc += t.amount; }}
    }});
    
    const expHtml = Object.entries(expenseByCategory).sort((a,b) => b[1]-a[1]).map(([cat, amt]) => {{
        const pct = totalExp ? (amt/totalExp*100).toFixed(1) : 0;
        return `<div class="cat-card expense" onclick="filterByCategory('${{cat}}')"><div class="cat-header"><span class="cat-name">${{cat}}</span><span class="cat-pct">${{pct}}%</span></div><div class="cat-amount">-${{fmt(amt)}}</div><div class="cat-bar"><div class="cat-fill expense" style="width:${{pct}}%"></div></div></div>`;
    }}).join('') || '<div class="empty-state"><div class="icon">📭</div>Tidak ada data</div>';
    
    const incHtml = Object.entries(incomeByCategory).sort((a,b) => b[1]-a[1]).map(([cat, amt]) => {{
        const pct = totalInc ? (amt/totalInc*100).toFixed(1) : 0;
        return `<div class="cat-card income" onclick="filterByCategory('${{cat}}')"><div class="cat-header"><span class="cat-name">${{cat}}</span><span class="cat-pct">${{pct}}%</span></div><div class="cat-amount">+${{fmt(amt)}}</div><div class="cat-bar"><div class="cat-fill income" style="width:${{pct}}%"></div></div></div>`;
    }}).join('') || '<div class="empty-state"><div class="icon">📭</div>Tidak ada data</div>';
    
    document.getElementById('expenseCategories').innerHTML = expHtml;
    document.getElementById('incomeCategories').innerHTML = incHtml;
}}

function filterByCategory(cat) {{
    document.getElementById('categoryFilter').value = cat;
    applyFilters();
}}

function updateTransactionList() {{
    const sorted = [...filteredTx].sort((a,b) => new Date(b.date) - new Date(a.date));
    const html = sorted.map(t => {{
        const d = new Date(t.date);
        const dateStr = d.toLocaleDateString('id-ID', {{day:'2-digit',month:'short',year:'2-digit'}});
        const timeStr = d.toLocaleTimeString('id-ID', {{hour:'2-digit',minute:'2-digit'}});
        const emoji = t.type === 'income' ? '💰' : '💸';
        const sign = t.type === 'income' ? '+' : '-';
        return `<div class="tx-card"><div class="tx-icon">${{emoji}}</div><div class="tx-info"><div class="tx-desc">${{t.description}}</div><div class="tx-meta"><span class="tx-tag">${{t.category}}</span><span>${{dateStr}} ${{timeStr}}</span><span>ID: ${{t.id}}</span></div></div><div class="tx-amount ${{t.type}}">${{sign}}${{fmt(t.amount)}}</div></div>`;
    }}).join('') || '<div class="empty-state"><div class="icon">📭</div>Tidak ada transaksi</div>';
    document.getElementById('txList').innerHTML = html;
}}

// Initialize
document.addEventListener('DOMContentLoaded', () => {{
    applyFilters();
}});
</script>
</body>
</html>'''
