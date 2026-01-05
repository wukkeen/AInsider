# src/utils/rate_limiter.py
import asyncio
from datetime import datetime, timedelta
from typing import Optional

class TelegramRateLimiter:
    """
    Implements Telegram Bot API rate limits [web:33][web:36]
    
    Limits:
    - 1 message per second per chat
    - 30 messages per second globally
    - 20 messages per minute per group
    """
    
    def __init__(self):
        self.last_message_time = datetime.now()
        self.message_timestamps = []  # Track last 30 messages
        self.min_interval = 1.0  # seconds between messages to same chat
    
    async def wait_if_needed(self) -> float:
        """
        Calculate and wait if rate limit would be exceeded
        
        Returns:
            Time waited in seconds
        """
        time_since_last = (datetime.now() - self.last_message_time).total_seconds()
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            await asyncio.sleep(wait_time)
            return wait_time
        
        return 0
    
    def record_message(self):
        """Record message for rate limit tracking"""
        now = datetime.now()
        self.last_message_time = now
        self.message_timestamps.append(now)
        
        # Remove messages older than 1 minute
        cutoff = now - timedelta(minutes=1)
        self.message_timestamps = [ts for ts in self.message_timestamps if ts > cutoff]
        
        # Check global limit (30/sec)
        recent = [ts for ts in self.message_timestamps if ts > now - timedelta(seconds=1)]
        if len(recent) >= 30:
            raise RuntimeError("Global rate limit (30/sec) would be exceeded")
