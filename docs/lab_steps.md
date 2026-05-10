# Lab Steps - Hướng dẫn chi tiết 14 ngày

## TUẦN 1: Xây dựng nền tảng detection

### Ngày 1-2: Chuẩn bị OS & kiểm tra USB Wi-Fi

**Mục tiêu:** OS sẵn sàng, adapter hoạt động, monitor mode bật

**Công việc:**
- Cài Kali/Ubuntu mới
- Cập nhật hệ thống
- Cài aircrack-ng, iw, wireless-tools
- Cắm USB Wi-Fi
- Kiểm tra interface: `ip link`, `iw dev`
- Kiểm tra monitor mode support: `sudo iw list | grep monitor`
- Bật monitor mode: `sudo airmon-ng start wlan0`
- Test bắt packet: `sudo airodump-ng wlan0mon` (20 giây, nên thấy AP)

**Checklist:**
- [ ] OS installed
- [ ] Adapter recognized
- [ ] Monitor mode enabled
- [ ] Can see APs in airodump-ng

**Troubleshoot:**
- Adapter không nhận diện → Check `lsusb`, thử port USB khác
- Monitor mode failed → Update driver: `sudo apt install linux-firmware`
- No APs in scan → Kiểm tra Wi-Fi có bật, đổi channel

---

### Ngày 3-4: Beacon scanning & whitelist config

**Mục tiêu:** Xác định AP thật, tạo whitelist

**Công việc:**

1. **Scan và lấy thông tin AP thật:**

```bash
# Terminal 1 - Quét 30 giây
sudo airodump-ng wlan0mon --write-interval 1

# Ghi lại:
# - SSID: Company-WiFi
# - BSSID: AA:BB:CC:11:22:33
# - CHANNEL: 6
# - ENCRYPTION: WPA2
```

2. **Tạo project Python:**

```bash
cd ~
mkdir wifi-security-monitor
cd wifi-security-monitor

# Clone hoặc copy code
git clone <repo> .

# Tạo venv
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

3. **Cấu hình whitelist.json:**

```bash
# Sửa file
nano config/whitelist.json
```

Nội dung:
```json
[
  {
    "ssid": "Company-WiFi",
    "bssid": "AA:BB:CC:11:22:33",
    "channel": 6,
    "encryption": "WPA2"
  }
]
```

4. **Cấu hình config.yaml:**

```bash
nano config/config.yaml
```

Các parameter quan trọng:
```yaml
interface: wlan0mon                          # Thay đổi nếu interface khác
interactive_scan: true                       # true = chọn từ menu
scan_seconds: 8                              # Quét 8 giây
threshold_deauth: 20                         # Ngưỡng deauth frame
ssid_similarity_threshold: 0.85              # Mức tương đồng SSID
```

**Checklist:**
- [ ] Whitelist config đúng với AP thật
- [ ] Config file chỉnh đúng interface
- [ ] Dependencies cài xong
- [ ] Python venv activate được

---

### Ngày 5-6: Detect rogue AP

**Mục tiêu:** Tool phát hiện AP giả mao (Evil Twin)

**Công việc:**

1. **Test tool trên AP thật:**

```bash
cd ~/wifi-security-monitor
source .venv/bin/activate

# Chạy tool
sudo .venv/bin/python -m detector.main

# Menu sẽ hiện danh sách AP, chọn số của Company-WiFi
# Nếu không có alert = OK (AP hợp lệ)
```

2. **Tạo rogue AP - Cách 1 (Hotspot điện thoại):**

**Terminal 1 - Chạy tool:**
```bash
sudo .venv/bin/python -m detector.main
# Chọn: 1 (hoặc số của Company-WiFi)
# Output: [*] Targeting BSSID AA:BB:CC:11:22:33 (CH 6)
```

**Điện thoại - Tạo hotspot:**
- Tên SSID: "Company-WiFi" (giống whitelist nhưng khác BSSID)
- Bật Hotspot

**Terminal 1 - Quan sát:**
```
[ALERT] SSID matches legitimate AP but BSSID is unknown
```

3. **Tạo rogue AP - Cách 2 (hostapd - chuyên nghiệp hơn):**

**Terminal 2:**
```bash
sudo apt install -y hostapd

# Tạo config (giả sử adapter 2 = wlan1)
cat <<'EOF' > /tmp/fakeap.conf
interface=wlan1
ssid=Company-WiFi
hw_mode=g
channel=6
auth_algs=1
wpa=0
EOF

# Chạy
sudo hostapd /tmp/fakeap.conf
# Output: wlan1: AP-ENABLED
```

**Terminal 1:**
```
[ALERT] SSID matches legitimate AP but BSSID is unknown
```

4. **Kiểm tra log:**

```bash
# Terminal 3
tail -f logs/wifi_alerts.jsonl | jq .

# Output:
{
  "timestamp": "2026-05-10T14:20:00Z",
  "event_type": "rogue_ap_detected",
  "ssid": "Company-WiFi",
  "legit_bssid": "AA:BB:CC:11:22:33",
  "detected_bssid": "66:77:88:99:AA:BB",
  "severity": "high"
}
```

**Checklist:**
- [ ] Tool phát hiện AP thật (không alert)
- [ ] Tool phát hiện fake AP từ hotspot
- [ ] Tool phát hiện fake AP từ hostapd
- [ ] Log JSON format đúng

---

### Ngày 7: Detect deauthentication attack

**Mục tiêu:** Phát hiện deauth frame burst

**Công việc:**

1. **Test deauth detection:**

**Terminal 1 - Chạy tool:**
```bash
sudo .venv/bin/python -m detector.main
# Chọn target AP: Company-WiFi
```

**Terminal 2 - Gửi deauth frame:**
```bash
# Tìm BSSID từ airodump-ng
sudo airodump-ng wlan0mon | grep "Company-WiFi"
# Output: AA:BB:CC:11:22:33  ...  Company-WiFi

# Gửi 25 deauth frame
sudo aireplay-ng --deauth 25 -a AA:BB:CC:11:22:33 wlan0mon

# Output:
# 14:30:45  Sending 25 DeAuth (Code 7) directed to broadcast
# 14:30:46  Sent 25 packages
```

**Terminal 1 - Quan sát:**
```
[ALERT] Deauth frame burst exceeds threshold
```

2. **Kiểm tra log:**

```bash
tail -f logs/wifi_alerts.jsonl | jq '.[] | select(.event_type=="deauth_attack_detected")'

# Output:
{
  "timestamp": "2026-05-10T14:35:00Z",
  "event_type": "deauth_attack_detected",
  "source_mac": "FF:FF:FF:FF:FF:FF",
  "destination_mac": "FF:FF:FF:FF:FF:FF",
  "ap_bssid": "AA:BB:CC:11:22:33",
  "count": 25,
  "window_seconds": 10,
  "severity": "high"
}
```

3. **Test threshold:**

Chỉnh `config.yaml` để test:
```yaml
window_seconds: 10           # Cửa sổ 10 giây
threshold_deauth: 20         # Ngưỡng 20 frame
```

Gửi ít hơn 20 frame → không alert
Gửi 20+ frame → alert

**Checklist:**
- [ ] Detect deauth frame burst ≥20 frames/10s
- [ ] Log format chính xác
- [ ] Threshold có thể chỉnh
- [ ] Clear threshold = không alert

---

## TUẦN 2: Hoàn thiện & tích hợp

### Ngày 8: OpenSearch dashboard

**Mục tiêu:** Đẩy log lên OpenSearch, xem dashboard

**Công việc:**

1. **Cài Docker:**

```bash
sudo apt install -y docker.io docker-compose
```

2. **Chạy OpenSearch:**

```bash
cd ~/wifi-security-monitor
docker compose up -d

# Chờ ~30 giây
sleep 30

# Check status
docker ps
# CONTAINER ID   STATUS
# abc123...      Up 25 seconds (healthy)  ← OpenSearch
# def456...      Up 20 seconds             ← Dashboards
```

3. **Enable output vào OpenSearch:**

```bash
nano config/config.yaml

# Chỉnh:
opensearch:
  enabled: true
  endpoint: http://localhost:9200
  index: wifi-security-logs
  verify_tls: false
```

4. **Chạy tool:**

```bash
# Terminal 1
sudo .venv/bin/python -m detector.main

# Chọn target & trigger alert (hotspot rogue/deauth)
# Log sẽ được đẩy vào OpenSearch
```

5. **Truy cập Dashboards:**

- Mở: http://localhost:5601
- Index Management → Indices
- Nên thấy `wifi-security-logs` index

6. **Tạo visualization:**

- Create Visualization
- Query: `event_type: "rogue_ap_detected"`
- Chart type: Count, Pie, Timeline, etc.

**Checklist:**
- [ ] Docker containers chạy
- [ ] Log đẩy lên OpenSearch thành công
- [ ] Index wifi-security-logs tạo
- [ ] Dashboard visualize được

---

### Ngày 9: Web dashboard FastAPI

**Mục tiêu:** Web UI quản lý & monitor realtime

**Công việc:**

1. **Chạy web server:**

```bash
cd ~/wifi-security-monitor
source .venv/bin/activate

# Terminal 1
sudo .venv/bin/uvicorn webapp.app:app --host 0.0.0.0 --port 8000

# Output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

2. **Truy cập web:**

- Mở: http://localhost:8000

**Chức năng:**
- 📊 Scan & chọn AP
- 📋 Whitelist management (add/edit/delete)
- ▶️ Start/Stop monitoring
- 📈 Realtime chart (rogue/deauth)
- 🔍 Live logs stream

3. **Test các chức năng:**

- Scan AP: Click "Scan", nên thấy danh sách AP
- Whitelist: Add/Edit/Delete entry
- Monitor: Click "Start" để bắt đầu
- Trigger alert: Hotspot hoặc deauth
- Chart: Nên thấy realtime update

**Checklist:**
- [ ] Web server chạy tại :8000
- [ ] Scan function hoạt động
- [ ] Whitelist management OK
- [ ] Monitor start/stop OK
- [ ] Live logs stream realtime
- [ ] Chart update realtime

---

### Ngày 10-11: Telegram alert (optional)

**Mục tiêu:** Nhận alert qua Telegram bot

**Công việc:**

1. **Tạo Telegram bot:**

- Mở Telegram, tìm `@BotFather`
- `/start` → `/newbot`
- Tên bot: "WiFi Security Monitor"
- Lấy token: `123:ABCDefg...`

2. **Lấy Chat ID:**

- Mở bot vừa tạo
- `/start`
- Truy cập: `https://api.telegram.org/bot<TOKEN>/getUpdates`
- Tìm `"id": 987654321`

3. **Cấu hình:**

```bash
nano config/config.yaml

# Chỉnh:
telegram:
  enabled: true
  bot_token: "123:ABCDefg..."
  chat_id: "987654321"
```

4. **Test:**

```bash
# Terminal 1
sudo .venv/bin/python -m detector.main

# Terminal 2 - Trigger alert
sudo aireplay-ng --deauth 25 -a AA:BB:CC:11:22:33 wlan0mon

# Telegram: Nhận message "[ALERT] Deauth frame burst exceeds threshold"
```

**Checklist:**
- [ ] Telegram bot token có
- [ ] Chat ID có
- [ ] Config cấu hình đúng
- [ ] Nhận alert qua bot

---

### Ngày 12: README & Test cases

**Mục tiêu:** Tài liệu đầy đủ

**Công việc:**

Xem các file:
- [README.md](../README.md) - Hướng dẫn sử dụng chính
- [test_cases.md](test_cases.md) - Chi tiết test case
- [common_issues.md](common_issues.md) - Troubleshooting

**Checklist:**
- [ ] README đầy đủ & clear
- [ ] Test cases pass
- [ ] Troubleshooting guide có

---

### Ngày 13: Viết báo cáo

**Mục tiêu:** Báo cáo kỹ thuật

Xem: [report_outline.md](report_outline.md)

---

### Ngày 14: Demo & slides

**Mục tiêu:** Chuẩn bị presentation

**Nội dung:**
1. Architecture diagram
2. Live demo: Phát hiện rogue AP
3. Live demo: Phát hiện deauth
4. Log/Dashboard
5. Code highlights

---

## Tóm tắt timeline

| Ngày | Công việc | Deadline |
|------|----------|----------|
| 1-2 | OS setup, monitor mode | Day 2 PM |
| 3-4 | Beacon scan, whitelist | Day 4 PM |
| 5-6 | Rogue AP detection + test | Day 6 PM |
| 7 | Deauth detection | Day 7 PM |
| 8 | OpenSearch integration | Day 8 PM |
| 9 | Web dashboard | Day 9 PM |
| 10-11 | Telegram alert | Day 11 PM |
| 12 | Doc + test cases | Day 12 PM |
| 13 | Report writing | Day 13 PM |
| 14 | Demo & presentation | Day 14 PM |

---

## Mẹo & Best practices

1. **Ghi lại log thường xuyên** - Dùng screenshot để minh chứng
2. **Test từng bước** - Không chờ cuối để phát hiện lỗi
3. **Backup config** - Trước khi thay đổi lớn
4. **Monitor resource** - `htop`, `docker stats`
5. **Keep notes** - Ghi lại lỗi & cách fix

## Resources

- Scapy docs: https://scapy.readthedocs.io/
- aircrack-ng: https://www.aircrack-ng.org/
- OpenSearch: https://opensearch.org/
- FastAPI: https://fastapi.tiangolo.com/
