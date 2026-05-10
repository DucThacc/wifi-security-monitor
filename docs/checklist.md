# Completion Checklist - Hệ thống giám sát WiFi Security

Danh sách kiểm tra để hoàn thành đề tài 14 ngày.

---

## PHẦN 1: Chuẩn bị môi trường (Ngày 1-2)

- [ ] OS (Kali/Ubuntu) cài xong
- [ ] System update: `apt update && apt upgrade`
- [ ] aircrack-ng cài: `apt install aircrack-ng`
- [ ] iw, wireless-tools cài
- [ ] Python 3 (≥3.9) cài sẵn
- [ ] pip & venv hoạt động
- [ ] Docker & docker-compose cài xong
- [ ] USB Wi-Fi adapter nhận diện: `lsusb`
- [ ] Interface hiển thị: `ip link | grep wlan`
- [ ] iw detect monitor support: `iw list | grep monitor`
- [ ] Monitor mode bật thành công: `iwconfig | grep Monitor`
- [ ] airodump-ng thấy AP (≥1): `airodump-ng wlan0mon`

**Kết quả:** ✅ Monitor mode hoạt động

---

## PHẦN 2: Project Setup (Ngày 3-4)

- [ ] Git clone/download project
- [ ] Folder structure tạo đúng
- [ ] Python venv tạo: `python3 -m venv .venv`
- [ ] Venv activate: `source .venv/bin/activate`
- [ ] requirements.txt cài: `pip install -r requirements.txt`
- [ ] Scapy import OK: `python -c "import scapy"`
- [ ] PyYAML import OK: `python -c "import yaml"`
- [ ] FastAPI import OK: `python -c "import fastapi"`
- [ ] Folder config/ tồn tại
- [ ] File config/whitelist.json tồn tại
- [ ] File config/config.yaml tồn tại
- [ ] Folder logs/ tồn tại (hoặc tự tạo)
- [ ] Folder detector/ có main.py, engine.py, etc.
- [ ] Folder webapp/ có app.py

**Kết quả:** ✅ Project structure OK

---

## PHẦN 3: Cấu hình & Whitelist (Ngày 4-5)

- [ ] Tìm BSSID AP thật: `airodump-ng wlan0mon`
- [ ] Ghi lại SSID, BSSID, CHANNEL, ENCRYPTION
- [ ] Chỉnh config/whitelist.json:
  - [ ] SSID đúng
  - [ ] BSSID đúng (6 octet hex)
  - [ ] CHANNEL đúng (1-14 cho 2.4GHz)
  - [ ] ENCRYPTION = "WPA2" (hoặc đúng loại)
- [ ] Chỉnh config/config.yaml:
  - [ ] interface = "wlan0mon" (hoặc interface thực tế)
  - [ ] whitelist_path = "config/whitelist.json"
  - [ ] log_path = "logs/wifi_alerts.jsonl"
  - [ ] interactive_scan = true
  - [ ] scan_seconds = 8
  - [ ] threshold_deauth = 20
  - [ ] window_seconds = 10
  - [ ] opensearch.enabled = false (tạm)
  - [ ] telegram.enabled = false (tạm)

**Kết quả:** ✅ Config file hợp lệ

---

## PHẦN 4: Detect Rogue AP (Ngày 5-6)

- [ ] Run tool: `sudo .venv/bin/python -m detector.main`
- [ ] Tool chạy không lỗi
- [ ] Menu scan hiện & chọn được AP
- [ ] Chọn AP thật, không có alert 5 phút
- [ ] Tạo hotspot điện thoại SSID="Company-WiFi"
- [ ] Bật hotspot & quan sát tool
- [ ] Alert "[ALERT] SSID matches..." xuất hiện
- [ ] Kiểm tra log: `tail logs/wifi_alerts.jsonl`
- [ ] Log JSON format đúng
- [ ] JSON có field: event_type, ssid, bssid, severity
- [ ] Severity = "high"
- [ ] Tắt hotspot, alert không tiếp tục

**Kết quả:** ✅ Rogue AP detection OK

---

## PHẦN 5: Detect Deauth Attack (Ngày 7-8)

- [ ] Tool chạy, chọn AP target
- [ ] Terminal khác: `sudo aireplay-ng --deauth 20 -a <BSSID> wlan0mon`
- [ ] Gửi ≥20 deauth frame
- [ ] Alert "[ALERT] Deauth frame burst..." xuất hiện trong 10s
- [ ] Kiểm tra log: `tail logs/wifi_alerts.jsonl`
- [ ] Event type = "deauth_attack_detected"
- [ ] Field "count" = ≥20
- [ ] Field "window_seconds" = 10
- [ ] Severity = "high"
- [ ] Gửi <20 frame → không alert (đúng)

**Kết quả:** ✅ Deauth detection OK

---

## PHẦN 6: Logging & Format (Ngày 9)

- [ ] Log file tạo: `logs/wifi_alerts.jsonl`
- [ ] File có >0 dòng (alerts)
- [ ] Mỗi dòng là valid JSON: `cat logs/wifi_alerts.jsonl | jq .`
- [ ] Không có "parse error"
- [ ] Có required fields:
  - [ ] timestamp (ISO 8601 format)
  - [ ] event_type (rogue_ap_detected, deauth_attack_detected, etc.)
  - [ ] severity (high, medium, low)
  - [ ] message (string description)
- [ ] Timestamp format: "2026-05-10T14:45:30Z"
- [ ] JSON line terminator: \n (LF)
- [ ] No trailing comma in JSON

**Kết quả:** ✅ Logging format OK

---

## PHẦN 7: OpenSearch Dashboard (Ngày 8-10)

- [ ] Docker cài xong
- [ ] docker-compose.yml tồn tại
- [ ] Chạy: `docker compose up -d`
- [ ] Chờ 30 giây
- [ ] Docker container chạy: `docker ps`
  - [ ] opensearch container UP
  - [ ] opensearch-dashboards container UP
- [ ] OpenSearch accessible: `curl http://localhost:9200`
- [ ] Dashboards accessible: http://localhost:5601
- [ ] Chỉnh config.yaml: opensearch.enabled = true
- [ ] Chỉnh endpoint: http://localhost:9200
- [ ] Chạy tool, trigger alerts
- [ ] Index tạo: `curl http://localhost:9200/_cat/indices`
  - [ ] wifi-security-logs index tồn tại
  - [ ] Doc count > 0
- [ ] Dashboards hiển thị data

**Kết quả:** ✅ OpenSearch + Dashboards hoạt động

---

## PHẦN 8: Web Dashboard (Ngày 9-11)

- [ ] Run: `sudo .venv/bin/uvicorn webapp.app:app --host 0.0.0.0 --port 8000`
- [ ] Mở http://localhost:8000
- [ ] Scan button hoạt động
- [ ] Whitelist table hiển thị
- [ ] Whitelist add/edit/delete OK
- [ ] Monitor start/stop button OK
- [ ] Live logs stream realtime
- [ ] Chart update realtime (khi có alert)
- [ ] No console error/warning

**Kết quả:** ✅ Web dashboard hoạt động

---

## PHẦN 9: Telegram Alert (Ngày 10-11) [Optional]

- [ ] Tạo Telegram bot: @BotFather → /newbot
- [ ] Lấy bot token: 123:ABCDefg...
- [ ] Lấy chat ID từ getUpdates API
- [ ] Chỉnh config.yaml:
  - [ ] telegram.enabled = true
  - [ ] telegram.bot_token = "..."
  - [ ] telegram.chat_id = "..."
- [ ] Chạy tool, trigger alert
- [ ] Telegram nhận message
- [ ] Message có event_type & severity

**Kết quả:** ✅ Telegram alert hoạt động (optional)

---

## PHẦN 10: Documentation (Ngày 12)

- [ ] README.md cập nhật:
  - [ ] Tổng quan đề tài
  - [ ] Kiến trúc hệ thống
  - [ ] Chuẩn bị môi trường (step by step)
  - [ ] Cài đặt project
  - [ ] Chạy tool (CLI, Web, OpenSearch)
  - [ ] Kiểm thử (rogue AP, deauth)
  - [ ] Tích hợp OpenSearch
  - [ ] Cảnh báo Telegram
  - [ ] Xử lý lỗi
  - [ ] Cảnh báo pháp lý
- [ ] lab_steps.md cập nhật (14 ngày chi tiết)
- [ ] test_cases.md cập nhật (7 TC đầy đủ)
- [ ] report_outline.md tạo (dàn ý báo cáo)
- [ ] common_issues.md tạo/update
- [ ] log_format.md tạo
- [ ] Photo_list.md tạo (ảnh cần chụp)

**Kết quả:** ✅ Documentation đầy đủ

---

## PHẦN 11: Test Cases Execution (Ngày 12)

- [ ] TC01: AP hợp lệ - không alert
- [ ] TC02: Rogue AP (hotspot) - alert
- [ ] TC03: Evil Twin (hostapd open) - alert
- [ ] TC04: Deauth attack - alert
- [ ] TC05: Normal traffic - no alert
- [ ] TC06: Log JSON format - valid
- [ ] TC07: Dashboard visualize - show data

**Kết quả:** ✅ 7/7 test case PASS

---

## PHẦN 12: Report Writing (Ngày 13)

- [ ] Chương 1: Tổng quan đề tài
- [ ] Chương 2: Cơ sở lý thuyết
- [ ] Chương 3: Thiết kế hệ thống
- [ ] Chương 4: Triển khai hệ thống
- [ ] Chương 5: Kiểm thử & đánh giá
- [ ] Chương 6: Kết luận & hướng phát triển
- [ ] Phụ lục A: Cài đặt chi tiết
- [ ] Phụ lục B: Test case
- [ ] Phụ lục C: Troubleshooting
- [ ] Phụ lục D: Screenshots
- [ ] Phụ lục E: Source code
- [ ] Tài liệu tham khảo (≥5 nguồn)
- [ ] Ký duyệt (nếu cần)

**Kết quả:** ✅ Report hoàn chỉnh

---

## PHẦN 13: Demo & Presentation (Ngày 14)

- [ ] Screenshots:
  - [ ] Lab setup (adapter, monitor mode)
  - [ ] airodump-ng thấy AP
  - [ ] whitelist.json config
  - [ ] Tool chạy bình thường
  - [ ] Rogue AP detection
  - [ ] Deauth attack detection
  - [ ] Log JSON file
  - [ ] OpenSearch dashboard
  - [ ] Web dashboard
  - [ ] Telegram alert
- [ ] Video demo (5-10 phút):
  - [ ] Monitor mode bật
  - [ ] Tool scan AP
  - [ ] Rogue AP triggered
  - [ ] Deauth triggered
  - [ ] Log & dashboard
- [ ] Slide presentation:
  - [ ] Title slide
  - [ ] Problem statement
  - [ ] Architecture diagram
  - [ ] Key findings
  - [ ] Demo highlight
  - [ ] Conclusions

**Kết quả:** ✅ Demo & presentation sẵn sàng

---

## PHẦN 14: Final Check

- [ ] Source code clean (no temp files)
- [ ] requirements.txt updated
- [ ] config.yaml example clean
- [ ] whitelist.json sample valid
- [ ] No hardcoded passwords/tokens
- [ ] All test case pass
- [ ] Documentation readable
- [ ] Screenshot/video quality good
- [ ] Report spell-checked
- [ ] Backup on USB/Cloud

**Kết quả:** ✅ Project ready for submission

---

## Progress Timeline

| Ngày | Công việc | Status | % |
|------|----------|--------|---|
| 1-2 | Environment | ✅ | 100 |
| 3-4 | Setup & Config | ✅ | 100 |
| 5-6 | Rogue AP detect | ✅ | 100 |
| 7-8 | Deauth detect | ✅ | 100 |
| 9 | Logging | ✅ | 100 |
| 10-11 | Dashboard & Telegram | ✅ | 100 |
| 12 | Documentation | ✅ | 100 |
| 13 | Report | ✅ | 100 |
| 14 | Demo | ✅ | 100 |

---

## Notes

- Mỗi ngày ghi lại progress
- Backup code/config thường xuyên
- Chụp ảnh/video step-by-step
- Keep terminal history: `history > log-history.txt`
- Test nhiều lần trước submit

---

## Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Developer | __________ | __________ | ____ |
| Reviewer | __________ | __________ | ____ |
| Supervisor | __________ | __________ | ____ |
