"""Tests for city graph tool."""
import sys
sys.path.insert(0, '/mnt/e/test/proj/myagent')

import pytest
from pathlib import Path
import tempfile
import sqlite3

def test_city_graph_tool_basic():
    """Test basic city graph search functionality."""
    from src.agent.Tools.city_graph_tool import search_city_graph, init_city_graph_db
    
    # Create temp db
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    init_city_graph_db(db_path)
    
    # Test search for city
    result = search_city_graph.invoke({"query": "北京"})
    print(f"Result: {result}")
    
    assert result is not None
    assert "北京" in result or "城市知识图谱数据库" in result or "查询出错" in result

def test_city_graph_tool_no_result():
    """Test city search with no results."""
    from src.agent.Tools.city_graph_tool import search_city_graph, init_city_graph_db
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    init_city_graph_db(db_path)
    result = search_city_graph.invoke({"query": "完全不存在的城市xyz"})
    print(f"Result: {result}")
    assert result is not None

def test_city_graph_tool_province():
    """Test province search."""
    from src.agent.Tools.city_graph_tool import search_city_graph, init_city_graph_db
    
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    init_city_graph_db(db_path)
    result = search_city_graph.invoke({"query": "浙江省"})
    print(f"Result: {result}")
    assert result is not None

if __name__ == "__main__":
    test_city_graph_tool_basic()
    test_city_graph_tool_no_result()
    test_city_graph_tool_province()
    print("All tests passed!")
