from .engine import DetectorEngine, scan_targets
from .utils import load_yaml


def choose_target(items):
    if not items:
        print("[!] No AP found in scan window")
        return None, None

    print("\n=== Scan Results ===")
    for idx, item in enumerate(items, start=1):
        print(
            f"{idx:02d}) SSID={item['ssid']} BSSID={item['bssid']} "
            f"CH={item['channel']} ENC={item['enc']} RSSI={item['rssi']}"
        )

    choice = input("Select target index (Enter for all): ").strip()
    if not choice:
        return None, None

    try:
        index = int(choice)
        if 1 <= index <= len(items):
            return items[index - 1]["bssid"], items[index - 1]["channel"]
    except ValueError:
        pass

    print("[!] Invalid selection, using all")
    return None, None


def main():
    cfg = load_yaml("config/config.yaml")
    engine = DetectorEngine("config/config.yaml")
    iface = engine.cfg.get("interface", "wlan0mon")
    target_bssid = None
    target_channel = None

    if cfg.get("interactive_scan", False):
        print(f"[*] Scanning on {iface} for {cfg.get('scan_seconds', 8)} seconds")
        items = scan_targets(
            iface=iface,
            scan_seconds=cfg.get("scan_seconds", 8),
            max_results=cfg.get("scan_max_results", 20),
        )
        target_bssid, target_channel = choose_target(items)

    if target_bssid:
        print(f"[*] Targeting BSSID {target_bssid} (CH {target_channel})")
    else:
        print("[*] Targeting all APs")

    print(f"[*] Sniffing on {iface} (monitor mode required)")
    engine.run_sniffing(iface=iface, target_bssid=target_bssid, target_channel=target_channel)


if __name__ == "__main__":
    main()
