import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.database.manager import DatabaseManager

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = """
💰 *MONEY TRACKER BOT* 💰
━━━━━━━━━━━━━━━━━━━━━━━

Halo {name}! 👋

Selamat datang di asisten keuangan pribadi Anda!
Saya akan membantu mencatat pemasukan & pengeluaran dengan mudah menggunakan AI.

━━━━━━━━━━━━━━━━━━━━━━━
🚀 *CARA PAKAI*
━━━━━━━━━━━━━━━━━━━━━━━

Cukup ketik transaksi dengan bahasa sehari-hari:

📤 *Pengeluaran:*
• `beli makan 50rb`
• `bayar listrik 200rb`
• `bensin 100k`

📥 *Pemasukan:*
• `gajian 5jt`
• `dapat bonus 1jt`
• `freelance 500rb`

━━━━━━━━━━━━━━━━━━━━━━━
Ketik /help untuk melihat semua perintah 📖
"""

HELP_MESSAGE = """
📖 *PANDUAN LENGKAP*
━━━━━━━━━━━━━━━━━━━━━━━

📝 *PERINTAH TERSEDIA:*

/start
↳ Mulai bot & lihat pesan selamat datang

/help
↳ Tampilkan panduan ini

/history
↳ Lihat 10 transaksi terakhir

/summary
↳ Ringkasan keuangan bulan ini

/summary `[bulan]` `[tahun]`
↳ Ringkasan bulan tertentu
↳ Contoh: `/summary 12 2024`

/delete `[id]`
↳ Hapus transaksi berdasarkan ID
↳ Contoh: `/delete 5`

━━━━━━━━━━━━━━━━━━━━━━━
💡 *TIPS FORMAT ANGKA:*
━━━━━━━━━━━━━━━━━━━━━━━

• `rb` atau `ribu` = x1.000
• `jt` atau `juta` = x1.000.000
• `k` = x1.000

*Contoh:*
• 50rb = Rp 50.000
• 1.5jt = Rp 1.500.000
• 100k = Rp 100.000

━━━━━━━━━━━━━━━━━━━━━━━
📂 *KATEGORI OTOMATIS:*
━━━━━━━━━━━━━━━━━━━━━━━

*Pengeluaran:*
makanan, transportasi, belanja, tagihan, hiburan, kesehatan, pendidikan

*Pemasukan:*
gaji, bonus, freelance, investasi, hadiah

━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI akan otomatis mendeteksi kategori dari pesan Anda!
"""


class CommandHandler:
    """Handles Telegram bot commands."""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user_name = update.effective_user.first_name or "User"
        message = WELCOME_MESSAGE.format(name=user_name)

        # Quick action buttons
        keyboard = [
            [
                InlineKeyboardButton("📋 History", callback_data="history"),
                InlineKeyboardButton("📊 Summary", callback_data="summary"),
            ],
            [InlineKeyboardButton("📖 Bantuan", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            message, parse_mode="Markdown", reply_markup=reply_markup
        )

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /help command."""
        await update.message.reply_text(HELP_MESSAGE, parse_mode="Markdown")

    async def cmd_history(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /history command - show last 10 transactions."""
        user_id = update.effective_user.id
        transactions = self.db.get_transactions(user_id, limit=10)

        if not transactions:
            message = """
📭 *BELUM ADA TRANSAKSI*
━━━━━━━━━━━━━━━━━━━━━━━

Anda belum memiliki catatan transaksi.

💡 *Mulai catat sekarang!*
Ketik transaksi seperti:
• `beli makan 50rb`
• `gajian 5jt`
"""
            await update.message.reply_text(message, parse_mode="Markdown")
            return

        lines = [
            "📋 *RIWAYAT TRANSAKSI*",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "",
        ]

        for i, t in enumerate(transactions, 1):
            type_emoji = "💰" if t.type == "income" else "💸"
            sign = "+" if t.type == "income" else "-"
            amount_str = f"{t.amount:,.0f}".replace(",", ".")
            date_str = t.created_at.strftime("%d/%m")
            desc = t.description[:18] + ".." if len(t.description) > 18 else t.description
            
            lines.append(f"{type_emoji} *{desc}*")
            lines.append(f"   📅 {date_str} │ 💵 `{sign}Rp {amount_str}`")
            lines.append(f"   🆔 Ketik `/delete {t.id}` untuk hapus")
            if i < len(transactions):
                lines.append("")

        lines.append("")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("💡 *Tap ID untuk copy, lalu paste*")

        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


    async def cmd_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /summary [month] [year] command."""
        user_id = update.effective_user.id

        # Parse month and year from args
        now = datetime.now()
        month = now.month
        year = now.year

        if context.args:
            try:
                if len(context.args) >= 1:
                    month = int(context.args[0])
                if len(context.args) >= 2:
                    year = int(context.args[1])
            except ValueError:
                await update.message.reply_text(
                    "❌ Format salah!\nGunakan: `/summary [bulan] [tahun]`\nContoh: `/summary 12 2024`",
                    parse_mode="Markdown",
                )
                return

        if not (1 <= month <= 12):
            await update.message.reply_text("❌ Bulan harus antara 1-12")
            return

        summary = self.db.get_summary(user_id, month, year)

        # Format amounts
        income_str = f"{summary['income']:,.0f}".replace(",", ".")
        expense_str = f"{summary['expense']:,.0f}".replace(",", ".")
        balance = summary["balance"]
        balance_str = f"{abs(balance):,.0f}".replace(",", ".")

        if balance >= 0:
            balance_display = f"+Rp {balance_str}"
            balance_emoji = "📈"
            status = "✅ Keuangan sehat!"
        else:
            balance_display = f"-Rp {balance_str}"
            balance_emoji = "📉"
            status = "⚠️ Pengeluaran melebihi pemasukan"

        # Month name in Indonesian
        month_names = [
            "",
            "Januari",
            "Februari",
            "Maret",
            "April",
            "Mei",
            "Juni",
            "Juli",
            "Agustus",
            "September",
            "Oktober",
            "November",
            "Desember",
        ]

        message = f"""
📊 *RINGKASAN KEUANGAN*
━━━━━━━━━━━━━━━━━━━━━━━
📅 {month_names[month]} {year}
━━━━━━━━━━━━━━━━━━━━━━━

💰 *Pemasukan*
   Rp {income_str}

💸 *Pengeluaran*
   Rp {expense_str}

━━━━━━━━━━━━━━━━━━━━━━━
{balance_emoji} *Saldo: {balance_display}*

{status}
"""
        await update.message.reply_text(message, parse_mode="Markdown")

    async def cmd_delete(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /delete [id] command."""
        user_id = update.effective_user.id

        if not context.args:
            await update.message.reply_text(
                "❌ *Format salah!*\n\nGunakan: `/delete [id]`\nContoh: `/delete 5`\n\n💡 Lihat ID di `/history`",
                parse_mode="Markdown",
            )
            return

        try:
            transaction_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ ID harus berupa angka")
            return

        # Check if transaction exists
        transaction = self.db.get_transaction_by_id(user_id, transaction_id)
        if not transaction:
            await update.message.reply_text(
                f"❌ Transaksi dengan ID `{transaction_id}` tidak ditemukan\n\n💡 Cek ID yang benar di `/history`",
                parse_mode="Markdown",
            )
            return

        # Show what will be deleted
        if self.db.delete_transaction(user_id, transaction_id):
            message = f"""
✅ *TRANSAKSI DIHAPUS*
━━━━━━━━━━━━━━━━━━━━━━━

🗑️ Transaksi #{transaction_id} berhasil dihapus:

{transaction.format_display()}
"""
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Gagal menghapus transaksi. Coba lagi nanti.")

    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks."""
        query = update.callback_query
        await query.answer()

        if query.data == "history":
            # Simulate /history command
            user_id = query.from_user.id
            transactions = self.db.get_transactions(user_id, limit=10)

            if not transactions:
                message = "📭 Belum ada transaksi tercatat."
            else:
                lines = ["📋 *RIWAYAT TRANSAKSI*", "━━━━━━━━━━━━━━━━━━━━━━━", ""]
                for i, t in enumerate(transactions, 1):
                    type_emoji = "💰" if t.type == "income" else "💸"
                    sign = "+" if t.type == "income" else "-"
                    amount_str = f"{t.amount:,.0f}".replace(",", ".")
                    date_str = t.created_at.strftime("%d/%m")
                    desc = t.description[:18] + ".." if len(t.description) > 18 else t.description
                    
                    lines.append(f"{type_emoji} *{desc}*")
                    lines.append(f"   📅 {date_str} │ 💵 `{sign}Rp {amount_str}`")
                    lines.append(f"   🆔 `/delete {t.id}`")
                    if i < len(transactions):
                        lines.append("")
                
                lines.append("")
                lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
                message = "\n".join(lines)

            await query.edit_message_text(message, parse_mode="Markdown")

        elif query.data == "summary":
            user_id = query.from_user.id
            now = datetime.now()
            summary = self.db.get_summary(user_id, now.month, now.year)

            income_str = f"{summary['income']:,.0f}".replace(",", ".")
            expense_str = f"{summary['expense']:,.0f}".replace(",", ".")
            balance_str = f"{summary['balance']:,.0f}".replace(",", ".")

            month_names = [
                "", "Januari", "Februari", "Maret", "April", "Mei", "Juni",
                "Juli", "Agustus", "September", "Oktober", "November", "Desember",
            ]

            message = f"""
📊 *RINGKASAN {month_names[now.month].upper()} {now.year}*
━━━━━━━━━━━━━━━━━━━━━━━

💰 Pemasukan: Rp {income_str}
💸 Pengeluaran: Rp {expense_str}
📈 Saldo: Rp {balance_str}
"""
            await query.edit_message_text(message, parse_mode="Markdown")

        elif query.data == "help":
            await query.edit_message_text(HELP_MESSAGE, parse_mode="Markdown")
