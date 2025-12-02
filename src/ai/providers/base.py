"""Base AI Provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class AIModel:
    """AI Model information."""
    id: str
    name: str
    description: Optional[str] = None


@dataclass
class ProviderInfo:
    """Provider status information."""
    name: str
    display_name: str
    is_configured: bool
    current_model: Optional[str] = None


@dataclass
class ParsedTransaction:
    """Parsed transaction data from AI."""
    
    type: str  # "income" or "expense"
    amount: float
    category: str
    description: str
    confidence: float = 1.0
    
    def is_valid(self) -> bool:
        """Check if parsed transaction has valid data."""
        return (
            self.type in ("income", "expense")
            and self.amount > 0
            and len(self.category) > 0
            and self.description is not None
        )


@dataclass
class ParsedSubscription:
    """Parsed subscription data from AI."""
    
    name: str
    amount: float
    category: str  # streaming, hosting, domain, software, other
    duration_months: int
    start_date: Optional[str] = None  # format YYYY-MM-DD atau None untuk hari ini
    
    def is_valid(self) -> bool:
        """Check if parsed subscription has valid data."""
        return (
            len(self.name) > 0
            and self.amount > 0
            and self.duration_months > 0
        )


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    name: str = ""  # Provider identifier (e.g., "poe", "groq")
    display_name: str = ""  # Human-readable name
    
    @abstractmethod
    def __init__(self, api_key: str, base_url: str, model: str):
        """Initialize provider with credentials."""
        pass
    
    @abstractmethod
    def parse_transaction(self, message: str) -> Optional[ParsedTransaction]:
        """Parse natural language message into transaction data."""
        pass
    
    def parse_subscription(self, message: str) -> Optional[ParsedSubscription]:
        """Parse natural language message into subscription data."""
        return None  # Default implementation, override in subclasses
    
    @abstractmethod
    def list_models(self) -> list[AIModel]:
        """Fetch available models from the provider."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the provider connection is working."""
        pass
    
    @abstractmethod
    def set_model(self, model_id: str) -> bool:
        """Set the active model for this provider."""
        pass
    
    @abstractmethod
    def get_current_model(self) -> str:
        """Get the current model ID."""
        pass
    
    def get_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name=self.name,
            display_name=self.display_name,
            is_configured=True,
            current_model=self.get_current_model()
        )
    
    def _build_prompt(self, message: str) -> str:
        """Build prompt for AI model."""
        return f"""Kamu adalah asisten untuk mengekstrak informasi transaksi keuangan dari pesan dalam bahasa Indonesia.

Ekstrak informasi berikut dari pesan pengguna:
- type: "income" untuk pemasukan, "expense" untuk pengeluaran
- amount: jumlah uang dalam angka (konversi rb=ribu=1000, jt=juta=1000000)
- category: kategori transaksi (makanan, transportasi, belanja, tagihan, hiburan, kesehatan, pendidikan, langganan, gaji, bonus, freelance, investasi, hadiah, lainnya)
- description: deskripsi singkat transaksi

Pesan pengguna: "{message}"

Balas HANYA dengan JSON valid tanpa penjelasan:
{{"type": "income/expense", "amount": angka, "category": "kategori", "description": "deskripsi"}}"""

    def _build_subscription_prompt(self, message: str) -> str:
        """Build prompt for subscription parsing."""
        from datetime import date
        today = date.today().strftime("%Y-%m-%d")
        
        return f"""Kamu adalah asisten untuk mengekstrak informasi langganan/subscription dari pesan dalam bahasa Indonesia.

Tanggal hari ini: {today}

Ekstrak informasi berikut dari pesan pengguna:
- name: nama layanan (Netflix, Spotify, VPS, Domain, YouTube Premium, dll) - capitalize dengan benar
- amount: biaya dalam angka (konversi: rb/ribu=1000, jt/juta=1000000, k=1000)
- category: kategori HARUS salah satu dari: streaming, hosting, domain, software, other
  * streaming: Netflix, Spotify, YouTube Premium, Disney+, HBO, Apple Music
  * hosting: VPS, Cloud, Server, DigitalOcean, AWS, Heroku
  * domain: Domain, Namecheap, GoDaddy
  * software: Adobe, Microsoft 365, Canva, Figma, JetBrains
  * other: lainnya
- duration_months: durasi dalam bulan (1 bulan=1, 1 tahun=12, setahun=12, sebulan=1)
- start_date: tanggal mulai format YYYY-MM-DD. Jika tidak disebutkan gunakan null. Jika "hari ini" gunakan {today}. Konversi nama bulan Indonesia (januari=01, februari=02, maret=03, april=04, mei=05, juni=06, juli=07, agustus=08, september=09, oktober=10, november=11, december/desember=12)

Contoh:
- "langganan netflix 50rb 1 bulan" -> {{"name": "Netflix", "amount": 50000, "category": "streaming", "duration_months": 1, "start_date": null}}
- "berlangganan spotify 60rb setahun mulai 1 januari 2025" -> {{"name": "Spotify", "amount": 60000, "category": "streaming", "duration_months": 12, "start_date": "2025-01-01"}}
- "langganan youtube premium 80rb 3 bulan dimulai dari tanggal 15 december 2025" -> {{"name": "YouTube Premium", "amount": 80000, "category": "streaming", "duration_months": 3, "start_date": "2025-12-15"}}

Pesan pengguna: "{message}"

Balas HANYA dengan JSON valid tanpa penjelasan:
{{"name": "nama", "amount": angka, "category": "kategori", "duration_months": angka, "start_date": "YYYY-MM-DD atau null"}}"""
