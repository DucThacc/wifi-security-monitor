# WiFi Security Monitor - Rogue AP & Deauth Detection

Hệ thống giám sát an ninh Wi-Fi và phát hiện Rogue AP, Evil Twin, Deauthentication Attack.

## Mục lục
1. [Phân tích đề tài](#1-phân-tích-đề-tài)
2. [Kiến trúc hệ thống](#2-kiến-trúc-hệ-thống)
3. [Chuẩn bị môi trường](#3-chuẩn-bị-môi-trường)
4. [Cài đặt](#4-cài-đặt)
5. [Chạy hệ thống](#5-chạy-hệ-thống)
6. [Kiểm thử](#6-kiểm-thử)
7. [Tích hợp Dashboard](#7-tích-hợp-dashboard)
8. [Cảnh báo Telegram](#8-cảnh-báo-telegram)
9. [Xử lý lỗi](#9-xử-lý-lỗi)
10. [Cảnh báo pháp lý](#10-cảnh-báo-pháp-lý)

---

## 1. Phân tích đề tài

### Các khái niệm chính

**Rogue AP (Unauthorized Access Point):**
- Access Point không được phép trong hệ thống
- Có thể do nhân viên không may cài đặt
- Có thể do attacker cố tình tấn công

**Evil Twin (Fake AP):**
- AP giả mao có SSID giống/tương tự AP hợp lệ nhưng BSSID khác
- Dùng để lừa client kết nối
- Client tưởng là AP thật nhưng thực tế kết nối vào AP giả của attacker

**Deauthentication Attack:**
- Attacker gửi nhiều frame deauthentication tới client hoặc AP
- Mục đích: cắt kết nối Wi-Fi của client
- Client sẽ tìm kết nối lại, có thể kết nối vào Evil Twin

**Wireless IDS/WIDS (Wireless Intrusion Detection System):**
- Hệ thống giám sát không dây
- Phát hiện hoạt động bất thường
- Không liên quan đến mạng có dây

**Rogue AP Detection vs AP Localization:**
- **Detection:** Phát hiện có AP không hợp lệ (Yes/No)
- **Localization:** Xác định vị trí chính xác AP (GPS/RSSI triangulation)
- Đề tài này chỉ thực hiện Detection

**Phạm vi đề tài:**
- ✅ Phát hiện Rogue AP
- ✅ Phát hiện Evil Twin
- ✅ Phát hiện Deauth Attack
- ✅ Ghi log chi tiết
- ✅ Dashboard giám sát
- ✅ Cảnh báo Telegram (optional)
- ❌ Định vị chính xác AP giả
- ❌ Crack password Wi-Fi
- ❌ Chiếm quyền truy cập

---

## 2. Kiến trúc hệ thống

### Sơ đồ kiến trúc

```
┌─────────────────┐    ┌──────────────────┐
│   Legit AP      │    │  Rogue/Evil Twin │
│ SSID: Company   │    │  SSID: Company   │
│ BSSID: AA:BB..  │    │  BSSID: 66:77..  │
└────────┬────────┘    └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    │ Beacon/Deauth Frame
                    │
         ┌──────────▼──────────┐
         │  Kali/Ubuntu PC     │
         │  USB Wi-Fi Adapter  │
         │  Monitor Mode       │
         └──────────┬──────────┘
                    │
         ┌──────────▼──────────┐
         │  Python Detection   │
         │  Engine (Scapy)     │
         │  - Rogue AP         │
         │  - Deauth Attack    │
         └──────────┬──────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
  JSON Log      OpenSearch    Telegram
  File          Dashboard      Alert
```

### Luồng xử lý

1. **Capture:** USB Wi-Fi adapter ở monitor mode bắt beacon/deauth frame
2. **Analyze:** Detection Engine phân tích:
   - SSID, BSSID, Channel, RSSI, Encryption
   - So sánh với whitelist
   - Đếm deauth frame
3. **Alert:** Nếu phát hiện:
   - In log JSON
   - Gửi OpenSearch (nếu bật)
   - Gửi Telegram (nếu bật)
4. **Dashboard:** Web UI hoặc OpenSearch Dashboards hiển thị realtime

---

## 3. Chuẩn bị môi trường

### Yêu cầu phần cứng

- **PC/Laptop:** Ubuntu/Kali Linux, 2GB RAM, 20GB disk
- **USB Wi-Fi adapter:** Hỗ trợ monitor mode (Atheros/Realtek tốt hơn)
- **Access Point:** Wi-Fi router thật để test
- **Điện thoại:** (optional) để tạo rogue AP

### Kiểm tra & Cài đặt

**Bước 1: Cập nhật hệ thống**

```bash
sudo apt update && sudo apt -y upgrade
```

**Bước 2: Cài đặt công cụ wireless**

```bash
sudo apt -y install aircrack-ng iw wireless-tools
```

**Bước 3: Kiểm tra USB Wi-Fi**

Cắm USB adapter rồi chạy:

```bash
ip link
# Output:
# wlan0: <BROADCAST,MULTICAST> mtu 1500
#       ...
```

```bash
iw dev
# Output:
# phy#0
#  Interface wlan0
#     ifindex 3
#     type managed
#     txpower 20.00 dBm
```

**Bước 4: Kiểm tra hỗ trợ monitor mode**

```bash
sudo iw list | grep -A 10 "Supported interface modes"
# Cần thấy dòng: * monitor
```

**Bước 5: Bật monitor mode**

```bash
# Kill các tiến trình can thiệp
sudo airmon-ng check kill

# Bật monitor mode
sudo airmon-ng start wlan0
# Output: (phy0) - Switching to monitor mode for [phy0]wlan0
#         (monitor mode enabled on [phy0]wlan0mon)

# Kiểm tra
iwconfig
# Output:
# wlan0mon  IEEE 802.11bgn  Mode:Monitor  Frequency:2.412 GHz
```

**Bước 6: Kiểm tra bắt packet**

```bash
sudo airodump-ng wlan0mon
# Nên thấy danh sách AP khoảng 1-2 giây
```

**Bước 7: Cài Python & pip**

```bash
sudo apt -y install python3 python3-pip python3-venv docker.io docker-compose
```

---

## 4. Cài đặt

### Clone/Setup project

```bash
cd ~/wifi-security-monitor

# Tạo virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Cài dependencies
pip install -r requirements.txt
```

### Cấu hình whitelist

Chỉnh sửa [config/whitelist.json](config/whitelist.json) với AP thật của bạn.

Tìm SSID/BSSID thật:

```bash
sudo airodump-ng wlan0mon
# BSSID              SSID              CH   MB   ENC CIPHER AUTH
# AA:BB:CC:11:22:33  Company-WiFi       6   130  WPA2 CCMP   PSK
```

Cập nhật file:

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

### Cấu hình chính

[config/config.yaml](config/config.yaml):

```yaml
interface: wlan0mon
whitelist_path: config/whitelist.json
log_path: logs/wifi_alerts.jsonl

# Scan setting
interactive_scan: true    # true = chọn AP từ menu, false = quet tất cả
scan_seconds: 8
scan_max_results: 20

# Rogue AP detection
ssid_similarity_threshold: 0.85   # 0-1, càng cao càng chặt
alert_cooldown_seconds: 30        # Tránh spam alert cùng SSID

# Deauth detection
window_seconds: 10        # Cửa sổ thời gian
threshold_deauth: 20      # Ngưỡng deauth frame

# OpenSearch (optional)
opensearch:
  enabled: false
  endpoint: http://localhost:9200
  index: wifi-security-logs
  verify_tls: false

# Telegram (optional)
telegram:
  enabled: false
  bot_token: "YOUR_TOKEN"
  chat_id: "YOUR_CHAT_ID"
```

---

## 5. Chạy hệ thống

### Mode CLI (command line)

```bash
sudo .venv/bin/python -m detector.main
```

**Khi `interactive_scan: true`:**

1. Tool sẽ quét 8 giây
2. Hiển thị danh sách AP
3. Nhập số thứ tự để chọn target (ví dụ: `1`)
4. Hoặc bấm Enter để quét tất cả
5. Bắt đầu sniffing và in alert realtime

**Output mẫu:**

```
[*] Scanning on wlan0mon for 8 seconds
[ALERT] SSID matches legitimate AP but BSSID is unknown
[ALERT] Deauth frame burst exceeds threshold
```

### Mode Web (FastAPI Dashboard)

```bash
sudo .venv/bin/python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

Mở browser: **http://localhost:8000**

Chức năng:
- 📊 Dashboard realtime
- 🔍 Scan & chọn AP
- ⚙️ Quản lý whitelist (add/edit/delete)
- ▶️ Start/Stop monitor
- 📋 Xem log chi tiết
- 📈 Biểu đồ alert thống kê

---

## 6. Kiểm thử

### TC01: Phát hiện AP hợp lệ

```bash
# Chạy tool
sudo .venv/bin/python -m detector.main

# Kết quả: AP legit trong whitelist không có alert
```

### TC02: Phát hiện Rogue AP / Evil Twin

**Cách 1 - Dùng Hotspot điện thoại:**

1. Tắt hotspot trước
2. Chạy tool
3. Đặt hotspot SSID = "Company-WiFi" (giống whitelist)
4. Bật hotspot
5. Quan sát terminal:

```
[ALERT] SSID matches legitimate AP but BSSID is unknown
```

Kiểm tra log:

```bash
tail -f logs/wifi_alerts.jsonl
# {"timestamp": "...", "event_type": "rogue_ap_detected", ...}
```

**Cách 2 - Dùng hostapd (Kali):**

Mở terminal thứ 2:

```bash
sudo apt -y install hostapd
cat <<'EOF' > /tmp/fakeap.conf
interface=wlan0
ssid=Company-WiFi
hw_mode=g
channel=6
auth_algs=1
ignore_broadcast_ssid=0
EOF
sudo hostapd /tmp/fakeap.conf
```

Kiểm tra terminal 1 (tool):

```
[ALERT] SSID matches legitimate AP but BSSID is unknown
```

### TC03: Phát hiện Deauthentication Attack

Mở terminal thứ 2 và giả lập deauth attack:

```bash
# Gửi 20 deauth frame trong 10 giây
sudo aireplay-ng --deauth 20 -a AA:BB:CC:11:22:33 wlan0mon
```

Kiểm tra terminal 1:

```
[ALERT] Deauth frame burst exceeds threshold
```

Kiểm tra log:

```bash
tail -f logs/wifi_alerts.jsonl
# {"event_type": "deauth_attack_detected", "count": 20, ...}
```

### TC04: Log JSON format

```bash
cat logs/wifi_alerts.jsonl | jq .
```

Output mẫu:

```json
{
  "timestamp": "2026-05-10T12:00:00Z",
  "event_type": "rogue_ap_detected",
  "ssid": "Company-WiFi",
  "legit_bssid": "AA:BB:CC:11:22:33",
  "detected_bssid": "66:77:88:99:AA:BB",
  "channel": 6,
  "rssi": -42,
  "severity": "high",
  "message": "SSID matches legitimate AP but BSSID is unknown"
}
```

---

## 7. Tích hợp Dashboard

### OpenSearch + Docker Compose

**Bước 1: Start containers**

```bash
docker compose up -d
```

**Bước 2: Chờ 30 giây và check**

```bash
# OpenSearch
curl -u admin:admin -k https://localhost:9200/

# Dashboards
open http://localhost:5601
```

Tên đăng nhập: `admin` / Mật khẩu: `admin`

**Bước 3: Cấu hình log push**

Chỉnh sửa [config/config.yaml](config/config.yaml):

```yaml
opensearch:
  enabled: true
  endpoint: http://localhost:9200
  index: wifi-security-logs
  verify_tls: false
```

**Bước 4: Tạo index pattern**

1. Vào OpenSearch Dashboards
2. Index Management → Indices
3. Nên thấy `wifi-security-logs` (nếu chạy tool với log mới)

**Bước 5: Tạo dashboard**

1. OpenSearch Dashboards → Visualize → New visualization
2. Tạo các chart:
   - **Alert count:** Count of records
   - **Event type pie:** Terms aggregation on event_type
   - **Timeline:** Date histogram on timestamp
   - **Top BSSID:** Terms aggregation on detected_bssid

---

## 8. Cảnh báo Telegram

### Tạo Telegram Bot

1. Mở Telegram, tìm `@BotFather`
2. Gõ `/start` → `/newbot`
3. Đặt tên: "WiFi Security Monitor"
4. Lấy bot token (ví dụ: `123:ABCDefg...`)
5. Gõ `/start @YourBotName` để activate

### Lấy Chat ID

1. Mở bot vừa tạo
2. Gõ `/start`
3. Truy cập: `https://api.telegram.org/bot<TOKEN>/getUpdates`
4. Tìm `"id": XXXXXXXX` (chat_id)

### Cấu hình

[config/config.yaml](config/config.yaml):

```yaml
telegram:
  enabled: true
  bot_token: "123:ABCDefg..."
  chat_id: "987654321"
```

Khi phát hiện alert, bot sẽ gửi message tới chat.

---

## 9. Xử lý lỗi

### Lỗi: "Monitor mode not supported"

```
[Errno 9] Bad file descriptor
```

**Giải pháp:**
- Cập nhật driver: `sudo ubuntu-drivers install`
- Thử adapter khác
- Dùng Kali Linux (hỗ trợ tốt hơn Ubuntu)

### Lỗi: "Permission denied"

```
PermissionError: [Errno 13] Permission denied
```

**Giải pháp:**
```bash
sudo .venv/bin/python -m detector.main
```

### Lỗi: "No beacon captured"

**Giải pháp:**
- Kiểm tra AP bật: `sudo airodump-ng wlan0mon`
- Đổi channel: `sudo iwconfig wlan0mon channel 6`
- Đổi qua monitor mode lại: `sudo airmon-ng stop wlan0mon && sudo airmon-ng start wlan0`

### Lỗi: OpenSearch timeout

```
Connection timeout
```

**Giải pháp:**
```bash
docker ps
# Nếu container tắt: docker compose up -d
# Nếu port 9200 bận: lsof -i :9200 && kill -9 PID
```

---

## 10. Cảnh báo pháp lý

⚠️ **QUAN TRỌNG:**

1. **Chỉ test trong lab của chính mình**
2. **Không tấn công mạng người khác**
3. **Không crack password Wi-Fi**
4. **Không chiếm quyền truy cập**
5. **Keafterall kỹ thuật này tuân thủ pháp luật địa phương**
6. **Có thể bị phạt nặng nếu vi phạm**

---

## Checklist hoàn thành 14 ngày

- [ ] Ngày 1-2: Chuẩn bị môi trường, test monitor mode
- [ ] Ngày 3-4: Code beacon scanner, whitelist config
- [ ] Ngày 5-6: Detect rogue AP, test với hotspot
- [ ] Ngày 7-8: Detect deauth attack, test với aireplay-ng
- [ ] Ngày 9-10: Hoàn thiện logging, tích hợp OpenSearch
- [ ] Ngày 11: Web dashboard
- [ ] Ngày 12: README, test cases
- [ ] Ngày 13: Report
- [ ] Ngày 14: Demo & slides

---

## Tham khảo

- Scapy: https://scapy.readthedocs.io/
- aircrack-ng: https://www.aircrack-ng.org/
- OpenSearch: https://opensearch.org/
- FastAPI: https://fastapi.tiangolo.com/
