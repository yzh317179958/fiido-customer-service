#!/usr/bin/env python3
"""
坐席认证系统测试

测试内容:
- 坐席登录（成功/失败）
- Token 生成和验证
- 坐席信息查询
- Token 刷新
- 密码加密验证

运行方式:
python3 tests/test_agent_auth.py
"""

import requests
import json
import time
from typing import Dict, Optional

# 测试配置
BASE_URL = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# ANSI 颜色代码
GREEN = '\033[0;32m'
RED = '\033[0;31m'
YELLOW = '\033[0;33m'
BLUE = '\033[0;34m'
RESET = '\033[0m'

# 测试统计
total_tests = 0
passed_tests = 0
failed_tests = 0


def print_test_header(test_name: str):
    """打印测试标题"""
    global total_tests
    total_tests += 1
    print(f"\n{BLUE}{'=' * 60}")
    print(f"测试 {total_tests}: {test_name}")
    print(f"{'=' * 60}{RESET}\n")


def print_success(message: str):
    """打印成功消息"""
    global passed_tests
    passed_tests += 1
    print(f"{GREEN}✅ {message}{RESET}")


def print_error(message: str):
    """打印错误消息"""
    global failed_tests
    failed_tests += 1
    print(f"{RED}❌ {message}{RESET}")


def print_info(message: str):
    """打印信息"""
    print(f"   {message}")


def login_and_get_token(username: str = "admin", password: str = "admin123") -> Optional[str]:
    """登录并返回访问 Token"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": username,
                "password": password
            }
        )
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("token")
    except Exception as exc:
        print_error(f"获取 Token 失败: {exc}")
    return None


def test_admin_login():
    """测试管理员登录"""
    print_test_header("管理员登录")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": "admin",
                "password": "admin123"
            }
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success") and data.get("token") and data.get("refresh_token"):
                print_success("管理员登录成功")
                print_info(f"用户名: {data['agent']['username']}")
                print_info(f"角色: {data['agent']['role']}")
                print_info(f"Token 长度: {len(data['token'])} 字符")
                print_info(f"过期时间: {data['expires_in']} 秒")
                return data
            else:
                print_error("登录响应格式错误")
                return None
        else:
            print_error(f"登录失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return None


def test_agent_login():
    """测试普通坐席登录"""
    print_test_header("普通坐席登录")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": "agent001",
                "password": "agent123"
            }
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success") and data.get("token"):
                print_success("坐席登录成功")
                print_info(f"用户名: {data['agent']['username']}")
                print_info(f"姓名: {data['agent']['name']}")
                print_info(f"角色: {data['agent']['role']}")
                print_info(f"最大会话数: {data['agent']['max_sessions']}")
                return data
            else:
                print_error("登录响应格式错误")
                return None
        else:
            print_error(f"登录失败，状态码: {response.status_code}")
            return None

    except Exception as e:
        print_error(f"登录异常: {str(e)}")
        return None


def test_invalid_password():
    """测试错误密码登录"""
    print_test_header("错误密码登录（应该失败）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": "admin",
                "password": "wrongpassword"
            }
        )

        if response.status_code == 401:
            print_success("正确拒绝了错误密码")
            print_info(f"错误信息: {response.json().get('detail')}")
        else:
            print_error(f"应该返回 401，但返回了 {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_invalid_username():
    """测试不存在的用户名"""
    print_test_header("不存在的用户名（应该失败）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        if response.status_code == 401:
            print_success("正确拒绝了不存在的用户")
            print_info(f"错误信息: {response.json().get('detail')}")
        else:
            print_error(f"应该返回 401，但返回了 {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_get_profile():
    """测试获取坐席信息"""
    print_test_header("获取坐席信息")

    try:
        response = requests.get(
            f"{BASE_URL}/api/agent/profile",
            headers=HEADERS,
            params={"username": "admin"}
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success") and data.get("agent"):
                agent = data["agent"]
                print_success("成功获取坐席信息")
                print_info(f"ID: {agent['id']}")
                print_info(f"用户名: {agent['username']}")
                print_info(f"姓名: {agent['name']}")
                print_info(f"角色: {agent['role']}")
                print_info(f"状态: {agent['status']}")

                # 验证密码哈希不在响应中
                if "password_hash" not in agent:
                    print_success("密码哈希已正确隐藏")
                else:
                    print_error("密码哈希不应该出现在响应中！")
            else:
                print_error("响应格式错误")
        else:
            print_error(f"请求失败，状态码: {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_get_nonexistent_profile():
    """测试获取不存在的坐席信息"""
    print_test_header("获取不存在的坐席信息（应该失败）")

    try:
        response = requests.get(
            f"{BASE_URL}/api/agent/profile",
            headers=HEADERS,
            params={"username": "nonexistent"}
        )

        if response.status_code == 404:
            print_success("正确返回 404")
            print_info(f"错误信息: {response.json().get('detail')}")
        else:
            print_error(f"应该返回 404，但返回了 {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_agent_status_api():
    """测试坐席状态管理接口"""
    print_test_header("坐席状态管理")

    token = login_and_get_token()
    if not token:
        print_error("无法获取 Token，跳过坐席状态测试")
        return

    auth_headers = {
        "Authorization": f"Bearer {token}"
    }
    json_headers = {
        **auth_headers,
        "Content-Type": "application/json"
    }

    try:
        # 获取当前状态
        response = requests.get(
            f"{BASE_URL}/api/agent/status",
            headers=auth_headers
        )
        if response.status_code != 200 or not response.json().get("success"):
            print_error("获取坐席状态失败")
            return

        data = response.json()["data"]
        required_fields = ["status", "status_note", "current_sessions", "today_stats"]
        if all(field in data for field in required_fields):
            print_success("成功获取坐席状态")
        else:
            print_error("坐席状态返回字段不完整")
            return

        # 更新状态为 break
        update = requests.put(
            f"{BASE_URL}/api/agent/status",
            headers=json_headers,
            json={
                "status": "break",
                "status_note": "测试小休"
            }
        )
        if update.status_code == 200 and update.json().get("success"):
            updated_data = update.json()["data"]
            if updated_data["status"] == "break":
                print_success("坐席状态更新成功")
            else:
                print_error("坐席状态更新未生效")
        else:
            print_error("坐席状态更新失败")
            return

        # 心跳上报
        heartbeat = requests.post(
            f"{BASE_URL}/api/agent/status/heartbeat",
            headers=auth_headers
        )
        if heartbeat.status_code == 200 and heartbeat.json().get("success"):
            print_success("坐席心跳上报成功")
        else:
            print_error("坐席心跳上报失败")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")
    finally:
        # 恢复为在线状态
        requests.put(
            f"{BASE_URL}/api/agent/status",
            headers=json_headers,
            json={
                "status": "online",
                "status_note": ""
            }
        )


def test_agent_today_stats():
    """测试坐席今日统计接口"""
    print_test_header("坐席今日统计")

    token = login_and_get_token()
    if not token:
        print_error("无法获取 Token，跳过统计测试")
        return

    headers = {
        "Authorization": f"Bearer {token}"
    }

    try:
        response = requests.get(
            f"{BASE_URL}/api/agent/stats/today",
            headers=headers
        )

        if response.status_code == 200 and response.json().get("success"):
            data = response.json()["data"]
            expected_fields = {"processed_count", "avg_response_time", "avg_duration", "satisfaction_score"}
            if expected_fields.issubset(set(data.keys())):
                print_success("成功获取坐席今日统计")
                print_info(f"当前会话: {data.get('current_sessions', 0)}")
                print_info(f"今日已处理: {data['processed_count']}")
            else:
                print_error("坐席今日统计返回字段缺失")
        else:
            print_error("坐席今日统计接口请求失败")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_token_refresh():
    """测试 Token 刷新"""
    print_test_header("Token 刷新")

    try:
        # 先登录获取刷新 Token
        login_response = requests.post(
            f"{BASE_URL}/api/agent/login",
            headers=HEADERS,
            json={
                "username": "admin",
                "password": "admin123"
            }
        )

        if login_response.status_code != 200:
            print_error("登录失败，无法测试 Token 刷新")
            return

        refresh_token = login_response.json()["refresh_token"]
        print_info(f"获取到刷新 Token (长度: {len(refresh_token)})")

        # 刷新 Token
        refresh_response = requests.post(
            f"{BASE_URL}/api/agent/refresh",
            headers=HEADERS,
            json={"refresh_token": refresh_token}
        )

        if refresh_response.status_code == 200:
            data = refresh_response.json()

            if data.get("success") and data.get("token"):
                print_success("Token 刷新成功")
                print_info(f"新 Token 长度: {len(data['token'])}")
                print_info(f"过期时间: {data['expires_in']} 秒")
            else:
                print_error("刷新响应格式错误")
        else:
            print_error(f"刷新失败，状态码: {refresh_response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_invalid_refresh_token():
    """测试无效的刷新 Token"""
    print_test_header("无效的刷新 Token（应该失败）")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/refresh",
            headers=HEADERS,
            json={"refresh_token": "invalid_token_123456"}
        )

        if response.status_code == 401:
            print_success("正确拒绝了无效的刷新 Token")
            print_info(f"错误信息: {response.json().get('detail')}")
        else:
            print_error(f"应该返回 401，但返回了 {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_logout():
    """测试坐席登出"""
    print_test_header("坐席登出")

    try:
        response = requests.post(
            f"{BASE_URL}/api/agent/logout",
            headers=HEADERS,
            params={"username": "admin"}
        )

        if response.status_code == 200:
            data = response.json()

            if data.get("success"):
                print_success("登出成功")
                print_info(f"消息: {data.get('message')}")
            else:
                print_error("登出响应格式错误")
        else:
            print_error(f"登出失败，状态码: {response.status_code}")

    except Exception as e:
        print_error(f"测试异常: {str(e)}")


def test_all_default_accounts():
    """测试所有默认账号"""
    print_test_header("测试所有默认账号")

    accounts = [
        {"username": "admin", "password": "admin123", "role": "admin"},
        {"username": "agent001", "password": "agent123", "role": "agent"},
        {"username": "agent002", "password": "agent123", "role": "agent"}
    ]

    success_count = 0

    for account in accounts:
        try:
            response = requests.post(
                f"{BASE_URL}/api/agent/login",
                headers=HEADERS,
                json={
                    "username": account["username"],
                    "password": account["password"]
                }
            )

            if response.status_code == 200:
                data = response.json()
                if data["agent"]["role"] == account["role"]:
                    print_info(f"✓ {account['username']} ({account['role']}) - 登录成功")
                    success_count += 1
                else:
                    print_error(f"✗ {account['username']} - 角色不匹配")
            else:
                print_error(f"✗ {account['username']} - 登录失败")

        except Exception as e:
            print_error(f"✗ {account['username']} - 异常: {str(e)}")

    if success_count == len(accounts):
        print_success(f"所有 {len(accounts)} 个默认账号都可以正常登录")
    else:
        print_error(f"只有 {success_count}/{len(accounts)} 个账号可以登录")


def print_summary():
    """打印测试总结"""
    print(f"\n{BLUE}{'=' * 60}")
    print("            测试结果汇总")
    print(f"{'=' * 60}{RESET}\n")

    print(f"通过: {GREEN}{passed_tests}{RESET}")
    print(f"失败: {RED}{failed_tests}{RESET}")
    print(f"总计: {total_tests}\n")

    if failed_tests == 0:
        print(f"{GREEN}{'=' * 60}")
        print("          所有测试通过！")
        print(f"{'=' * 60}{RESET}\n")
        return 0
    else:
        print(f"{RED}{'=' * 60}")
        print("        存在失败的测试！请修复后再继续")
        print(f"{'=' * 60}{RESET}\n")
        return 1


def main():
    """主测试流程"""
    print(f"\n{BLUE}{'=' * 60}")
    print("      Fiido AI客服 - 坐席认证系统测试")
    print(f"{'=' * 60}{RESET}\n")

    # 检查后端是否运行
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=5)
        if response.status_code != 200:
            print_error("后端未运行，请先启动 backend.py")
            return 1
    except Exception:
        print_error("无法连接到后端，请先启动 backend.py")
        return 1

    print_info(f"✓ 后端服务运行正常 ({BASE_URL})\n")

    # 执行所有测试
    test_admin_login()
    test_agent_login()
    test_invalid_password()
    test_invalid_username()
    test_get_profile()
    test_get_nonexistent_profile()
    test_agent_status_api()
    test_agent_today_stats()
    test_token_refresh()
    test_invalid_refresh_token()
    test_logout()
    test_all_default_accounts()

    # 打印总结
    return print_summary()


if __name__ == "__main__":
    exit(main())
