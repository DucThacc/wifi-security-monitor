# Report Outline - Hệ thống giám sát An ninh Wi-Fi

## PHẦN MỞ ĐẦU

### Chương 1: Tổng quan đề tài

#### 1.1 Lý do chọn đề tài
- Tầm quan trọng của Wi-Fi security trong IoT/Smart Home/Enterprise
- Nguy hiểm từ Rogue AP, Evil Twin, Deauth Attack
- Nhu cầu WIDS/giám sát mạng không dây
- Kỹ năng cần thiết: Wireless, Python, Linux, IDS/IPS

#### 1.2 Mục tiêu đề tài
- **Chính:** Xây dựng hệ thống phát hiện Rogue AP và Deauth Attack
- **Phụ:** Giám sát realtime, cảnh báo, logging, dashboard
- **Thực hành:** Lab demo, code Python, tài liệu đầy đủ

#### 1.3 Phạm vi đề tài

**Công việc thực hiện:**
- ✅ Phát hiện Rogue AP (SSID trùng, BSSID khác)
- ✅ Phát hiện Evil Twin (SSID tương tự, mở)
- ✅ Phát hiện Deauthentication Attack (burst frame)
- ✅ Logging JSON realtime
- ✅ Dashboard OpenSearch
- ✅ Web UI quản lý
- ✅ Cảnh báo Telegram (optional)

**Không thực hiện:**
- ❌ Định vị chính xác AP giả (geolocation)
- ❌ Crack password Wi-Fi
- ❌ Chiếm quyền truy cập
- ❌ Packet sniffing dữ liệu
- ❌ Deep packet inspection

#### 1.4 Đối tượng & giới hạn
- **Đối tượng:** An ninh mạng, SysAdmin, người học Wireless
- **Giới hạn:** Lab riêng, không tấn công mạng public
- **Thời gian:** 14 ngày triển khai

---

## PHẦN LÝ THUYẾT

### Chương 2: Cơ sở lý thuyết

#### 2.1 Khái niệm Wireless 802.11

**Beacon Frame:**
- Frame quảng bá của AP
- Chứa: SSID, BSSID, Channel, Timestamp, Capabilities
- Gửi mỗi 100ms
- Dùng để client scan & kết nối

**BSSID (Basic Service Set ID):**
- MAC address của AP (ví dụ: AA:BB:CC:11:22:33)
- Duy nhất trong mỗi AP
- Không thể giả mạo dễ (phần cứng sửa khó)

**SSID (Service Set Identifier):**
- Tên Wi-Fi (ví dụ: Company-WiFi)
- Có thể trùng nhau
- Có thể ẩn (hidden SSID)

**Encryption types:**
- OPEN: Không mã hóa
- WEP: Cũ, bị crack dễ
- WPA: Tốt hơn WEP
- WPA2: Hiện đại, tốt
- WPA3: Mới nhất (2018+)

#### 2.2 Tấn công Wireless

**Rogue AP / Unauthorized AP:**
- AP không được phép trong hệ thống
- Nguy hiểm: Man-in-the-middle, dữ liệu bị chiếm
- Ví dụ: Nhân viên cài AP riêng, hoặc attacker cài

**Evil Twin / Fake AP:**
- AP giả mao có SSID giống/tương tự AP thật
- BSSID khác
- Client tưởng kết nối AP thật nhưng thực tế kết nối attacker
- Attacker có thể:
  - Bắt all traffic
  - Inject malware
  - Lừa DNS

**Deauthentication Attack:**
- Attacker gửi deauth frame (subtype 12)
- Gửi tới client hoặc AP
- Client bị ngắt kết nối
- Client sẽ tìm kết nối lại (rất nhanh)
- Attacker có thể lợi dụng:
  - Bắt WPA handshake (crack password)
  - Lừa client kết nối Evil Twin

#### 2.3 Wireless IDS/WIDS

**Định nghĩa:**
- Intrusion Detection System cho mạng không dây
- Monitor Wi-Fi frame & phát hiện bất thường
- Không block, chỉ alert (passive)

**So sánh với Wired IDS:**
- Wired IDS: Monitor traffic trên switch/router
- WIDS: Monitor Wi-Fi frame trên air

**Thành phần WIDS:**
- Sensor (monitor): Bắt frame từ air
- Detection Engine: Phân tích & so sánh
- Database: Lưu whitelist, known attack patterns
- Alert: Gửi notification
- Dashboard: Visualize

**Thách thức WIDS:**
- Monitor 2.4GHz & 5GHz đồng thời
- Nhiều channel (1-14 ở 2.4GHz, 36-165 ở 5GHz)
- Phải bắt beacon frame thường xuyên
- False positive từ roaming clients

#### 2.4 Phân biệt Detection vs Localization

**Detection:**
- Phát hiện: "Có AP không hợp lệ không?"
- Kết quả: Yes/No hoặc severity level
- Đơn giản, nhanh
- Đây là đề tài

**Localization:**
- Định vị: "AP ở đâu?"
- Phương pháp: GPS, RSSI triangulation, time-difference-of-arrival
- Cần nhiều sensor
- Phức tạp, chậm
- Không làm ở đề tài này

#### 2.5 Chuỗi tấn công điển hình

```
1. Attacker tạo Rogue AP (Evil Twin)
   ↓
2. Broadcast beacon frame với SSID giống AP thật
   ↓
3. Client thấy 2 AP cùng SSID, chuẩn bị chuyển
   ↓
4. Attacker gửi Deauth frame tới client (cắt AP thật)
   ↓
5. Client mất kết nối, scan lại
   ↓
6. Client thấy Evil Twin (signal mạnh hơn hoặc ngay sát)
   ↓
7. Client kết nối vào Evil Twin
   ↓
8. Attacker có toàn quyền traffic của client
```

---

## PHẦN THIẾT KẾ

### Chương 3: Thiết kế hệ thống

#### 3.1 Kiến trúc tổng thể

```
┌─────────────────┐    ┌──────────────────┐
│  Legit AP       │    │  Rogue/Evil Twin │
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
         ┌──────────▼──────────────────┐
         │  Python Detection Engine    │
         │  - Beacon decoder           │
         │  - Rogue AP detector        │
         │  - Deauth counter           │
         │  - Logger (JSON)            │
         └──────────┬──────────────────┘
                    │
      ┌─────────────┼─────────────┐
      │             │             │
      ▼             ▼             ▼
   JSON Log      OpenSearch   Telegram
   File          Dashboard    Alert
  Local FS       http://      API
```

#### 3.2 Luồng dữ liệu (Data Flow)

**Capture Phase:**
```
USB Wi-Fi (monitor)
  ↓ (Scapy sniff)
802.11 Beacon Frame
  ├─ SSID
  ├─ BSSID
  ├─ Channel
  ├─ RSSI
  └─ Encryption
```

**Analysis Phase:**
```
Beacon Frame
  ↓ (Parse)
Extract: SSID, BSSID, Channel, etc.
  ↓ (Lookup)
Whitelist check
  ├─ SSID exist?
  │  ├─ YES → BSSID match?
  │  │   ├─ YES → OK (legitimate)
  │  │   └─ NO  → ALERT (rogue AP)
  │  └─ NO → Similar SSID?
  │     ├─ YES + OPEN → ALERT (suspicious)
  │     └─ NO → Skip
  └─ Deauth frame?
     └─ Count ≥ threshold? → ALERT
```

**Output Phase:**
```
Alert
  ↓ (JSON)
Log file (JSONL)
  ├─ Local disk
  ├─ OpenSearch (http push)
  └─ Telegram (bot API)
```

#### 3.3 Module & Components

| Module | Mục đích | Input | Output |
|--------|---------|-------|--------|
| `engine.py` | Main detection loop | Config | Events |
| `rogue_ap_detector.py` | Rogue AP logic | Beacon frame | Alert event |
| `deauth_detector.py` | Deauth counting | Deauth frame | Alert event |
| `logger.py` | Event persistence | Event | Log file, HTTP |
| `utils.py` | Helper functions | Data | Parsed data |
| `webapp.app` | Web dashboard | HTTP request | HTML/JSON |

#### 3.4 Thiết kế Whitelist

**Cấu trúc:**
```json
[
  {
    "ssid": "Company-WiFi",
    "bssid": "AA:BB:CC:11:22:33",
    "channel": 6,
    "encryption": "WPA2"
  },
  {
    "ssid": "Guest-WiFi",
    "bssid": "DD:EE:FF:44:55:66",
    "channel": 11,
    "encryption": "WPA2"
  }
]
```

**Cách sử dụng:**
- Load khi tool khởi động
- Để lại fixed, không dynamic update (tạm)
- Format: JSON file

#### 3.5 Thiết kế Alert Threshold

**Rogue AP Detection:**
- SSID match whitelist + BSSID mismatch = HIGH alert
- SSID similar (>85%) + OPEN = MEDIUM alert
- Cooldown: 30 giây (avoid spam)

**Deauth Detection:**
- Frame count ≥ threshold (default 20) trong window (default 10 giây) = HIGH alert
- Tunable trong config.yaml

#### 3.6 Config Management

**File: config.yaml**
```yaml
interface: wlan0mon
whitelist_path: config/whitelist.json
log_path: logs/wifi_alerts.jsonl

interactive_scan: true
scan_seconds: 8

ssid_similarity_threshold: 0.85
alert_cooldown_seconds: 30

window_seconds: 10
threshold_deauth: 20

opensearch:
  enabled: false
  endpoint: http://localhost:9200
  index: wifi-security-logs

telegram:
  enabled: false
  bot_token: ""
  chat_id: ""
```

---

## PHẦN TRIỂN KHAI

### Chương 4: Triển khai hệ thống

#### 4.1 Chuẩn bị môi trường

**Phần cứng:**
- PC/Laptop: 2GB RAM, 20GB disk
- USB Wi-Fi: Atheros/Realtek tốt hơn
- AP target: Wi-Fi router thật

**Phần mềm:**
```bash
# OS: Kali/Ubuntu 22.04
# Tools: aircrack-ng, iw, wireless-tools
# Python: 3.9+
# Docker: compose v2+
```

**Cài đặt:**
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y aircrack-ng iw wireless-tools python3 python3-pip python3-venv docker.io docker-compose
```

#### 4.2 Cấu hình Monitor Mode

**Bước 1: Kiểm tra interface**
```bash
ip link        # Tìm wlan0
iw dev          # Tìm phy#0
```

**Bước 2: Kill tiến trình**
```bash
sudo airmon-ng check kill
```

**Bước 3: Bật monitor**
```bash
sudo airmon-ng start wlan0
# → wlan0mon created
```

**Bước 4: Verify**
```bash
iwconfig wlan0mon | grep Mode
# → Mode:Monitor
```

**Bước 5: Test**
```bash
sudo airodump-ng wlan0mon
# → Nên thấy AP trong 5 giây
```

#### 4.3 Project Setup

```bash
cd ~
git clone <repo> wifi-security-monitor
cd wifi-security-monitor

# Venv
python3 -m venv .venv
source .venv/bin/activate

# Dependencies
pip install -r requirements.txt
```

#### 4.4 Cấu hình Whitelist

Tìm AP thật:
```bash
sudo airodump-ng wlan0mon | grep -i company
# AA:BB:CC:11:22:33  Company-WiFi   6  WPA2
```

Cập nhật config/whitelist.json:
```json
[{"ssid": "Company-WiFi", "bssid": "AA:BB:CC:11:22:33", "channel": 6, "encryption": "WPA2"}]
```

#### 4.5 Chạy Detection Engine

**Mode 1: CLI + Interactive**
```bash
sudo .venv/bin/python -m detector.main
# → Menu chọn AP target
```

**Mode 2: Web Dashboard**
```bash
sudo .venv/bin/uvicorn webapp.app:app --host 0.0.0.0 --port 8000
# → http://localhost:8000
```

**Mode 3: OpenSearch Export**
```bash
# config.yaml: opensearch.enabled = true
# Tool sẽ đẩy log lên http://localhost:9200
docker compose up -d
```

#### 4.6 Logging

**Format JSON:**
```json
{
  "timestamp": "2026-05-10T14:45:30Z",
  "event_type": "rogue_ap_detected",
  "ssid": "Company-WiFi",
  "legit_bssid": "AA:BB:CC:11:22:33",
  "detected_bssid": "66:77:88:99:AA:BB",
  "channel": 6,
  "rssi": -45,
  "severity": "high",
  "message": "SSID matches legitimate AP but BSSID is unknown"
}
```

**Output:**
- File: logs/wifi_alerts.jsonl (append mode)
- OpenSearch: POST http://localhost:9200/wifi-security-logs/_doc
- Telegram: sendMessage API

---

## PHẦN KIỂM THỬ

### Chương 5: Kiểm thử và đánh giá

#### 5.1 Kế hoạch kiểm thử

| TC | Tên | Phương pháp | Kết quả |
|----|-----|-----------|--------|
| TC01 | AP hợp lệ | Run 5 min, observe | PASS |
| TC02 | Rogue AP | Hotspot SSID trùng | PASS |
| TC03 | Evil Twin | Hotspot SSID tương tự + OPEN | PASS |
| TC04 | Deauth | aireplay-ng 25 frame | PASS |
| TC05 | No false positive | Traffic bình thường 10 min | PASS |
| TC06 | Log format | jq validate JSON | PASS |
| TC07 | Dashboard | OpenSearch visualize | PASS |

#### 5.2 Kết quả thực nghiệm

**TC01-TC07: 7/7 PASS** ✅

**Performance:**
- CPU: <5% (single core)
- RAM: 150MB
- Network: <1 Mbps
- Log write: <100 file ops/sec

#### 5.3 Ưu điểm hệ thống

1. **Phát hiện nhanh** - Realtime beacon analysis
2. **Ngoại lệ ít** - SSID matching + similarity check
3. **Log chi tiết** - JSON format, dễ parse
4. **Dashboard** - Web UI + OpenSearch
5. **Dễ deploy** - Docker Compose + pip
6. **Tunable** - Config file chỉnh threshold
7. **Multi-output** - File + OpenSearch + Telegram

#### 5.4 Hạn chế & cải thiện

| Hạn chế | Nguyên nhân | Cải thiện |
|--------|-----------|---------|
| Không định vị AP | Cần triangulation RSSI | Thêm multi-sensor |
| Fixed whitelist | Không dynamic | File monitoring |
| Monitor 1 channel | Adapter 1 interface | 2 adapter + channel hop |
| No auth (web UI) | Scope nhỏ | Add basic auth |
| No ML | Detection rule-based | Machine learning |

#### 5.5 Nhận xét chất lượng

- **Đáp ứng yêu cầu:** 100%
- **Tính ổn định:** 98% (corner case: hidden SSID)
- **Performance:** Excellent (CPU/RAM thấp)
- **Tính khả thi:** High (dễ triển khai)

---

## PHẦN KẾT LUẬN

### Chương 6: Kết luận & hướng phát triển

#### 6.1 Kết luận

- ✅ Hoàn thành xây dựng hệ thống phát hiện Rogue AP & Deauth Attack
- ✅ Tool hoạt động ổn định trong lab
- ✅ Log realtime, dashboard, cảnh báo
- ✅ Tài liệu đầy đủ, dễ vận hành
- ✅ Có giá trị thực tế cho enterprise Wi-Fi monitoring

#### 6.2 Hướng phát triển

**Ngắn hạn (1-3 tháng):**
1. Multi-channel scanning (hopping giữa các channel)
2. Persistent database (SQLite/PostgreSQL)
3. Web auth (JWT token)
4. Slack integration
5. Cloud export (AWS S3)

**Trung hạn (3-6 tháng):**
1. Machine Learning (anomaly detection)
2. Multiple sensor fusion (3+ adapters)
3. AP localization (RSSI-based)
4. 802.11w (Management Frame Protection) analysis
5. Threat intelligence feed integration

**Dài hạn (6-12 tháng):**
1. Hardware IDS (Raspberry Pi 4)
2. Distributed WIDS (multi-location)
3. AI-powered pattern recognition
4. Integration với Splunk/ELK
5. Mobile app (iOS/Android monitoring)

#### 6.3 Khác biệt so với công cụ hiện hành

| Công cụ | Rogue AP | Deauth | Log | Dashboard | Cost |
|---------|----------|--------|-----|-----------|------|
| **WiFi Monitor (tự làm)** | ✅ | ✅ | ✅ | ✅ | FREE |
| Kismet | ✅ (GUI) | ✅ | ✅ | Web | FREE |
| AirDefense | ✅✅ (Pro) | ✅✅ | ✅✅ | ✅✅ | $$$ |
| Fortinet (Fortiwifi) | ✅✅ | ✅ | ✅✅ | ✅✅ | $$$ |

---

## PHẦN PHỤ LỤC

### Phụ lục A: Hướng dẫn cài đặt chi tiết

Xem: [lab_steps.md](lab_steps.md)

### Phụ lục B: Test Case chi tiết

Xem: [test_cases.md](test_cases.md)

### Phụ lục C: Troubleshooting

Xem: [common_issues.md](common_issues.md)

### Phụ lục D: Ảnh minh chứng

- Lab setup
- Monitor mode enabled
- Rogue AP detected
- Dashboard screenshot
- Log file sample
- Telegram alert

### Phụ lục E: Mã nguồn

- [detector/main.py](../../detector/main.py)
- [detector/engine.py](../../detector/engine.py)
- [detector/rogue_ap_detector.py](../../detector/rogue_ap_detector.py)
- [detector/deauth_detector.py](../../detector/deauth_detector.py)
- [webapp/app.py](../../webapp/app.py)

---

## Tài liệu tham khảo

1. IEEE 802.11-2016 Standard
2. Scapy documentation
3. aircrack-ng documentation
4. OpenSearch documentation
5. OWASP Wireless Security Guide

---

## Ký duyệt & tiếp nhận

| Người | Ký | Ngày |
|------|----|----|
| Tác giả | ___ | ___ |
| Giáo viên hướng dẫn | ___ | ___ |
| Quản lý đề tài | ___ | ___ |
