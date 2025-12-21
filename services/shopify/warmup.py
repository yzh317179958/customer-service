"""
Shopify UK 缓存预热服务

负责后台预热订单和物流数据，确保用户查询时能快速响应。

设计原则：
1. 用户请求优先：预热时检测到用户请求则暂停
2. 低速率预热：0.5 次/秒，避免影响 Shopify API 限流
3. 失败重试：单个订单失败不影响整体预热
4. 详细日志：记录预热进度和错误

版本: v4.2.0
"""

import os
import asyncio
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class WarmupStats:
    """预热统计数据"""
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    warmup_type: str = "unknown"  # full / incremental
    total_orders: int = 0
    orders_warmed: int = 0
    orders_failed: int = 0
    orders_skipped: int = 0  # 已有缓存跳过
    tracking_warmed: int = 0
    tracking_failed: int = 0
    errors: List[str] = field(default_factory=list)

    @property
    def duration_seconds(self) -> float:
        """预热耗时（秒）"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0

    @property
    def duration_str(self) -> str:
        """预热耗时（格式化）"""
        seconds = self.duration_seconds
        if seconds < 60:
            return f"{seconds:.1f} 秒"
        elif seconds < 3600:
            return f"{seconds / 60:.1f} 分钟"
        else:
            return f"{seconds / 3600:.1f} 小时"

    def to_dict(self) -> Dict[str, Any]:
        """转为字典"""
        return {
            "warmup_type": self.warmup_type,
            "start_time": datetime.fromtimestamp(self.start_time).isoformat() if self.start_time else None,
            "end_time": datetime.fromtimestamp(self.end_time).isoformat() if self.end_time else None,
            "duration": self.duration_str,
            "total_orders": self.total_orders,
            "orders_warmed": self.orders_warmed,
            "orders_failed": self.orders_failed,
            "orders_skipped": self.orders_skipped,
            "tracking_warmed": self.tracking_warmed,
            "tracking_failed": self.tracking_failed,
            "success_rate": f"{self.orders_warmed / max(self.total_orders, 1) * 100:.1f}%",
            "errors": self.errors[:10]  # 只返回前10个错误
        }


class WarmupService:
    """
    缓存预热服务

    功能：
    - 全量预热：预热最近 N 天的所有订单
    - 增量预热：只预热新订单 + 刷新即将过期的缓存
    - 用户优先：检测到用户请求时暂停预热
    """

    def __init__(self):
        """初始化预热服务"""
        # 从环境变量读取配置
        self.enabled = os.getenv("WARMUP_ENABLED", "true").lower() == "true"
        self.order_days = int(os.getenv("WARMUP_ORDER_DAYS", "7"))
        self.rate_limit = float(os.getenv("WARMUP_RATE_LIMIT", "0.5"))  # 次/秒
        self.pause_on_user_request = os.getenv("WARMUP_PAUSE_ON_USER_REQUEST", "true").lower() == "true"
        self.max_retries = int(os.getenv("WARMUP_MAX_RETRIES", "3"))

        # 内部状态
        self._is_running = False
        self._should_stop = False
        self._pending_user_requests: Set[str] = set()  # 正在处理的用户请求
        self._last_warmup_stats: Optional[WarmupStats] = None
        self._warmup_history: List[WarmupStats] = []

        # 延迟导入，避免循环依赖
        self._service = None
        self._client = None

        logger.info(f"✅ 预热服务初始化完成 (enabled={self.enabled}, days={self.order_days}, rate={self.rate_limit}/s)")

    @property
    def service(self):
        """延迟获取 ShopifyService (UK站点)"""
        if self._service is None:
            from services.shopify.service import get_shopify_service
            self._service = get_shopify_service('uk')
        return self._service

    @property
    def client(self):
        """延迟获取 ShopifyClient (UK站点)"""
        if self._client is None:
            from services.shopify.client import get_shopify_client
            self._client = get_shopify_client('uk')
        return self._client

    @property
    def is_running(self) -> bool:
        """是否正在预热"""
        return self._is_running

    @property
    def last_warmup_stats(self) -> Optional[Dict[str, Any]]:
        """获取上次预热统计"""
        if self._last_warmup_stats:
            return self._last_warmup_stats.to_dict()
        return None

    def register_user_request(self, session_id: str):
        """
        注册用户请求（用于优先级控制）

        在用户发起请求时调用，预热服务会暂停让出资源
        """
        self._pending_user_requests.add(session_id)
        logger.debug(f"📥 注册用户请求: {session_id}")

    def unregister_user_request(self, session_id: str):
        """
        取消注册用户请求

        在用户请求完成时调用
        """
        self._pending_user_requests.discard(session_id)
        logger.debug(f"📤 取消用户请求: {session_id}")

    def has_pending_user_request(self) -> bool:
        """是否有待处理的用户请求"""
        return len(self._pending_user_requests) > 0

    async def _wait_for_rate_limit(self):
        """等待速率限制"""
        # 0.5次/秒 = 每2秒一次
        wait_time = 1.0 / self.rate_limit
        await asyncio.sleep(wait_time)

    async def _pause_for_user_request(self):
        """暂停等待用户请求完成"""
        if self.pause_on_user_request and self.has_pending_user_request():
            logger.info("⏸️  检测到用户请求，预热暂停 1 秒")
            await asyncio.sleep(1.0)

    async def get_recent_orders(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        获取最近 N 天的订单列表

        Args:
            days: 获取最近多少天的订单

        Returns:
            订单列表 (包含订单号和订单ID)
        """
        # 计算起始日期
        since_date = datetime.utcnow() - timedelta(days=days)
        since_str = since_date.strftime("%Y-%m-%dT00:00:00Z")

        logger.info(f"📋 获取 {days} 天内的订单 (since: {since_str})")

        # 使用 Shopify API 获取订单
        # 注意：这里直接调用客户端，不使用缓存
        params = {
            "status": "any",
            "limit": 250,  # Shopify API 最大限制
            "created_at_min": since_str,
            "fields": "id,name,created_at,fulfillment_status"
        }

        try:
            data = await self.client._request("GET", "/orders.json", params=params)
            orders = data.get("orders", [])

            result = []
            for order in orders:
                result.append({
                    "order_id": str(order.get("id")),
                    "order_number": order.get("name", "").lstrip("#"),
                    "created_at": order.get("created_at"),
                    "fulfillment_status": order.get("fulfillment_status")
                })

            logger.info(f"✅ 获取到 {len(result)} 个订单")
            return result

        except Exception as e:
            logger.error(f"❌ 获取订单列表失败: {e}")
            raise

    async def warmup_order(self, order_number: str, stats: WarmupStats) -> bool:
        """
        预热单个订单

        Args:
            order_number: 订单号
            stats: 统计对象

        Returns:
            是否成功
        """
        for retry in range(self.max_retries):
            try:
                # 检查是否应该暂停
                await self._pause_for_user_request()

                # 检查是否应该停止
                if self._should_stop:
                    logger.info("⏹️  收到停止信号，中断预热")
                    return False

                # 调用服务预热订单（会自动写入缓存）
                result = await self.service.search_order_by_number(order_number, use_cache=True)

                if result and result.get("cached"):
                    # 已有缓存，跳过
                    stats.orders_skipped += 1
                    logger.debug(f"⏭️  跳过已缓存订单: {order_number}")
                else:
                    stats.orders_warmed += 1
                    logger.debug(f"🔥 预热订单成功: {order_number}")

                return True

            except Exception as e:
                if retry < self.max_retries - 1:
                    logger.warning(f"⚠️  预热订单 {order_number} 失败 (重试 {retry + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(1.0)  # 重试前等待
                else:
                    stats.orders_failed += 1
                    stats.errors.append(f"订单 {order_number}: {str(e)}")
                    logger.error(f"❌ 预热订单 {order_number} 最终失败: {e}")
                    return False

        return False

    async def warmup_tracking(self, order_id: str, order_number: str, stats: WarmupStats) -> bool:
        """
        预热物流信息

        Args:
            order_id: 订单ID
            order_number: 订单号（用于日志）
            stats: 统计对象

        Returns:
            是否成功
        """
        for retry in range(self.max_retries):
            try:
                await self._pause_for_user_request()

                if self._should_stop:
                    return False

                # 调用服务预热物流（会自动写入缓存）
                result = await self.service.get_order_tracking(order_id, use_cache=True)

                if result and result.get("cached"):
                    logger.debug(f"⏭️  跳过已缓存物流: {order_number}")
                else:
                    stats.tracking_warmed += 1
                    logger.debug(f"🔥 预热物流成功: {order_number}")

                return True

            except Exception as e:
                if retry < self.max_retries - 1:
                    logger.warning(f"⚠️  预热物流 {order_number} 失败 (重试 {retry + 1}): {e}")
                    await asyncio.sleep(1.0)
                else:
                    stats.tracking_failed += 1
                    stats.errors.append(f"物流 {order_number}: {str(e)}")
                    logger.error(f"❌ 预热物流 {order_number} 最终失败: {e}")
                    return False

        return False

    async def full_warmup(self, days: Optional[int] = None) -> WarmupStats:
        """
        全量预热

        预热最近 N 天的所有订单和物流信息

        Args:
            days: 预热天数（默认使用配置值）

        Returns:
            预热统计数据
        """
        if self._is_running:
            logger.warning("⚠️  预热已在运行中，跳过")
            return self._last_warmup_stats

        days = days or self.order_days
        stats = WarmupStats(warmup_type="full")
        stats.start_time = time.time()

        self._is_running = True
        self._should_stop = False

        logger.info(f"🚀 开始全量预热 ({days} 天)")

        try:
            # 1. 获取订单列表
            orders = await self.get_recent_orders(days)
            stats.total_orders = len(orders)

            logger.info(f"📊 待预热订单: {stats.total_orders} 个")

            # 2. 逐个预热
            for i, order in enumerate(orders, 1):
                if self._should_stop:
                    logger.info("⏹️  预热被中断")
                    break

                order_number = order["order_number"]
                order_id = order["order_id"]

                # 预热订单详情
                await self.warmup_order(order_number, stats)
                await self._wait_for_rate_limit()

                # 预热物流信息（如果已发货）
                if order.get("fulfillment_status"):
                    await self.warmup_tracking(order_id, order_number, stats)
                    await self._wait_for_rate_limit()

                # 进度日志（每 50 个输出一次）
                if i % 50 == 0:
                    logger.info(f"📈 预热进度: {i}/{stats.total_orders} ({i * 100 // stats.total_orders}%)")

        except Exception as e:
            stats.errors.append(f"全量预热异常: {str(e)}")
            logger.error(f"❌ 全量预热异常: {e}")

        finally:
            self._is_running = False
            stats.end_time = time.time()
            self._last_warmup_stats = stats
            self._warmup_history.append(stats)

            # 保留最近 100 条历史
            if len(self._warmup_history) > 100:
                self._warmup_history = self._warmup_history[-100:]

            logger.info(
                f"✅ 全量预热完成 - 耗时: {stats.duration_str}, "
                f"成功: {stats.orders_warmed}, 跳过: {stats.orders_skipped}, "
                f"失败: {stats.orders_failed}, 物流: {stats.tracking_warmed}"
            )

        return stats

    async def incremental_warmup(self, hours: int = 6) -> WarmupStats:
        """
        增量预热

        只预热新订单和刷新物流信息

        Args:
            hours: 预热最近多少小时的新订单

        Returns:
            预热统计数据
        """
        if self._is_running:
            logger.warning("⚠️  预热已在运行中，跳过")
            return self._last_warmup_stats

        stats = WarmupStats(warmup_type="incremental")
        stats.start_time = time.time()

        self._is_running = True
        self._should_stop = False

        logger.info(f"🔄 开始增量预热 ({hours} 小时内)")

        try:
            # 计算时间范围
            since_date = datetime.utcnow() - timedelta(hours=hours)
            since_str = since_date.strftime("%Y-%m-%dT%H:%M:%SZ")

            # 获取最近的订单
            params = {
                "status": "any",
                "limit": 250,
                "created_at_min": since_str,
                "fields": "id,name,created_at,fulfillment_status"
            }

            data = await self.client._request("GET", "/orders.json", params=params)
            orders = data.get("orders", [])
            stats.total_orders = len(orders)

            logger.info(f"📊 待预热订单: {stats.total_orders} 个 (增量)")

            # 预热订单
            for order in orders:
                if self._should_stop:
                    break

                order_number = order.get("name", "").lstrip("#")
                order_id = str(order.get("id"))

                await self.warmup_order(order_number, stats)
                await self._wait_for_rate_limit()

                if order.get("fulfillment_status"):
                    await self.warmup_tracking(order_id, order_number, stats)
                    await self._wait_for_rate_limit()

        except Exception as e:
            stats.errors.append(f"增量预热异常: {str(e)}")
            logger.error(f"❌ 增量预热异常: {e}")

        finally:
            self._is_running = False
            stats.end_time = time.time()
            self._last_warmup_stats = stats
            self._warmup_history.append(stats)

            if len(self._warmup_history) > 100:
                self._warmup_history = self._warmup_history[-100:]

            logger.info(
                f"✅ 增量预热完成 - 耗时: {stats.duration_str}, "
                f"成功: {stats.orders_warmed}, 跳过: {stats.orders_skipped}"
            )

        return stats

    def stop(self):
        """停止当前预热任务"""
        if self._is_running:
            self._should_stop = True
            logger.info("⏹️  发送停止信号")

    def get_status(self) -> Dict[str, Any]:
        """获取预热服务状态"""
        return {
            "enabled": self.enabled,
            "is_running": self._is_running,
            "config": {
                "order_days": self.order_days,
                "rate_limit": self.rate_limit,
                "pause_on_user_request": self.pause_on_user_request,
                "max_retries": self.max_retries
            },
            "pending_user_requests": len(self._pending_user_requests),
            "last_warmup": self.last_warmup_stats,
            "history_count": len(self._warmup_history)
        }

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取预热历史记录"""
        recent = self._warmup_history[-limit:] if self._warmup_history else []
        return [stats.to_dict() for stats in reversed(recent)]


# ==================== 全局实例 ====================

_warmup_service: Optional[WarmupService] = None


def get_warmup_service() -> WarmupService:
    """获取预热服务单例"""
    global _warmup_service
    if _warmup_service is None:
        _warmup_service = WarmupService()
    return _warmup_service
