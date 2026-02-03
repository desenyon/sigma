import asyncio
import time
from typing import Dict, Optional

class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, requests_per_minute: int = 10, min_interval: float = 1.0):
        self.requests_per_minute = requests_per_minute
        self.min_interval = min_interval
        self.last_request_time = 0
        self.request_count = 0
        self.window_start = time.time()
        self._lock = asyncio.Lock()
    
    async def wait(self):
        """Wait if necessary to respect rate limits."""
        async with self._lock:
            current_time = time.time()
            
            # Reset window if a minute has passed
            if current_time - self.window_start >= 60:
                self.window_start = current_time
                self.request_count = 0
            
            # Check if we've hit the rate limit
            if self.request_count >= self.requests_per_minute:
                wait_time = 60 - (current_time - self.window_start)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    self.window_start = time.time()
                    self.request_count = 0
            
            # Ensure minimum interval between requests
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)
            
            self.last_request_time = time.time()
            self.request_count += 1
