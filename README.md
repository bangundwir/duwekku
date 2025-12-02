# Telegram Money Tracker Bot 💰

Bot Telegram untuk mencatat keuangan pribadi dengan bantuan AI. Cukup ketik transaksi dengan bahasa natural, AI akan membantu mengekstrak informasi dan menyimpannya.

## Fitur

- 📝 Catat transaksi dengan bahasa natural (contoh: "beli makan 50rb", "gajian 5jt")
- 🤖 Multi AI Provider: Pilih antara Poe API atau Groq API
- 🧠 Pilih model AI sesuai kebutuhan
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

### Transaksi
- `/start` - Tampilkan pesan selamat datang
- `/history` - Lihat 10 transaksi terakhir
- `/summary` - Ringkasan bulan ini
- `/summary [bulan] [tahun]` - Ringkasan bulan tertentu
- `/delete [id]` - Hapus transaksi

### AI Provider
- `/provider` - Lihat AI provider aktif
- `/provider list` - Lihat semua provider tersedia
- `/provider set [nama]` - Ganti provider (poe/groq)
- `/models` - Lihat model AI tersedia
- `/model set [nama]` - Ganti model AI

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
│   ├── ai/           # AI providers (Poe, Groq)
│   │   └── providers/  # Provider implementations
│   ├── database/     # SQLite & TiDB Cloud
│   └── models/       # Data models
├── config/           # Settings
├── tests/            # Unit tests
└── data/             # SQLite database
```

## AI Providers

Bot mendukung multiple AI providers:

| Provider | Model Default | Keterangan |
|----------|---------------|------------|
| Groq | llama-3.3-70b-versatile | Cepat, gratis |
| Poe | gemini-2.5-flash | Multi-model |

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
