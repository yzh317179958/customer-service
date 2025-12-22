"""
Fiido智能客服后端服务 - AI 客服入口

使用 FastAPI 提供 RESTful API，采用 OAuth+JWT 鉴权
支持基于 Workflow 的多轮对话

【架构说明 - 微服务模式】
各产品独立部署，本文件仅负责 AI 客服：
- AI 客服 (8000)：本服务
- 坐席工作台 (8002)：独立微服务，见 products/agent_workbench/main.py
- 通知服务 (8003)：规划中
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# 【微服务架构】导入 Bootstrap 模块
from infrastructure.bootstrap import (
    BootstrapFactory, Component,
    get_session_store, get_coze_client, get_token_manager, get_jwt_oauth_app,
    get_workflow_id, get_app_id,
    get_agent_manager, get_agent_token_manager,
    get_ticket_store, get_ticket_template_store, get_audit_log_store, get_quick_reply_store,
    get_sse_queues,
    start_background_tasks, start_warmup_scheduler, shutdown_background_tasks,
)
import services.bootstrap  # noqa: F401  # 确保服务层依赖注册

# 导入业务组件（使用三层架构路径）
from services.session.variable_replacer import VariableReplacer
from services.ticket.assignment import SmartAssignmentEngine
from services.ticket.automation import CustomerReplyAutoReopen

# 加载环境变量
load_dotenv()

# ====================
# 网络代理防护（禁用未受支持的 SOCKS 代理）
# ====================
PROXY_ENV_VARS = [
    "http_proxy", "https_proxy", "all_proxy",
    "HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY",
]

for var in PROXY_ENV_VARS:
    value = os.environ.pop(var, None)
    if value:
        print(f"⚠️  检测到代理变量 {var}，已忽略")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理 - 使用 bootstrap 模块统一初始化

    微服务架构：全家桶模式下初始化所有组件
    """
    print(f"\n{'=' * 60}")
    print(f"🚀 Fiido 智能客服后端服务初始化 (全家桶模式)")
    print(f"{'=' * 60}")

    # ============================================================
    # 1. 使用 Bootstrap 工厂初始化所有组件
    # ============================================================
    factory = BootstrapFactory()
    factory.init_components([
        Component.REDIS,
        Component.COZE,
        Component.REGULATOR,
        Component.AGENT_AUTH,
        Component.TICKET,
        Component.SSE,
    ])

    # ============================================================
    # 2. 从 bootstrap 获取组件实例
    # ============================================================
    session_store = get_session_store()
    coze_client = get_coze_client()
    token_manager = get_token_manager()
    jwt_oauth_app = get_jwt_oauth_app()
    agent_manager = get_agent_manager()
    agent_token_manager = get_agent_token_manager()
    ticket_store = get_ticket_store()
    ticket_template_store = get_ticket_template_store()
    audit_log_store = get_audit_log_store()
    quick_reply_store = get_quick_reply_store()
    sse_queues = get_sse_queues()
    regulator = factory.get_instance(Component.REGULATOR)

    # 获取 Coze 配置
    WORKFLOW_ID = get_workflow_id()
    APP_ID = get_app_id()
    AUTH_MODE = os.getenv("COZE_AUTH_MODE", "OAUTH_JWT")

    print(f"🔐 鉴权模式: {AUTH_MODE}")
    print(f"📱 App ID: {APP_ID}")
    print(f"🔄 Workflow ID: {WORKFLOW_ID}")
    print(f"💬 多轮对话: 已启用")

    # ============================================================
    # 3. 初始化业务组件（依赖基础组件）
    # ============================================================

    # 变量替换器
    variable_replacer = VariableReplacer()

    # 智能分配引擎
    smart_assignment_engine = None
    try:
        if agent_manager and session_store:
            smart_assignment_engine = SmartAssignmentEngine(
                agent_manager=agent_manager,
                session_store=session_store
            )
            print("[Bootstrap] ✅ 智能分配引擎初始化成功")
    except Exception as e:
        print(f"[Bootstrap] ⚠️ 智能分配引擎初始化失败: {e}")

    # 客户回复自动恢复规则
    customer_reply_auto_reopen = None
    try:
        if ticket_store:
            customer_reply_auto_reopen = CustomerReplyAutoReopen(
                ticket_store,
                agent_manager=agent_manager
            )
            print("[Bootstrap] ✅ 客户回复自动恢复规则初始化成功")
    except Exception as e:
        print(f"[Bootstrap] ⚠️ 客户回复自动恢复规则初始化失败: {e}")

    # ============================================================
    # 4. 注入产品模块依赖
    # ============================================================

    # AI 客服模块依赖
    try:
        from products.ai_chatbot import dependencies as ai_deps
        ai_deps.set_coze_client(coze_client)
        ai_deps.set_token_manager(token_manager)
        ai_deps.set_session_store(session_store)
        ai_deps.set_regulator(regulator)
        ai_deps.set_jwt_oauth_app(jwt_oauth_app)
        ai_deps.set_config(WORKFLOW_ID, APP_ID)
        ai_deps.set_sse_queues(sse_queues)
        ai_deps.set_smart_assignment_engine(smart_assignment_engine)
        ai_deps.set_customer_reply_auto_reopen(customer_reply_auto_reopen)
        print("[Bootstrap] ✅ AI 客服模块依赖初始化成功")
    except Exception as e:
        print(f"[Bootstrap] ⚠️ AI 客服模块依赖初始化失败: {e}")

    # ============================================================
    # 5. 启动后台任务
    # ============================================================
    start_background_tasks(ticket_store, agent_manager, sse_queues)
    start_warmup_scheduler()

    print(f"{'=' * 60}\n")

    yield

    # ============================================================
    # 6. 清理资源
    # ============================================================
    await shutdown_background_tasks()
    print("👋 服务已关闭")


# ====================
# 创建 FastAPI 应用
# ====================
app = FastAPI(
    title="Fiido智能客服API",
    description="基于 Coze Workflow 的智能客服后端服务，支持 OAuth+JWT 鉴权和多轮对话",
    version="8.0.0",
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

# ====================
# 静态文件服务
# ====================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 挂载静态文件目录
try:
    app.mount("/static", StaticFiles(directory=CURRENT_DIR), name="static")
except Exception as e:
    print(f"⚠️  静态文件挂载失败: {e}")

# 挂载素材目录
ASSETS_DIR = os.path.join(CURRENT_DIR, "assets")
if os.path.exists(ASSETS_DIR):
    try:
        app.mount("/assets", StaticFiles(directory=ASSETS_DIR), name="assets")
        print(f"✅ 素材目录已挂载: /assets -> {ASSETS_DIR}")
    except Exception as e:
        print(f"⚠️  素材目录挂载失败: {e}")
else:
    print(f"⚠️  素材目录不存在: {ASSETS_DIR}")

# ====================
# 注册产品路由
# ====================
from products.ai_chatbot import get_router as get_ai_chatbot_router
app.include_router(get_ai_chatbot_router(), prefix="/api", tags=["AI智能客服"])
print("✅ AI 客服模块路由已注册: /api/*")


# ====================
# 根路由与静态文件端点
# ====================
@app.get("/")
async def root():
    """根路径 - 返回 API 信息"""
    return {
        "service": "Fiido智能客服API",
        "status": "running",
        "version": "8.0.0",
        "auth_mode": "OAUTH_JWT",
        "architecture": "三层架构 (products/services/infrastructure)",
        "modules": {
            "ai_chatbot": "AI 智能客服"
        },
        "docs": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/index2.html")
async def serve_index():
    """提供前端页面"""
    index_path = os.path.join(CURRENT_DIR, "index2.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "前端文件未找到"}


@app.get("/fiido2.png")
async def serve_icon():
    """提供客服头像图片"""
    icon_path = os.path.join(CURRENT_DIR, "fiido2.png")
    if os.path.exists(icon_path):
        return FileResponse(icon_path)
    return {"error": "图片文件未找到"}
