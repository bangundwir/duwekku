# Requirements Document

## Introduction

Bot Telegram untuk mencatat keuangan pribadi dengan bantuan AI. Bot ini memungkinkan pengguna mencatat pemasukan dan pengeluaran melalui chat Telegram dengan bahasa natural, dimana AI akan membantu mengekstrak informasi transaksi dari pesan pengguna. Data disimpan di SQLite (lokal) dan TiDB Cloud (cloud) untuk redundansi.

## Glossary

- **Bot**: Aplikasi Telegram bot yang menerima dan memproses pesan pengguna
- **Transaction**: Catatan keuangan berupa pemasukan (income) atau pengeluaran (expense)
- **AI Parser**: Komponen yang menggunakan Poe API (Gemini 2.5 Flash) untuk mengekstrak informasi transaksi dari pesan natural
- **SQLite**: Database lokal untuk penyimpanan offline
- **TiDB Cloud**: Database cloud MySQL-compatible untuk backup dan sinkronisasi
- **Category**: Kategori transaksi seperti makanan, transportasi, gaji, dll

## Requirements

### Requirement 1

**User Story:** As a user, I want to record my financial transactions through Telegram chat, so that I can easily track my money without using complex apps.

#### Acceptance Criteria

1. WHEN a user sends a message describing a transaction THEN the Bot SHALL parse the message using AI Parser and extract amount, category, and description
2. WHEN the AI Parser successfully extracts transaction data THEN the Bot SHALL save the transaction to both SQLite and TiDB Cloud databases
3. WHEN a transaction is saved successfully THEN the Bot SHALL reply with a confirmation message showing the recorded details
4. IF the AI Parser fails to extract valid transaction data THEN the Bot SHALL ask the user to clarify the transaction details
5. WHEN a user sends "/start" command THEN the Bot SHALL display a welcome message with usage instructions

### Requirement 2

**User Story:** As a user, I want to view my transaction history and summary, so that I can understand my spending patterns.

#### Acceptance Criteria

1. WHEN a user sends "/history" command THEN the Bot SHALL display the last 10 transactions from the database
2. WHEN a user sends "/summary" command THEN the Bot SHALL display total income, total expense, and balance for the current month
3. WHEN a user sends "/summary [month] [year]" command THEN the Bot SHALL display summary for the specified month and year
4. WHEN displaying transactions THEN the Bot SHALL format each entry with date, category, amount, and description

### Requirement 3

**User Story:** As a user, I want my data to be stored reliably, so that I never lose my financial records.

#### Acceptance Criteria

1. WHEN a transaction is recorded THEN the Bot SHALL save it to SQLite database first as primary storage
2. WHEN SQLite save succeeds THEN the Bot SHALL attempt to sync the transaction to TiDB Cloud
3. IF TiDB Cloud sync fails THEN the Bot SHALL mark the transaction as pending sync and retry later
4. WHEN the Bot starts THEN the Bot SHALL attempt to sync any pending transactions to TiDB Cloud

### Requirement 4

**User Story:** As a developer, I want the codebase to be modular and maintainable, so that I can easily extend and debug the application.

#### Acceptance Criteria

1. THE Bot SHALL organize code into separate modules: bot handler, AI parser, database layer, and models
2. THE Bot SHALL use environment variables or configuration file for API keys and database credentials
3. THE Bot SHALL implement logging for debugging and monitoring purposes
4. THE Bot SHALL handle errors gracefully without crashing the application

### Requirement 5

**User Story:** As a user, I want to delete or edit my transactions, so that I can correct mistakes in my records.

#### Acceptance Criteria

1. WHEN a user sends "/delete [id]" command THEN the Bot SHALL remove the specified transaction from both databases
2. WHEN a transaction is deleted successfully THEN the Bot SHALL confirm the deletion to the user
3. IF the specified transaction ID does not exist THEN the Bot SHALL inform the user that the transaction was not found

### Requirement 6

**User Story:** As a user, I want the AI to understand my natural language input, so that I can record transactions without following strict formats.

#### Acceptance Criteria

1. WHEN a user sends "beli makan 50rb" THEN the AI Parser SHALL extract: type=expense, amount=50000, category=food
2. WHEN a user sends "gajian 5jt" THEN the AI Parser SHALL extract: type=income, amount=5000000, category=salary
3. WHEN a user sends a message with ambiguous amount format THEN the AI Parser SHALL normalize it to numeric value (e.g., "50rb" → 50000, "5jt" → 5000000)
4. WHEN parsing transaction THEN the AI Parser SHALL return structured JSON with fields: type, amount, category, description
5. WHEN a user sends a message in Indonesian THEN the AI Parser SHALL understand and process it correctly
