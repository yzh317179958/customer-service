"""
Shopify UK 订单缓存层

基于 Redis 实现订单数据缓存，减少 Shopify API 调用频率。

缓存策略：
- 订单列表: 5 分钟 (用户可能频繁查询)
- 订单详情: 10 分钟 (相对稳定)
- 物流信息: 30 分钟 (更新频率低)
- 订单数量: 60 分钟 (统计数据)

遵循 CLAUDE.md 规范：
- 使用连接池限制并发
- 所有数据设置 TTL
- 完善的错误处理
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

import redis

logger = logging.getLogger(__name__)


class ShopifyUKCache:
    """
    Shopify UK 订单缓存

    特点：
    - 复用项目现有的 Redis 连接池
    - 分层 TTL 策略
    - 命名空间隔离 (shopify:uk:)
    """

    # 缓存键前缀
    PREFIX = "shopify:uk"

    # 默认 TTL 配置 (秒)
    DEFAULT_TTL = {
        "order_list": 300,      # 5 分钟
        "order_detail": 600,    # 10 分钟
        "tracking": 1800,       # 30 分钟
        "order_count": 3600,    # 60 分钟
    }

    def __init__(self, redis_client: Optional[redis.Redis] = None):
        """
        初始化缓存

        Args:
            redis_client: Redis 客户端实例，如果不提供则创建新连接
        """
        if redis_client:
            self.redis = redis_client
        else:
            # 从环境变量创建 Redis 连接
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            max_connections = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
            timeout = float(os.getenv("REDIS_TIMEOUT", "5.0"))

            pool = redis.ConnectionPool.from_url(
                redis_url,
                max_connections=max_connections,
                socket_timeout=timeout,
                socket_connect_timeout=timeout,
                decode_responses=True
            )
            self.redis = redis.Redis(connection_pool=pool)

        # 从环境变量读取 TTL 配置
        self.ttl = {
            "order_list": int(os.getenv("SHOPIFY_UK_CACHE_ORDER_LIST", self.DEFAULT_TTL["order_list"])),
            "order_detail": int(os.getenv("SHOPIFY_UK_CACHE_ORDER_DETAIL", self.DEFAULT_TTL["order_detail"])),
            "tracking": int(os.getenv("SHOPIFY_UK_CACHE_TRACKING", self.DEFAULT_TTL["tracking"])),
            "order_count": int(os.getenv("SHOPIFY_UK_CACHE_COUNT", self.DEFAULT_TTL["order_count"])),
        }

        logger.info(f"✅ Shopify UK 缓存初始化完成 (TTL: {self.ttl})")

    # ==================== 订单列表缓存 ====================

    def _order_list_key(self, email: str) -> str:
        """生成订单列表缓存键"""
        # 使用邮箱的小写形式作为键
        return f"{self.PREFIX}:orders:list:{email.lower()}"

    async def get_order_list(self, email: str) -> Optional[List[Dict]]:
        """
        获取订单列表缓存

        Args:
            email: 客户邮箱

        Returns:
            订单列表，缓存未命中返回 None
        """
        try:
            key = self._order_list_key(email)
            data = self.redis.get(key)

            if data:
                logger.debug(f"🎯 缓存命中: 订单列表 ({email})")
                return json.loads(data)

            logger.debug(f"💨 缓存未命中: 订单列表 ({email})")
            return None

        except Exception as e:
            logger.error(f"❌ 读取订单列表缓存失败: {e}")
            return None

    async def set_order_list(self, email: str, orders: List[Dict]) -> bool:
        """
        设置订单列表缓存

        Args:
            email: 客户邮箱
            orders: 订单列表数据

        Returns:
            是否设置成功
        """
        try:
            key = self._order_list_key(email)
            data = json.dumps(orders, ensure_ascii=False, default=str)
            self.redis.setex(key, self.ttl["order_list"], data)
            logger.debug(f"💾 缓存写入: 订单列表 ({email}, TTL={self.ttl['order_list']}s)")
            return True
        except Exception as e:
            logger.error(f"❌ 写入订单列表缓存失败: {e}")
            return False

    # ==================== 订单详情缓存 ====================

    def _order_detail_key(self, order_id: str) -> str:
        """生成订单详情缓存键"""
        return f"{self.PREFIX}:orders:detail:{order_id}"

    async def get_order_detail(self, order_id: str) -> Optional[Dict]:
        """
        获取订单详情缓存

        Args:
            order_id: Shopify 订单 ID

        Returns:
            订单详情，缓存未命中返回 None
        """
        try:
            key = self._order_detail_key(order_id)
            data = self.redis.get(key)

            if data:
                logger.debug(f"🎯 缓存命中: 订单详情 ({order_id})")
                return json.loads(data)

            logger.debug(f"💨 缓存未命中: 订单详情 ({order_id})")
            return None

        except Exception as e:
            logger.error(f"❌ 读取订单详情缓存失败: {e}")
            return None

    async def set_order_detail(self, order_id: str, order: Dict) -> bool:
        """
        设置订单详情缓存

        Args:
            order_id: Shopify 订单 ID
            order: 订单详情数据

        Returns:
            是否设置成功
        """
        try:
            key = self._order_detail_key(order_id)
            data = json.dumps(order, ensure_ascii=False, default=str)
            self.redis.setex(key, self.ttl["order_detail"], data)
            logger.debug(f"💾 缓存写入: 订单详情 ({order_id}, TTL={self.ttl['order_detail']}s)")
            return True
        except Exception as e:
            logger.error(f"❌ 写入订单详情缓存失败: {e}")
            return False

    # ==================== 订单号搜索缓存 ====================

    def _order_search_key(self, order_number: str) -> str:
        """生成订单搜索缓存键"""
        # 清理订单号格式
        clean_number = order_number.strip().lstrip("#").upper()
        return f"{self.PREFIX}:orders:search:{clean_number}"

    async def get_order_by_number(self, order_number: str) -> Optional[Dict]:
        """
        按订单号获取缓存

        Args:
            order_number: 订单号

        Returns:
            订单详情，缓存未命中返回 None
        """
        try:
            key = self._order_search_key(order_number)
            data = self.redis.get(key)

            if data:
                logger.debug(f"🎯 缓存命中: 订单搜索 ({order_number})")
                return json.loads(data)

            logger.debug(f"💨 缓存未命中: 订单搜索 ({order_number})")
            return None

        except Exception as e:
            logger.error(f"❌ 读取订单搜索缓存失败: {e}")
            return None

    async def set_order_by_number(self, order_number: str, order: Optional[Dict]) -> bool:
        """
        按订单号设置缓存

        Args:
            order_number: 订单号
            order: 订单详情数据（None 表示订单不存在）

        Returns:
            是否设置成功
        """
        try:
            key = self._order_search_key(order_number)

            if order is None:
                # 缓存"订单不存在"状态，使用较短的 TTL
                self.redis.setex(key, 60, json.dumps({"_not_found": True}))
                logger.debug(f"💾 缓存写入: 订单不存在 ({order_number}, TTL=60s)")
            else:
                data = json.dumps(order, ensure_ascii=False, default=str)
                self.redis.setex(key, self.ttl["order_detail"], data)
                logger.debug(f"💾 缓存写入: 订单搜索 ({order_number}, TTL={self.ttl['order_detail']}s)")

            return True
        except Exception as e:
            logger.error(f"❌ 写入订单搜索缓存失败: {e}")
            return False

    # ==================== 物流信息缓存 ====================

    def _tracking_key(self, order_id: str) -> str:
        """生成物流信息缓存键"""
        return f"{self.PREFIX}:tracking:{order_id}"

    async def get_tracking(self, order_id: str) -> Optional[Dict]:
        """
        获取物流信息缓存

        Args:
            order_id: Shopify 订单 ID

        Returns:
            物流信息，缓存未命中返回 None
        """
        try:
            key = self._tracking_key(order_id)
            data = self.redis.get(key)

            if data:
                logger.debug(f"🎯 缓存命中: 物流信息 ({order_id})")
                return json.loads(data)

            logger.debug(f"💨 缓存未命中: 物流信息 ({order_id})")
            return None

        except Exception as e:
            logger.error(f"❌ 读取物流信息缓存失败: {e}")
            return None

    async def set_tracking(self, order_id: str, tracking: Dict) -> bool:
        """
        设置物流信息缓存

        Args:
            order_id: Shopify 订单 ID
            tracking: 物流信息数据

        Returns:
            是否设置成功
        """
        try:
            key = self._tracking_key(order_id)
            data = json.dumps(tracking, ensure_ascii=False, default=str)
            self.redis.setex(key, self.ttl["tracking"], data)
            logger.debug(f"💾 缓存写入: 物流信息 ({order_id}, TTL={self.ttl['tracking']}s)")
            return True
        except Exception as e:
            logger.error(f"❌ 写入物流信息缓存失败: {e}")
            return False

    # ==================== 订单数量缓存 ====================

    def _order_count_key(self, status: str = "any") -> str:
        """生成订单数量缓存键"""
        return f"{self.PREFIX}:orders:count:{status}"

    async def get_order_count(self, status: str = "any") -> Optional[int]:
        """
        获取订单数量缓存

        Args:
            status: 订单状态

        Returns:
            订单数量，缓存未命中返回 None
        """
        try:
            key = self._order_count_key(status)
            data = self.redis.get(key)

            if data:
                logger.debug(f"🎯 缓存命中: 订单数量 ({status})")
                return int(data)

            logger.debug(f"💨 缓存未命中: 订单数量 ({status})")
            return None

        except Exception as e:
            logger.error(f"❌ 读取订单数量缓存失败: {e}")
            return None

    async def set_order_count(self, status: str, count: int) -> bool:
        """
        设置订单数量缓存

        Args:
            status: 订单状态
            count: 订单数量

        Returns:
            是否设置成功
        """
        try:
            key = self._order_count_key(status)
            self.redis.setex(key, self.ttl["order_count"], str(count))
            logger.debug(f"💾 缓存写入: 订单数量 ({status}={count}, TTL={self.ttl['order_count']}s)")
            return True
        except Exception as e:
            logger.error(f"❌ 写入订单数量缓存失败: {e}")
            return False

    # ==================== 缓存管理 ====================

    async def invalidate_order(self, order_id: str, order_number: Optional[str] = None) -> int:
        """
        使订单相关缓存失效

        Args:
            order_id: Shopify 订单 ID
            order_number: 订单号（可选）

        Returns:
            删除的缓存键数量
        """
        try:
            deleted = 0

            # 删除订单详情缓存
            key = self._order_detail_key(order_id)
            deleted += self.redis.delete(key)

            # 删除物流信息缓存
            key = self._tracking_key(order_id)
            deleted += self.redis.delete(key)

            # 删除订单号搜索缓存
            if order_number:
                key = self._order_search_key(order_number)
                deleted += self.redis.delete(key)

            logger.info(f"🗑️ 缓存失效: order_id={order_id}, 删除 {deleted} 个键")
            return deleted

        except Exception as e:
            logger.error(f"❌ 缓存失效操作失败: {e}")
            return 0

    async def clear_all(self) -> int:
        """
        清空所有 Shopify UK 缓存

        Returns:
            删除的缓存键数量
        """
        try:
            pattern = f"{self.PREFIX}:*"
            keys = list(self.redis.scan_iter(pattern, count=100))

            if keys:
                deleted = self.redis.delete(*keys)
                logger.warning(f"🧹 清空 Shopify UK 缓存: 删除 {deleted} 个键")
                return deleted

            return 0

        except Exception as e:
            logger.error(f"❌ 清空缓存失败: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            统计信息字典
        """
        try:
            stats = {
                "order_list": 0,
                "order_detail": 0,
                "order_search": 0,
                "tracking": 0,
                "order_count": 0,
                "total": 0,
            }

            # 统计各类型缓存数量
            for key in self.redis.scan_iter(f"{self.PREFIX}:*", count=100):
                stats["total"] += 1

                if ":orders:list:" in key:
                    stats["order_list"] += 1
                elif ":orders:detail:" in key:
                    stats["order_detail"] += 1
                elif ":orders:search:" in key:
                    stats["order_search"] += 1
                elif ":tracking:" in key:
                    stats["tracking"] += 1
                elif ":orders:count:" in key:
                    stats["order_count"] += 1

            return stats

        except Exception as e:
            logger.error(f"❌ 获取缓存统计失败: {e}")
            return {"error": str(e)}


# ==================== 全局实例 ====================

_shopify_uk_cache: Optional[ShopifyUKCache] = None


def get_shopify_uk_cache() -> ShopifyUKCache:
    """获取 Shopify UK 缓存单例"""
    global _shopify_uk_cache
    if _shopify_uk_cache is None:
        _shopify_uk_cache = ShopifyUKCache()
    return _shopify_uk_cache
