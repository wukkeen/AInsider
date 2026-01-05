import asyncio
import httpx
import json

async def explore_api():
    async with httpx.AsyncClient() as client:
        print("Checking CLOB /markets...")
        try:
            resp = await client.get("https://clob.polymarket.com/markets")
            if resp.status_code == 200:
                data = resp.json()
                print(f"CLOB /markets success. Count: {len(data['data']) if 'data' in data else '?'}")
                if 'data' in data and len(data['data']) > 0:
                     print("Sample CLOB market keys:", data['data'][0].keys())
            else:
                print(f"CLOB /markets failed: {resp.status_code}")
        except Exception as e:
            print(f"CLOB error: {e}")

        print("\nChecking Gamma /events...")
        try:
            resp = await client.get("https://gamma-api.polymarket.com/events?limit=5")
            if resp.status_code == 200:
                data = resp.json()
                print(f"Gamma /events success. Count: {len(data)}")
                if len(data) > 0:
                    print("Sample Gamma event keys:", data[0].keys())
            else:
                 print(f"Gamma /events failed: {resp.status_code}")
        except Exception as e:
            print(f"Gamma error: {e}")

if __name__ == "__main__":
    asyncio.run(explore_api())
