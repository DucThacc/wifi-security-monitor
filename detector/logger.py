import json
import requests

from .utils import ensure_dir, utc_ts


class EventLogger:
    def __init__(self, log_path, opensearch_cfg=None, telegram_cfg=None):
        self.log_path = log_path
        self.opensearch_cfg = opensearch_cfg or {}
        self.telegram_cfg = telegram_cfg or {}
        ensure_dir(self.log_path)

    def log_event(self, event):
        event.setdefault("timestamp", utc_ts())
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")

        msg = event.get("message") or event.get("event_type")
        print(f"[ALERT] {msg}")

        if self.opensearch_cfg.get("enabled"):
            self._send_opensearch(event)
        if self.telegram_cfg.get("enabled"):
            self._send_telegram(event)

    def _send_opensearch(self, event):
        endpoint = self.opensearch_cfg.get("endpoint", "").rstrip("/")
        index = self.opensearch_cfg.get("index", "wifi-security-logs")
        url = f"{endpoint}/{index}/_doc"
        try:
            requests.post(url, json=event, timeout=3, verify=self.opensearch_cfg.get("verify_tls", False))
        except Exception:
            pass

    def _send_telegram(self, event):
        token = self.telegram_cfg.get("bot_token", "").strip()
        chat_id = self.telegram_cfg.get("chat_id", "").strip()
        if not token or not chat_id:
            return
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        text = event.get("message", event.get("event_type", "alert"))
        try:
            requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=3)
        except Exception:
            pass
