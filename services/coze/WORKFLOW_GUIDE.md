# Coze Workflow 插件配置指南

本文档详细说明如何在 Coze 平台配置 Shopify UK 订单查询插件。

## 1. 整体架构

```
用户输入: "我的订单 #UK22080 什么时候发货？"
         ↓
   Coze AI 意图识别
         ↓
   识别为: 订单查询 (order_query)
         ↓
   调用 Shopify 插件
         ↓
   FastAPI 后端 /api/shopify/*
         ↓
   Shopify Admin API
         ↓
   返回订单数据 + 客服话术
         ↓
   Coze 格式化回复给用户
```

## 2. 前置条件

### 2.1 后端服务部署

确保后端 API 可公网访问：

```bash
# 本地开发时可使用 ngrok 暴露
ngrok http 8000
# 得到类似 https://abc123.ngrok.io 的公网地址

# 生产环境应部署到云服务器
# 例如: https://api.your-domain.com
```

### 2.2 API 端点测试

```bash
# 测试订单搜索 API
curl "https://your-api.com/api/shopify/orders/search?q=UK22080"

# 测试健康检查
curl "https://your-api.com/api/shopify/health"
```

## 3. 在 Coze 平台创建插件

### 步骤 1: 进入插件管理

1. 登录 [Coze 平台](https://www.coze.com)
2. 进入你的 Bot/应用
3. 左侧菜单选择 **"插件"**
4. 点击 **"创建插件"**

### 步骤 2: 配置插件基本信息

```
插件名称: Shopify UK 订单查询
插件描述: 查询 Fiido UK 店铺的订单信息和物流状态
```

### 步骤 3: 导入 OpenAPI 规范

1. 选择 **"通过 OpenAPI 导入"**
2. 上传 `coze/shopify_plugin.yaml` 文件
3. 或粘贴 YAML 内容

### 步骤 4: 配置服务器地址

将 `servers` 中的 URL 替换为你的实际地址：

```yaml
servers:
  - url: https://your-api-domain.com
    description: 生产环境
```

## 4. 在 Workflow 中使用插件

### 4.1 工作流设计

```
开始
  ↓
意图识别 (LLM 节点)
  ↓
条件分支
  ├── order_query → 订单搜索插件
  ├── tracking_query → 物流查询插件
  └── general → 通用回复
  ↓
格式化回复 (LLM 节点)
  ↓
结束
```

### 4.2 意图识别节点配置

**节点类型**: LLM 节点

**Prompt**:
```
分析用户输入，判断用户意图并提取关键信息。

意图类型：
1. order_query - 查询订单状态/详情（关键词：订单、查询、状态、发货、到货）
2. tracking_query - 查询物流信息（关键词：物流、快递、到哪了、运单、追踪）
3. order_list - 查询所有订单（关键词：我的订单、历史订单、订单记录）
4. general - 其他问题

提取实体：
- order_number: 订单号（如 UK22080, #UK22080, UK-22080）
- email: 邮箱地址

用户输入: {{user_input}}

输出 JSON 格式:
{
  "intent": "order_query|tracking_query|order_list|general",
  "order_number": "提取的订单号或null",
  "email": "提取的邮箱或null",
  "confidence": 0.0-1.0
}
```

### 4.3 条件分支配置

```
条件 1: intent == "order_query" && order_number != null
  → 调用 searchOrderByNumber 工具

条件 2: intent == "tracking_query" && order_number != null
  → 先调用 searchOrderByNumber 获取 order_id
  → 再调用 getOrderTracking

条件 3: intent == "order_list" && email != null
  → 调用 getOrdersByEmail

默认:
  → 通用对话回复
```

### 4.4 插件调用配置

**订单搜索**:
```yaml
工具: searchOrderByNumber
输入:
  q: {{order_number}}
输出变量: order_result
```

**物流查询**:
```yaml
工具: getOrderTracking
输入:
  order_id: {{order_result.data.order.order_id}}
输出变量: tracking_result
```

### 4.5 回复格式化节点

**订单查询回复 Prompt**:
```
根据订单数据生成友好的客服回复。

订单数据: {{order_result}}

要求:
1. 使用友好的口吻
2. 突出重要信息（订单号、状态、金额）
3. 如果有物流信息，提供追踪链接
4. 如果有问题，提供解决建议

回复模板参考:
您好！为您查询到订单 {{order_number}} 的信息：

📦 订单状态：{{fulfillment_status}}
💰 订单金额：{{total_price}} {{currency}}
📅 下单时间：{{created_at}}

{{#if tracking}}
🚚 物流信息：
承运商：{{tracking.company}}
运单号：{{tracking.number}}
追踪链接：{{tracking.url}}
{{else}}
📝 您的订单正在处理中，发货后会通知您物流信息。
{{/if}}

如有其他问题，请随时告诉我！
```

**物流查询回复**:

直接使用 API 返回的 `message_template_zh` 字段。

## 5. 话术模板示例

### 5.1 订单状态查询

**用户**: 我的订单 UK22080 什么时候发货？

**回复**:
```
您好！为您查询到订单 #UK22080 的信息：

📦 订单状态：已发货
💰 订单金额：1637.69 GBP
📅 下单时间：2025-12-09

🚚 物流信息：
承运商：Royal Mail
运单号：AB123456789GB
当前状态：运输中

追踪链接：https://www.royalmail.com/track?trackNumber=AB123456789GB

如有其他问题，请随时告诉我！
```

### 5.2 订单未发货

**用户**: 查一下我的订单 UK22081

**回复**:
```
您好！为您查询到订单 #UK22081 的信息：

📦 订单状态：未发货
💰 订单金额：1299.00 GBP
📅 下单时间：2025-12-10

📝 您的订单正在处理中，我们会尽快为您安排发货。
发货后您会收到邮件通知，届时可以追踪物流状态。

如有其他问题，请随时告诉我！
```

### 5.3 订单不存在

**用户**: 查询订单 UK99999

**回复**:
```
抱歉，未能找到订单号 UK99999 的订单记录。

请您确认：
1. 订单号是否输入正确
2. 该订单是否在 Fiido UK 官网下单

如果您有订单确认邮件，可以提供邮件中的订单号，我帮您再次查询。
```

## 6. 调试与测试

### 6.1 在 Coze 调试

1. 进入 Workflow 编辑器
2. 点击 "测试" 按钮
3. 输入测试用例
4. 查看每个节点的输入输出

### 6.2 测试用例

```
# 测试 1: 订单号查询
用户输入: "我的订单 UK22080 什么时候发货？"
预期: 调用 searchOrderByNumber，返回订单详情

# 测试 2: 物流查询
用户输入: "帮我查一下物流到哪了，订单号UK22080"
预期: 调用 getOrderTracking，返回物流信息和追踪链接

# 测试 3: 邮箱查询
用户输入: "我的邮箱是 test@example.com，查一下我的订单"
预期: 调用 getOrdersByEmail，返回订单列表

# 测试 4: 订单不存在
用户输入: "查询订单 UK99999"
预期: 返回 404，告知订单不存在
```

## 7. 生产环境注意事项

### 7.1 API 安全

建议为 Coze 插件调用添加认证：

```python
@app.get("/api/shopify/orders/search")
async def search_order(
    q: str,
    x_coze_token: str = Header(None)
):
    if x_coze_token != EXPECTED_COZE_TOKEN:
        raise HTTPException(401, "Unauthorized")
    # ... 处理逻辑
```

### 7.2 CORS 配置

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://www.coze.com", "https://api.coze.com"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 7.3 监控告警

- 监控插件调用成功率
- 设置响应时间告警阈值（< 2s）
- 记录所有 API 调用日志

## 8. 常见问题

### Q1: 插件调用失败

检查：
1. API URL 是否可公网访问
2. CORS 是否正确配置
3. 请求超时设置（Coze 默认 30s）

### Q2: 响应解析错误

检查：
1. API 返回的 JSON 格式是否正确
2. 字段名是否与 OpenAPI 规范一致
3. 是否有 null 值未处理

### Q3: 缓存不生效

检查：
1. Redis 服务是否正常运行
2. 缓存 TTL 配置
3. 查看后端日志确认缓存命中情况

---

**文档维护者**: Claude Code
**最后更新**: 2025-12-09
