# Database Documentation

Dokumentasi lengkap untuk sistem database Money Tracker Bot.

## Overview

Bot menggunakan dual database system:
- **SQLite**: Database lokal untuk performa
- **TiDB Cloud**: Cloud backup (opsional)

## Struktur Database

### Tabel: transactions
Menyimpan semua transaksi keuangan.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Telegram user ID |
| type | TEXT | "income" atau "expense" |
| amount | REAL | Jumlah transaksi |
| category | TEXT | Kategori transaksi |
| description | TEXT | Deskripsi transaksi |
| created_at | TEXT | Timestamp ISO format |
| synced | INTEGER | Status sync ke cloud |
| short_id | TEXT | ID pendek 5 digit |

### Tabel: subscriptions
Menyimpan data langganan user.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Telegram user ID |
| name | TEXT | Nama layanan |
| amount | REAL | Biaya langganan |
| category | TEXT | Kategori (streaming/hosting/dll) |
| start_date | TEXT | Tanggal mulai |
| end_date | TEXT | Tanggal berakhir |
| duration_months | INTEGER | Durasi dalam bulan |
| is_active | INTEGER | Status aktif |
| created_at | TEXT | Timestamp |
| short_id | TEXT | ID pendek 5 digit |

### Tabel: bot_users
Menyimpan data user bot.

| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Primary key (Telegram ID) |
| username | TEXT | Telegram username |
| first_name | TEXT | Nama depan |
| registered_at | TEXT | Tanggal registrasi |
| last_active | TEXT | Terakhir aktif |
| is_blocked | INTEGER | Status blokir |
| subscription_plan_id | INTEGER | ID plan aktif |
| subscription_plan_name | TEXT | Nama plan |
| hourly_query_limit | INTEGER | Limit per jam |
| hourly_queries_used | INTEGER | Query terpakai per jam |
| daily_query_limit | INTEGER | Limit per hari |
| daily_queries_used | INTEGER | Query terpakai per hari |
| monthly_query_limit | INTEGER | Limit per bulan |
| monthly_queries_used | INTEGER | Query terpakai per bulan |
| total_queries | INTEGER | Total query sepanjang waktu |
| reset_hours | INTEGER | Jam reset hourly |
| last_hourly_reset | TEXT | Timestamp reset hourly |
| last_query_reset | TEXT | Timestamp reset daily |
| last_monthly_reset | TEXT | Timestamp reset monthly |

### Tabel: subscription_plans
Menyimpan paket langganan.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Nama plan |
| hourly_query_limit | INTEGER | Limit per jam |
| daily_query_limit | INTEGER | Limit per hari |
| monthly_query_limit | INTEGER | Limit per bulan |
| reset_hours | INTEGER | Jam reset hourly |
| price | REAL | Harga (Rp) |
| duration_days | INTEGER | Durasi (hari) |
| features | TEXT | JSON array fitur |
| is_active | INTEGER | Status aktif |
| is_default | INTEGER | Plan default |
| created_at | TEXT | Timestamp |

### Tabel: user_subscriptions
Menyimpan subscription user ke plan.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| user_id | INTEGER | Telegram user ID |
| plan_id | INTEGER | ID plan |
| plan_name | TEXT | Nama plan |
| start_date | TEXT | Tanggal mulai |
| end_date | TEXT | Tanggal berakhir |
| status | TEXT | Status (active/expired) |
| assigned_by | TEXT | Admin yang assign |
| assigned_at | TEXT | Timestamp assign |

### Tabel: admin_sessions
Menyimpan session admin dashboard.

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| token | TEXT | Session token |
| admin_username | TEXT | Username admin |
| created_at | TEXT | Timestamp |
| expires_at | TEXT | Waktu expire |

### Tabel: user_preferences
Menyimpan preferensi user.

| Column | Type | Description |
|--------|------|-------------|
| user_id | INTEGER | Primary key |
| ai_provider | TEXT | Provider AI aktif |
| ai_model | TEXT | Model AI aktif |
| updated_at | TEXT | Timestamp update |

## Struktur Kode

```
src/database/
├── __init__.py
├── manager.py      # Database manager abstraction
├── sqlite_db.py    # SQLite implementation
└── tidb_db.py      # TiDB Cloud implementation
```

### manager.py
- `DatabaseManager` class
- Abstraksi untuk dual database
- Auto-sync ke cloud

### sqlite_db.py
- `SQLiteDB` class
- Implementasi SQLite lengkap
- Migration otomatis
- CRUD operations

### tidb_db.py
- `TiDBDatabase` class
- Koneksi ke TiDB Cloud
- Sync operations

## Migration

Database mendukung migration otomatis:
- Kolom baru ditambahkan dengan `ALTER TABLE`
- Default values untuk backward compatibility
- Tidak ada data loss

## Backup

### Manual Backup
```bash
cp data/money_tracker.db data/backup_$(date +%Y%m%d).db
```

### Cloud Sync
Jika TiDB Cloud dikonfigurasi, data otomatis di-sync.

## Environment Variables

```env
# SQLite
DATABASE_PATH=data/money_tracker.db

# TiDB Cloud (opsional)
TIDB_HOST=your_host
TIDB_PORT=4000
TIDB_USER=your_user
TIDB_PASSWORD=your_password
TIDB_DATABASE=your_database
```
