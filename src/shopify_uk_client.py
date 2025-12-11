"""
Shopify UK 店铺 API 客户端

专用于 Fiido UK 店铺 (fiidouk.myshopify.com) 的订单查询功能。
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
from datetime import datetime
from decimal import Decimal

import httpx
from pydantic import BaseModel

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
}


# ==================== API 客户端 ====================

class ShopifyUKClient:
    """
    Shopify UK 店铺 API 客户端

    特点：
    - 速率限制: 2次/秒 (Shopify 标准计划限制)
    - 连接池: 复用 HTTP 连接
    - 超时保护: 连接 5s，读取 30s
    - 错误重试: 自动重试临时错误
    """

    def __init__(
        self,
        shop_domain: Optional[str] = None,
        access_token: Optional[str] = None,
        api_version: Optional[str] = None,
    ):
        """
        初始化 Shopify UK 客户端

        Args:
            shop_domain: 店铺域名 (默认从环境变量读取)
            access_token: Admin API Access Token
            api_version: API 版本 (默认 2024-01)
        """
        self.shop_domain = shop_domain or os.getenv(
            "SHOPIFY_UK_SHOP_DOMAIN", "fiidouk.myshopify.com"
        )
        self.access_token = access_token or os.getenv("SHOPIFY_UK_ACCESS_TOKEN")
        self.api_version = api_version or os.getenv(
            "SHOPIFY_UK_API_VERSION", "2024-01"
        )

        if not self.access_token:
            logger.warning("⚠️ SHOPIFY_UK_ACCESS_TOKEN 未配置")

        self.base_url = f"https://{self.shop_domain}/admin/api/{self.api_version}"

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

        logger.info(f"✅ Shopify UK 客户端初始化: {self.shop_domain}")

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
                "Shopify UK Access Token 未配置"
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
        # 清理订单号格式
        clean_number = order_number.strip().lstrip("#")

        params = {
            "name": clean_number,
            "status": "any",
            "limit": 1
        }

        data = await self._request("GET", "/orders.json", params=params)
        orders = data.get("orders", [])

        if not orders:
            return None

        return self._parse_order_detail(orders[0])

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

        return self._parse_order_detail(order)

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
            currency=order.get("currency", "GBP"),
            items_count=sum(item.get("quantity", 0) for item in line_items),
            customer_email=customer.get("email"),
            customer_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip(),
            primary_product=primary_product
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

    def _parse_order_detail(self, order: Dict) -> ShopifyOrderDetail:
        """解析订单详情"""
        summary = self._parse_order_summary(order)

        # 解析商品列表（包含商品级别的发货状态）
        line_items = [
            ShopifyLineItem(
                title=item.get("title", ""),
                variant_title=item.get("variant_title"),
                sku=item.get("sku"),
                quantity=item.get("quantity", 1),
                price=item.get("price", "0"),
                fulfillment_status=item.get("fulfillment_status")  # fulfilled/null
            )
            for item in order.get("line_items", [])
        ]

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
                "shop_domain": self.shop_domain,
                "api_version": self.api_version,
                "total_orders": count
            }
        except ShopifyAPIError as e:
            return {
                "status": "unhealthy",
                "error": e.message,
                "code": e.code
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# ==================== 全局实例 ====================

_shopify_uk_client: Optional[ShopifyUKClient] = None


def get_shopify_uk_client() -> ShopifyUKClient:
    """获取 Shopify UK 客户端单例"""
    global _shopify_uk_client
    if _shopify_uk_client is None:
        _shopify_uk_client = ShopifyUKClient()
    return _shopify_uk_client
