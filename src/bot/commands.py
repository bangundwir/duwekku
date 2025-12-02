import io
import logging
from datetime import datetime, date
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from src.database.manager import DatabaseManager
from src.ai.provider_manager import ProviderManager
from src.utils.exporter import TransactionExporter
from src.models.subscription import Subscription, SUBSCRIPTION_CATEGORIES
from src.models.transaction import Transaction
from src.subscription.formatter import SubscriptionFormatter
from src.subscription.keyboard import SubscriptionKeyboardBuilder

logger = logging.getLogger(__name__)

WELCOME_MESSAGE = """
💰 *MONEY TRACKER BOT* 💰
━━━━━━━━━━━━━━━━━━━━━━━

Halo {name}! 👋

Selamat datang di asisten keuangan pribadi Anda!
Saya akan membantu mencatat pemasukan, pengeluaran, dan langganan dengan mudah menggunakan AI.

━━━━━━━━━━━━━━━━━━━━━━━
🚀 *CARA PAKAI*
━━━━━━━━━━━━━━━━━━━━━━━

*💵 Transaksi:*
• `beli makan 50rb`
• `gajian 5jt`

*📅 Langganan:*
• `/addsub langganan netflix 150rb 1 bulan`
• `/addsub berlangganan spotify 60rb setahun`

*📊 Analisis:*
• `/analysis` - Cek kesehatan keuangan
• `/subs` - Lihat semua langganan

━━━━━━━━━━━━━━━━━━━━━━━
Ketik /help untuk panduan lengkap 📖
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

/provider
↳ Lihat AI provider aktif

/provider list
↳ Lihat semua provider tersedia

/provider set `[nama]`
↳ Ganti provider (poe/groq)
↳ Contoh: `/provider set groq`

/models
↳ Lihat model AI tersedia

/model set `[nama]`
↳ Ganti model AI
↳ Contoh: `/model set llama-3.3-70b-versatile`

/export
↳ Export data transaksi (pilih format)

/export csv
↳ Download data dalam format CSV

/export html
↳ Download laporan dalam format HTML

/analysis
↳ Analisis kesehatan keuangan dengan skor dan saran

━━━━━━━━━━━━━━━━━━━━━━━
📅 *LANGGANAN/SUBSCRIPTION:*

/subs
↳ Lihat semua langganan aktif

/addsub
↳ Tambah langganan (dengan menu interaktif)

/addsub `langganan netflix 150rb 1 bulan`
↳ Tambah dengan bahasa natural (AI parsing)

/addsub `langganan spotify 60rb 1 tahun mulai 1 januari 2025`
↳ Tambah dengan tanggal mulai custom

/addsub `[nama]` `[jumlah]` `[mulai]` `[akhir]` `[kategori]`
↳ Tambah langganan baru
↳ Contoh: `/addsub Netflix 150000 2024-01-01 2024-12-31 streaming`

/subs
↳ Lihat semua langganan aktif

/delsub `[id]`
↳ Hapus langganan
↳ Contoh: `/delsub 12345`

/renewsub `[id]` `[tanggal_baru]`
↳ Perpanjang langganan
↳ Contoh: `/renewsub 12345 2025-12-31`

/subcost
↳ Lihat total biaya langganan bulanan

/exportsubs
↳ Export langganan ke HTML (responsive)

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
⌨️ *KEYBOARD:*
━━━━━━━━━━━━━━━━━━━━━━━

/keyboard
↳ Tampilkan keyboard shortcut

/hide
↳ Sembunyikan keyboard

💡 Tekan tombol `⌨️ Hide` untuk menyembunyikan
💡 Ketik /keyboard untuk menampilkan kembali

━━━━━━━━━━━━━━━━━━━━━━━
🤖 AI akan otomatis mendeteksi kategori dari pesan Anda!
"""


class CommandHandler:
    """Handles Telegram bot commands."""

    def __init__(self, db_manager: DatabaseManager, provider_manager: Optional[ProviderManager] = None,
                 subscription_manager=None, financial_analyzer=None):
        self.db = db_manager
        self.provider_manager = provider_manager
        self.subscription_manager = subscription_manager
        self.financial_analyzer = financial_analyzer

    def _get_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Get persistent main keyboard that appears at bottom of chat."""
        keyboard = [
            [
                KeyboardButton("📋 History"),
                KeyboardButton("📊 Summary"),
                KeyboardButton("📅 Langganan"),
            ],
            [
                KeyboardButton("📈 Analisis"),
                KeyboardButton("📥 Export"),
                KeyboardButton("⚙️ Settings"),
            ],
            [
                KeyboardButton("➕ Catat"),
                KeyboardButton("📖 Help"),
                KeyboardButton("⌨️ Hide"),
            ],
        ]
        return ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True,
            is_persistent=False,  # Can be hidden
        )

    async def cmd_keyboard(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /keyboard command - show/hide keyboard."""
        reply_keyboard = self._get_main_keyboard()
        await update.message.reply_text(
            "⌨️ Keyboard ditampilkan!",
            reply_markup=reply_keyboard
        )

    async def cmd_hide(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /hide command - hide keyboard."""
        from telegram import ReplyKeyboardRemove
        await update.message.reply_text(
            "⌨️ Keyboard disembunyikan.\n💡 Ketik /keyboard untuk menampilkan kembali.",
            reply_markup=ReplyKeyboardRemove()
        )

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command."""
        user_name = update.effective_user.first_name or "User"
        message = WELCOME_MESSAGE.format(name=user_name)

        # Persistent keyboard at bottom
        reply_keyboard = self._get_main_keyboard()

        # Send welcome with keyboard
        await update.message.reply_text(
            message, 
            parse_mode="Markdown", 
            reply_markup=reply_keyboard
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
        
        # Provider selection callbacks
        elif query.data.startswith("set_provider:"):
            provider_name = query.data.split(":")[1]
            user_id = query.from_user.id
            
            if self.provider_manager and self.provider_manager.set_user_provider(user_id, provider_name):
                info = self.provider_manager.get_user_provider_info(user_id)
                providers = self.provider_manager.list_providers()
                
                # Rebuild provider buttons
                provider_buttons = []
                for p in providers:
                    if p.is_configured:
                        emoji = "✅" if p.name == info.name else "⬜"
                        provider_buttons.append(
                            InlineKeyboardButton(
                                f"{emoji} {p.display_name}",
                                callback_data=f"set_provider:{p.name}"
                            )
                        )
                
                keyboard = [
                    provider_buttons,
                    [InlineKeyboardButton("🧠 Pilih Model", callback_data="show_models")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"""
✅ *PROVIDER BERHASIL DIGANTI*
━━━━━━━━━━━━━━━━━━━━━━━

📦 *Provider Aktif:*
   {info.display_name}

🧠 *Model Aktif:*
   `{info.current_model}`

━━━━━━━━━━━━━━━━━━━━━━━
*Pilih Provider:*
"""
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "show_models":
            user_id = query.from_user.id
            if self.provider_manager:
                await self._show_models_interactive(query, user_id)
        
        elif query.data.startswith("models_page:"):
            page = int(query.data.split(":")[1])
            user_id = query.from_user.id
            if self.provider_manager:
                await self._show_models_interactive(query, user_id, page)
        
        elif query.data.startswith("set_model:"):
            model_id = query.data.split(":", 1)[1]
            user_id = query.from_user.id
            
            if self.provider_manager and self.provider_manager.set_user_model(user_id, model_id):
                info = self.provider_manager.get_user_provider_info(user_id)
                
                keyboard = [
                    [InlineKeyboardButton("🧠 Pilih Model Lain", callback_data="show_models")],
                    [InlineKeyboardButton("🔙 Kembali ke Provider", callback_data="show_provider")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"""
✅ *MODEL BERHASIL DIGANTI*
━━━━━━━━━━━━━━━━━━━━━━━

📦 *Provider:* {info.display_name}
🧠 *Model:* `{info.current_model}`

━━━━━━━━━━━━━━━━━━━━━━━
Sekarang bot akan menggunakan model ini untuk parsing transaksi.
"""
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "show_provider":
            user_id = query.from_user.id
            if self.provider_manager:
                info = self.provider_manager.get_user_provider_info(user_id)
                providers = self.provider_manager.list_providers()
                
                provider_buttons = []
                for p in providers:
                    if p.is_configured:
                        emoji = "✅" if p.name == info.name else "⬜"
                        provider_buttons.append(
                            InlineKeyboardButton(
                                f"{emoji} {p.display_name}",
                                callback_data=f"set_provider:{p.name}"
                            )
                        )
                
                keyboard = [
                    provider_buttons,
                    [InlineKeyboardButton("🧠 Pilih Model", callback_data="show_models")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = f"""
🤖 *PENGATURAN AI*
━━━━━━━━━━━━━━━━━━━━━━━

📦 *Provider Aktif:*
   {info.display_name}

🧠 *Model Aktif:*
   `{info.current_model}`

━━━━━━━━━━━━━━━━━━━━━━━
*Pilih Provider:*
"""
                await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "noop":
            # Do nothing, just acknowledge
            pass
        
        # Subscription callbacks
        elif query.data == "show_subs":
            user_id = query.from_user.id
            if self.subscription_manager:
                subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
                cost_info = self.subscription_manager.get_monthly_cost(user_id)
                
                if not subscriptions:
                    reply_markup = SubscriptionKeyboardBuilder.category_selection()
                    await query.edit_message_text(
                        "📭 *BELUM ADA LANGGANAN*\n"
                        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        "Tambahkan langganan pertama Anda!\n\n"
                        "💡 Contoh:\n"
                        "`langganan netflix 50rb 1 bulan`",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                    return
                
                # Count by status
                active_count = len([s for s in subscriptions if s.status == "active"])
                expiring_count = len([s for s in subscriptions if s.status == "expiring_soon"])
                expired_count = len([s for s in subscriptions if s.status == "expired"])
                
                lines = [
                    "📅 *DAFTAR LANGGANAN*",
                    "━━━━━━━━━━━━━━━━━━━━━━━",
                    f"💰 Total: *{SubscriptionFormatter.format_amount(cost_info['total'])}*/bulan",
                    f"✅ {active_count} │ ⚠️ {expiring_count} │ ❌ {expired_count}",
                    "",
                ]
                
                # Sort: expiring soon first, then by end date
                sorted_subs = sorted(subscriptions, key=lambda x: (x.status != "expiring_soon", x.days_remaining))
                
                for sub in sorted_subs[:8]:  # Limit to 8 for readability
                    # Calculate progress
                    total_days = (sub.end_date - sub.start_date).days
                    elapsed = (date.today() - sub.start_date).days
                    progress = min(100, max(0, (elapsed / total_days * 100) if total_days > 0 else 0))
                    
                    status_emoji = SubscriptionFormatter.format_status_emoji(sub.status)
                    cat_emoji = SubscriptionFormatter.format_category_emoji(sub.category)
                    countdown = SubscriptionFormatter.format_countdown(sub.days_remaining)
                    progress_bar = SubscriptionFormatter.format_progress_emoji(progress)
                    
                    lines.append(f"{status_emoji} *{sub.name}* {cat_emoji}")
                    lines.append(f"   💵 {SubscriptionFormatter.format_amount(sub.amount)}")
                    lines.append(f"   ⏱️ {countdown}")
                    lines.append(f"   {progress_bar}")
                    lines.append(f"   🆔 `{sub.id}`")
                    lines.append("")
                
                if len(subscriptions) > 8:
                    lines.append(f"_...dan {len(subscriptions) - 8} lainnya_")
                
                keyboard = [
                    [
                        InlineKeyboardButton("➕ Tambah", callback_data="show_addsub"),
                        InlineKeyboardButton("💰 Biaya", callback_data="show_subcost"),
                    ],
                    [
                        InlineKeyboardButton("🗑️ Hapus", callback_data="show_delsub"),
                        InlineKeyboardButton("🔄 Perpanjang", callback_data="show_renewsub"),
                    ],
                    [
                        InlineKeyboardButton("📥 Export HTML", callback_data="export_subs"),
                        InlineKeyboardButton("📊 Export Stats", callback_data="export_subs_enhanced"),
                    ],
                    [
                        InlineKeyboardButton("🔄 Refresh", callback_data="show_subs"),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "show_addsub":
            keyboard = [
                [InlineKeyboardButton("🎬 Streaming", callback_data="addsub_cat:streaming")],
                [InlineKeyboardButton("🖥️ Hosting/VPS", callback_data="addsub_cat:hosting")],
                [InlineKeyboardButton("🌐 Domain", callback_data="addsub_cat:domain")],
                [InlineKeyboardButton("💿 Software", callback_data="addsub_cat:software")],
                [InlineKeyboardButton("📦 Lainnya", callback_data="addsub_cat:other")],
                [InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                "📅 *TAMBAH LANGGANAN*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Pilih kategori atau ketik langsung:\n\n"
                "💡 *Contoh:*\n"
                "`/addsub langganan netflix 150rb 1 bulan`\n"
                "`/addsub berlangganan spotify 60rb setahun`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("addsub_cat:"):
            category = query.data.split(":")[1]
            cat_names = {
                "streaming": "🎬 Streaming (Netflix, Spotify, dll)",
                "hosting": "🖥️ Hosting/VPS",
                "domain": "🌐 Domain",
                "software": "💿 Software",
                "other": "📦 Lainnya",
            }
            
            keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="show_addsub")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await query.edit_message_text(
                f"📅 *TAMBAH {cat_names.get(category, category).upper()}*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"Ketik dengan format natural:\n\n"
                f"💡 *Contoh:*\n"
                f"`/addsub langganan netflix 150rb 1 bulan`\n"
                f"`/addsub vps digitalocean 100rb 3 bulan`\n\n"
                f"Atau format manual:\n"
                f"`/addsub Netflix 150000 2024-01-01 2024-12-31 {category}`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        elif query.data == "show_analysis":
            user_id = query.from_user.id
            if self.financial_analyzer:
                analysis = self.financial_analyzer.analyze(user_id)
                
                if analysis is None:
                    keyboard = [[InlineKeyboardButton("📋 Lihat Transaksi", callback_data="history")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "📊 *ANALISIS KEUANGAN*\n\n"
                        "⚠️ Data tidak cukup (minimal 5 transaksi).",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                    return
                
                def fmt(amount):
                    return f"Rp {amount:,.0f}".replace(",", ".")
                
                # Score visual
                if analysis.score >= 70:
                    score_emoji = "🟢"
                    score_label = "Sehat"
                elif analysis.score >= 40:
                    score_emoji = "🟡"
                    score_label = "Perlu Perhatian"
                else:
                    score_emoji = "🔴"
                    score_label = "Perlu Perbaikan"
                
                score_bar = "█" * (analysis.score // 10) + "░" * (10 - analysis.score // 10)
                trend_emoji = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(analysis.trend, "➡️")
                
                lines = [
                    "📊 *ANALISIS KESEHATAN KEUANGAN*",
                    "━━━━━━━━━━━━━━━━━━━━━━━",
                    "",
                    f"{score_emoji} *Skor: {analysis.score}/100* - {score_label}",
                    f"`{score_bar}`",
                    "",
                    f"📥 Pemasukan: *{fmt(analysis.income_total)}*",
                    f"📤 Pengeluaran: *{fmt(analysis.expense_total)}*",
                    f"💵 Saldo: *{fmt(analysis.balance)}*",
                    "",
                    f"📊 Rasio: `{analysis.expense_ratio:.1f}%` │ {trend_emoji} Trend",
                ]
                
                if analysis.warnings:
                    lines.append("")
                    lines.append("⚠️ " + analysis.warnings[0][:80])
                
                keyboard = [
                    [
                        InlineKeyboardButton("📋 History", callback_data="history"),
                        InlineKeyboardButton("📅 Langganan", callback_data="show_subs"),
                    ],
                    [InlineKeyboardButton("📥 Export Lengkap", callback_data="export:html:all")],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data == "show_subcost":
            user_id = query.from_user.id
            if self.subscription_manager:
                cost_info = self.subscription_manager.get_monthly_cost(user_id)
                
                def fmt(amount):
                    return f"Rp {amount:,.0f}".replace(",", ".")
                
                cat_emoji = {
                    "streaming": "🎬", "hosting": "🖥️", "domain": "🌐",
                    "software": "💿", "other": "📦",
                }
                
                lines = [
                    "💰 *BIAYA LANGGANAN BULANAN*",
                    "━━━━━━━━━━━━━━━━━━━━━━━",
                    "",
                    f"📊 *Total: {fmt(cost_info['total'])}/bulan*",
                    "",
                ]
                
                if cost_info["by_category"]:
                    lines.append("*Per Kategori:*")
                    for cat, amount in sorted(cost_info["by_category"].items(), key=lambda x: -x[1]):
                        emoji = cat_emoji.get(cat, "📦")
                        pct = (amount / cost_info["total"] * 100) if cost_info["total"] > 0 else 0
                        lines.append(f"{emoji} {cat.title()}: {fmt(amount)} ({pct:.1f}%)")
                
                keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)
        
        # Delete subscription callbacks
        elif query.data == "show_delsub":
            user_id = query.from_user.id
            if self.subscription_manager:
                subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
                
                if not subscriptions:
                    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text(
                        "📭 Tidak ada langganan untuk dihapus.",
                        reply_markup=reply_markup
                    )
                    return
                
                def fmt(amount):
                    return f"Rp {amount:,.0f}".replace(",", ".")
                
                lines = [
                    "🗑️ *HAPUS LANGGANAN*",
                    "━━━━━━━━━━━━━━━━━━━━━━━",
                    "",
                    "Pilih langganan yang ingin dihapus:",
                    "",
                ]
                
                # Create buttons for each subscription
                keyboard = []
                for sub in subscriptions:
                    btn_text = f"🗑️ {sub.name} - {fmt(sub.amount)}"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"confirm_delsub:{sub.id}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data.startswith("confirm_delsub:"):
            user_id = query.from_user.id
            sub_id = int(query.data.split(":")[1])
            
            if self.subscription_manager:
                sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
                
                if not sub:
                    await query.edit_message_text("❌ Langganan tidak ditemukan")
                    return
                
                def fmt(amount):
                    return f"Rp {amount:,.0f}".replace(",", ".")
                
                keyboard = [
                    [
                        InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"do_delsub:{sub_id}"),
                        InlineKeyboardButton("❌ Batal", callback_data="show_subs"),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    f"⚠️ *KONFIRMASI HAPUS*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"Yakin ingin menghapus langganan ini?\n\n"
                    f"📦 *{sub.name}*\n"
                    f"💵 {fmt(sub.amount)}/bulan\n"
                    f"📅 Berakhir: {sub.end_date.strftime('%d %b %Y')}\n\n"
                    f"⚠️ Tindakan ini tidak dapat dibatalkan!",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
        
        elif query.data.startswith("do_delsub:"):
            user_id = query.from_user.id
            sub_id = int(query.data.split(":")[1])
            
            if self.subscription_manager:
                sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
                sub_name = sub.name if sub else "Unknown"
                
                if self.subscription_manager.delete_subscription(user_id, sub_id):
                    keyboard = [[InlineKeyboardButton("📋 Lihat Langganan", callback_data="show_subs")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"✅ *LANGGANAN DIHAPUS*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"🗑️ *{sub_name}* berhasil dihapus",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text("❌ Gagal menghapus langganan")
        
        # Renew subscription callbacks
        elif query.data == "show_renewsub":
            user_id = query.from_user.id
            if self.subscription_manager:
                subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
                
                if not subscriptions:
                    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("📭 Tidak ada langganan untuk diperpanjang.", reply_markup=reply_markup)
                    return
                
                lines = [
                    "🔄 *PERPANJANG LANGGANAN*",
                    "━━━━━━━━━━━━━━━━━━━━━━━",
                    "",
                    "Pilih langganan yang ingin diperpanjang:",
                    "",
                ]
                
                keyboard = []
                for sub in sorted(subscriptions, key=lambda x: x.days_remaining):
                    status_emoji = SubscriptionFormatter.format_status_emoji(sub.status)
                    btn_text = f"{status_emoji} {sub.name} ({sub.days_remaining}d)"
                    keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"renew_select:{sub.id}")])
                
                keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")])
                reply_markup = InlineKeyboardMarkup(keyboard)
                await query.edit_message_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data.startswith("renew_select:"):
            sub_id = int(query.data.split(":")[1])
            reply_markup = SubscriptionKeyboardBuilder.renew_options(sub_id)
            
            await query.edit_message_text(
                "🔄 *PILIH DURASI PERPANJANGAN*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Pilih berapa lama ingin memperpanjang:",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
        
        elif query.data.startswith("sub_renew_do:"):
            parts = query.data.split(":")
            sub_id = int(parts[1])
            months = int(parts[2])
            user_id = query.from_user.id
            
            if self.subscription_manager:
                from datetime import timedelta
                sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
                
                if sub:
                    # Calculate new end date (approximate: 30 days per month)
                    new_end = sub.end_date + timedelta(days=months * 30)
                    
                    if self.subscription_manager.renew_subscription(user_id, sub_id, new_end):
                        keyboard = [[InlineKeyboardButton("📋 Lihat Langganan", callback_data="show_subs")]]
                        reply_markup = InlineKeyboardMarkup(keyboard)
                        
                        await query.edit_message_text(
                            f"✅ *LANGGANAN DIPERPANJANG*\n"
                            f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                            f"📦 *{sub.name}*\n"
                            f"📅 Berakhir: {new_end.strftime('%d %b %Y')}\n"
                            f"⏱️ Diperpanjang {months} bulan",
                            parse_mode="Markdown",
                            reply_markup=reply_markup
                        )
                    else:
                        await query.edit_message_text("❌ Gagal memperpanjang langganan")
                else:
                    await query.edit_message_text("❌ Langganan tidak ditemukan")
        
        # Enhanced export subscription callback
        elif query.data == "export_subs_enhanced":
            user_id = query.from_user.id
            if self.subscription_manager:
                subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
                
                if not subscriptions:
                    await query.edit_message_text("📭 Tidak ada langganan untuk diexport")
                    return
                
                await query.edit_message_text("⏳ Sedang menyiapkan laporan interaktif...")
                
                # Generate enhanced HTML
                html_content = TransactionExporter.subscriptions_to_html_enhanced(
                    subscriptions=subscriptions,
                    title="Daftar Langganan"
                )
                
                # Calculate totals
                active_subs = [s for s in subscriptions if s.status != "expired"]
                expiring_subs = [s for s in subscriptions if s.status == "expiring_soon"]
                total_monthly = sum(s.amount for s in active_subs)
                
                filename = f"langganan_enhanced_{datetime.now().strftime('%Y%m%d')}.html"
                html_bytes = io.BytesIO(html_content.encode('utf-8'))
                html_bytes.name = filename
                
                caption = f"""
✅ *EXPORT LANGGANAN INTERAKTIF*
━━━━━━━━━━━━━━━━━━━━━━━
📅 Total: {len(subscriptions)} langganan
✅ Aktif: {len(active_subs)}
⚠️ Segera berakhir: {len(expiring_subs)}
💰 Biaya: {SubscriptionFormatter.format_amount(total_monthly)}/bulan
━━━━━━━━━━━━━━━━━━━━━━━
✨ *Fitur:*
• ⏱️ Live countdown timer
• 🔍 Filter & search
• 📊 Statistik & chart
• 📅 Timeline view
• 🎨 Animasi modern
"""
                await query.message.reply_document(
                    document=html_bytes,
                    filename=filename,
                    caption=caption,
                    parse_mode="Markdown"
                )
        
        # Subscription to Transaction callback
        elif query.data.startswith("sub_to_tx:"):
            user_id = query.from_user.id
            sub_id = int(query.data.split(":")[1])
            
            if self.subscription_manager:
                sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
                
                if not sub:
                    await query.edit_message_text("❌ Langganan tidak ditemukan")
                    return
                
                # Create transaction from subscription
                transaction = Transaction(
                    user_id=user_id,
                    type="expense",
                    amount=sub.amount,
                    category="tagihan",
                    description=f"Pembayaran {sub.name}",
                    created_at=datetime.now(),
                )
                
                saved = self.db.save_transaction(transaction)
                
                if saved:
                    def fmt(amount):
                        return f"Rp {amount:,.0f}".replace(",", ".")
                    
                    keyboard = [
                        [
                            InlineKeyboardButton("📋 Lihat Transaksi", callback_data="history"),
                            InlineKeyboardButton("📅 Lihat Langganan", callback_data="show_subs"),
                        ],
                    ]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    
                    await query.edit_message_text(
                        f"✅ *PEMBAYARAN TERCATAT!*\n"
                        f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                        f"💸 *Pengeluaran*\n"
                        f"📦 {sub.name}\n"
                        f"💵 {fmt(sub.amount)}\n"
                        f"📁 Kategori: Tagihan\n"
                        f"🆔 ID Transaksi: `{saved.id}`\n\n"
                        f"💡 Transaksi ini sudah tercatat di history Anda",
                        parse_mode="Markdown",
                        reply_markup=reply_markup
                    )
                else:
                    await query.edit_message_text("❌ Gagal mencatat transaksi")
        
        # Export callbacks
        elif query.data == "show_export":
            keyboard = [
                [
                    InlineKeyboardButton("📄 CSV (Spreadsheet)", callback_data="export:csv:all"),
                    InlineKeyboardButton("🌐 HTML (Laporan)", callback_data="export:html:all"),
                ],
                [
                    InlineKeyboardButton("📅 Bulan Ini (CSV)", callback_data="export:csv:month"),
                    InlineKeyboardButton("📅 Bulan Ini (HTML)", callback_data="export:html:month"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = """
📥 *EXPORT DATA TRANSAKSI*
━━━━━━━━━━━━━━━━━━━━━━━

Pilih format export:

📄 *CSV* - Untuk dibuka di Excel/Google Sheets
🌐 *HTML* - Laporan visual yang bisa dicetak

━━━━━━━━━━━━━━━━━━━━━━━
*Pilih format:*
"""
            await query.edit_message_text(message, parse_mode="Markdown", reply_markup=reply_markup)
        
        elif query.data.startswith("export:"):
            parts = query.data.split(":")
            format_type = parts[1]  # csv or html
            scope = parts[2]  # all or month
            user_id = query.from_user.id
            month_only = (scope == "month")
            
            await query.edit_message_text("⏳ Sedang menyiapkan file export...")
            
            # Create a fake message object to reuse export methods
            if format_type == "csv":
                await self._send_csv_export(query.message, user_id, month_only)
            elif format_type == "html":
                await self._send_html_export(query.message, user_id, month_only)
        
        # Export subscriptions callback (basic HTML)
        elif query.data == "export_subs":
            user_id = query.from_user.id
            if self.subscription_manager:
                subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
                
                if not subscriptions:
                    keyboard = [[InlineKeyboardButton("🔙 Kembali", callback_data="show_subs")]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await query.edit_message_text("📭 Tidak ada langganan untuk diexport", reply_markup=reply_markup)
                    return
                
                await query.edit_message_text("⏳ Sedang menyiapkan laporan langganan...")
                
                # Generate subscription HTML
                html_content = TransactionExporter.subscriptions_to_html(
                    subscriptions=subscriptions,
                    title="Daftar Langganan"
                )
                
                # Calculate totals
                active_subs = [s for s in subscriptions if s.status != "expired"]
                total_monthly = sum(s.amount for s in active_subs)
                
                filename = f"langganan_{datetime.now().strftime('%Y%m%d')}.html"
                html_bytes = io.BytesIO(html_content.encode('utf-8'))
                html_bytes.name = filename
                
                caption = f"""
✅ *EXPORT DAFTAR LANGGANAN*
━━━━━━━━━━━━━━━━━━━━━━━
📅 Total: {len(subscriptions)} langganan
✅ Aktif: {len(active_subs)}
💰 Biaya: {SubscriptionFormatter.format_amount(total_monthly)}/bulan
━━━━━━━━━━━━━━━━━━━━━━━
💡 Buka di browser untuk melihat
"""
                await query.message.reply_document(
                    document=html_bytes,
                    filename=filename,
                    caption=caption,
                    parse_mode="Markdown"
                )

    async def cmd_provider(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /provider command - show provider with interactive buttons."""
        if not self.provider_manager:
            await update.message.reply_text("❌ Provider manager tidak tersedia")
            return
        
        user_id = update.effective_user.id
        info = self.provider_manager.get_user_provider_info(user_id)
        providers = self.provider_manager.list_providers()
        
        if not info:
            await update.message.reply_text("❌ Tidak ada provider yang dikonfigurasi")
            return
        
        # Build provider buttons
        provider_buttons = []
        for p in providers:
            if p.is_configured:
                emoji = "✅" if p.name == info.name else "⬜"
                provider_buttons.append(
                    InlineKeyboardButton(
                        f"{emoji} {p.display_name}",
                        callback_data=f"set_provider:{p.name}"
                    )
                )
        
        keyboard = [
            provider_buttons,
            [InlineKeyboardButton("🧠 Pilih Model", callback_data="show_models")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        message = f"""
🤖 *PENGATURAN AI*
━━━━━━━━━━━━━━━━━━━━━━━

📦 *Provider Aktif:*
   {info.display_name}

🧠 *Model Aktif:*
   `{info.current_model}`

━━━━━━━━━━━━━━━━━━━━━━━
*Pilih Provider:*
"""
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)

    async def cmd_models(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /models command - list available models with interactive buttons."""
        if not self.provider_manager:
            await update.message.reply_text("❌ Provider manager tidak tersedia")
            return
        
        user_id = update.effective_user.id
        await self._show_models_interactive(update.message, user_id)
    
    async def _show_models_interactive(self, message_or_query, user_id: int, page: int = 0) -> None:
        """Show models with interactive pagination."""
        info = self.provider_manager.get_user_provider_info(user_id)
        models = self.provider_manager.list_models(user_id)
        
        if not models:
            text = "❌ Tidak dapat mengambil daftar model"
            if hasattr(message_or_query, 'edit_message_text'):
                await message_or_query.edit_message_text(text)
            else:
                await message_or_query.reply_text(text)
            return
        
        # Pagination settings
        models_per_page = 8
        total_pages = (len(models) + models_per_page - 1) // models_per_page
        page = max(0, min(page, total_pages - 1))
        
        start_idx = page * models_per_page
        end_idx = min(start_idx + models_per_page, len(models))
        page_models = models[start_idx:end_idx]
        
        current_model = info.current_model if info else None
        
        # Build model buttons (2 per row)
        keyboard = []
        for i in range(0, len(page_models), 2):
            row = []
            for m in page_models[i:i+2]:
                emoji = "✅" if m.id == current_model else "⬜"
                # Truncate long model names
                display_name = m.id[:20] + ".." if len(m.id) > 20 else m.id
                row.append(InlineKeyboardButton(
                    f"{emoji} {display_name}",
                    callback_data=f"set_model:{m.id}"
                ))
            keyboard.append(row)
        
        # Navigation buttons
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"models_page:{page-1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"models_page:{page+1}"))
        keyboard.append(nav_row)
        
        # Back button
        keyboard.append([InlineKeyboardButton("🔙 Kembali ke Provider", callback_data="show_provider")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        text = f"""
🧠 *PILIH MODEL AI*
━━━━━━━━━━━━━━━━━━━━━━━
📦 Provider: *{info.display_name if info else 'Unknown'}*
✅ Model aktif: `{current_model}`
━━━━━━━━━━━━━━━━━━━━━━━

*Tap untuk memilih model:*
"""
        
        if hasattr(message_or_query, 'edit_message_text'):
            await message_or_query.edit_message_text(text, parse_mode="Markdown", reply_markup=reply_markup)
        else:
            await message_or_query.reply_text(text, parse_mode="Markdown", reply_markup=reply_markup)

    async def cmd_model(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /model command - redirect to interactive model selection."""
        if not self.provider_manager:
            await update.message.reply_text("❌ Provider manager tidak tersedia")
            return
        
        user_id = update.effective_user.id
        args = context.args or []
        
        # If user provides model name directly, set it
        if args and args[0] == "set" and len(args) > 1:
            model_id = args[1]
            if self.provider_manager.set_user_model(user_id, model_id):
                info = self.provider_manager.get_user_provider_info(user_id)
                keyboard = [[InlineKeyboardButton("🧠 Lihat Model Lain", callback_data="show_models")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                message = f"""
✅ *MODEL BERHASIL DIGANTI*
━━━━━━━━━━━━━━━━━━━━━━━

📦 *Provider:* {info.display_name}
🧠 *Model:* `{info.current_model}`
"""
                await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
            else:
                await update.message.reply_text(
                    f"❌ Gagal mengatur model `{model_id}`\n\n"
                    f"💡 Ketik `/models` untuk melihat model tersedia",
                    parse_mode="Markdown"
                )
            return
        
        # Show interactive model selection
        await self._show_models_interactive(update.message, user_id)

    async def cmd_export(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /export [csv|html] command - export transaction data."""
        user_id = update.effective_user.id
        args = context.args or []
        
        if not args:
            # Show export options with buttons
            keyboard = [
                [
                    InlineKeyboardButton("📄 CSV (Spreadsheet)", callback_data="export:csv:all"),
                    InlineKeyboardButton("🌐 HTML (Laporan)", callback_data="export:html:all"),
                ],
                [
                    InlineKeyboardButton("📅 Bulan Ini (CSV)", callback_data="export:csv:month"),
                    InlineKeyboardButton("📅 Bulan Ini (HTML)", callback_data="export:html:month"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            message = """
📥 *EXPORT DATA TRANSAKSI*
━━━━━━━━━━━━━━━━━━━━━━━

Pilih format export:

📄 *CSV* - Untuk dibuka di Excel/Google Sheets
🌐 *HTML* - Laporan visual yang bisa dicetak

━━━━━━━━━━━━━━━━━━━━━━━
*Pilih format:*
"""
            await update.message.reply_text(message, parse_mode="Markdown", reply_markup=reply_markup)
            return
        
        format_type = args[0].lower()
        
        if format_type == "csv":
            await self._send_csv_export(update.message, user_id)
        elif format_type == "html":
            await self._send_html_export(update.message, user_id)
        else:
            await update.message.reply_text(
                "❌ Format tidak dikenal.\n\nGunakan: `/export csv` atau `/export html`",
                parse_mode="Markdown"
            )
    
    async def _send_csv_export(self, message, user_id: int, month_only: bool = False) -> None:
        """Send CSV export file."""
        if month_only:
            now = datetime.now()
            transactions = self.db.get_transactions_by_month(user_id, now.month, now.year)
            filename = f"transaksi_{now.strftime('%Y-%m')}.csv"
            title = f"Transaksi {now.strftime('%B %Y')}"
        else:
            transactions = self.db.get_all_transactions(user_id)
            filename = f"transaksi_semua_{datetime.now().strftime('%Y%m%d')}.csv"
            title = "Semua Transaksi"
        
        if not transactions:
            await message.reply_text("📭 Tidak ada transaksi untuk diexport")
            return
        
        csv_content = TransactionExporter.to_csv(transactions)
        
        # Send as document
        csv_bytes = io.BytesIO(csv_content.encode('utf-8-sig'))  # UTF-8 with BOM for Excel
        csv_bytes.name = filename
        
        caption = f"""
✅ *EXPORT BERHASIL*
━━━━━━━━━━━━━━━━━━━━━━━
📄 Format: CSV
📊 {title}
📝 Total: {len(transactions)} transaksi
━━━━━━━━━━━━━━━━━━━━━━━
💡 Buka dengan Excel atau Google Sheets
"""
        await message.reply_document(
            document=csv_bytes,
            filename=filename,
            caption=caption,
            parse_mode="Markdown"
        )
    
    async def _send_html_export(self, message, user_id: int, month_only: bool = False) -> None:
        """Send HTML export file."""
        if month_only:
            now = datetime.now()
            transactions = self.db.get_transactions_by_month(user_id, now.month, now.year)
            summary = self.db.get_summary(user_id, now.month, now.year)
            filename = f"laporan_{now.strftime('%Y-%m')}.html"
            title = f"Laporan Keuangan {now.strftime('%B %Y')}"
        else:
            transactions = self.db.get_all_transactions(user_id)
            # Calculate total summary
            total_income = sum(t.amount for t in transactions if t.type == "income")
            total_expense = sum(t.amount for t in transactions if t.type == "expense")
            summary = {"income": total_income, "expense": total_expense, "balance": total_income - total_expense}
            filename = f"laporan_semua_{datetime.now().strftime('%Y%m%d')}.html"
            title = "Laporan Keuangan Lengkap"
        
        if not transactions:
            await message.reply_text("📭 Tidak ada transaksi untuk diexport")
            return
        
        html_content = TransactionExporter.to_html(transactions, title=title, summary=summary)
        
        # Send as document
        html_bytes = io.BytesIO(html_content.encode('utf-8'))
        html_bytes.name = filename
        
        caption = f"""
✅ *EXPORT BERHASIL*
━━━━━━━━━━━━━━━━━━━━━━━
🌐 Format: HTML
📊 {title}
📝 Total: {len(transactions)} transaksi
━━━━━━━━━━━━━━━━━━━━━━━
💡 Buka di browser untuk melihat/cetak
"""
        await message.reply_document(
            document=html_bytes,
            filename=filename,
            caption=caption,
            parse_mode="Markdown"
        )

    # ==================== FINANCIAL ANALYSIS COMMANDS ====================
    
    async def cmd_analysis(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /analysis command - show financial health analysis with interactive buttons."""
        user_id = update.effective_user.id
        
        if not self.financial_analyzer:
            await update.message.reply_text("❌ Fitur analisis belum tersedia")
            return
        
        # Get analysis
        analysis = self.financial_analyzer.analyze(user_id)
        
        if analysis is None:
            keyboard = [
                [InlineKeyboardButton("📋 Lihat Transaksi", callback_data="history")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📊 *ANALISIS KEUANGAN*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "⚠️ Data tidak cukup untuk analisis.\n"
                "Minimal 5 transaksi diperlukan.\n\n"
                "💡 Tambahkan lebih banyak transaksi terlebih dahulu.",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Score emoji and visual bar
        if analysis.score >= 70:
            score_emoji = "🟢"
            score_label = "Sehat"
            score_bar = "█" * (analysis.score // 10) + "░" * (10 - analysis.score // 10)
        elif analysis.score >= 40:
            score_emoji = "🟡"
            score_label = "Perlu Perhatian"
            score_bar = "█" * (analysis.score // 10) + "░" * (10 - analysis.score // 10)
        else:
            score_emoji = "🔴"
            score_label = "Perlu Perbaikan"
            score_bar = "█" * (analysis.score // 10) + "░" * (10 - analysis.score // 10)
        
        # Trend emoji
        trend_emoji = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(analysis.trend, "➡️")
        trend_text = {"improving": "Membaik", "stable": "Stabil", "declining": "Menurun"}.get(analysis.trend, "Stabil")
        
        # Format amounts
        def fmt(amount):
            return f"Rp {amount:,.0f}".replace(",", ".")
        
        # Build message
        lines = [
            "📊 *ANALISIS KESEHATAN KEUANGAN*",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"{score_emoji} *Skor: {analysis.score}/100* - {score_label}",
            f"`{score_bar}`",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "*💰 RINGKASAN BULAN INI*",
            "",
            f"📥 Pemasukan: *{fmt(analysis.income_total)}*",
            f"📤 Pengeluaran: *{fmt(analysis.expense_total)}*",
            f"💵 Saldo: *{fmt(analysis.balance)}*",
            "",
            f"📊 Rasio Pengeluaran: `{analysis.expense_ratio:.1f}%`",
            f"💎 Tingkat Tabungan: `{analysis.savings_rate:.1f}%`",
            f"{trend_emoji} Trend: *{trend_text}*",
        ]
        
        # Top categories with visual bars
        if analysis.top_categories:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("*💸 TOP 3 PENGELUARAN*")
            lines.append("")
            for i, (cat, amount, pct) in enumerate(analysis.top_categories[:3], 1):
                bar_len = int(pct / 10)
                bar = "▓" * bar_len + "░" * (10 - bar_len)
                lines.append(f"{i}. *{cat.title()}*")
                lines.append(f"   {fmt(amount)} ({pct:.1f}%)")
                lines.append(f"   `{bar}`")
        
        # Warnings
        if analysis.warnings:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("*⚠️ PERINGATAN*")
            for w in analysis.warnings[:2]:
                lines.append(f"• {w}")
        
        # Subscription info
        if analysis.subscription_count > 0:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("*📅 LANGGANAN AKTIF*")
            lines.append(f"📦 Total: {analysis.subscription_count} langganan")
            lines.append(f"💰 Biaya: {fmt(analysis.subscription_monthly_cost)}/bulan")
            
            if analysis.expiring_subscriptions:
                lines.append("")
                lines.append("⚠️ *Segera Berakhir:*")
                for sub in analysis.expiring_subscriptions[:3]:
                    lines.append(f"• {sub.name} ({sub.days_remaining} hari)")
        
        # Suggestions (shortened)
        if analysis.suggestions:
            lines.append("")
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("*💡 SARAN*")
            for s in analysis.suggestions[:2]:
                # Shorten long suggestions
                if len(s) > 100:
                    s = s[:100] + "..."
                lines.append(f"• {s}")
        
        # Action buttons
        keyboard = [
            [
                InlineKeyboardButton("📋 History", callback_data="history"),
                InlineKeyboardButton("📊 Summary", callback_data="summary"),
            ],
            [
                InlineKeyboardButton("📅 Langganan", callback_data="show_subs"),
                InlineKeyboardButton("📥 Export", callback_data="show_export"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)

    # ==================== SUBSCRIPTION COMMANDS ====================
    
    async def cmd_addsub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /addsub command - with AI parsing support."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        args = context.args or []
        
        if not args:
            # Show interactive menu
            keyboard = [
                [InlineKeyboardButton("🎬 Streaming", callback_data="addsub_cat:streaming")],
                [InlineKeyboardButton("🖥️ Hosting/VPS", callback_data="addsub_cat:hosting")],
                [InlineKeyboardButton("🌐 Domain", callback_data="addsub_cat:domain")],
                [InlineKeyboardButton("💿 Software", callback_data="addsub_cat:software")],
                [InlineKeyboardButton("📦 Lainnya", callback_data="addsub_cat:other")],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📅 *TAMBAH LANGGANAN*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Pilih kategori atau ketik langsung:\n\n"
                "💡 *Contoh natural:*\n"
                "• `langganan netflix 150rb 1 bulan`\n"
                "• `berlangganan spotify 60rb setahun`\n"
                "• `vps digitalocean 100rb 3 bulan`\n\n"
                "Atau gunakan format:\n"
                "`/addsub [nama] [jumlah] [mulai] [akhir] [kategori]`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Check if it's natural language (contains words like "langganan", "bulan", etc)
        full_text = " ".join(args)
        is_natural = any(word in full_text.lower() for word in ["langganan", "berlangganan", "bulan", "tahun", "subscribe"])
        
        if is_natural and self.provider_manager:
            # Use AI to parse
            await update.message.chat.send_action("typing")
            parsed = self.provider_manager.parse_subscription(user_id, full_text)
            
            if parsed and parsed.is_valid():
                from dateutil.relativedelta import relativedelta
                
                # Use parsed start_date if available, otherwise use today
                if parsed.start_date:
                    try:
                        start_date = date.fromisoformat(parsed.start_date)
                    except ValueError:
                        start_date = date.today()
                else:
                    start_date = date.today()
                
                end_date = start_date + relativedelta(months=parsed.duration_months)
                
                sub = Subscription(
                    user_id=user_id,
                    name=parsed.name,
                    amount=parsed.amount,
                    category=parsed.category,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                sub_id = self.subscription_manager.add_subscription(sub)
                sub.id = sub_id
                
                # Also create transaction for the subscription payment
                transaction = Transaction(
                    user_id=user_id,
                    type="expense",
                    amount=parsed.amount,
                    category="langganan",
                    description=f"Langganan {parsed.name}",
                    created_at=datetime.now(),
                )
                saved_tx = self.db.save_transaction(transaction)
                
                # Format amount
                amount_str = f"{parsed.amount:,.0f}".replace(",", ".")
                
                # Duration text
                if parsed.duration_months == 1:
                    dur_text = "1 bulan"
                elif parsed.duration_months == 12:
                    dur_text = "1 tahun"
                else:
                    dur_text = f"{parsed.duration_months} bulan"
                
                # Show with action buttons
                keyboard = [
                    [
                        InlineKeyboardButton("📋 Lihat Langganan", callback_data="show_subs"),
                        InlineKeyboardButton("📊 Lihat Transaksi", callback_data="history"),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                tx_info = ""
                if saved_tx:
                    tx_info = f"\n\n💸 *Transaksi Tercatat:*\n   ID: `{saved_tx.id}` │ Kategori: Langganan"
                
                await update.message.reply_text(
                    f"✅ *LANGGANAN BERHASIL DITAMBAHKAN!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 *{parsed.name}*\n"
                    f"💵 Biaya: `Rp {amount_str}`\n"
                    f"📁 Kategori: {parsed.category.title()}\n"
                    f"⏱️ Durasi: {dur_text}\n\n"
                    f"📅 *Periode Langganan:*\n"
                    f"   Mulai: `{start_date.strftime('%d %B %Y')}`\n"
                    f"   Berakhir: `{end_date.strftime('%d %B %Y')}`\n\n"
                    f"⏳ Sisa waktu: *{sub.days_remaining} hari*\n"
                    f"🆔 ID Langganan: `{sub_id}`"
                    f"{tx_info}",
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                )
                return
        
        # Manual format: /addsub name amount start end [category]
        if len(args) < 4:
            await update.message.reply_text(
                "❌ *FORMAT SALAH*\n\n"
                "Gunakan:\n"
                "`/addsub [nama] [jumlah] [mulai] [akhir] [kategori]`\n\n"
                "*Atau ketik natural:*\n"
                "`/addsub langganan netflix 150rb 1 bulan`\n\n"
                "*Kategori:* streaming, hosting, domain, software, other",
                parse_mode="Markdown"
            )
            return
        
        try:
            name = args[0]
            amount = float(args[1].replace(".", "").replace(",", ""))
            start_date = date.fromisoformat(args[2])
            end_date = date.fromisoformat(args[3])
            category = args[4].lower() if len(args) > 4 else "other"
            
            if category not in SUBSCRIPTION_CATEGORIES:
                category = "other"
            
            if end_date < start_date:
                await update.message.reply_text("❌ Tanggal berakhir harus setelah tanggal mulai")
                return
            
            if amount <= 0:
                await update.message.reply_text("❌ Jumlah harus lebih dari 0")
                return
            
            sub = Subscription(
                user_id=user_id,
                name=name,
                amount=amount,
                category=category,
                start_date=start_date,
                end_date=end_date,
            )
            
            sub_id = self.subscription_manager.add_subscription(sub)
            sub.id = sub_id
            
            keyboard = [
                [
                    InlineKeyboardButton("📋 Lihat Semua", callback_data="show_subs"),
                    InlineKeyboardButton("➕ Tambah Lagi", callback_data="show_addsub"),
                ],
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"✅ *LANGGANAN DITAMBAHKAN*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{sub.format_display()}",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            
        except ValueError:
            await update.message.reply_text(
                f"❌ Format tidak valid.\n\n"
                f"Pastikan:\n"
                f"• Jumlah adalah angka\n"
                f"• Tanggal format YYYY-MM-DD\n\n"
                f"Contoh: `/addsub Netflix 150000 2024-01-01 2024-12-31 streaming`",
                parse_mode="Markdown"
            )

    async def cmd_subs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /subs command - list all subscriptions with interactive buttons."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
        
        if not subscriptions:
            keyboard = [[InlineKeyboardButton("➕ Tambah Langganan", callback_data="show_addsub")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                "📭 *BELUM ADA LANGGANAN*\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                "Tambahkan langganan pertama Anda!\n\n"
                "💡 Ketik: `langganan netflix 150rb 1 bulan`",
                parse_mode="Markdown",
                reply_markup=reply_markup
            )
            return
        
        # Count by status
        cost_info = self.subscription_manager.get_monthly_cost(user_id)
        active_count = len([s for s in subscriptions if s.status == "active"])
        expiring_count = len([s for s in subscriptions if s.status == "expiring_soon"])
        expired_count = len([s for s in subscriptions if s.status == "expired"])
        
        lines = [
            "📅 *DAFTAR LANGGANAN*",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            f"💰 Total: *{SubscriptionFormatter.format_amount(cost_info['total'])}*/bulan",
            f"✅ {active_count} aktif │ ⚠️ {expiring_count} segera │ ❌ {expired_count} expired",
            "",
        ]
        
        # Sort: expiring soon first
        sorted_subs = sorted(subscriptions, key=lambda x: (x.status != "expiring_soon", x.days_remaining))
        
        for sub in sorted_subs[:10]:  # Limit to 10
            # Calculate progress
            total_days = (sub.end_date - sub.start_date).days
            elapsed = (date.today() - sub.start_date).days
            progress = min(100, max(0, (elapsed / total_days * 100) if total_days > 0 else 0))
            
            status_emoji = SubscriptionFormatter.format_status_emoji(sub.status)
            cat_emoji = SubscriptionFormatter.format_category_emoji(sub.category)
            countdown = SubscriptionFormatter.format_countdown(sub.days_remaining)
            progress_bar = SubscriptionFormatter.format_progress_emoji(progress)
            
            lines.append(f"{status_emoji} *{sub.name}* {cat_emoji}")
            lines.append(f"   💵 {SubscriptionFormatter.format_amount(sub.amount)}")
            lines.append(f"   ⏱️ {countdown}")
            lines.append(f"   {progress_bar}")
            lines.append(f"   🆔 `{sub.id}`")
            lines.append("")
        
        if len(subscriptions) > 10:
            lines.append(f"_...dan {len(subscriptions) - 10} lainnya_")
        
        # Action buttons
        keyboard = [
            [
                InlineKeyboardButton("➕ Tambah", callback_data="show_addsub"),
                InlineKeyboardButton("💰 Biaya", callback_data="show_subcost"),
            ],
            [
                InlineKeyboardButton("🗑️ Hapus", callback_data="show_delsub"),
                InlineKeyboardButton("🔄 Perpanjang", callback_data="show_renewsub"),
            ],
            [
                InlineKeyboardButton("📥 Export", callback_data="export_subs"),
                InlineKeyboardButton("📊 Stats", callback_data="export_subs_enhanced"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=reply_markup)

    async def cmd_delsub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /delsub [id] command."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        args = context.args or []
        
        if not args:
            await update.message.reply_text(
                "❌ *FORMAT SALAH*\n\n"
                "Gunakan: `/delsub [id]`\n"
                "Contoh: `/delsub 12345`\n\n"
                "💡 Lihat ID di `/subs`",
                parse_mode="Markdown"
            )
            return
        
        try:
            sub_id = int(args[0])
        except ValueError:
            await update.message.reply_text("❌ ID harus berupa angka")
            return
        
        # Get subscription first
        sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
        if not sub:
            await update.message.reply_text(
                f"❌ Langganan dengan ID `{sub_id}` tidak ditemukan\n\n"
                f"💡 Cek ID yang benar di `/subs`",
                parse_mode="Markdown"
            )
            return
        
        if self.subscription_manager.delete_subscription(user_id, sub_id):
            await update.message.reply_text(
                f"✅ *LANGGANAN DIHAPUS*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"🗑️ {sub.name} berhasil dihapus",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Gagal menghapus langganan")

    async def cmd_renewsub(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /renewsub [id] [new_end_date] command."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        args = context.args or []
        
        if len(args) < 2:
            await update.message.reply_text(
                "❌ *FORMAT SALAH*\n\n"
                "Gunakan: `/renewsub [id] [tanggal_baru]`\n"
                "Contoh: `/renewsub 12345 2025-12-31`\n\n"
                "💡 Lihat ID di `/subs`",
                parse_mode="Markdown"
            )
            return
        
        try:
            sub_id = int(args[0])
            new_end_date = date.fromisoformat(args[1])
        except ValueError:
            await update.message.reply_text(
                "❌ Format tidak valid.\n"
                "ID harus angka, tanggal format YYYY-MM-DD",
                parse_mode="Markdown"
            )
            return
        
        # Get subscription first
        sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
        if not sub:
            await update.message.reply_text(
                f"❌ Langganan dengan ID `{sub_id}` tidak ditemukan",
                parse_mode="Markdown"
            )
            return
        
        if self.subscription_manager.renew_subscription(user_id, sub_id, new_end_date):
            # Get updated subscription
            updated_sub = self.subscription_manager.get_subscription_by_id(user_id, sub_id)
            await update.message.reply_text(
                f"✅ *LANGGANAN DIPERPANJANG*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"{updated_sub.format_display()}",
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ Gagal memperpanjang langganan")

    async def cmd_subcost(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /subcost command - show subscription costs."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        cost_info = self.subscription_manager.get_monthly_cost(user_id)
        
        def fmt(amount):
            return f"Rp {amount:,.0f}".replace(",", ".")
        
        if cost_info["count"] == 0:
            await update.message.reply_text(
                "📭 Belum ada langganan aktif.\n"
                "Tambahkan dengan `/addsub`",
                parse_mode="Markdown"
            )
            return
        
        # Category emoji
        cat_emoji = {
            "streaming": "🎬",
            "hosting": "🖥️",
            "domain": "🌐",
            "software": "💿",
            "other": "📦",
        }
        
        lines = [
            "💰 *BIAYA LANGGANAN BULANAN*",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "",
            f"📊 *Total: {fmt(cost_info['total'])}/bulan*",
            "",
            "━━━━━━━━━━━━━━━━━━━━━━━",
            "*Per Kategori:*",
            "",
        ]
        
        for category, amount in sorted(cost_info["by_category"].items(), key=lambda x: -x[1]):
            emoji = cat_emoji.get(category, "📦")
            pct = (amount / cost_info["total"] * 100) if cost_info["total"] > 0 else 0
            lines.append(f"{emoji} {category.title()}: {fmt(amount)} ({pct:.1f}%)")
        
        lines.append("")
        lines.append(f"📝 Total {cost_info['count']} langganan aktif")
        
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

    async def cmd_export_full(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /exportfull command - export full HTML report with analysis and subscriptions."""
        user_id = update.effective_user.id
        
        await update.message.reply_text("⏳ Sedang menyiapkan laporan lengkap...")
        
        # Get all data
        transactions = self.db.get_all_transactions(user_id)
        
        subscriptions = []
        if self.subscription_manager:
            subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
        
        analysis = None
        if self.financial_analyzer:
            analysis = self.financial_analyzer.analyze(user_id)
        
        if not transactions and not subscriptions:
            await update.message.reply_text("📭 Tidak ada data untuk diexport")
            return
        
        # Generate full HTML
        html_content = TransactionExporter.to_html_full(
            transactions=transactions,
            subscriptions=subscriptions,
            analysis=analysis,
            title="Laporan Keuangan Lengkap"
        )
        
        # Send as document
        filename = f"laporan_lengkap_{datetime.now().strftime('%Y%m%d')}.html"
        html_bytes = io.BytesIO(html_content.encode('utf-8'))
        html_bytes.name = filename
        
        caption = f"""
✅ *EXPORT LAPORAN LENGKAP*
━━━━━━━━━━━━━━━━━━━━━━━
🌐 Format: HTML Interaktif
📝 Transaksi: {len(transactions)}
📅 Langganan: {len(subscriptions)}
📊 Analisis: {'Ya' if analysis else 'Tidak'}
━━━━━━━━━━━━━━━━━━━━━━━
💡 Buka di browser untuk melihat
"""
        await update.message.reply_document(
            document=html_bytes,
            filename=filename,
            caption=caption,
            parse_mode="Markdown"
        )

    async def cmd_exportsubs(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /exportsubs command - export subscriptions to HTML."""
        user_id = update.effective_user.id
        
        if not self.subscription_manager:
            await update.message.reply_text("❌ Fitur subscription belum tersedia")
            return
        
        subscriptions = self.subscription_manager.get_subscriptions(user_id, include_expired=True)
        
        if not subscriptions:
            await update.message.reply_text("📭 Tidak ada langganan untuk diexport")
            return
        
        await update.message.reply_text("⏳ Sedang menyiapkan laporan langganan...")
        
        # Generate subscription HTML
        html_content = TransactionExporter.subscriptions_to_html(
            subscriptions=subscriptions,
            title="Daftar Langganan"
        )
        
        # Calculate totals for caption
        active_subs = [s for s in subscriptions if s.status != "expired"]
        total_monthly = sum(s.amount for s in active_subs)
        
        def fmt(amount):
            return f"Rp {amount:,.0f}".replace(",", ".")
        
        # Send as document
        filename = f"langganan_{datetime.now().strftime('%Y%m%d')}.html"
        html_bytes = io.BytesIO(html_content.encode('utf-8'))
        html_bytes.name = filename
        
        caption = f"""
✅ *EXPORT DAFTAR LANGGANAN*
━━━━━━━━━━━━━━━━━━━━━━━
📅 Total Langganan: {len(subscriptions)}
✅ Aktif: {len(active_subs)}
💰 Biaya Bulanan: {fmt(total_monthly)}
━━━━━━━━━━━━━━━━━━━━━━━
💡 Buka di browser untuk melihat
📱 Responsive untuk mobile
"""
        await update.message.reply_document(
            document=html_bytes,
            filename=filename,
            caption=caption,
            parse_mode="Markdown"
        )
