# Telegram Money Tracker Bot 💰

Bot Telegram untuk mencatat keuangan pribadi dengan bantuan AI. Cukup ketik transaksi dengan bahasa natural, AI akan membantu mengekstrak informasi dan menyimpannya.

## Fitur

### 📝 Transaksi
- Catat transaksi dengan bahasa natural (contoh: "beli makan 50rb", "gajian 5jt")
- 🤖 Multi AI Provider: Pilih antara Poe API atau Groq API
- 🧠 Pilih model AI sesuai kebutuhan
- 📊 Lihat ringkasan keuangan bulanan
- 📋 Lihat history transaksi
- 🗑️ Hapus transaksi
- 🆔 ID transaksi unik 5 digit

### 📅 Langganan/Subscription
- Catat langganan dengan bahasa natural
- Otomatis hitung tanggal berakhir
- Notifikasi langganan yang akan berakhir
- Lihat total biaya langganan bulanan
- Kategori: streaming, hosting, domain, software, other

### 📊 Analisis Keuangan
- Skor kesehatan keuangan (0-100)
- Breakdown pengeluaran per kategori
- Perbandingan dengan bulan sebelumnya
- Saran dan peringatan otomatis

### 📥 Export Data
- Export ke CSV (untuk Excel/Google Sheets)
- Export ke HTML dengan filter interaktif
- Dark theme modern & responsive

### 💾 Database
- Dual database: SQLite (lokal) + TiDB Cloud (backup)
- Sinkronisasi otomatis

## Instalasi

1. Clone repository
2. Install dependencies dengan UV:
```bash
uv sync
```

3. Copy `.env.example` ke `.env` dan isi kredensial:
```bash
cp .env.example .env
```

4. Jalankan bot:
```bash
uv run python src/main.py
```

## Perintah Bot

### 📝 Transaksi
- `/start` - Tampilkan pesan selamat datang
- `/help` - Panduan lengkap
- `/history` - Lihat 10 transaksi terakhir
- `/summary` - Ringkasan bulan ini
- `/summary [bulan] [tahun]` - Ringkasan bulan tertentu
- `/delete [id]` - Hapus transaksi

### 📅 Langganan
- `/subs` - Lihat semua langganan aktif
- `/addsub` - Tambah langganan (menu interaktif)
- `/addsub langganan netflix 50rb 1 bulan` - Tambah dengan bahasa natural
- `/addsub langganan spotify 60rb 1 tahun mulai 1 januari 2025` - Dengan tanggal mulai
- `/delsub [id]` - Hapus langganan
- `/renewsub [id] [tanggal]` - Perpanjang langganan
- `/exportsubs` - Export langganan ke HTML (responsive)

### 📊 Analisis
- `/analysis` - Analisis kesehatan keuangan

### 🤖 AI Provider
- `/provider` - Lihat AI provider aktif
- `/provider list` - Lihat semua provider tersedia
- `/provider set [nama]` - Ganti provider (poe/groq)
- `/models` - Lihat model AI tersedia
- `/model set [nama]` - Ganti model AI

### 📥 Export Data
- `/export` - Pilih format export (interaktif)
- `/export csv` - Download data dalam format CSV
- `/exportfull` - Export HTML lengkap dengan filter interaktif

## Contoh Penggunaan

### Transaksi (Cukup ketik langsung tanpa command)
```
beli makan siang 50rb
gajian bulan ini 5jt
bayar listrik 200rb
dapat bonus 1jt
```

### Langganan (Cukup ketik langsung atau pakai /addsub)
```
langganan netflix 50rb 1 bulan
berlangganan spotify 60rb setahun
saya berlangganan youtube premium 80rb 3 bulan
langganan vps digitalocean 100rb 1 bulan mulai hari ini
langganan domain 150rb 1 tahun mulai 1 januari 2025
berlangganan adobe 200rb 1 bulan dimulai dari tanggal 15 december 2025
```

Bot akan otomatis:
- Mendeteksi nama layanan
- Mengkonversi jumlah (50rb → 50.000)
- Menentukan kategori (streaming/hosting/domain/software/other)
- Mendeteksi tanggal mulai dari teks (atau gunakan hari ini jika tidak disebutkan)
- Menghitung tanggal berakhir berdasarkan durasi
- Opsi untuk mencatat sebagai transaksi pengeluaran

### Fitur Langganan Terintegrasi
- **Otomatis tercatat sebagai transaksi pengeluaran** saat menambah langganan
- Kategori transaksi: "langganan"
- Menampilkan ID langganan dan ID transaksi
- Hapus langganan dengan tombol interaktif atau `/delsub [id]`
- Lihat total biaya langganan bulanan per kategori
- Export langganan ke HTML responsive dengan `/exportsubs`

## Testing

```bash
uv run pytest tests/ -v
```

## Struktur Project

```
├── src/
│   ├── bot/          # Telegram bot handlers
│   ├── ai/           # AI providers (Poe, Groq)
│   │   └── providers/  # Provider implementations
│   ├── database/     # SQLite & TiDB Cloud
│   └── models/       # Data models
├── config/           # Settings
├── tests/            # Unit tests
└── data/             # SQLite database
```

## AI Providers

Bot mendukung multiple AI providers untuk parsing transaksi dan langganan:

| Provider | Model Default | Keterangan |
|----------|---------------|------------|
| Groq | llama-3.3-70b-versatile | Cepat, gratis, recommended |
| Poe | gemini-2.5-flash | Multi-model (GPT-4o, Claude, Gemini) |

### Fitur AI Terintegrasi

Kedua provider mendukung:
- ✅ Parsing transaksi natural language
- ✅ Parsing langganan natural language
- ✅ Deteksi tanggal mulai dari teks
- ✅ Konversi jumlah (50rb → 50.000)
- ✅ Kategorisasi otomatis
- ✅ Ganti provider/model kapan saja

### Konfigurasi Provider

Set environment variables di `.env`:

```env
# Groq API (recommended)
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile

# Poe API
POE_API_KEY=your_poe_api_key
POE_MODEL=gemini-2.5-flash

# Default provider
DEFAULT_AI_PROVIDER=groq
```

### Ganti Provider

```
/provider list          # Lihat provider tersedia
/provider set groq      # Ganti ke Groq
/provider set poe       # Ganti ke Poe
/models                 # Lihat model tersedia
/model set gpt-4o       # Ganti model (Poe)
```


## Admin Dashboard 🎛️

Admin Dashboard adalah antarmuka web untuk mengelola bot dan user.

### Fitur Admin Dashboard

- 📊 **Dashboard**: Statistik user, subscription, dan query
- 👥 **User Management**: Lihat, blokir, hapus user
- 💳 **Subscription Plans**: Kelola paket langganan
- 🔢 **Query Limits**: Atur batasan query per user
- 📈 **Analytics**: Grafik penggunaan 30 hari terakhir

### Menjalankan Admin Dashboard

```bash
# Install dependencies
uv sync

# Jalankan admin dashboard (port 8080)
uv run python -m src.admin.server
```

Akses dashboard di: `http://localhost:8080`

### Konfigurasi Admin

Set environment variables di `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your_secure_password
ADMIN_PORT=8080
```

### API Endpoints

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| POST | `/api/admin/login` | Login admin |
| POST | `/api/admin/logout` | Logout admin |
| GET | `/api/admin/users` | List users (paginated) |
| GET | `/api/admin/users/{id}` | Detail user |
| PUT | `/api/admin/users/{id}/block` | Blokir user |
| PUT | `/api/admin/users/{id}/unblock` | Unblock user |
| DELETE | `/api/admin/users/{id}` | Hapus user |
| PUT | `/api/admin/users/{id}/limits` | Set query limits |
| GET | `/api/admin/users/{id}/usage` | Get usage stats |
| GET | `/api/admin/plans` | List subscription plans |
| POST | `/api/admin/plans` | Create plan |
| PUT | `/api/admin/users/{id}/subscription` | Assign subscription |
| GET | `/api/admin/stats` | Dashboard statistics |
| GET | `/api/admin/analytics/queries` | Query analytics |

### Menjalankan Bot + Dashboard

**Opsi 1: Jalankan bersamaan (recommended)**
```bash
uv run python run_all.py
```
Script ini akan menjalankan bot Telegram dan admin dashboard dalam satu proses.

**Opsi 2: Jalankan terpisah**
```bash
# Terminal 1: Bot
uv run python src/main.py

# Terminal 2: Admin Dashboard
uv run python -m src.admin.server
```
