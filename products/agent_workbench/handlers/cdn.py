# -*- coding: utf-8 -*-
"""
Agent Workbench - CDN Handler

CDN 健康检查 API 端点

Endpoints:
- POST /cdn/health-check - 触发 CDN 健康检查
- GET /cdn/health-log - 获取健康检查日志
"""

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/cdn", tags=["CDN Health"])


@router.post("/health-check")
async def trigger_cdn_health_check(auto_fix: bool = False):
    """
    手动触发 CDN URL 健康检查

    Args:
        auto_fix: 是否自动修复失效的 URL

    Returns:
        检查结果
    """
    try:
        from infrastructure.monitoring.cdn_health import run_health_check

        # 异步执行检查
        results = await run_health_check(auto_fix=auto_fix)

        return {
            "success": True,
            "data": {
                "check_time": results.get("check_time"),
                "total": results.get("total"),
                "valid": results.get("valid"),
                "invalid": results.get("invalid"),
                "fixed": results.get("fixed", 0),
                "auto_fix_enabled": auto_fix
            }
        }

    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="CDN 健康检查模块未找到"
        )
    except Exception as e:
        print(f"❌ CDN 健康检查失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"检查失败: {str(e)}"
        )


@router.get("/health-log")
async def get_cdn_health_log():
    """
    获取最近的 CDN 健康检查日志

    Returns:
        最近一次检查的详细结果
    """
    try:
        log_file = Path(__file__).parent.parent.parent.parent / "assets" / "cdn_health_log.json"

        if not log_file.exists():
            return {
                "success": True,
                "data": None,
                "message": "暂无健康检查记录"
            }

        with open(log_file, 'r', encoding='utf-8') as f:
            log_data = json.load(f)

        return {
            "success": True,
            "data": log_data
        }

    except Exception as e:
        print(f"❌ 获取 CDN 健康日志失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
