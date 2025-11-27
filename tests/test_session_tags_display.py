#!/usr/bin/env python3
"""
会话标签系统显示功能自动化测试 v3.6.0
"""

import requests
import json
import sys
from typing import Dict, Any

# 配置
API_BASE = "http://localhost:8000"
ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZ2VudF9pZCI6ImFnZW50XzE3NjM5NzM2MDM2MzIiLCJ1c2VybmFtZSI6ImFkbWluIiwicm9sZSI6ImFkbWluIiwiaWF0IjoxNzY0MTMxMDgzLjczNjY5MjIsImV4cCI6MTc2NDEzNDY4My43MzY2OTIyfQ.UxRoX0BOw1NC8TlimLJCsOaLsMQU9A_7C-_7yruuR6Q"

# 测试统计
passed = 0
failed = 0
total = 0

def test_case(name: str, actual: Any, expected: Any) -> bool:
    """测试用例"""
    global passed, failed, total
    total += 1

    print(f"测试 {total}: {name} ... ", end="")

    if actual == expected:
        print("✅ 通过")
        passed += 1
        return True
    else:
        print("❌ 失败")
        print(f"  预期: {expected}")
        print(f"  实际: {actual}")
        failed += 1
        return False

def api_get(path: str) -> Dict[str, Any]:
    """API GET 请求"""
    try:
        response = requests.get(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"❌ API请求失败: {e}")
        return {"success": False, "error": str(e)}

def api_post(path: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """API POST 请求"""
    try:
        response = requests.post(
            f"{API_BASE}{path}",
            headers={
                "Authorization": f"Bearer {ADMIN_TOKEN}",
                "Content-Type": "application/json"
            },
            json=data,
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"❌ API请求失败: {e}")
        return {"success": False, "error": str(e)}

def api_delete(path: str) -> Dict[str, Any]:
    """API DELETE 请求"""
    try:
        response = requests.delete(
            f"{API_BASE}{path}",
            headers={"Authorization": f"Bearer {ADMIN_TOKEN}"},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"❌ API请求失败: {e}")
        return {"success": False, "error": str(e)}

print("🧪 会话标签系统显示功能自动化测试")
print("=" * 50)
print()

# 测试1: 统计数据显示
print("📊 测试1: 统计数据显示")
print("=" * 50)

stats = api_get("/api/sessions/stats")
test_case("获取会话统计", stats.get("success"), True)
test_case("待接入数量统计", stats.get("data", {}).get("by_status", {}).get("pending_manual"), 4)
test_case("服务中数量统计", stats.get("data", {}).get("by_status", {}).get("manual_live"), 1)

print()

# 测试2: 标签显示数据
print("🏷️  测试2: 标签显示数据")
print("=" * 50)

tags = api_get("/api/tags")
test_case("获取标签列表", tags.get("success"), True)

system_tags = tags.get("data", {}).get("system_tags", [])
test_case("系统标签数量", len(system_tags), 6)

vip_tag = next((t for t in system_tags if t["id"] == "tag_vip"), None)
test_case("VIP标签存在", vip_tag is not None and vip_tag["name"] == "VIP", True)

urgent_tag = next((t for t in system_tags if t["id"] == "tag_urgent"), None)
test_case("紧急标签存在", urgent_tag is not None and urgent_tag["name"] == "紧急", True)

print()

# 测试3: 会话列表标签显示
print("📋 测试3: 会话列表标签显示")
print("=" * 50)

sessions = api_get("/api/sessions?limit=50")
test_case("获取所有会话", sessions.get("success"), True)

session_list = sessions.get("data", {}).get("sessions", [])

zhangsan = next((s for s in session_list if s["session_name"] == "vip_customer_张三_001"), None)
test_case("张三会话存在", zhangsan is not None, True)
if zhangsan:
    test_case("张三会话标签", "tag_vip" in zhangsan.get("tags", []), True)

lisi = next((s for s in session_list if s["session_name"] == "urgent_issue_李四_002"), None)
if lisi:
    test_case("李四会话多标签", len(lisi.get("tags", [])), 2)
    test_case("李四包含紧急标签", "tag_urgent" in lisi.get("tags", []), True)
    test_case("李四包含技术标签", "tag_technical" in lisi.get("tags", []), True)

wangwu = next((s for s in session_list if s["session_name"] == "refund_request_王五_003"), None)
if wangwu:
    test_case("王五会话标签", "tag_refund" in wangwu.get("tags", []), True)

qianqi = next((s for s in session_list if s["session_name"] == "battery_problem_钱七_005"), None)
if qianqi:
    test_case("钱七会话VIP标签", "tag_vip" in qianqi.get("tags", []), True)
    test_case("钱七会话技术标签", "tag_technical" in qianqi.get("tags", []), True)

print()

# 测试4: 按状态筛选会话
print("🔍 测试4: 按状态筛选会话")
print("=" * 50)

pending_sessions = api_get("/api/sessions?status=pending_manual&limit=50")
test_case("筛选待接入会话成功", pending_sessions.get("success"), True)
test_case("待接入会话数量", len(pending_sessions.get("data", {}).get("sessions", [])) >= 4, True)

live_sessions = api_get("/api/sessions?status=manual_live&limit=50")
test_case("筛选服务中会话成功", live_sessions.get("success"), True)
test_case("服务中会话数量", len(live_sessions.get("data", {}).get("sessions", [])) >= 1, True)

print()

# 测试5: 按标签筛选会话
print("🏷️  测试5: 按标签筛选会话")
print("=" * 50)

vip_sessions = api_get("/api/sessions/by-tag/tag_vip?limit=10")
test_case("筛选VIP标签会话成功", vip_sessions.get("success"), True)
test_case("VIP标签会话数量", len(vip_sessions.get("data", {}).get("sessions", [])) >= 2, True)

tech_sessions = api_get("/api/sessions/by-tag/tag_technical?limit=10")
test_case("筛选技术标签会话成功", tech_sessions.get("success"), True)
test_case("技术标签会话数量", len(tech_sessions.get("data", {}).get("sessions", [])) >= 2, True)

urgent_sessions = api_get("/api/sessions/by-tag/tag_urgent?limit=10")
test_case("筛选紧急标签会话成功", urgent_sessions.get("success"), True)
test_case("紧急标签会话数量", len(urgent_sessions.get("data", {}).get("sessions", [])) >= 1, True)

print()

# 测试6: 标签颜色和图标
print("🎨 测试6: 标签颜色和图标")
print("=" * 50)

if vip_tag:
    test_case("VIP标签颜色", vip_tag.get("color"), "#F59E0B")
    test_case("VIP标签图标", vip_tag.get("icon"), "🟡")

if urgent_tag:
    test_case("紧急标签颜色", urgent_tag.get("color"), "#EF4444")
    test_case("紧急标签图标", urgent_tag.get("icon"), "🔴")

tech_tag = next((t for t in system_tags if t["id"] == "tag_technical"), None)
if tech_tag:
    test_case("技术标签颜色", tech_tag.get("color"), "#3B82F6")
    test_case("技术标签图标", tech_tag.get("icon"), "🔵")

print()

# 测试7: 标签管理操作
print("🔄 测试7: 标签管理操作")
print("=" * 50)

# 创建自定义标签
custom_tag_response = api_post("/api/tags", {
    "name": "测试标签",
    "color": "#10B981",
    "icon": "🧪",
    "description": "自动化测试标签"
})

test_case("创建自定义标签", custom_tag_response.get("success"), True)

if custom_tag_response.get("success"):
    custom_tag_id = custom_tag_response.get("data", {}).get("tag", {}).get("id")
    test_case("自定义标签ID生成", custom_tag_id and custom_tag_id.startswith("tag_custom_"), True)

    # 添加标签到会话
    add_tag_response = api_post("/api/sessions/vip_customer_张三_001/tags", {"tag_id": custom_tag_id})
    test_case("添加标签到会话", add_tag_response.get("success"), True)

    # 验证标签已添加
    zhangsan_updated = api_get("/api/sessions?limit=50")
    if zhangsan_updated.get("success"):
        sessions_updated = zhangsan_updated.get("data", {}).get("sessions", [])
        zhangsan_session = next((s for s in sessions_updated if s["session_name"] == "vip_customer_张三_001"), None)
        if zhangsan_session:
            test_case("验证标签已添加", custom_tag_id in zhangsan_session.get("tags", []), True)

    # 移除标签
    remove_tag_response = api_delete(f"/api/sessions/vip_customer_张三_001/tags/{custom_tag_id}")
    test_case("移除会话标签", remove_tag_response.get("success"), True)

print()

# 测试结果汇总
print("=" * 50)
print("📊 测试结果汇总")
print("=" * 50)
print(f"总测试数: {total}")
print(f"✅ 通过: {passed}")
print(f"❌ 失败: {failed}")
print()

if failed == 0:
    print("✅ 所有测试通过！")
    sys.exit(0)
else:
    print(f"❌ 有 {failed} 个测试失败")
    sys.exit(1)
