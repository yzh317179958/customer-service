"""
Shopify 多站点订单服务层

整合 ShopifyClient 和 ShopifyCache，提供带缓存的订单查询服务。
支持所有站点，通过 site_code 参数选择站点。

用于 API 端点调用，自动处理缓存逻辑。
"""

import logging
from typing import Optional, List, Dict, Any

from services.shopify.client import (
    ShopifyClient,
    ShopifyOrderSummary,
    ShopifyOrderDetail,
    ShopifyAPIError,
    get_shopify_client,
    ERROR_CODES,
)
from services.shopify.cache import ShopifyCache, get_shopify_cache
from services.shopify.sites import (
    get_site_config,
    get_all_configured_sites,
    detect_site_from_order_number,
    SiteCode,
)
from services.shopify.tracking import enrich_tracking_data
from services.tracking import get_tracking_service, TrackingStatus

logger = logging.getLogger(__name__)


class ShopifyService:
    """
    Shopify 多站点订单服务

    特点：
    - 自动缓存查询结果
    - 缓存命中时响应 < 100ms
    - 缓存未命中时调用 Shopify API
    - 支持多站点切换
    """

    def __init__(
        self,
        site_code: str,
        client: Optional[ShopifyClient] = None,
        cache: Optional[ShopifyCache] = None
    ):
        """
        初始化服务

        Args:
            site_code: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
            client: Shopify 客户端（可选，默认使用工厂创建）
            cache: 缓存实例（可选，默认使用工厂创建）
        """
        self.site_code = site_code.lower().strip()
        self.client = client or get_shopify_client(self.site_code)
        self.cache = cache or get_shopify_cache(self.site_code)
        logger.info(f"✅ Shopify {self.site_code.upper()} 服务初始化完成")

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
                logger.info(f"🎯 缓存命中: 订单列表 ({self.site_code}:{email})")
                return {
                    "orders": orders,
                    "total": len(cached_orders),
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_list"],
                    "site_code": self.site_code
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单列表 ({self.site_code}:{email})")
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
            "cache_ttl": self.cache.ttl["order_list"],
            "site_code": self.site_code
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
        async def enrich_cached_delivery_status(order: Dict[str, Any]) -> bool:
            """
            缓存命中时的状态补全：
            Shopify fulfillment.shipment_status 可能为空，导致商品显示为“已发货”。
            若存在 tracking_number，则用 17track 的状态补全为“已收货/运输中/派送中/投递失败”。

            Returns:
                bool: 是否发生了更新（用于回写缓存）
            """
            line_items: List[Dict[str, Any]] = order.get("line_items") or []
            if not line_items:
                return False

            # 仅补全：已发货（fulfilled）但 delivery_status 为空的实物商品
            candidates: Dict[str, Optional[str]] = {}
            for item in line_items:
                if item.get("delivery_status"):
                    continue
                if item.get("fulfillment_status") != "fulfilled":
                    continue
                tracking_number = item.get("tracking_number")
                if not tracking_number:
                    continue
                candidates.setdefault(tracking_number, item.get("tracking_company"))

            if not candidates:
                return False

            status_text_map = {
                "success": ("已收货", "Received"),
                "in_transit": ("运输中", "In Transit"),
                "out_for_delivery": ("派送中", "Out for Delivery"),
                "failure": ("投递失败", "Delivery Failed"),
            }

            track17_service = get_tracking_service()
            updated = False

            for tracking_number, tracking_company in candidates.items():
                try:
                    track17_status = await track17_service.get_status(tracking_number, tracking_company)
                except Exception as exc:
                    logger.warning(f"17track 查询失败: {tracking_number}, {exc}")
                    continue

                if not track17_status:
                    continue

                delivery_status = None
                if track17_status == TrackingStatus.DELIVERED:
                    delivery_status = "success"
                elif track17_status == TrackingStatus.IN_TRANSIT:
                    delivery_status = "in_transit"
                elif track17_status == TrackingStatus.OUT_FOR_DELIVERY:
                    delivery_status = "out_for_delivery"
                elif track17_status in (TrackingStatus.ALERT, TrackingStatus.UNDELIVERED, TrackingStatus.EXPIRED):
                    delivery_status = "failure"

                if not delivery_status:
                    continue

                status_zh, status_en = status_text_map[delivery_status]

                for item in line_items:
                    if item.get("tracking_number") != tracking_number:
                        continue
                    if item.get("delivery_status"):
                        continue
                    if item.get("fulfillment_status") != "fulfilled":
                        continue
                    item["delivery_status"] = delivery_status
                    item["delivery_status_zh"] = status_zh
                    item["delivery_status_en"] = status_en
                    updated = True

            return updated

        # 尝试从缓存获取
        if use_cache:
            cached_order = await self.cache.get_order_by_number(order_number)
            if cached_order is not None:
                # 检查是否是"不存在"标记
                if cached_order.get("_not_found"):
                    logger.info(f"🎯 缓存命中: 订单不存在 ({self.site_code}:{order_number})")
                    return None

                # 缓存命中：对“已发货但实际已收货”的情况做 17track 补全，并回写缓存
                try:
                    updated = await enrich_cached_delivery_status(cached_order)
                    if updated:
                        await self.cache.set_order_by_number(order_number, cached_order)
                        order_id = cached_order.get("order_id")
                        if order_id:
                            await self.cache.set_order_detail(str(order_id), cached_order)
                except Exception as exc:
                    logger.warning(f"缓存订单状态补全失败: {self.site_code}:{order_number}, {exc}")

                logger.info(f"🎯 缓存命中: 订单搜索 ({self.site_code}:{order_number})")
                return {
                    "order": cached_order,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_detail"],
                    "site_code": self.site_code
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单搜索 ({self.site_code}:{order_number})")
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
            "cache_ttl": self.cache.ttl["order_detail"],
            "site_code": self.site_code
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
                logger.info(f"🎯 缓存命中: 订单详情 ({self.site_code}:{order_id})")
                return {
                    "order": cached_order,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_detail"],
                    "site_code": self.site_code
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单详情 ({self.site_code}:{order_id})")
        order = await self.client.get_order_detail(order_id)

        # 转换为字典
        order_data = order.model_dump()

        # 保存到缓存
        if use_cache:
            await self.cache.set_order_detail(order_id, order_data)

        return {
            "order": order_data,
            "cached": False,
            "cache_ttl": self.cache.ttl["order_detail"],
            "site_code": self.site_code
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
                logger.info(f"🎯 缓存命中: 物流信息 ({self.site_code}:{order_id})")
                return {
                    "tracking": cached_tracking,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["tracking"],
                    "site_code": self.site_code
                }

        # 缓存未命中，获取订单详情提取物流信息
        logger.info(f"🔄 调用 Shopify API: 物流信息 ({self.site_code}:{order_id})")
        order = await self.client.get_order_detail(order_id)

        # 提取物流信息
        tracking_data = {
            "order_id": order.order_id,
            "order_number": order.order_number,
            "fulfillment_status": order.fulfillment_status,
            "fulfillments": [f.model_dump() for f in order.fulfillments],
            "site_code": self.site_code
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
            "cache_ttl": self.cache.ttl["tracking"],
            "site_code": self.site_code
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
                logger.info(f"🎯 缓存命中: 订单数量 ({self.site_code}:{status})")
                return {
                    "count": cached_count,
                    "status": status,
                    "cached": True,
                    "cache_ttl": self.cache.ttl["order_count"],
                    "site_code": self.site_code
                }

        # 缓存未命中，调用 Shopify API
        logger.info(f"🔄 调用 Shopify API: 订单数量 ({self.site_code}:{status})")
        count = await self.client.get_order_count(status=status)

        # 保存到缓存
        if use_cache:
            await self.cache.set_order_count(status, count)

        return {
            "count": count,
            "status": status,
            "cached": False,
            "cache_ttl": self.cache.ttl["order_count"],
            "site_code": self.site_code
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
            "site_code": self.site_code,
            "api": api_health,
            "cache": cache_stats
        }


# ==================== 服务工厂 ====================

_services: Dict[str, ShopifyService] = {}


def get_shopify_service(site_code: str) -> ShopifyService:
    """
    获取 Shopify 服务实例（单例模式，按站点缓存）

    Args:
        site_code: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)

    Returns:
        对应站点的服务实例

    Raises:
        ShopifyAPIError: 如果站点未配置
    """
    global _services

    code = site_code.lower().strip()

    if code not in _services:
        # 验证站点是否已配置
        config = get_site_config(code)
        if not config:
            raise ShopifyAPIError(
                ERROR_CODES["SITE_NOT_CONFIGURED"]["code"],
                f"站点 {code.upper()} 未配置或 Access Token 缺失"
            )
        _services[code] = ShopifyService(code)

    return _services[code]


async def search_order_across_sites(
    order_number: str,
    use_cache: bool = True
) -> Optional[Dict[str, Any]]:
    """
    跨站点搜索订单

    根据订单号前缀自动检测站点，或遍历所有站点搜索

    Args:
        order_number: 订单号
        use_cache: 是否使用缓存

    Returns:
        包含订单详情和站点信息的字典，如果未找到返回 None
    """
    # 首先尝试自动检测站点
    detected_site = detect_site_from_order_number(order_number)
    if detected_site:
        try:
            service = get_shopify_service(detected_site)
            result = await service.search_order_by_number(order_number, use_cache)
            if result:
                return result
        except ShopifyAPIError:
            pass

    # 如果自动检测失败，遍历所有已配置站点
    configured_sites = get_all_configured_sites()
    for site_code in configured_sites:
        if site_code == detected_site:
            continue  # 跳过已尝试的站点

        try:
            service = get_shopify_service(site_code)
            result = await service.search_order_by_number(order_number, use_cache)
            if result:
                return result
        except ShopifyAPIError:
            continue

    return None


async def get_all_sites_health() -> Dict[str, Any]:
    """
    获取所有已配置站点的健康状态

    Returns:
        各站点健康状态
    """
    configured_sites = get_all_configured_sites()
    health_status = {}

    for site_code in configured_sites:
        try:
            service = get_shopify_service(site_code)
            health_status[site_code] = await service.health_check()
        except ShopifyAPIError as e:
            health_status[site_code] = {
                "status": "error",
                "error": e.message,
                "code": e.code
            }
        except Exception as e:
            health_status[site_code] = {
                "status": "error",
                "error": str(e)
            }

    return health_status


def get_configured_sites_list() -> List[Dict[str, str]]:
    """
    获取所有已配置站点列表

    Returns:
        站点信息列表
    """
    configured = get_all_configured_sites()
    return [
        {
            "code": config.code,
            "name": config.name,
            "shop_domain": config.shop_domain,
            "currency": config.currency
        }
        for config in configured.values()
    ]


async def search_orders_by_email_across_sites(
    email: str,
    limit: int = 10,
    use_cache: bool = True
) -> Dict[str, Any]:
    """
    跨站点按邮箱搜索订单

    遍历所有已配置站点，汇总该邮箱的所有订单。

    Args:
        email: 客户邮箱
        limit: 每个站点返回的订单数量限制
        use_cache: 是否使用缓存

    Returns:
        包含所有站点订单的汇总结果
    """
    configured_sites = get_all_configured_sites()
    all_orders = []
    sites_searched = []
    sites_with_orders = []

    for site_code in configured_sites:
        try:
            service = get_shopify_service(site_code)
            result = await service.get_orders_by_email(email, limit=limit, use_cache=use_cache)

            sites_searched.append(site_code)

            if result.get("orders"):
                # 为每个订单添加站点信息（如果尚未添加）
                for order in result["orders"]:
                    if "site_code" not in order:
                        order["site_code"] = site_code
                all_orders.extend(result["orders"])
                sites_with_orders.append(site_code)

        except ShopifyAPIError as e:
            logger.warning(f"站点 {site_code} 查询失败: {e.message}")
            continue
        except Exception as e:
            logger.warning(f"站点 {site_code} 查询异常: {str(e)}")
            continue

    # 按创建时间倒序排序
    all_orders.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return {
        "orders": all_orders[:limit * 2],  # 返回合理数量的订单
        "total": len(all_orders),
        "email": email,
        "sites_searched": sites_searched,
        "sites_with_orders": sites_with_orders,
        "cached": False  # 汇总结果不标记缓存状态
    }
