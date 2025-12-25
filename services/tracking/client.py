"""
17track API 客户端

封装 17track API V2.2 的调用，提供运单注册、轨迹查询等功能。

API 文档：https://api.17track.net/en/doc?version=v2

使用示例：
    from services.tracking.client import Track17Client

    client = Track17Client(api_key="your_api_key")

    # 注册运单
    result = await client.register_tracking("AB123456789GB", "royalmail")

    # 查询轨迹
    info = await client.get_tracking_info("AB123456789GB")
"""

import os
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime

logger = logging.getLogger(__name__)


class Track17Error(Exception):
    """17track API 错误"""

    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"17track API Error [{code}]: {message}")


class Track17Client:
    """
    17track API V2.4 客户端

    主要功能：
    - register_tracking: 注册运单到 17track 进行追踪
    - get_tracking_info: 查询运单的物流轨迹
    - retrack: 重新追踪已停止的运单
    - stop_tracking: 停止追踪运单
    """

    # 默认 API 基础 URL (V2.4)
    DEFAULT_BASE_URL = "https://api.17track.net/track/v2.4"

    # 承运商代码映射（常用）
    # 来源: https://res.17track.net/asset/carrier/info/apicarrier.all.csv
    CARRIER_CODES = {
        # UK 承运商
        "royal mail": 11031,
        "royalmail": 11031,
        "dpd": 100010,          # DPD (UK)
        "dpd uk": 100010,
        "hermes": 100018,       # Hermes
        "evri": 100331,         # EVRi (Hermes 改名)
        "yodel": 100017,
        "parcelforce": 11033,
        "uk mail": 100020,      # UK Mail
        "collect+": 100142,     # CollectPlus
        "collectplus": 100142,
        "dx freight": 100484,
        "dxfreight": 100484,
        "dx": 100484,
        # 德国承运商
        "dhl": 100001,          # DHL Express
        "dhl express": 100001,
        "dhl paket": 7041,      # DHL Paket (德国国内)
        "dpd germany": 100007,  # DPD (DE)
        "dpd de": 100007,
        "hermes de": 100031,    # Hermes (DE)
        "deutsche post": 7041,
        # 法国承运商
        "chronopost": 100037,
        "colissimo": 100038,
        "dpd france": 100072,   # DPD (FR)
        "dpd fr": 100072,
        # 其他欧洲
        "gls": 100005,
        "gls italy": 100024,    # GLS (IT)
        "gls spain": 100189,    # GLS Spain
        "correos": 100053,
        "poste italiane": 100091,
        "postnl": 100047,       # DHL Parcel (NL) / PostNL
        "bpost": 100015,
        "dhl parcel uk": 100152,
        "dhl parcel nl": 100047,
        # 国际承运商
        "ups": 100002,
        "fedex": 100003,
        "tnt": 100004,
        "usps": 21051,
        # 中国承运商
        "yunexpress": 190008,   # YunExpress 云途物流
        "yun express": 190008,
        "yanwen": 190001,
        "4px": 190004,
        "sf express": 3011,
        "cne express": 190122,
        "cainiao": 190011,
        "china post": 3001,
        "yunda": 191197,        # 韵达快运
        "yunda express": 191197,
        # DHL 系列
        "dhl ecommerce": 7047,  # DHL eCommerce US
        "dhl ecommerce asia": 7048,
    }

    # 承运商名称标准化映射（Shopify 名称 -> 标准名称）
    CARRIER_NAME_MAP = {
        # UK
        "Royal Mail": "royal mail",
        "DPD": "dpd",
        "DPD UK": "dpd uk",
        "DPD Local": "dpd uk",
        "Evri": "evri",
        "EVRi": "evri",
        "EVRI": "evri",
        "Hermes": "hermes",
        "Hermes UK": "hermes",
        "Yodel": "yodel",
        "Parcelforce": "parcelforce",
        "Parcelforce Worldwide": "parcelforce",
        "DX Freight": "dx freight",
        "DX FREIGHT": "dx freight",
        "DX": "dx",
        "UK Mail": "uk mail",
        "CollectPlus": "collectplus",
        "Collect+": "collectplus",
        "DHL Parcel UK": "dhl parcel uk",
        # 德国
        "DHL": "dhl",
        "DHL Express": "dhl express",
        "DHL Paket": "dhl paket",
        "DPD Germany": "dpd germany",
        "DPD DE": "dpd de",
        "Hermes DE": "hermes de",
        "Deutsche Post": "deutsche post",
        # 法国
        "Chronopost": "chronopost",
        "Colissimo": "colissimo",
        "DPD France": "dpd france",
        "DPD FR": "dpd fr",
        # 其他欧洲
        "GLS": "gls",
        "GLS Italy": "gls italy",
        "GLS Spain": "gls spain",
        "Correos": "correos",
        "Poste Italiane": "poste italiane",
        "PostNL": "postnl",
        "Bpost": "bpost",
        "bpost": "bpost",
        # 国际
        "UPS": "ups",
        "FedEx": "fedex",
        "FEDEX": "fedex",
        "TNT": "tnt",
        "USPS": "usps",
        # 中国
        "Yun Express": "yunexpress",
        "YunExpress": "yunexpress",
        "YUNEXPRESS": "yunexpress",
        "云途": "yunexpress",
        "Yanwen": "yanwen",
        "4PX": "4px",
        "SF Express": "sf express",
        "顺丰": "sf express",
        "CNE Express": "cne express",
        "Cainiao": "cainiao",
        "菜鸟": "cainiao",
        "China Post": "china post",
        "中国邮政": "china post",
        "Yunda": "yunda",
        "韵达": "yunda",
        # DHL 系列
        "DHL eCommerce": "dhl ecommerce",
        "DHL eCommerce Asia": "dhl ecommerce asia",
    }

    # 17track 不支持的承运商（提供官网链接供用户直接查询）
    UNSUPPORTED_CARRIERS = {
        "yunway": "https://www.yunway.com/",
        "YUNWAY": "https://www.yunway.com/",
    }

    @classmethod
    def normalize_carrier(cls, carrier_name: str) -> Optional[str]:
        """
        标准化承运商名称

        从 Shopify fulfillment 的承运商名称转换为 17track 可识别的标准名称。

        Args:
            carrier_name: 原始承运商名称（来自 Shopify）

        Returns:
            标准化后的承运商名称，未找到返回 None
        """
        if not carrier_name:
            return None

        # 先尝试精确匹配
        if carrier_name in cls.CARRIER_NAME_MAP:
            return cls.CARRIER_NAME_MAP[carrier_name]

        # 尝试小写匹配
        lower_name = carrier_name.lower().strip()
        if lower_name in cls.CARRIER_CODES:
            return lower_name

        # 尝试模糊匹配
        for key in cls.CARRIER_NAME_MAP:
            if key.lower() in lower_name or lower_name in key.lower():
                return cls.CARRIER_NAME_MAP[key]

        logger.debug(f"未知承运商: {carrier_name}")
        return None

    @classmethod
    def is_unsupported_carrier(cls, carrier_name: str) -> bool:
        """
        检查是否为 17track 不支持的承运商

        Args:
            carrier_name: 承运商名称

        Returns:
            True 如果不支持
        """
        if not carrier_name:
            return False
        lower_name = carrier_name.lower().strip()
        return lower_name in [k.lower() for k in cls.UNSUPPORTED_CARRIERS.keys()]

    @classmethod
    def get_unsupported_carrier_url(cls, carrier_name: str) -> Optional[str]:
        """
        获取不支持的承运商的官网链接

        Args:
            carrier_name: 承运商名称

        Returns:
            承运商官网 URL，如果支持或未知则返回 None
        """
        if not carrier_name:
            return None
        lower_name = carrier_name.lower().strip()
        for key, url in cls.UNSUPPORTED_CARRIERS.items():
            if key.lower() == lower_name:
                return url
        return None

    @classmethod
    def get_carrier_code(cls, carrier_name: str) -> Optional[int]:
        """
        获取承运商代码

        Args:
            carrier_name: 承运商名称（原始或标准化后的）

        Returns:
            17track 承运商代码，未找到返回 None
        """
        # 先标准化
        normalized = cls.normalize_carrier(carrier_name)
        if normalized and normalized in cls.CARRIER_CODES:
            return cls.CARRIER_CODES[normalized]

        # 直接尝试
        lower_name = carrier_name.lower().strip() if carrier_name else ""
        return cls.CARRIER_CODES.get(lower_name)

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        初始化客户端

        Args:
            api_key: 17track API Key，默认从环境变量 TRACK17_API_KEY 读取
            base_url: API 基础 URL，默认使用官方地址
            timeout: 请求超时时间（秒）
        """
        self.api_key = api_key or os.getenv("TRACK17_API_KEY")
        if not self.api_key:
            logger.warning("TRACK17_API_KEY 未设置，API 调用将失败")

        self.base_url = base_url or os.getenv("TRACK17_API_URL") or self.DEFAULT_BASE_URL
        self.timeout = timeout

        # HTTP 客户端配置
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers={
                    "Content-Type": "application/json",
                    "17token": self.api_key or "",
                },
            )
        return self._client

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        endpoint: str,
        data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        发送 API 请求

        Args:
            endpoint: API 端点路径
            data: 请求数据

        Returns:
            API 响应数据

        Raises:
            Track17Error: API 调用失败
        """
        if not self.api_key:
            raise Track17Error(0, "API Key 未配置")

        url = f"{self.base_url}/{endpoint}"
        client = await self._get_client()

        try:
            response = await client.post(url, json=data)
            result = response.json()

            # 检查响应状态
            code = result.get("code", -1)
            if code != 0:
                raise Track17Error(
                    code=code,
                    message=result.get("message", "Unknown error"),
                    data=result.get("data"),
                )

            return result

        except httpx.RequestError as e:
            logger.error(f"17track API 请求失败: {e}")
            raise Track17Error(-1, f"网络请求失败: {str(e)}")

        except Exception as e:
            if isinstance(e, Track17Error):
                raise
            logger.error(f"17track API 调用异常: {e}")
            raise Track17Error(-1, f"API 调用异常: {str(e)}")

    def _normalize_carrier_code(self, carrier: str) -> Optional[int]:
        """
        标准化承运商代码

        Args:
            carrier: 承运商名称或代码

        Returns:
            17track 承运商代码，未找到返回 None
        """
        if isinstance(carrier, int):
            return carrier

        if carrier.isdigit():
            return int(carrier)

        # 查找承运商代码
        carrier_lower = carrier.lower().strip()
        return self.CARRIER_CODES.get(carrier_lower)

    async def register_tracking(
        self,
        tracking_number: str,
        carrier_code: Optional[str] = None,
        order_id: Optional[str] = None,
        tag: Optional[str] = None,
        destination_postal_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        注册运单到 17track 进行追踪

        Args:
            tracking_number: 运单号
            carrier_code: 承运商代码或名称（可选，17track 会自动识别）
            order_id: 关联订单号（可选，用于后续查询）
            tag: 自定义标签（可选）
            destination_postal_code: 目的地邮编（可选，某些承运商如 DX FREIGHT 需要）

        Returns:
            注册结果，包含：
            - accepted: 成功注册的运单列表
            - rejected: 拒绝的运单列表（如已存在）

        Raises:
            Track17Error: API 调用失败
        """
        # 构建请求数据
        tracking_data = {
            "number": tracking_number,
        }

        # 添加承运商代码
        if carrier_code:
            carrier_id = self._normalize_carrier_code(carrier_code)
            if carrier_id:
                tracking_data["carrier"] = carrier_id

        # 添加可选参数
        if order_id:
            tracking_data["order"] = order_id
        if tag:
            tracking_data["tag"] = tag
        if destination_postal_code:
            tracking_data["destination_postal_code"] = destination_postal_code

        data = [tracking_data]

        logger.info(f"注册运单到 17track: {tracking_number}, carrier={carrier_code}, postal_code={destination_postal_code}")

        result = await self._request("register", data)

        # 解析结果
        response_data = result.get("data", {})
        accepted = response_data.get("accepted", [])
        rejected = response_data.get("rejected", [])

        if rejected:
            reject_info = rejected[0] if rejected else {}
            logger.warning(
                f"运单注册被拒绝: {tracking_number}, "
                f"原因: {reject_info.get('error', {}).get('message', 'unknown')}"
            )

        return {
            "success": len(accepted) > 0,
            "accepted": accepted,
            "rejected": rejected,
            "tracking_number": tracking_number,
        }

    async def register_batch(
        self,
        trackings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        批量注册运单

        Args:
            trackings: 运单列表，每项包含：
                - number: 运单号（必填）
                - carrier: 承运商代码（可选）
                - order: 订单号（可选）

        Returns:
            注册结果
        """
        # 标准化承运商代码
        data = []
        for item in trackings:
            tracking_data = {"number": item["number"]}
            if "carrier" in item:
                carrier_id = self._normalize_carrier_code(item["carrier"])
                if carrier_id:
                    tracking_data["carrier"] = carrier_id
            if "order" in item:
                tracking_data["order"] = item["order"]
            data.append(tracking_data)

        logger.info(f"批量注册运单到 17track: {len(data)} 个")

        result = await self._request("register", data)
        return result.get("data", {})

    async def get_tracking_info(
        self,
        tracking_number: str,
        carrier_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        查询运单的物流轨迹

        Args:
            tracking_number: 运单号
            carrier_code: 承运商代码（可选）

        Returns:
            物流信息，包含：
            - number: 运单号
            - carrier: 承运商信息
            - status: 当前状态
            - track: 轨迹事件列表
            - lastEvent: 最新事件

        Raises:
            Track17Error: API 调用失败
        """
        # 构建请求数据
        tracking_data = {"number": tracking_number}

        if carrier_code:
            carrier_id = self._normalize_carrier_code(carrier_code)
            if carrier_id:
                tracking_data["carrier"] = carrier_id

        data = [tracking_data]

        logger.info(f"查询物流轨迹: {tracking_number}")

        result = await self._request("gettrackinfo", data)

        # 解析结果
        response_data = result.get("data", {})
        accepted = response_data.get("accepted", [])
        rejected = response_data.get("rejected", [])

        if rejected:
            reject_info = rejected[0] if rejected else {}
            error_msg = reject_info.get("error", {}).get("message", "unknown")
            raise Track17Error(-2, f"查询失败: {error_msg}")

        if not accepted:
            return {
                "success": False,
                "tracking_number": tracking_number,
                "message": "未找到物流信息",
            }

        tracking_info = accepted[0]
        track_info = tracking_info.get("track_info", {})

        # V2.4 API: 状态在 latest_status
        latest_status = track_info.get("latest_status", {})
        status = latest_status.get("status")  # e.g. "InTransit", "Delivered"
        sub_status = latest_status.get("sub_status")

        # V2.4 API: 事件在 tracking.providers[0].events
        events = self._parse_events_v2(track_info)

        # V2.4 API: 最新事件在 latest_event
        last_event = track_info.get("latest_event", {})

        return {
            "success": True,
            "tracking_number": tracking_number,
            "number": tracking_info.get("number"),
            "carrier": tracking_info.get("carrier"),
            "status": status,
            "sub_status": sub_status,
            "track_info": track_info,
            "events": events,
            "last_event": last_event,
        }

    def _parse_events(self, tracking_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析物流事件列表 (旧版 V2.2 格式，保留兼容)

        Args:
            tracking_info: 17track 返回的物流信息

        Returns:
            格式化的事件列表
        """
        events = []
        track = tracking_info.get("track", {})

        # z1 是事件列表 (旧格式)
        raw_events = track.get("z1", [])

        for event in raw_events:
            events.append({
                "timestamp": event.get("a"),  # 时间
                "status": event.get("c"),  # 状态描述
                "location": event.get("d"),  # 地点
                "status_code": event.get("b"),  # 状态码
            })

        return events

    def _parse_events_v2(self, track_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        解析物流事件列表 (V2.4 新格式)

        V2.4 API 的事件结构:
        track_info.tracking.providers[0].events[]

        每个事件包含:
        - time_iso: ISO 格式时间
        - description: 事件描述
        - location: 地点
        - sub_status: 子状态

        Args:
            track_info: 17track 返回的 track_info 字段

        Returns:
            格式化的事件列表
        """
        events = []

        # 获取 providers
        tracking = track_info.get("tracking", {})
        providers = tracking.get("providers", [])

        if not providers:
            return events

        # 取第一个 provider 的事件
        provider = providers[0]
        raw_events = provider.get("events", [])

        for event in raw_events:
            # 地点可能在 location 或 address 中
            location = event.get("location")
            if not location:
                address = event.get("address", {})
                parts = []
                if address.get("city"):
                    parts.append(address["city"])
                if address.get("country"):
                    parts.append(address["country"])
                location = ", ".join(parts) if parts else None

            events.append({
                "timestamp": event.get("time_iso"),  # ISO 格式时间
                "status": event.get("description"),  # 事件描述
                "location": location,
                "status_code": event.get("sub_status"),  # 子状态作为状态码
            })

        return events

    async def retrack(
        self,
        tracking_number: str,
        carrier_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        重新追踪已停止的运单

        Args:
            tracking_number: 运单号
            carrier_code: 承运商代码（可选）

        Returns:
            重新追踪结果
        """
        tracking_data = {"number": tracking_number}

        if carrier_code:
            carrier_id = self._normalize_carrier_code(carrier_code)
            if carrier_id:
                tracking_data["carrier"] = carrier_id

        data = [tracking_data]

        logger.info(f"重新追踪运单: {tracking_number}")

        result = await self._request("retrack", data)
        return result.get("data", {})

    async def stop_tracking(
        self,
        tracking_number: str,
        carrier_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        停止追踪运单

        Args:
            tracking_number: 运单号
            carrier_code: 承运商代码（可选）

        Returns:
            停止追踪结果
        """
        tracking_data = {"number": tracking_number}

        if carrier_code:
            carrier_id = self._normalize_carrier_code(carrier_code)
            if carrier_id:
                tracking_data["carrier"] = carrier_id

        data = [tracking_data]

        logger.info(f"停止追踪运单: {tracking_number}")

        result = await self._request("stoptrack", data)
        return result.get("data", {})

    async def change_carrier(
        self,
        tracking_number: str,
        new_carrier_code: str,
    ) -> Dict[str, Any]:
        """
        更改运单的承运商

        Args:
            tracking_number: 运单号
            new_carrier_code: 新承运商代码

        Returns:
            更改结果
        """
        carrier_id = self._normalize_carrier_code(new_carrier_code)
        if not carrier_id:
            raise Track17Error(-3, f"未知承运商: {new_carrier_code}")

        data = [{"number": tracking_number, "carrier": carrier_id}]

        logger.info(f"更改运单承运商: {tracking_number} -> {new_carrier_code}")

        result = await self._request("changecarrier", data)
        return result.get("data", {})


# 全局客户端实例（可选，用于简化调用）
_default_client: Optional[Track17Client] = None


def get_track17_client() -> Track17Client:
    """
    获取默认的 17track 客户端实例

    Returns:
        Track17Client 实例
    """
    global _default_client
    if _default_client is None:
        _default_client = Track17Client()
    return _default_client
