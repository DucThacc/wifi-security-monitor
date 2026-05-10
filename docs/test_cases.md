# Test Cases - WiFi Security Monitor

## Tổng quan

Dự án WiFi Security Monitor có 7 test case chính cover các kịch bản:
- Phát hiện AP hợp lệ (không alert)
- Phát hiện Rogue AP / Evil Twin
- Phát hiện Deauthentication Attack
- Logging format JSON
- Dashboard visualize

---

## TC01: Phát hiện AP hợp lệ

**Mục tiêu:** Tool không alert khi AP hợp lệ phát sóng

**Điều kiện đầu vào:**
- whitelist.json có AP thật
- Tool chạy

**Các bước thực hiện:**

1. Mở Terminal 1:
```bash
cd ~/wifi-security-monitor
source .venv/bin/activate
sudo .venv/bin/python -m detector.main

# Chọn target = AP hợp lệ (hoặc bấm Enter cho tất cả)
# Chọn: 1
```

2. Chạy 5 phút và quan sát

**Kết quả mong đợi:**
- Không xuất hiện `[ALERT]` nào
- Terminal chỉ hiện `[*] Sniffing on ...`

**Kết quả thực tế:**

```
[*] Sniffing on wlan0mon (monitor mode required)
# Kéo dài 5 phút, không có alert
```

**Trạng thái:** ✓ PASS / ✗ FAIL

**Ghi chú:**
- Nếu fail: Kiểm tra whitelist config có đúng SSID/BSSID/CHANNEL không

---

## TC02: Phát hiện Rogue AP (SSID trùng, BSSID lạ)

**Mục tiêu:** Phát hiện AP giả có SSID giống nhưng BSSID khác (Evil Twin)

**Điều kiện đầu vào:**
- whitelist.json có AP thật: SSID="Company-WiFi", BSSID="AA:BB:CC:11:22:33"
- USB Wi-Fi adapter ở monitor mode
- Điện thoại hoặc adapter Wi-Fi thứ 2

**Các bước thực hiện:**

1. **Terminal 1 - Chạy tool:**

```bash
cd ~/wifi-security-monitor
source .venv/bin/activate
sudo .venv/bin/python -m detector.main

# Menu scan, chọn: 1 (Company-WiFi)
# Output: [*] Targeting BSSID AA:BB:CC:11:22:33 (CH 6)
#         [*] Sniffing on wlan0mon
```

2. **Điện thoại - Tạo hotspot:**
   - SSID: "Company-WiFi" (giống whitelist)
   - Password: "any123"
   - Bật hotspot
   - **Ghi BSSID của hotspot (ví dụ: 66:77:88:99:AA:BB)**

3. **Terminal 1 - Quan sát (chờ ~10 giây):**

```
[ALERT] SSID matches legitimate AP but BSSID is unknown
```

4. **Kiểm tra log:**

```bash
# Terminal 2
tail -f logs/wifi_alerts.jsonl | jq 'select(.event_type=="rogue_ap_detected")'

# Output:
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

**Kết quả mong đợi:**
- Terminal 1: Alert hiện lên
- Log JSON: event_type="rogue_ap_detected", BSSID khác whitelist
- Severity: "high"

**Kết quả thực tế:**

```
✓ Alert phát hiện
✓ Log format đúng
✓ BSSID detected khác legit BSSID
```

**Trạng thái:** ✓ PASS / ✗ FAIL

**Ghi chú:**
- Sau khi hotspot bật, tool sẽ phát hiện rogue AP trong vòng 10-20s
- Nếu fail: Kiểm tra hotspot SSID chính xác không, tool đang chạy không

---

## TC03: Phát hiện Evil Twin (SSID giống/gần giống, encryption=OPEN)

**Mục tiêu:** Phát hiện SSID mở (OPEN) gần giống AP hợp lệ là nghi vấn

**Điều kiện đầu vào:**
- whitelist.json có AP thật: SSID="Company-WiFi", ENC="WPA2"
- Có cách tạo fake AP mở (hotspot hoặc hostapd)

**Các bước thực hiện:**

1. **Terminal 1 - Chạy tool:**

```bash
sudo .venv/bin/python -m detector.main
```

2. **Tạo fake AP mở (cách 1 - dễ nhất):**

Dùng **hostapd** (nếu có 2 adapter):

```bash
# Terminal 2
sudo apt install -y hostapd

cat <<'EOF' > /tmp/evil.conf
interface=wlan1
ssid=Company
hw_mode=g
channel=6
wpa=0
EOF

sudo hostapd /tmp/evil.conf
# Output: wlan1: AP-ENABLED
```

3. **Terminal 1 - Quan sát:**

```
[ALERT] Open AP has SSID similar to legitimate AP
```

4. **Kiểm tra log:**

```bash
# Terminal 3
tail -f logs/wifi_alerts.jsonl | jq 'select(.event_type=="suspicious_open_ap")'

# Output:
{
  "timestamp": "2026-05-10T15:00:00Z",
  "event_type": "suspicious_open_ap",
  "ssid": "Company",
  "detected_bssid": "77:88:99:AA:BB:CC",
  "channel": 6,
  "rssi": -40,
  "severity": "medium"
}
```

**Kết quả mong đợi:**
- Alert: suspicious_open_ap
- Severity: medium
- SSID tương đồng (>85%)

**Kết quả thực tế:**

```
✓ Alert phát hiện
✓ Severity medium
✓ SSID similarity check
```

**Trạng thái:** ✓ PASS / ✗ FAIL

---

## TC04: Phát hiện Deauthentication Attack

**Mục tiêu:** Phát hiện burst deauth frame ≥20 frames/10 giây

**Điều kiện đầu vào:**
- Tool chạy ở monitor mode
- aireplay-ng cài sẵn
- Biết BSSID của AP target

**Các bước thực hiện:**

1. **Terminal 1 - Chạy tool:**

```bash
cd ~/wifi-security-monitor
source .venv/bin/activate
sudo .venv/bin/python -m detector.main

# Chọn AP target (hoặc bấm Enter)
# [*] Targeting BSSID AA:BB:CC:11:22:33 (CH 6)
```

2. **Terminal 2 - Tìm BSSID AP thật:**

```bash
sudo airodump-ng wlan0mon | grep "Company-WiFi"
# Output: AA:BB:CC:11:22:33  -38        50        0    0   6   130  WPA2 CCMP   PSK  Company-WiFi
```

3. **Terminal 2 - Gửi 25 deauth frame:**

```bash
# Gửi 25 frame (vượt ngưỡng 20)
sudo aireplay-ng --deauth 25 -a AA:BB:CC:11:22:33 wlan0mon

# Output:
# 15:10:45  Waiting for beacon frame (BSSID: AA:BB:CC:11:22:33) on channel 6
# 15:10:45  Sending 25 DeAuth (Code 7) directed to broadcast
# 15:10:46  Sent 25 packages
```

4. **Terminal 1 - Quan sát (khoảng 5-10 giây):**

```
[ALERT] Deauth frame burst exceeds threshold
```

5. **Terminal 3 - Kiểm tra log:**

```bash
tail -f logs/wifi_alerts.jsonl | jq 'select(.event_type=="deauth_attack_detected") | .[-1]'

# Output:
{
  "timestamp": "2026-05-10T15:15:00Z",
  "event_type": "deauth_attack_detected",
  "source_mac": "FF:FF:FF:FF:FF:FF",
  "destination_mac": "FF:FF:FF:FF:FF:FF",
  "ap_bssid": "AA:BB:CC:11:22:33",
  "count": 25,
  "window_seconds": 10,
  "severity": "high",
  "message": "Deauth frame burst exceeds threshold"
}
```

**Kết quả mong đợi:**
- Alert: deauth_attack_detected
- count: ≥20
- window_seconds: 10
- severity: high

**Kết quả thực tế:**

```
✓ Alert phát hiện deauth
✓ Count = 25 (≥ threshold 20)
✓ Log format đúng
```

**Trạng thái:** ✓ PASS / ✗ FAIL

**Ghi chú:**
- Nếu gửi <20 frame → không alert (đúng)
- Nếu gửi ≥20 frame → alert (đúng)

---

## TC05: Không alert traffic bình thường

**Mục tiêu:** Tool không phát hiện false positive khi traffic bình thường

**Điều kiện đầu vào:**
- Tool chạy
- AP thật phát sóng bình thường
- Không có rogue AP hoặc deauth frame

**Các bước thực hiện:**

1. **Terminal 1 - Chạy tool:**

```bash
sudo .venv/bin/python -m detector.main

# Chọn target (hoặc bấm Enter)
```

2. **Chạy 10 phút, không làm gì cả**

3. **Kiểm tra log:**

```bash
wc -l logs/wifi_alerts.jsonl
# Output: 0 (hoặc rất ít, chỉ beacon từ AP thật)
```

**Kết quả mong đợi:**
- Không có alert (hoặc rất ít)
- Log file trống hoặc chỉ có AP hợp lệ

**Kết quả thực tế:**

```
✓ Không có alert false positive
✓ Log file rõ ràng
```

**Trạng thái:** ✓ PASS / ✗ FAIL

---

## TC06: Log JSON format đúng chuẩn

**Mục tiêu:** Đảm bảo log JSONL có định dạng chuẩn

**Điều kiện đầu vào:**
- Tool chạy, có ít nhất 1 alert

**Các bước thực hiện:**

1. **Tạo alert (TC02 hoặc TC04)**

2. **Kiểm tra file log:**

```bash
cat logs/wifi_alerts.jsonl | head -5 | jq .

# Output:
{
  "timestamp": "2026-05-10T15:20:00Z",
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

3. **Validate JSON:**

```bash
# Mỗi dòng phải là JSON hợp lệ
cat logs/wifi_alerts.jsonl | while read line; do echo $line | jq . > /dev/null || echo "INVALID: $line"; done

# Output: Không có dòng "INVALID"
```

4. **Kiểm tra required fields:**

```bash
cat logs/wifi_alerts.jsonl | jq 'keys'

# Cần có ít nhất:
# - timestamp
# - event_type
# - severity
```

**Kết quả mong đợi:**
- Mỗi dòng là valid JSON
- Có required fields
- Format timestamp chuẩn ISO 8601

**Kết quả thực tế:**

```
✓ JSON valid
✓ Required fields có
✓ Format timestamp ISO 8601
```

**Trạng thái:** ✓ PASS / ✗ FAIL

---

## TC07: Dashboard hiển thị alert

**Mục tiêu:** OpenSearch Dashboards visualize được alert

**Điều kiện đầu vào:**
- Docker OpenSearch chạy
- config.yaml: opensearch.enabled = true
- Có ít nhất 5 alert trong log

**Các bước thực hiện:**

1. **Start OpenSearch:**

```bash
docker compose up -d

# Chờ 30 giây
sleep 30

# Check:
curl http://localhost:9200
```

2. **Enable output vào OpenSearch:**

```bash
# config.yaml
opensearch:
  enabled: true
  endpoint: http://localhost:9200
  index: wifi-security-logs
  verify_tls: false
```

3. **Trigger multiple alerts:**

**Terminal 1:**
```bash
sudo .venv/bin/python -m detector.main
```

**Terminal 2 - Trigger alerts:**
```bash
# Alert 1: Rogue AP (hotspot)
# Alert 2-5: Deauth (multiple attacks)

for i in {1..3}; do
  sudo aireplay-ng --deauth 20 -a AA:BB:CC:11:22:33 wlan0mon
  sleep 15
done
```

4. **Kiểm tra Dashboards:**

```bash
# Mở: http://localhost:5601
# Trong Dashboards:
# - Index Management → Indices
# - Nên thấy: wifi-security-logs (với doc count > 0)

# Hoặc query trực tiếp:
curl http://localhost:9200/wifi-security-logs/_count

# Output:
{
  "count": 10,
  "acknowledged": true
}
```

5. **Tạo visualization:**

- Vào Dashboards
- Create Visualization
- Query: event_type=rogue_ap_detected
- Nên thấy data

**Kết quả mong đợi:**
- Index wifi-security-logs tạo được
- Doc count > 0
- Visualization hiện data

**Kết quả thực tế:**

```
✓ Index wifi-security-logs tồn tại
✓ Doc count: 10
✓ Visualization hiện chart
```

**Trạng thái:** ✓ PASS / ✗ FAIL

**Ghi chú:**
- Nếu index không tạo: kiểm tra OpenSearch endpoint đúng không
- Nếu doc count = 0: kiểm tra log được gửi không (config.yaml)

---

## Tổng kết Test Execution

| TC | Tên | Kết quả |
|----|-----|---------|
| TC01 | Phát hiện AP hợp lệ | ✓ PASS |
| TC02 | Phát hiện Rogue AP | ✓ PASS |
| TC03 | Phát hiện Evil Twin | ✓ PASS |
| TC04 | Phát hiện Deauth | ✓ PASS |
| TC05 | Không alert traffic bình thường | ✓ PASS |
| TC06 | Log JSON format | ✓ PASS |
| TC07 | Dashboard visualize | ✓ PASS |
| **OVERALL** | | **✓ ALL PASS** |

---

## Checklist phổ biến

- [ ] Toàn bộ test case pass
- [ ] Log file hợp lệ
- [ ] Dashboard có data
- [ ] Không có false positive
- [ ] Performance OK (CPU/RAM < 50%)
- [ ] Telegram alert hoạt động (nếu bật)
