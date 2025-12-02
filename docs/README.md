# Money Tracker Bot - Dokumentasi

Dokumentasi lengkap untuk Money Tracker Bot dan Admin Dashboard.

## Daftar Dokumentasi

| File | Deskripsi |
|------|-----------|
| [README.md](README.md) | Dokumentasi utama (file ini) |
| [bot.md](bot.md) | Dokumentasi Telegram Bot |
| [admin-dashboard.md](admin-dashboard.md) | Dokumentasi Admin Dashboard |
| [database.md](database.md) | Dokumentasi Database |
| [ai-providers.md](ai-providers.md) | Dokumentasi AI Providers |
| [models.md](models.md) | Dokumentasi Data Models |
| [api-reference.md](api-reference.md) | API Reference lengkap |
| [testing.md](testing.md) | Dokumentasi Testing |

---

# Admin Dashboard Documentation

Dokumentasi lengkap untuk Admin Dashboard Money Tracker Bot.

## Daftar Isi

- [Overview](#overview)
- [Instalasi & Konfigurasi](#instalasi--konfigurasi)
- [Menjalankan Dashboard](#menjalankan-dashboard)
- [Fitur Dashboard](#fitur-dashboard)
- [API Reference](#api-reference)

## Overview

Admin Dashboard adalah antarmuka web untuk mengelola Money Tracker Bot. Dashboard ini menyediakan fitur untuk:

- Melihat statistik pengguna dan query
- Mengelola pengguna (block, unblock, delete)
- Mengelola subscription plans
- Mengatur query limits per pengguna
- Reset query counters

## Instalasi & Konfigurasi

### Environment Variables

Tambahkan variabel berikut di file `.env`:

```env
# Admin Dashboard
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_PORT=8080
```

### Dependencies

Dashboard menggunakan:
- FastAPI untuk backend API
- Tailwind CSS untuk styling
- Alpine.js untuk interaktivitas frontend
- Chart.js untuk grafik

## Menjalankan Dashboard

### Menjalankan Bersamaan dengan Bot

```bash
python run_all.py
```

Script ini akan menjalankan bot Telegram dan admin dashboard secara bersamaan.

### Menjalankan Dashboard Saja

```bash
uvicorn src.admin.server:app --host 0.0.0.0 --port 8080
```

### Akses Dashboard

Buka browser dan akses: `http://localhost:8080`

Login dengan kredensial yang sudah dikonfigurasi di `.env`.

## Fitur Dashboard

### 1. Dashboard Overview

Halaman utama menampilkan:
- Total Users
- Active Users
- Active Subscriptions
- Today's Queries
- Grafik Query Volume (30 hari terakhir)

### 2. User Management

#### Melihat Daftar User
- Tabel dengan pagination
- Pencarian berdasarkan username atau ID
- Informasi: username, user ID, tanggal registrasi, query usage, status

#### User Detail Modal
Klik user untuk melihat detail:

**Statistik Query:**
- ⏰ Hourly Queries (biru)
- 📅 Daily Queries (hijau)
- 📆 Monthly Queries (ungu)
- 📊 Total Queries (oranye)

**Set Query Limits:**
- Hourly Limit
- Daily Limit
- Monthly Limit
- Reset Hours (berapa jam sekali reset hourly)

**Assign Subscription:**
- Pilih plan dari dropdown
- Opsional: custom duration

**Reset Query Counters:**
- ⏰ Reset Hourly - reset counter per jam
- 📅 Reset Daily - reset counter harian
- 📆 Reset Monthly - reset counter bulanan
- 🔄 Reset All - reset semua counter

**Danger Zone:**
- Reset Data User - hapus semua transaksi dan langganan

#### Aksi User
- 👁️ View Details
- 🚫 Block/Unblock
- 🗑️ Delete

### 3. Subscription Plans

#### View Modes
- **Card View**: Tampilan kartu dengan detail lengkap
- **Table View**: Tampilan tabel untuk overview cepat

#### Informasi Plan
- Nama plan
- Harga (Rp)
- Durasi (hari)
- ⏰ Hourly Query Limit
- 📊 Daily Query Limit
- 📆 Monthly Query Limit
- 🔄 Reset Hours
- ⭐ Default Plan badge
- Status (Active/Inactive)
- Features list

#### Create New Plan
Form untuk membuat plan baru:
- 📝 Plan Name
- 💰 Price (Rp)
- 📅 Duration (days)
- ⏰ Hourly Query Limit
- 🔄 Reset Hours (dropdown: 1-24 jam)
- 📊 Daily Query Limit
- 📆 Monthly Query Limit
- ✨ Features (comma separated)
- ⭐ Set as Default Plan (checkbox)

#### Edit Plan
- Klik tombol "Edit" pada plan
- Modal dengan form yang sama seperti create
- Simpan perubahan

#### Set Default Plan
- Klik "⭐ Set as Default" pada plan
- Plan default akan otomatis diterapkan ke user baru
- Hanya satu plan yang bisa jadi default

#### Delete Plan
- Klik tombol "Delete"
- Konfirmasi penghapusan


## API Reference

### Authentication

#### Login
```
POST /api/admin/login
```
Request:
```json
{
  "username": "admin",
  "password": "password"
}
```
Response:
```json
{
  "token": "session_token",
  "username": "admin",
  "message": "Login successful"
}
```

#### Logout
```
POST /api/admin/logout
Authorization: Bearer <token>
```

#### Check Session
```
GET /api/admin/session
Authorization: Bearer <token>
```

### Users

#### Get Users (Paginated)
```
GET /api/admin/users?page=1&per_page=20&search=keyword
Authorization: Bearer <token>
```

#### Get User Detail
```
GET /api/admin/users/{user_id}
Authorization: Bearer <token>
```

#### Block User
```
PUT /api/admin/users/{user_id}/block
Authorization: Bearer <token>
```

#### Unblock User
```
PUT /api/admin/users/{user_id}/unblock
Authorization: Bearer <token>
```

#### Delete User
```
DELETE /api/admin/users/{user_id}
Authorization: Bearer <token>
```

#### Reset User Data
```
POST /api/admin/users/{user_id}/reset
Authorization: Bearer <token>
```
Menghapus semua transaksi dan langganan user.

### Query Limits

#### Set User Limits
```
PUT /api/admin/users/{user_id}/limits
Authorization: Bearer <token>
```
Request:
```json
{
  "hourly_limit": 20,
  "daily_limit": 100,
  "monthly_limit": 1000,
  "reset_hours": 1
}
```

#### Get User Usage
```
GET /api/admin/users/{user_id}/usage
Authorization: Bearer <token>
```

#### Reset Query Counters
```
POST /api/admin/users/{user_id}/reset-queries?reset_type=all
Authorization: Bearer <token>
```
Parameter `reset_type`:
- `hourly` - reset counter per jam
- `daily` - reset counter harian
- `monthly` - reset counter bulanan
- `all` - reset semua counter

### Subscription Plans

#### Get All Plans
```
GET /api/admin/plans
Authorization: Bearer <token>
```

#### Get Default Plan
```
GET /api/admin/plans/default
Authorization: Bearer <token>
```

#### Create Plan
```
POST /api/admin/plans
Authorization: Bearer <token>
```
Request:
```json
{
  "name": "Premium",
  "hourly_query_limit": 50,
  "daily_query_limit": 200,
  "monthly_query_limit": 2000,
  "reset_hours": 1,
  "price": 75000,
  "duration_days": 30,
  "features": ["Export CSV", "Analisis lengkap"],
  "is_default": false
}
```

#### Update Plan
```
PUT /api/admin/plans/{plan_id}
Authorization: Bearer <token>
```
Request body sama dengan create.

#### Set Default Plan
```
PUT /api/admin/plans/{plan_id}/default
Authorization: Bearer <token>
```

#### Delete Plan
```
DELETE /api/admin/plans/{plan_id}
Authorization: Bearer <token>
```

### User Subscription

#### Assign Subscription
```
PUT /api/admin/users/{user_id}/subscription
Authorization: Bearer <token>
```
Request:
```json
{
  "plan_id": 2,
  "duration_days": 30
}
```

### Analytics

#### Get Dashboard Stats
```
GET /api/admin/stats
Authorization: Bearer <token>
```
Response:
```json
{
  "total_users": 100,
  "active_users": 85,
  "blocked_users": 5,
  "active_subscriptions": 30,
  "today_queries": 500,
  "total_transactions": 10000
}
```

#### Get Query Analytics
```
GET /api/admin/analytics/queries?days=30
Authorization: Bearer <token>
```

## Default Subscription Plans

Sistem menyediakan 4 plan default:

| Plan | Hourly | Daily | Monthly | Price | Duration |
|------|--------|-------|---------|-------|----------|
| Free (Default) | 5 | 10 | 100 | Rp 0 | Unlimited |
| Basic | 20 | 50 | 500 | Rp 25.000 | 30 hari |
| Premium | 50 | 200 | 2.000 | Rp 75.000 | 30 hari |
| Pro | 200 | 1.000 | 10.000 | Rp 150.000 | 30 hari |

## Query Limit System

### Cara Kerja

1. **Hourly Limit**: Reset setiap X jam (configurable via `reset_hours`)
2. **Daily Limit**: Reset setiap tengah malam
3. **Monthly Limit**: Reset setiap awal bulan

### Prioritas Pengecekan

1. Cek hourly limit → jika tercapai, tolak query
2. Cek daily limit → jika tercapai, tolak query
3. Cek monthly limit → jika tercapai, tolak query
4. Jika semua OK, izinkan query dan increment counter

### Default Plan untuk User Baru

- User baru otomatis mendapat limit dari plan yang ditandai sebagai "Default"
- Admin bisa mengubah default plan kapan saja
- Perubahan default plan hanya berlaku untuk user baru

## Security

- Session-based authentication dengan token
- Token disimpan di localStorage browser
- Session expire setelah periode tertentu
- CORS enabled untuk development

## Troubleshooting

### Dashboard tidak bisa diakses
1. Pastikan port tidak digunakan aplikasi lain
2. Cek environment variables sudah benar
3. Pastikan dependencies terinstall

### Login gagal
1. Cek username dan password di `.env`
2. Pastikan tidak ada spasi di credentials
3. Restart server setelah mengubah `.env`

### Data tidak muncul
1. Pastikan database sudah terkoneksi
2. Cek console browser untuk error
3. Refresh halaman atau logout/login ulang
