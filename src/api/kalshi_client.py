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
        Fetch recent trades for a specific market ticker.
        """
        try:
            # https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/trades
            params = {"limit": limit}
            resp = await self.client.get(f"{self.BASE_URL}/markets/{ticker}/trades", params=params)
            resp.raise_for_status()
            data = resp.json()
            # Returns {'trades': [...]}
            return data.get('trades', [])
        except Exception as e:
            logger.error(f"Error fetching Kalshi trades for {ticker}: {e}")
            return []
            
    async def close(self):
        await self.client.aclose()
