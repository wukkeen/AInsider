import httpx
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class CLOBClient:
    """
    Client for Polymarket's Public API (CLOB and Data API).
    No API Key required for these endpoints.
    """
    CLOB_URL = "https://clob.polymarket.com"
    GAMMA_URL = "https://gamma-api.polymarket.com" # For better market details
    DATA_URL = "https://data-api.polymarket.com"

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_active_markets(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch active markets. 
        Using CLOB /markets is okay, but Gamma /events might be better for "active" filtering.
        Let's use CLOB /markets for now as it's the core engine.
        """
        try:
            # next_cursor handling could be added for pagination
            resp = await self.client.get(f"{self.CLOB_URL}/markets")
            resp.raise_for_status()
            data = resp.json()
            
            # The structure is usually {'data': [...], ...}
            markets = data.get('data', [])
            
            # Simple client-side filter and limit since public API minimal params
            active = [m for m in markets if m.get('active') is True][:limit]
            return active
        except Exception as e:
            logger.error(f"Error fetching active markets: {e}")
            return []

    async def get_market_trades(self, market_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Fetch recent trades for a specific market (Condition ID).
        Uses the Data API.
        """
        try:
            # market_id in CLOB usually refers to 'condition_id' or 'token_id'
            # Data API expects 'market' param which is often the condition_id
            url = f"{self.DATA_URL}/trades"
            params = {
                "market": market_id,
                "limit": limit,
            }
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            trades = resp.json()
            return trades
        except Exception as e:
            logger.error(f"Error fetching trades for {market_id}: {e}")
            return []

    async def close(self):
        await self.client.aclose()
