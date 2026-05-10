from collections import deque


class DeauthDetector:
    def __init__(self, window_seconds=10, threshold=20):
        self.window_seconds = window_seconds
        self.threshold = threshold
        self.timestamps = deque()
        self.last_alert_ts = None

    def handle_deauth(self, now_epoch, source_mac, dest_mac, ap_bssid):
        events = []
        self.timestamps.append(now_epoch)
        self._expire(now_epoch)

        count = len(self.timestamps)
        if count >= self.threshold:
            events.append(
                {
                    "event_type": "deauth_attack_detected",
                    "source_mac": source_mac,
                    "destination_mac": dest_mac,
                    "ap_bssid": ap_bssid,
                    "count": count,
                    "window_seconds": self.window_seconds,
                    "severity": "high",
                    "message": "Deauth frame burst exceeds threshold",
                }
            )
            self.timestamps.clear()

        return events

    def _expire(self, now_epoch):
        while self.timestamps and (now_epoch - self.timestamps[0]) > self.window_seconds:
            self.timestamps.popleft()
