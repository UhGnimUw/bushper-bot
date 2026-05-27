"""Tests for web API endpoints."""
import sys
sys.path.insert(0, '/mnt/e/test/proj/myagent')

import pytest
from fastapi.testclient import TestClient
import tempfile
from pathlib import Path

@pytest.fixture
def client():
    """Create test client."""
    # Patch metrics db path
    import src.agent.db_service as db
    db_path = Path(tempfile.gettempdir()) / 'test_web_api.db'
    if db_path.exists():
        db_path.unlink()
    original = db.DB_PATH
    db.DB_PATH = db_path
    
    from web_server import app
    with TestClient(app) as c:
        yield c
    
    db.DB_PATH = original

def test_chat_endpoint(client):
    """Test /chat endpoint."""
    response = client.post("/chat", json={"message": "你好"})
    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "session_id" in data
    print(f"Chat response: {data['response'][:100]}")

def test_monitor_stats_endpoint(client):
    """Test /api/monitor/stats endpoint."""
    response = client.get("/api/monitor/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "summary" in data
    print(f"Monitor stats: {data['summary']}")

def test_monitor_recent_endpoint(client):
    """Test /api/monitor/recent endpoint."""
    response = client.get("/api/monitor/recent?hours=24&limit=50")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "metrics" in data
    print(f"Got {len(data['metrics'])} metric entries")

def test_feishu_sessions_endpoint(client):
    """Test /api/feishu/sessions endpoint."""
    response = client.get("/api/feishu/sessions")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "sessions" in data
    print(f"Got {len(data['sessions'])} sessions")

def test_feishu_conversations_endpoint(client):
    """Test /api/feishu/conversations endpoint."""
    response = client.get("/api/feishu/conversations")
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] == True
    assert "conversations" in data

def test_clear_endpoint(client):
    """Test /clear/{session_id} endpoint."""
    # First create a session
    response = client.post("/chat", json={"message": "测试"})
    session_id = response.json()["session_id"]
    
    # Then clear it
    response = client.delete(f"/clear/{session_id}")
    assert response.status_code == 200
    assert response.json()["ok"] == True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
