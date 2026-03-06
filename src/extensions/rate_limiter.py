import time
import logging
from .base_extension import CrewExtension

class RateLimiter(CrewExtension):
    """
    Prevents the crew from exceeding free tier API rate limits using a rolling time window.
    """
    def __init__(self, requests_per_minute: int = 2):
        self.rpm_limit = requests_per_minute
        self.call_timestamps = []
        self.logger = logging.getLogger('Rate Limiter')

    def on_step(self, thread_id: str, *, state_update: dict, full_state: dict):
        current_time = time.time()
        self.call_timestamps = [t for t in self.call_timestamps if current_time - t < 60.0]
        if len(self.call_timestamps) >= self.rpm_limit:
            oldest_time = self.call_timestamps[0]
            sleep_time = 60.0 - (current_time - oldest_time)
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached (%i RPM). Pausing for %i seconds...", self.rpm_limit, sleep_time)
                time.sleep(sleep_time)
            new_time = time.time()
            self.call_timestamps = [t for t in self.call_timestamps if new_time - t < 60.0]
        self.call_timestamps.append(time.time())
