# -*- coding: utf-8 -*-
"""
基础设施 - 后台任务调度器模块

提供后台任务的统一管理，包括：
- SLA 预警任务
- 坐席心跳监控
- 缓存预热调度
"""

import os
import asyncio
from typing import Optional, Callable, Any


# ============================================================================
# 全局状态
# ============================================================================

_sla_task: Optional[asyncio.Task] = None
_heartbeat_task: Optional[asyncio.Task] = None
_warmup_scheduler = None
_warmup_service_factory: Optional[Callable[[], Any]] = None
_initialized = False

# 配置
SLA_CHECK_INTERVAL = int(os.getenv("SLA_CHECK_INTERVAL", "60"))
AGENT_OFFLINE_THRESHOLD = int(os.getenv("AGENT_OFFLINE_THRESHOLD", "30"))
AGENT_CHECK_INTERVAL = int(os.getenv("AGENT_CHECK_INTERVAL", "10"))
WARMUP_ENABLED = os.getenv("WARMUP_ENABLED", "true").lower() == "true"


def register_warmup_service_factory(factory: Callable[[], Any]) -> None:
    """
    注册缓存预热服务工厂
    """
    global _warmup_service_factory
    _warmup_service_factory = factory


async def sla_alert_background_task(
    ticket_store: Any,
    agent_manager: Any,
    sse_queues: dict
):
    """
    SLA 预警后台任务

    定期检查所有活跃工单的 SLA 状态，向负责坐席推送预警
    """
    print(f"[Scheduler] 🔔 SLA 预警任务启动 (间隔: {SLA_CHECK_INTERVAL}秒)")

    while True:
        try:
            await asyncio.sleep(SLA_CHECK_INTERVAL)

            if not ticket_store:
                continue

            # 获取所有预警
            result = ticket_store.detect_sla_alerts(
                status_filter=["warning", "urgent", "violated"]
            )
            alerts = result.get("alerts", [])

            if not alerts:
                continue

            # 按负责坐席分组推送
            alerts_by_agent = {}
            for alert in alerts:
                agent_id = alert.get("assigned_to")
                if agent_id:
                    if agent_id not in alerts_by_agent:
                        alerts_by_agent[agent_id] = []
                    alerts_by_agent[agent_id].append(alert)

            # 推送给各坐席
            import time
            for agent_id, agent_alerts in alerts_by_agent.items():
                if agent_manager:
                    agent = agent_manager.get_agent_by_id(agent_id)
                    if agent and agent.username in sse_queues:
                        try:
                            await sse_queues[agent.username].put({
                                "type": "sla_alert",
                                "alerts": agent_alerts,
                                "count": len(agent_alerts),
                                "timestamp": time.time()
                            })
                        except Exception:
                            pass

        except asyncio.CancelledError:
            print("[Scheduler] 🔔 SLA 预警任务已停止")
            break
        except Exception as e:
            print(f"[Scheduler] ❌ SLA 预警检查异常: {e}")
            await asyncio.sleep(5)


async def agent_heartbeat_monitor_task(agent_manager: Any):
    """
    坐席心跳监控后台任务

    定期检查所有坐席的心跳超时情况，自动设置离线
    """
    print(f"[Scheduler] 💓 心跳监控启动 (超时: {AGENT_OFFLINE_THRESHOLD}秒, 间隔: {AGENT_CHECK_INTERVAL}秒)")

    while True:
        try:
            await asyncio.sleep(AGENT_CHECK_INTERVAL)

            if not agent_manager:
                continue

            import time
            from infrastructure.security.agent_auth import AgentStatus

            current_time = time.time()

            for agent in agent_manager.get_all_agents():
                if agent.status in {AgentStatus.ONLINE, AgentStatus.BUSY}:
                    idle_seconds = current_time - agent.last_active_at

                    if idle_seconds > AGENT_OFFLINE_THRESHOLD:
                        print(f"[Scheduler] ⚠️ 坐席【{agent.name}】心跳超时 ({idle_seconds:.0f}秒)，自动离线")
                        agent_manager.update_status(
                            agent.username,
                            AgentStatus.OFFLINE,
                            f"心跳超时（{int(idle_seconds)}秒无活动）"
                        )

        except asyncio.CancelledError:
            print("[Scheduler] 💓 心跳监控已停止")
            break
        except Exception as e:
            print(f"[Scheduler] ❌ 心跳监控异常: {e}")
            await asyncio.sleep(5)


def start_background_tasks(
    ticket_store: Any = None,
    agent_manager: Any = None,
    sse_queues: dict = None
):
    """
    启动后台任务

    Args:
        ticket_store: 工单存储（SLA 预警需要）
        agent_manager: 坐席管理器（心跳监控需要）
        sse_queues: SSE 队列（SLA 预警推送需要）
    """
    global _sla_task, _heartbeat_task, _initialized

    if _initialized:
        return

    # SLA 预警任务
    if ticket_store and sse_queues:
        _sla_task = asyncio.create_task(
            sla_alert_background_task(ticket_store, agent_manager, sse_queues)
        )

    # 心跳监控任务
    if agent_manager:
        _heartbeat_task = asyncio.create_task(
            agent_heartbeat_monitor_task(agent_manager)
        )

    _initialized = True
    print("[Scheduler] ✅ 后台任务已启动")


def start_warmup_scheduler():
    """
    启动缓存预热调度器

    使用 APScheduler 定时执行预热任务
    """
    global _warmup_scheduler

    if not WARMUP_ENABLED:
        print("[Scheduler] ⏭️ 缓存预热已禁用")
        return

    try:
        from apscheduler.schedulers.asyncio import AsyncIOScheduler
        from apscheduler.triggers.cron import CronTrigger

        if _warmup_service_factory is None:
            print("[Scheduler] ⚠️ 未注册缓存预热服务，跳过调度器启动")
            return

        warmup_service = _warmup_service_factory()
        _warmup_scheduler = AsyncIOScheduler()

        # Chat history cleanup - daily at 03:00 (server timezone)
        try:
            from infrastructure.scheduler.tasks.cleanup_chat_history import cleanup_old_chat_messages

            _warmup_scheduler.add_job(
                lambda: asyncio.create_task(cleanup_old_chat_messages()),
                CronTrigger(hour=3, minute=0),
                id="cleanup_chat_history",
                name="聊天记录清理",
                replace_existing=True,
            )
        except Exception as e:
            print(f"[Scheduler] ⚠️ 聊天记录清理任务注册失败: {e}")

        # 02:00 UTC - 全量预热
        _warmup_scheduler.add_job(
            warmup_service.full_warmup,
            CronTrigger(hour=2, minute=0),
            id="warmup_full",
            name="全量预热",
            replace_existing=True
        )

        # 08:00/14:00/20:00 UTC - 增量预热
        for hour in [8, 14, 20]:
            _warmup_scheduler.add_job(
                warmup_service.incremental_warmup,
                CronTrigger(hour=hour, minute=0),
                id=f"warmup_incremental_{hour}",
                name=f"增量预热 ({hour}:00 UTC)",
                replace_existing=True
            )

        # CDN 健康检查 - 每周日 03:00 UTC
        try:
            from infrastructure.monitoring.cdn_health import run_health_check
            _warmup_scheduler.add_job(
                lambda: asyncio.create_task(run_health_check(auto_fix=True)),
                CronTrigger(day_of_week='sun', hour=3, minute=0),
                id="cdn_health_check",
                name="CDN 健康检查",
                replace_existing=True
            )
        except ImportError:
            pass

        _warmup_scheduler.start()
        print("[Scheduler] ✅ 缓存预热调度器启动")
        print("   📅 全量预热: 02:00 UTC")
        print("   📅 增量预热: 08:00/14:00/20:00 UTC")

    except Exception as e:
        print(f"[Scheduler] ⚠️ 缓存预热调度器启动失败: {e}")


async def shutdown_background_tasks():
    """关闭所有后台任务"""
    global _sla_task, _heartbeat_task, _warmup_scheduler

    if _sla_task:
        _sla_task.cancel()
        try:
            await _sla_task
        except asyncio.CancelledError:
            pass

    if _heartbeat_task:
        _heartbeat_task.cancel()
        try:
            await _heartbeat_task
        except asyncio.CancelledError:
            pass

    if _warmup_scheduler:
        _warmup_scheduler.shutdown(wait=False)
        print("[Scheduler] ⏹️ 缓存预热调度器已关闭")

    print("[Scheduler] 👋 后台任务已关闭")


def reset():
    """重置初始化状态（仅用于测试）"""
    global _sla_task, _heartbeat_task, _warmup_scheduler, _initialized
    _sla_task = None
    _heartbeat_task = None
    _warmup_scheduler = None
    _initialized = False
