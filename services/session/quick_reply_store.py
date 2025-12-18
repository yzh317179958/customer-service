"""
快捷回复存储管理

模块3: L1-1-Part2-模块3 - 快捷回复系统
版本: v3.7.0
"""

import json
from typing import List, Optional
import redis
import uuid

from src.quick_reply import QuickReply, QuickReplyCategory


class QuickReplyStore:
    """快捷回复Redis存储管理"""

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.key_prefix = "quick_reply"
        self.index_key = f"{self.key_prefix}:index"  # 所有快捷回复ID的集合
        self.category_key_prefix = f"{self.key_prefix}:category"  # 按分类索引
        self.agent_key_prefix = f"{self.key_prefix}:agent"  # 按坐席索引

    def create(self, quick_reply: QuickReply) -> QuickReply:
        """创建快捷回复"""
        # 生成ID（如果没有）
        if not quick_reply.id:
            quick_reply.id = f"reply_{uuid.uuid4().hex[:12]}"

        # 保存到Redis
        key = f"{self.key_prefix}:{quick_reply.id}"
        self.redis.set(key, json.dumps(quick_reply.to_dict()))

        # 更新索引
        self.redis.sadd(self.index_key, quick_reply.id)

        # 更新分类索引
        category_key = f"{self.category_key_prefix}:{quick_reply.category}"
        self.redis.sadd(category_key, quick_reply.id)

        # 更新坐席索引
        agent_key = f"{self.agent_key_prefix}:{quick_reply.created_by}"
        self.redis.sadd(agent_key, quick_reply.id)

        return quick_reply

    def get(self, reply_id: str) -> Optional[QuickReply]:
        """获取快捷回复"""
        key = f"{self.key_prefix}:{reply_id}"
        data = self.redis.get(key)

        if not data:
            return None

        return QuickReply.from_dict(json.loads(data))

    def update(self, reply_id: str, updates: dict) -> Optional[QuickReply]:
        """更新快捷回复"""
        quick_reply = self.get(reply_id)
        if not quick_reply:
            return None

        # 如果分类变化，更新分类索引
        old_category = quick_reply.category
        new_category = updates.get('category', old_category)

        if old_category != new_category:
            # 从旧分类移除
            old_category_key = f"{self.category_key_prefix}:{old_category}"
            self.redis.srem(old_category_key, reply_id)

            # 添加到新分类
            new_category_key = f"{self.category_key_prefix}:{new_category}"
            self.redis.sadd(new_category_key, reply_id)

        # 更新字段
        for key, value in updates.items():
            if hasattr(quick_reply, key):
                setattr(quick_reply, key, value)

        # 更新时间戳
        import time
        quick_reply.updated_at = time.time()

        # 保存
        key = f"{self.key_prefix}:{reply_id}"
        self.redis.set(key, json.dumps(quick_reply.to_dict()))

        return quick_reply

    def delete(self, reply_id: str) -> bool:
        """删除快捷回复"""
        quick_reply = self.get(reply_id)
        if not quick_reply:
            return False

        # 删除数据
        key = f"{self.key_prefix}:{reply_id}"
        self.redis.delete(key)

        # 删除索引
        self.redis.srem(self.index_key, reply_id)

        # 删除分类索引
        category_key = f"{self.category_key_prefix}:{quick_reply.category}"
        self.redis.srem(category_key, reply_id)

        # 删除坐席索引
        agent_key = f"{self.agent_key_prefix}:{quick_reply.created_by}"
        self.redis.srem(agent_key, reply_id)

        return True

    def list_all(self, limit: int = 100, offset: int = 0) -> List[QuickReply]:
        """获取所有快捷回复列表"""
        reply_ids = list(self.redis.smembers(self.index_key))

        # 分页
        paginated_ids = reply_ids[offset:offset + limit]

        # 批量获取
        replies = []
        for reply_id in paginated_ids:
            reply = self.get(reply_id)
            if reply:
                replies.append(reply)

        # 按使用次数降序排列
        replies.sort(key=lambda x: x.usage_count, reverse=True)

        return replies

    def list_by_category(
        self,
        category: QuickReplyCategory,
        limit: int = 100,
        offset: int = 0
    ) -> List[QuickReply]:
        """按分类获取快捷回复"""
        category_key = f"{self.category_key_prefix}:{category}"
        reply_ids = list(self.redis.smembers(category_key))

        # 分页
        paginated_ids = reply_ids[offset:offset + limit]

        # 批量获取
        replies = []
        for reply_id in paginated_ids:
            reply = self.get(reply_id)
            if reply:
                replies.append(reply)

        # 按使用次数降序排列
        replies.sort(key=lambda x: x.usage_count, reverse=True)

        return replies

    def list_by_agent(
        self,
        agent_id: str,
        include_shared: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[QuickReply]:
        """按坐席获取快捷回复"""
        replies = []

        # 获取坐席自己创建的
        agent_key = f"{self.agent_key_prefix}:{agent_id}"
        agent_reply_ids = list(self.redis.smembers(agent_key))

        for reply_id in agent_reply_ids:
            reply = self.get(reply_id)
            if reply:
                replies.append(reply)

        # 如果包含共享的，获取团队共享的快捷回复
        if include_shared:
            all_reply_ids = list(self.redis.smembers(self.index_key))
            for reply_id in all_reply_ids:
                if reply_id in agent_reply_ids:
                    continue  # 已经添加过了

                reply = self.get(reply_id)
                if reply and reply.is_shared:
                    replies.append(reply)

        # 按使用次数降序排列
        replies.sort(key=lambda x: x.usage_count, reverse=True)

        # 分页
        return replies[offset:offset + limit]

    def search(
        self,
        keyword: str,
        agent_id: Optional[str] = None,
        category: Optional[QuickReplyCategory] = None,
        limit: int = 50
    ) -> List[QuickReply]:
        """搜索快捷回复"""
        # 获取候选列表
        if category:
            candidates = self.list_by_category(category, limit=1000)
        elif agent_id:
            candidates = self.list_by_agent(agent_id, limit=1000)
        else:
            candidates = self.list_all(limit=1000)

        # 关键词搜索
        keyword_lower = keyword.lower()
        results = []

        for reply in candidates:
            # 在标题或内容中搜索
            if (keyword_lower in reply.title.lower() or
                keyword_lower in reply.content.lower()):
                results.append(reply)

        # 限制结果数量
        return results[:limit]

    def increment_usage(self, reply_id: str) -> bool:
        """增加使用次数"""
        quick_reply = self.get(reply_id)
        if not quick_reply:
            return False

        quick_reply.increment_usage()

        # 保存
        key = f"{self.key_prefix}:{reply_id}"
        self.redis.set(key, json.dumps(quick_reply.to_dict()))

        return True

    def get_stats(self) -> dict:
        """获取使用统计"""
        all_replies = self.list_all(limit=1000)

        total_count = len(all_replies)
        total_usage = sum(r.usage_count for r in all_replies)

        # 分类统计
        category_stats = {}
        for reply in all_replies:
            if reply.category not in category_stats:
                category_stats[reply.category] = {
                    'count': 0,
                    'usage': 0
                }
            category_stats[reply.category]['count'] += 1
            category_stats[reply.category]['usage'] += reply.usage_count

        # TOP 10
        top_10 = sorted(all_replies, key=lambda x: x.usage_count, reverse=True)[:10]

        return {
            'total_count': total_count,
            'total_usage': total_usage,
            'category_stats': category_stats,
            'top_10': [r.to_dict() for r in top_10]
        }
