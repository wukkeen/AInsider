import asyncio
import httpx

async def test_kalshi():
    async with httpx.AsyncClient() as client:
        print("Fetching markets...")
        resp = await client.get("https://api.elections.kalshi.com/trade-api/v2/markets?limit=1")
        if resp.status_code != 200:
            print(f"Markets failed: {resp.status_code}")
            return
            
        data = resp.json()
        if not data.get('markets'):
            print("No markets found")
            return
            
        ticker = data['markets'][0]['ticker']
        print(f"Testing with ticker: {ticker}")
        
        # Test 1: Trades Endpoint
        print(f"\nTesting GET /markets/{ticker}/trades...")
        resp = await client.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/trades")
        print(f"Status: {resp.status_code}")
        
        # Test 2: Orderbook Endpoint
        print(f"\nTesting GET /markets/{ticker}/orderbook...")
        resp = await client.get(f"https://api.elections.kalshi.com/trade-api/v2/markets/{ticker}/orderbook")
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            print(f"Orderbook data keys: {resp.json().keys()}")

if __name__ == "__main__":
    asyncio.run(test_kalshi())
