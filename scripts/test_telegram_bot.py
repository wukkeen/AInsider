# scripts/test_telegram_bot.py
import asyncio
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from datetime import datetime

from src.monitoring.telegram_bot import create_telegram_bot, TelegramAlert

async def test_bot():
    """Send test alerts to verify Telegram bot works"""
    
    load_dotenv()
    try:
        bot = create_telegram_bot()
    except ValueError as e:
        print(f"Error: {e}")
        return
    
    # Start bot in background
    bot_task = asyncio.create_task(bot.start())
    await asyncio.sleep(2)  # Let bot initialize
    
    # Test 1: Send status notification
    print("Test 1: Status notification...")
    await bot.send_status_notification("✅ Bot test started!")
    await asyncio.sleep(2)
    
    # Test 2: Queue a high-risk alert
    print("Test 2: High-risk alert...")
    high_risk_alert = TelegramAlert(
        alert_id="test_001",
        timestamp=datetime.now(),
        risk_level="HIGH",
        risk_score=87,
        market_name="Fed Rate Decision March 2026",
        wallet_address="0x7a3f2b1c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f90",
        trade_size_usd=78500,
        message="⏰ TIMING | 🐋 WHALE | 🎯 ACCURACY",
        details_json={"test": True}
    )
    
    await bot.queue_alert(high_risk_alert)
    await asyncio.sleep(3)  # Wait for processing
    
    # Test 3: Check stats
    print("Test 3: Stats...")
    await bot.send_status_notification(
        f"📊 Stats: {bot.stats['messages_sent']} messages sent, "
        f"{bot.stats['alerts_received']} alerts received"
    )
    
    # Stop bot
    bot.monitoring_active = False
    await bot.stop()
    print("Test complete!")


if __name__ == "__main__":
    asyncio.run(test_bot())
