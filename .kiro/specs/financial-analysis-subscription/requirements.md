# Requirements Document

## Introduction

Fitur tambahan untuk Bot Telegram Money Tracker yang mencakup: (1) Analisis kesehatan keuangan dengan saran perbaikan, (2) Manajemen subscription/langganan seperti Netflix, Spotify, VPS, domain dengan tracking tanggal mulai, berakhir, dan status aktif, serta (3) Export laporan ke format HTML interaktif yang dapat didownload.

## Glossary

- **Bot**: Aplikasi Telegram bot yang menerima dan memproses pesan pengguna
- **Financial Analysis**: Analisis kesehatan keuangan berdasarkan data transaksi pengguna
- **Subscription**: Layanan berlangganan seperti Netflix, Spotify, VPS, domain yang memiliki periode aktif
- **Health Score**: Skor kesehatan keuangan dalam skala 0-100
- **Expense Ratio**: Rasio pengeluaran terhadap pemasukan
- **HTML Report**: Laporan keuangan dalam format HTML interaktif yang dapat didownload

## Requirements

### Requirement 1

**User Story:** As a user, I want to see my financial health analysis, so that I can understand how well I manage my money and get suggestions for improvement.

#### Acceptance Criteria

1. WHEN a user sends "/analysis" command THEN the Bot SHALL calculate and display a financial health score (0-100) based on income, expense, and savings ratio
2. WHEN displaying financial analysis THEN the Bot SHALL show expense breakdown by category with percentage
3. WHEN the expense ratio exceeds 80% of income THEN the Bot SHALL provide a warning message about overspending
4. WHEN analyzing finances THEN the Bot SHALL compare current month spending with previous month and show the trend
5. WHEN the user has insufficient data (less than 5 transactions) THEN the Bot SHALL inform the user that more data is needed for accurate analysis

### Requirement 2

**User Story:** As a user, I want to receive personalized financial suggestions, so that I can improve my spending habits.

#### Acceptance Criteria

1. WHEN generating analysis THEN the Bot SHALL identify the top 3 expense categories and suggest reduction strategies
2. WHEN a category exceeds 30% of total expenses THEN the Bot SHALL flag it as a high-spending category with specific advice
3. WHEN the user has positive savings THEN the Bot SHALL congratulate and suggest investment options
4. WHEN the user has negative balance THEN the Bot SHALL provide actionable tips to reduce expenses

### Requirement 3

**User Story:** As a user, I want to track my subscriptions and recurring payments, so that I can manage my monthly commitments effectively.

#### Acceptance Criteria

1. WHEN a user sends "/addsub [name] [amount] [start_date] [end_date]" command THEN the Bot SHALL create a new subscription record with the provided details
2. WHEN a user sends "/subs" command THEN the Bot SHALL display all active subscriptions with name, amount, start date, end date, and days remaining
3. WHEN a subscription is within 7 days of expiration THEN the Bot SHALL mark it with a warning indicator
4. WHEN a subscription has expired THEN the Bot SHALL mark it as inactive and display it separately
5. WHEN a user sends "/delsub [id]" command THEN the Bot SHALL remove the specified subscription from the database

### Requirement 4

**User Story:** As a user, I want to categorize my subscriptions, so that I can see how much I spend on different types of services.

#### Acceptance Criteria

1. WHEN adding a subscription THEN the Bot SHALL allow optional category specification (streaming, hosting, domain, software, other)
2. WHEN displaying subscriptions THEN the Bot SHALL group them by category with subtotals
3. WHEN a user sends "/subcost" command THEN the Bot SHALL display total monthly subscription cost and breakdown by category

### Requirement 5

**User Story:** As a user, I want to export my financial data to HTML format, so that I can view and share my reports offline.

#### Acceptance Criteria

1. WHEN a user sends "/export" command THEN the Bot SHALL generate an HTML file containing all transactions and send it as a document
2. WHEN generating HTML export THEN the Bot SHALL include interactive filters for date range, category, and transaction type
3. WHEN generating HTML export THEN the Bot SHALL include visual charts showing expense and income breakdown
4. WHEN generating HTML export THEN the Bot SHALL include subscription list with status indicators
5. WHEN generating HTML export THEN the Bot SHALL include financial health summary and analysis

### Requirement 6

**User Story:** As a user, I want the HTML report to be mobile-friendly and visually appealing, so that I can view it on any device.

#### Acceptance Criteria

1. WHEN generating HTML export THEN the Bot SHALL create a responsive design that works on mobile and desktop
2. WHEN displaying data in HTML THEN the Bot SHALL use modern styling with dark theme and clear typography
3. WHEN displaying charts THEN the Bot SHALL use interactive Chart.js visualizations
4. WHEN the HTML file is opened THEN the Bot SHALL enable client-side filtering without requiring server connection

### Requirement 7

**User Story:** As a user, I want to receive subscription renewal reminders, so that I don't miss important payment dates.

#### Acceptance Criteria

1. WHEN a subscription is expiring within 3 days THEN the Bot SHALL send a reminder notification to the user
2. WHEN displaying subscription details THEN the Bot SHALL show renewal status (active, expiring soon, expired)
3. WHEN a user sends "/renewsub [id] [new_end_date]" command THEN the Bot SHALL update the subscription end date

