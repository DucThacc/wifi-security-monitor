from .utils import normalize_ssid, similarity


class RogueAPDetector:
    def __init__(self, whitelist, ssid_similarity_threshold=0.85, alert_cooldown_seconds=30):
        self.whitelist = whitelist
        self.ssid_similarity_threshold = ssid_similarity_threshold
        self.alert_cooldown_seconds = alert_cooldown_seconds
        self._seen_bssid = set()
        self._last_alert = {}

    def _ssid_match(self, ssid):
        ssid_norm = normalize_ssid(ssid)
        for ap in self.whitelist:
            if normalize_ssid(ap.get("ssid")) == ssid_norm:
                yield ap

    def _similar_whitelist(self, ssid):
        ssid_norm = normalize_ssid(ssid)
        for ap in self.whitelist:
            w = normalize_ssid(ap.get("ssid"))
            if similarity(ssid_norm, w) >= self.ssid_similarity_threshold:
                yield ap

    def handle_ap(self, ssid, bssid, channel, rssi, encryption, now_ts, now_epoch):
        events = []
        if not ssid or not bssid:
            return events

        ssid_norm = normalize_ssid(ssid)
        key = f"{ssid_norm}:{bssid}"
        if key in self._seen_bssid:
            return events
        self._seen_bssid.add(key)

        # Rogue/Evil Twin: SSID matches, BSSID not in whitelist
        for ap in self._ssid_match(ssid):
            legit_bssid = ap.get("bssid")
            if legit_bssid and legit_bssid.lower() != bssid.lower():
                events.append(
                    {
                        "timestamp": now_ts,
                        "event_type": "rogue_ap_detected",
                        "ssid": ssid,
                        "legit_bssid": legit_bssid,
                        "detected_bssid": bssid,
                        "channel": channel,
                        "rssi": rssi,
                        "severity": "high",
                        "message": "SSID matches legitimate AP but BSSID is unknown",
                    }
                )
                return events

        # Suspicious open AP with similar SSID
        if encryption == "OPEN":
            for ap in self._similar_whitelist(ssid):
                if self._cooldown_ok(ssid_norm, now_epoch):
                    events.append(
                        {
                            "timestamp": now_ts,
                            "event_type": "suspicious_open_ap",
                            "ssid": ssid,
                            "detected_bssid": bssid,
                            "channel": channel,
                            "rssi": rssi,
                            "severity": "medium",
                            "message": "Open AP has SSID similar to legitimate AP",
                        }
                    )
                break

        return events

    def _cooldown_ok(self, key, now_epoch):
        last = self._last_alert.get(key)
        if last is None or (now_epoch - last) >= self.alert_cooldown_seconds:
            self._last_alert[key] = now_epoch
            return True
        return False
