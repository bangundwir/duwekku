# Admin Dashboard Documentation

Dokumentasi lengkap untuk Admin Dashboard Money Tracker Bot.

## Overview

Admin Dashboard adalah antarmuka web untuk mengelola Money Tracker Bot. Dashboard ini menyediakan fitur untuk:

- Melihat statistik pengguna dan query
- Mengelola pengguna (block, unblock, delete)
- Mengelola subscription plans
- Mengatur query limits per pengguna
- Reset query counters

## Instalasi & Konfigurasi

### Environment Variables

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_PORT=8080
```

### Dependencies

- FastAPI (backend API)
- Tailwind CSS (styling)
- Alpine.js (frontend interaktivity)
- Chart.js (grafik)

## Menjalankan Dashboard

### Bersamaan dengan Bot
```bash
python run_all.py
```

### Dashboard Saja
```bash
uvicorn src.admin.server:app --host 0.0.0.0 --port 8080
```

### Akses
Buka browser: `http://localhost:8080`

## Fitur Dashboard

### 1. Dashboard Overview

Halaman utama menampilkan:
- **Total Users**: Jumlah user terdaftar
- **Active Users**: User aktif (tidak diblokir)
- **Active Subscriptions**: Langganan aktif
- **Today's Queries**: Query hari ini
- **Grafik**: Query volume 30 hari terakhir

### 2. User Management

#### Tabel User
- Pagination dengan 20 item per halaman
- Pencarian berdasarkan username atau ID
- Kolom: User, ID, Registered, Queries, Status, Actions

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
- Reset Hours

**Assign Subscription:**
- Pilih plan dari dropdown
- Custom duration (opsional)

**Reset Query Counters:**
- ⏰ Reset Hourly
- 📅 Reset Daily
- 📆 Reset Monthly
- 🔄 Reset All

**Danger Zone:**
- Reset Data User (hapus transaksi & langganan)

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
Form fields:
- 📝 Plan Name
- 💰 Price (Rp)
- 📅 Duration (days)
- ⏰ Hourly Query Limit
- 🔄 Reset Hours (1-24 jam)
- 📊 Daily Query Limit
- 📆 Monthly Query Limit
- ✨ Features (comma separated)
- ⭐ Set as Default Plan

#### Edit Plan
- Klik "Edit" pada plan
- Modal dengan form lengkap
- Simpan perubahan

#### Set Default Plan
- Klik "⭐ Set as Default"
- Plan default untuk user baru
- Hanya satu plan bisa default

#### Delete Plan
- Klik "Delete"
- Konfirmasi penghapusan

## Default Subscription Plans

| Plan | Hourly | Daily | Monthly | Price | Duration |
|------|--------|-------|---------|-------|----------|
| Free ⭐ | 5 | 10 | 100 | Rp 0 | Unlimited |
| Basic | 20 | 50 | 500 | Rp 25.000 | 30 hari |
| Premium | 50 | 200 | 2.000 | Rp 75.000 | 30 hari |
| Pro | 200 | 1.000 | 10.000 | Rp 150.000 | 30 hari |

## Query Limit System

### Cara Kerja
1. **Hourly Limit**: Reset setiap X jam (configurable)
2. **Daily Limit**: Reset setiap tengah malam
3. **Monthly Limit**: Reset setiap awal bulan

### Prioritas Pengecekan
1. Cek hourly limit → tolak jika tercapai
2. Cek daily limit → tolak jika tercapai
3. Cek monthly limit → tolak jika tercapai
4. Izinkan query dan increment counter

### Default Plan untuk User Baru
- User baru otomatis dapat limit dari default plan
- Admin bisa ubah default plan kapan saja
- Perubahan hanya berlaku untuk user baru

## Struktur Kode

```
src/admin/
├── __init__.py
├── server.py           # Server entry point
├── api.py              # FastAPI routes
├── templates/
│   └── index.html      # Dashboard UI
└── services/
    ├── auth_service.py       # Authentication
    ├── user_service.py       # User management
    ├── subscription_service.py # Subscription management
    └── query_limiter.py      # Query limit management
```

## Security

- Session-based authentication
- Token di localStorage browser
- Session expire otomatis
- CORS enabled

## Troubleshooting

### Dashboard tidak bisa diakses
1. Cek port tidak digunakan aplikasi lain
2. Verifikasi environment variables
3. Pastikan dependencies terinstall

### Login gagal
1. Cek username/password di `.env`
2. Tidak ada spasi di credentials
3. Restart server setelah ubah `.env`

### Data tidak muncul
1. Pastikan database terkoneksi
2. Cek console browser untuk error
3. Refresh atau logout/login ulang
