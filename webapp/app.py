import json
import time
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

from detector.engine import MonitorRunner, scan_targets
from detector.utils import load_json, load_yaml

APP_TITLE = "WiFi Security Monitor"
CFG_PATH = "config/config.yaml"

app = FastAPI(title=APP_TITLE)
monitor = MonitorRunner(CFG_PATH)


def read_cfg():
    return load_yaml(CFG_PATH)


def read_whitelist(path):
    return load_json(path)


def write_whitelist(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=True)


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(
        """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>WiFi Security Monitor</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; margin-top: 10px; }
    th, td { border: 1px solid #ccc; padding: 6px; }
    .row { display: flex; gap: 12px; }
    .panel { flex: 1; }
    .log { background: #111; color: #0f0; padding: 8px; height: 220px; overflow: auto; }
    .filters { margin-top: 6px; display: flex; gap: 8px; }
    .filters input { flex: 1; padding: 6px; }
    .chart { border: 1px solid #ccc; margin-top: 8px; }
    button { padding: 6px 10px; }
  </style>
</head>
<body>
  <h2>WiFi Security Monitor</h2>
  <div class="row">
    <div class="panel">
      <h3>Scan AP</h3>
      <button onclick="scan()">Scan</button>
      <div class="filters">
        <input id="scanFilter" placeholder="Filter SSID/BSSID" oninput="renderScan()" />
      </div>
      <table id="scanTable">
        <thead><tr><th>#</th><th>SSID</th><th>BSSID</th><th>CH</th><th>ENC</th><th>RSSI</th><th>Action</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="panel">
      <h3>Whitelist</h3>
      <button onclick="loadWhitelist()">Reload</button>
      <div class="filters">
        <input id="wlFilter" placeholder="Filter SSID/BSSID" oninput="renderWhitelist()" />
      </div>
      <table id="wlTable">
        <thead><tr><th>SSID</th><th>BSSID</th><th>CH</th><th>ENC</th><th>Action</th></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

  <h3>Monitor</h3>
  <button onclick="startMonitor()">Start</button>
  <button onclick="stopMonitor()">Stop</button>
  <span id="status"></span>

  <h3>Realtime Chart</h3>
  <canvas id="chart" class="chart" width="800" height="220"></canvas>

  <h3>Live Logs</h3>
  <div class="log" id="logBox"></div>

<script>
let scanCache = [];
let whitelistCache = [];
const chartState = { bucketSize: 5, windowSeconds: 60, buckets: [] };

async function scan() {
  const res = await fetch('/api/scan');
  const data = await res.json();
  scanCache = data.items || [];
  renderScan();
}

function renderScan() {
  const filter = document.getElementById('scanFilter').value.toLowerCase().trim();
  const tbody = document.querySelector('#scanTable tbody');
  tbody.innerHTML = '';
  scanCache.forEach((item, idx) => {
    const key = `${item.ssid} ${item.bssid}`.toLowerCase();
    if (filter && !key.includes(filter)) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${idx+1}</td><td>${item.ssid}</td><td>${item.bssid}</td>
      <td>${item.channel}</td><td>${item.enc}</td><td>${item.rssi}</td>
      <td><button onclick="addToWhitelist(${idx})">Add</button>
          <button onclick="startTarget(${idx})">Target</button></td>`;
    tbody.appendChild(tr);
  });
}

async function loadWhitelist() {
  const res = await fetch('/api/whitelist');
  const data = await res.json();
  whitelistCache = data.items || [];
  renderWhitelist();
}

function renderWhitelist() {
  const filter = document.getElementById('wlFilter').value.toLowerCase().trim();
  const tbody = document.querySelector('#wlTable tbody');
  tbody.innerHTML = '';
  whitelistCache.forEach((item) => {
    const key = `${item.ssid} ${item.bssid}`.toLowerCase();
    if (filter && !key.includes(filter)) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>${item.ssid}</td><td>${item.bssid}</td><td>${item.channel}</td><td>${item.encryption}</td>
      <td>
        <button onclick="editWhitelist('${item.bssid}')">Edit</button>
        <button onclick="deleteWhitelist('${item.bssid}')">Delete</button>
      </td>`;
    tbody.appendChild(tr);
  });
}

async function addToWhitelist(idx) {
  const item = scanCache[idx];
  const body = { ssid: item.ssid, bssid: item.bssid, channel: item.channel, encryption: item.enc };
  await fetch('/api/whitelist', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  await loadWhitelist();
}

async function editWhitelist(bssid) {
  const ssid = prompt('SSID?');
  const channel = prompt('Channel?');
  const enc = prompt('Encryption?');
  if (!ssid) return;
  const body = { ssid: ssid, channel: parseInt(channel), encryption: enc || 'WPA2' };
  await fetch(`/api/whitelist/${bssid}`, { method: 'PUT', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body) });
  await loadWhitelist();
}

async function deleteWhitelist(bssid) {
  await fetch(`/api/whitelist/${bssid}`, { method: 'DELETE' });
  await loadWhitelist();
}

async function startMonitor() {
  await fetch('/api/monitor/start', { method: 'POST' });
  await refreshStatus();
}

async function startTarget(idx) {
  const item = scanCache[idx];
  await fetch('/api/monitor/start', { method: 'POST', headers: {'Content-Type':'application/json'},
    body: JSON.stringify({ bssid: item.bssid, channel: item.channel }) });
  await refreshStatus();
}

async function stopMonitor() {
  await fetch('/api/monitor/stop', { method: 'POST' });
  await refreshStatus();
}

async function refreshStatus() {
  const res = await fetch('/api/status');
  const data = await res.json();
  document.getElementById('status').innerText = data.running ? 'RUNNING' : 'STOPPED';
}

function connectLogs() {
  const logBox = document.getElementById('logBox');
  const evt = new EventSource('/api/logs/stream');
  evt.onmessage = (e) => {
    logBox.textContent += e.data + "\n";
    logBox.scrollTop = logBox.scrollHeight;
    try {
      const payload = JSON.parse(e.data);
      updateChart(payload);
    } catch (err) {
      // ignore non-JSON lines
    }
  };
}

function updateChart(payload) {
  const eventType = payload.event_type || "unknown";
  const ts = payload.timestamp ? Date.parse(payload.timestamp) / 1000 : Date.now() / 1000;
  const bucket = Math.floor(ts / chartState.bucketSize);
  const last = chartState.buckets[chartState.buckets.length - 1];

  if (!last || last.bucket !== bucket) {
    chartState.buckets.push({ bucket: bucket, rogue: 0, deauth: 0 });
  }

  const current = chartState.buckets[chartState.buckets.length - 1];
  if (eventType === "rogue_ap_detected" || eventType === "suspicious_open_ap") {
    current.rogue += 1;
  } else if (eventType === "deauth_attack_detected") {
    current.deauth += 1;
  }

  const maxBuckets = Math.ceil(chartState.windowSeconds / chartState.bucketSize);
  if (chartState.buckets.length > maxBuckets) {
    chartState.buckets = chartState.buckets.slice(-maxBuckets);
  }

  drawChart();
}

function drawChart() {
  const canvas = document.getElementById('chart');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const width = canvas.parentElement.clientWidth;
  if (width > 0 && canvas.width !== width) {
    canvas.width = width;
  }

  const height = canvas.height;
  ctx.clearRect(0, 0, canvas.width, height);

  const buckets = chartState.buckets;
  const maxCount = Math.max(1, ...buckets.map(b => Math.max(b.rogue, b.deauth)));
  const pad = 20;
  const w = canvas.width - pad * 2;
  const h = height - pad * 2;

  ctx.strokeStyle = '#999';
  ctx.beginPath();
  ctx.moveTo(pad, pad);
  ctx.lineTo(pad, pad + h);
  ctx.lineTo(pad + w, pad + h);
  ctx.stroke();

  function drawSeries(color, key) {
    ctx.strokeStyle = color;
    ctx.beginPath();
    buckets.forEach((b, i) => {
      const x = pad + (i / Math.max(1, buckets.length - 1)) * w;
      const y = pad + h - (b[key] / maxCount) * h;
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();
  }

  drawSeries('#d9534f', 'rogue');
  drawSeries('#f0ad4e', 'deauth');
}

loadWhitelist();
refreshStatus();
connectLogs();
window.addEventListener('resize', drawChart);
</script>
</body>
</html>
"""
    )


@app.get("/api/scan")
def api_scan():
    cfg = read_cfg()
    iface = cfg.get("interface", "wlan0mon")
    items = scan_targets(
        iface=iface,
        scan_seconds=cfg.get("scan_seconds", 8),
        max_results=cfg.get("scan_max_results", 20),
    )
    return {"items": items}


@app.get("/api/whitelist")
def api_whitelist():
    cfg = read_cfg()
    items = read_whitelist(cfg.get("whitelist_path", "config/whitelist.json"))
    return {"items": items}


@app.post("/api/whitelist")
def api_whitelist_add(payload=Body(...)):
    cfg = read_cfg()
    path = cfg.get("whitelist_path", "config/whitelist.json")
    items = read_whitelist(path)
    bssid = payload.get("bssid")
    if not bssid:
        raise HTTPException(status_code=400, detail="bssid required")

    items = [i for i in items if i.get("bssid", "").lower() != bssid.lower()]
    items.append(
        {
            "ssid": payload.get("ssid"),
            "bssid": bssid,
            "channel": payload.get("channel"),
            "encryption": payload.get("encryption", "WPA2"),
        }
    )
    write_whitelist(path, items)
    return {"ok": True}


@app.put("/api/whitelist/{bssid}")
def api_whitelist_edit(bssid: str, payload=Body(...)):
    cfg = read_cfg()
    path = cfg.get("whitelist_path", "config/whitelist.json")
    items = read_whitelist(path)
    found = False
    for item in items:
        if item.get("bssid", "").lower() == bssid.lower():
            item["ssid"] = payload.get("ssid", item.get("ssid"))
            item["channel"] = payload.get("channel", item.get("channel"))
            item["encryption"] = payload.get("encryption", item.get("encryption"))
            found = True
            break
    if not found:
        raise HTTPException(status_code=404, detail="bssid not found")
    write_whitelist(path, items)
    return {"ok": True}


@app.delete("/api/whitelist/{bssid}")
def api_whitelist_delete(bssid: str):
    cfg = read_cfg()
    path = cfg.get("whitelist_path", "config/whitelist.json")
    items = read_whitelist(path)
    items = [i for i in items if i.get("bssid", "").lower() != bssid.lower()]
    write_whitelist(path, items)
    return {"ok": True}


@app.post("/api/monitor/start")
def api_monitor_start(payload=Body(default={})):  # noqa: B008
    bssid = payload.get("bssid")
    channel = payload.get("channel")
    started = monitor.start(target_bssid=bssid, target_channel=channel)
    return {"started": started, **monitor.status()}


@app.post("/api/monitor/stop")
def api_monitor_stop():
    stopped = monitor.stop()
    return {"stopped": stopped, **monitor.status()}


@app.get("/api/status")
def api_status():
    return monitor.status()


@app.get("/api/logs/stream")
def api_logs_stream():
    cfg = read_cfg()
    path = cfg.get("log_path", "logs/wifi_alerts.jsonl")

    def event_stream():
        log_path = Path(path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        if not log_path.exists():
            log_path.touch()
        with open(log_path, "r", encoding="utf-8") as f:
            f.seek(0, 2)
            while True:
                line = f.readline()
                if line:
                    yield f"data: {line.strip()}\n\n"
                else:
                    time.sleep(1)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
