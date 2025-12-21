# Customer Portal API Routes
# 客户控制台路由定义

from fastapi import APIRouter

router = APIRouter(
    prefix="/api/portal",
    tags=["客户控制台"]
)

# TODO: 实现以下路由
# - /account - 账户信息
# - /subscription - 订阅管理
# - /usage - 用量统计
# - /billing - 账单管理
