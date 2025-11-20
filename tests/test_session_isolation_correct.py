#!/usr/bin/env python3
"""
会话隔离测试脚本 - 正确版本
严格遵循《Coze会话隔离最终解决方案.md》的实现方式:
1. 页面加载时立即调用 /api/conversation/new
2. 使用返回的 conversation_id 进行对话
3. 验证会话完全隔离
"""

import requests
import json
import uuid
import time

BASE_URL = "http://localhost:8000"

def generate_session_id():
    """模拟前端生成唯一的 session_id"""
    return f"session_{uuid.uuid4().hex[:16]}"

def create_conversation(session_id):
    """
    创建新对话 - 关键步骤!
    这是会话隔离的核心:必须在发送消息前预先创建conversation
    """
    print(f"   📞 调用 /api/conversation/new (session: {session_id})")
    response = requests.post(
        f"{BASE_URL}/api/conversation/new",
        json={"session_id": session_id},
        timeout=30
    )
    data = response.json()

    if data.get("success"):
        conv_id = data.get("conversation_id")
        print(f"   ✅ Conversation已创建: {conv_id}")
        return conv_id
    else:
        print(f"   ❌ 创建失败: {data.get('error')}")
        return None

def send_message(session_id, conversation_id, message):
    """发送消息"""
    payload = {
        "message": message,
        "user_id": session_id,
        "conversation_id": conversation_id  # 【关键】必须传入
    }

    response = requests.post(
        f"{BASE_URL}/api/chat",
        json=payload,
        timeout=60
    )
    return response.json()

print("=" * 70)
print("🧪 会话隔离测试 - 正确实现版本")
print("=" * 70)
print("\n📋 测试步骤:")
print("  1. 用户A打开页面 → 立即创建conversation_A")
print("  2. 用户B打开页面 → 立即创建conversation_B")
print("  3. 验证 conversation_A ≠ conversation_B")
print("  4. 用户A/B分别对话，验证上下文隔离")

# ===== 步骤1: 用户A打开页面 =====
print("\n" + "-" * 70)
print("👤 用户A打开页面")
print("-" * 70)
session_a = generate_session_id()
print(f"   生成 session_id: {session_a}")
conv_a = create_conversation(session_a)

if not conv_a:
    print("\n❌ 测试中止: 无法创建 conversation_A")
    exit(1)

time.sleep(1)

# ===== 步骤2: 用户B打开页面 =====
print("\n" + "-" * 70)
print("👤 用户B打开页面")
print("-" * 70)
session_b = generate_session_id()
print(f"   生成 session_id: {session_b}")
conv_b = create_conversation(session_b)

if not conv_b:
    print("\n❌ 测试中止: 无法创建 conversation_B")
    exit(1)

# ===== 步骤3: 验证conversation_id不同 =====
print("\n" + "=" * 70)
print("🔍 验证 Conversation ID")
print("=" * 70)
print(f"Session A: {session_a}")
print(f"  → Conversation ID: {conv_a}")
print(f"\nSession B: {session_b}")
print(f"  → Conversation ID: {conv_b}")

if conv_a == conv_b:
    print("\n❌ 【严重问题】两个session获得了相同的conversation_id!")
    print("   会话隔离必然失败!")
    print("   请检查后端 /api/conversation/new 实现")
    exit(1)
else:
    print(f"\n✅ Conversation ID 不同 - 这是会话隔离的前提条件")

time.sleep(1)

# ===== 步骤4: 用户A对话 =====
print("\n" + "-" * 70)
print("💬 用户A - 第1轮对话")
print("-" * 70)
message_a1 = "你好，我的名字是张三，我今年25岁"
print(f"   消息: {message_a1}")
print(f"   使用 Conversation: {conv_a}")

result_a1 = send_message(session_a, conv_a, message_a1)
if result_a1.get("success"):
    print(f"   ✅ AI回复: {result_a1.get('message', '')[:100]}...")
else:
    print(f"   ❌ 失败: {result_a1.get('error')}")

time.sleep(2)

# ===== 步骤5: 用户B对话 =====
print("\n" + "-" * 70)
print("💬 用户B - 第1轮对话")
print("-" * 70)
message_b1 = "你好，我叫李四，我是一名程序员"
print(f"   消息: {message_b1}")
print(f"   使用 Conversation: {conv_b}")

result_b1 = send_message(session_b, conv_b, message_b1)
if result_b1.get("success"):
    print(f"   ✅ AI回复: {result_b1.get('message', '')[:100]}...")
else:
    print(f"   ❌ 失败: {result_b1.get('error')}")

time.sleep(2)

# ===== 步骤6: 用户A第2轮 - 测试记忆 =====
print("\n" + "-" * 70)
print("💬 用户A - 第2轮对话 (测试上下文记忆)")
print("-" * 70)
message_a2 = "我叫什么名字？我多大了？"
print(f"   消息: {message_a2}")
print(f"   期望: 应该记得\"张三\"和\"25岁\"")

result_a2 = send_message(session_a, conv_a, message_a2)
if result_a2.get("success"):
    response_a2 = result_a2.get('message', '')
    print(f"   ✅ AI回复: {response_a2[:200]}...")

    # 检查是否记住了正确的信息
    if "张三" in response_a2 and "25" in response_a2:
        print("\n   ✅ 【成功】正确记住了用户A的信息")
        context_a_ok = True
    elif "李四" in response_a2 or "程序员" in response_a2:
        print("\n   ❌ 【失败】混淆了用户B的信息!")
        context_a_ok = False
    else:
        print("\n   ⚠️  未能识别上下文")
        context_a_ok = False
else:
    print(f"   ❌ 失败: {result_a2.get('error')}")
    context_a_ok = False

time.sleep(2)

# ===== 步骤7: 用户B第2轮 - 测试记忆 =====
print("\n" + "-" * 70)
print("💬 用户B - 第2轮对话 (测试上下文记忆)")
print("-" * 70)
message_b2 = "我的名字是什么？我的职业是什么？"
print(f"   消息: {message_b2}")
print(f"   期望: 应该记得\"李四\"和\"程序员\"")

result_b2 = send_message(session_b, conv_b, message_b2)
if result_b2.get("success"):
    response_b2 = result_b2.get('message', '')
    print(f"   ✅ AI回复: {response_b2[:200]}...")

    # 检查是否记住了正确的信息
    if "李四" in response_b2 and "程序员" in response_b2:
        print("\n   ✅ 【成功】正确记住了用户B的信息")
        context_b_ok = True
    elif "张三" in response_b2 or "25" in response_b2:
        print("\n   ❌ 【失败】混淆了用户A的信息!")
        context_b_ok = False
    else:
        print("\n   ⚠️  未能识别上下文")
        context_b_ok = False
else:
    print(f"   ❌ 失败: {result_b2.get('error')}")
    context_b_ok = False

time.sleep(2)

# ===== 步骤8: 关键验证 - 用户A不应该知道用户B的信息 =====
print("\n" + "-" * 70)
print("🔍 关键验证 - 会话隔离测试")
print("-" * 70)
message_a3 = "你知道李四是谁吗？"
print(f"   用户A问: {message_a3}")
print(f"   期望: 不应该知道李四（因为李四是用户B说的）")

result_a3 = send_message(session_a, conv_a, message_a3)
if result_a3.get("success"):
    response_a3 = result_a3.get('message', '')
    print(f"   ✅ AI回复: {response_a3[:200]}...")

    # 检查会话隔离
    if "程序员" in response_a3 and "李四" in response_a3:
        print("\n   ❌ 【失败】用户A知道了用户B的信息 - 会话隔离失败!")
        isolation_ok = False
    else:
        print("\n   ✅ 【成功】用户A不知道用户B的信息 - 会话隔离成功!")
        isolation_ok = True
else:
    print(f"   ❌ 失败: {result_a3.get('error')}")
    isolation_ok = False

# ===== 最终结果 =====
print("\n" + "=" * 70)
print("📊 测试结果总结")
print("=" * 70)

print(f"\n🔐 Conversation ID 验证:")
print(f"   Session A: {session_a}")
print(f"   → Conversation: {conv_a}")
print(f"   Session B: {session_b}")
print(f"   → Conversation: {conv_b}")
print(f"   ✅ ID不同: {conv_a != conv_b}")

print(f"\n📝 上下文记忆测试:")
print(f"   ✅ 用户A上下文正确: {context_a_ok}")
print(f"   ✅ 用户B上下文正确: {context_b_ok}")

print(f"\n🔒 会话隔离测试:")
print(f"   ✅ 用户A/B完全隔离: {isolation_ok}")

print(f"\n" + "=" * 70)
if isolation_ok and context_a_ok and context_b_ok:
    print("✅ 【测试通过】会话隔离功能正常!")
    print("   - Conversation ID 正确分配")
    print("   - 各用户上下文独立")
    print("   - 会话完全隔离")
else:
    print("❌ 【测试失败】会话隔离存在问题!")
    if not (conv_a != conv_b):
        print("   - Conversation ID 相同 (根本原因!)")
    if not context_a_ok or not context_b_ok:
        print("   - 上下文记忆混乱")
    if not isolation_ok:
        print("   - 会话隔离失效")
print("=" * 70)
