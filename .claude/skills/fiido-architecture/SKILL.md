---
name: fiido-architecture
description: 当修改 Fiido 项目代码时，自动检查三层架构依赖规则，分析新功能归属，阻止违规依赖
---

# Fiido 三层架构守护者

## 何时使用
- 用户要开发新功能
- 用户要修改现有代码
- 用户要创建新模块

## 三层架构规则

```
products/（产品层）
    ↓ 可以依赖
services/（服务层）
    ↓ 可以依赖
infrastructure/（基础设施层）
```

## 依赖规则表（铁律）

| 从 | 到 | 允许？ |
|----|----|----|
| products → services | ✅ 允许 |
| products → infrastructure | ✅ 允许 |
| services → infrastructure | ✅ 允许 |
| services → products | ❌ 禁止 |
| infrastructure → services | ❌ 禁止 |
| infrastructure → products | ❌ 禁止 |
| products ↔ products | ❌ 禁止（不能互相依赖）|

## 新功能分析模板

当用户提出新需求时，必须先分析：

```
用户需求：[需求描述]

【分析结果】
1. 产品归属：products/[产品名]

2. 需要的服务层：
   - services/xxx ✓ 已有
   - services/yyy ✗ 需新建

3. 需要的基础设施：
   - infrastructure/xxx ✓ 已有

4. 开发计划（自底向上）：
   Step 1: [基础设施层改动]
   Step 2: [服务层改动]
   Step 3: [产品层改动]
   Step 4: 测试验证

是否确认执行？
```

## 代码检查示例

✅ 正确：
```python
# products/ai_chatbot/handlers/chat.py
from services.shopify import ShopifyService  # OK
from infrastructure.database import get_redis  # OK
```

❌ 错误：
```python
# services/shopify/client.py
from products.ai_chatbot import chat  # 违规！服务层不能依赖产品层
```

## 发现违规时
1. 立即停止
2. 告知用户具体违规位置
3. 建议正确的依赖方式

## 生产环境架构考量

分析新功能时必须考虑企业级生产环境要求：

- **服务边界清晰**：每个服务职责单一，避免循环依赖
- **水平扩展能力**：设计时考虑多实例部署场景
- **故障隔离**：一个服务故障不应导致整个系统崩溃
- **可观测性**：预留日志、监控、追踪接入点
- **配置外置**：敏感配置通过环境变量管理，不硬编码
