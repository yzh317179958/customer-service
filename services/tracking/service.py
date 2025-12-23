"""
物流追踪服务层

封装业务逻辑，提供统一的物流追踪接口。

主要功能：
- 注册订单物流追踪
- 查询物流轨迹事件
- 运单号与订单号映射查询
- 缓存管理

使用示例：
    from services.tracking import get_tracking_service

    service = get_tracking_service()

    # 注册追踪
    await service.register_order_tracking(
        order_id="12345",
        tracking_number="AB123456789GB",
        carrier="royalmail"
    )

    # 查询轨迹
    events = await service.get_tracking_events("AB123456789GB")
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from .client import Track17Client, Track17Error, get_track17_client
from .models import (
    TrackingStatus,
    TrackingEvent,
    TrackingInfo,
    CarrierInfo,
)

logger = logging.getLogger(__name__)

# 缓存配置
CACHE_TTL_TRACKING = int(os.getenv("SHOPIFY_CACHE_TRACKING", 21600))  # 6 小时
CACHE_TTL_MAPPING = 86400 * 7  # 7 天


class TrackingService:
    """
    物流追踪服务

    封装 17track API 调用，提供业务层接口。
    支持 Redis 缓存和运单-订单映射存储。
    """

    def __init__(
        self,
        client: Optional[Track17Client] = None,
        redis_client: Optional[Any] = None,
    ):
        """
        初始化服务

        Args:
            client: 17track API 客户端
            redis_client: Redis 客户端（可选，用于缓存）
        """
        self.client = client or get_track17_client()
        self.redis = redis_client

        # 内存缓存（Redis 不可用时使用）
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._mapping: Dict[str, str] = {}  # tracking_number -> order_id

    def _get_redis(self):
        """获取 Redis 客户端"""
        if self.redis:
            return self.redis

        # 尝试从全局获取
        try:
            from infrastructure.database.connection import get_redis_client
            return get_redis_client()
        except Exception:
            return None

    async def _cache_get(self, key: str) -> Optional[Dict[str, Any]]:
        """从缓存获取数据"""
        redis = self._get_redis()
        if redis:
            try:
                data = await redis.get(f"tracking:{key}")
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.debug(f"Redis 缓存读取失败: {e}")

        # 降级到内存缓存
        cached = self._cache.get(key)
        if cached:
            if cached.get("expires_at", 0) > datetime.now().timestamp():
                return cached.get("data")
            else:
                del self._cache[key]
        return None

    async def _cache_set(
        self,
        key: str,
        data: Dict[str, Any],
        ttl: int = CACHE_TTL_TRACKING,
    ):
        """写入缓存"""
        redis = self._get_redis()
        if redis:
            try:
                await redis.setex(
                    f"tracking:{key}",
                    ttl,
                    json.dumps(data, default=str),
                )
                return
            except Exception as e:
                logger.debug(f"Redis 缓存写入失败: {e}")

        # 降级到内存缓存
        self._cache[key] = {
            "data": data,
            "expires_at": datetime.now().timestamp() + ttl,
        }

    async def _mapping_get(self, tracking_number: str) -> Optional[str]:
        """获取运单号对应的订单 ID"""
        redis = self._get_redis()
        if redis:
            try:
                order_id = await redis.get(f"tracking_map:{tracking_number}")
                if order_id:
                    return order_id.decode() if isinstance(order_id, bytes) else order_id
            except Exception as e:
                logger.debug(f"Redis 映射读取失败: {e}")

        return self._mapping.get(tracking_number)

    async def _mapping_set(self, tracking_number: str, order_id: str):
        """保存运单号与订单 ID 的映射"""
        redis = self._get_redis()
        if redis:
            try:
                await redis.setex(
                    f"tracking_map:{tracking_number}",
                    CACHE_TTL_MAPPING,
                    order_id,
                )
                return
            except Exception as e:
                logger.debug(f"Redis 映射写入失败: {e}")

        self._mapping[tracking_number] = order_id

    async def register_order_tracking(
        self,
        order_id: str,
        tracking_number: str,
        carrier: Optional[str] = None,
        order_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        注册订单物流追踪

        将运单号注册到 17track 进行追踪，并保存运单-订单映射。

        Args:
            order_id: Shopify 订单 ID
            tracking_number: 运单号
            carrier: 承运商名称或代码
            order_number: 订单显示号（如 #1234）

        Returns:
            注册结果:
            - success: 是否成功
            - message: 结果消息
            - tracking_number: 运单号
        """
        try:
            # 构建标签（用于 Webhook 回调时识别订单）
            tag = f"order_{order_id}"

            # 调用 17track API 注册
            result = await self.client.register_tracking(
                tracking_number=tracking_number,
                carrier_code=carrier,
                order_id=order_number or order_id,
                tag=tag,
            )

            # 保存映射
            await self._mapping_set(tracking_number, order_id)

            if result.get("success"):
                logger.info(
                    f"运单注册成功: {tracking_number} -> 订单 {order_id}"
                )
                return {
                    "success": True,
                    "message": "运单注册成功",
                    "tracking_number": tracking_number,
                    "order_id": order_id,
                }
            else:
                # 可能是重复注册
                rejected = result.get("rejected", [])
                if rejected:
                    error_msg = rejected[0].get("error", {}).get("message", "")
                    if "already exists" in error_msg.lower():
                        logger.info(f"运单已注册: {tracking_number}")
                        return {
                            "success": True,
                            "message": "运单已注册",
                            "tracking_number": tracking_number,
                            "order_id": order_id,
                        }

                return {
                    "success": False,
                    "message": "注册失败",
                    "tracking_number": tracking_number,
                    "rejected": rejected,
                }

        except Track17Error as e:
            logger.error(f"运单注册失败: {tracking_number}, 错误: {e}")
            return {
                "success": False,
                "message": str(e),
                "tracking_number": tracking_number,
            }

    async def get_tracking_events(
        self,
        tracking_number: str,
        carrier: Optional[str] = None,
        use_cache: bool = True,
    ) -> List[TrackingEvent]:
        """
        获取物流轨迹事件列表

        Args:
            tracking_number: 运单号
            carrier: 承运商（可选）
            use_cache: 是否使用缓存

        Returns:
            物流事件列表，按时间倒序排列
        """
        cache_key = f"events:{tracking_number}"

        # 尝试从缓存获取
        if use_cache:
            cached = await self._cache_get(cache_key)
            if cached:
                logger.debug(f"从缓存获取物流事件: {tracking_number}")
                return [TrackingEvent(**e) for e in cached]

        try:
            # 调用 API 查询
            result = await self.client.get_tracking_info(
                tracking_number=tracking_number,
                carrier_code=carrier,
            )

            if not result.get("success"):
                logger.warning(f"查询物流失败: {tracking_number}")
                return []

            # 转换事件格式
            events = []
            raw_events = result.get("events", [])

            for raw in raw_events:
                event = TrackingEvent(
                    timestamp_str=raw.get("timestamp"),
                    status=raw.get("status"),
                    location=raw.get("location"),
                    description=raw.get("status"),
                    status_code=raw.get("status_code"),
                )

                # 尝试解析时间戳
                if event.timestamp_str:
                    try:
                        event.timestamp = datetime.fromisoformat(
                            event.timestamp_str.replace(" ", "T")
                        )
                    except ValueError:
                        pass

                events.append(event)

            # 写入缓存
            if events:
                cache_data = [e.model_dump() for e in events]
                await self._cache_set(cache_key, cache_data)

            return events

        except Track17Error as e:
            logger.error(f"查询物流失败: {tracking_number}, 错误: {e}")
            return []

    async def get_tracking_info(
        self,
        tracking_number: str,
        carrier: Optional[str] = None,
        use_cache: bool = True,
    ) -> Optional[TrackingInfo]:
        """
        获取完整物流信息

        Args:
            tracking_number: 运单号
            carrier: 承运商（可选）
            use_cache: 是否使用缓存

        Returns:
            TrackingInfo 对象，查询失败返回 None
        """
        cache_key = f"info:{tracking_number}"

        # 尝试从缓存获取
        if use_cache:
            cached = await self._cache_get(cache_key)
            if cached:
                logger.debug(f"从缓存获取物流信息: {tracking_number}")
                return TrackingInfo(**cached)

        try:
            # 调用 API 查询
            result = await self.client.get_tracking_info(
                tracking_number=tracking_number,
                carrier_code=carrier,
            )

            if not result.get("success"):
                return None

            # 获取订单 ID
            order_id = await self._mapping_get(tracking_number)

            # 构建 TrackingInfo
            track_info = result.get("track_info", {})
            status_code = track_info.get("e")
            status = TrackingStatus.from_code(status_code) if status_code is not None else None

            # 承运商信息
            carrier_data = result.get("carrier")
            carrier_info = None
            if carrier_data:
                if isinstance(carrier_data, dict):
                    carrier_info = CarrierInfo(
                        code=carrier_data.get("key"),
                        name=carrier_data.get("name"),
                        url=carrier_data.get("url"),
                    )
                elif isinstance(carrier_data, int):
                    # 只有承运商代码
                    carrier_info = CarrierInfo(code=carrier_data)

            # 事件列表
            events = await self.get_tracking_events(tracking_number, carrier, use_cache=False)

            # 最新事件
            last_event_data = result.get("last_event", {})
            last_event = TrackingEvent.from_17track_event(last_event_data) if last_event_data else None

            info = TrackingInfo(
                tracking_number=tracking_number,
                carrier=carrier_info,
                status=status,
                sub_status=track_info.get("f"),
                status_zh=status.zh if status else None,
                events=events,
                last_event=last_event,
                order_id=order_id,
                raw_data=result,
            )

            # 写入缓存
            cache_data = info.model_dump()
            await self._cache_set(cache_key, cache_data)

            return info

        except Track17Error as e:
            logger.error(f"查询物流信息失败: {tracking_number}, 错误: {e}")
            return None

    async def find_order_by_tracking(
        self,
        tracking_number: str,
    ) -> Optional[str]:
        """
        通过运单号查找关联的订单 ID

        Args:
            tracking_number: 运单号

        Returns:
            订单 ID，未找到返回 None
        """
        return await self._mapping_get(tracking_number)

    async def get_status(
        self,
        tracking_number: str,
        carrier: Optional[str] = None,
    ) -> Optional[TrackingStatus]:
        """
        获取运单当前状态

        Args:
            tracking_number: 运单号
            carrier: 承运商（可选）

        Returns:
            TrackingStatus 枚举值，查询失败返回 None
        """
        info = await self.get_tracking_info(tracking_number, carrier)
        return info.status if info else None

    async def is_delivered(
        self,
        tracking_number: str,
        carrier: Optional[str] = None,
    ) -> bool:
        """
        检查运单是否已签收

        Args:
            tracking_number: 运单号
            carrier: 承运商（可选）

        Returns:
            是否已签收
        """
        status = await self.get_status(tracking_number, carrier)
        return status == TrackingStatus.DELIVERED if status else False

    async def has_exception(
        self,
        tracking_number: str,
        carrier: Optional[str] = None,
    ) -> bool:
        """
        检查运单是否有异常

        Args:
            tracking_number: 运单号
            carrier: 承运商（可选）

        Returns:
            是否有异常
        """
        status = await self.get_status(tracking_number, carrier)
        return status.is_exception if status else False

    async def clear_cache(self, tracking_number: str):
        """
        清除运单缓存

        Args:
            tracking_number: 运单号
        """
        redis = self._get_redis()
        keys = [
            f"tracking:events:{tracking_number}",
            f"tracking:info:{tracking_number}",
        ]

        if redis:
            try:
                for key in keys:
                    await redis.delete(key)
            except Exception as e:
                logger.debug(f"Redis 缓存清除失败: {e}")

        # 清除内存缓存
        self._cache.pop(f"events:{tracking_number}", None)
        self._cache.pop(f"info:{tracking_number}", None)


# 全局服务实例
_default_service: Optional[TrackingService] = None


def get_tracking_service() -> TrackingService:
    """
    获取默认的物流追踪服务实例

    Returns:
        TrackingService 实例
    """
    global _default_service
    if _default_service is None:
        _default_service = TrackingService()
    return _default_service
