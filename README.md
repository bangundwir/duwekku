# Telegram Money Tracker Bot 💰

Bot Telegram untuk mencatat keuangan pribadi dengan bantuan AI. Cukup ketik transaksi dengan bahasa natural, AI akan membantu mengekstrak informasi dan menyimpannya.

## Fitur

- 📝 Catat transaksi dengan bahasa natural (contoh: "beli makan 50rb", "gajian 5jt")
- 🤖 AI parsing menggunakan Poe API (Gemini 2.5 Flash)
- 📊 Lihat ringkasan keuangan bulanan
- 📋 Lihat history transaksi
- 🗑️ Hapus transaksi
- 💾 Dual database: SQLite (lokal) + TiDB Cloud (backup)

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

- `/start` - Tampilkan pesan selamat datang
- `/history` - Lihat 10 transaksi terakhir
- `/summary` - Ringkasan bulan ini
- `/summary [bulan] [tahun]` - Ringkasan bulan tertentu
- `/delete [id]` - Hapus transaksi

## Contoh Penggunaan

Cukup ketik transaksi dengan bahasa natural:
- "beli makan siang 50rb"
- "gajian bulan ini 5jt"
- "bayar listrik 200rb"
- "dapat bonus 1jt"

## Testing

```bash
uv run pytest tests/ -v
```

## Struktur Project

```
├── src/
│   ├── bot/          # Telegram bot handlers
│   ├── ai/           # AI parser (Poe API)
│   ├── database/     # SQLite & TiDB Cloud
│   └── models/       # Data models
├── config/           # Settings
├── tests/            # Unit tests
└── data/             # SQLite database
```
