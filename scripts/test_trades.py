import asyncio
import httpx
import json

async def test_trades():
    # First get a market ID from CLOB
    async with httpx.AsyncClient() as client:
        print("Getting a market ID...")
        resp = await client.get("https://clob.polymarket.com/markets")
        market_id = None
        if resp.status_code == 200:
            data = resp.json()
            if 'data' in data and len(data['data']) > 0:
                # Use the condition_id or something similar? 
                # Docs said 'market' parameter uses conditionId
                mid = data['data'][0].get('condition_id') 
                # Or maybe 'market_slug'?
                # Search results said "market (using conditionId)"
                market_id = mid
                print(f"Using Market ID (condition_id): {market_id}")
        
        if market_id:
            print(f"Querying trades for {market_id}...")
            # https://data-api.polymarket.com/trades?market=...
            try:
                resp = await client.get(f"https://data-api.polymarket.com/trades?market={market_id}&limit=5")
                if resp.status_code == 200:
                    trades = resp.json()
                    print(f"Trades success. Count: {len(trades)}")
                    if len(trades) > 0:
                        print("Sample trade:", trades[0])
                else:
                    print(f"Trades failed: {resp.status_code} {resp.text}")
            except Exception as e:
                print(f"Trades error: {e}")

if __name__ == "__main__":
    asyncio.run(test_trades())
