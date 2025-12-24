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

## 二、依赖关系

```
Phase 1 核心功能:

Step 1.1 ─┬─→ Step 1.3 ─→ Step 1.4 ─→ Step 1.8
          │
Step 1.2 ─┘

Step 1.5 ─→ Step 1.6 ─→ Step 1.7.1 ─→ Step 1.7.2 ─→ Step 1.7.3

Phase 2 扩展功能 (依赖 Phase 1 全部完成):

Step 2.1 ─→ Step 2.2 ─→ Step 2.3 ─→ Step 2.4
```

---

## 三、Phase 1 - P0 核心功能

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

## 四、Phase 2 - P1 重要功能

### Step 2.1: 添加 slowapi 依赖

**目标**: `requirements.txt` 添加限流依赖

**依赖**: Phase 1 完成

**改动**:
- `requirements.txt` 添加 `slowapi==0.1.9`
- 服务器执行 `pip install slowapi`

**验证**:
```bash
python3 -c "import slowapi; print(slowapi.__version__)"
```

**状态**: ⬜ 待开发

---

### Step 2.2: main.py 集成限流中间件

**目标**: `products/ai_chatbot/main.py` 集成 SlowAPI

**依赖**: Step 2.1

**改动**:
- 初始化 `Limiter` 实例
- 添加 `RateLimitExceeded` 异常处理器
- 将 limiter 挂载到 app.state

**验证**:
```bash
# 快速发送 11 次请求
for i in {1..11}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/api/health; done
# 期望: 前 10 次 200，第 11 次 429
```

**状态**: ⬜ 待开发

---

### Step 2.3: chat 端点添加限流装饰器

**目标**: `/api/chat/stream` 端点添加限流

**依赖**: Step 2.2

**改动**:
- `handlers/chat.py` 的 `chat_stream` 函数添加 `@limiter.limit("10/minute")`

**验证**:
```bash
# 对 chat/stream 端点快速发 11 次
for i in {1..11}; do
  curl -s -o /dev/null -w "%{http_code}\n" \
    -X POST http://localhost:8000/api/chat/stream \
    -H "Content-Type: application/json" \
    -d '{"message":"test"}'
done
# 期望: 第 11 次返回 429
```

**状态**: ⬜ 待开发

---

### Step 2.4: 监控指标端点

**目标**: 暴露 `/metrics` 端点

**依赖**: Step 2.3

**改动**:
- `requirements.txt` 添加 `prometheus-client==0.19.0`
- `infrastructure/monitoring/metrics.py` 定义指标
- `main.py` 添加 `/metrics` 路由

**验证**:
```bash
curl http://localhost:8000/metrics
# 期望: 返回 Prometheus 格式文本
```

**状态**: ⬜ 待开发

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
| v7.7.0-r3 | 2025-12-24 | 精简格式：移除代码示例，只保留指令；拆分大步骤为小步骤 |
| v7.7.0-r2 | 2025-12-24 | 增加依赖关系、代码示例、具体改动说明 |
| v7.7.0 | 2025-12-24 | 初始版本 |
