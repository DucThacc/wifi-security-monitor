import threading
import time

from scapy.all import Dot11Beacon, Dot11Deauth, sniff

from .deauth_detector import DeauthDetector
from .logger import EventLogger
from .rogue_ap_detector import RogueAPDetector
from .utils import get_channel, get_encryption, get_rssi, get_ssid, load_json, load_yaml, utc_ts


def scan_targets(iface, scan_seconds=8, max_results=20):
    results = {}

    def handler(pkt):
        if not pkt.haslayer(Dot11Beacon):
            return
        ssid = get_ssid(pkt) or "<hidden>"
        bssid = pkt.addr2 or pkt.addr3
        channel = get_channel(pkt)
        enc = get_encryption(pkt)
        rssi = get_rssi(pkt)
        key = (ssid, bssid, channel, enc)
        results.setdefault(key, rssi)

    sniff(iface=iface, prn=handler, store=False, timeout=scan_seconds)

    items = []
    for (ssid, bssid, channel, enc), rssi in results.items():
        items.append({"ssid": ssid, "bssid": bssid, "channel": channel, "enc": enc, "rssi": rssi})

    items.sort(key=lambda x: (x["ssid"], x["bssid"] or ""))
    return items[:max_results]


class DetectorEngine:
    def __init__(self, cfg_path="config/config.yaml"):
        self.cfg_path = cfg_path
        self.cfg = load_yaml(cfg_path)
        self.whitelist = load_json(self.cfg.get("whitelist_path", "config/whitelist.json"))
        self.rogue = RogueAPDetector(
            whitelist=self.whitelist,
            ssid_similarity_threshold=self.cfg.get("ssid_similarity_threshold", 0.85),
            alert_cooldown_seconds=self.cfg.get("alert_cooldown_seconds", 30),
        )
        self.deauth = DeauthDetector(
            window_seconds=self.cfg.get("window_seconds", 10),
            threshold=self.cfg.get("threshold_deauth", 20),
        )
        self.logger = EventLogger(
            log_path=self.cfg.get("log_path", "logs/wifi_alerts.jsonl"),
            opensearch_cfg=self.cfg.get("opensearch", {}),
            telegram_cfg=self.cfg.get("telegram", {}),
        )

    def run_sniffing(self, iface, target_bssid=None, target_channel=None, stop_event=None):
        def handler(pkt):
            if pkt.haslayer(Dot11Beacon):
                ssid = get_ssid(pkt)
                bssid = pkt.addr2 or pkt.addr3
                channel = get_channel(pkt)
                rssi = get_rssi(pkt)
                enc = get_encryption(pkt)
                if target_bssid and bssid and bssid.lower() != target_bssid.lower():
                    return
                if target_channel and channel and channel != target_channel:
                    return
                now_ts = utc_ts()
                now_epoch = time.time()
                for event in self.rogue.handle_ap(ssid, bssid, channel, rssi, enc, now_ts, now_epoch):
                    self.logger.log_event(event)

            if pkt.haslayer(Dot11Deauth):
                src = pkt.addr2
                dst = pkt.addr1
                ap_bssid = pkt.addr3 or pkt.addr2
                if target_bssid and ap_bssid and ap_bssid.lower() != target_bssid.lower():
                    return
                now_epoch = time.time()
                for event in self.deauth.handle_deauth(now_epoch, src, dst, ap_bssid):
                    self.logger.log_event(event)

        if stop_event is None:
            sniff(iface=iface, prn=handler, store=False)
            return

        while not stop_event.is_set():
            sniff(iface=iface, prn=handler, store=False, timeout=1)


class MonitorRunner:
    def __init__(self, cfg_path="config/config.yaml"):
        self.cfg_path = cfg_path
        self.thread = None
        self.stop_event = threading.Event()
        self.target_bssid = None
        self.target_channel = None
        self.last_error = None

    def start(self, target_bssid=None, target_channel=None):
        if self.thread and self.thread.is_alive():
            return False

        self.stop_event.clear()
        self.target_bssid = target_bssid
        self.target_channel = target_channel

        def _run():
            try:
                engine = DetectorEngine(self.cfg_path)
                iface = engine.cfg.get("interface", "wlan0mon")
                engine.run_sniffing(
                    iface=iface,
                    target_bssid=self.target_bssid,
                    target_channel=self.target_channel,
                    stop_event=self.stop_event,
                )
            except Exception as exc:
                self.last_error = str(exc)

        self.thread = threading.Thread(target=_run, daemon=True)
        self.thread.start()
        return True

    def stop(self):
        if self.thread and self.thread.is_alive():
            self.stop_event.set()
            self.thread.join(timeout=2)
            return True
        return False

    def status(self):
        return {
            "running": bool(self.thread and self.thread.is_alive()),
            "target_bssid": self.target_bssid,
            "target_channel": self.target_channel,
            "last_error": self.last_error,
        }
