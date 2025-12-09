import sqlite3
import logging
import requests
import os
from pathlib import Path

logger = logging.getLogger(__name__)

try:
    from mac_vendor_lookup import MacLookup
except ImportError:
    MacLookup = None

# Default DB Path
DB_PATH = Path(os.path.expanduser("~")) / "mac_vendor_cache.db"

def set_db_path(path: Path):
    global DB_PATH
    DB_PATH = path

def _init_db():
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS mac_vendors (
                mac TEXT PRIMARY KEY,
                vendor TEXT
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"Could not initialize MAC vendor DB: {e}")

# Call init immediately on import (or lazy?)
_init_db()

def get_vendor(mac: str) -> str:
    """Get vendor for MAC address (Cached DB -> MacLookup -> API)"""
    if not mac:
        return None
        
    mac_clean = mac.upper().replace(":", "").replace("-", "").replace(".", "")
    
    # 1. Check DB
    try:
        conn = sqlite3.connect(str(DB_PATH))
        c = conn.cursor()
        c.execute("SELECT vendor FROM mac_vendors WHERE mac = ?", (mac_clean,))
        row = c.fetchone()
        conn.close()
        if row:
            return row[0]
    except Exception as e:
        pass

    # 2. Lookup
    vendor = None
    if MacLookup:
        try:
            mac_formatted = ":".join(mac_clean[i:i+2] for i in range(0, 12, 2))
            vendor = MacLookup().lookup(mac_formatted)
        except:
            pass
            
    # 3. API Fallback
    if not vendor:
        try:
            resp = requests.get(f"https://api.macvendors.com/{mac_clean}", timeout=3)
            if resp.status_code == 200:
                vendor = resp.text
        except:
            pass
            
    # Cache result (even if None/Failure? No, only hits)
    # Actually, we should cache None to avoid repeated API hits.
    # But for now, cache hits.
    
    if vendor:
        try:
            conn = sqlite3.connect(str(DB_PATH))
            c = conn.cursor()
            c.execute("INSERT OR REPLACE INTO mac_vendors (mac, vendor) VALUES (?, ?)", (mac_clean, vendor))
            conn.commit()
            conn.close()
        except:
            pass
            
    return vendor
