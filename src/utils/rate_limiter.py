import time
import logging

class RateLimiter():
    """
    Prevents the crew from exceeding free tier API rate limits using a rolling time window.
    """
    def __init__(self, requests_per_minute: int = 3):
        self.rpm_limit = requests_per_minute
        self.call_timestamps = []
        self.logger = logging.getLogger('Rate Limiter')

    def wait_if_needed(self):
        current_time = time.time()
        self.call_timestamps = [t for t in self.call_timestamps if current_time - t < 60.0]
        if len(self.call_timestamps) >= self.rpm_limit:
            sleep_time = 60.0 - (current_time - self.call_timestamps[0])
            if sleep_time > 0:
                self.logger.warning(f"Rate limit reached (%i RPM). Pausing for %i seconds...", self.rpm_limit, sleep_time)
                time.sleep(sleep_time)
            current_time = time.time()
            self.call_timestamps = [t for t in self.call_timestamps if current_time - t < 60.0]
        self.call_timestamps.append(time.time())
