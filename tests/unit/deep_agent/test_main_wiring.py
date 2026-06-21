"""装配测试 —— 验证 main 已注册 deep 路由且未破坏现有路由。"""
from src.main import app


def test_deep_routes_registered():
    paths = {r.path for r in app.routes}
    assert "/api/v1/deep/chat" in paths
    assert "/api/v1/deep/chat/stream" in paths


def test_existing_chat_routes_still_present():
    paths = {r.path for r in app.routes}
    # 现有路由必须仍在,证明并存未受影响
    assert "/api/v1/chat" in paths
    assert "/api/v1/chat/stream" in paths
