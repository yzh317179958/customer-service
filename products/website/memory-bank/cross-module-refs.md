# 官网模块 - 跨模块功能引用

> **模块路径**：products/website/
> **最后更新**：2025-12-30

---

## 官网商业化

**主文档**：`docs/features/website-commercial/`

**状态**：⏳ 开发中

**本模块职责**：
- 官网前端展示（产品介绍、定价、案例）
- 用户注册/登录 API
- 表单收集 API（预约演示、联系我们）
- 支付流程入口和回调处理
- 嵌入 AI 客服组件

**涉及文件**：

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| main.py | 新增 | FastAPI 应用入口 |
| routes.py | 新增 | API 路由定义 |
| handlers/auth.py | 新增 | 用户认证处理 |
| handlers/leads.py | 新增 | 表单收集处理 |
| handlers/payment.py | 新增 | 支付回调处理 |
| frontend/crossborder-ai-solutions/ | 修改 | 内容适配 |

**对接模块**：
- `services/billing` - 套餐查询、订阅创建、支付集成
- `infrastructure/security` - JWT 认证
- `infrastructure/database` - 数据存储
- `products/ai_chatbot` - 嵌入 AI 客服组件
