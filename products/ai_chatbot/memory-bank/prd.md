# AI 智能客服 - 产品需求文档

> **版本**: v7.7.0
> **创建日期**: 2024-12-24
> **状态**: 待开发

---

## 一、产品概述

AI 智能客服是 Fiido 智能服务平台的核心产品，为海外用户（UK、EU、US）提供 24/7 自助服务能力。

### 1.1 核心价值

- **自助服务**: 用户无需等待即可查询订单、物流状态
- **智能对话**: 基于 Coze Workflow 的多轮对话能力
- **无缝转接**: 智能判断时机，自动转接人工客服

### 1.2 当前状态

| 能力 | 状态 |
|------|------|
| Coze 工作流集成 | ✅ 已完成 |
| 订单查询（多站点） | ✅ 已完成 |
| 物流追踪（17track） | ✅ 已完成 |
| 人工转接（状态机） | ✅ 已完成 |
| 前端交互（Vue 3） | ✅ 已完成 |

---

## 二、v7.7.0 核心需求（P0）

### 2.1 默认语言切换为英文

**需求描述**: 系统默认语言从中文切换为英文，确保海外用户获得原生英文体验。

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| services | `shopify/tracking.py` | 默认返回 `_en` 字段 |
| services | `tracking/models.py` | `TrackingStatus.en` 作为默认 |
| products | `prompts/*.md` | 所有提示词英文化 |
| products | `handlers/chat.py` | 系统消息默认英文 |
| frontend | `ChatPanel.vue` | 占位符、提示文案英文化 |

**验收标准**:
- [ ] API 响应状态文案默认英文
- [ ] Coze 工作流输出默认英文
- [ ] 前端所有 UI 文案显示英文
- [ ] 中文输入时 AI 仍能中文回复

---

### 2.2 快捷回复 - Order Status

**需求描述**: "Order Status" 改为 "Where's my package?"，引导用户提供订单号后调用 Coze。

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| frontend | `WelcomeScreen.vue` | 文案改为 "Where's my package?" |
| frontend | `ChatPanel.vue` | 携带 `intent: order_status` |
| products | `handlers/chat.py` | 识别 intent 参数 |

**验收标准**:
- [ ] 按钮显示 "Where's my package?"
- [ ] 引导用户输入订单号或邮箱
- [ ] Coze 能正确查询订单

---

### 2.3 快捷回复 - Product Help（售前）

**需求描述**: 售前咨询选项，用户输入问题后直接传递给 Coze，无需订单校验。

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| frontend | `ChatPanel.vue` | 携带 `intent: presale` |
| products | `models.py` | ChatRequest 增加 `intent` 字段 |
| products | `handlers/chat.py` | intent 传递给 Coze |

**验收标准**:
- [ ] 用户点击后可直接输入问题
- [ ] Coze 收到 `intent=presale` 参数
- [ ] AI 直接回答，无订单校验

---

### 2.4 快捷回复 - Running into a little issue（售后）

**需求描述**: 售后问题必须先校验订单存在，再将问题传递给 Coze。

**业务流程**:
```
用户点击 "Running into a little issue"
    ↓
AI: "Please provide your order number first"
    ↓
用户输入订单号（如 UK22080）
    ↓
后端调用 shopify.search_order_by_number() 校验
    ├─ 存在 → "Order found! Please describe your issue"
    └─ 不存在 → "Order not found. Please check and try again"
    ↓
用户输入问题
    ↓
将 (订单号 + 问题) 传递给 Coze
```

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| frontend | `WelcomeScreen.vue` | 文案改为 "Running into a little issue" |
| frontend | `ChatPanel.vue` | 新增售后流程状态机 |
| frontend | `chatStore.ts` | 新增 `afterSaleState` 状态 |
| products | `handlers/chat.py` | 订单校验逻辑 |
| products | `models.py` | ChatRequest 增加 `order_number` 字段 |

**验收标准**:
- [ ] 必须先输入有效订单号
- [ ] 无效订单号给出友好提示
- [ ] Coze 收到订单上下文

---

### 2.5 快捷回复 - Contact Us

**需求描述**: 保留现有逻辑，告知用户如何联系人工客服。

**验收标准**:
- [ ] 点击后显示联系方式
- [ ] 引导用户描述问题

---

### 2.6 UI 素材替换

**需求描述**: 将 emoji 图标替换为品牌设计素材。

**素材来源**: `products/ai_chatbot/ai.fiido.comchat/`

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| frontend | `WelcomeScreen.vue` | icon 改为 `<img>` |
| frontend | `ChatFloatButton.vue` | 浮窗图标替换 |
| frontend | `public/icons/` | 新增素材文件 |

**验收标准**:
- [ ] 快捷回复显示品牌 icon
- [ ] 客服头像与官网一致
- [ ] 不同分辨率下清晰显示

---

## 三、v7.7.0 重要需求（P1）

### 3.1 意图预识别机制

**需求描述**: 4 个快捷回复作为意图预识别入口，不同意图走不同前置校验。

**Intent 枚举**:
```python
class UserIntent(str, Enum):
    PRESALE = "presale"           # 售前 - 无需订单
    ORDER_STATUS = "order_status" # 订单查询 - 需订单号/邮箱
    AFTER_SALE = "after_sale"     # 售后 - 必须校验订单
    CONTACT_AGENT = "contact_agent" # 人工转接
    GENERAL = "general"           # 通用对话
```

**验收标准**:
- [ ] 每个快捷回复对应一个 intent
- [ ] 后端根据 intent 执行不同逻辑
- [ ] Coze 能识别 intent 参数

---

### 3.2 监控告警

**需求描述**: 建立关键指标监控和异常告警。

**监控指标**:
- 请求响应时间（P50/P95/P99）
- Coze API 调用成功率
- 人工转接触发率
- 会话平均时长

**改动范围**:
| 层级 | 文件 | 改动 |
|------|------|------|
| infrastructure | `monitoring/` | 新增指标采集模块 |
| products | `handlers/*.py` | 埋点关键指标 |

**验收标准**:
- [ ] 关键指标可查询
- [ ] 异常时发送告警

---

### 3.3 请求限流

**需求描述**: 防止恶意请求或滥用。

**限流规则**:
- 每个 session_id: 10 次/分钟
- 每个 IP: 100 次/分钟
- 全局: 1000 次/分钟

**验收标准**:
- [ ] 超限返回 429 状态码
- [ ] 限流记录到日志

---

## 四、v7.7.0 扩展需求（P2）

### 4.1 多语言动态切换

- 前端提供语言切换按钮
- 语言偏好持久化到 localStorage
- API 响应根据语言参数返回

### 4.2 会话历史持久化

**技术方案**: session_id 持久化到 localStorage

```typescript
const getOrCreateSessionId = () => {
  let sessionId = localStorage.getItem('fiido_session_id')
  if (!sessionId) {
    sessionId = `session_${Date.now()}_${randomString()}_${randomString()}`
    localStorage.setItem('fiido_session_id', sessionId)
  }
  return sessionId
}
```

**隔离保证**:
- 不同浏览器/设备各自独立
- 同一浏览器多标签页共享（期望行为）

### 4.3 富媒体消息支持

- 前端支持图片上传
- 后端存储到 OSS
- Coze 处理图片输入

---

## 五、优先级与工作量

| 优先级 | 需求 | 工作量 |
|--------|------|--------|
| **P0** | 2.1 默认语言英文 | 2 天 |
| **P0** | 2.2 Order Status | 0.5 天 |
| **P0** | 2.3 Product Help | 0.5 天 |
| **P0** | 2.4 售后订单校验 | 2 天 |
| **P0** | 2.5 Contact Us | 0 天 |
| **P0** | 2.6 UI 素材替换 | 1 天 |
| **P1** | 3.1 意图预识别 | 1 天 |
| **P1** | 3.2 监控告警 | 2 天 |
| **P1** | 3.3 请求限流 | 1 天 |
| **P2** | 4.1 多语言切换 | 3 天 |
| **P2** | 4.2 会话持久化 | 2 天 |
| **P2** | 4.3 富媒体消息 | 5 天 |

**P0 总计**: 约 6 天
**P1 总计**: 约 4 天

---

## 六、涉及文件清单

### Products 层
```
products/ai_chatbot/
├── handlers/chat.py            # [修改] intent 处理、订单校验
├── models.py                   # [修改] Intent 枚举、ChatRequest
├── prompts/*.md                # [修改] 提示词英文化
└── frontend/
    ├── src/components/
    │   ├── WelcomeScreen.vue   # [修改] 快捷回复文案
    │   ├── ChatPanel.vue       # [修改] 售后流程状态机
    │   └── StatusBar.vue       # [修改] 状态文案英文化
    ├── src/stores/chatStore.ts # [修改] intent、afterSaleState
    └── public/icons/           # [新增] 品牌 icon
```

### Services 层
```
services/
├── shopify/tracking.py         # [修改] 默认返回英文
└── tracking/models.py          # [修改] TrackingStatus 默认英文
```

### Infrastructure 层
```
infrastructure/
├── monitoring/                 # [新增] 指标采集（P1）
└── security/                   # [新增] 限流配置（P1）
```

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.7.0 | 2025-12-24 | 全新创建，基于 ai-chatbot-prd-v7.7.md |
