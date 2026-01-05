"""
Telegram Bot for real-time Polymarket alert delivery
Handles async polling, rate limiting, and command processing
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from dataclasses import dataclass
import os
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
)
from telegram.constants import ChatAction, ParseMode
from telegram.error import TelegramError, BadRequest

load_dotenv()

logger = logging.getLogger(__name__)

@dataclass
class TelegramAlert:
    """Data class for alert queuing"""
    alert_id: str
    timestamp: datetime
    risk_level: str  # "HIGH", "MEDIUM", "LOW"
    risk_score: int  # 0-100
    market_name: str
    wallet_address: str
    trade_size_usd: float
    message: str
    details_json: Dict


class TelegramBotManager:
    """
    Manages Telegram bot operations with async polling,
    rate limiting, and alert queue management
    
    Rate Limits [web:33][web:36]:
    - 1 message per second to same chat
    - 30 messages per second globally
    - 20 messages per minute to groups
    """
    
    def __init__(self, token: str, chat_id: int):
        """
        Initialize Telegram bot
        
        Args:
            token: Bot token from @BotFather
            chat_id: Your personal chat ID
        """
        self.token = token
        self.chat_id = chat_id
        
        # Rate limiting
        self.last_message_time = datetime.now()
        self.min_interval = 1.0  # 1 second between messages to same chat
        self.message_queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        self.queue_processor_task = None
        
        # State tracking
        self.is_paused = False
        self.monitoring_active = True
        self.shutdown_requested = False
        self.last_trade = None  # For /test command
        self.stats = {
            "messages_sent": 0,
            "alerts_received": 0,
            "high_risk_alerts": 0,
            "start_time": datetime.now(),
        }
        
        # Build application
        self.app = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Register command and callback handlers [web:32]"""
        # Commands
        self.app.add_handler(CommandHandler("start", self._cmd_start))
        self.app.add_handler(CommandHandler("status", self._cmd_status))
        self.app.add_handler(CommandHandler("stop", self._cmd_stop))
        self.app.add_handler(CommandHandler("shutdown", self._cmd_shutdown))
        self.app.add_handler(CommandHandler("test", self._cmd_test))
        self.app.add_handler(CommandHandler("stats", self._cmd_stats))
        
        # Callback buttons
        self.app.add_handler(CallbackQueryHandler(self._callback_button))
    
    # ========== Command Handlers ==========
    
    async def _cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /start command"""
        welcome_message = (
            "🚨 <b>AInsider Trading Monitor</b>\n\n"
            "I monitor Polymarket for suspicious trading patterns and send you "
            "real-time alerts when anomalies are detected.\n\n"
            "<b>Available Commands:</b>\n"
            "/test - Show latest checked trade\n"
            "/status - Current monitoring status\n"
            "/stop - Pause alert delivery\n"
            "/start - Resume alert delivery\n"
            "/stats - Show monitoring statistics\n"
            "/shutdown - Stop the bot completely\n\n"
            "🔔 <i>You will receive alerts automatically. "
            "🔔 <i>You will receive alerts automatically. "
            "I respect Telegram rate limits (1 msg/sec)</i>"
        )
        
        await update.message.reply_html(welcome_message)
        logger.info(f"Bot started with user {update.effective_user.id}")
    
    async def _cmd_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show current monitoring status"""
        status_emoji = "🟢" if self.monitoring_active else "🔴"
        pause_emoji = "⏸️" if self.is_paused else "▶️"
        queue_size = self.message_queue.qsize()
        
        status_message = (
            f"{status_emoji} <b>Monitoring Status</b>\n\n"
            f"Monitoring: {'Active' if self.monitoring_active else 'Inactive'}\n"
            f"Alerts: {'Paused' if self.is_paused else 'Delivering'}\n"
            f"Queue Size: {queue_size}/100\n"
            f"Messages Sent: {self.stats['messages_sent']}\n"
            f"Uptime: {self._format_uptime()}\n"
        )
        
        await update.message.reply_html(status_message)
    
    async def _cmd_stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Pause alert delivery"""
        self.is_paused = True
        await update.message.reply_text("⏸️ Alert delivery paused. Monitoring continues in background.")
        logger.info("Alert delivery paused by user")
    
    async def _cmd_shutdown(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Shutdown the application"""
        self.shutdown_requested = True
        self.monitoring_active = False # Stop queue processor
        await update.message.reply_text("🛑 Shutting down monitor...")
        logger.info("Shutdown requested by user")
        # The main loop in main.py should check bot.shutdown_requested
    
    async def _cmd_test(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show the latest checked trade"""
        if not self.last_trade:
             await update.message.reply_text("⚠️ No trades checked yet.")
             return

        trade = self.last_trade
        # Format the last trade
        msg = (
            f"🧪 <b>Latest Scanned Trade</b>\n"
            f"Market: {trade.get('market_name', 'Unknown')}\n"
            f"Size: ${trade.get('size_usd', 0):,.2f}\n"
            f"Source: {trade.get('source', 'Unknown')}\n"
            f"ID: <code>{trade.get('id', 'Unknown')[:8]}...</code>"
        )
        await update.message.reply_html(msg)

    async def _cmd_resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Resume alert delivery (alias for start logic if paused)"""
        self.is_paused = False
        await update.message.reply_text("▶️ Alert delivery resumed.")

    def update_last_trade(self, trade_info: Dict):
        """Update the last checked trade for /test command"""
        self.last_trade = trade_info
    
    async def _cmd_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show monitoring statistics"""
        uptime_seconds = (datetime.now() - self.stats['start_time']).total_seconds()
        alerts_per_hour = (self.stats['alerts_received'] / (uptime_seconds / 3600)) if uptime_seconds > 0 else 0
        
        stats_message = (
            "<b>📊 Monitoring Statistics</b>\n\n"
            f"Uptime: {self._format_uptime()}\n"
            f"Total Alerts: {self.stats['alerts_received']}\n"
            f"High-Risk Alerts: {self.stats['high_risk_alerts']}\n"
            f"Messages Sent: {self.stats['messages_sent']}\n"
            f"Alerts/Hour: {alerts_per_hour:.2f}\n"
            f"Queue Size: {self.message_queue.qsize()}/100\n"
        )
        
        await update.message.reply_html(stats_message)
    
    async def _cmd_top_alerts(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Show top 3 recent high-risk alerts (placeholder)"""
        top_message = (
            "<b>🔴 Top Recent High-Risk Alerts</b>\n\n"
            "1️⃣ <b>Fed Rate Decision March 2026</b>\n"
            "   Risk Score: 87/100\n"
            "   Trade Size: $78,500\n"
            "   Time: 27h before resolution\n\n"
            "2️⃣ <b>Trump Indictment Georgia</b>\n"
            "   Risk Score: 82/100\n"
            "   Pattern: Coordinated 3-wallet network\n\n"
            "3️⃣ <b>2024 Presidential Election</b>\n"
            "   Risk Score: 79/100\n"
            "   Whale: Historical accuracy anomaly\n"
        )
        
        await update.message.reply_html(top_message)
    
    async def _callback_button(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle inline button callbacks"""
        query = update.callback_query
        await query.answer()
        
        if query.data == "view_details":
            await query.edit_message_text(
                text="<b>📋 Alert Details</b>\n\n"
                "Wallet: 0x7a3f2b1c...\n"
                "Market: Fed Rate Decision\n"
                "Position: YES @ 0.23\n"
                "Profit: $72,415 (292% ROI)\n"
                "Timing: 27.25h before resolution",
                parse_mode=ParseMode.HTML
            )
        elif query.data == "check_wallet":
            await query.edit_message_text(
                text="🔗 <b>Wallet Analysis</b>\n\n"
                "View on PolygonScan:\n"
                "https://polygonscan.com/address/0x7a3f2b1c...",
                parse_mode=ParseMode.HTML
            )
    
    # ========== Core Bot Operations ==========
    
    async def queue_alert(self, alert: TelegramAlert) -> bool:
        """
        Add alert to queue for delivery [web:32]
        
        Non-blocking: returns immediately
        Respects queue size limit
        """
        try:
            self.message_queue.put_nowait(alert)
            self.stats['alerts_received'] += 1
            
            if alert.risk_level == "HIGH":
                self.stats['high_risk_alerts'] += 1
            
            logger.debug(f"Alert queued: {alert.alert_id} (Queue size: {self.message_queue.qsize()})")
            return True
            
        except asyncio.QueueFull:
            logger.warning(f"Alert queue full, dropping alert: {alert.alert_id}")
            return False
    
    async def _process_alert_queue(self):
        """
        Background task that processes alert queue with rate limiting [web:33]
        
        Respects 1 message per second per chat limit
        """
        logger.info("Alert queue processor started")
        
        while self.monitoring_active:
            try:
                if self.is_paused:
                    await asyncio.sleep(1)
                    continue
                
                # Wait for alert (with timeout to check monitoring_active)
                try:
                    alert = await asyncio.wait_for(
                        self.message_queue.get(),
                        timeout=5.0
                    )
                except asyncio.TimeoutError:
                    continue
                
                # Rate limiting: ensure 1+ second between messages [web:33][web:36]
                time_since_last = (datetime.now() - self.last_message_time).total_seconds()
                if time_since_last < self.min_interval:
                    sleep_time = self.min_interval - time_since_last
                    await asyncio.sleep(sleep_time)
                
                # Send formatted alert
                await self._send_alert_message(alert)
                
                self.last_message_time = datetime.now()
                self.stats['messages_sent'] += 1
                
                self.message_queue.task_done()
                
            except Exception as e:
                logger.error(f"Error processing alert queue: {e}", exc_info=True)
                await asyncio.sleep(2)
    
    async def _send_alert_message(self, alert: TelegramAlert) -> bool:
        """
        Send formatted alert message to Telegram
        
        Uses HTML parsing for rich formatting
        Includes inline action buttons
        """
        try:
            # Color-coded emoji by risk level
            risk_emoji = "🔴" if alert.risk_level == "HIGH" else "🟡" if alert.risk_level == "MEDIUM" else "🟢"
            
            # Format message
            message_html = (
                f"{risk_emoji} <b>{alert.market_name}</b>\n"
                f"Risk Score: {alert.risk_score}/100\n"
                f"Risk Level: {alert.risk_level}\n\n"
                
                f"<b>Trade Details</b>\n"
                f"Size: ${alert.trade_size_usd:,.0f}\n"
                f"Wallet: <code>{alert.wallet_address[:16]}...</code>\n"
                f"Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC\n\n"
                
                f"<b>Flags</b>\n"
                f"{alert.message}\n"
            )
            
            # Create inline keyboard with action buttons
            keyboard = InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("📋 Details", callback_data="view_details"),
                    InlineKeyboardButton("🔗 Wallet", callback_data="check_wallet"),
                ]
            ])
            
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=message_html,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=True
            )
            
            logger.info(f"Alert sent: {alert.alert_id}")
            return True
            
        except BadRequest as e:
            logger.error(f"Bad request sending alert: {e}")
            return False
        except TelegramError as e:
            logger.error(f"Telegram API error: {e}")
            return False
    
    async def send_status_notification(self, message: str):
        """Send status notification (non-alert message)"""
        try:
            await self.app.bot.send_message(
                chat_id=self.chat_id,
                text=f"ℹ️ {message}",
                parse_mode=ParseMode.HTML
            )
        except TelegramError as e:
            logger.error(f"Failed to send status notification: {e}")
    
    # ========== Bot Lifecycle ==========
    
    async def start(self):
        """
        Start bot with async polling (non-blocking) [web:32]
        
        Uses manual initialization to avoid conflicts with existing asyncio loops.
        """
        logger.info("Starting Telegram bot...")
        
        # Start alert queue processor
        self.queue_processor_task = asyncio.create_task(self._process_alert_queue())
        
        # Initialize and start application
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=True
        )
        logger.info("Telegram bot polling started")
    
    async def stop(self):
        """Stop bot and cleanup"""
        logger.info("Stopping Telegram bot...")
        self.monitoring_active = False
        
        if self.queue_processor_task:
            self.queue_processor_task.cancel()
            try:
                await self.queue_processor_task
            except asyncio.CancelledError:
                pass
        
        # Stop polling and application
        if self.app.updater.running:
            await self.app.updater.stop()
        if self.app.running:
            await self.app.stop()
        await self.app.shutdown()
        
        logger.info("Telegram bot stopped")
    
    # ========== Utility Methods ==========
    
    def _format_uptime(self) -> str:
        """Format uptime in human-readable format"""
        uptime = datetime.now() - self.stats['start_time']
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        return f"{hours}h {minutes}m {seconds}s"


# ========== Factory Function ==========

def create_telegram_bot(token: str = None, chat_id: int = None) -> TelegramBotManager:
    """
    Create and configure Telegram bot manager
    
    Args:
        token: Bot token (defaults to TELEGRAM_BOT_TOKEN env var)
        chat_id: Chat ID (defaults to TELEGRAM_CHAT_ID env var)
    
    Returns:
        Configured TelegramBotManager instance
    """
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or int(os.getenv("TELEGRAM_CHAT_ID", "0"))
    
    if not token or not chat_id:
        raise ValueError("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
    
    return TelegramBotManager(token, chat_id)
