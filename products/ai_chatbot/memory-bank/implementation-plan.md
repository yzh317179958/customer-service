# AI 智能客服 - 实现计划

> **版本**: v7.7.0
> **创建日期**: 2025-12-24
> **方法论**: Vibe Coding 分步骤开发

---

## 一、开发原则

1. **自底向上**: infrastructure → services → products
2. **增量开发**: 每步只做一件事，立即测试验证
3. **频繁提交**: 每个功能点完成即提交
4. **单次提交**: < 10 个文件，< 500 行代码

---

## 二、临时策略：转人工“保留但不启用”（contact-only）

> **背景**：当前阶段不做人工转接闭环，但需要保留未来转人工能力的代码结构。  
> **目标**：任何“转人工/人工客服”触发场景都 **不改变会话状态**、**不走人工转接**，继续保持 AI 对话可用；同时在对话中输出固定联系文案，引导用户联系人工客服。

### 2.1 统一输出文案（固定内容）

当命中“转人工触发条件”时，向用户输出以下内容（作为 assistant/system 提示均可，但需保证在聊天窗口可见）：

```
您可以通过以下方式联系我们：
邮箱：service@fiido.com
电话：(852) 56216918（服务时间：周一至周五，上午9点至晚上10点，GMT+8）

祝您骑行愉快!
```

### 2.2 触发条件（本期只做“提示”，不做转接）

- 用户点击前端入口（当前 UI 的 “Live Agent / Contact Us”）
- 用户输入命中监管关键词（示例：人工、转人工、客服、投诉…）
-（可选）后端监管引擎判定需要转人工（VIP / AI fail-loop）时也仅提示联系方式

### 2.3 保留未来转人工能力的方式（开关）

- 引入开关（建议：`ENABLE_MANUAL_HANDOFF`，默认 `false`）
  - `false`：当前阶段行为（contact-only，不改状态）
  - `true`：恢复原有转人工状态机（`pending_manual/manual_live`）与 SSE 通知链路

---

## 三、依赖关系

```
Phase 1 核心功能:

Step 1.1 ─┬─→ Step 1.3 ─→ Step 1.4 ─→ Step 1.8
          │
Step 1.2 ─┘

Step 1.5 ─→ Step 1.6 ─→ Step 1.7.1 ─→ Step 1.7.2 ─→ Step 1.7.3

Phase 2 安全防护 (已迁移至 infrastructure/security 模块):

  ┌─────────────────────────────────────────────────────┐
  │  参见: infrastructure/security/memory-bank/         │
  │        implementation-plan.md Step 9               │
  └─────────────────────────────────────────────────────┘
```

---

## 四、Phase 0（插入任务）- Contact-only（不转接、不改状态）

> 说明：此 Phase 属于“生产策略调整”，会影响既有转人工链路，但目标是“保留代码、禁用状态机”。

### Step 0.1: 新增开关与联系文案构造入口

**目标**：以配置开关控制“是否启用转人工状态机”，并提供统一联系文案构造入口。

**改动**:
- 新增环境变量（建议）：
  - `ENABLE_MANUAL_HANDOFF=false`（默认 false）
- 新增工具函数（建议位置：`products/ai_chatbot` 内部）：
  - `get_contact_support_message()`：返回固定联系文案（本期先硬编码；后续可改为从 env/配置读取）

**验证**:
```bash
python3 -c "from products.ai_chatbot.<module> import get_contact_support_message; print(get_contact_support_message())"
# 期望输出包含: service@fiido.com, (852) 56216918
```

---

### Step 0.2: manual/escalate 改为 contact-only（不改会话状态）

**目标**：用户点击“转人工”入口时，不触发 `pending_manual/manual_live`，仅返回并展示联系文案。

**改动**:
- `products/ai_chatbot/handlers/manual.py`
  - 当 `ENABLE_MANUAL_HANDOFF=false`：
    - 不调用 `session_state.transition_status()`
    - 不推送 `status_change` SSE（保持未来可恢复）
    - 返回 `success=true` + `contact_message`
  - 当 `ENABLE_MANUAL_HANDOFF=true`：保持现有行为不变（未来启用）

**验证**:
- `curl -X POST http://localhost:8000/api/manual/escalate -H 'Content-Type: application/json' -d '{"session_name":"session_x","reason":"manual"}'`
- 期望：响应包含 `contact_message`；会话状态不变（仍为 `bot_active`）

---

### Step 0.3: chat 端点中“触发转人工”逻辑改为 contact-only（不改会话状态）

**目标**：用户输入命中关键词/VIP/fail-loop 等触发时，继续 AI 对话，但追加联系文案；不进入人工状态机。

**改动**:
- `products/ai_chatbot/handlers/chat.py`
  - 当 `ENABLE_MANUAL_HANDOFF=false`：
    - 禁止把会话转为 `pending_manual`
    - 若会话当前处于 `pending_manual/manual_live`（历史遗留），也不阻断 AI（避免 409）
    - 在合适时机把联系文案追加到回复末尾（或作为额外 system 消息）
  - 当 `ENABLE_MANUAL_HANDOFF=true`：保持现有转人工状态机逻辑

**验证**:
- 发送包含“转人工/人工/客服”等关键词的消息：
  - 仍返回 AI 回复
  - 回复末尾追加联系文案
  - 不出现 409，不出现 session 状态切换

---

### Step 0.4: 前端“转人工”入口改为展示联系文案（不改变前端状态机）

**目标**：点击 “Live Agent” 不再让 UI 进入 `pending_manual/manual_live`，只在聊天窗口展示联系文案。

**改动**:
- `products/ai_chatbot/frontend/src/stores/chatStore.ts`
  - `escalateToManual()`：在 contact-only 模式下不更新 `sessionStatus`
- `products/ai_chatbot/frontend/src/components/ChatPanel.vue`
  - 点击按钮后展示联系文案（从后端返回或前端本地模板）

**验证**:
- 点击 Live Agent：
  - 聊天窗口出现联系文案
  - 输入框仍可用（继续 AI 对话）

---

### Step 0.5: 回归测试（确保“禁用转接”不影响其它功能）

**目标**：确保 contact-only 改动不破坏普通聊天、售后状态机、聊天记录存储等。

**验证建议**:
- 普通问答（`/api/chat/stream`）
- 售后流程（订单校验 → 问题 → Coze 回复）
- contact-only 触发（按钮 + 关键词）
- 聊天记录页面能查询到本次会话（坐席工作台）

---

## 五、Phase 1 - P0 核心功能

### Step 1.1: TrackingStatus 枚举英文化

**目标**: `services/tracking/models.py` 中 TrackingStatus 枚举值改为英文

**改动**:
- 将 `TrackingStatus` 枚举的 value 从中文改为英文
- 添加 `zh` 属性保留中文翻译备用

**验证**:
```bash
python3 -c "from services.tracking.models import TrackingStatus; print(TrackingStatus.DELIVERED.value)"
# 期望输出: Delivered
```

**状态**: ⬜ 待开发

---

### Step 1.2: Shopify tracking.py 返回英文

**目标**: `services/shopify/tracking.py` 状态翻译函数默认返回英文

**依赖**: Step 1.1

**改动**:
- 修改 `get_status_text()` 函数默认返回 `_en` 字段
- 保留 `lang` 参数支持切换中文

**验证**:
```bash
curl http://localhost:8000/api/tracking/UK22080
# 期望: "current_status": "In Transit" (非 "运输中")
```

**状态**: ⬜ 待开发

---

### Step 1.3: 前端 UI 文案英文化

**目标**: 前端组件中的中文文案改为英文

**依赖**: Step 1.1, 1.2

**改动**:
- `ChatPanel.vue`: 输入框 placeholder 改为英文
- `ChatMessage.vue`: 物流时间线提示改为英文
- `StatusBar.vue`: 确认状态文案为英文

**验证**:
- 打开 https://ai.fiido.com/chat-test/
- 检查输入框、状态栏、物流时间线均为英文

**状态**: ⬜ 待开发

---

### Step 1.4: 提示词英文化

**目标**: `prompts/订单查询回复_v2.md` 翻译为英文

**依赖**: Step 1.3

**改动**:
- 翻译 `prompts/订单查询回复_v2.md` 为英文版
- 保留原中文版本为 `_zh.md` 后缀备份

**验证**:
- 发送英文问题 "Where is my order UK22080?"，AI 回复英文
- 发送中文问题 "我的订单 UK22080 在哪？"，AI 仍能回复中文

**注意**: 修改后由用户手动迁移到 Coze 平台

**状态**: ⬜ 待开发

---

### Step 1.5: UserIntent 枚举定义

**目标**: 在 `products/ai_chatbot/models.py` 新增 UserIntent 枚举

**改动**:
- 新增 `UserIntent` 枚举：PRESALE, ORDER_STATUS, AFTER_SALE, CONTACT_AGENT, GENERAL
- `ChatRequest` 添加 `intent: Optional[UserIntent]` 字段
- `ChatRequest` 添加 `order_number: Optional[str]` 字段

**验证**:
```bash
python3 -c "from products.ai_chatbot.models import UserIntent; print(UserIntent.PRESALE.value)"
# 期望输出: presale
```

**状态**: ⬜ 待开发

---

### Step 1.6: chat.py 处理 intent 参数

**目标**: `handlers/chat.py` 识别并传递 intent 参数给 Coze

**依赖**: Step 1.5

**改动**:
- 从 `ChatRequest` 读取 `intent` 字段
- 将 intent 传递给 Coze workflow 的 `parameters`

**验证**:
```bash
curl -X POST http://localhost:8000/api/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message":"test","intent":"presale"}'
# 期望: Coze 收到 intent=presale 参数
```

**状态**: ⬜ 待开发

---

### Step 1.7.1: WelcomeScreen 快捷按钮文案更新

**目标**: 更新 `WelcomeScreen.vue` 四个快捷按钮的文案

**依赖**: Step 1.6

**改动**:
- "Order status" → "Where's my package?"
- "Product help" 保持不变
- "Returns" → "Running into a little issue"
- "Contact us" 保持不变
- 每个按钮添加 `intent` 字段映射

**验证**:
- 打开聊天窗口，检查 4 个按钮显示正确文案
- 点击按钮后控制台输出对应 intent 值

**状态**: ⬜ 待开发

---

### Step 1.7.2: chatStore 新增售后状态

**目标**: `chatStore.ts` 新增售后流程状态管理

**依赖**: Step 1.7.1

**改动**:
- 新增 `AfterSaleState` 类型：idle, awaiting_order, validating, order_found
- 新增 `afterSaleState` ref
- 新增 `validatedOrderNumber` ref

**验证**:
- 在 Vue DevTools 中检查 chatStore 包含新状态字段
- 状态初始值为 `idle`

**状态**: ⬜ 待开发

---

### Step 1.7.3: ChatPanel 售后流程状态机

**目标**: `ChatPanel.vue` 实现售后流程状态机逻辑

**依赖**: Step 1.7.2

**改动**:
- 点击 "Running into a little issue" 时设置 `afterSaleState = 'awaiting_order'`
- 用户输入订单号时调用后端校验 API
- 校验成功后设置 `afterSaleState = 'order_found'`
- 用户输入问题后携带 `order_number` 发送给 Coze

**验证**:
1. 点击 "Running into a little issue" → 显示引导
2. 输入 "UK99999" → 显示 "Order not found"
3. 输入 "UK22080" → 显示 "Order found"
4. 输入问题 → Coze 返回带订单上下文的回复

**状态**: ⬜ 待开发

---

### Step 1.8: UI 素材替换

**目标**: emoji 替换为品牌 icon

**依赖**: Step 1.7.3

**改动**:
- 复制 `ai.fiido.comchat/hi-there/` 下 4 个 icon 到 `frontend/public/icons/`
- 重命名 `iocn-*` → `icon-*`
- `WelcomeScreen.vue` 中 emoji 改为 `<img>` 标签

**验证**:
- 4 个快捷按钮显示品牌 icon（非 emoji）
- 不同屏幕尺寸下 icon 清晰显示

**状态**: ⬜ 待开发

---

## 四、Phase 2 - 安全防护（由 infrastructure/security 模块统一实现）

> **重要**: 本 Phase 已迁移至 `infrastructure/security/` 模块统一实现
>
> **参见**: [infrastructure/security/memory-bank/implementation-plan.md](../../../infrastructure/security/memory-bank/implementation-plan.md)

### 迁移说明

安全防护功能（限流、监控指标等）属于基础设施层能力，应由 `infrastructure/security/` 统一提供，所有产品共享复用。

**原 Step 2.1-2.4 已迁移至安全模块：**

| 原 AI 客服 Step | 迁移至安全模块 Step | 说明 |
|-----------------|---------------------|------|
| Step 2.1 添加 slowapi 依赖 | Step 1 | 依赖统一管理 |
| Step 2.2 集成限流中间件 | Step 2, 7 | 限流器工厂 + 模块导出 |
| Step 2.3 chat 端点限流 | **Step 9** | AI 客服接入限流 |
| Step 2.4 监控指标端点 | Step 11, 12 | Prometheus 指标 |

### AI 客服安全接入

安全模块 **Step 9** 将为 AI 客服完成以下配置：

```yaml
ai_chatbot:
  rate_limits:
    "/api/chat/stream": "10/minute"
    "/api/chat": "10/minute"
    "/api/tracking/*": "30/minute"
    "/api/shopify/*": "20/minute"
    default: "60/minute"

  message_limits:
    max_length: 1000  # 单条消息最大字符数
```

### 开发顺序

```
1. 完成 AI 客服 Phase 1（业务功能）
2. 完成 infrastructure/security Phase 1（安全组件）
3. 执行 infrastructure/security Step 9（AI 客服接入）
```

---

## 五、Phase 3 - P2 扩展功能（待规划）

| Step | 任务 | 状态 |
|------|------|------|
| 3.1 | 多语言动态切换 | ⬜ 规划中 |
| 3.2 | 会话历史持久化 (localStorage) | ⬜ 规划中 |
| 3.3 | 富媒体消息支持 | ⬜ 规划中 |

---

## 六、开发检查清单

每个 Step 完成后：

- [ ] 代码无语法错误
- [ ] 按验证方法测试通过
- [ ] 不破坏现有功能
- [ ] 更新 `progress.md` 状态
- [ ] Git 提交（message 包含 Step 编号）

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v7.7.0-r4 | 2025-12-24 | Phase 2 安全防护迁移至 infrastructure/security 模块统一实现 |
| v7.7.0-r3 | 2025-12-24 | 精简格式：移除代码示例，只保留指令；拆分大步骤为小步骤 |
| v7.7.0-r2 | 2025-12-24 | 增加依赖关系、代码示例、具体改动说明 |
| v7.7.0 | 2025-12-24 | 初始版本 |
