#!/usr/bin/env python3
"""
诊断聊天接口问题的测试脚本
"""
import httpx
import json
import time
import sys

API_BASE = "http://localhost:8000"

def test_conversation_new():
    """测试创建会话"""
    print("=" * 60)
    print("测试1: 创建新会话")
    print("=" * 60)

    try:
        response = httpx.post(
            f"{API_BASE}/api/conversation/new",
            json={"session_id": "debug_test_001"},
            timeout=10.0
        )
        print(f"✅ 状态码: {response.status_code}")
        print(f"✅ 响应: {response.json()}")
        return True
    except Exception as e:
        print(f"❌ 失败: {e}")
        return False

def test_chat_stream():
    """测试流式聊天"""
    print("\n" + "=" * 60)
    print("测试2: 发送消息(流式)")
    print("=" * 60)

    try:
        print("发送请求...")
        start_time = time.time()

        with httpx.stream(
            'POST',
            f"{API_BASE}/api/chat/stream",
            json={"message": "你好", "user_id": "debug_test_001"},
            timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=10.0)
        ) as response:
            print(f"✅ 状态码: {response.status_code}")
            print(f"✅ 连接耗时: {time.time() - start_time:.2f}秒")

            if response.status_code != 200:
                print(f"❌ 错误响应: {response.text}")
                return False

            print("\n接收SSE流:")
            print("-" * 60)

            count = 0
            for line in response.iter_lines():
                if line.startswith('data: '):
                    count += 1
                    try:
                        data = json.loads(line[6:])
                        print(f"[{count}] type={data.get('type')}, content={data.get('content', '')[:50]}...")

                        if data.get('type') == 'done':
                            print("\n✅ 流式响应完成")
                            break
                        elif data.get('type') == 'error':
                            print(f"\n❌ 服务器返回错误: {data.get('content')}")
                            return False
                    except json.JSONDecodeError as e:
                        print(f"⚠️  JSON解析失败: {line}")

                # 超过20条停止(避免输出过多)
                if count > 20:
                    print("\n(输出超过20条,截断)")
                    break

            elapsed = time.time() - start_time
            print(f"\n✅ 总耗时: {elapsed:.2f}秒")
            print(f"✅ 共收到 {count} 条SSE事件")
            return True

    except httpx.ReadTimeout:
        elapsed = time.time() - start_time
        print(f"\n❌ 读取超时 ({elapsed:.2f}秒)")
        print("可能原因:")
        print("  1. Coze API响应慢")
        print("  2. 工作流配置有问题")
        print("  3. 网络连接问题")
        return False
    except httpx.ConnectTimeout:
        print(f"\n❌ 连接超时")
        print("可能原因:")
        print("  1. 后端服务未启动")
        print("  2. 端口被防火墙阻止")
        return False
    except Exception as e:
        print(f"\n❌ 异常: {type(e).__name__}: {e}")
        return False

def main():
    print("🔍 AI客服聊天接口诊断工具\n")

    # 测试1
    success1 = test_conversation_new()

    # 测试2
    success2 = test_chat_stream()

    # 总结
    print("\n" + "=" * 60)
    print("诊断总结")
    print("=" * 60)
    print(f"创建会话: {'✅ 通过' if success1 else '❌ 失败'}")
    print(f"流式聊天: {'✅ 通过' if success2 else '❌ 失败'}")

    if success1 and success2:
        print("\n🎉 所有测试通过!")
        sys.exit(0)
    else:
        print("\n⚠️  存在问题,请检查后端日志")
        sys.exit(1)

if __name__ == "__main__":
    main()
