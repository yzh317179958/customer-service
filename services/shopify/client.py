"""
Shopify 多站点 API 客户端

支持所有 Fiido Shopify 店铺的订单查询功能。
仅支持只读操作（read_orders, read_shipping 权限）。

遵循 CLAUDE.md 规范：
- 使用连接池限制并发
- 实现速率限制 (2次/秒)
- 完善的错误处理
"""

import os
import time
import asyncio
import logging
from typing import Optional, Dict, Any, List

import httpx
from pydantic import BaseModel

from services.shopify.sites import ShopifySiteConfig, get_site_config

logger = logging.getLogger(__name__)


# ==================== 数据模型 ====================

class ShopifyAddress(BaseModel):
    """收货地址"""
    address1: Optional[str] = None
    address2: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    country: Optional[str] = None
    zip: Optional[str] = None


class ShopifyLineItem(BaseModel):
    """订单商品项"""
    title: str
    variant_title: Optional[str] = None
    sku: Optional[str] = None
    quantity: int
    price: str
    fulfillment_status: Optional[str] = None  # 商品级别发货状态: fulfilled/null
    delivery_status: Optional[str] = None  # 送达状态: success(已送达)/pending/in_transit/failure
    delivery_status_zh: Optional[str] = None  # 状态文本（中文）
    delivery_status_en: Optional[str] = None  # 状态文本（英文）
    tracking_company: Optional[str] = None  # 承运商
    tracking_number: Optional[str] = None  # 运单号
    tracking_url: Optional[str] = None  # 追踪链接
    image_url: Optional[str] = None  # 商品图片 URL
    product_url: Optional[str] = None  # 商品详情页 URL


class FulfillmentLineItem(BaseModel):
    """发货记录中的商品项"""
    title: str
    quantity: int


class ShopifyFulfillment(BaseModel):
    """发货信息"""
    id: int
    status: str
    tracking_company: Optional[str] = None
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    created_at: Optional[str] = None
    line_items: List[FulfillmentLineItem] = []  # 该发货记录包含的商品


class PrimaryProduct(BaseModel):
    """主商品信息（用于订单列表展示）"""
    title: str
    image_url: Optional[str] = None
    product_url: Optional[str] = None


class ShopifyOrderSummary(BaseModel):
    """订单摘要"""
    order_id: str
    order_number: str
    created_at: str
    financial_status: str
    fulfillment_status: Optional[str] = None
    total_price: str
    currency: str
    items_count: int
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    primary_product: Optional[PrimaryProduct] = None  # 主商品（用于图文展示）
    site_code: Optional[str] = None  # 站点代码


class ShopifyOrderDetail(ShopifyOrderSummary):
    """订单详情"""
    line_items: List[ShopifyLineItem] = []
    subtotal_price: Optional[str] = None
    total_shipping: Optional[str] = None
    total_discounts: Optional[str] = None
    total_tax: Optional[str] = None
    shipping_address: Optional[ShopifyAddress] = None
    fulfillments: List[ShopifyFulfillment] = []
    note: Optional[str] = None
    tags: Optional[str] = None
    discount_codes: List[str] = []


# ==================== 错误定义 ====================

class ShopifyAPIError(Exception):
    """Shopify API 错误"""
    def __init__(self, code: int, message: str, details: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        super().__init__(f"[{code}] {message}")


ERROR_CODES = {
    "SHOPIFY_API_ERROR": {"code": 5001, "message": "Shopify API 调用失败"},
    "ORDER_NOT_FOUND": {"code": 5002, "message": "订单不存在"},
    "INVALID_ORDER_NUMBER": {"code": 5003, "message": "无效的订单号格式"},
    "RATE_LIMITED": {"code": 5004, "message": "请求过于频繁，请稍后重试"},
    "TOKEN_INVALID": {"code": 5005, "message": "API Token 无效或已过期"},
    "PERMISSION_DENIED": {"code": 5006, "message": "权限不足"},
    "SITE_NOT_CONFIGURED": {"code": 5007, "message": "站点未配置"},
}


# ==================== API 客户端 ====================

class ShopifyClient:
    """
    Shopify 多站点 API 客户端

    特点：
    - 速率限制: 2次/秒 (Shopify 标准计划限制)
    - 连接池: 复用 HTTP 连接
    - 超时保护: 连接 5s，读取 30s
    - 多站点支持: 通过 site_code 参数切换站点
    """

    def __init__(self, site_config: ShopifySiteConfig):
        """
        初始化 Shopify 客户端

        Args:
            site_config: 站点配置对象
        """
        self.site_config = site_config
        self.shop_domain = site_config.shop_domain
        self.access_token = site_config.access_token
        self.api_version = site_config.api_version
        self.site_code = site_config.code
        self.base_url = site_config.base_url

        # 速率限制: 2次/秒
        self._rate_limiter = asyncio.Semaphore(2)
        self._last_request_time = 0.0
        self._min_request_interval = 0.5  # 500ms

        # HTTP 客户端配置
        self._timeout = httpx.Timeout(
            connect=5.0,
            read=30.0,
            write=10.0,
            pool=10.0
        )

        logger.info(f"✅ Shopify {self.site_code.upper()} 客户端初始化: {self.shop_domain}")

    async def _wait_for_rate_limit(self):
        """等待速率限制"""
        elapsed = time.time() - self._last_request_time
        if elapsed < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - elapsed)
        self._last_request_time = time.time()

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        发送 HTTP 请求（带速率限制）

        Args:
            method: HTTP 方法
            endpoint: API 端点 (如 /orders.json)
            params: 查询参数

        Returns:
            响应 JSON 数据
        """
        if not self.access_token:
            raise ShopifyAPIError(
                ERROR_CODES["TOKEN_INVALID"]["code"],
                f"Shopify {self.site_code.upper()} Access Token 未配置"
            )

        async with self._rate_limiter:
            await self._wait_for_rate_limit()

            headers = {
                "X-Shopify-Access-Token": self.access_token,
                "Content-Type": "application/json"
            }

            url = f"{self.base_url}{endpoint}"

            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    response = await client.request(
                        method,
                        url,
                        headers=headers,
                        params=params,
                        **kwargs
                    )

                    # 处理错误响应
                    if response.status_code == 401:
                        raise ShopifyAPIError(
                            ERROR_CODES["TOKEN_INVALID"]["code"],
                            ERROR_CODES["TOKEN_INVALID"]["message"]
                        )
                    elif response.status_code == 403:
                        raise ShopifyAPIError(
                            ERROR_CODES["PERMISSION_DENIED"]["code"],
                            ERROR_CODES["PERMISSION_DENIED"]["message"]
                        )
                    elif response.status_code == 404:
                        raise ShopifyAPIError(
                            ERROR_CODES["ORDER_NOT_FOUND"]["code"],
                            ERROR_CODES["ORDER_NOT_FOUND"]["message"]
                        )
                    elif response.status_code == 429:
                        raise ShopifyAPIError(
                            ERROR_CODES["RATE_LIMITED"]["code"],
                            ERROR_CODES["RATE_LIMITED"]["message"]
                        )
                    elif response.status_code >= 400:
                        raise ShopifyAPIError(
                            ERROR_CODES["SHOPIFY_API_ERROR"]["code"],
                            f"Shopify API 错误: {response.status_code}",
                            {"status_code": response.status_code, "body": response.text}
                        )

                    return response.json()

            except httpx.TimeoutException:
                raise ShopifyAPIError(
                    ERROR_CODES["SHOPIFY_API_ERROR"]["code"],
                    "请求超时"
                )
            except httpx.RequestError as e:
                raise ShopifyAPIError(
                    ERROR_CODES["SHOPIFY_API_ERROR"]["code"],
                    f"网络请求失败: {str(e)}"
                )

    # ==================== 订单查询方法 ====================

    async def get_orders_by_email(
        self,
        email: str,
        limit: int = 10,
        status: str = "any"
    ) -> List[ShopifyOrderSummary]:
        """
        按客户邮箱查询订单列表

        Args:
            email: 客户邮箱
            limit: 返回数量限制 (1-250)
            status: 订单状态筛选 (open/closed/cancelled/any)

        Returns:
            订单摘要列表
        """
        params = {
            "email": email,
            "limit": min(limit, 250),
            "status": status,
            "fields": "id,name,created_at,financial_status,fulfillment_status,"
                      "total_price,currency,line_items,customer"
        }

        data = await self._request("GET", "/orders.json", params=params)
        orders = data.get("orders", [])

        return [self._parse_order_summary(order) for order in orders]

    async def search_order_by_number(
        self,
        order_number: str
    ) -> Optional[ShopifyOrderDetail]:
        """
        按订单号搜索订单

        Args:
            order_number: 订单号 (支持 #UK22080 或 UK22080 格式)

        Returns:
            订单详情，如果不存在返回 None
        """
        # 兼容 Shopify 订单名通常带 "#" 前缀：#UK22080
        raw = (order_number or "").strip()
        if not raw:
            return None

        normalized = raw.lstrip("#")
        candidates = []
        # 优先尝试原始输入格式，避免一些店铺只认带 # 的 name
        candidates.append(raw)
        candidates.append(normalized)
        if not raw.startswith("#"):
            candidates.append(f"#{normalized}")

        seen = set()
        orders = []
        for candidate in candidates:
            candidate = (candidate or "").strip()
            if not candidate or candidate in seen:
                continue
            seen.add(candidate)

            params = {
                "name": candidate,
                "status": "any",
                "limit": 1
            }

            data = await self._request("GET", "/orders.json", params=params)
            orders = data.get("orders", [])
            if orders:
                break

        if not orders:
            return None

        # 获取订单 ID，然后调用 get_order_detail 获取完整数据（包含 refunds）
        # /orders.json 默认不返回 refunds 字段，需要通过 /orders/{id}.json 获取
        order_id = orders[0].get("id")
        if order_id:
            return await self.get_order_detail(str(order_id))

        # 降级：直接解析（带 17track 缓存查询）
        return await self._parse_order_detail_with_tracking(orders[0])

    async def get_order_detail(self, order_id: str) -> ShopifyOrderDetail:
        """
        获取订单详情

        Args:
            order_id: Shopify 订单 ID

        Returns:
            订单详情
        """
        data = await self._request("GET", f"/orders/{order_id}.json")
        order = data.get("order")

        if not order:
            raise ShopifyAPIError(
                ERROR_CODES["ORDER_NOT_FOUND"]["code"],
                ERROR_CODES["ORDER_NOT_FOUND"]["message"]
            )

        # 使用带 17track 缓存查询的版本
        return await self._parse_order_detail_with_tracking(order)

    async def get_order_count(
        self,
        status: str = "any",
        financial_status: Optional[str] = None
    ) -> int:
        """
        获取订单数量统计

        Args:
            status: 订单状态
            financial_status: 支付状态

        Returns:
            订单数量
        """
        params = {"status": status}
        if financial_status:
            params["financial_status"] = financial_status

        data = await self._request("GET", "/orders/count.json", params=params)
        return data.get("count", 0)

    # ==================== 数据解析方法 ====================

    def _parse_order_summary(self, order: Dict) -> ShopifyOrderSummary:
        """解析订单摘要"""
        customer = order.get("customer", {}) or {}
        line_items = order.get("line_items", [])

        # 提取主商品信息（优先选择电动车，其次是配件）
        primary_product = None
        service_keywords = ['worry-free', 'protection', 'insurance', 'warranty', 'service']

        # 电动车产品关键词（Fiido 产品线）
        ebike_keywords = ['titan', 'c11', 'c21', 'c22', 'air', 'd3', 'd11', 'd21',
                         'l3', 'm1', 'nomads', 't1', 't2', 'ebike', 'e-bike', 'electric bike']

        ebike_item = None  # 电动车商品
        accessory_item = None  # 配件商品（备选）

        for item in line_items:
            title = item.get("title", "")
            title_lower = title.lower()

            # 跳过服务类商品
            if any(kw in title_lower for kw in service_keywords):
                continue

            # 判断是否是电动车
            is_ebike = any(kw in title_lower for kw in ebike_keywords)

            if is_ebike and ebike_item is None:
                ebike_item = item
            elif not is_ebike and accessory_item is None:
                accessory_item = item

            # 如果已经找到电动车，可以提前退出
            if ebike_item is not None:
                break

        # 优先使用电动车，其次使用配件
        selected_item = ebike_item or accessory_item

        if selected_item:
            title = selected_item.get("title", "")
            # 通过商品名称关键词匹配图片 URL
            image_url = self._get_product_image_by_title(title)

            # 构建商品详情页 URL
            product_url = None
            product_id = selected_item.get("product_id")
            if product_id:
                product_url = f"https://www.fiido.com/products/{product_id}"

            primary_product = PrimaryProduct(
                title=title,
                image_url=image_url,
                product_url=product_url
            )

        return ShopifyOrderSummary(
            order_id=str(order.get("id")),
            order_number=order.get("name", ""),
            created_at=order.get("created_at", ""),
            financial_status=order.get("financial_status", ""),
            fulfillment_status=order.get("fulfillment_status"),
            total_price=order.get("total_price", "0"),
            currency=order.get("currency", self.site_config.currency),
            items_count=sum(item.get("quantity", 0) for item in line_items),
            customer_email=customer.get("email"),
            customer_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            primary_product=primary_product,
            site_code=self.site_code
        )

    def _get_product_image_by_title(self, title: str) -> Optional[str]:
        """根据商品名称关键词匹配图片 URL"""
        title_lower = title.lower()

        # 产品图片映射表（按优先级排序）
        product_images = [
            ("titan", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-titan.webp?v=1755064725"),
            ("c11 pro", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11-pro_dce92f31-e919-4a94-b8b0-f9cb9b037d75.webp?v=1740465827"),
            ("c11", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-c11.png?v=1763374439"),
            ("c21", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-L.webp?v=1739848641"),
            ("c22", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1-L.webp?v=1739848641"),
            ("air", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/c31-img-1.webp?v=1750820407"),
            ("d3 pro", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/d3pro-2024-1.jpg?v=1709777461"),
            ("d3", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/d3pro-2024-1.jpg?v=1709777461"),
            ("d11", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/d11-2024-1.webp?v=1709777461"),
            ("d21", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/d11-2024-1.webp?v=1709777461"),
            ("l3", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/l3-main-1.jpg?v=1727161438"),
            ("m1 pro", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee.webp?v=1755851713"),
            ("m1", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/7-m1-pro_a8e3269b-7ec7-4f38-a211-1cb2649c18ee.webp?v=1755851713"),
            ("nomads", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/11-sunstone-yellow-m.webp?v=1751939345"),
            ("t1", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/t1pro-main-1_56e88db4-5144-4e04-bf86-310a6bfa75d8.jpg?v=1719560237"),
            ("t2", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/t2-main-1-green.jpg?v=1712557682"),
        ]

        # 配件图片映射表
        accessory_images = [
            ("pannier bag", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/bike-rack-pannier-bag.jpg?v=1690970482"),
            ("rack bag", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/bike-rack-pannier-bag.jpg?v=1690970482"),
            ("helmet", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/1_2e3a8c93-9e21-42ba-9e2d-20185a8446eb.jpg?v=1710150097"),
            ("brake pad", "https://cdn.shopify.com/s/files/1/0511/3308/7940/products/Fiido-Electric-Bike-BrakePads.jpg?v=1656662379"),
            ("charger", "https://cdn.shopify.com/s/files/1/0511/3308/7940/products/Fiido-Electric-Bike-Charger-for-EU.jpg?v=1656905714"),
            ("fender", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/M1_a985f037-e887-4f3c-8d49-8338e04bce73.jpg?v=1723106303"),
            ("phone holder", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/phone-holder.jpg?v=1690970482"),
            ("battery", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/battery-pack.jpg?v=1690970482"),
            ("basket", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/front-basket.jpg?v=1690970482"),
            ("mirror", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/rearview-mirror.jpg?v=1690970482"),
            ("cap", "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/fiido-cap.jpg?v=1690970482"),
        ]

        # 先匹配产品
        for keyword, url in product_images:
            if keyword in title_lower:
                return url

        # 再匹配配件
        for keyword, url in accessory_images:
            if keyword in title_lower:
                return url

        return None

    def _is_service_product(self, title: str, sku: str) -> bool:
        """
        判断是否为服务类商品（无需物流发货）

        Args:
            title: 商品名称
            sku: 商品SKU

        Returns:
            True 如果是服务类商品
        """
        title_lower = title.lower()
        sku_lower = sku.lower() if sku else ""

        # 服务类商品关键词
        service_keywords = [
            "worry-free",
            "worry free",
            "seel",
            "warranty",
            "protection",
            "insurance",
            "extended warranty",
            "service plan",
        ]

        # SKU 前缀
        service_skus = [
            "seel",
            "wfp",
            "warranty",
        ]

        # 匹配名称
        for keyword in service_keywords:
            if keyword in title_lower:
                return True

        # 匹配 SKU
        for sku_prefix in service_skus:
            if sku_lower.startswith(sku_prefix):
                return True

        return False

    def _translate_delivery_status(
        self,
        delivery_status: Optional[str],
        fulfillment_status: Optional[str]
    ) -> tuple:
        """
        翻译商品状态为中英文文本

        Args:
            delivery_status: 送达/退款状态
            fulfillment_status: 发货状态

        Returns:
            (中文状态, 英文状态) 元组
        """
        # 状态翻译映射表
        status_map = {
            # 退款相关状态
            "returned": ("已退货退款", "Returned & Refunded"),
            "refunded": ("已退款", "Refunded"),
            "cancelled": ("已取消", "Cancelled"),
            "expired": ("已失效", "Expired"),
            # 服务类商品状态
            "active": ("已生效", "Active"),
            "pending": ("待支付", "Payment Pending"),
            # 物流状态
            "success": ("已收货", "Received"),
            "in_transit": ("运输中", "In Transit"),
            "out_for_delivery": ("派送中", "Out for Delivery"),
            "failure": ("投递失败", "Delivery Failed"),
        }

        # 优先使用 delivery_status
        if delivery_status and delivery_status in status_map:
            return status_map[delivery_status]

        # 其次使用 fulfillment_status
        if fulfillment_status == "fulfilled":
            return ("已发货", "Shipped")

        # 默认待发货
        return ("待发货", "Pending")

    def _parse_order_detail(self, order: Dict) -> ShopifyOrderDetail:
        """
        解析订单详情（同步版本，不查询 17track 缓存）

        注意：此方法是同步的，无法查询 17track 缓存。
        如需补充 17track 状态，请使用异步版本 _parse_order_detail_with_tracking()
        """
        return self._parse_order_detail_impl(order, track17_service=None)

    async def _parse_order_detail_with_tracking(self, order: Dict) -> ShopifyOrderDetail:
        """
        解析订单详情（异步版本，支持 17track 状态查询）

        当 Shopify 的 shipment_status 为空时，会主动查询 17track API
        获取真实的物流状态。

        Args:
            order: Shopify 订单原始数据

        Returns:
            ShopifyOrderDetail 对象
        """
        # 延迟导入避免循环依赖
        from services.tracking import get_tracking_service
        track17_service = get_tracking_service()
        return await self._parse_order_detail_impl_async(order, track17_service=track17_service)

    def _parse_order_detail_impl(
        self,
        order: Dict,
        track17_service=None,
    ) -> ShopifyOrderDetail:
        """
        解析订单详情的核心实现

        Args:
            order: Shopify 订单原始数据
            track17_service: TrackingService 实例（可选，用于查询 17track 缓存）

        Returns:
            ShopifyOrderDetail 对象
        """
        summary = self._parse_order_summary(order)

        # 获取订单支付状态，用于服务类商品状态判断
        financial_status = order.get("financial_status", "")

        # 先解析发货信息，用于后续匹配商品的送达状态
        fulfillments_raw = order.get("fulfillments", [])

        # 构建商品名称到发货信息的映射
        # key: 商品title, value: {status, shipment_status, tracking_company, tracking_number, tracking_url}
        # 注意：
        #   - status: 发货操作状态 (success=发货成功, pending=待发货)
        #   - shipment_status: 物流运输状态 (delivered=已送达, in_transit=运输中, out_for_delivery=派送中)
        item_fulfillment_map = {}
        for f in fulfillments_raw:
            f_status = f.get("status", "")  # 发货操作状态
            f_shipment_status = f.get("shipment_status")  # 物流运输状态（真正的送达状态）
            f_company = f.get("tracking_company")
            f_number = f.get("tracking_number")
            f_url = f.get("tracking_url")
            for item in f.get("line_items", []):
                item_title = item.get("title", "")
                if item_title:
                    item_fulfillment_map[item_title] = {
                        "status": f_status,
                        "shipment_status": f_shipment_status,
                        "tracking_company": f_company,
                        "tracking_number": f_number,
                        "tracking_url": f_url
                    }

        # 解析退款信息，构建商品级退款映射
        # key: 商品title, value: {refunded: True, restock_type: return/cancel/no_restock}
        item_refund_map = {}
        refunds = order.get("refunds", [])
        for refund in refunds:
            for refund_line_item in refund.get("refund_line_items", []):
                line_item = refund_line_item.get("line_item", {})
                item_title = line_item.get("title", "")
                if item_title:
                    item_refund_map[item_title] = {
                        "refunded": True,
                        "restock_type": refund_line_item.get("restock_type", ""),
                        "quantity": refund_line_item.get("quantity", 0)
                    }

        # 统计实物商品（非服务类）的退款情况，用于判断服务类商品状态
        all_line_items = order.get("line_items", [])
        physical_items_count = 0
        physical_items_refunded_count = 0
        for item in all_line_items:
            item_title = item.get("title", "")
            item_sku = item.get("sku", "")
            if not self._is_service_product(item_title, item_sku):
                physical_items_count += 1
                if item_title in item_refund_map:
                    physical_items_refunded_count += 1

        # 判断是否所有实物商品都已退款
        all_physical_refunded = (physical_items_count > 0 and
                                  physical_items_refunded_count == physical_items_count)

        # 解析商品列表（包含商品级别的发货状态和送达状态）
        line_items = []
        for item in order.get("line_items", []):
            item_title = item.get("title", "")
            item_sku = item.get("sku", "")

            # 判断是否为服务类商品（无需物流发货）
            is_service_product = self._is_service_product(item_title, item_sku)

            # 从发货记录中获取该商品的送达状态和物流信息
            fulfillment_info = item_fulfillment_map.get(item_title, {})

            # 获取商品退款信息
            refund_info = item_refund_map.get(item_title, {})
            is_refunded = refund_info.get("refunded", False)
            restock_type = refund_info.get("restock_type", "")

            # 服务类商品状态判断
            if is_service_product:
                # 服务类商品跟随订单整体状态：
                # - 只有所有实物商品都退款了，服务类商品才显示退款
                # - 否则显示已生效
                if all_physical_refunded or financial_status == "refunded":
                    service_status = "expired"  # 已失效（服务类商品随实物退款后失效）
                elif financial_status == "paid":
                    service_status = "active"  # 已生效
                elif financial_status == "pending":
                    service_status = "pending"
                else:
                    service_status = "active" if financial_status else "pending"

                delivery_status = service_status
                fulfillment_status = "service"  # 标记为服务类商品
            else:
                # 实物商品状态判断
                # 优先级：退款状态 > 送达状态 > 发货状态
                if is_refunded:
                    # 根据 restock_type 决定退款类型
                    if restock_type == "return":
                        delivery_status = "returned"  # 退货退款
                    elif restock_type == "cancel":
                        delivery_status = "cancelled"  # 取消退款（未发货）
                    else:
                        delivery_status = "refunded"  # 仅退款（no_restock 或其他）
                    fulfillment_status = item.get("fulfillment_status")
                else:
                    # 状态判断优先级：shipment_status > status > fulfillment_status
                    # - shipment_status: 物流运输状态（真正的送达状态）
                    #   - delivered: 已送达（对应"已收货"）
                    #   - in_transit: 运输中
                    #   - out_for_delivery: 派送中
                    #   - failure: 投递失败
                    # - status: 发货操作状态（success=发货成功，不是送达成功）
                    # - fulfillment_status: 商品发货状态（fulfilled/null）

                    shipment_status = fulfillment_info.get("shipment_status")
                    f_status = fulfillment_info.get("status")

                    if shipment_status:
                        # 优先使用物流运输状态
                        # 将 Shopify shipment_status 映射到我们的 delivery_status
                        if shipment_status == "delivered":
                            delivery_status = "success"  # 已送达 → 已收货
                        else:
                            delivery_status = shipment_status  # in_transit, out_for_delivery, failure 等
                    elif f_status == "success":
                        # 发货成功但没有 shipment_status，说明已发货但物流状态未知
                        # 【增强】尝试从 17track 缓存获取真实状态
                        tracking_number = fulfillment_info.get("tracking_number")
                        track17_status = None
                        if tracking_number and track17_service:
                            track17_status = track17_service.get_cached_status_sync(tracking_number)

                        if track17_status:
                            # 17track 有缓存数据，使用它来补充状态
                            from services.tracking import TrackingStatus
                            if track17_status == TrackingStatus.DELIVERED:
                                delivery_status = "success"  # 17track 显示已送达 → 已收货
                            elif track17_status == TrackingStatus.IN_TRANSIT:
                                delivery_status = "in_transit"  # 运输中
                            elif track17_status == TrackingStatus.OUT_FOR_DELIVERY:
                                delivery_status = "out_for_delivery"  # 派送中
                            elif track17_status in (TrackingStatus.ALERT, TrackingStatus.UNDELIVERED):
                                delivery_status = "failure"  # 异常/投递失败
                            else:
                                # 其他状态，保持"已发货"
                                delivery_status = None
                        else:
                            # 无 17track 缓存，保持原有逻辑
                            delivery_status = None  # 让前端根据 fulfillment_status 显示"已发货"
                    else:
                        delivery_status = f_status if f_status else None

                    fulfillment_status = item.get("fulfillment_status")

            # 翻译 delivery_status 为中英文状态文本
            status_zh, status_en = self._translate_delivery_status(delivery_status, fulfillment_status)

            # 获取商品图片和链接
            image_url = self._get_product_image_by_title(item_title)
            product_url = None
            product_id = item.get("product_id")
            if product_id:
                product_url = f"https://www.fiido.com/products/{product_id}"

            line_items.append(ShopifyLineItem(
                title=item_title,
                variant_title=item.get("variant_title"),
                sku=item_sku,
                quantity=item.get("quantity", 1),
                price=item.get("price", "0"),
                fulfillment_status=fulfillment_status,
                delivery_status=delivery_status,
                delivery_status_zh=status_zh,
                delivery_status_en=status_en,
                tracking_company=fulfillment_info.get("tracking_company") if not is_service_product else None,
                tracking_number=fulfillment_info.get("tracking_number") if not is_service_product else None,
                tracking_url=fulfillment_info.get("tracking_url") if not is_service_product else None,
                image_url=image_url,
                product_url=product_url
            ))

        # 解析收货地址
        shipping = order.get("shipping_address") or {}
        shipping_address = ShopifyAddress(
            address1=shipping.get("address1"),
            address2=shipping.get("address2"),
            city=shipping.get("city"),
            province=shipping.get("province"),
            country=shipping.get("country"),
            zip=shipping.get("zip")
        ) if shipping else None

        # 解析发货信息（包含每个发货记录的商品列表）
        fulfillments = []
        for f in order.get("fulfillments", []):
            # 提取该发货记录包含的商品
            fulfillment_line_items = [
                FulfillmentLineItem(
                    title=item.get("title", ""),
                    quantity=item.get("quantity", 1)
                )
                for item in f.get("line_items", [])
            ]
            fulfillments.append(ShopifyFulfillment(
                id=f.get("id"),
                status=f.get("status", ""),
                tracking_company=f.get("tracking_company"),
                tracking_number=f.get("tracking_number"),
                tracking_url=f.get("tracking_url"),
                created_at=f.get("created_at"),
                line_items=fulfillment_line_items
            ))

        # 解析折扣码
        discount_codes = [
            dc.get("code", "") for dc in order.get("discount_codes", [])
        ]

        return ShopifyOrderDetail(
            **summary.model_dump(),
            line_items=line_items,
            subtotal_price=order.get("subtotal_price"),
            total_shipping=order.get("total_shipping_price_set", {}).get(
                "shop_money", {}
            ).get("amount"),
            total_discounts=order.get("total_discounts"),
            total_tax=order.get("total_tax"),
            shipping_address=shipping_address,
            fulfillments=fulfillments,
            note=order.get("note"),
            tags=order.get("tags"),
            discount_codes=discount_codes
        )

    async def _parse_order_detail_impl_async(
        self,
        order: Dict,
        track17_service=None,
    ) -> ShopifyOrderDetail:
        """
        解析订单详情的异步版本（支持主动查询 17track API）

        当 Shopify 的 shipment_status 为空时，会主动调用 17track API
        获取真实的物流状态，而不是只依赖缓存。

        Args:
            order: Shopify 订单原始数据
            track17_service: TrackingService 实例

        Returns:
            ShopifyOrderDetail 对象
        """
        summary = self._parse_order_summary(order)
        financial_status = order.get("financial_status", "")
        fulfillments_raw = order.get("fulfillments", [])

        # 构建商品名称到发货信息的映射
        item_fulfillment_map = {}
        for f in fulfillments_raw:
            f_status = f.get("status", "")
            f_shipment_status = f.get("shipment_status")
            f_company = f.get("tracking_company")
            f_number = f.get("tracking_number")
            f_url = f.get("tracking_url")
            for item in f.get("line_items", []):
                item_title = item.get("title", "")
                if item_title:
                    item_fulfillment_map[item_title] = {
                        "status": f_status,
                        "shipment_status": f_shipment_status,
                        "tracking_company": f_company,
                        "tracking_number": f_number,
                        "tracking_url": f_url
                    }

        # 解析退款信息
        item_refund_map = {}
        refunds = order.get("refunds", [])
        for refund in refunds:
            for refund_line_item in refund.get("refund_line_items", []):
                line_item = refund_line_item.get("line_item", {})
                item_title = line_item.get("title", "")
                if item_title:
                    item_refund_map[item_title] = {
                        "refunded": True,
                        "restock_type": refund_line_item.get("restock_type", ""),
                        "quantity": refund_line_item.get("quantity", 0)
                    }

        # 统计实物商品退款情况
        all_line_items = order.get("line_items", [])
        physical_items_count = 0
        physical_items_refunded_count = 0
        for item in all_line_items:
            item_title = item.get("title", "")
            item_sku = item.get("sku", "")
            if not self._is_service_product(item_title, item_sku):
                physical_items_count += 1
                if item_title in item_refund_map:
                    physical_items_refunded_count += 1

        all_physical_refunded = (physical_items_count > 0 and
                                  physical_items_refunded_count == physical_items_count)

        # 解析商品列表
        line_items = []
        for item in order.get("line_items", []):
            item_title = item.get("title", "")
            item_sku = item.get("sku", "")
            is_service_product = self._is_service_product(item_title, item_sku)
            fulfillment_info = item_fulfillment_map.get(item_title, {})
            refund_info = item_refund_map.get(item_title, {})
            is_refunded = refund_info.get("refunded", False)
            restock_type = refund_info.get("restock_type", "")

            if is_service_product:
                # 服务类商品状态判断
                if all_physical_refunded or financial_status == "refunded":
                    service_status = "expired"
                elif financial_status == "paid":
                    service_status = "active"
                elif financial_status == "pending":
                    service_status = "pending"
                else:
                    service_status = "active" if financial_status else "pending"

                delivery_status = service_status
                fulfillment_status = "service"
            else:
                # 实物商品状态判断
                if is_refunded:
                    if restock_type == "return":
                        delivery_status = "returned"
                    elif restock_type == "cancel":
                        delivery_status = "cancelled"
                    else:
                        delivery_status = "refunded"
                    fulfillment_status = item.get("fulfillment_status")
                else:
                    shipment_status = fulfillment_info.get("shipment_status")
                    f_status = fulfillment_info.get("status")

                    if shipment_status:
                        if shipment_status == "delivered":
                            delivery_status = "success"
                        else:
                            delivery_status = shipment_status
                    elif f_status == "success":
                        # 发货成功但没有 shipment_status
                        # 【主动查询】调用 17track API 获取真实状态
                        tracking_number = fulfillment_info.get("tracking_number")
                        tracking_company = fulfillment_info.get("tracking_company")
                        track17_status = None

                        if tracking_number and track17_service:
                            try:
                                # 主动查询 17track API（会使用缓存）
                                track17_status = await track17_service.get_status(
                                    tracking_number, tracking_company
                                )
                            except Exception as e:
                                logger.warning(f"17track 查询失败: {tracking_number}, {e}")

                        if track17_status:
                            from services.tracking import TrackingStatus
                            if track17_status == TrackingStatus.DELIVERED:
                                delivery_status = "success"
                            elif track17_status == TrackingStatus.IN_TRANSIT:
                                delivery_status = "in_transit"
                            elif track17_status == TrackingStatus.OUT_FOR_DELIVERY:
                                delivery_status = "out_for_delivery"
                            elif track17_status in (TrackingStatus.ALERT, TrackingStatus.UNDELIVERED):
                                delivery_status = "failure"
                            else:
                                delivery_status = None
                        else:
                            delivery_status = None
                    else:
                        delivery_status = f_status if f_status else None

                    fulfillment_status = item.get("fulfillment_status")

            status_zh, status_en = self._translate_delivery_status(delivery_status, fulfillment_status)
            image_url = self._get_product_image_by_title(item_title)
            product_url = None
            product_id = item.get("product_id")
            if product_id:
                product_url = f"https://www.fiido.com/products/{product_id}"

            line_items.append(ShopifyLineItem(
                title=item_title,
                variant_title=item.get("variant_title"),
                sku=item_sku,
                quantity=item.get("quantity", 1),
                price=item.get("price", "0"),
                fulfillment_status=fulfillment_status,
                delivery_status=delivery_status,
                delivery_status_zh=status_zh,
                delivery_status_en=status_en,
                tracking_company=fulfillment_info.get("tracking_company") if not is_service_product else None,
                tracking_number=fulfillment_info.get("tracking_number") if not is_service_product else None,
                tracking_url=fulfillment_info.get("tracking_url") if not is_service_product else None,
                image_url=image_url,
                product_url=product_url
            ))

        # 解析收货地址
        shipping = order.get("shipping_address") or {}
        shipping_address = ShopifyAddress(
            address1=shipping.get("address1"),
            address2=shipping.get("address2"),
            city=shipping.get("city"),
            province=shipping.get("province"),
            country=shipping.get("country"),
            zip=shipping.get("zip")
        ) if shipping else None

        # 解析发货信息
        fulfillments = []
        for f in order.get("fulfillments", []):
            fulfillment_line_items = [
                FulfillmentLineItem(
                    title=item.get("title", ""),
                    quantity=item.get("quantity", 1)
                )
                for item in f.get("line_items", [])
            ]
            fulfillments.append(ShopifyFulfillment(
                id=f.get("id"),
                status=f.get("status", ""),
                tracking_company=f.get("tracking_company"),
                tracking_number=f.get("tracking_number"),
                tracking_url=f.get("tracking_url"),
                created_at=f.get("created_at"),
                line_items=fulfillment_line_items
            ))

        discount_codes = [
            dc.get("code", "") for dc in order.get("discount_codes", [])
        ]

        return ShopifyOrderDetail(
            **summary.model_dump(),
            line_items=line_items,
            subtotal_price=order.get("subtotal_price"),
            total_shipping=order.get("total_shipping_price_set", {}).get(
                "shop_money", {}
            ).get("amount"),
            total_discounts=order.get("total_discounts"),
            total_tax=order.get("total_tax"),
            shipping_address=shipping_address,
            fulfillments=fulfillments,
            note=order.get("note"),
            tags=order.get("tags"),
            discount_codes=discount_codes
        )

    # ==================== 健康检查 ====================

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查 - 验证 API 连接

        Returns:
            健康状态信息
        """
        try:
            count = await self.get_order_count(status="any")
            return {
                "status": "healthy",
                "site_code": self.site_code,
                "shop_domain": self.shop_domain,
                "api_version": self.api_version,
                "total_orders": count
            }
        except ShopifyAPIError as e:
            return {
                "status": "unhealthy",
                "site_code": self.site_code,
                "error": e.message,
                "code": e.code
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "site_code": self.site_code,
                "error": str(e)
            }


# ==================== 客户端工厂 ====================

_clients: Dict[str, ShopifyClient] = {}


def get_shopify_client(site_code: str) -> ShopifyClient:
    """
    获取 Shopify 客户端（单例模式，按站点缓存）

    Args:
        site_code: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)

    Returns:
        对应站点的 Shopify 客户端

    Raises:
        ShopifyAPIError: 如果站点未配置
    """
    global _clients

    code = site_code.lower().strip()

    if code not in _clients:
        config = get_site_config(code)
        if not config:
            raise ShopifyAPIError(
                ERROR_CODES["SITE_NOT_CONFIGURED"]["code"],
                f"站点 {code.upper()} 未配置或 Access Token 缺失"
            )
        _clients[code] = ShopifyClient(config)

    return _clients[code]


def get_all_clients() -> Dict[str, ShopifyClient]:
    """
    获取所有已配置站点的客户端

    Returns:
        站点代码到客户端的映射
    """
    from src.shopify_sites import get_all_configured_sites

    sites = get_all_configured_sites()
    clients = {}
    for code in sites:
        try:
            clients[code] = get_shopify_client(code)
        except ShopifyAPIError:
            pass
    return clients
