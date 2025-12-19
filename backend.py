"""
Fiido智能客服后端服务
使用 FastAPI 提供 RESTful API，采用 OAuth+JWT 鉴权
支持基于 Workflow 的多轮对话

【会话隔离机制】
根据官方文档 b.md，会话隔离的核心是 session_name：
1. 前端打开页面时生成唯一的 session_id (存储在 sessionStorage)
2. 前端在每次请求中携带 session_id
3. 后端将 session_id 作为 session_name 传入 JWT，实现会话隔离
4. 工作流已恢复为静态会话 "default"，不再需要动态传入 CONVERSATION_NAME
"""

import os
import json
import time
import asyncio
from typing import Optional
from contextlib import asynccontextmanager
import uuid
import hashlib
from datetime import datetime, timezone
import csv
import io
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, field_validator
from dotenv import load_dotenv
from typing import Dict, Any, List, Literal

from cozepy import Coze, TokenAuth, JWTAuth, JWTOAuthApp
import httpx

MAX_TICKET_EXPORT_ROWS = 10000

# 导入 OAuth Token 管理器
from src.oauth_token_manager import OAuthTokenManager

# 导入 SessionState 和 Regulator 模块（P0 任务）
from src.session_state import (
    SessionState,
    SessionStatus,
    InMemorySessionStore,
    Message,
    MessageRole,
    EscalationInfo
)
from src.redis_session_store import RedisSessionStore  # Redis 存储实现
from src.regulator import Regulator, RegulatorConfig
from src.shift_config import get_shift_config, is_in_shift
from src.email_service import get_email_service, send_escalation_email

# 导入坐席认证系统模块
from src.agent_auth import (
    AgentManager,
    AgentTokenManager,
    initialize_super_admin,
    LoginRequest,
    LoginResponse,
    agent_to_dict,
    Agent,
    AgentStatus,
    UpdateAgentSkillsRequest
)

# 【模块3】导入快捷回复系统模块
from src.quick_reply import QuickReply, QuickReplyCategory, QUICK_REPLY_CATEGORIES, SUPPORTED_VARIABLES
from src.quick_reply_store import QuickReplyStore
from src.variable_replacer import VariableReplacer, build_variable_context

# 【Shopify UK】导入 Shopify UK 订单服务
# Shopify 多站点服务（v5.3.0+）
from src.shopify_service import (
    ShopifyService,
    get_shopify_service,
    search_order_across_sites,
    search_orders_by_email_across_sites,
    get_all_sites_health,
    get_configured_sites_list,
)
from src.shopify_client import ShopifyAPIError
from src.shopify_sites import detect_site_from_order_number, SiteCode
from src.shopify_service import get_shopify_service
from src.ticket import (
    Ticket,
    TicketPriority,
    TicketStatus,
    TicketType,
    TicketCustomerInfo,
    TicketCommentType,
)
from src.ticket_store import TicketStore
from src.audit_log import AuditLogStore
from src.ticket_assignment import SmartAssignmentEngine
from src.ticket_template import TicketTemplateStore, TicketTemplate
from src.automation_rules import CustomerReplyAutoReopen

# 【增量3-1】导入 SLA 计时器模块
from src.sla_timer import SLATimer, calculate_ticket_sla, SLAStatus
from src.asset_service import match_order_items_images, reload_mapping as reload_asset_mapping

# 【模块5】导入协助请求模块
from src.assist_request import (
    AssistRequest,
    AssistStatus,
    CreateAssistRequestRequest,
    AnswerAssistRequestRequest,
    assist_request_store
)

# 加载环境变量
load_dotenv()

# ====================
# 网络代理防护（禁用未受支持的 SOCKS 代理）
# ====================
PROXY_ENV_VARS = [
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
]


def _clear_proxy_env():
    """禁用影响 httpx/requests 的环境代理，避免 SOCKS 协议报错"""
    cleared = []
    for var in PROXY_ENV_VARS:
        value = os.environ.pop(var, None)
        if value:
            cleared.append((var, value))

    if cleared:
        removed = ", ".join(var for var, _ in cleared)
        print(f"⚠️  检测到代理变量，已忽略: {removed}")


_clear_proxy_env()

# 配置 HTTP 客户端超时
HTTP_TIMEOUT = httpx.Timeout(
    connect=float(os.getenv("HTTP_TIMEOUT_CONNECT", 10.0)),
    read=float(os.getenv("HTTP_TIMEOUT_READ", 30.0)),
    write=10.0,
    pool=10.0
)

ATTACHMENTS_DIR = Path(os.getenv("ATTACHMENTS_DIR", "attachments")).resolve()
ATTACHMENTS_DIR.mkdir(parents=True, exist_ok=True)

ATTACHMENT_RULES = [
    {
        "name": "image",
        "max_size": 10 * 1024 * 1024,
        "content_types": {"image/jpeg", "image/png", "image/webp", "image/gif"},
        "extensions": {".jpg", ".jpeg", ".png", ".webp", ".gif"}
    },
    {
        "name": "document",
        "max_size": 20 * 1024 * 1024,
        "content_types": {
            "application/pdf",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/plain"
        },
        "extensions": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt"}
    },
    {
        "name": "video",
        "max_size": 50 * 1024 * 1024,
        "content_types": {"video/mp4"},
        "extensions": {".mp4"}
    }
]

MAX_ATTACHMENT_SIZE_FALLBACK = 5 * 1024 * 1024


class ChatRequest(BaseModel):
    """聊天请求模型"""
    message: str
    parameters: Optional[dict] = {}
    user_id: Optional[str] = None  # 会话 ID（前端生成的唯一标识）
    conversation_id: Optional[str] = None  # Conversation ID（用于保留历史对话）


class ChatResponse(BaseModel):
    """聊天响应模型"""
    success: bool
    message: Optional[str] = None
    error: Optional[str] = None


class NewConversationRequest(BaseModel):
    """创建新对话请求模型"""
    user_id: str  # session_id


class ConversationResponse(BaseModel):
    """Conversation 响应模型"""
    success: bool
    conversation_id: Optional[str] = None
    error: Optional[str] = None


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求模型"""
    refresh_token: str


class CreateTicketRequest(BaseModel):
    """创建工单请求"""
    session_name: Optional[str] = None
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer: Optional[TicketCustomerInfo] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class UpdateTicketRequest(BaseModel):
    """更新工单请求"""
    status: Optional[TicketStatus] = None
    priority: Optional[TicketPriority] = None
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=500)
    metadata_updates: Optional[Dict[str, Any]] = None
    change_reason: Optional[str] = Field(default=None, max_length=200)


class SessionTicketRequest(BaseModel):
    """从会话创建工单的可选参数"""
    title: Optional[str] = Field(default=None, max_length=200)
    description: Optional[str] = Field(default=None, max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM


class ManualTicketRequest(BaseModel):
    """手动创建工单请求"""
    title: str = Field(..., max_length=200)
    description: str = Field(..., max_length=5000)
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer: TicketCustomerInfo
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AssignTicketRequest(BaseModel):
    agent_id: str = Field(..., max_length=100)
    agent_name: Optional[str] = Field(default=None, max_length=100)
    note: Optional[str] = Field(default=None, max_length=500)


class TicketCommentRequest(BaseModel):
    content: str = Field(..., max_length=2000)
    comment_type: TicketCommentType = TicketCommentType.INTERNAL
    notify_agent_id: Optional[str] = Field(default=None, max_length=100)
    mentions: Optional[List[str]] = Field(default=None, description="被@提醒的坐席ID列表")


class TicketTemplateRequest(BaseModel):
    name: str = Field(..., max_length=100)
    ticket_type: TicketType = TicketType.AFTER_SALE
    category: str = Field(..., max_length=100)
    priority: TicketPriority = TicketPriority.MEDIUM
    title_template: str = Field(..., max_length=200)
    description_template: str = Field(..., max_length=5000)


class TicketTemplateRenderRequest(BaseModel):
    customer_name: Optional[str] = None


class ReopenTicketRequest(BaseModel):
    reason: str = Field(..., max_length=200)
    comment: Optional[str] = Field(default=None, max_length=500)


class ArchiveTicketRequest(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=200)


class AutoArchiveRequest(BaseModel):
    older_than_days: Optional[int] = Field(default=30, ge=1, le=365)


class TicketFilters(BaseModel):
    """工单高级筛选"""
    statuses: Optional[List[TicketStatus]] = Field(default=None, description="筛选状态列表")
    priorities: Optional[List[TicketPriority]] = Field(default=None, description="筛选优先级")
    ticket_types: Optional[List[TicketType]] = Field(default=None, description="工单类型")
    assigned: Optional[str] = Field(
        default=None,
        description="指派筛选: mine / unassigned / 指定坐席ID"
    )
    assigned_agent_ids: Optional[List[str]] = Field(default=None, description="指定坐席ID列表")
    keyword: Optional[str] = Field(default=None, max_length=200, description="关键字搜索")
    tags: Optional[List[str]] = Field(default=None, description="标签匹配 (metadata.tags)")
    categories: Optional[List[str]] = Field(default=None, description="问题分类，匹配 metadata.category/categories")
    created_start: Optional[float] = Field(default=None, ge=0, description="创建起始时间(Unix秒)")
    created_end: Optional[float] = Field(default=None, ge=0, description="创建结束时间(Unix秒)")
    updated_start: Optional[float] = Field(default=None, ge=0, description="更新起始时间(Unix秒)")
    updated_end: Optional[float] = Field(default=None, ge=0, description="更新时间止(Unix秒)")
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)
    sort_by: Optional[str] = Field(default="updated_at")
    sort_desc: bool = Field(default=True)


class TicketExportRequest(BaseModel):
    format: Literal['csv', 'xlsx', 'pdf'] = 'csv'
    filters: Optional[TicketFilters] = None


class SmartAssignRequest(BaseModel):
    """智能分配推荐请求"""
    ticket_type: TicketType = TicketType.AFTER_SALE
    priority: TicketPriority = TicketPriority.MEDIUM
    customer_email: Optional[str] = None
    customer_country: Optional[str] = None
    category: Optional[str] = None
    keywords: List[str] = Field(default_factory=list, description="关键字列表")
    tags: List[str] = Field(default_factory=list, description="标签列表")


class BatchAssignRequest(BaseModel):
    """批量分配请求"""
    ticket_ids: List[str]
    target_agent_id: str = Field(..., max_length=100)
    target_agent_name: Optional[str] = Field(default=None, max_length=100)
    note: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = []
        for ticket_id in value:
            if ticket_id and ticket_id.strip():
                cleaned.append(ticket_id.strip())
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids 不能为空")
        if len(unique) > 50:
            raise ValueError("一次最多分配50个工单")
        return unique


class BatchCloseRequest(BaseModel):
    ticket_ids: List[str]
    close_reason: Optional[str] = Field(default=None, max_length=200)
    comment: Optional[str] = Field(default=None, max_length=500)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = []
        for ticket_id in value:
            if ticket_id and ticket_id.strip():
                cleaned.append(ticket_id.strip())
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids 不能为空")
        if len(unique) > 50:
            raise ValueError("一次最多操作50个工单")
        return unique


class BatchPriorityRequest(BaseModel):
    ticket_ids: List[str]
    priority: TicketPriority
    reason: Optional[str] = Field(default=None, max_length=200)

    @field_validator("ticket_ids")
    @classmethod
    def validate_ticket_ids(cls, value: List[str]) -> List[str]:
        cleaned = []
        for ticket_id in value:
            if ticket_id and ticket_id.strip():
                cleaned.append(ticket_id.strip())
        unique = list(dict.fromkeys(cleaned))
        if not unique:
            raise ValueError("ticket_ids 不能为空")
        if len(unique) > 50:
            raise ValueError("一次最多操作50个工单")
        return unique


class UpdateAgentStatusRequest(BaseModel):
    """坐席状态更新请求"""
    status: AgentStatus
    status_note: Optional[str] = Field(
        default=None,
        max_length=120,
        description="状态说明（可选）"
    )


# 全局变量
coze_client: Optional[Coze] = None
token_manager: Optional[OAuthTokenManager] = None
jwt_oauth_app: Optional[JWTOAuthApp] = None  # 用于 Chat SDK 的 JWTOAuthApp
session_store: Optional[InMemorySessionStore] = None  # 会话状态存储（P0）
regulator: Optional[Regulator] = None  # 监管策略引擎（P0）
agent_manager: Optional[AgentManager] = None  # 坐席账号管理器
agent_token_manager: Optional[AgentTokenManager] = None  # 坐席 JWT Token 管理器
quick_reply_store: Optional['QuickReplyStore'] = None  # 快捷回复存储管理器（模块3）
variable_replacer: Optional['VariableReplacer'] = None  # 变量替换器（模块3）
ticket_store: Optional['TicketStore'] = None  # 工单系统存储（L1-2）
smart_assignment_engine: Optional['SmartAssignmentEngine'] = None  # 智能分配引擎
customer_reply_auto_reopen: Optional['CustomerReplyAutoReopen'] = None  # 客户回复自动恢复规则
WORKFLOW_ID: str = ""
APP_ID: str = ""  # AI 应用 ID（应用中嵌入对话流时必需）
AUTH_MODE: str = ""  # 鉴权模式：OAUTH_JWT 或 PAT


def _format_timestamp(ts: Optional[float]) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromtimestamp(ts, timezone.utc)
        return dt.isoformat()
    except Exception:
        return str(ts)


def _tickets_to_csv_bytes(tickets: List['Ticket']) -> bytes:
    headers = [
        "ticket_id",
        "title",
        "status",
        "priority",
        "ticket_type",
        "customer_name",
        "customer_email",
        "customer_phone",
        "assigned_agent_name",
        "assigned_agent_id",
        "session_name",
        "created_at",
        "updated_at",
        "first_response_at",
        "resolved_at",
        "closed_at",
        "reopened_count",
        "description",
        "tags",
        "metadata"
    ]
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    for ticket in tickets:
        data = ticket.to_dict()
        customer = data.get("customer") or {}
        metadata = data.get("metadata") or {}
        tags = metadata.get("tags")
        if isinstance(tags, list):
            tags_value = ", ".join(str(tag) for tag in tags)
        elif isinstance(tags, str):
            tags_value = tags
        else:
            tags_value = ""
        writer.writerow([
            ticket.ticket_id,
            ticket.title,
            ticket.status.value if isinstance(ticket.status, TicketStatus) else ticket.status,
            ticket.priority.value if isinstance(ticket.priority, TicketPriority) else ticket.priority,
            ticket.ticket_type.value if isinstance(ticket.ticket_type, TicketType) else ticket.ticket_type,
            customer.get("name") or "",
            customer.get("email") or "",
            customer.get("phone") or "",
            ticket.assigned_agent_name or "",
            ticket.assigned_agent_id or "",
            ticket.session_name or "",
            _format_timestamp(ticket.created_at),
            _format_timestamp(ticket.updated_at),
            _format_timestamp(ticket.first_response_at),
            _format_timestamp(ticket.resolved_at),
            _format_timestamp(ticket.closed_at),
            ticket.reopened_count,
            ticket.description,
            tags_value,
            json.dumps(metadata, ensure_ascii=False)
        ])
    return output.getvalue().encode("utf-8-sig")

# P0-5: SSE 消息队列 - 用于人工消息推送
# 结构: {session_name: asyncio.Queue()}
sse_queues: dict = {}  # type: dict[str, asyncio.Queue]
audit_log_store: Optional[AuditLogStore] = None
ticket_template_store: Optional[TicketTemplateStore] = None


async def enqueue_sse_message(target: str, payload: dict):
    """将消息放入指定目标的 SSE 队列中，队列满时丢弃最旧的数据"""
    global sse_queues
    if target not in sse_queues:
        sse_queues[target] = asyncio.Queue()
        print(f"✅ 创建全局SSE队列: {target}")

    queue = sse_queues[target]
    try:
        queue.put_nowait(payload)
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        queue.put_nowait(payload)


async def handle_customer_reply_event(session_state: SessionState, source: str):
    """
    当会话产生客户回复时，触发自动恢复规则
    """
    global customer_reply_auto_reopen
    if not customer_reply_auto_reopen or not session_state:
        return

    try:
        updated_tickets = await customer_reply_auto_reopen.handle_reply(
            session_state,
            notify_callback=enqueue_sse_message
        )
    except Exception as exc:
        print(f"⚠️ 客户回复自动恢复执行失败: {exc}")
        return

    if not updated_tickets:
        return

    for ticket in updated_tickets:
        log_ticket_event(
            "status_changed",
            ticket.ticket_id,
            operator=None,
            details={
                "from_status": TicketStatus.WAITING_CUSTOMER.value,
                "to_status": TicketStatus.IN_PROGRESS.value,
                "trigger": "customer_reply",
                "source": source,
            }
        )
        print(f"🔄 客户回复自动恢复工单: {ticket.ticket_id} (source={source})")


def _resolve_attachment_rule(filename: str, content_type: Optional[str]):
    extension = Path(filename or "").suffix.lower()
    for rule in ATTACHMENT_RULES:
        if (content_type and content_type in rule["content_types"]) or (extension and extension in rule["extensions"]):
            return rule
    return None


async def _save_attachment_file(upload: UploadFile, dest: Path, max_size: int) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    size = 0

    try:
        with dest.open("wb") as buffer:
            while True:
                chunk = await upload.read(1024 * 1024)
                if not chunk:
                    break
                size += len(chunk)
                if size > max_size:
                    raise ValueError("FILE_TOO_LARGE")
                buffer.write(chunk)
    except Exception:
        if dest.exists():
            dest.unlink()
        raise
    finally:
        await upload.seek(0)

    return size


def _is_path_within(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def _attachment_response(ticket_id: str, attachment):
    data = attachment.dict()
    data["download_url"] = f"/api/tickets/{ticket_id}/attachments/{attachment.attachment_id}"
    return data


def log_ticket_event(
    event_type: str,
    ticket_id: str,
    operator: Optional[Dict[str, Any]],
    details: Optional[Dict[str, Any]] = None
):
    global audit_log_store
    if not audit_log_store:
        return
    operator_id = "system"
    operator_name = "system"
    if operator:
        operator_id = operator.get("agent_id") or operator.get("username") or "system"
        operator_name = operator.get("username") or operator_id
    try:
        audit_log_store.add_log(
            ticket_id=ticket_id,
            event_type=event_type,  # type: ignore[arg-type]
            operator_id=operator_id,
            operator_name=operator_name,
            details=details or {}
        )
    except Exception as exc:
        print(f"⚠️ 记录协作日志失败: {exc}")
    except asyncio.QueueFull:
        try:
            queue.get_nowait()
        except asyncio.QueueEmpty:
            pass
        queue.put_nowait(payload)

# 坐席状态相关配置
AGENT_AUTO_BUSY_SECONDS = int(os.getenv("AGENT_AUTO_BUSY_SECONDS", "300"))
AGENT_STATS_TTL = int(os.getenv("AGENT_STATS_TTL", "86400"))


def _agent_stats_key(agent_identifier: str) -> str:
    """构建坐席当日统计的 Redis Key"""
    date_key = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"agent_stats:{agent_identifier}:{date_key}"


def _update_agent_stat(agent_identifier: str, field: str, amount: float, *, as_int: bool = False):
    """更新坐席统计字段"""
    if not agent_manager or not hasattr(agent_manager, "redis"):
        return

    redis_client = getattr(agent_manager, "redis", None)
    if not redis_client:
        return

    key = _agent_stats_key(agent_identifier)
    try:
        if as_int:
            redis_client.hincrby(key, field, int(amount))
        else:
            redis_client.hincrbyfloat(key, field, float(amount))
        redis_client.expire(key, AGENT_STATS_TTL)
    except Exception as exc:
        print(f"⚠️ 更新坐席统计失败: {exc}")


def _parse_float(value: Optional[str]) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _parse_int(value: Optional[str]) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _record_agent_response_time(agent_identifier: str, seconds: float):
    """记录坐席响应时间"""
    if seconds is None or seconds < 0:
        return
    _update_agent_stat(agent_identifier, "total_response_time", seconds)
    _update_agent_stat(agent_identifier, "response_samples", 1, as_int=True)


def _record_agent_session_duration(agent_identifier: str, seconds: float):
    """记录坐席处理时长并增加完成数"""
    if seconds is None or seconds < 0:
        return
    _update_agent_stat(agent_identifier, "total_duration", seconds)
    _update_agent_stat(agent_identifier, "duration_samples", 1, as_int=True)
    _update_agent_stat(agent_identifier, "processed_count", 1, as_int=True)


def _load_agent_stats(agent_identifier: str) -> Dict[str, Any]:
    """读取坐席当日统计原始数据"""
    if not agent_manager or not hasattr(agent_manager, "redis"):
        return {}
    redis_client = getattr(agent_manager, "redis", None)
    if not redis_client:
        return {}
    key = _agent_stats_key(agent_identifier)
    try:
        return redis_client.hgetall(key) or {}
    except Exception as exc:
        print(f"⚠️ 读取坐席统计失败: {exc}")
        return {}


def _compose_today_stats(agent_identifier: str) -> Dict[str, Any]:
    """组装今日统计指标"""
    raw = _load_agent_stats(agent_identifier)
    total_response = _parse_float(raw.get("total_response_time"))
    response_samples = _parse_int(raw.get("response_samples"))
    total_duration = _parse_float(raw.get("total_duration"))
    duration_samples = _parse_int(raw.get("duration_samples"))
    satisfaction_total = _parse_float(raw.get("satisfaction_total"))
    satisfaction_samples = _parse_int(raw.get("satisfaction_samples"))
    processed = _parse_int(raw.get("processed_count"))

    avg_response = total_response / response_samples if response_samples else 0.0
    avg_duration = total_duration / duration_samples if duration_samples else 0.0
    satisfaction = satisfaction_total / satisfaction_samples if satisfaction_samples else 0.0

    return {
        "processed_count": processed,
        "avg_response_time": round(avg_response, 2),
        "avg_duration": round(avg_duration, 2),
        "satisfaction_score": round(satisfaction, 2)
    }


async def _count_agent_live_sessions(agent_identifier: str) -> int:
    """统计坐席当前处理中的会话数"""
    if not session_store:
        return 0
    try:
        live_sessions = await session_store.list_by_status(
            status=SessionStatus.MANUAL_LIVE,
            limit=500
        )
        return sum(
            1
            for session in live_sessions
            if session.assigned_agent and session.assigned_agent.id == agent_identifier
        )
    except Exception as exc:
        print(f"⚠️ 统计当前会话失败: {exc}")
        return 0


async def _build_agent_status_payload(agent_obj: Agent, agent_identifier: str) -> Dict[str, Any]:
    """构建返回给前端的状态信息"""
    today_stats = _compose_today_stats(agent_identifier)
    current_sessions = await _count_agent_live_sessions(agent_identifier)
    return {
        "status": agent_obj.status.value if isinstance(agent_obj.status, AgentStatus) else agent_obj.status,
        "status_note": agent_obj.status_note or "",
        "status_updated_at": agent_obj.status_updated_at,
        "last_active_at": agent_obj.last_active_at,
        "current_sessions": current_sessions,
        "max_sessions": agent_obj.max_sessions,
        "today_stats": today_stats
    }


def _auto_adjust_agent_status(agent_obj: Agent) -> Agent:
    """根据最近活跃时间自动切换状态"""
    if not agent_manager:
        return agent_obj

    last_active = agent_obj.last_active_at or 0
    now = time.time()
    if (
        agent_obj.status == AgentStatus.ONLINE
        and AGENT_AUTO_BUSY_SECONDS > 0
        and now - last_active > AGENT_AUTO_BUSY_SECONDS
    ):
        agent_obj.status = AgentStatus.BUSY
        if not agent_obj.status_note:
            agent_obj.status_note = "系统检测到超过5分钟无操作，已自动置为忙碌"
        agent_obj.status_updated_at = now
        try:
            agent_manager.update_agent(agent_obj)
        except Exception as exc:
            print(f"⚠️ 自动更新坐席状态失败: {exc}")
    return agent_obj


# 【增量3-4】SLA 预警后台任务配置
SLA_CHECK_INTERVAL = int(os.getenv("SLA_CHECK_INTERVAL", "60"))  # 默认60秒检查一次
_sla_task: Optional[asyncio.Task] = None  # 后台任务引用

# 【心跳超时自动离线】配置
AGENT_OFFLINE_THRESHOLD = int(os.getenv("AGENT_OFFLINE_THRESHOLD", "30"))  # 默认30秒无心跳自动离线
AGENT_CHECK_INTERVAL = int(os.getenv("AGENT_CHECK_INTERVAL", "10"))  # 默认10秒检查一次
_agent_heartbeat_task: Optional[asyncio.Task] = None  # 后台任务引用

# 【缓存预热调度】配置
_warmup_scheduler = None  # APScheduler 调度器
WARMUP_ENABLED = os.getenv("WARMUP_ENABLED", "true").lower() == "true"


async def sla_alert_background_task():
    """
    SLA 预警后台任务

    定期检查所有活跃工单的 SLA 状态，向负责坐席推送预警
    """
    global ticket_store, agent_manager, sse_queues

    print(f"🔔 SLA 预警后台任务启动 (间隔: {SLA_CHECK_INTERVAL}秒)")

    while True:
        try:
            await asyncio.sleep(SLA_CHECK_INTERVAL)

            if not ticket_store:
                continue

            # 获取所有预警（只关注 warning/urgent/violated）
            result = ticket_store.detect_sla_alerts(
                status_filter=["warning", "urgent", "violated"]
            )
            alerts = result.get("alerts", [])

            if not alerts:
                continue

            # 按负责坐席分组推送
            alerts_by_agent: Dict[str, list] = {}
            for alert in alerts:
                agent_id = alert.get("assigned_to")
                if agent_id:
                    if agent_id not in alerts_by_agent:
                        alerts_by_agent[agent_id] = []
                    alerts_by_agent[agent_id].append(alert)

            # 推送给各坐席
            for agent_id, agent_alerts in alerts_by_agent.items():
                # 查找坐席 username（SSE 队列以 username 为 key）
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
                        except Exception as push_err:
                            print(f"⚠️ SLA预警推送失败 ({agent.username}): {push_err}")

            # 同时广播给所有在线管理员
            if agent_manager:
                for agent in agent_manager.get_all_agents():
                    if agent.role == "admin" and agent.username in sse_queues:
                        try:
                            await sse_queues[agent.username].put({
                                "type": "sla_alert_summary",
                                "summary": result.get("summary", {}),
                                "timestamp": time.time()
                            })
                        except Exception:
                            pass

        except asyncio.CancelledError:
            print("🔔 SLA 预警后台任务已停止")
            break
        except Exception as e:
            print(f"❌ SLA 预警检查异常: {e}")
            await asyncio.sleep(5)  # 出错后短暂等待再重试


async def agent_heartbeat_monitor_task():
    """
    坐席心跳监控后台任务

    定期检查所有坐席的心跳超时情况，自动设置离线
    配置：
    - AGENT_OFFLINE_THRESHOLD: 心跳超时阈值（秒），默认30秒
    - AGENT_CHECK_INTERVAL: 检查间隔（秒），默认10秒
    """
    global agent_manager

    print(f"💓 坐席心跳监控启动 (超时阈值: {AGENT_OFFLINE_THRESHOLD}秒, 检查间隔: {AGENT_CHECK_INTERVAL}秒)")

    while True:
        try:
            await asyncio.sleep(AGENT_CHECK_INTERVAL)

            if not agent_manager:
                continue

            current_time = time.time()

            # 遍历所有坐席，检查心跳超时
            for agent in agent_manager.get_all_agents():
                # 只检查在线或忙碌状态的坐席
                if agent.status in {AgentStatus.ONLINE, AgentStatus.BUSY}:
                    idle_seconds = current_time - agent.last_active_at

                    if idle_seconds > AGENT_OFFLINE_THRESHOLD:
                        print(f"⚠️ 坐席【{agent.name}】({agent.username}) 心跳超时 ({idle_seconds:.0f}秒)，自动设为离线")
                        agent_manager.update_status(
                            agent.username,
                            AgentStatus.OFFLINE,
                            f"心跳超时（{int(idle_seconds)}秒无活动）"
                        )

        except asyncio.CancelledError:
            print("💓 坐席心跳监控已停止")
            break
        except Exception as e:
            print(f"❌ 坐席心跳监控异常: {e}")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(5)  # 出错后短暂等待再重试


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global coze_client, token_manager, jwt_oauth_app, session_store, regulator, agent_manager, agent_token_manager, quick_reply_store, variable_replacer, ticket_store, smart_assignment_engine, audit_log_store, ticket_template_store, WORKFLOW_ID, APP_ID, AUTH_MODE, _sla_task, _agent_heartbeat_task, customer_reply_auto_reopen, _warmup_scheduler

    # 读取配置
    WORKFLOW_ID = os.getenv("COZE_WORKFLOW_ID", "")
    APP_ID = os.getenv("COZE_APP_ID", "")
    AUTH_MODE = os.getenv("COZE_AUTH_MODE", "OAUTH_JWT")
    api_base = os.getenv("COZE_API_BASE", "https://api.coze.com")

    if not WORKFLOW_ID:
        raise ValueError("COZE_WORKFLOW_ID 环境变量未设置")
    if not APP_ID:
        raise ValueError("COZE_APP_ID 环境变量未设置")

    print(f"\n{'=' * 60}")
    print(f"🚀 Fiido 智能客服后端服务初始化")
    print(f"{'=' * 60}")
    print(f"🔐 鉴权模式: {AUTH_MODE}")
    print(f"🌐 API Base: {api_base}")
    print(f"📱 App ID: {APP_ID}")
    print(f"🔄 Workflow ID: {WORKFLOW_ID}")
    print(f"💬 多轮对话: 已启用")

    # 初始化 SessionState 存储（P0 + Redis 数据持久化）
    # 约束16.3.1 - Redis 不可用时降级到内存存储
    try:
        # 读取 Redis 配置
        USE_REDIS = os.getenv("USE_REDIS", "true").lower() == "true"
        REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        REDIS_MAX_CONNECTIONS = int(os.getenv("REDIS_MAX_CONNECTIONS", "50"))
        REDIS_TIMEOUT = float(os.getenv("REDIS_TIMEOUT", "5.0"))
        REDIS_SESSION_TTL = int(os.getenv("REDIS_SESSION_TTL", "86400"))  # 24小时

        if USE_REDIS:
            try:
                session_store = RedisSessionStore(
                    redis_url=REDIS_URL,
                    max_connections=REDIS_MAX_CONNECTIONS,
                    socket_timeout=REDIS_TIMEOUT,
                    socket_connect_timeout=REDIS_TIMEOUT,
                    default_ttl=REDIS_SESSION_TTL
                )
                print(f"✅ 使用 Redis 存储")
                print(f"   URL: {REDIS_URL}")
                print(f"   连接池: {REDIS_MAX_CONNECTIONS}")
                print(f"   TTL: {REDIS_SESSION_TTL}s ({REDIS_SESSION_TTL/3600}h)")

                # 健康检查
                health = session_store.check_health()
                if health.get("status") == "healthy":
                    print(f"   内存: {health['used_memory_mb']}MB / {health['max_memory_mb']}")
                    print(f"   会话数: {health['total_sessions']}")
                else:
                    print(f"   ⚠️ 健康检查异常: {health.get('error')}")

            except Exception as redis_error:
                print(f"❌ Redis 连接失败: {redis_error}")
                print(f"⚠️  降级到内存存储（生产环境不推荐）")
                session_store = InMemorySessionStore()
        else:
            session_store = InMemorySessionStore()
            print(f"⚠️ 使用内存存储（开发/测试环境）")

    except Exception as e:
        print(f"❌ SessionState 存储初始化失败: {str(e)}")
        print(f"⚠️  降级到内存存储")
        session_store = InMemorySessionStore()

    # 初始化 Regulator 监管引擎（P0）
    try:
        regulator_config = RegulatorConfig()
        regulator = Regulator(regulator_config)
        print(f"✅ Regulator 监管引擎初始化成功")
        print(f"   关键词: {len(regulator_config.keywords)}个")
        print(f"   失败阈值: {regulator_config.fail_threshold}")
    except Exception as e:
        print(f"⚠️  Regulator 初始化失败: {str(e)}")

    # OAuth+JWT 鉴权
    try:
        token_manager = OAuthTokenManager.from_env()
        # 获取初始 token
        access_token = token_manager.get_access_token()

        # 创建带超时配置的 HTTP 客户端（禁用环境代理以避免 SOCKS 协议问题）
        http_client = httpx.Client(
            timeout=HTTP_TIMEOUT,
            trust_env=False  # 不从环境变量读取代理配置，避免 SOCKS 协议不支持的问题
        )
        coze_client = Coze(
            auth=TokenAuth(token=access_token),
            base_url=api_base,
            http_client=http_client
        )
        print(f"✅ OAuth+JWT 鉴权初始化成功")
        print(f"   Token 预览: {access_token[:30]}...")
        print(f"   超时配置: 连接 10s, 读取 30s")

        # 创建 JWTOAuthApp (用于 Chat SDK token 生成)
        private_key_file = os.getenv("COZE_OAUTH_PRIVATE_KEY_FILE")
        if private_key_file and os.path.exists(private_key_file):
            with open(private_key_file, "r") as f:
                private_key = f.read()

            jwt_oauth_app = JWTOAuthApp(
                client_id=os.getenv("COZE_OAUTH_CLIENT_ID"),
                private_key=private_key,
                public_key_id=os.getenv("COZE_OAUTH_PUBLIC_KEY_ID"),
                base_url=api_base,
            )
            print(f"✅ JWTOAuthApp 初始化成功 (用于 Chat SDK)")
        else:
            print(f"⚠️  未找到私钥文件，Chat SDK token 生成将不可用")

    except Exception as e:
        raise ValueError(f"OAuth+JWT 初始化失败: {str(e)}")

    # 初始化坐席认证系统
    try:
        # JWT密钥（生产环境必须使用强随机密钥）
        JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev_secret_key_change_in_production_2025")

        # 初始化坐席 Token 管理器
        agent_token_manager = AgentTokenManager(
            secret_key=JWT_SECRET,
            algorithm="HS256",
            access_token_expire_minutes=int(os.getenv("AGENT_TOKEN_EXPIRE_MINUTES", "60")),
            refresh_token_expire_days=int(os.getenv("AGENT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        )

        # 初始化坐席账号管理器
        agent_manager = AgentManager(session_store)

        # 初始化超级管理员账号（系统根账号）
        print(f"🔐 初始化坐席认证系统...")
        admin_username = os.getenv("SUPER_ADMIN_USERNAME", "admin")
        admin_password = os.getenv("SUPER_ADMIN_PASSWORD", "admin123")
        initialize_super_admin(agent_manager, admin_username, admin_password)

        print(f"✅ 坐席认证系统初始化成功")
        print(f"   Token过期时间: 60分钟")
        print(f"   刷新Token过期: 7天")
        print(f"   超级管理员: {admin_username}")
        print(f"   ⚠️  其他坐席账号请通过管理员在系统内创建")

    except Exception as e:
        print(f"⚠️  坐席认证系统初始化失败: {str(e)}")
        print(f"   坐席登录功能将不可用")

    # 【模块3】初始化快捷回复系统
    try:
        # 使用session_store中的redis_client
        if USE_REDIS and hasattr(session_store, 'redis'):
            quick_reply_store = QuickReplyStore(session_store.redis)
            variable_replacer = VariableReplacer()
            print(f"✅ 快捷回复系统初始化成功")
            print(f"   存储: Redis")
        else:
            quick_reply_store = None
            variable_replacer = VariableReplacer()
            print(f"⚠️  快捷回复系统：内存存储未实现，功能受限")

    except Exception as e:
        print(f"⚠️  快捷回复系统初始化失败: {str(e)}")
        quick_reply_store = None
        variable_replacer = VariableReplacer()

    # 【L1-2】初始化工单系统（MVP）
    try:
        if USE_REDIS and hasattr(session_store, 'redis'):
            ticket_store = TicketStore(session_store.redis)
            print("✅ 工单系统初始化成功 (Redis)")
        else:
            ticket_store = TicketStore()
            print("⚠️  工单系统使用内存存储，仅适用于开发环境")
    except Exception as e:
        ticket_store = TicketStore()
        print(f"⚠️  工单系统初始化失败，回退到内存存储: {str(e)}")
    finally:
        if ticket_store:
            if customer_reply_auto_reopen:
                customer_reply_auto_reopen.update_dependencies(
                    ticket_store=ticket_store,
                    agent_manager=agent_manager
                )
            else:
                customer_reply_auto_reopen = CustomerReplyAutoReopen(
                    ticket_store,
                    agent_manager=agent_manager
                )

    # 初始化协作日志存储
    try:
        if USE_REDIS and hasattr(session_store, 'redis'):
            audit_log_store = AuditLogStore(session_store.redis)
            print("✅ 协作日志存储初始化成功 (Redis)")
        else:
            audit_log_store = AuditLogStore()
            print("⚠️ 协作日志使用内存存储，仅用于开发/测试")
    except Exception as e:
        audit_log_store = AuditLogStore()
        print(f"⚠️ 协作日志初始化失败，使用内存存储: {str(e)}")

    # 初始化工单模板存储
    try:
        if USE_REDIS and hasattr(session_store, 'redis'):
            ticket_template_store = TicketTemplateStore(session_store.redis)
            print("✅ 工单模板存储初始化成功 (Redis)")
        else:
            ticket_template_store = TicketTemplateStore()
            print("⚠️ 工单模板使用内存存储，仅用于开发/测试")
    except Exception as e:
        ticket_template_store = TicketTemplateStore()
        print(f"⚠️ 工单模板初始化失败，使用内存存储: {str(e)}")

    # 智能分配引擎
    try:
        if agent_manager and session_store:
            smart_assignment_engine = SmartAssignmentEngine(
                agent_manager=agent_manager,
                session_store=session_store
            )
            print("✅ 智能分配引擎初始化成功")
        else:
            smart_assignment_engine = None
            print("⚠️ 智能分配引擎未启用（缺少依赖）")
    except Exception as e:
        smart_assignment_engine = None
        print(f"⚠️ 智能分配引擎初始化失败: {str(e)}")

    print(f"{'=' * 60}\n")

    # 【增量3-4】启动 SLA 预警后台任务
    global _sla_task, _agent_heartbeat_task
    _sla_task = asyncio.create_task(sla_alert_background_task())

    # 【心跳超时自动离线】启动坐席心跳监控任务
    _agent_heartbeat_task = asyncio.create_task(agent_heartbeat_monitor_task())

    # 【缓存预热】启动 APScheduler 调度器
    if WARMUP_ENABLED:
        try:
            from apscheduler.schedulers.asyncio import AsyncIOScheduler
            from apscheduler.triggers.cron import CronTrigger
            from src.warmup_service import get_warmup_service

            warmup_service = get_warmup_service()
            _warmup_scheduler = AsyncIOScheduler()

            # 配置预热任务调度
            # 02:00 UTC (10:00 北京时间) - 全量预热
            _warmup_scheduler.add_job(
                warmup_service.full_warmup,
                CronTrigger(hour=2, minute=0),
                id="warmup_full",
                name="全量预热 (7天订单)",
                replace_existing=True
            )

            # 08:00 UTC (16:00 北京时间) - 增量预热
            _warmup_scheduler.add_job(
                warmup_service.incremental_warmup,
                CronTrigger(hour=8, minute=0),
                id="warmup_incremental_08",
                name="增量预热 (08:00 UTC)",
                replace_existing=True
            )

            # 14:00 UTC (22:00 北京时间) - 增量预热
            _warmup_scheduler.add_job(
                warmup_service.incremental_warmup,
                CronTrigger(hour=14, minute=0),
                id="warmup_incremental_14",
                name="增量预热 (14:00 UTC)",
                replace_existing=True
            )

            # 20:00 UTC (04:00 北京时间) - 增量预热
            _warmup_scheduler.add_job(
                warmup_service.incremental_warmup,
                CronTrigger(hour=20, minute=0),
                id="warmup_incremental_20",
                name="增量预热 (20:00 UTC)",
                replace_existing=True
            )

            # 【CDN 健康检查】每周日 03:00 UTC (11:00 北京时间) 检查并自动修复
            try:
                from src.cdn_health_checker import run_health_check
                _warmup_scheduler.add_job(
                    lambda: asyncio.create_task(run_health_check(auto_fix=True)),
                    CronTrigger(day_of_week='sun', hour=3, minute=0),
                    id="cdn_health_check",
                    name="CDN URL 健康检查 (每周日)",
                    replace_existing=True
                )
                print("   📅 CDN 健康检查: 03:00 UTC (每周日)")
            except ImportError:
                print("   ⚠️ CDN 健康检查模块未找到")

            _warmup_scheduler.start()
            print("✅ 缓存预热调度器启动")
            print("   📅 全量预热: 02:00 UTC (每天)")
            print("   📅 增量预热: 08:00/14:00/20:00 UTC")

        except Exception as e:
            print(f"⚠️ 缓存预热调度器启动失败: {e}")
            _warmup_scheduler = None
    else:
        print("⏭️ 缓存预热已禁用 (WARMUP_ENABLED=false)")

    # 初始化 AI 客服模块依赖
    try:
        from products.ai_chatbot import dependencies as ai_deps
        ai_deps.set_coze_client(coze_client)
        ai_deps.set_token_manager(token_manager)
        ai_deps.set_session_store(session_store)
        ai_deps.set_regulator(regulator)
        ai_deps.set_jwt_oauth_app(jwt_oauth_app)
        ai_deps.set_config(WORKFLOW_ID, APP_ID)
        print("✅ AI 客服模块依赖初始化成功")
    except Exception as e:
        print(f"⚠️ AI 客服模块依赖初始化失败: {e}")

    yield

    # 关闭时清理
    if _sla_task:
        _sla_task.cancel()
        try:
            await _sla_task
        except asyncio.CancelledError:
            pass

    if _agent_heartbeat_task:
        _agent_heartbeat_task.cancel()
        try:
            await _agent_heartbeat_task
        except asyncio.CancelledError:
            pass

    # 关闭预热调度器
    if _warmup_scheduler:
        _warmup_scheduler.shutdown(wait=False)
        print("⏹️ 缓存预热调度器已关闭")

    print("👋 关闭 Coze 客户端")


# 创建 FastAPI 应用
app = FastAPI(
    title="Fiido智能客服API",
    description="基于 Coze Workflow 的智能客服后端服务，支持 OAuth+JWT 鉴权和多轮对话",
    version="2.1.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取当前文件所在目录（用于提供静态文件）
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 挂载静态文件目录（提供图片等资源）
# 访问方式：http://IP:8000/fiido2.png
try:
    app.mount("/static", StaticFiles(directory=CURRENT_DIR), name="static")
except Exception as e:
    print(f"⚠️  静态文件挂载失败: {e}")

# 挂载素材目录（产品图片、Logo 等）
# 访问方式：https://ai.fiido.com/assets/products/c11-pro.webp
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
if os.path.exists(ASSETS_DIR):
    try:
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
        print(f"✅ 素材目录已挂载: /assets -> {ASSETS_DIR}")
    except Exception as e:
        print(f"⚠️  素材目录挂载失败: {e}")
else:
    print(f"⚠️  素材目录不存在: {ASSETS_DIR}")

# 注册 AI 客服模块路由
from products.ai_chatbot import get_router as get_ai_chatbot_router
app.include_router(get_ai_chatbot_router(), prefix="/api", tags=["AI智能客服"])
print("✅ AI 客服模块路由已注册: /api/*")

# 注册坐席工作台模块路由
from products.agent_workbench import get_router as get_agent_workbench_router
app.include_router(get_agent_workbench_router(), prefix="/api", tags=["坐席工作台"])
print("✅ 坐席工作台模块路由已注册: /api/*")


# ====================
# JWT 权限中间件 (Agent Authorization Middleware)
# ====================

# 初始化 HTTPBearer 安全方案
security = HTTPBearer()


async def verify_agent_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    验证 JWT Token

    Args:
        credentials: HTTP Bearer 凭证

    Returns:
        Dict: Token 载荷（包含 agent_id, username, role）

    Raises:
        HTTPException 401: Token 无效或已过期
    """
    if not agent_token_manager:
        raise HTTPException(
            status_code=503,
            detail="坐席认证系统未初始化"
        )

    token = credentials.credentials

    # 验证 Token
    payload = agent_token_manager.verify_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Token 无效或已过期"
        )

    return payload


async def require_admin(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求管理员权限

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    Raises:
        HTTPException 403: 权限不足（非管理员）
    """
    if agent.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="需要管理员权限"
        )

    return agent


async def require_agent(
    agent: Dict[str, Any] = Depends(verify_agent_token)
) -> Dict[str, Any]:
    """
    要求坐席权限（包括管理员）

    Args:
        agent: 经过 verify_agent_token 验证的坐席信息

    Returns:
        Dict: Token 载荷

    说明:
        此函数用于保护坐席工作台 API
        管理员和普通坐席都可以访问
    """
    return agent

@app.get("/")
async def root():
    """根路径 - 返回 API 信息"""
    return {
        "service": "Fiido智能客服API",
        "status": "running",
        "version": "2.2.0",
        "auth_mode": "OAUTH_JWT",
        "frontend": "Vue 3 前端（frontend/ 目录）",
        "frontend_url": "请访问 http://localhost:5173（需先启动 Vue 开发服务器）",
        "endpoints": {
            "chat": "/api/chat",
            "chat_stream": "/api/chat/stream",
            "health": "/api/health",
            "config": "/api/config",
            "bot_info": "/api/bot/info",
            "token_info": "/api/token/info",
            "conversation_new": "/api/conversation/new",
            "conversation_clear": "/api/conversation/clear"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/index2.html")
async def serve_index():
    """提供前端页面（明确指定文件名）"""
    index_path = os.path.join(CURRENT_DIR, "index2.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        raise HTTPException(status_code=404, detail="前端文件未找到")


@app.get("/fiido2.png")
async def serve_icon():
    """提供客服头像图片"""
    icon_path = os.path.join(CURRENT_DIR, "fiido2.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    else:
        raise HTTPException(status_code=404, detail="图片文件未找到")





@app.get("/api/agent/events")
async def agent_events(agent: dict = Depends(require_agent)):
    """
    坐席事件 SSE 流
    用于接收 @提醒、协助请求等实时事件
    """
    username = agent.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="INVALID_AGENT")

    global sse_queues
    if username not in sse_queues:
        sse_queues[username] = asyncio.Queue()
        print(f"✅ 创建坐席事件SSE队列: {username}")

    async def event_generator():
        queue = sse_queues[username]
        try:
            while True:
                payload = await queue.get()
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        except asyncio.CancelledError:
            print(f"⏹️  坐席事件 SSE 断开: {username}")
            raise
        except Exception as exc:
            print(f"❌ 坐席事件 SSE 异常: {str(exc)}")

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )




@app.get("/fiido2.png")
async def get_fiido_icon():
    """返回 fiido2.png 头像文件"""
    from fastapi.responses import FileResponse
    icon_path = os.path.join(CURRENT_DIR, "fiido2.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path, media_type="image/png")
    else:
        raise HTTPException(status_code=404, detail="Icon not found")


# ==================== P0-4: 核心人工接管 API ====================

@app.post("/api/manual/escalate")
async def manual_escalate(request: dict):
    """
    人工升级接口
    用户点击"人工客服"或监管触发后调用

    Body: { "session_name": "session_123", "reason": "user_request" }
    """
    if not session_store or not regulator:
        raise HTTPException(status_code=503, detail="SessionStore or Regulator not initialized")

    session_name = request.get("session_name")
    reason = request.get("reason", "user_request")

    if not session_name:
        raise HTTPException(status_code=400, detail="session_name is required")

    try:
        # 获取或创建会话状态
        # 从 AI 客服模块获取 conversation_cache
        from products.ai_chatbot.handlers.chat import conversation_cache
        session_state = await session_store.get_or_create(
            session_name=session_name,
            conversation_id=conversation_cache.get(session_name)
        )

        # 检查是否已在人工接管中
        if session_state.status == SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="MANUAL_IN_PROGRESS")

        # 更新升级信息
        # 将 user_request 映射到正确的枚举值 "manual"
        escalation_reason = "manual" if reason == "user_request" else reason

        # P1-邮件: 检查工作时间
        in_shift = is_in_shift()
        email_sent = False

        if not in_shift:
            # 非工作时间：只发邮件，不触发状态转换
            # 创建临时会话状态用于邮件内容
            session_state.escalation = EscalationInfo(
                reason=escalation_reason,
                details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
                severity="high" if reason == "user_request" else "low"
            )

            try:
                email_result = send_escalation_email(session_state)
                email_sent = email_result.get('success', False)
                if email_sent:
                    print(f"📧 非工作时间，已发送邮件通知: {session_name}")
                else:
                    print(f"⚠️  邮件发送失败: {email_result.get('error')}")
            except Exception as email_error:
                print(f"⚠️  邮件发送异常: {str(email_error)}")

            # 记录日志
            print(json.dumps({
                "event": "after_hours_escalate",
                "session_name": session_name,
                "reason": reason,
                "email_sent": email_sent,
                "timestamp": int(time.time())
            }, ensure_ascii=False))

            # 返回但不改变状态，AI继续服务
            return {
                "success": True,
                "data": session_state.model_dump(),
                "email_sent": email_sent,
                "is_in_shift": False
            }

        # 工作时间：正常触发人工接管
        session_state.escalation = EscalationInfo(
            reason=escalation_reason,
            details=f"用户主动请求人工服务" if reason == "user_request" else f"触发原因: {reason}",
            severity="high" if reason == "user_request" else "low"
        )

        # 状态转换为 pending_manual
        session_state.transition_status(
            new_status=SessionStatus.PENDING_MANUAL
        )

        # 智能分配坐席
        auto_assignment = None
        if smart_assignment_engine and not session_state.assigned_agent:
            auto_assignment = await smart_assignment_engine.assign_session(session_state)
            if auto_assignment:
                session_state.assigned_agent = auto_assignment.agent
                print(f"🤖 智能分配坐席: {auto_assignment.agent.name} ({auto_assignment.agent.id})")

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_escalate",
            "session_name": session_name,
            "reason": reason,
            "status": session_state.status,
            "timestamp": int(time.time())
        }, ensure_ascii=False))

        # P0-5: 推送状态变化事件到 SSE
        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "status_change",
                "status": session_state.status,
                "reason": reason,
                "timestamp": int(time.time())
            })
            print(f"✅ SSE 推送状态变化: {session_state.status}")

        return {
            "success": True,
            "data": session_state.model_dump(),
            "email_sent": email_sent,
            "is_in_shift": is_in_shift(),
            "auto_assigned": bool(auto_assignment),
            "recommendation": {
                "agent_id": auto_assignment.agent.id if auto_assignment else None,
                "agent_name": auto_assignment.agent.name if auto_assignment else None,
                "matched_tags": auto_assignment.matched_tags if auto_assignment else [],
                "manual_sessions": auto_assignment.manual_sessions if auto_assignment else 0,
                "pending_sessions": auto_assignment.pending_sessions if auto_assignment else 0,
            } if auto_assignment else None
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 人工升级失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"升级失败: {str(e)}")


# ==================== v2.5 新增：统计指标计算辅助函数 ====================

async def _calculate_ai_quality_metrics() -> dict:
    """
    计算 AI 质量指标（v2.5 新增）

    Returns:
        dict: {
            "avg_response_time_ms": 平均响应时长（毫秒）,
            "success_rate": AI 成功处理率,
            "escalation_rate": 人工升级率,
            "avg_messages_before_escalation": 升级前平均对话轮次
        }
    """
    if not session_store:
        return {
            "avg_response_time_ms": 0,
            "success_rate": 0.0,
            "escalation_rate": 0.0,
            "avg_messages_before_escalation": 0.0
        }

    try:
        # 获取所有会话（限制 1000 条以避免性能问题）
        all_sessions = await session_store.list_all(limit=1000)

        if not all_sessions:
            return {
                "avg_response_time_ms": 0,
                "success_rate": 0.0,
                "escalation_rate": 0.0,
                "avg_messages_before_escalation": 0.0
            }

        total_sessions = len(all_sessions)
        escalated_sessions = [s for s in all_sessions if s.escalation]
        escalation_count = len(escalated_sessions)

        # 计算升级率
        escalation_rate = escalation_count / total_sessions if total_sessions > 0 else 0.0
        success_rate = 1.0 - escalation_rate

        # 计算升级前平均对话轮次
        if escalated_sessions:
            messages_before_escalation = []
            for session in escalated_sessions:
                if session.escalation:
                    # 统计升级前的消息数量
                    escalation_time = session.escalation.trigger_at
                    pre_escalation_msgs = [
                        msg for msg in session.history
                        if msg.timestamp < escalation_time
                    ]
                    messages_before_escalation.append(len(pre_escalation_msgs))

            avg_messages = sum(messages_before_escalation) / len(messages_before_escalation) if messages_before_escalation else 0.0
        else:
            avg_messages = 0.0

        # 计算 AI 平均响应时长（简化版：基于历史消息的时间间隔）
        response_times = []
        for session in all_sessions:
            for i in range(len(session.history) - 1):
                if session.history[i].role == "user" and session.history[i + 1].role == "assistant":
                    response_time_sec = session.history[i + 1].timestamp - session.history[i].timestamp
                    response_times.append(response_time_sec * 1000)  # 转为毫秒

        avg_response_time_ms = sum(response_times) / len(response_times) if response_times else 0.0

        return {
            "avg_response_time_ms": round(avg_response_time_ms, 2),
            "success_rate": round(success_rate, 3),
            "escalation_rate": round(escalation_rate, 3),
            "avg_messages_before_escalation": round(avg_messages, 2)
        }

    except Exception as e:
        print(f"⚠️  计算 AI 质量指标失败: {e}")
        return {
            "avg_response_time_ms": 0,
            "success_rate": 0.0,
            "escalation_rate": 0.0,
            "avg_messages_before_escalation": 0.0
        }


async def _calculate_agent_efficiency_metrics() -> dict:
    """
    计算坐席效率指标（v2.5 新增）

    Returns:
        dict: {
            "avg_takeover_time_sec": 平均接入时长（秒）,
            "avg_service_time_sec": 平均服务时长（秒）,
            "resolution_rate": 一次解决率,
            "avg_sessions_per_agent": 每个坐席平均会话数
        }
    """
    if not session_store:
        return {
            "avg_takeover_time_sec": 0,
            "avg_service_time_sec": 0,
            "resolution_rate": 0.0,
            "avg_sessions_per_agent": 0.0
        }

    try:
        # 获取所有人工服务中和已完成的会话
        live_sessions = await session_store.list_by_status(SessionStatus.MANUAL_LIVE, limit=1000)
        closed_sessions = await session_store.list_by_status(SessionStatus.CLOSED, limit=1000)

        all_manual_sessions = live_sessions + [
            s for s in closed_sessions
            if s.last_manual_end_at is not None  # 曾经经过人工服务
        ]

        if not all_manual_sessions:
            return {
                "avg_takeover_time_sec": 0,
                "avg_service_time_sec": 0,
                "resolution_rate": 0.0,
                "avg_sessions_per_agent": 0.0
            }

        # 计算平均接入时长（pending_manual → manual_live）
        takeover_times = []
        for session in all_manual_sessions:
            if session.escalation and session.assigned_agent:
                # 简化计算：假设接入时间 = 当前时间或结束时间 - 升级时间
                if session.status == SessionStatus.MANUAL_LIVE:
                    takeover_time = time.time() - session.escalation.trigger_at
                elif session.last_manual_end_at:
                    takeover_time = session.last_manual_end_at - session.escalation.trigger_at
                else:
                    continue

                # 接入时长应该是升级到坐席接入的时间，这里简化处理
                # 实际应该记录坐席接入时间戳
                takeover_times.append(min(takeover_time, 3600))  # 限制最大 1 小时

        avg_takeover_time = sum(takeover_times) / len(takeover_times) if takeover_times else 0.0

        # 计算平均服务时长
        service_times = []
        current_time = time.time()
        for session in live_sessions:
            if session.escalation:
                service_time = current_time - session.escalation.trigger_at
                service_times.append(service_time)

        for session in closed_sessions:
            if session.last_manual_end_at and session.escalation:
                service_time = session.last_manual_end_at - session.escalation.trigger_at
                service_times.append(service_time)

        avg_service_time = sum(service_times) / len(service_times) if service_times else 0.0

        # 计算一次解决率（简化版：未再次升级的比例）
        # 实际应该根据工单系统判断问题是否解决
        resolved_sessions = len([
            s for s in closed_sessions
            if s.last_manual_end_at and s.ai_fail_count == 0
        ])
        resolution_rate = resolved_sessions / len(all_manual_sessions) if all_manual_sessions else 0.0

        # 计算每个坐席平均会话数
        agent_session_counts = {}
        for session in all_manual_sessions:
            if session.assigned_agent:
                agent_id = session.assigned_agent.id
                agent_session_counts[agent_id] = agent_session_counts.get(agent_id, 0) + 1

        avg_sessions_per_agent = (
            sum(agent_session_counts.values()) / len(agent_session_counts)
            if agent_session_counts else 0.0
        )

        return {
            "avg_takeover_time_sec": round(avg_takeover_time, 2),
            "avg_service_time_sec": round(avg_service_time, 2),
            "resolution_rate": round(resolution_rate, 3),
            "avg_sessions_per_agent": round(avg_sessions_per_agent, 2)
        }

    except Exception as e:
        print(f"⚠️  计算坐席效率指标失败: {e}")
        return {
            "avg_takeover_time_sec": 0,
            "avg_service_time_sec": 0,
            "resolution_rate": 0.0,
            "avg_sessions_per_agent": 0.0
        }




# ==================== 模块2: 队列管理 API ====================





@app.post("/api/manual/messages")
async def manual_message(request: dict):
    """
    人工阶段消息写入
    用于用户/坐席在人工接管期间的消息

    Body: {
        "session_name": "session_123",
        "role": "agent" | "user",
        "content": "我要人工"
    }
    """
    if not session_store:
        raise HTTPException(status_code=503, detail="SessionStore not initialized")

    session_name = request.get("session_name")
    role = request.get("role")
    content = request.get("content")

    if not all([session_name, role, content]):
        raise HTTPException(status_code=400, detail="session_name, role, and content are required")

    if role not in ["agent", "user"]:
        raise HTTPException(status_code=400, detail="role must be 'agent' or 'user'")

    try:
        # 获取会话状态
        session_state = await session_store.get(session_name)

        if not session_state:
            raise HTTPException(status_code=404, detail="Session not found")

        # 如果是用户消息，必须在manual_live状态
        if role == "user" and session_state.status != SessionStatus.MANUAL_LIVE:
            raise HTTPException(status_code=409, detail="Session not in manual_live status")

        # 创建消息
        agent_info = request.get("agent_info", {})
        message = Message(
            role=role,
            content=content,
            agent_id=agent_info.get("agent_id") if agent_info else None,
            agent_name=agent_info.get("agent_name") if agent_info else None
        )

        # 添加到历史
        session_state.add_message(message)

        # 保存会话状态
        await session_store.save(session_state)

        # 记录日志
        print(json.dumps({
            "event": "manual_message",
            "session_name": session_name,
            "role": role,
            "timestamp": message.timestamp
        }, ensure_ascii=False))

        # P0-5: 通过 SSE 推送消息到客户端
        if session_name in sse_queues:
            await sse_queues[session_name].put({
                "type": "manual_message",
                "role": role,
                "content": content,
                "timestamp": message.timestamp,
                "agent_id": message.agent_id,
                "agent_name": message.agent_name
            })
            print(f"✅ SSE 推送人工消息到队列: {session_name}, role={role}")

        if role == "user":
            await handle_customer_reply_event(session_state, source="manual_message")

        return {
            "success": True,
            "data": {
                "timestamp": message.timestamp
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 写入人工消息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"写入失败: {str(e)}")










# ====================
# 工单系统 API (L1-2 MVP)
# ====================






































































# ====================
# 坐席认证 API (Agent Authentication)
# ====================

















# ====================
# 管理员功能 API
# ====================

# 导入请求模型
from src.agent_auth import (
    CreateAgentRequest,
    UpdateAgentRequest,
    ResetPasswordRequest,
    ChangePasswordRequest,
    UpdateProfileRequest,
    validate_password,
    PasswordHasher,
    AgentRole
)






















# ====================
# 客户信息与业务上下文 API (v3.2.0+)
# ====================



# ====================
# 【模块3】快捷回复系统 API (v3.7.0+)
# ====================

















# ==================== 【模块5】内部备注功能 ====================

# 内存存储（生产环境应使用 Redis）
internal_notes_store: Dict[str, List[Dict[str, Any]]] = {}


class InternalNoteRequest(BaseModel):
    """创建/更新内部备注请求"""
    content: str
    mentions: Optional[List[str]] = []  # @的坐席username列表


@app.post("/api/sessions/{session_name}/notes")
async def create_internal_note(
    session_name: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    添加内部备注（仅坐席可见）

    Args:
        session_name: 会话ID
        request: 备注内容和@提醒列表
        agent: 当前登录坐席信息

    Returns:
        创建的备注信息
    """
    try:
        # 验证会话是否存在
        if not session_store:
            raise HTTPException(status_code=503, detail="会话系统未初始化")

        session_state = await session_store.get(session_name)
        if not session_state:
            raise HTTPException(
                status_code=404,
                detail="SESSION_NOT_FOUND: 会话不存在"
            )

        # 创建备注
        note = {
            "id": f"note_{uuid.uuid4().hex[:16]}",
            "session_name": session_name,
            "content": request.content,
            "created_by": agent.get("username"),
            "created_by_name": agent.get("name", agent.get("username")),
            "created_at": time.time(),
            "updated_at": time.time(),
            "mentions": request.mentions or []
        }

        # 保存到存储
        if session_name not in internal_notes_store:
            internal_notes_store[session_name] = []
        internal_notes_store[session_name].append(note)

        print(f"✅ 创建内部备注: {note['id']} for session {session_name} by {agent.get('username')}")

        # 如果有@提醒，通过SSE推送通知给被@的坐席
        if request.mentions:
            unique_mentions = set(request.mentions)
            print(f"📢 @提醒: {unique_mentions}")
            for username in unique_mentions:
                if not username:
                    continue
                await enqueue_sse_message(username, {
                    "type": "mention",
                    "source": "session_note",
                    "session_name": session_name,
                    "note_id": note["id"],
                    "from_agent": agent.get("name") or agent.get("username"),
                    "content": note["content"],
                    "created_at": note["created_at"]
                })

        return {
            "success": True,
            "data": note
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 创建内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"创建失败: {str(e)}"
        )


@app.get("/api/sessions/{session_name}/notes")
async def get_internal_notes(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话的所有内部备注

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        备注列表
    """
    try:
        # 获取备注列表
        notes = internal_notes_store.get(session_name, [])

        # 按创建时间倒序排序
        notes_sorted = sorted(notes, key=lambda x: x["created_at"], reverse=True)

        return {
            "success": True,
            "data": notes_sorted,
            "total": len(notes_sorted)
        }

    except Exception as e:
        print(f"❌ 获取内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )


@app.put("/api/sessions/{session_name}/notes/{note_id}")
async def update_internal_note(
    session_name: str,
    note_id: str,
    request: InternalNoteRequest,
    agent: dict = Depends(require_agent)
):
    """
    编辑内部备注（仅创建者和管理员可编辑）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        request: 新的备注内容
        agent: 当前登录坐席信息

    Returns:
        更新后的备注信息
    """
    try:
        # 查找备注
        notes = internal_notes_store.get(session_name, [])
        note = next((n for n in notes if n["id"] == note_id), None)

        if not note:
            raise HTTPException(
                status_code=404,
                detail="NOTE_NOT_FOUND: 备注不存在"
            )

        # 权限检查：仅创建者和管理员可编辑
        if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者和管理员可以编辑备注"
            )

        # 更新备注
        note["content"] = request.content
        note["mentions"] = request.mentions or []
        note["updated_at"] = time.time()

        print(f"✅ 更新内部备注: {note_id} by {agent.get('username')}")

        return {
            "success": True,
            "data": note
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 更新内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"更新失败: {str(e)}"
        )


@app.delete("/api/sessions/{session_name}/notes/{note_id}")
async def delete_internal_note(
    session_name: str,
    note_id: str,
    agent: dict = Depends(require_agent)
):
    """
    删除内部备注（仅创建者和管理员可删除）

    Args:
        session_name: 会话ID
        note_id: 备注ID
        agent: 当前登录坐席信息

    Returns:
        删除结果
    """
    try:
        # 查找备注
        notes = internal_notes_store.get(session_name, [])
        note = next((n for n in notes if n["id"] == note_id), None)

        if not note:
            raise HTTPException(
                status_code=404,
                detail="NOTE_NOT_FOUND: 备注不存在"
            )

        # 权限检查：仅创建者和管理员可删除
        if note["created_by"] != agent.get("username") and agent.get("role") != "admin":
            raise HTTPException(
                status_code=403,
                detail="PERMISSION_DENIED: 只有创建者和管理员可以删除备注"
            )

        # 删除备注
        internal_notes_store[session_name] = [
            n for n in notes if n["id"] != note_id
        ]

        print(f"✅ 删除内部备注: {note_id} by {agent.get('username')}")

        return {
            "success": True,
            "message": f"备注 {note_id} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 删除内部备注失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"删除失败: {str(e)}"
        )


# ==================== 【模块5】会话转接增强 ====================

class TransferRequestEnhanced(BaseModel):
    """增强的会话转接请求"""
    from_agent_id: str
    to_agent_id: str
    to_agent_name: str
    reason: str  # 转接原因
    note: Optional[str] = ""  # 转接备注（给接收坐席的说明）


# 转接历史存储
transfer_history_store: Dict[str, List[Dict[str, Any]]] = {}
pending_transfer_requests: Dict[str, List[Dict[str, Any]]] = {}


class TransferResponseRequest(BaseModel):
    """转接请求响应"""
    action: Literal['accept', 'decline']
    response_note: Optional[str] = ""


def find_pending_transfer_request(request_id: str):
    """
    辅助函数：定位待处理转接请求
    """
    for agent_id, requests in pending_transfer_requests.items():
        for index, request in enumerate(requests):
            if request.get("id") == request_id:
                return request, agent_id, index
    return None, None, None


@app.get("/api/sessions/{session_name}/transfer-history")
async def get_transfer_history(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """
    获取会话转接历史

    Args:
        session_name: 会话ID
        agent: 当前登录坐席信息

    Returns:
        转接历史列表
    """
    try:
        history = transfer_history_store.get(session_name, [])

        # 按时间倒序
        history_sorted = sorted(history, key=lambda x: x["transferred_at"], reverse=True)

        return {
            "success": True,
            "data": history_sorted,
            "total": len(history_sorted)
        }

    except Exception as e:
        print(f"❌ 获取转接历史失败: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"获取失败: {str(e)}"
        )






# ==================== 【模块5】协助请求功能 ====================







# ==================== Shopify 多站点订单查询 API (v5.3.0+) ====================


@app.get("/api/shopify/sites")
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


@app.get("/api/shopify/{site}/orders")
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


@app.get("/api/shopify/{site}/orders/search")
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
        # 参数验证
        if len(q) < 3:
            raise HTTPException(
                status_code=400,
                detail="INVALID_QUERY: 订单号至少需要3个字符"
            )

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


@app.get("/api/shopify/orders/global-search")
async def search_shopify_order_global(
    q: str
):
    """
    跨站点搜索订单

    根据订单号前缀自动检测站点，或遍历所有站点搜索

    Args:
        q: 订单号关键词

    Returns:
        订单详情（包含站点信息）
    """
    try:
        # 参数验证
        if len(q) < 3:
            raise HTTPException(
                status_code=400,
                detail="INVALID_QUERY: 订单号至少需要3个字符"
            )

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


@app.get("/api/shopify/orders/global-email-search")
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


@app.get("/api/shopify/{site}/orders/count")
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


@app.get("/api/shopify/{site}/orders/{order_id}")
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


@app.get("/api/shopify/{site}/orders/{order_id}/tracking")
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
        物流信息
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


@app.get("/api/shopify/{site}/health")
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


@app.get("/api/shopify/health/all")
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


# ==================== Shopify UK 订单查询 API (向后兼容) ====================


@app.get("/api/shopify/orders")
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


@app.get("/api/shopify/orders/search")
async def search_shopify_order(
    q: str
):
    """
    按订单号搜索订单 (UK站点，向后兼容)

    Args:
        q: 订单号关键词 (支持 #UK22080 或 UK22080 格式)

    Returns:
        订单详情
    """
    try:
        # 参数验证
        if len(q) < 3:
            raise HTTPException(
                status_code=400,
                detail="INVALID_QUERY: 订单号至少需要3个字符"
            )

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


@app.get("/api/shopify/orders/count")
async def get_shopify_order_count(
    status: str = "any"
):
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


@app.get("/api/shopify/orders/{order_id}")
async def get_shopify_order_detail(
    order_id: str
):
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


@app.get("/api/shopify/tracking")
async def get_shopify_tracking_by_query(
    order_id: Optional[str] = None
):
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
        from src.shopify_sites import get_all_configured_sites
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


@app.get("/api/shopify/orders/{order_id}/tracking")
async def get_shopify_order_tracking(
    order_id: str
):
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


@app.get("/api/shopify/health")
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


# ==================== 缓存预热管理 API ====================


@app.get("/api/warmup/status")
async def get_warmup_status():
    """
    获取预热服务状态

    Returns:
        预热服务状态信息
    """
    try:
        from src.warmup_service import get_warmup_service
        warmup_service = get_warmup_service()

        status = warmup_service.get_status()

        # 添加调度器信息
        if _warmup_scheduler:
            jobs = []
            for job in _warmup_scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })
            status["scheduler"] = {
                "running": _warmup_scheduler.running,
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


@app.post("/api/warmup/trigger")
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
        from src.warmup_service import get_warmup_service
        warmup_service = get_warmup_service()

        if warmup_service.is_running:
            return {
                "success": False,
                "error": "预热任务正在执行中",
                "message": "请等待当前任务完成后再触发"
            }

        # 异步启动预热任务
        import asyncio
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


@app.get("/api/warmup/history")
async def get_warmup_history(limit: int = 10):
    """
    获取预热历史记录

    Args:
        limit: 返回数量限制

    Returns:
        预热历史列表
    """
    try:
        from src.warmup_service import get_warmup_service
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


@app.post("/api/warmup/stop")
async def stop_warmup():
    """
    停止当前预热任务

    Returns:
        停止结果
    """
    try:
        from src.warmup_service import get_warmup_service
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


# =============================================================================
# CDN 健康检查 API
# =============================================================================

@app.post("/api/cdn/health-check")
async def trigger_cdn_health_check(auto_fix: bool = False):
    """
    手动触发 CDN URL 健康检查

    Args:
        auto_fix: 是否自动修复失效的 URL

    Returns:
        检查结果
    """
    try:
        from src.cdn_health_checker import run_health_check

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


@app.get("/api/cdn/health-log")
async def get_cdn_health_log():
    """
    获取最近的 CDN 健康检查日志

    Returns:
        最近一次检查的详细结果
    """
    try:
        import json
        from pathlib import Path

        log_file = Path(__file__).parent / "assets" / "cdn_health_log.json"

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


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")

    print(f"""
    ==========================================
    🚀 Fiido智能客服后端服务启动中...
    ==========================================
    📍 地址: http://{host}:{port}
    📖 API文档: http://{host}:{port}/docs
    📊 交互式文档: http://{host}:{port}/redoc
    🔐 鉴权模式: {os.getenv("COZE_AUTH_MODE", "OAUTH_JWT")}
    💬 多轮对话: 已启用
    🔧 人工接管: 已启用
    ==========================================
    """)

    uvicorn.run(
        "backend:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
