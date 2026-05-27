"""Tests for db_service."""
import sys
sys.path.insert(0, '/mnt/e/test/proj/myagent')

import pytest
import tempfile
from pathlib import Path

def test_db_service_init():
    """Test database initialization."""
    from src.agent.db_service import init_db, get_db_path
    
    db_path = Path(tempfile.gettempdir()) / 'test_metrics.db'
    if db_path.exists():
        db_path.unlink()
    
    # Patch DB_PATH temporarily
    import src.agent.db_service as db
    original = db.DB_PATH
    db.DB_PATH = db_path
    
    try:
        init_db()
        assert db_path.exists(), "Database should be created"
    finally:
        db.DB_PATH = original
        if db_path.exists():
            db_path.unlink()

def test_log_and_get_metrics():
    """Test logging and retrieving metrics."""
    from src.agent.db_service import init_db, log_metrics, get_recent_metrics
    import src.agent.db_service as db
    
    db_path = Path(tempfile.gettempdir()) / 'test_metrics2.db'
    if db_path.exists():
        db_path.unlink()
    
    original = db.DB_PATH
    db.DB_PATH = db_path
    
    try:
        init_db()
        log_metrics(response_time_ms=100.5, request_count=1)
        log_metrics(response_time_ms=200.0, request_count=2)
        
        metrics = get_recent_metrics(hours=24, limit=10)
        assert len(metrics) >= 2
        print(f"Got {len(metrics)} metrics")
    finally:
        db.DB_PATH = original
        if db_path.exists():
            db_path.unlink()

def test_feishu_conversations():
    """Test saving and retrieving Feishu conversations."""
    from src.agent.db_service import init_db, save_feishu_conversation, get_feishu_conversations
    import src.agent.db_service as db
    
    db_path = Path(tempfile.gettempdir()) / 'test_metrics3.db'
    if db_path.exists():
        db_path.unlink()
    
    original = db.DB_PATH
    db.DB_PATH = db_path
    
    try:
        init_db()
        save_feishu_conversation("session1", "你好", "你好！我是助手")
        save_feishu_conversation("session1", "今天天气", "晴天")
        
        convs = get_feishu_conversations(session_id="session1")
        assert len(convs) == 2
        print(f"Got {len(convs)} conversations")
    finally:
        db.DB_PATH = original
        if db_path.exists():
            db_path.unlink()

if __name__ == "__main__":
    test_db_service_init()
    test_log_and_get_metrics()
    test_feishu_conversations()
    print("All tests passed!")
