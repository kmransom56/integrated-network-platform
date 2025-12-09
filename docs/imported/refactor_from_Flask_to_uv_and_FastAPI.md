I would like to refactor to use uv and fastapi
Diagrams: Flowcharts & Mindmaps said:

Beautiful — that’s a great direction 🎯

Switching from a manual polling script + serve_d3_live.py to a FastAPI + uv (modern Python runtime) stack will make your system:
✅ event-driven,
✅ production-ready, and
✅ API-compatible with your D3.js dashboard.

Let’s build this cleanly and modularly.

🚀 Refactored Architecture Overview

You’ll end up with this layout:

/home/keith/network-d3js/
├── app/
│   ├── __init__.py
│   ├── main.py                 ← FastAPI app entry point
│   ├── routes/
│   │   ├── live.py             ← Live topology endpoints
│   ├── services/
│   │   ├── fortigate.py        ← API fetch + caching logic
│   ├── utils/
│   │   ├── paths.py            ← Centralized paths
│   └── templates/
│       └── index.html          ← Your D3.js dashboard
├── data/
│   └── live_network.json
├── icons/
│   └── icons_manifest.json
├── uv.lock
├── pyproject.toml
└── README.md

🧩 Step 1. Create FastAPI project

If you haven’t already:

uv init network-d3js-fastapi
cd network-d3js-fastapi
uv add fastapi uvicorn[standard] aiofiles httpx python-multipart


This will bootstrap your pyproject.toml with uv’s dependency manager.

🧱 Step 2. Add the FastAPI App

app/main.py

from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import asyncio

from app.services.fortigate import update_live_data_if_needed
from app.utils.paths import DATA_DIR, STATIC_DIR

app = FastAPI(title="FortiGate Network Topology API")

# Serve static assets (your D3 dashboard and icons)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/icons", StaticFiles(directory=Path("/home/keith/network-d3js/icons")), name="icons")

@app.get("/")
async def index():
    """Serve the main D3 dashboard."""
    index_path = STATIC_DIR / "index.html"
    return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

@app.get("/api/live")
async def get_live_data(background_tasks: BackgroundTasks):
    """Return live network topology JSON (auto-refresh if stale)."""
    data_path = DATA_DIR / "live_network.json"
    background_tasks.add_task(update_live_data_if_needed)
    if data_path.exists():
        return FileResponse(data_path, media_type="application/json")
    else:
        return JSONResponse({"error": "No live data yet."}, status_code=404)

@app.get("/health")
async def health():
    """Simple health check endpoint."""
    return {"status": "ok"}

🧰 Step 3. FortiGate Fetch + Cache Logic

app/services/fortigate.py

import asyncio
import json
import httpx
from datetime import datetime, timedelta
from pathlib import Path
from app.utils.paths import DATA_DIR, BASE_DIR

FORTIGATE_URL = "https://192.168.0.254:10443"
API_TOKEN = "YOUR_FORTIGATE_TOKEN_HERE"
CACHE_FILE = DATA_DIR / "live_network.json"
STALE_AFTER = timedelta(minutes=5)

HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

async def fetch_fortigate_data() -> dict:
    """Fetch from multiple FortiGate endpoints and merge results."""
    async with httpx.AsyncClient(verify=False, timeout=10) as client:
        endpoints = [
            "/api/v2/monitor/user/device/query",
            "/api/v2/monitor/router/arp",
            "/api/v2/cmdb/system/interface",
        ]
        responses = []
        for ep in endpoints:
            try:
                r = await client.get(f"{FORTIGATE_URL}{ep}", headers=HEADERS)
                if r.status_code == 200:
                    responses.append(r.json())
            except Exception as e:
                print(f"[!] Failed to fetch {ep}: {e}")

    nodes, links = [], []
    for resp in responses:
        if isinstance(resp, dict) and "results" in resp:
            for entry in resp["results"]:
                node = {
                    "id": entry.get("mac", entry.get("ip")),
                    "ip": entry.get("ip"),
                    "mac": entry.get("mac"),
                    "hostname": entry.get("hostname", "Unknown"),
                    "interface": entry.get("interface", ""),
                    "vendor": "fortinet",
                    "type": "device"
                }
                if node["id"]:
                    nodes.append(node)
    # Deduplicate
    seen = {}
    for n in nodes:
        if n["id"] not in seen:
            seen[n["id"]] = n
        else:
            seen[n["id"]].update({k: v for k, v in n.items() if v})
    nodes = list(seen.values())

    # Basic link generation (placeholder)
    links = [{"source": "FortiGate", "target": n["id"], "status": "up"} for n in nodes]

    return {"timestamp": datetime.now().isoformat(), "nodes": nodes, "links": links}

async def update_live_data_if_needed():
    """Refresh the cache file if missing or stale."""
    if not CACHE_FILE.exists() or is_stale(CACHE_FILE):
        print("[⚡] Fetching new FortiGate data...")
        data = await fetch_fortigate_data()
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(data, indent=2))
        print("[✅] live_network.json updated.")
    else:
        print("[⏳] Using cached data.")

def is_stale(path: Path) -> bool:
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    return datetime.now() - mtime > STALE_AFTER

🧩 Step 4. Paths Helper

app/utils/paths.py

from pathlib import Path

BASE_DIR = Path("/home/keith/network-d3js")
DATA_DIR = BASE_DIR / "data"
STATIC_DIR = BASE_DIR / "static"

🖼 Step 5. Keep Your D3 index.html

Move your latest index.html to:

/home/keith/network-d3js/static/index.html


Change the JSON fetch call to:

d3.json("/api/live")


instead of "data/live_network.json"

✅ Now it dynamically pulls from FastAPI.

🏃 Step 6. Run the Server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 12600