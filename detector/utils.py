import json
import os
from datetime import datetime, timezone
from difflib import SequenceMatcher

from scapy.all import Dot11Elt


def utc_ts():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_yaml(path):
    import yaml

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def normalize_ssid(ssid):
    if ssid is None:
        return ""
    return ssid.strip().lower()


def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()


def ensure_dir(path):
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)


def get_channel(pkt):
    elt = pkt.getlayer(Dot11Elt)
    while elt is not None:
        if elt.ID == 3 and elt.info:
            return int(elt.info[0])
        elt = elt.payload.getlayer(Dot11Elt)
    return None


def get_ssid(pkt):
    elt = pkt.getlayer(Dot11Elt)
    while elt is not None:
        if elt.ID == 0:
            try:
                return elt.info.decode(errors="ignore")
            except Exception:
                return None
        elt = elt.payload.getlayer(Dot11Elt)
    return None


def get_rssi(pkt):
    if hasattr(pkt, "dBm_AntSignal"):
        try:
            return int(pkt.dBm_AntSignal)
        except Exception:
            return None
    return None


def get_encryption(pkt):
    # Basic heuristic for Open/WEP/WPA/WPA2
    cap = getattr(pkt, "cap", None)
    privacy = bool(cap and cap.privacy)
    wpa = False
    wpa2 = False

    elt = pkt.getlayer(Dot11Elt)
    while elt is not None:
        if elt.ID == 48:
            wpa2 = True
        if elt.ID == 221 and elt.info.startswith(b"\x00P\xf2\x01\x01\x00"):
            wpa = True
        elt = elt.payload.getlayer(Dot11Elt)

    if wpa2:
        return "WPA2"
    if wpa:
        return "WPA"
    if privacy:
        return "WEP"
    return "OPEN"
