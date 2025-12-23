"""
物流通知模块 - 独立模式入口

支持独立启动，接收 Webhook 推送并发送通知。

启动命令:
    uvicorn products.notification.main:app --host 0.0.0.0 --port 8001

环境变量:
    ENABLE_NOTIFICATION=true
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_config

# 创建 FastAPI 应用
app = FastAPI(
    title="Fiido 物流通知服务",
    description="接收物流状态更新，发送通知邮件",
    version="1.0.0",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """根路由"""
    config = get_config()
    return {
        "service": "notification",
        "status": "running",
        "enabled": config.enabled,
    }


@app.get("/api/health")
async def health():
    """健康检查"""
    config = get_config()
    return {
        "status": "healthy",
        "module": "notification",
        "enabled": config.enabled,
    }


@app.get("/api/config")
async def config_info():
    """配置信息（不含敏感数据）"""
    config = get_config()
    return {
        "enabled": config.enabled,
        "email_from": config.email_from,
        "overseas_timeout_days": config.overseas_warehouse_timeout,
        "china_timeout_days": config.china_warehouse_timeout,
    }


# 注册 Webhook 路由
from .routes import router as webhook_router
app.include_router(webhook_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
