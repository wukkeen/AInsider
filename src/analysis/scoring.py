class RiskScorer:
    def __init__(self):
        pass

    def calculate_risk(self, trade: dict, market: dict) -> int:
        """
        Calculate risk score (0-100)
        
        Maduro Capture Case Study:
        - Insider bought ~$50k+ positions when odds were <15%.
        - High volume relative to typical liquidity.
        """
        score = 10
        
        size = float(trade.get('size_usd', 0) or 0)
        
        # 1. Size Impact
        if size > 50000:
            score += 70  # Massive whale -> Immediate HIGH risk
        elif size > 10000:
            score += 40  # Significant size
        elif size > 1000:
            score += 10
            
        # 2. Market Context (Stub)
        # In a real version, we'd check if (price < 0.15 and side == 'buy')
        
        return min(score, 100)
