# AInsider

A local Python application for monitoring prediction markets (Polymarket, Kalshi) to identify suspicious trading patterns.

## Features
- **Real-time Monitoring**: Scans Polymarket every 60 seconds.
- **Telegram Alerts**: Sends instant push notifications for suspicious activities.
- **Risk Scoring**: Analyzes trades for timing anomalies, whale movements, and network coordination.
- **Privacy-First**: Runs locally on your machine (Apple Silicon optimized).

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
     - `POLYMARKET_API_KEY`: Your Polymarket API/Clob key.
     - `POLYGON_PRIVATE_KEY`: For on-chain analysis (optional).

3. **Running the Monitor**
   ```bash
   python src/main.py
   ```

4. **Testing**
   ```bash
   python scripts/test_telegram_bot.py
   ```

## Project Structure
- `src/monitoring`: Telegram bot implementation.
- `src/analysis`: Risk scoring algorithms.
- `src/api`: Polymarket CLOB API client.
- `src/data`: Data storage and persistence.
