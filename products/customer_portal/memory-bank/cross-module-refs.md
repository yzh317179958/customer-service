# 客户控制台 - 跨模块功能引用

> **模块路径**：products/customer_portal/
> **最后更新**：2025-12-30

---

## 官网商业化

**主文档**：`docs/features/website-commercial/`

**状态**：⏳ 开发中

**本模块职责**：
- 客户账户信息管理
- 当前订阅状态查看
- 用量统计展示
- 套餐升级入口
- 账单查看和下载

**涉及文件**：

| 文件 | 改动类型 | 说明 |
|------|----------|------|
| main.py | 新增 | FastAPI 应用入口 |
| frontend/ | 新增 | 控制台前端 |
| handlers/ | 新增 | API 处理器 |

**对接模块**：
- `services/billing` - 获取订阅、用量、账单数据
- `infrastructure/security` - JWT 认证
- `products/agent_workbench` - 可选嵌入方式
