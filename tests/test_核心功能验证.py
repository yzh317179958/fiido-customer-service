"""
核心功能全面验证测试
验证项目：
1. Coze API 核心对话功能
2. 会话隔离机制
3. 人工接管完整流程
4. 技术约束遵守情况
"""

import requests
import json
import time
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"


def print_section(title: str, icon: str = "📋"):
    """打印分隔线"""
    print(f"\n{'=' * 70}")
    print(f"{icon} {title}")
    print(f"{'=' * 70}\n")


def print_result(step: str, success: bool, details: str = ""):
    """打印测试结果"""
    status_icon = "✅" if success else "❌"
    print(f"{status_icon} {step}")
    if details:
        print(f"   {details}")


class CoreFunctionalityTester:
    """核心功能测试器"""

    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results = {
            "coze_api": [],
            "session_isolation": [],
            "manual_takeover": [],
            "constraints": []
        }

    def test_coze_api_basic(self) -> bool:
        """测试 Coze API 基础对话功能"""
        print_section("1. Coze API 核心对话功能测试", "🤖")

        test_cases = [
            {
                "name": "同步对话接口",
                "endpoint": "/api/chat",
                "method": "POST",
                "body": {
                    "message": "你好，请介绍一下你自己",
                    "user_id": f"test_coze_{int(time.time())}"
                }
            },
            {
                "name": "流式对话接口",
                "endpoint": "/api/chat/stream",
                "method": "POST",
                "body": {
                    "message": "1+1等于几？",
                    "user_id": f"test_stream_{int(time.time())}"
                },
                "is_stream": True
            }
        ]

        all_passed = True

        for test in test_cases:
            try:
                if test.get("is_stream"):
                    # 流式接口测试
                    resp = requests.post(
                        f"{self.base_url}{test['endpoint']}",
                        json=test['body'],
                        stream=True,
                        timeout=30
                    )

                    if resp.status_code == 200:
                        # 读取 SSE 流
                        received_data = False
                        for line in resp.iter_lines():
                            if line:
                                line_str = line.decode('utf-8')
                                if line_str.startswith('data: '):
                                    received_data = True
                                    try:
                                        data = json.loads(line_str[6:])
                                        if data.get('type') == 'message':
                                            print_result(test['name'], True, f"收到流式响应: {data.get('content', '')[:50]}...")
                                            self.test_results['coze_api'].append((test['name'], True))
                                            break
                                    except json.JSONDecodeError:
                                        pass

                        if not received_data:
                            print_result(test['name'], False, "未收到有效的 SSE 数据")
                            self.test_results['coze_api'].append((test['name'], False))
                            all_passed = False
                    else:
                        print_result(test['name'], False, f"HTTP {resp.status_code}")
                        self.test_results['coze_api'].append((test['name'], False))
                        all_passed = False
                else:
                    # 同步接口测试
                    resp = requests.post(
                        f"{self.base_url}{test['endpoint']}",
                        json=test['body'],
                        timeout=30
                    )

                    if resp.status_code == 200:
                        data = resp.json()
                        if data.get('success') and data.get('message'):
                            print_result(test['name'], True, f"响应: {data['message'][:50]}...")
                            self.test_results['coze_api'].append((test['name'], True))
                        else:
                            print_result(test['name'], False, f"响应格式错误: {data}")
                            self.test_results['coze_api'].append((test['name'], False))
                            all_passed = False
                    else:
                        print_result(test['name'], False, f"HTTP {resp.status_code}")
                        self.test_results['coze_api'].append((test['name'], False))
                        all_passed = False

            except requests.exceptions.Timeout:
                print_result(test['name'], False, "请求超时（可能 Coze API 未配置）")
                self.test_results['coze_api'].append((test['name'], False))
                all_passed = False
            except Exception as e:
                print_result(test['name'], False, f"异常: {str(e)}")
                self.test_results['coze_api'].append((test['name'], False))
                all_passed = False

        return all_passed

    def test_session_isolation(self) -> bool:
        """测试会话隔离机制"""
        print_section("2. 会话隔离机制验证", "🔒")

        session_a = f"session_a_{int(time.time())}"
        session_b = f"session_b_{int(time.time())}"

        try:
            # 关键：为每个 session 创建独立的 conversation_id
            print("🔄 为 Session A 创建独立的 conversation")
            resp_conv_a = requests.post(
                f"{self.base_url}/api/conversation/new",
                json={"session_id": session_a},
                timeout=10
            )

            if resp_conv_a.status_code != 200:
                print_result("Session A 创建 conversation", False, f"HTTP {resp_conv_a.status_code}")
                self.test_results['session_isolation'].append(("创建 conversation", False))
                return False

            conv_data_a = resp_conv_a.json()
            conversation_id_a = conv_data_a.get('conversation_id')
            print(f"✅ Session A conversation_id: {conversation_id_a}")

            print("🔄 为 Session B 创建独立的 conversation")
            resp_conv_b = requests.post(
                f"{self.base_url}/api/conversation/new",
                json={"session_id": session_b},
                timeout=10
            )

            if resp_conv_b.status_code != 200:
                print_result("Session B 创建 conversation", False, f"HTTP {resp_conv_b.status_code}")
                self.test_results['session_isolation'].append(("创建 conversation", False))
                return False

            conv_data_b = resp_conv_b.json()
            conversation_id_b = conv_data_b.get('conversation_id')
            print(f"✅ Session B conversation_id: {conversation_id_b}")

            # 验证：两个 conversation_id 必须不同
            if conversation_id_a == conversation_id_b:
                print_result("Conversation ID 唯一性", False, "❌ 两个 session 的 conversation_id 相同！")
                self.test_results['session_isolation'].append(("Conversation 唯一性", False))
                return False
            else:
                print_result("Conversation ID 唯一性", True, "✅ 两个 session 的 conversation_id 不同")

            time.sleep(1)

            # Session A: 发送消息 "我是张三"（使用 conversation_id_a）
            print("\n📝 Session A: 发送 '我是张三'")
            resp_a1 = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "记住，我是张三",
                    "user_id": session_a,
                    "conversation_id": conversation_id_a
                },
                timeout=30
            )

            if resp_a1.status_code != 200:
                print_result("Session A 首次对话", False, f"HTTP {resp_a1.status_code}")
                self.test_results['session_isolation'].append(("Session A 首次对话", False))
                return False

            time.sleep(1)

            # Session B: 询问 "我是谁"（使用 conversation_id_b）
            print("📝 Session B: 询问 '我是谁'")
            resp_b1 = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "我是谁？",
                    "user_id": session_b,
                    "conversation_id": conversation_id_b
                },
                timeout=30
            )

            if resp_b1.status_code != 200:
                print_result("Session B 询问身份", False, f"HTTP {resp_b1.status_code}")
                self.test_results['session_isolation'].append(("Session B 询问身份", False))
                return False

            data_b = resp_b1.json()
            response_b = data_b.get('message', '').lower()

            # 验证：Session B 不应该知道张三
            if '张三' in response_b:
                print_result("会话隔离测试", False, f"❌ 会话隔离失败！Session B 知道了 Session A 的信息: {response_b}")
                self.test_results['session_isolation'].append(("会话隔离", False))
                return False
            else:
                print_result("会话隔离测试", True, f"✅ Session B 正确地不知道张三: {response_b[:80]}...")
                self.test_results['session_isolation'].append(("会话隔离", True))

            # Session A: 再次询问确认记忆（使用 conversation_id_a）
            print("📝 Session A: 再次询问 '我是谁'")
            resp_a2 = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "message": "我是谁？",
                    "user_id": session_a,
                    "conversation_id": conversation_id_a
                },
                timeout=30
            )

            if resp_a2.status_code == 200:
                data_a = resp_a2.json()
                response_a = data_a.get('message', '')

                if '张三' in response_a:
                    print_result("会话记忆保持", True, f"✅ Session A 正确记住了身份: {response_a[:80]}...")
                    self.test_results['session_isolation'].append(("会话记忆", True))
                else:
                    print_result("会话记忆保持", False, f"⚠️  Session A 未能记住身份: {response_a[:80]}...")
                    self.test_results['session_isolation'].append(("会话记忆", False))
                    return False

            return True

        except requests.exceptions.Timeout:
            print_result("会话隔离测试", False, "请求超时")
            self.test_results['session_isolation'].append(("会话隔离", False))
            return False
        except Exception as e:
            print_result("会话隔离测试", False, f"异常: {str(e)}")
            self.test_results['session_isolation'].append(("会话隔离", False))
            return False

    def test_manual_takeover_workflow(self) -> bool:
        """测试人工接管完整流程"""
        print_section("3. 人工接管完整流程验证", "👥")

        session_name = f"manual_test_{int(time.time())}"

        try:
            # 步骤1: AI 正常对话
            print("📝 步骤1: AI 正常对话")
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": "你好", "user_id": session_name},
                timeout=30
            )
            if resp.status_code == 200:
                print_result("AI 正常对话", True)
                self.test_results['manual_takeover'].append(("AI 正常对话", True))
            else:
                print_result("AI 正常对话", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("AI 正常对话", False))
                return False

            time.sleep(1)

            # 步骤2: 触发人工升级
            print("📝 步骤2: 触发人工升级")
            resp = requests.post(
                f"{self.base_url}/api/manual/escalate",
                json={"session_name": session_name, "reason": "manual"}  # 使用有效的枚举值
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get('success') and data['data']['status'] == 'pending_manual':
                    print_result("触发人工升级", True, "状态: pending_manual")
                    self.test_results['manual_takeover'].append(("触发人工升级", True))
                else:
                    print_result("触发人工升级", False, f"状态错误: {data}")
                    self.test_results['manual_takeover'].append(("触发人工升级", False))
                    return False
            else:
                print_result("触发人工升级", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("触发人工升级", False))
                return False

            # 步骤3: 验证 AI 对话被阻止
            print("📝 步骤3: 验证 AI 对话被阻止")
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": "测试", "user_id": session_name},
                timeout=10
            )
            if resp.status_code == 409:
                print_result("AI 对话被阻止", True, "✅ 正确返回 409 状态码")
                self.test_results['manual_takeover'].append(("AI 阻止", True))
            else:
                print_result("AI 对话被阻止", False, f"❌ 应返回 409，实际返回 {resp.status_code}")
                self.test_results['manual_takeover'].append(("AI 阻止", False))
                return False

            # 步骤4: 坐席接入
            print("📝 步骤4: 坐席接入会话")
            resp = requests.post(
                f"{self.base_url}/api/sessions/{session_name}/takeover",
                json={"agent_id": "test_agent", "agent_name": "测试坐席"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data['data']['status'] == 'manual_live':
                    print_result("坐席接入", True, "状态: manual_live")
                    self.test_results['manual_takeover'].append(("坐席接入", True))
                else:
                    print_result("坐席接入", False, f"状态错误: {data}")
                    self.test_results['manual_takeover'].append(("坐席接入", False))
                    return False
            else:
                print_result("坐席接入", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("坐席接入", False))
                return False

            # 步骤5: 人工发送消息
            print("📝 步骤5: 人工发送消息")
            resp = requests.post(
                f"{self.base_url}/api/manual/messages",
                json={
                    "session_name": session_name,
                    "role": "agent",
                    "content": "您好，我是测试坐席",
                    "agent_id": "test_agent",
                    "agent_name": "测试坐席"
                }
            )
            if resp.status_code == 200:
                print_result("人工发送消息", True)
                self.test_results['manual_takeover'].append(("人工消息", True))
            else:
                print_result("人工发送消息", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("人工消息", False))
                return False

            # 步骤6: 释放会话
            print("📝 步骤6: 释放会话，恢复 AI")
            resp = requests.post(
                f"{self.base_url}/api/sessions/{session_name}/release",
                json={"agent_id": "test_agent", "reason": "resolved"}
            )
            if resp.status_code == 200:
                data = resp.json()
                if data['data']['status'] == 'bot_active':
                    print_result("释放会话", True, "状态: bot_active")
                    self.test_results['manual_takeover'].append(("释放会话", True))
                else:
                    print_result("释放会话", False, f"状态错误: {data}")
                    self.test_results['manual_takeover'].append(("释放会话", False))
                    return False
            else:
                print_result("释放会话", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("释放会话", False))
                return False

            # 步骤7: 验证 AI 对话恢复
            print("📝 步骤7: 验证 AI 对话恢复")
            resp = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": "测试恢复", "user_id": session_name},
                timeout=30
            )
            if resp.status_code == 200:
                print_result("AI 对话恢复", True, "✅ AI 对话已恢复")
                self.test_results['manual_takeover'].append(("AI 恢复", True))
            else:
                print_result("AI 对话恢复", False, f"HTTP {resp.status_code}")
                self.test_results['manual_takeover'].append(("AI 恢复", False))
                return False

            return True

        except Exception as e:
            print_result("人工接管流程", False, f"异常: {str(e)}")
            self.test_results['manual_takeover'].append(("完整流程", False))
            return False

    def verify_constraints(self) -> bool:
        """验证技术约束遵守情况"""
        print_section("4. 技术约束遵守情况验证", "⚠️")

        constraints_check = []

        # 约束1: AI 对话核心流程未被修改
        print("🔍 验证约束1: AI 对话核心流程完整性")
        try:
            # 验证同步和流式接口仍然正常工作
            session_name = f"constraint_test_{int(time.time())}"

            # 同步接口
            resp_sync = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": "测试", "user_id": session_name},
                timeout=30
            )

            # 流式接口
            resp_stream = requests.post(
                f"{self.base_url}/api/chat/stream",
                json={"message": "测试", "user_id": f"{session_name}_stream"},
                stream=True,
                timeout=30
            )

            if resp_sync.status_code == 200 and resp_stream.status_code == 200:
                print_result("AI 核心接口完整", True, "同步和流式接口均正常")
                constraints_check.append(("AI 核心接口", True))
            else:
                print_result("AI 核心接口完整", False, f"同步:{resp_sync.status_code}, 流式:{resp_stream.status_code}")
                constraints_check.append(("AI 核心接口", False))

        except Exception as e:
            print_result("AI 核心接口完整", False, f"异常: {str(e)}")
            constraints_check.append(("AI 核心接口", False))

        # 约束2: SSE 格式未被修改
        print("\n🔍 验证约束2: SSE 流式响应格式")
        try:
            resp = requests.post(
                f"{self.base_url}/api/chat/stream",
                json={"message": "测试SSE", "user_id": f"sse_test_{int(time.time())}"},
                stream=True,
                timeout=30
            )

            sse_format_valid = False
            for line in resp.iter_lines():
                if line:
                    line_str = line.decode('utf-8')
                    if line_str.startswith('data: '):
                        try:
                            data = json.loads(line_str[6:])
                            if data.get('type') in ['message', 'done', 'error']:
                                sse_format_valid = True
                                break
                        except:
                            pass

            if sse_format_valid:
                print_result("SSE 格式规范", True, "SSE 事件格式符合规范")
                constraints_check.append(("SSE 格式", True))
            else:
                print_result("SSE 格式规范", False, "SSE 格式可能被修改")
                constraints_check.append(("SSE 格式", False))

        except Exception as e:
            print_result("SSE 格式规范", False, f"异常: {str(e)}")
            constraints_check.append(("SSE 格式", False))

        # 约束3: 会话隔离机制保持
        print("\n🔍 验证约束3: 会话隔离机制")
        # 这个在 test_session_isolation 中已经测试
        if any(item[0] == "会话隔离" and item[1] for item in self.test_results.get('session_isolation', [])):
            print_result("会话隔离机制", True, "session_name 隔离正常")
            constraints_check.append(("会话隔离", True))
        else:
            print_result("会话隔离机制", False, "隔离机制可能存在问题")
            constraints_check.append(("会话隔离", False))

        # 约束4: 新功能不影响原有功能
        print("\n🔍 验证约束4: 向后兼容性")
        if len([item for item in self.test_results.get('coze_api', []) if item[1]]) >= 2:
            print_result("向后兼容性", True, "原有 AI 对话功能不受影响")
            constraints_check.append(("向后兼容", True))
        else:
            print_result("向后兼容性", False, "原有功能可能受影响")
            constraints_check.append(("向后兼容", False))

        self.test_results['constraints'] = constraints_check
        return all(item[1] for item in constraints_check)

    def generate_report(self):
        """生成测试报告"""
        print_section("📊 测试报告汇总", "📋")

        categories = [
            ("Coze API 核心功能", "coze_api"),
            ("会话隔离机制", "session_isolation"),
            ("人工接管流程", "manual_takeover"),
            ("技术约束遵守", "constraints")
        ]

        total_tests = 0
        passed_tests = 0

        for category_name, category_key in categories:
            results = self.test_results.get(category_key, [])
            if results:
                category_passed = sum(1 for _, passed in results if passed)
                category_total = len(results)
                total_tests += category_total
                passed_tests += category_passed

                status = "✅ 通过" if category_passed == category_total else "❌ 失败"
                print(f"{status} {category_name}: {category_passed}/{category_total}")

                # 显示详细结果
                for test_name, passed in results:
                    icon = "  ✅" if passed else "  ❌"
                    print(f"{icon} {test_name}")

        print(f"\n{'=' * 70}")
        pass_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"总计: {passed_tests}/{total_tests} 通过 ({pass_rate:.1f}%)")
        print(f"{'=' * 70}\n")

        if pass_rate == 100:
            print("🎉 所有测试通过！系统功能完整，约束遵守良好。")
            return True
        elif pass_rate >= 80:
            print("⚠️  大部分测试通过，但有少数问题需要关注。")
            return False
        else:
            print("❌ 测试通过率较低，需要修复关键问题。")
            return False


def main():
    print("""
╔══════════════════════════════════════════════════════════════════╗
║              Fiido 智能客服系统 - 核心功能全面验证               ║
║                                                                  ║
║  验证范围:                                                        ║
║  1. ✅ Coze API 核心对话功能                                     ║
║  2. ✅ 会话隔离机制                                              ║
║  3. ✅ 人工接管完整流程                                          ║
║  4. ✅ 技术约束遵守情况                                          ║
╚══════════════════════════════════════════════════════════════════╝
    """)

    tester = CoreFunctionalityTester()

    # 执行测试
    try:
        # 测试1: Coze API
        coze_passed = tester.test_coze_api_basic()

        # 测试2: 会话隔离
        isolation_passed = tester.test_session_isolation()

        # 测试3: 人工接管流程
        takeover_passed = tester.test_manual_takeover_workflow()

        # 测试4: 约束验证
        constraints_passed = tester.verify_constraints()

        # 生成报告
        all_passed = tester.generate_report()

        # 退出码
        sys.exit(0 if all_passed else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
