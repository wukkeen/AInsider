"""
Main orchestrator for AInsider
Monitors multiple prediction markets (Polymarket, Kalshi) for suspicious patterns
"""

import asyncio
import logging
import os
from datetime import datetime
from dotenv import load_dotenv

from src.api.clob_client import CLOBClient
from src.api.kalshi_client import KalshiClient
from src.analysis.scoring import RiskScorer
from src.monitoring.telegram_bot import create_telegram_bot, TelegramAlert
from src.data.storage import Database

load_dotenv()

logger = logging.getLogger(__name__)


class MarketMonitor:
    """
    Generic monitor that orchestrates multiple market clients
    """
    
    def __init__(self, telegram_bot_manager):
        """Initialize monitor with Telegram bot"""
        self.bot = telegram_bot_manager
        self.poly_client = CLOBClient()
        self.kalshi_client = KalshiClient()
        self.scorer = RiskScorer()
        self.db = Database()
        self.running = False
        self.poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "60"))
        # Rate Limit Safety:
        # Polymarket: ~50-100 req/10s. We do ~20 sequential in a burst every 60s. Safe.
        # Kalshi: ~1000 req/hour (conservative). 1 call every 60s = 60/hour. Very safe.
        self.kalshi_poll_interval = max(self.poll_interval, 60) # Ensure at least 60s for Kalshi
    
    async def monitor_polymarket(self):
        """Monitor Polymarket activity"""
        logger.info(f"Starting Polymarket monitoring...")
        while self.running:
            try:
                markets = await self.poly_client.get_active_markets(limit=20)
                for market in markets:
                    # Polymarket market IDs are usually condition_id for Data API
                    # The market dict from CLOB has 'condition_id'
                    condition_id = market.get('condition_id')
                    if condition_id:
                        await self._analyze_market(
                            source="Polymarket",
                            market_id=condition_id,
                            market_name=market.get('question', 'Unknown'),
                            client=self.poly_client
                        )
                await asyncio.sleep(self.poll_interval)
            except Exception as e:
                logger.error(f"Polymarket loop error: {e}")
                await asyncio.sleep(self.poll_interval)

    async def monitor_kalshi(self):
        """Monitor Kalshi activity"""
        logger.info(f"Starting Kalshi monitoring...")
        while self.running:
            try:
                markets = await self.kalshi_client.get_active_markets(limit=20)
                for market in markets:
                    # Kalshi uses 'ticker'
                    ticker = market.get('ticker')
                    if ticker:
                        await self._analyze_market(
                            source="Kalshi",
                            market_id=ticker,
                            market_name=market.get('title', 'Unknown'),
                            client=self.kalshi_client
                        )
                await asyncio.sleep(self.kalshi_poll_interval)
            except Exception as e:
                logger.error(f"Kalshi loop error: {e}")
                await asyncio.sleep(self.kalshi_poll_interval)

    async def _analyze_market(self, source, market_id, market_name, client):
        """Generic analysis for any market source"""
        try:
            trades = await client.get_market_trades(market_id, limit=5)
            for trade in trades:
                # Normalize trade data (very basic normalization)
                trade_data = self._normalize_trade(source, trade)
                
                # Mock risk Scoring (since we rely on the stub)
                # In real code, we'd pass normalized data to scorer
                risk_score = self.scorer.calculate_risk(trade_data, {})
                
                if risk_score >= 70:
                    # Construct Trading URL
                    if source == "Polymarket":
                        # Polymarket uses 'slug' from the market/event object. 
                        # We only have market_name (question) here. 
                        # To get a real link, we need the event slug. 
                        # For now, we'll try to find a slug if available or link to the main page.
                        # Ideally, we should pass more metadata to _analyze_market.
                        url = f"https://polymarket.com/market/{market_name.replace(' ', '-').lower()}" # Fallback
                        if 'slug' in trade_data.get('raw', {}):
                             url = f"https://polymarket.com/event/{trade_data['raw']['slug']}"
                        elif 'market_slug' in trade_data.get('raw', {}):
                             url = f"https://polymarket.com/market/{trade_data['raw']['market_slug']}"
                    
                    elif source == "Kalshi":
                        # Kalshi typically uses /markets/{ticker}
                        url = f"https://kalshi.com/markets/{market_id}"

                    alert = TelegramAlert(
                        alert_id=f"{source}_{market_id}_{trade_data['id']}",
                        timestamp=datetime.now(),
                        risk_level="HIGH" if risk_score >= 85 else "MEDIUM",
                        risk_score=risk_score,
                        market_name=market_name,
                        wallet_address=trade_data['user'],
                        trade_size_usd=trade_data['size_usd'],
                        message=f"[{source}] Suspicious activity\n🔗 <a href='{url}'>Trade on {source}</a>",
                        details_json=trade_data
                    )
                    await self.bot.queue_alert(alert)
        except Exception as e:
            logger.error(f"Error analyzing {source} market {market_id}: {e}")

    def _normalize_trade(self, source, trade):
        """Normalize trade objects from different APIs"""
        if source == "Polymarket":
            return {
                "id": trade.get("transactionHash", "unknown"),
                "user": trade.get("proxyWallet", "unknown"),
                "size_usd": float(trade.get("size", 0)) * float(trade.get("price", 0)),
                "raw": trade
            }
        elif source == "Kalshi":
            # Kalshi trade structure might differ
            return {
                "id": trade.get("trade_id", "unknown"),
                "user": "KalshiUser", # Kalshi is often anonymous/hashed
                "size_usd": float(trade.get("count", 0)) * float(trade.get("price", 0)), # approximate
                "raw": trade
            }
        return {}

    async def start(self):
        self.running = True
        await self.bot.start()
        await self.bot.send_status_notification("✅ AInsider Started (Polymarket + Kalshi)")
        
        # Run both monitors
        await asyncio.gather(
            self.monitor_polymarket(),
            self.monitor_kalshi()
        )

    async def stop(self):
        self.running = False
        await self.poly_client.close()
        await self.kalshi_client.close()
        await self.bot.stop()

async def main():
    logging.basicConfig(level=logging.INFO)
    try:
        bot = create_telegram_bot()
        monitor = MarketMonitor(bot)
        await monitor.start()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    asyncio.run(main())
