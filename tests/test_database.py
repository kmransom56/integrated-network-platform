import pytest
import sqlite3
import os
from unittest.mock import patch, MagicMock
# We import the internal functions to test them directly
# Since they are private/module-level in meraki_visualizer, we verify logic through exposed methods or by importing them.
# The module handles DB init at module level, so we must be careful not to overwrite the real DB.

from shared.visualization import meraki_visualizer

@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary database path"""
    db_path = tmp_path / "test_mac_vendor.db"
    
    # Patch the global MAC_VENDOR_DB_PATH in the module
    with patch("shared.visualization.meraki_visualizer.MAC_VENDOR_DB_PATH", db_path):
        # We must re-init the DB on the new path
        meraki_visualizer._init_mac_vendor_db()
        yield db_path

def test_db_init(temp_db):
    """Test database creation"""
    assert temp_db.exists()
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    # Check table existence
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='mac_vendors';")
    assert c.fetchone() is not None
    conn.close()

def test_db_read_write(temp_db):
    """Test reading and writing vendors"""
    mac = "001122334455"
    vendor = "Test Vendor Inc."
    
    # Write
    meraki_visualizer._set_vendor_in_db(mac, vendor)
    
    # Read
    conn = sqlite3.connect(str(temp_db))
    c = conn.cursor()
    c.execute("SELECT vendor FROM mac_vendors WHERE mac=?", (mac,))
    result = c.fetchone()
    conn.close()
    
    assert result is not None
    assert result[0] == vendor
    
    # Verify module getter
    retrieved = meraki_visualizer._get_vendor_from_db(mac)
    assert retrieved == vendor

def test_db_persistence(temp_db):
    """Test data persists across connections"""
    mac = "AABBCCDDEEFF"
    
    meraki_visualizer._set_vendor_in_db(mac, "Persist Vendor")
    
    # "Restart" app (new connection in getter)
    val = meraki_visualizer._get_vendor_from_db(mac)
    assert val == "Persist Vendor"
