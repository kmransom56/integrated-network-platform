import pytest
from fastapi.testclient import TestClient
from api.main import create_application

# Initialize app for testing
app = create_application()
client = TestClient(app)

def test_read_root():
    """Test the landing page serves HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Integrated Network Platform" in response.text
    assert "Interactive Map" in response.text

def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "services" in data

def test_static_files_ui():
    """Test that UI D3 assets are accessible"""
    response = client.get("/ui/")
    # It might return index.html or 404 if directory listing is off and no index.html
    # But /ui is mounted with html=True so it should serve index.html if present
    # The default D3 index.html was copied to /ui/index.html
    assert response.status_code == 200

def test_visualization_renderers():
    """Test renderer options endpoint"""
    response = client.get("/api/v1/visualization/renderers")
    assert response.status_code == 200
    data = response.json()
    assert "three.js" in [r["name"] for r in data["renderers"]]

def test_config_status():
    """Test config status endpoint"""
    response = client.get("/config/status")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "features" in data
