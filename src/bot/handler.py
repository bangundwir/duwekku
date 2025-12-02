import logging
from datetime import datetime, date
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler as TelegramCommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from src.ai.parser import AIParser
from src.ai.provider_manager import ProviderManager
from src.database.manager import DatabaseManager
from src.models.transaction import Transaction
from src.subscription.manager import SubscriptionManager
from src.analysis.analyzer import FinancialAnalyzer
from .commands import CommandHandler

logger = logging.getLogger(__name__)


class BotHandler:
    """Main Telegram bot handler."""
    
    def __init__(
        self,
        token: str,
        db_manager: DatabaseManager,
        provider_manager: Optional[ProviderManager] = None,
        ai_parser: Optional[AIParser] = None,  # Deprecated, use provider_manager
    ):
        self.token = token
        self.db_manager = db_manager
        self.provider_manager = provider_manager
        self.ai_parser = ai_parser  # Fallback for backward compatibility
        
        # Initialize subscription manager and financial analyzer
        self.subscription_manager = SubscriptionManager(db_manager)
        self.financial_analyzer = FinancialAnalyzer(db_manager, self.subscription_manager)
        
        self.commands = CommandHandler(
            db_manager, 
            provider_manager,
            subscription_manager=self.subscription_manager,
            financial_analyzer=self.financial_analyzer
        )
        self.app: Application = None
    
    def setup(self) -> Application:
        """Set up the bot application with handlers."""
        self.app = Application.builder().token(self.token).build()
        
        # Command handlers
        self.app.add_handler(TelegramCommandHandler("start", self.commands.cmd_start))
        self.app.add_handler(TelegramCommandHandler("help", self.commands.cmd_help))
        self.app.add_handler(TelegramCommandHandler("history", self.commands.cmd_history))
        self.app.add_handler(TelegramCommandHandler("summary", self.commands.cmd_summary))
        self.app.add_handler(TelegramCommandHandler("delete", self.commands.cmd_delete))
        
        # AI Provider commands
        self.app.add_handler(TelegramCommandHandler("provider", self.commands.cmd_provider))
        self.app.add_handler(TelegramCommandHandler("models", self.commands.cmd_models))
        self.app.add_handler(TelegramCommandHandler("model", self.commands.cmd_model))
        
        # Export command
        self.app.add_handler(TelegramCommandHandler("export", self.commands.cmd_export))
        self.app.add_handler(TelegramCommandHandler("exportfull", self.commands.cmd_export_full))
        self.app.add_handler(TelegramCommandHandler("exportsubs", self.commands.cmd_exportsubs))
        
        # Financial Analysis command
        self.app.add_handler(TelegramCommandHandler("analysis", self.commands.cmd_analysis))
        
        # Subscription commands
        self.app.add_handler(TelegramCommandHandler("addsub", self.commands.cmd_addsub))
        self.app.add_handler(TelegramCommandHandler("subs", self.commands.cmd_subs))
        self.app.add_handler(TelegramCommandHandler("delsub", self.commands.cmd_delsub))
        self.app.add_handler(TelegramCommandHandler("renewsub", self.commands.cmd_renewsub))
        self.app.add_handler(TelegramCommandHandler("subcost", self.commands.cmd_subcost))
        
        # Keyboard commands
        self.app.add_handler(TelegramCommandHandler("keyboard", self.commands.cmd_keyboard))
        self.app.add_handler(TelegramCommandHandler("hide", self.commands.cmd_hide))
        
        # Callback handler for inline buttons
        self.app.add_handler(CallbackQueryHandler(self.commands.handle_callback))
        
        # Message handler for transaction parsing
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self.handle_message
        ))
        
        # Error handler
        self.app.add_error_handler(self.error_handler)
        
        return self.app

    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle incoming text messages for transaction/subscription parsing."""
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        if not message_text:
            return
        
        # Handle keyboard button presses
        keyboard_handlers = {
            "📋 History": self.commands.cmd_history,
            "📊 Summary": self.commands.cmd_summary,
            "📅 Langganan": self.commands.cmd_subs,
            "📈 Analisis": self.commands.cmd_analysis,
            "📥 Export": self.commands.cmd_export,
            "⚙️ Settings": self.commands.cmd_provider,
            "📖 Help": self.commands.cmd_help,
            "➕ Catat": self._show_add_transaction_help,
            "⌨️ Hide": self.commands.cmd_hide,
            "⌨️ Show": self.commands.cmd_keyboard,
        }
        
        if message_text in keyboard_handlers:
            handler = keyboard_handlers[message_text]
            await handler(update, context)
            return
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
        # Check if it's a subscription message - expanded keywords
        sub_keywords = ["langganan", "berlangganan", "subscribe", "subscription", "subs", "netflix", "spotify", "youtube premium", "disney", "hbo", "vps", "hosting", "domain"]
        msg_lower = message_text.lower()
        is_subscription = any(kw in msg_lower for kw in sub_keywords)
        
        # Also check for duration patterns that indicate subscription
        duration_patterns = ["bulan", "tahun", "setahun", "sebulan", "minggu"]
        has_duration = any(p in msg_lower for p in duration_patterns)
        
        if is_subscription and has_duration and self.provider_manager and self.subscription_manager:
            # Parse as subscription
            parsed_sub = self.provider_manager.parse_subscription(user_id, message_text)
            
            if parsed_sub and parsed_sub.is_valid():
                from dateutil.relativedelta import relativedelta
                from src.models.subscription import Subscription
                
                # Use parsed start_date if available, otherwise use today
                if parsed_sub.start_date:
                    try:
                        start_date = date.fromisoformat(parsed_sub.start_date)
                    except ValueError:
                        start_date = date.today()
                else:
                    start_date = date.today()
                
                end_date = start_date + relativedelta(months=parsed_sub.duration_months)
                
                sub = Subscription(
                    user_id=user_id,
                    name=parsed_sub.name,
                    amount=parsed_sub.amount,
                    category=parsed_sub.category,
                    start_date=start_date,
                    end_date=end_date,
                )
                
                sub_id = self.subscription_manager.add_subscription(sub)
                sub.id = sub_id
                
                # Also create transaction for the subscription payment
                transaction = Transaction(
                    user_id=user_id,
                    type="expense",
                    amount=parsed_sub.amount,
                    category="langganan",
                    description=f"Langganan {parsed_sub.name}",
                    created_at=datetime.now(),
                )
                saved_tx = self.db_manager.save_transaction(transaction)
                
                # Format amount
                amount_str = f"{parsed_sub.amount:,.0f}".replace(",", ".")
                
                # Duration text
                if parsed_sub.duration_months == 1:
                    dur_text = "1 bulan"
                elif parsed_sub.duration_months == 12:
                    dur_text = "1 tahun"
                else:
                    dur_text = f"{parsed_sub.duration_months} bulan"
                
                keyboard = [
                    [
                        InlineKeyboardButton("📋 Lihat Langganan", callback_data="show_subs"),
                        InlineKeyboardButton("📊 Lihat Transaksi", callback_data="history"),
                    ],
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                tx_info = ""
                if saved_tx:
                    tx_info = f"\n💸 *Transaksi Tercatat:*\n   ID: `{saved_tx.id}` │ Kategori: Langganan"
                
                await update.message.reply_text(
                    f"✅ *LANGGANAN BERHASIL DITAMBAHKAN!*\n"
                    f"━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"📦 *{parsed_sub.name}*\n"
                    f"💵 Biaya: `Rp {amount_str}`\n"
                    f"📁 Kategori: {parsed_sub.category.title()}\n"
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
        
        # Parse transaction using AI (prefer provider_manager)
        parsed = None
        if self.provider_manager:
            parsed = self.provider_manager.parse_transaction(user_id, message_text)
        elif self.ai_parser:
            parsed = self.ai_parser.parse_transaction(message_text)
        
        if not parsed:
            message = """
🤔 *Hmm, saya tidak mengerti...*
━━━━━━━━━━━━━━━━━━━━━━━

Coba ketik dengan format seperti ini:

📤 *Pengeluaran:*
• `beli makan 50rb`
• `bayar listrik 200rb`

📥 *Pemasukan:*
• `gajian 5jt`
• `dapat bonus 1jt`

📅 *Langganan:*
• `langganan netflix 50rb 1 bulan`
• `berlangganan spotify 60rb setahun`

💡 Ketik /help untuk panduan lengkap
"""
            await update.message.reply_text(message, parse_mode="Markdown")
            return
        
        # Create and save transaction
        transaction = Transaction(
            user_id=user_id,
            type=parsed.type,
            amount=parsed.amount,
            category=parsed.category,
            description=parsed.description,
            created_at=datetime.now(),
        )
        
        saved = self.db_manager.save_transaction(transaction)
        
        if saved:
            type_text = "PEMASUKAN" if saved.type == "income" else "PENGELUARAN"
            type_emoji = "💰" if saved.type == "income" else "💸"
            sign = "+" if saved.type == "income" else "-"
            amount_str = f"{saved.amount:,.0f}".replace(",", ".")
            
            message = f"""
✅ *TRANSAKSI TERCATAT!*
━━━━━━━━━━━━━━━━━━━━━━━

{type_emoji} *{type_text}*

{saved.format_display()}

━━━━━━━━━━━━━━━━━━━━━━━
📊 /summary - Lihat ringkasan
🗑️ `/delete {saved.id}` - Batalkan
"""
            await update.message.reply_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text(
                "❌ Gagal menyimpan transaksi. Silakan coba lagi."
            )
    
    async def _show_add_transaction_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show help for adding transactions."""
        message = """
➕ *TAMBAH TRANSAKSI*
━━━━━━━━━━━━━━━━━━━━━━━

Ketik transaksi dengan format natural:

💸 *Pengeluaran:*
• `beli makan 50rb`
• `bayar listrik 500k`
• `belanja bulanan 1.5jt`

💰 *Pemasukan:*
• `gajian 5jt`
• `terima bonus 2jt`
• `dapat freelance 1.5jt`

📅 *Langganan:*
• `langganan netflix 150rb 1 bulan`
• `berlangganan spotify 60rb setahun`

━━━━━━━━━━━━━━━━━━━━━━━
💡 AI akan otomatis mendeteksi jenis dan kategori!
"""
        await update.message.reply_text(message, parse_mode="Markdown")
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle errors gracefully."""
        logger.error(f"Error handling update: {context.error}", exc_info=context.error)
        
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "❌ Terjadi kesalahan. Silakan coba lagi nanti."
            )
    
    def run(self) -> None:
        """Start the bot polling."""
        if not self.app:
            self.setup()
        
        logger.info("Starting bot...")
        self.app.run_polling(allowed_updates=Update.ALL_TYPES)
