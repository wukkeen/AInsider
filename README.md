# AInsider

A local Python application for monitoring prediction markets (Polymarket and Kalshi) to identify suspicious trading patterns.

## Features
- **Dual-Engine Monitoring**: Scans both [Polymarket](https://polymarket.com) and [Kalshi](https://kalshi.com) simultaneously.
- **Cost-Free Public APIs**: Uses the public free tiers for both platforms. No API keys required for market data.
- **Telegram Alerts**: Sends instant push notifications with trading links when anomalies are detected.
- **Risk Scoring**: Analyzes trades for anomalous sizing and timing (stub implementation ready for your logic).
- **Privacy-First**: Runs locally on your machine.

## Setup

1. **Environment Setup**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configuration**
   - Edit `.env` file with your credentials:
     - `TELEGRAM_BOT_TOKEN`: Get from @BotFather
     - `TELEGRAM_CHAT_ID`: Run `python scripts/get_chat_id.py` to find this.
     - *Note: Polymarket/Kalshi API keys are NOT required.*

3. **Running the Monitor**
   ```bash
   source .venv/bin/activate
   python -m src.main
   ```

4. **Testing Alerts**
   ```bash
   python scripts/test_telegram_bot.py
   ```

## Rate Limits & Safety
- **Polymarket**: Optimized to ensure < 50 requests/10s burst.
- **Kalshi**: Conservative polling (60s interval) to stay well within free tier limits.
- **Telegram**: Built-in rate limiter ensures < 1 message/second to prevent spam blocks.

## Project Structure
- `src/monitoring`: Telegram bot implementation.
- `src/analysis`: Risk scoring algorithms.
- `src/api`: Public API clients for Polymarket and Kalshi.
- `src/main.py`: Dual-engine orchestrator.
