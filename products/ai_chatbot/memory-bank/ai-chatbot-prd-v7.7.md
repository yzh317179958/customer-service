# AI 智能客服模块产品需求说明

> **版本**: v7.7.0
> **创建日期**: 2024-12-24
> **状态**: 待开发

---

## 一、现状分析摘要

### 1.1 模块整体状态

**已实现的核心能力：**
- ✅ Coze 工作流深度集成（会话隔离、流式响应、多轮对话）
- ✅ 订单查询（Shopify 多站点、缓存机制）
- ✅ 物流追踪（17track API、自动注册、轨迹时间线）
- ✅ 人工转接（状态机、班次控制、SSE 实时推送）
- ✅ 前端交互（Vue 3 + Pinia、快捷回复、消息气泡）

**主要差距：**

| 差距项 | 当前状态 | 影响程度 |
|--------|---------|---------|
| 默认语言 | 中文优先，英文次之 | 高 - 海外用户体验差 |
| 快捷回复逻辑 | 纯前端引导，无意图预处理 | 高 - 售后流程缺失订单校验 |
| UI 素材 | 使用 emoji 图标 | 中 - 品牌一致性不足 |
| 监控告警 | 日志记录有，告警机制缺失 | 中 - 无法及时发现问题 |
| 安全防护 | 基础校验，缺少限流 | 中 - 潜在滥用风险 |

### 1.2 架构合规性

- ✅ 严格遵守三层架构（products → services → infrastructure）
- ✅ 无跨产品依赖
- ✅ 数据库双写策略（PostgreSQL + Redis）

---

## 二、核心功能需求（P0 - 必须上线前完成）

### 2.1 默认语言切换为英文

**需求描述：**
将系统默认语言从中文切换为英文，确保海外用户（主要市场：UK、EU、US）获得原生英文体验。

**当前状态：**
- 后端状态翻译：`services/shopify/tracking.py` 同时输出 `_zh` 和 `_en` 字段
- Coze 提示词：`prompts/` 目录下为中文版本
- 前端文案：硬编码英文（WelcomeScreen.vue）

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| services | `shopify/tracking.py` | 默认返回 `_en` 字段作为主字段 |
| services | `tracking/models.py` | `TrackingStatus.zh` 改为 `.en` 作为默认 |
| products | `prompts/*.md` | 所有提示词改为英文版本 |
| products | `handlers/chat.py` | 系统消息默认英文 |
| frontend | `ChatPanel.vue` | 占位符、提示文案英文化 |
| frontend | `StatusBar.vue` | 状态文案英文化 |

**验收标准：**
- [ ] 所有 API 响应的状态文案默认为英文
- [ ] Coze 工作流输出默认英文（除非检测到中文输入）
- [ ] 前端所有按钮、提示、状态显示为英文
- [ ] 中文用户输入时，AI 仍能用中文回复

---

### 2.2 快捷回复业务逻辑优化 - Order Status

**需求描述：**
"Order Status" 选项改为 "Where's my package?"，点击后引导用户提供订单号或邮箱，然后将信息传递给 Coze 工作流。

**当前状态：**
- 前端本地回复，不调用后端 API
- 引导文案已存在，但未与后端集成

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `WelcomeScreen.vue` | 文案改为 "Where's my package?" |
| frontend | `ChatPanel.vue` | 增加意图标记，用户后续输入带上 `intent: order_status` |
| products | `handlers/chat.py` | 识别 `intent` 参数，传递给 Coze |

**验收标准：**
- [ ] 按钮显示 "Where's my package?"
- [ ] 点击后显示引导："Please provide your order number or email"
- [ ] 用户输入订单号后，Coze 能正确查询订单

---

### 2.3 快捷回复业务逻辑优化 - Product Help（售前）

**需求描述：**
售前咨询选项，用户点击后引导输入问题，直接将问题传递给 Coze 工作流，无需订单校验。

**当前状态：**
- 前端本地回复，引导用户描述问题
- 后续用户输入作为普通消息处理

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `WelcomeScreen.vue` | 保持现有文案 |
| frontend | `ChatPanel.vue` | 增加 `intent: presale` 标记 |
| products | `models.py` | ChatRequest 增加 `intent` 字段 |
| products | `handlers/chat.py` | 将 intent 传递给 Coze 的 `parameters` |

**验收标准：**
- [ ] 用户点击 "Product help" 后输入问题
- [ ] Coze 收到 `intent=presale` 参数
- [ ] AI 直接回答产品相关问题，无订单校验流程

---

### 2.4 快捷回复业务逻辑优化 - Running into a little issue（售后）

**需求描述：**
售后问题选项，用户必须先提供订单号，后端校验订单存在后，才将问题传递给 Coze 工作流。

**当前状态：**
- 当前按钮文案为 "Returns"
- 无订单校验机制

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `WelcomeScreen.vue` | 文案改为 "Running into a little issue" |
| frontend | `ChatPanel.vue` | 新增售后流程状态机（等待订单号 → 校验 → 输入问题） |
| frontend | `chatStore.ts` | 新增 `afterSaleState` 状态 |
| products | `handlers/chat.py` | 新增订单校验逻辑（调用 shopify service） |
| products | `models.py` | ChatRequest 增加 `order_number` 可选字段 |

**业务流程：**
```
用户点击 "Running into a little issue"
    ↓
AI 回复："Please provide your order number first"
    ↓
用户输入订单号（如 UK22080）
    ↓
后端调用 shopify.search_order_by_number() 校验
    ├─ 订单存在 → "Order found! Please describe your issue"
    └─ 订单不存在 → "Order not found. Please check and try again"
    ↓
用户输入问题
    ↓
将 (订单号 + 问题) 传递给 Coze 工作流
```

**验收标准：**
- [ ] 按钮显示 "Running into a little issue"
- [ ] 必须先输入有效订单号才能继续
- [ ] 无效订单号给出友好提示
- [ ] Coze 收到订单上下文后回答售后问题

---

### 2.5 快捷回复业务逻辑优化 - Contact Us

**需求描述：**
保留现有逻辑，告知用户如何联系人工客服。

**当前状态：**
- 前端本地回复，引导用户描述问题后转人工

**改动范围：**
- 无需改动，保持现有逻辑

**验收标准：**
- [ ] 点击后显示人工客服联系方式
- [ ] 引导用户描述问题以便分配专员

---

### 2.6 UI 素材替换

**需求描述：**
将客服图标和快捷回复 icon 替换为品牌设计素材。

**当前状态：**
- 快捷回复使用 emoji（🚚、🔧、↩️、📞）
- 客服头像使用 `fiido2.png`

**素材来源：**
`products/ai_chatbot/ai.fiido.comchat/` 目录

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `WelcomeScreen.vue` | icon 改为 `<img>` 引用素材图片 |
| frontend | `ChatFloatButton.vue` | 浮窗图标替换 |
| frontend | `public/` | 新增 icon 素材文件 |

**验收标准：**
- [ ] 快捷回复按钮显示品牌设计的 icon
- [ ] 客服头像与官网风格一致
- [ ] 图标在不同分辨率下清晰显示

---

## 三、重要功能需求（P1 - 上线后短期内完成）

### 3.1 意图预识别机制完善

**需求描述：**
将 4 个快捷回复作为意图预识别入口，不同意图走不同的前置校验逻辑。

**当前状态：**
- 快捷回复仅作为 UI 引导
- 无意图标记传递给后端

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `chatStore.ts` | 新增 `currentIntent` 状态 |
| frontend | `ChatPanel.vue` | 消息发送时携带 intent |
| products | `models.py` | 定义 Intent 枚举 |
| products | `handlers/chat.py` | 根据 intent 选择处理流程 |

**Intent 枚举定义：**
```python
class UserIntent(str, Enum):
    PRESALE = "presale"           # 售前咨询 - 无需订单
    ORDER_STATUS = "order_status" # 订单查询 - 需要订单号/邮箱
    AFTER_SALE = "after_sale"     # 售后问题 - 必须先校验订单
    CONTACT_AGENT = "contact_agent" # 人工转接
    GENERAL = "general"           # 通用对话
```

**验收标准：**
- [ ] 每个快捷回复对应一个 intent
- [ ] 后端根据 intent 执行不同前置逻辑
- [ ] Coze 工作流能识别并利用 intent 参数

---

### 3.2 监控告警机制

**需求描述：**
建立关键指标监控和异常告警机制。

**当前状态：**
- 日志记录完整（print 语句）
- 无结构化监控
- 无告警通知

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| infrastructure | `monitoring/` | 新增指标采集模块 |
| products | `handlers/*.py` | 埋点关键指标 |
| infrastructure | `logging/` | 结构化日志输出 |

**监控指标：**
- 请求响应时间（P50/P95/P99）
- Coze API 调用成功率
- 人工转接触发率
- 会话平均时长

**验收标准：**
- [ ] 关键指标可查询
- [ ] 异常时能发送告警（邮件/钉钉）

---

### 3.3 请求限流防护

**需求描述：**
防止恶意请求或滥用。

**当前状态：**
- 无请求限流
- 依赖 Coze 的限流

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| products | `main.py` | 集成 slowapi 或自定义限流中间件 |
| infrastructure | `security/` | 新增限流配置 |

**限流规则：**
- 每个 session_id：10 次/分钟
- 每个 IP：100 次/分钟
- 全局：1000 次/分钟

**验收标准：**
- [ ] 超过限流返回 429 状态码
- [ ] 限流信息记录到日志

---

## 四、扩展功能需求（P2 - 中长期规划）

### 4.1 多语言动态切换

**需求描述：**
支持用户手动切换语言，或根据浏览器语言自动适配。

**验收标准：**
- [ ] 前端提供语言切换按钮
- [ ] 语言偏好持久化到 localStorage
- [ ] API 响应根据语言参数返回对应文案

---

### 4.2 会话历史持久化

**需求描述：**
用户重新打开页面时，能恢复之前的会话历史。

**技术方案：session_id 持久化到 localStorage**

```typescript
// 改造后的逻辑
const getOrCreateSessionId = () => {
  let sessionId = localStorage.getItem('fiido_session_id')
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${randomString()}_${randomString()}`
    localStorage.setItem('fiido_session_id', sessionId)
  }
  return sessionId
}
```

**会话隔离保证：**

| 场景 | 结果 | 隔离性 |
|------|------|--------|
| 用户 A 在 Chrome | `session_A_chrome` → 独立会话 | ✅ |
| 用户 A 在 Firefox | `session_A_firefox` → 另一个独立会话 | ✅ |
| 用户 B 在 Chrome | `session_B_chrome` → 另一个独立会话 | ✅ |
| 用户 A 刷新 Chrome | 复用 `session_A_chrome` → 恢复历史 | ✅ |

**隔离原理：**
- `localStorage` 是浏览器级别隔离的（不同浏览器、不同设备各自独立）
- `session_id` 包含时间戳 + 随机字符串，全局唯一
- 不同用户/设备/浏览器必然生成不同的 `session_id`
- 同一浏览器多个标签页共享 `session_id`（期望行为）

**改动范围：**

| 层级 | 文件 | 改动内容 |
|------|------|---------|
| frontend | `chatStore.ts` | `sessionId` 改为从 localStorage 读取/写入 |
| frontend | `ChatPanel.vue` | 新增"清除会话"按钮 |
| products | `handlers/conversation.py` | 支持根据 session_id 恢复 conversation_id |

**验收标准：**
- [ ] 刷新页面后自动恢复会话历史
- [ ] 不同浏览器/设备会话完全隔离
- [ ] 提供清除历史的选项（清除 localStorage 中的 session_id）

---

### 4.3 富媒体消息支持

**需求描述：**
支持用户发送图片、视频等富媒体内容。

**验收标准：**
- [ ] 前端支持图片上传
- [ ] 后端存储到 OSS
- [ ] Coze 能处理图片输入

---

## 五、技术约束与注意事项

### 5.1 架构依赖规范

```
products/ai_chatbot/
    → 可以依赖 services/shopify、services/tracking、services/session
    → 可以依赖 infrastructure/bootstrap、infrastructure/database
    → 禁止依赖其他 products（如 agent_workbench）
```

### 5.2 数据库双写策略

- 写入顺序：PostgreSQL（主）→ Redis（缓存）
- Redis 失败时：记录日志，不阻塞业务
- 读取优先：Redis → PostgreSQL

### 5.3 Coze 工作流约束

- workflow_id：`7577578868671037445`
- app_id：`7577213576494989365`
- 会话隔离：必须传递 `session_name` 参数
- Token 有效期：需定期刷新（OAuthTokenManager 自动处理）

### 5.4 版本号规范

当前版本：`v7.6.23`
本次需求完成后版本：`v7.7.0`（新增功能，次版本号 +1）

---

## 六、涉及文件清单

### 6.1 Products 层

```
products/ai_chatbot/
├── handlers/
│   └── chat.py                    # [修改] 增加 intent 处理、订单校验
├── models.py                      # [修改] 增加 Intent 枚举、ChatRequest.intent
├── prompts/
│   ├── 意图识别.md                # [修改] 英文版本
│   ├── 订单查询回复.md            # [修改] 英文版本
│   ├── 产品咨询智能回复.md        # [修改] 英文版本
│   └── ...                        # [修改] 所有提示词英文化
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── WelcomeScreen.vue  # [修改] 快捷回复文案、icon
│   │   │   ├── ChatPanel.vue      # [修改] 售后流程状态机
│   │   │   └── StatusBar.vue      # [修改] 状态文案英文化
│   │   ├── stores/
│   │   │   └── chatStore.ts       # [修改] 增加 intent、afterSaleState、session持久化
│   │   └── api/
│   │       └── chat.ts            # [修改] 请求参数增加 intent
│   └── public/
│       └── icons/                 # [新增] 品牌 icon 素材
└── ai.fiido.comchat/              # [参考] UI 素材来源
```

### 6.2 Services 层

```
services/
├── shopify/
│   └── tracking.py                # [修改] 默认返回英文字段
└── tracking/
    └── models.py                  # [修改] TrackingStatus 默认英文
```

### 6.3 Infrastructure 层

```
infrastructure/
├── monitoring/                    # [新增] 监控指标采集（P1）
└── security/                      # [新增] 限流配置（P1）
```

---

## 七、优先级排序总结

| 优先级 | 需求 | 预计工作量 |
|--------|------|-----------|
| **P0** | 2.1 默认语言切换为英文 | 2 天 |
| **P0** | 2.2 Order Status 逻辑 | 0.5 天 |
| **P0** | 2.3 Product Help 逻辑 | 0.5 天 |
| **P0** | 2.4 售后问题订单校验 | 2 天 |
| **P0** | 2.5 Contact Us 保持 | 0 天 |
| **P0** | 2.6 UI 素材替换 | 1 天 |
| **P1** | 3.1 意图预识别完善 | 1 天 |
| **P1** | 3.2 监控告警 | 2 天 |
| **P1** | 3.3 请求限流 | 1 天 |
| **P2** | 4.1 多语言动态切换 | 3 天 |
| **P2** | 4.2 会话历史持久化 | 2 天 |
| **P2** | 4.3 富媒体消息 | 5 天 |

**P0 总计：约 6 天**
**P1 总计：约 4 天**

---

*本文档可直接用于 PRD 详细设计和开发任务拆分。*
