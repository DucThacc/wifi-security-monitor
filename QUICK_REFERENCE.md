# QUICK REFERENCE - Hệ thống giám sát WiFi Security

## 🚀 Quick Start (5 phút)

```bash
# 1. Bật monitor mode
sudo airmon-ng start wlan0

# 2. Setup project
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Config whitelist (cập nhật SSID/BSSID)
nano config/whitelist.json

# 4. Chạy tool
sudo python -m detector.main

# 5. (Optional) Web dashboard
sudo uvicorn webapp.app:app --port 8000  # → http://localhost:8000
```

---

## 📋 Core Files

| File | Mục đích | Chỉnh sửa? |
|------|---------|-----------|
| `detector/main.py` | Entry point CLI | ❌ |
| `detector/engine.py` | Detection loop | ❌ |
| `detector/rogue_ap_detector.py` | Rogue AP logic | ❌ |
| `detector/deauth_detector.py` | Deauth counter | ❌ |
| `detector/logger.py` | Log + export | ❌ |
| `config/whitelist.json` | AP hợp lệ | ✅ **EDIT** |
| `config/config.yaml` | Thresholds | ✅ **TUNE** |
| `webapp/app.py` | Web UI | ❌ |
| `docker-compose.yml` | OpenSearch | ❌ |

---

## ⚙️ Configuration

### config/whitelist.json
```json
[
  {
    "ssid": "YOUR_SSID",
    "bssid": "AA:BB:CC:DD:EE:FF",
    "channel": 6,
    "encryption": "WPA2"
  }
]
```

### config/config.yaml (Important)
```yaml
interface: wlan0mon                    # Change if different
threshold_deauth: 20                   # Deauth frames
window_seconds: 10                     # Detection window
ssid_similarity_threshold: 0.85        # 0-1, higher = stricter

opensearch:
  enabled: false  # Set to true for dashboard
telegram:
  enabled: false  # Set to true for alerts
```

---

## 🎯 Commands Cheat Sheet

### Monitor Mode
```bash
# Check adapter
ip link
iw dev

# Enable
sudo airmon-ng start wlan0

# Check
iwconfig | grep wlan0mon

# Scan APs
sudo airodump-ng wlan0mon
```

### Tool
```bash
# Run (CLI)
sudo python -m detector.main

# Run (Web)
sudo uvicorn webapp.app:app --host 0.0.0.0 --port 8000

# Get info
python -c "from detector.utils import load_yaml; import pprint; pprint.pprint(load_yaml('config/config.yaml'))"
```

### Testing
```bash
# Rogue AP (hotspot)
# → Set phone hotspot SSID = "YOUR_SSID"
# → Turn on hotspot
# → Tool should alert within 20 sec

# Deauth attack
sudo aireplay-ng --deauth 25 -a AA:BB:CC:DD:EE:FF wlan0mon
# → Tool should alert within 10 sec
```

### Logging
```bash
# View logs
tail -f logs/wifi_alerts.jsonl

# Parse JSON
cat logs/wifi_alerts.jsonl | jq .

# Count alerts
cat logs/wifi_alerts.jsonl | wc -l

# Filter by type
cat logs/wifi_alerts.jsonl | jq 'select(.event_type=="rogue_ap_detected")'

# Statistics
cat logs/wifi_alerts.jsonl | jq -s 'group_by(.event_type) | map({type: .[0].event_type, count: length})'
```

### Dashboard
```bash
# Start OpenSearch
docker compose up -d

# Access
# - OpenSearch: http://localhost:9200
# - Dashboards: http://localhost:5601

# Check status
docker ps
docker compose logs opensearch | tail -5

# Stop
docker compose down
```

---

## 🔴 Alert Types

| Event | Trigger | Severity | Action |
|-------|---------|----------|--------|
| **rogue_ap_detected** | SSID match + BSSID diff | HIGH | Check physically |
| **suspicious_open_ap** | SSID similar + OPEN | MEDIUM | Investigate |
| **deauth_attack_detected** | ≥20 frames / 10s | HIGH | Alert admin |

---

## 📊 Web Dashboard Features

| Feature | URL | Action |
|---------|-----|--------|
| **Scan** | `/api/scan` | List nearby APs |
| **Whitelist** | `/api/whitelist` | CRUD whitelist |
| **Monitor** | `/api/monitor/start` | Start sniffing |
| **Logs** | `/api/logs/stream` | Realtime stream |

**Web UI:** http://localhost:8000

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| Monitor mode fails | `sudo apt install linux-firmware` |
| No AP in scan | Move closer to AP / check adapter |
| Permission denied | Use `sudo` before python |
| OpenSearch unreachable | `docker compose restart` |
| Web UI not responding | Kill old process: `lsof -i :8000` |
| Log file not created | Create manually: `mkdir -p logs` |

---

## 📈 Performance

- **CPU:** <5% (idle), <15% (active sniff)
- **RAM:** 150-300 MB
- **Network:** <1 Mbps
- **Latency:** Alert within 10 sec

---

## 📚 Documentation

| File | Content |
|------|---------|
| [README.md](README.md) | Main guide |
| [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) | 14-day roadmap |
| [docs/lab_steps.md](docs/lab_steps.md) | Detailed steps |
| [docs/test_cases.md](docs/test_cases.md) | 7 test scenarios |
| [docs/report_outline.md](docs/report_outline.md) | Report structure |
| [docs/checklist.md](docs/checklist.md) | Completion checklist |
| [docs/common_issues.md](docs/common_issues.md) | Troubleshooting |

---

## 🔐 Security Notes

✅ **SAFE:**
- Sniffing beacon frames
- Monitoring Wi-Fi traffic
- Logging events
- Alert generation

❌ **NOT ALLOWED:**
- Attacking live networks
- Cracking passwords
- Accessing unauthorized networks
- Intercepting encrypted data

**Use only in your own lab/network!**

---

## 📞 Support

### Before asking for help:

1. Check [docs/common_issues.md](docs/common_issues.md)
2. Verify config files (whitelist.json, config.yaml)
3. Confirm monitor mode is on: `iwconfig | grep Monitor`
4. Check tool output has no errors
5. Verify interface name in config matches system

### Debugging:

```bash
# Check system
uname -a
python3 --version
pip list | grep scapy

# Check network
ip link
iw dev
sudo airmon-ng check kill

# Check logs
tail -100 logs/wifi_alerts.jsonl
```

---

## 🎓 Learning Resources

- **802.11 Wireless:** https://en.wikipedia.org/wiki/IEEE_802.11
- **Scapy:** https://scapy.readthedocs.io/
- **aircrack-ng:** https://www.aircrack-ng.org/
- **OpenSearch:** https://opensearch.org/
- **FastAPI:** https://fastapi.tiangolo.com/

---

## 📋 Checklist Before Submission

- [ ] All code tested (7/7 test cases pass)
- [ ] Config files cleaned (no test values)
- [ ] Log files cleared
- [ ] Documentation complete
- [ ] No hardcoded passwords/tokens
- [ ] Screenshot collected (33 total)
- [ ] Report written
- [ ] Demo video ready
- [ ] Backup created

---

## 🎯 Success Indicators

✅ Tool runs without errors
✅ Detects rogue AP within 20 sec
✅ Detects deauth attack within 10 sec
✅ Log file has valid JSON
✅ Dashboard shows data
✅ Web UI responsive
✅ Documentation clear
✅ Test cases pass

---

**Version:** 1.0.0
**Date:** 2026-05-10
**Status:** Production Ready ✅
