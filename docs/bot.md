# Telegram Bot Documentation

Dokumentasi lengkap untuk Telegram Money Tracker Bot.

## Overview

Bot Telegram untuk mencatat keuangan pribadi dengan bantuan AI. Cukup ketik transaksi dengan bahasa natural, AI akan membantu mengekstrak informasi dan menyimpannya.

## Fitur Utama

### 📝 Transaksi
- Catat transaksi dengan bahasa natural
- Multi AI Provider (Poe/Groq)
- Ringkasan keuangan bulanan
- History transaksi
- ID transaksi unik 5 digit

### 📅 Langganan/Subscription
- Catat langganan dengan bahasa natural
- Otomatis hitung tanggal berakhir
- Notifikasi langganan akan berakhir
- Kategori: streaming, hosting, domain, software, other

### 📊 Analisis Keuangan
- Skor kesehatan keuangan (0-100)
- Breakdown pengeluaran per kategori
- Perbandingan dengan bulan sebelumnya
- Saran dan peringatan otomatis

### 📥 Export Data
- Export ke CSV
- Export ke HTML dengan filter interaktif

## Perintah Bot

### Transaksi
| Command | Deskripsi |
|---------|-----------|
| `/start` | Tampilkan pesan selamat datang |
| `/help` | Panduan lengkap |
| `/history` | Lihat 10 transaksi terakhir |
| `/summary` | Ringkasan bulan ini |
| `/summary [bulan] [tahun]` | Ringkasan bulan tertentu |
| `/delete [id]` | Hapus transaksi |
| `/status` | Lihat status query limit |

### Langganan
| Command | Deskripsi |
|---------|-----------|
| `/subs` | Lihat semua langganan aktif |
| `/addsub` | Tambah langganan (menu interaktif) |
| `/addsub [text]` | Tambah dengan bahasa natural |
| `/delsub [id]` | Hapus langganan |
| `/renewsub [id] [tanggal]` | Perpanjang langganan |
| `/exportsubs` | Export langganan ke HTML |

### Analisis
| Command | Deskripsi |
|---------|-----------|
| `/analysis` | Analisis kesehatan keuangan |

### AI Provider
| Command | Deskripsi |
|---------|-----------|
| `/provider` | Lihat AI provider aktif |
| `/provider list` | Lihat semua provider |
| `/provider set [nama]` | Ganti provider |
| `/models` | Lihat model AI tersedia |
| `/model set [nama]` | Ganti model AI |

### Export
| Command | Deskripsi |
|---------|-----------|
| `/export` | Pilih format export |
| `/export csv` | Download CSV |
| `/exportfull` | Export HTML lengkap |

## Contoh Penggunaan

### Transaksi (Ketik langsung tanpa command)
```
beli makan siang 50rb
gajian bulan ini 5jt
bayar listrik 200rb
dapat bonus 1jt
```

### Langganan
```
langganan netflix 50rb 1 bulan
berlangganan spotify 60rb setahun
langganan vps 100rb 1 bulan mulai hari ini
langganan domain 150rb 1 tahun mulai 1 januari 2025
```

## Query Limit System

Bot menggunakan sistem limit query untuk mengontrol penggunaan:

### Tipe Limit
- **Hourly**: Reset setiap X jam
- **Daily**: Reset setiap tengah malam
- **Monthly**: Reset setiap awal bulan

### Cek Status
Gunakan `/status` untuk melihat:
- Sisa query per jam
- Sisa query per hari
- Sisa query per bulan
- Waktu reset berikutnya

### Upgrade Plan
Jika limit tercapai, user bisa upgrade subscription plan untuk mendapat limit lebih tinggi.

## Struktur Kode

```
src/bot/
├── __init__.py
├── handler.py      # Main message handler
└── commands.py     # Command handlers
```

### handler.py
- `MessageHandler` class
- Handle semua incoming messages
- Routing ke command atau AI parser
- Query limit checking

### commands.py
- `CommandHandler` class
- Implementasi semua commands
- Callback query handlers
- Interactive menus

## Environment Variables

```env
# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token

# AI Providers
GROQ_API_KEY=your_groq_key
POE_API_KEY=your_poe_key
DEFAULT_AI_PROVIDER=groq

# Database
DATABASE_PATH=data/money_tracker.db
```

## Error Handling

Bot menangani berbagai error:
- Invalid command format
- AI parsing failure
- Database errors
- Rate limiting
- Network errors

Semua error ditampilkan dengan pesan user-friendly dalam Bahasa Indonesia.
