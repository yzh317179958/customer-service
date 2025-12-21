# -*- coding: utf-8 -*-
"""
Agent Workbench - Warmup Handler

缓存预热管理 API 端点

Endpoints:
- GET /warmup/status - 获取预热状态
- POST /warmup/trigger - 触发预热任务
- GET /warmup/history - 获取预热历史
- POST /warmup/stop - 停止预热任务
"""

import time
import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/warmup", tags=["Warmup Service"])

# 全局预热调度器引用（由 main.py 设置）
_warmup_scheduler = None


def set_warmup_scheduler(scheduler):
    """设置预热调度器引用"""
    global _warmup_scheduler
    _warmup_scheduler = scheduler


def get_warmup_scheduler():
    """获取预热调度器"""
    return _warmup_scheduler


@router.get("/status")
async def get_warmup_status():
    """
    获取预热服务状态

    Returns:
        预热服务状态信息
    """
    try:
        from services.shopify.warmup import get_warmup_service
        warmup_service = get_warmup_service()

        status = warmup_service.get_status()

        # 添加调度器信息
        scheduler = get_warmup_scheduler()
        if scheduler:
            jobs = []
            for job in scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
            status["scheduler"] = {
                "running": scheduler.running,
                "jobs": jobs
            }
        else:
            status["scheduler"] = None

        return {
            "success": True,
            "data": status
        }

    except Exception as e:
        print(f"❌ 获取预热状态失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/trigger")
async def trigger_warmup(
    warmup_type: str = "incremental",
    days: int = 7
):
    """
    手动触发预热任务

    Args:
        warmup_type: 预热类型 (full/incremental)
        days: 预热天数 (仅全量预热生效)

    Returns:
        触发结果
    """
    try:
        from services.shopify.warmup import get_warmup_service
        warmup_service = get_warmup_service()

        if warmup_service.is_running:
            return {
                "success": False,
                "error": "预热任务正在执行中",
                "message": "请等待当前任务完成后再触发"
            }

        # 异步启动预热任务
        if warmup_type == "full":
            task = asyncio.create_task(warmup_service.full_warmup(days=days))
            message = f"全量预热任务已启动 ({days} 天)"
        else:
            task = asyncio.create_task(warmup_service.incremental_warmup())
            message = "增量预热任务已启动"

        return {
            "success": True,
            "message": message,
            "warmup_type": warmup_type,
            "task_id": f"warmup_{warmup_type}_{int(time.time())}"
        }

    except Exception as e:
        print(f"❌ 触发预热失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"触发失败: {str(e)}"
        )


@router.get("/history")
async def get_warmup_history(limit: int = 10):
    """
    获取预热历史记录

    Args:
        limit: 返回数量限制

    Returns:
        预热历史列表
    """
    try:
        from services.shopify.warmup import get_warmup_service
        warmup_service = get_warmup_service()

        history = warmup_service.get_history(limit=limit)

        return {
            "success": True,
            "data": {
                "history": history,
                "total": len(history)
            }
        }

    except Exception as e:
        print(f"❌ 获取预热历史失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/stop")
async def stop_warmup():
    """
    停止当前预热任务

    Returns:
        停止结果
    """
    try:
        from services.shopify.warmup import get_warmup_service
        warmup_service = get_warmup_service()

        if not warmup_service.is_running:
            return {
                "success": False,
                "message": "没有正在运行的预热任务"
            }

        warmup_service.stop()

        return {
            "success": True,
            "message": "已发送停止信号，任务将在当前订单处理完成后停止"
        }

    except Exception as e:
        print(f"❌ 停止预热失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
