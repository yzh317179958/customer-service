"""
Shopify UK 订单服务层

整合 ShopifyUKClient 和 ShopifyUKCache，提供带缓存的订单查询服务。

用于 API 端点调用，自动处理缓存逻辑。
"""

import logging
from typing import Optional, List, Dict, Any

from src.shopify_uk_client import (
    ShopifyUKClient,
    ShopifyOrderSummary,
    ShopifyOrderDetail,
    ShopifyAPIError,
    get_shopify_uk_client,
)
from src.shopify_uk_cache import ShopifyUKCache, get_shopify_uk_cache
from src.shopify_tracking import enrich_tracking_data

logger = logging.getLogger(__name__)


class ShopifyUKService:
    """
    Shopify UK 订单服务

    特点：
    - 自动缓存查询结果
    - 缓存命中时响应 < 100ms
    - 缓存未命中时调用 Shopify API
    """

    def __init__(
        self,
        client: Optional[ShopifyUKClient] = None,
        cache: Optional[ShopifyUKCache] = None
    ):
        """
        初始化服务

        Args:
            client: Shopify 客户端（可选，默认使用单例）
            cache: 缓存实例（可选，默认使用单例）
        """
        self.client = client or get_shopify_uk_client()
        self.cache = cache or get_shopify_uk_cache()
        logger.info("✅ Shopify UK 服务初始化完成")

    async def get_orders_by_email(
        self,
        email: str,
        limit: int = 10,
        status: str = "any",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        按客户邮箱查询订单列表

        Args:
            email: 客户邮箱
            limit: 返回数量限制 (1-50)
            status: 订单状态筛选 (open/closed/cancelled/any)
            use_cache: 是否使用缓存

        Returns:
            包含订单列表和缓存状态的字典
        """
        cache_hit = False

        # 尝试从缓存获取
        if use_cache:
            cached_orders = await self.cache.get_order_list(email)
            if cached_orders is not None:
                cache_hit = True
                # 从缓存返回时应用 limit
                orders = cached_orders[:limit]
                logger.info(f"🎯 缓存命中: 订单列表 ({email})")
                return {
                    "orders": orders,
                    "total": len(cached_orders),
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_list"]
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单列表 ({email})")
        orders = await self.client.get_orders_by_email(email, limit=50, status=status)

        # 转换为字典列表
        orders_data = [order.model_dump() for order in orders]

        # 保存到缓存（保存完整结果，供后续不同 limit 查询使用）
        if use_cache:
            await self.cache.set_order_list(email, orders_data)

        return {
            "orders": orders_data[:limit],
            "total": len(orders_data),
            "cached": False,
            "cache_ttl": self.cache.ttl["order_list"]
        }

    async def search_order_by_number(
        self,
        order_number: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        按订单号搜索订单

        Args:
            order_number: 订单号 (支持 #UK22080 或 UK22080 格式)
            use_cache: 是否使用缓存

        Returns:
            包含订单详情和缓存状态的字典，如果订单不存在返回 None
        """
        # 尝试从缓存获取
        if use_cache:
            cached_order = await self.cache.get_order_by_number(order_number)
            if cached_order is not None:
                # 检查是否是"不存在"标记
                if cached_order.get("_not_found"):
                    logger.info(f"🎯 缓存命中: 订单不存在 ({order_number})")
                    return None

                logger.info(f"🎯 缓存命中: 订单搜索 ({order_number})")
                return {
                    "order": cached_order,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_detail"]
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单搜索 ({order_number})")
        order = await self.client.search_order_by_number(order_number)

        if order is None:
            # 缓存"订单不存在"状态
            if use_cache:
                await self.cache.set_order_by_number(order_number, None)
            return None

        # 转换为字典
        order_data = order.model_dump()

        # 保存到缓存
        if use_cache:
            await self.cache.set_order_by_number(order_number, order_data)

        return {
            "order": order_data,
            "cached": False,
            "cache_ttl": self.cache.ttl["order_detail"]
        }

    async def get_order_detail(
        self,
        order_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取订单详情

        Args:
            order_id: Shopify 订单 ID
            use_cache: 是否使用缓存

        Returns:
            包含订单详情和缓存状态的字典
        """
        # 尝试从缓存获取
        if use_cache:
            cached_order = await self.cache.get_order_detail(order_id)
            if cached_order is not None:
                logger.info(f"🎯 缓存命中: 订单详情 ({order_id})")
                return {
                    "order": cached_order,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_detail"]
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单详情 ({order_id})")
        order = await self.client.get_order_detail(order_id)

        # 转换为字典
        order_data = order.model_dump()

        # 保存到缓存
        if use_cache:
            await self.cache.set_order_detail(order_id, order_data)

        return {
            "order": order_data,
            "cached": False,
            "cache_ttl": self.cache.ttl["order_detail"]
        }

    async def get_order_tracking(
        self,
        order_id: str,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取订单物流信息

        Args:
            order_id: Shopify 订单 ID
            use_cache: 是否使用缓存

        Returns:
            包含物流信息和缓存状态的字典
        """
        # 尝试从缓存获取
        if use_cache:
            cached_tracking = await self.cache.get_tracking(order_id)
            if cached_tracking is not None:
                logger.info(f"🎯 缓存命中: 物流信息 ({order_id})")
                return {
                    "tracking": cached_tracking,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["tracking"]
                }

        # 缓存未命中，获取订单详情提取物流信息
        logger.info(f"🔄 调用 Shopify API: 物流信息 ({order_id})")
        order = await self.client.get_order_detail(order_id)

        # 提取物流信息
        tracking_data = {
            "order_id": order.order_id,
            "order_number": order.order_number,
            "fulfillment_status": order.fulfillment_status,
            "fulfillments": [f.model_dump() for f in order.fulfillments]
        }

        # 如果有发货信息，提取主要物流信息
        if order.fulfillments:
            primary = order.fulfillments[0]
            tracking_data["primary_tracking"] = {
                "company": primary.tracking_company,
                "number": primary.tracking_number,
                "url": primary.tracking_url,
                "status": primary.status,
                "shipped_at": primary.created_at
            }

        # 使用翻译模块丰富物流数据
        tracking_data = enrich_tracking_data(tracking_data)

        # 保存到缓存（保存丰富后的数据）
        if use_cache:
            await self.cache.set_tracking(order_id, tracking_data)

        return {
            "tracking": tracking_data,
            "cached": False,
            "cache_ttl": self.cache.ttl["tracking"]
        }

    async def get_order_count(
        self,
        status: str = "any",
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        获取订单数量统计

        Args:
            status: 订单状态
            use_cache: 是否使用缓存

        Returns:
            包含订单数量和缓存状态的字典
        """
        # 尝试从缓存获取
        if use_cache:
            cached_count = await self.cache.get_order_count(status)
            if cached_count is not None:
                logger.info(f"🎯 缓存命中: 订单数量 ({status})")
                return {
                    "count": cached_count,
                    "status": status,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_count"]
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单数量 ({status})")
        count = await self.client.get_order_count(status=status)

        # 保存到缓存
        if use_cache:
            await self.cache.set_order_count(status, count)

        return {
            "count": count,
            "status": status,
            "cached": False,
            "cache_ttl": self.cache.ttl["order_count"]
        }

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            健康状态信息
        """
        # 检查 Shopify API
        api_health = await self.client.health_check()

        # 检查缓存
        cache_stats = self.cache.get_stats()

        return {
            "api": api_health,
            "cache": cache_stats
        }


# ==================== 全局实例 ====================

_shopify_uk_service: Optional[ShopifyUKService] = None


def get_shopify_uk_service() -> ShopifyUKService:
    """获取 Shopify UK 服务单例"""
    global _shopify_uk_service
    if _shopify_uk_service is None:
        _shopify_uk_service = ShopifyUKService()
    return _shopify_uk_service
