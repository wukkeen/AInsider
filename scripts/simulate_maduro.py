from src.analysis.scoring import RiskScorer
import json

def simulate():
    scorer = RiskScorer()
    
    print("🧪 Simulating Maduro Capture Insider Trade Detection...\n")
    
    # scenario 1: The Insider Whale
    # "Yes shares at around 11 cents... earning over $630,000" implies a bet size ~ $70k-$100k
    maduro_trade = {
        "id": "0xMaduroWhale",
        "market": "Maduro in U.S. custody?",
        "size_usd": 75000.00,
        "price": 0.11,
        "side": "buy",
        "user": "0xInsiderWallet123"
    }
    
    # Scenario 2: Regular user
    regular_trade = {
        "id": "0xRegularJoe",
        "market": "Maduro in U.S. custody?",
        "size_usd": 50.00,
        "price": 0.11,
        "side": "buy",
        "user": "0xJoe"
    }
    
    print("--- Scenario 1: Insider Whale Trade ---")
    print(json.dumps(maduro_trade, indent=2))
    score = scorer.calculate_risk(maduro_trade, {})
    print(f"Risk Score: {score}/100")
    print(f"Alert Level: {'HIGH 🚨' if score >= 80 else 'MEDIUM ⚠️' if score >= 50 else 'LOW'}")
    
    print("\n--- Scenario 2: Regular Trade ---")
    print(json.dumps(regular_trade, indent=2))
    score = scorer.calculate_risk(regular_trade, {})
    print(f"Risk Score: {score}/100")
    print(f"Alert Level: {'HIGH 🚨' if score >= 80 else 'MEDIUM ⚠️' if score >= 50 else 'LOW'}")

if __name__ == "__main__":
    simulate()
