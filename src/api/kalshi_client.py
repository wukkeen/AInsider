import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class KalshiClient:
    """
    Client for Kalshi's Public API (v2).
    """
    BASE_URL = "https://api.elections.kalshi.com/trade-api/v2"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_active_markets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch active markets from Kalshi.
        """
        try:
            # https://api.elections.kalshi.com/trade-api/v2/markets
            params = {"limit": limit}
            resp = await self.client.get(f"{self.BASE_URL}/markets", params=params)
            resp.raise_for_status()
            data = resp.json()
            # Returns {'markets': [...], 'cursor': ...}
            return data.get('markets', [])
        except Exception as e:
            logger.error(f"Error fetching Kalshi markets: {e}")
            return []

    async def get_market_trades(self, ticker: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent trades or orderbook for a specific market ticker.
        User-specific trades are private, and public trade history seems restricted (404).
        We will fetch the Orderbook to detect activity/pricing.
        """
        try:
            # Fallback to orderbook since /trades is often 404 public
            # https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook
            resp = await self.client.get(f"{self.BASE_URL}/markets/{ticker}/orderbook")
            resp.raise_for_status()
            data = resp.json()
            
            # Construct a "trade-like" object from the top of the book to maintain compatibility
            # { 'orderbook': { 'yes': [[price, qty], ...], 'no': [...] } }
            book = data.get('orderbook', {})
            yes_ask = book.get('yes', [])
            
            # Synthesize a "latest quote" as a trade for monitoring
            if yes_ask and len(yes_ask) > 0:
                best_ask = yes_ask[0] # [price, count]
                return [{
                    "trade_id": "latest_quote",
                    "price": best_ask[0],
                    "count": best_ask[1],
                    "created_time": "now",
                    "is_quote": True
                }]
            return []
        except Exception as e:
            logger.error(f"Error fetching Kalshi orderbook for {ticker}: {e}")
            return []
            
    async def close(self):
        await self.client.aclose()
