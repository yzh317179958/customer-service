#!/usr/bin/env python3
"""
创建测试数据 - 模块2优先级测试专用
通过API创建会话 + Redis修改VIP状态
"""

import requests
import time
import redis
import json

BASE_URL = "http://localhost:8000"

def main():
    print("=" * 60)
    print("  创建测试数据（模块2优先级测试）")
    print("=" * 60)

    # 连接 Redis
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        redis_client.ping()
        print("✅ 已连接到 Redis\n")
    except Exception as e:
        print(f"❌ Redis 连接失败: {e}")
        return

    # 测试会话数据
    test_sessions = [
        {
            "session_name": "vip_customer_张三_001",
            "nickname": "张三 (VIP会员)",
            "vip": True,
            "keywords": [],
            "message": "你好，我的 D4S 电动车电池充不进电了"
        },
        {
            "session_name": "refund_request_王五_003",
            "nickname": "王五",
            "vip": False,
            "keywords": ["退款"],
            "message": "我要申请退款，收到的车子有划痕"
        },
        {
            "session_name": "complaint_赵六_004",
            "nickname": "赵六",
            "vip": False,
            "keywords": ["投诉"],
            "message": "我要投诉你们的服务态度"
        },
        {
            "session_name": "normal_customer_孙七_005",
            "nickname": "孙七",
            "vip": False,
            "keywords": [],
            "message": "请问这款车的续航里程是多少？"
        },
    ]

    print(f"创建 {len(test_sessions)} 个测试会话...\n")

    created_count = 0
    for data in test_sessions:
        session_name = data["session_name"]

        try:
            # 步骤1: 创建会话（发送消息触发AI对话）
            chat_payload = {
                "message": data["message"],
                "user_id": session_name
            }

            chat_response = requests.post(
                f"{BASE_URL}/api/chat",
                json=chat_payload,
                timeout=10
            )

            if chat_response.status_code != 200:
                print(f"❌ 创建会话失败: {session_name} - {chat_response.status_code}")
                continue

            # 步骤2: 修改 Redis 中的 user_profile（设置VIP和昵称）
            session_key = f"session:{session_name}"
            session_json = redis_client.get(session_key)

            if session_json:
                session_data = json.loads(session_json)
                session_data["user_profile"] = {
                    "nickname": data["nickname"],
                    "vip": data["vip"],
                    "metadata": {}
                }

                # 保存回 Redis
                redis_client.set(session_key, json.dumps(session_data))

            # 步骤3: 触发人工升级
            escalate_payload = {
                "session_name": session_name,
                "reason": "manual"
            }

            escalate_response = requests.post(
                f"{BASE_URL}/api/manual/escalate",
                json=escalate_payload,
                timeout=5
            )

            if escalate_response.status_code == 200:
                vip_badge = '👑VIP' if data['vip'] else '   '
                keyword_info = f" [关键词: {','.join(data['keywords'])}]" if data['keywords'] else ""
                print(f"✅ {vip_badge} {session_name:35s} {data['nickname']:15s}{keyword_info}")
                created_count += 1
            else:
                print(f"⚠️  升级失败: {session_name} - {escalate_response.status_code}")

            # 短暂延迟
            time.sleep(0.5)

        except Exception as e:
            print(f"❌ 创建失败: {session_name} - {e}")

    print(f"\n" + "=" * 60)
    print(f"✅ 测试数据创建完成！成功创建 {created_count}/{len(test_sessions)} 个会话")
    print("=" * 60)

    # 验证创建结果
    time.sleep(1)
    print(f"\n📊 数据验证：")

    try:
        # 查询队列API
        queue_response = requests.get(f"{BASE_URL}/api/sessions/queue", timeout=5)
        if queue_response.status_code == 200:
            queue_data = queue_response.json()
            if queue_data['success']:
                stats = queue_data['data']
                print(f"  - 队列总数: {stats['total_count']}")
                print(f"  - VIP数量: {stats['vip_count']}")
                print(f"  - 平均等待: {stats['avg_wait_time']:.1f}秒")

                # 显示队列排序
                if stats['queue']:
                    print(f"\n🎯 队列排序（按优先级）:")
                    for item in stats['queue'][:5]:
                        vip_badge = '👑VIP' if item['is_vip'] else '    '
                        priority_emoji = {
                            'urgent': '🔴',
                            'high': '🟠',
                            'normal': '⚪'
                        }.get(item['priority_level'], '⚪')
                        user_name = item.get('user_profile', {}).get('nickname', '未知')
                        keywords = f" [关键词: {','.join(item['urgent_keywords'])}]" if item['urgent_keywords'] else ""
                        print(f"  {item['position']}. {priority_emoji} {vip_badge} {user_name:20s} ({item['priority_level']}){keywords}")

        # 查询会话列表
        sessions_response = requests.get(
            f"{BASE_URL}/api/sessions?status=pending_manual&limit=10",
            timeout=5
        )
        if sessions_response.status_code == 200:
            sessions_data = sessions_response.json()
            if sessions_data['success']:
                total = sessions_data['data']['total']
                print(f"\n  - pending_manual会话: {total} 个")

                # 显示各会话的优先级
                print(f"\n📋 会话优先级详情:")
                for session in sessions_data['data']['sessions']:
                    priority = session.get('priority', {})
                    vip = '👑VIP' if priority.get('is_vip') else '   '
                    level = priority.get('level', 'unknown')
                    keywords = priority.get('urgent_keywords', [])
                    user_name = session.get('user_profile', {}).get('nickname', '未知')

                    keyword_info = f" [{','.join(keywords)}]" if keywords else ""
                    print(f"  {vip} {user_name:20s} → {level:6s}{keyword_info}")

    except Exception as e:
        print(f"⚠️  验证失败: {e}")

    print(f"\n💡 提示：")
    print(f"  1. 访问坐席工作台查看效果: http://localhost:5182/")
    print(f"  2. 登录账号: admin / admin123")
    print(f"  3. 点击左侧【待接入】标签页，查看优先级标识")
    print(f"  4. 观察【等待队列】统计卡片")
    print()

if __name__ == "__main__":
    main()
