import logging
from datetime import datetime
from typing import Optional

from telegram import Update
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
        self.commands = CommandHandler(db_manager, provider_manager)
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
        """Handle incoming text messages for transaction parsing."""
        user_id = update.effective_user.id
        message_text = update.message.text.strip()
        
        if not message_text:
            return
        
        # Show typing indicator
        await update.message.chat.send_action("typing")
        
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
