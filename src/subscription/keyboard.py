"""Subscription Keyboard Builder for interactive Telegram buttons."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional, List


class SubscriptionKeyboardBuilder:
    """Build interactive inline keyboards for subscription management."""
    
    @staticmethod
    def main_menu() -> InlineKeyboardMarkup:
        """Main subscription menu with action buttons.
        
        Returns:
            InlineKeyboardMarkup with main menu buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("➕ Tambah", callback_data="sub_add"),
                InlineKeyboardButton("📋 Daftar", callback_data="sub_list"),
            ],
            [
                InlineKeyboardButton("💰 Biaya", callback_data="sub_cost"),
                InlineKeyboardButton("📥 Export", callback_data="sub_export"),
            ],
            [
                InlineKeyboardButton("🔍 Filter", callback_data="sub_filter"),
                InlineKeyboardButton("📊 Statistik", callback_data="sub_stats"),
            ],
            [
                InlineKeyboardButton("🔙 Menu Utama", callback_data="main_menu"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def subscription_list(
        subscriptions: list,
        page: int = 0,
        per_page: int = 5,
        filter_status: str = "all"
    ) -> InlineKeyboardMarkup:
        """Subscription list with pagination and filter.
        
        Args:
            subscriptions: List of subscriptions
            page: Current page number
            per_page: Items per page
            filter_status: Filter by status (all, active, expiring_soon, expired)
            
        Returns:
            InlineKeyboardMarkup with subscription buttons
        """
        # Filter subscriptions
        if filter_status != "all":
            subscriptions = [s for s in subscriptions if s.status == filter_status]
        
        # Paginate
        total_pages = max(1, (len(subscriptions) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_subs = subscriptions[start_idx:end_idx]
        
        keyboard = []
        
        # Subscription buttons
        for sub in page_subs:
            status_emoji = {"active": "✅", "expiring_soon": "⚠️", "expired": "❌"}.get(sub.status, "📦")
            keyboard.append([
                InlineKeyboardButton(
                    f"{status_emoji} {sub.name[:20]}",
                    callback_data=f"sub_detail:{sub.id}"
                )
            ])
        
        # Pagination buttons
        nav_buttons = []
        if page > 0:
            nav_buttons.append(InlineKeyboardButton("◀️ Prev", callback_data=f"sub_page:{page-1}:{filter_status}"))
        nav_buttons.append(InlineKeyboardButton(f"{page+1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_buttons.append(InlineKeyboardButton("Next ▶️", callback_data=f"sub_page:{page+1}:{filter_status}"))
        
        if nav_buttons:
            keyboard.append(nav_buttons)
        
        # Action buttons
        keyboard.append([
            InlineKeyboardButton("➕ Tambah", callback_data="sub_add"),
            InlineKeyboardButton("🔍 Filter", callback_data="sub_filter"),
        ])
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="show_subs"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def subscription_detail(sub_id: int, sub_name: str = "") -> InlineKeyboardMarkup:
        """Detail view with Renew, Delete, Edit buttons.
        
        Args:
            sub_id: Subscription ID
            sub_name: Subscription name (for display)
            
        Returns:
            InlineKeyboardMarkup with action buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("🔄 Perpanjang", callback_data=f"sub_renew:{sub_id}"),
                InlineKeyboardButton("✏️ Edit", callback_data=f"sub_edit:{sub_id}"),
            ],
            [
                InlineKeyboardButton("🗑️ Hapus", callback_data=f"sub_delete_confirm:{sub_id}"),
            ],
            [
                InlineKeyboardButton("🔙 Kembali", callback_data="sub_list"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def delete_confirmation(sub_id: int, sub_name: str = "") -> InlineKeyboardMarkup:
        """Confirmation dialog for deletion.
        
        Args:
            sub_id: Subscription ID
            sub_name: Subscription name (for display)
            
        Returns:
            InlineKeyboardMarkup with confirmation buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("✅ Ya, Hapus", callback_data=f"sub_delete_yes:{sub_id}"),
                InlineKeyboardButton("❌ Batal", callback_data=f"sub_detail:{sub_id}"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def renew_options(sub_id: int) -> InlineKeyboardMarkup:
        """Renewal period options (1m, 3m, 6m, 1y).
        
        Args:
            sub_id: Subscription ID
            
        Returns:
            InlineKeyboardMarkup with renewal period buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("1 Bulan", callback_data=f"sub_renew_do:{sub_id}:1"),
                InlineKeyboardButton("3 Bulan", callback_data=f"sub_renew_do:{sub_id}:3"),
            ],
            [
                InlineKeyboardButton("6 Bulan", callback_data=f"sub_renew_do:{sub_id}:6"),
                InlineKeyboardButton("1 Tahun", callback_data=f"sub_renew_do:{sub_id}:12"),
            ],
            [
                InlineKeyboardButton("🔙 Kembali", callback_data=f"sub_detail:{sub_id}"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def filter_options(current_filter: str = "all") -> InlineKeyboardMarkup:
        """Filter buttons for status filtering.
        
        Args:
            current_filter: Currently active filter
            
        Returns:
            InlineKeyboardMarkup with filter buttons
        """
        filters = [
            ("all", "📊 Semua"),
            ("active", "✅ Aktif"),
            ("expiring_soon", "⚠️ Segera Berakhir"),
            ("expired", "❌ Kadaluarsa"),
        ]
        
        keyboard = []
        for filter_key, filter_label in filters:
            emoji = "🔘" if filter_key == current_filter else "⚪"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {filter_label}",
                    callback_data=f"sub_filter_set:{filter_key}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="sub_list"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def sort_options(current_sort: str = "end_date") -> InlineKeyboardMarkup:
        """Sort options for subscription list.
        
        Args:
            current_sort: Currently active sort
            
        Returns:
            InlineKeyboardMarkup with sort buttons
        """
        sorts = [
            ("name", "🔤 Nama"),
            ("amount", "💰 Jumlah"),
            ("end_date", "📅 Tanggal Berakhir"),
            ("days_remaining", "⏱️ Sisa Hari"),
        ]
        
        keyboard = []
        for sort_key, sort_label in sorts:
            emoji = "🔘" if sort_key == current_sort else "⚪"
            keyboard.append([
                InlineKeyboardButton(
                    f"{emoji} {sort_label}",
                    callback_data=f"sub_sort_set:{sort_key}"
                )
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="sub_list"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def category_selection() -> InlineKeyboardMarkup:
        """Category selection for adding subscription.
        
        Returns:
            InlineKeyboardMarkup with category buttons
        """
        categories = [
            ("streaming", "🎬 Streaming"),
            ("hosting", "🖥️ Hosting/VPS"),
            ("domain", "🌐 Domain"),
            ("software", "💿 Software"),
            ("other", "📦 Lainnya"),
        ]
        
        keyboard = []
        for cat_key, cat_label in categories:
            keyboard.append([
                InlineKeyboardButton(cat_label, callback_data=f"sub_add_cat:{cat_key}")
            ])
        
        keyboard.append([
            InlineKeyboardButton("🔙 Kembali", callback_data="show_subs"),
        ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def export_options() -> InlineKeyboardMarkup:
        """Export format options.
        
        Returns:
            InlineKeyboardMarkup with export format buttons
        """
        keyboard = [
            [
                InlineKeyboardButton("📄 HTML (Interaktif)", callback_data="sub_export_html"),
            ],
            [
                InlineKeyboardButton("📊 HTML (Statistik)", callback_data="sub_export_stats"),
            ],
            [
                InlineKeyboardButton("🔙 Kembali", callback_data="show_subs"),
            ],
        ]
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def back_to_list() -> InlineKeyboardMarkup:
        """Simple back button to subscription list.
        
        Returns:
            InlineKeyboardMarkup with back button
        """
        keyboard = [
            [InlineKeyboardButton("🔙 Kembali ke Daftar", callback_data="sub_list")],
        ]
        return InlineKeyboardMarkup(keyboard)
