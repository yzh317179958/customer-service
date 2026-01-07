# -*- coding: utf-8 -*-
"""
Agent Workbench - Shopify Handler

Shopify 订单查询 API 端点
支持多站点订单查询、物流追踪、健康检查

Endpoints:
- GET /shopify/sites - 获取已配置站点列表
- GET /shopify/{site}/orders - 按站点查询订单
- GET /shopify/{site}/orders/search - 按站点搜索订单
- GET /shopify/orders/global-search - 跨站点搜索订单
- GET /shopify/orders/global-email-search - 跨站点邮箱搜索
- GET /shopify/{site}/orders/count - 订单数量统计
- GET /shopify/{site}/orders/{order_id} - 订单详情
- GET /shopify/{site}/orders/{order_id}/tracking - 订单物流
- GET /shopify/{site}/health - 站点健康检查
- GET /shopify/health/all - 全站点健康检查
- GET /shopify/orders - UK站点订单查询（兼容）
- GET /shopify/orders/search - UK站点搜索（兼容）
- GET /shopify/orders/count - UK站点统计（兼容）
- GET /shopify/orders/{order_id} - UK订单详情（兼容）
- GET /shopify/tracking - 全站点物流查询
- GET /shopify/orders/{order_id}/tracking - UK物流（兼容）
- GET /shopify/health - UK健康检查（兼容）
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from services.shopify.service import (
    ShopifyService,
    get_shopify_service,
    search_order_across_sites,
    search_orders_by_email_across_sites,
    get_all_sites_health,
    get_configured_sites_list,
)
from services.shopify.client import ShopifyAPIError
from services.shopify.sites import get_all_configured_sites
from services.asset.service import match_order_items_images
from services.tracking import get_tracking_service
from infrastructure.security import require_internal_api_key

router = APIRouter(
    prefix="/shopify",
    tags=["Shopify Orders"],
    dependencies=[Depends(require_internal_api_key)],
)


# ============================================================================
# 多站点 API
# ============================================================================

@router.get("/sites")
async def get_shopify_sites():
    """
    获取所有已配置的 Shopify 站点列表

    Returns:
        站点列表（包含站点代码、名称、域名、货币）
    """
    try:
        sites = get_configured_sites_list()
        return {
            "success": True,
            "data": {
                "sites": sites,
                "total": len(sites)
            }
        }
    except Exception as e:
        print(f"❌ 获取站点列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/{site}/orders")
async def get_shopify_site_orders(
    site: str,
    email: str,
    limit: int = 10,
    status: str = "any"
):
    """
    按客户邮箱查询指定站点的订单列表

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
        email: 客户邮箱
        limit: 返回数量限制 (1-50)
        status: 订单状态筛选 (open/closed/cancelled/any)

    Returns:
        订单列表
    """
    try:
        # 参数验证
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=400,
                detail="INVALID_LIMIT: limit 必须在 1-50 之间"
            )

        if status not in ["open", "closed", "cancelled", "any"]:
            raise HTTPException(
                status_code=400,
                detail="INVALID_STATUS: status 必须是 open/closed/cancelled/any"
            )

        # 调用服务
        service = get_shopify_service(site)
        result = await service.get_orders_by_email(email, limit=limit, status=status)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误 ({site}): {e.message}")
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            raise HTTPException(
                status_code=404,
                detail=f"SITE_NOT_FOUND: 站点 {site.upper()} 未配置"
            )
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查询订单列表失败 ({site}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/{site}/orders/search")
async def search_shopify_site_order(
    site: str,
    q: str
):
    """
    按订单号搜索指定站点的订单

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
        q: 订单号关键词

    Returns:
        订单详情
    """
    try:
        # 参数验证 - 返回友好提示而不是抛错，避免 Coze 工作流阻塞
        if not q or len(q) < 3:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q or "",
                    "site_code": site,
                    "message": "INVALID_QUERY: Please provide a valid order number (at least 3 characters)"
                }
            }

        # 调用服务
        service = get_shopify_service(site)
        result = await service.search_order_by_number(q)

        # 订单不存在时返回空值
        if result is None:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q,
                    "site_code": site,
                    "message": "ORDER_NOT_FOUND: 未找到该订单号"
                }
            }

        # 为订单商品添加图片 URL
        if result.get("order") and result["order"].get("line_items"):
            base_url = "https://ai.fiido.com/assets"
            result["order"]["line_items"] = match_order_items_images(
                result["order"]["line_items"],
                base_url=base_url
            )

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误 ({site}): {e.message}")
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            raise HTTPException(
                status_code=404,
                detail=f"SITE_NOT_FOUND: 站点 {site.upper()} 未配置"
            )
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 搜索订单失败 ({site}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/orders/global-search")
async def search_shopify_order_global(q: str):
    """
    跨站点搜索订单

    根据订单号前缀自动检测站点，或遍历所有站点搜索

    Args:
        q: 订单号关键词

    Returns:
        订单详情（包含站点信息）
    """
    try:
        # 参数验证 - 返回友好提示而不是抛错，避免 Coze 工作流阻塞
        if not q or len(q) < 3:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q or "",
                    "message": "INVALID_QUERY: Please provide a valid order number (at least 3 characters)"
                }
            }

        # 调用跨站点搜索
        result = await search_order_across_sites(q)

        # 订单不存在时返回空值
        if result is None:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q,
                    "message": "ORDER_NOT_FOUND: 在所有站点均未找到该订单号"
                }
            }

        # 为订单商品添加图片 URL
        if result.get("order") and result["order"].get("line_items"):
            base_url = "https://ai.fiido.com/assets"
            result["order"]["line_items"] = match_order_items_images(
                result["order"]["line_items"],
                base_url=base_url
            )

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 跨站点搜索订单失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/orders/global-email-search")
async def search_shopify_orders_by_email_global(
    email: str,
    limit: int = 10
):
    """
    跨站点按邮箱搜索订单

    自动遍历所有已配置站点，汇总该邮箱的所有订单。

    Args:
        email: 客户邮箱地址
        limit: 每个站点返回的订单数量限制 (1-50)

    Returns:
        所有站点的订单汇总
    """
    try:
        # 参数验证
        if not email or "@" not in email:
            raise HTTPException(
                status_code=400,
                detail="INVALID_EMAIL: 请提供有效的邮箱地址"
            )

        if limit < 1 or limit > 50:
            limit = 10

        # 调用跨站点邮箱搜索
        result = await search_orders_by_email_across_sites(email, limit=limit)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 跨站点邮箱搜索失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/{site}/orders/count")
async def get_shopify_site_order_count(
    site: str,
    status: str = "any"
):
    """
    获取指定站点的订单数量统计

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
        status: 订单状态筛选 (open/closed/cancelled/any)

    Returns:
        订单数量
    """
    try:
        if status not in ["open", "closed", "cancelled", "any"]:
            raise HTTPException(
                status_code=400,
                detail="INVALID_STATUS: status 必须是 open/closed/cancelled/any"
            )

        service = get_shopify_service(site)
        result = await service.get_order_count(status=status)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            raise HTTPException(
                status_code=404,
                detail=f"SITE_NOT_FOUND: 站点 {site.upper()} 未配置"
            )
        print(f"❌ Shopify API 错误 ({site}): {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取订单数量失败 ({site}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/{site}/orders/{order_id}")
async def get_shopify_site_order_detail(
    site: str,
    order_id: str
):
    """
    获取指定站点的订单详情

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
        order_id: Shopify 订单 ID

    Returns:
        订单详情
    """
    try:
        service = get_shopify_service(site)
        result = await service.get_order_detail(order_id)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5002:  # ORDER_NOT_FOUND
            return {
                "success": True,
                "data": {
                    "order": None,
                    "order_id": order_id,
                    "site_code": site,
                    "message": "ORDER_NOT_FOUND: 未找到该订单"
                }
            }
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            raise HTTPException(
                status_code=404,
                detail=f"SITE_NOT_FOUND: 站点 {site.upper()} 未配置"
            )
        print(f"❌ Shopify API 错误 ({site}): {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取订单详情失败 ({site}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/{site}/orders/{order_id}/tracking")
async def get_shopify_site_order_tracking(
    site: str,
    order_id: str
):
    """
    获取指定站点的订单物流信息

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)
        order_id: Shopify 订单 ID

    Returns:
        物流信息（包含 17track 轨迹事件）
    """
    # 检查 order_id 是否为空或无效值
    if not order_id or order_id in ("null", "None", "undefined", ""):
        return {
            "success": True,
            "data": {
                "tracking": None,
                "order_id": order_id,
                "site_code": site,
                "message": "INVALID_ORDER_ID: 订单ID为空，无法查询物流"
            }
        }

    try:
        service = get_shopify_service(site)
        result = await service.get_order_tracking(order_id)

        # 如果有运单号，调用 17track 获取轨迹事件
        tracking_data = result.get("tracking")
        primary_tracking = tracking_data.get("primary_tracking") if tracking_data else None
        tracking_number = primary_tracking.get("number") if primary_tracking else None

        if tracking_data and tracking_number:
            try:
                tracking_service = get_tracking_service()
                tracking_info = await tracking_service.get_tracking_info_with_auto_register(
                    tracking_number=tracking_number,
                    carrier=primary_tracking.get("company"),
                    order_id=order_id,
                    order_number=tracking_data.get("order_number"),
                )
                if tracking_info:
                    # 添加 17track 返回的事件列表
                    events = []
                    if tracking_info.events:
                        for event in tracking_info.events:
                            events.append({
                                "timestamp": event.timestamp_str or (event.timestamp.isoformat() if event.timestamp else None),
                                "description": event.description or event.status,
                                "description_zh": event.status_zh or event.description_zh,
                                "location": event.location,
                            })
                    tracking_data["events"] = events
                    # 添加物流状态
                    if tracking_info.status:
                        tracking_data["shipment_status"] = tracking_info.status.value
                        tracking_data["shipment_status_zh"] = tracking_info.status.zh
                    if tracking_info.is_pending:
                        tracking_data["is_pending"] = True
            except Exception as e:
                # 17track 查询失败不影响主流程，记录日志即可
                print(f"⚠️ 17track 物流查询失败: {tracking_number}, 错误: {e}")

        # 添加前端兼容字段（从 primary_tracking 提取）
        if tracking_data and primary_tracking:
            tracking_data["tracking_number"] = primary_tracking.get("number")
            tracking_data["tracking_company"] = primary_tracking.get("company")
            tracking_data["tracking_url"] = primary_tracking.get("tracking_url_generated") or primary_tracking.get("url")

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5002:  # ORDER_NOT_FOUND
            return {
                "success": True,
                "data": {
                    "tracking": None,
                    "order_id": order_id,
                    "site_code": site,
                    "message": "ORDER_NOT_FOUND: 未找到该订单的物流信息"
                }
            }
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            raise HTTPException(
                status_code=404,
                detail=f"SITE_NOT_FOUND: 站点 {site.upper()} 未配置"
            )
        print(f"❌ Shopify API 错误 ({site}): {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取物流信息失败 ({site}): {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/{site}/health")
async def shopify_site_health_check(site: str):
    """
    指定站点的 Shopify 服务健康检查

    Args:
        site: 站点代码 (us/uk/eu/de/fr/it/es/nl/pl)

    Returns:
        健康状态信息
    """
    try:
        service = get_shopify_service(site)
        result = await service.health_check()

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5007:  # SITE_NOT_CONFIGURED
            return {
                "success": False,
                "data": {
                    "site_code": site,
                    "status": "not_configured",
                    "message": f"站点 {site.upper()} 未配置"
                }
            }
        return {
            "success": False,
            "error": e.message
        }

    except Exception as e:
        print(f"❌ Shopify 健康检查失败 ({site}): {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


@router.get("/health/all")
async def shopify_all_sites_health_check():
    """
    所有站点的 Shopify 服务健康检查

    Returns:
        各站点健康状态信息
    """
    try:
        result = await get_all_sites_health()

        # 统计健康/不健康的站点
        healthy_count = sum(
            1 for status in result.values()
            if status.get("api", {}).get("status") == "healthy"
        )
        total_count = len(result)

        return {
            "success": True,
            "data": {
                "sites": result,
                "summary": {
                    "total": total_count,
                    "healthy": healthy_count,
                    "unhealthy": total_count - healthy_count
                }
            }
        }

    except Exception as e:
        print(f"❌ Shopify 全站点健康检查失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# UK 站点兼容 API（向后兼容）
# ============================================================================

@router.get("/orders")
async def get_shopify_orders(
    email: str,
    limit: int = 10,
    status: str = "any"
):
    """
    按客户邮箱查询订单列表 (UK站点，向后兼容)

    Args:
        email: 客户邮箱
        limit: 返回数量限制 (1-50)
        status: 订单状态筛选 (open/closed/cancelled/any)

    Returns:
        订单列表
    """
    try:
        # 参数验证
        if limit < 1 or limit > 50:
            raise HTTPException(
                status_code=400,
                detail="INVALID_LIMIT: limit 必须在 1-50 之间"
            )

        if status not in ["open", "closed", "cancelled", "any"]:
            raise HTTPException(
                status_code=400,
                detail="INVALID_STATUS: status 必须是 open/closed/cancelled/any"
            )

        # 调用服务
        service = get_shopify_service('uk')
        result = await service.get_orders_by_email(email, limit=limit, status=status)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 查询订单列表失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/orders/search")
async def search_shopify_order(q: str):
    """
    按订单号搜索订单 (UK站点，向后兼容)

    Args:
        q: 订单号关键词 (支持 #UK22080 或 UK22080 格式)

    Returns:
        订单详情
    """
    try:
        # 参数验证 - 返回友好提示而不是抛错，避免 Coze 工作流阻塞
        if not q or len(q) < 3:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q or "",
                    "message": "INVALID_QUERY: Please provide a valid order number (at least 3 characters)"
                }
            }

        # 调用服务
        service = get_shopify_service('uk')
        result = await service.search_order_by_number(q)

        # 订单不存在时返回空值（不抛出错误，避免 Coze 工作流阻塞）
        if result is None:
            return {
                "success": True,
                "data": {
                    "order": None,
                    "query": q,
                    "message": "ORDER_NOT_FOUND: 未找到该订单号"
                }
            }

        # 为订单商品添加图片 URL
        if result.get("order") and result["order"].get("line_items"):
            base_url = "https://ai.fiido.com/assets"
            result["order"]["line_items"] = match_order_items_images(
                result["order"]["line_items"],
                base_url=base_url
            )

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 搜索订单失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )


@router.get("/orders/count")
async def get_shopify_order_count(status: str = "any"):
    """
    获取订单数量统计 (UK站点，向后兼容)

    Args:
        status: 订单状态筛选 (open/closed/cancelled/any)

    Returns:
        订单数量
    """
    try:
        if status not in ["open", "closed", "cancelled", "any"]:
            raise HTTPException(
                status_code=400,
                detail="INVALID_STATUS: status 必须是 open/closed/cancelled/any"
            )

        service = get_shopify_service('uk')
        result = await service.get_order_count(status=status)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取订单数量失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/orders/{order_id}")
async def get_shopify_order_detail(order_id: str):
    """
    获取订单详情 (UK站点，向后兼容)

    Args:
        order_id: Shopify 订单 ID

    Returns:
        订单详情
    """
    try:
        service = get_shopify_service('uk')
        result = await service.get_order_detail(order_id)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5002:  # ORDER_NOT_FOUND - 返回空值而不是错误
            return {
                "success": True,
                "data": {
                    "order": None,
                    "order_id": order_id,
                    "message": "ORDER_NOT_FOUND: 未找到该订单"
                }
            }
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取订单详情失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/tracking")
async def get_shopify_tracking_by_query(order_id: Optional[str] = None):
    """
    获取订单物流信息（全站点支持）

    自动遍历所有站点查找订单并返回物流信息。

    Args:
        order_id: Shopify 订单 ID（可选）

    Returns:
        物流信息
    """
    # 检查 order_id 是否为空或无效值
    if not order_id or order_id in ("null", "None", "undefined", ""):
        return {
            "success": True,
            "data": {
                "tracking": None,
                "order_id": order_id or "",
                "message": "INVALID_ORDER_ID: 订单ID为空，无法查询物流"
            }
        }

    try:
        # 遍历所有已配置站点查找订单
        configured_sites = get_all_configured_sites()

        for site_code in configured_sites:
            try:
                service = get_shopify_service(site_code)
                result = await service.get_order_tracking(order_id)
                # 找到订单，返回结果
                return {
                    "success": True,
                    "data": result
                }
            except ShopifyAPIError as e:
                if e.code == 5002:  # ORDER_NOT_FOUND - 继续尝试下一个站点
                    continue
                raise
            except Exception:
                continue

        # 所有站点都没找到
        return {
            "success": True,
            "data": {
                "tracking": None,
                "order_id": order_id,
                "message": "ORDER_NOT_FOUND: 在所有站点均未找到该订单的物流信息"
            }
        }

    except ShopifyAPIError as e:
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取物流信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/orders/{order_id}/tracking")
async def get_shopify_order_tracking(order_id: str):
    """
    获取订单物流信息 (UK站点，向后兼容)

    Args:
        order_id: Shopify 订单 ID

    Returns:
        物流信息
    """
    # 检查 order_id 是否为空或无效值（Coze 可能传入 null/None/空字符串）
    if not order_id or order_id in ("null", "None", "undefined", ""):
        return {
            "success": True,
            "data": {
                "tracking": None,
                "order_id": order_id,
                "message": "INVALID_ORDER_ID: 订单ID为空，无法查询物流"
            }
        }

    try:
        service = get_shopify_service('uk')
        result = await service.get_order_tracking(order_id)

        return {
            "success": True,
            "data": result
        }

    except ShopifyAPIError as e:
        if e.code == 5002:  # ORDER_NOT_FOUND - 返回空值而不是错误
            return {
                "success": True,
                "data": {
                    "tracking": None,
                    "order_id": order_id,
                    "message": "ORDER_NOT_FOUND: 未找到该订单的物流信息"
                }
            }
        print(f"❌ Shopify API 错误: {e.message}")
        raise HTTPException(
            status_code=502,
            detail=f"SHOPIFY_ERROR: {e.message}"
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 获取物流信息失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@router.get("/health")
async def shopify_health_check():
    """
    Shopify UK 服务健康检查 (向后兼容)

    Returns:
        健康状态信息
    """
    try:
        service = get_shopify_service('uk')
        result = await service.health_check()

        return {
            "success": True,
            "data": result
        }

    except Exception as e:
        print(f"❌ Shopify 健康检查失败: {str(e)}")
        return {
            "success": False,
            "error": str(e)
        }
