# AI Providers Documentation

Dokumentasi lengkap untuk sistem AI Providers Money Tracker Bot.

## Overview

Bot mendukung multiple AI providers untuk parsing transaksi dan langganan dengan bahasa natural.

## Supported Providers

### 1. Groq (Recommended)

**Kelebihan:**
- Sangat cepat (inference < 1 detik)
- Gratis dengan limit generous
- Model Llama 3.3 70B berkualitas tinggi

**Model Tersedia:**
| Model | Deskripsi |
|-------|-----------|
| llama-3.3-70b-versatile | Default, balanced |
| llama-3.1-70b-versatile | Alternatif |
| llama-3.1-8b-instant | Lebih cepat, kurang akurat |
| mixtral-8x7b-32768 | Context panjang |

**Konfigurasi:**
```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
```

### 2. Poe

**Kelebihan:**
- Akses ke banyak model (GPT-4o, Claude, Gemini)
- Fleksibel ganti model

**Model Tersedia:**
| Model | Deskripsi |
|-------|-----------|
| gemini-2.5-flash | Default, cepat |
| gpt-4o | OpenAI terbaru |
| claude-3-opus | Anthropic terbaik |
| claude-3-sonnet | Balanced |

**Konfigurasi:**
```env
POE_API_KEY=your_poe_api_key
POE_MODEL=gemini-2.5-flash
```

## Struktur Kode

```
src/ai/
├── __init__.py
├── parser.py           # Transaction parser
├── provider_manager.py # Provider management
└── providers/
    ├── __init__.py
    ├── base.py         # Base provider class
    ├── groq.py         # Groq implementation
    └── poe.py          # Poe implementation
```

### parser.py
- `TransactionParser` class
- Parse transaksi dari text natural
- Parse langganan dari text natural
- Normalisasi amount (50rb → 50000)

### provider_manager.py
- `ProviderManager` class
- Manage active provider per user
- Switch provider/model
- Fallback handling

### providers/base.py
- `BaseProvider` abstract class
- Interface untuk semua providers
- Common methods

### providers/groq.py
- `GroqProvider` class
- Implementasi Groq API
- Streaming support

### providers/poe.py
- `PoeProvider` class
- Implementasi Poe API
- Multi-model support

## Cara Kerja Parsing

### 1. Input Text
```
beli makan siang 50rb
```

### 2. AI Processing
AI mengekstrak:
- Type: expense
- Amount: 50000
- Category: makanan
- Description: makan siang

### 3. Output JSON
```json
{
  "type": "expense",
  "amount": 50000,
  "category": "makanan",
  "description": "makan siang"
}
```

## Parsing Langganan

### Input
```
langganan netflix 50rb 1 bulan mulai hari ini
```

### Output
```json
{
  "name": "Netflix",
  "amount": 50000,
  "category": "streaming",
  "duration_months": 1,
  "start_date": "2025-12-03"
}
```

## Commands

### Lihat Provider Aktif
```
/provider
```

### Lihat Semua Provider
```
/provider list
```

### Ganti Provider
```
/provider set groq
/provider set poe
```

### Lihat Model Tersedia
```
/models
```

### Ganti Model
```
/model set gpt-4o
/model set llama-3.3-70b-versatile
```

## Error Handling

### Rate Limiting
Jika provider rate limited, bot akan:
1. Menampilkan pesan error
2. Suggest coba lagi nanti
3. Atau ganti provider

### API Errors
- Timeout: Retry otomatis
- Invalid response: Fallback ke regex parsing
- Auth error: Notify admin

## Best Practices

1. **Gunakan Groq** untuk penggunaan normal (cepat, gratis)
2. **Gunakan Poe** jika butuh model spesifik (GPT-4o, Claude)
3. **Set default provider** di `.env` untuk konsistensi
4. **Monitor usage** via admin dashboard

## Menambah Provider Baru

1. Buat file di `src/ai/providers/`
2. Extend `BaseProvider` class
3. Implement required methods:
   - `parse_transaction()`
   - `parse_subscription()`
   - `get_available_models()`
4. Register di `provider_manager.py`
