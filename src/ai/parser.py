import json
import re
import logging
from dataclasses import dataclass
from typing import Optional

import openai

logger = logging.getLogger(__name__)


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
    duration_months: int  # durasi dalam bulan
    
    def is_valid(self) -> bool:
        """Check if parsed subscription has valid data."""
        return (
            len(self.name) > 0
            and self.amount > 0
            and self.duration_months > 0
        )


def normalize_amount(amount_str: str) -> Optional[float]:
    """
    Normalize Indonesian amount string to numeric value.
    
    Examples:
        "50rb" -> 50000
        "5jt" -> 5000000
        "100k" -> 100000
        "1.5jt" -> 1500000
        "2,5jt" -> 2500000
    """
    if not amount_str:
        return None
    
    # Clean the string
    amount_str = amount_str.lower().strip()
    amount_str = amount_str.replace(" ", "")
    
    # Handle decimal separators
    amount_str = amount_str.replace(",", ".")
    
    # Extract number and multiplier
    multipliers = {
        "rb": 1000,
        "ribu": 1000,
        "k": 1000,
        "jt": 1000000,
        "juta": 1000000,
        "m": 1000000,
    }

    # Try to find multiplier
    multiplier = 1
    for suffix, mult in multipliers.items():
        if amount_str.endswith(suffix):
            multiplier = mult
            amount_str = amount_str[:-len(suffix)]
            break
    
    # Extract numeric value
    try:
        # Remove any remaining non-numeric chars except dot
        numeric_str = re.sub(r"[^\d.]", "", amount_str)
        if not numeric_str:
            return None
        value = float(numeric_str) * multiplier
        return value
    except (ValueError, TypeError):
        return None


class AIParser:
    """AI-powered transaction parser using Poe API."""
    
    def __init__(self, api_key: str, base_url: str = "https://api.poe.com/v1", model: str = "gemini-2.5-flash"):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model
    
    def _build_subscription_prompt(self, message: str) -> str:
        """Build prompt for subscription parsing."""
        return f"""Kamu adalah asisten untuk mengekstrak informasi langganan/subscription dari pesan dalam bahasa Indonesia.

Ekstrak informasi berikut dari pesan pengguna:
- name: nama layanan (Netflix, Spotify, VPS, Domain, dll)
- amount: biaya per bulan dalam angka (konversi rb=ribu=1000, jt=juta=1000000)
- category: kategori (streaming, hosting, domain, software, other)
- duration_months: durasi langganan dalam bulan (1 bulan=1, 1 tahun=12, 6 bulan=6)

Pesan pengguna: "{message}"

Balas HANYA dengan JSON valid tanpa penjelasan:
{{"name": "nama layanan", "amount": angka, "category": "kategori", "duration_months": angka}}"""

    def parse_subscription(self, message: str) -> Optional[ParsedSubscription]:
        """Parse natural language message into subscription data."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": self._build_subscription_prompt(message)}
                ],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            return self._parse_subscription_response(content)
            
        except Exception as e:
            logger.error(f"AI subscription parsing error: {e}")
            return None
    
    def _parse_subscription_response(self, response: str) -> Optional[ParsedSubscription]:
        """Parse AI response JSON into ParsedSubscription."""
        try:
            response = response.strip()
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                response = json_match.group()
            
            data = json.loads(response)
            
            parsed = ParsedSubscription(
                name=data.get("name", ""),
                amount=float(data.get("amount", 0)),
                category=data.get("category", "other"),
                duration_months=int(data.get("duration_months", 1)),
            )
            
            if parsed.is_valid():
                return parsed
            return None
            
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse subscription response: {e}")
            return None

    def _build_prompt(self, message: str) -> str:
        """Build prompt for AI model."""
        return f"""Kamu adalah asisten untuk mengekstrak informasi transaksi keuangan dari pesan dalam bahasa Indonesia.

Ekstrak informasi berikut dari pesan pengguna:
- type: "income" untuk pemasukan, "expense" untuk pengeluaran
- amount: jumlah uang dalam angka (konversi rb=ribu=1000, jt=juta=1000000)
- category: kategori transaksi (makanan, transportasi, belanja, tagihan, hiburan, kesehatan, pendidikan, gaji, bonus, freelance, investasi, hadiah, lainnya)
- description: deskripsi singkat transaksi

Pesan pengguna: "{message}"

Balas HANYA dengan JSON valid tanpa penjelasan:
{{"type": "income/expense", "amount": angka, "category": "kategori", "description": "deskripsi"}}"""
    
    def parse_transaction(self, message: str) -> Optional[ParsedTransaction]:
        """Parse natural language message into transaction data."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": self._build_prompt(message)}
                ],
                temperature=0.1,
            )
            
            content = response.choices[0].message.content
            return self._parse_response(content, message)
            
        except Exception as e:
            logger.error(f"AI parsing error: {e}")
            return None
    
    def _parse_response(self, response: str, original_message: str) -> Optional[ParsedTransaction]:
        """Parse AI response JSON into ParsedTransaction."""
        try:
            # Try to extract JSON from response
            response = response.strip()
            
            # Find JSON in response
            json_match = re.search(r'\{[^}]+\}', response)
            if json_match:
                response = json_match.group()
            
            data = json.loads(response)
            
            parsed = ParsedTransaction(
                type=data.get("type", "expense"),
                amount=float(data.get("amount", 0)),
                category=data.get("category", "lainnya"),
                description=data.get("description", original_message),
            )
            
            if parsed.is_valid():
                return parsed
            return None
            
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            logger.error(f"Failed to parse AI response: {e}")
            return None
