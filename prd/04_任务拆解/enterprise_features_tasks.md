# 企业级客服工作台功能任务拆解 v3.5+

> **文档版本**: v1.0
> **创建时间**: 2025-11-26
> **参考系统**: 拼多多商家客服工作台、聚水潭ERP客服模块
> **适用场景**: 跨境电商独立站AI客服系统
> **关联文档**: `prd/01_全局指导/REFERENCE_SYSTEMS.md`

---

## 📊 功能优先级说明

| 优先级 | 说明 | 时间预估 | 适用场景 |
|-------|------|---------|---------|
| **P0** | 紧急且重要，立即实施 | 3-5天 | 严重影响用户体验或业务运转 |
| **P1** | 重要且常用，短期实施 | 1-2周 | 显著提升效率，用户强需求 |
| **P2** | 重要但不紧急，中期实施 | 1-2月 | 锦上添花，提升体验 |
| **P3** | 锦上添花，长期规划 | 2-6月 | 创新功能，差异化竞争 |

---

## 🎯 Phase 1: 基础增强 (v3.5.0 - 2周)

### 任务1: 快捷回复系统增强 ⭐ P0

**当前状态**: ✅ **已完成** (v3.5.0 - 2025-11-26)
- ✅ 后端API完整实现（CRUD + 使用统计）
- ✅ 前端组件完整实现（分类、搜索、变量替换）
- ✅ 5个分类管理
- ✅ 17个动态变量支持
- ✅ 权限控制（管理员/坐席）
- ✅ 使用次数追踪
- ✅ 回归测试通过（12/12）

**目标**:
实现拼多多级别的快捷回复功能，支持分类、变量替换、快捷键

**功能需求**:

#### 1.1 快捷回复分类管理

**数据模型**:
```typescript
interface QuickReply {
  id: string
  category: 'pre_sales' | 'after_sales' | 'logistics' | 'technical' | 'policy'
  title: string
  content: string
  variables: string[]  // 支持的变量列表
  shortcut?: string    // 快捷键 (如 'Ctrl+1')
  is_shared: boolean   // 是否团队共享
  created_by: string
  usage_count: number  // 使用次数统计
}

interface QuickReplyCategory {
  key: string
  label: string
  icon: string
  color: string
}
```

**分类定义**:
- 售前咨询 (pre_sales): 产品介绍、选型建议、价格说明
- 售后服务 (after_sales): 退换货、质量问题、保修政策
- 物流相关 (logistics): 配送时效、物流追踪、清关说明
- 技术支持 (technical): 故障排查、使用教程、参数说明
- 政策条款 (policy): 隐私政策、服务条款、合规说明

**UI设计**:
```
┌─────────────────────────────────────────┐
│ 快捷短语                         [设置] │
├─────────────────────────────────────────┤
│ [售前] [售后] [物流] [技术] [政策]      │
├─────────────────────────────────────────┤
│ 🔍 搜索短语...                          │
├─────────────────────────────────────────┤
│ ✓ 您好，很高兴为您服务！           Ctrl+1│
│ ✓ 关于{product_name}的详细参数...  Ctrl+2│
│ ✓ 您的订单{order_id}已发货        Ctrl+3│
│ ✓ 预计{delivery_days}天内送达     Ctrl+4│
└─────────────────────────────────────────┘
```

#### 1.2 动态变量替换

**支持的变量**:
```typescript
const QUICK_REPLY_VARIABLES = {
  // 客户信息
  '{customer_name}': '客户姓名',
  '{customer_email}': '客户邮箱',
  '{customer_country}': '客户国家',

  // 订单信息
  '{order_id}': '订单号',
  '{order_amount}': '订单金额',
  '{order_status}': '订单状态',
  '{payment_method}': '支付方式',

  // 商品信息
  '{product_name}': '商品名称',
  '{product_sku}': '商品SKU',
  '{product_price}': '商品价格',
  '{product_stock}': '库存数量',

  // 物流信息
  '{tracking_number}': '物流单号',
  '{delivery_days}': '配送天数',
  '{carrier}': '物流公司',

  // 其他
  '{agent_name}': '坐席姓名',
  '{current_date}': '当前日期',
  '{current_time}': '当前时间'
}
```

**替换逻辑**:
```typescript
function replaceVariables(content: string, context: SessionContext): string {
  let result = content

  // 客户信息
  result = result.replace('{customer_name}', context.customer?.name || '尊敬的客户')
  result = result.replace('{customer_email}', context.customer?.email || '')

  // 订单信息
  if (context.currentOrder) {
    result = result.replace('{order_id}', context.currentOrder.id)
    result = result.replace('{order_amount}', `€${context.currentOrder.amount}`)
  }

  // 时间信息
  result = result.replace('{current_date}', new Date().toLocaleDateString('zh-CN'))
  result = result.replace('{current_time}', new Date().toLocaleTimeString('zh-CN'))

  return result
}
```

#### 1.3 快捷键支持

**快捷键映射**:
```typescript
const QUICK_REPLY_SHORTCUTS = {
  'Ctrl+1': 'welcome_message',
  'Ctrl+2': 'thank_you',
  'Ctrl+3': 'order_shipped',
  'Ctrl+4': 'refund_policy',
  'Ctrl+5': 'warranty_info',
  'Ctrl+6': 'delivery_time',
  'Ctrl+7': 'out_of_stock',
  'Ctrl+8': 'payment_issue',
  'Ctrl+9': 'goodbye'
}
```

**全局监听**:
```typescript
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && /^[1-9]$/.test(e.key)) {
    e.preventDefault()
    const shortcut = `Ctrl+${e.key}`
    const replyId = QUICK_REPLY_SHORTCUTS[shortcut]
    if (replyId) {
      insertQuickReply(replyId)
    }
  }
})
```

**后端API**:
```python
# 获取快捷回复列表
@app.get("/api/quick-replies")
async def get_quick_replies(
    category: Optional[str] = None,
    agent: dict = Depends(require_agent)
):
    """获取快捷回复列表"""
    pass

# 创建快捷回复
@app.post("/api/quick-replies")
async def create_quick_reply(
    request: CreateQuickReplyRequest,
    agent: dict = Depends(require_admin)
):
    """创建快捷回复（需要管理员权限）"""
    pass

# 使用统计
@app.post("/api/quick-replies/{id}/use")
async def use_quick_reply(id: str):
    """记录使用次数"""
    pass
```

**验收标准**:
- [ ] 支持5个分类的快捷回复
- [ ] 支持至少12个动态变量
- [ ] 支持Ctrl+1到Ctrl+9快捷键
- [ ] 显示变量预览（鼠标悬停显示替换结果）
- [ ] 统计使用频率，自动排序
- [ ] 管理员可配置团队共享短语

**预估工时**: 3天

---

### 任务2: 会话标签系统 ⭐ P0

**当前状态**:
- ❌ 无标签功能

**目标**:
实现会话标签功能，快速分类和筛选会话

**功能需求**:

#### 2.1 标签数据模型

```typescript
interface SessionTag {
  id: string
  name: string
  color: string  // hex颜色
  icon?: string
  category: 'status' | 'priority' | 'custom'
  is_system: boolean  // 系统预设 vs 自定义
  created_by?: string
}

// 预设标签
const SYSTEM_TAGS = [
  { name: 'VIP', color: '#F59E0B', icon: 'Crown' },
  { name: '退款', color: '#EF4444', icon: 'DollarSign' },
  { name: '售后', color: '#8B5CF6', icon: 'Tool' },
  { name: '技术', color: '#3B82F6', icon: 'Cpu' },
  { name: '紧急', color: '#DC2626', icon: 'AlertCircle' },
  { name: '跟进', color: '#10B981', icon: 'Clock' }
]
```

#### 2.2 UI设计

**会话列表标签显示**:
```
┌──────────────────────────────────────┐
│ [👤] John Smith         [10:30]     │
│      电池续航问题...                  │
│      [VIP] [技术] [紧急]              │
└──────────────────────────────────────┘
```

**标签管理界面**:
```
┌─────────────────────────────────────┐
│ 标签管理                     [+ 新建]│
├─────────────────────────────────────┤
│ 系统标签                             │
│ 🟡 VIP           使用 156次  [编辑] │
│ 🔴 退款          使用 89次   [编辑] │
│ 🟣 售后          使用 234次  [编辑] │
│                                      │
│ 自定义标签                           │
│ 🔵 电池问题      使用 45次   [删除] │
│ 🟢 物流咨询      使用 67次   [删除] │
└─────────────────────────────────────┘
```

**标签筛选**:
```
会话筛选: [全部▾] [待接入] [服务中]
标签筛选: [VIP] [退款] [售后] [技术] [+更多]
```

#### 2.3 后端实现

```python
# 标签模型
class SessionTag(BaseModel):
    id: str
    name: str
    color: str
    icon: Optional[str]
    category: Literal['status', 'priority', 'custom']
    is_system: bool = False
    usage_count: int = 0
    created_by: Optional[str]

# 会话-标签关联
class SessionTagRelation(BaseModel):
    session_name: str
    tag_id: str
    added_by: str
    added_at: float

# API接口
@app.get("/api/tags")
async def get_tags():
    """获取所有标签"""
    pass

@app.post("/api/tags")
async def create_tag(request: CreateTagRequest, agent: dict = Depends(require_agent)):
    """创建自定义标签"""
    pass

@app.post("/api/sessions/{session_name}/tags")
async def add_session_tag(session_name: str, tag_id: str):
    """给会话添加标签"""
    pass

@app.delete("/api/sessions/{session_name}/tags/{tag_id}")
async def remove_session_tag(session_name: str, tag_id: str):
    """移除会话标签"""
    pass

@app.get("/api/sessions/by-tag/{tag_id}")
async def get_sessions_by_tag(tag_id: str):
    """按标签筛选会话"""
    pass
```

**验收标准**:
- [ ] 支持6个系统预设标签
- [ ] 支持自定义标签（不限数量）
- [ ] 会话列表显示标签（最多显示3个，更多显示"+2"）
- [ ] 点击标签可筛选
- [ ] 标签颜色自定义
- [ ] 标签使用次数统计
- [ ] 批量打标签（选中多个会话）

**预估工时**: 2天

---

### 任务3: 会话置顶功能 ⭐ P0

**当前状态**:
- ❌ 无置顶功能

**目标**:
允许坐席将重要会话置顶，优先显示

**功能需求**:

#### 3.1 置顶逻辑

```typescript
interface SessionPinned {
  session_name: string
  pinned_by: string
  pinned_at: number
  pin_reason?: string  // 置顶原因（可选）
}
```

#### 3.2 UI设计

**置顶按钮**:
```
会话卡片右上角: [📌] 置顶按钮
已置顶会话: 顶部显示，背景色略深
```

**会话列表排序**:
```
1. 置顶会话（按置顶时间倒序）
2. 未置顶会话（按最后消息时间倒序）
```

#### 3.3 后端实现

```python
@app.post("/api/sessions/{session_name}/pin")
async def pin_session(
    session_name: str,
    reason: Optional[str] = None,
    agent: dict = Depends(require_agent)
):
    """置顶会话"""
    pass

@app.delete("/api/sessions/{session_name}/pin")
async def unpin_session(session_name: str):
    """取消置顶"""
    pass

@app.get("/api/sessions/pinned")
async def get_pinned_sessions():
    """获取所有置顶会话"""
    pass
```

**验收标准**:
- [ ] 点击📌图标置顶/取消置顶
- [ ] 置顶会话在列表顶部显示
- [ ] 置顶会话背景色区分
- [ ] 显示置顶时间和原因
- [ ] 最多置顶10个会话

**预估工时**: 1天

---

### 任务4: 自动回复机制 ⭐ P0

**当前状态**:
- ❌ 无自动回复

**目标**:
实现欢迎语、离线提示、等待提示等自动回复

**功能需求**:

#### 4.1 自动回复类型

```typescript
enum AutoReplyType {
  WELCOME = 'welcome',           // 欢迎语
  OFFLINE = 'offline',           // 离线提示
  BUSY = 'busy',                 // 坐席繁忙
  QUEUE = 'queue',               // 排队等待
  KEYWORD = 'keyword',           // 关键词触发
  TIMEOUT = 'timeout'            // 超时提示
}

interface AutoReplyRule {
  id: string
  type: AutoReplyType
  trigger_condition: object      // 触发条件
  reply_content: string
  enabled: boolean
  delay_seconds?: number         // 延迟发送（秒）
  variables: string[]
}
```

#### 4.2 欢迎语

**触发条件**: 客户首次发送消息

**内容模板**:
```
您好{customer_name}，我是Fiido客服{agent_name}，很高兴为您服务！
请问有什么可以帮助您的吗？

⏰ 工作时间：周一至周五 9:00-18:00 (CET)
📧 邮件：support@fiido.com
📞 电话：+49 XXX XXXXXX
```

#### 4.3 离线提示

**触发条件**: 客户在非工作时间咨询

**内容模板**:
```
您好，当前不在工作时间。

⏰ 我们的工作时间：
   周一至周五 9:00-18:00 (CET)
   周六周日休息

我们会在工作时间尽快回复您，也可以留下您的邮箱或电话，我们会主动联系您。

感谢理解！
```

#### 4.4 等待提示

**触发条件**: 所有坐席繁忙，客户需要排队

**内容模板**:
```
抱歉让您久等了，当前咨询量较大。

您前面还有 {queue_position} 位客户等待
预计等待时间：{estimated_wait_time} 分钟

我们会尽快为您服务，感谢您的耐心等待！
```

#### 4.5 关键词触发

**示例规则**:
```typescript
const KEYWORD_RULES = [
  {
    keywords: ['退款', 'refund', '退货'],
    reply: '关于退款政策，请参考：https://fiido.com/refund-policy\n\n如需申请退款，请提供订单号，我会立即为您处理。'
  },
  {
    keywords: ['物流', 'tracking', '快递'],
    reply: '您可以通过订单号在这里查询物流：https://fiido.com/track\n\n如需帮助，请提供您的订单号。'
  },
  {
    keywords: ['价格', 'price', '多少钱'],
    reply: '您可以在官网查看最新价格：https://fiido.com/products\n\n如有疑问，欢迎随时咨询！'
  }
]
```

#### 4.6 后端实现

```python
# 自动回复规则模型
class AutoReplyRule(BaseModel):
    id: str
    type: AutoReplyType
    trigger_condition: dict
    reply_content: str
    enabled: bool = True
    delay_seconds: int = 0
    variables: List[str] = Field(default_factory=list)

# API接口
@app.get("/api/auto-reply-rules")
async def get_auto_reply_rules(agent: dict = Depends(require_admin)):
    """获取自动回复规则（管理员）"""
    pass

@app.post("/api/auto-reply-rules")
async def create_auto_reply_rule(
    request: CreateAutoReplyRuleRequest,
    agent: dict = Depends(require_admin)
):
    """创建自动回复规则"""
    pass

@app.put("/api/auto-reply-rules/{id}")
async def update_auto_reply_rule(
    id: str,
    request: UpdateAutoReplyRuleRequest,
    agent: dict = Depends(require_admin)
):
    """更新自动回复规则"""
    pass

# 触发自动回复
async def trigger_auto_reply(session_name: str, message: Message):
    """检查并触发自动回复"""
    rules = await get_enabled_auto_reply_rules()

    for rule in rules:
        if should_trigger(rule, session_name, message):
            reply_content = replace_variables(rule.reply_content, session_name)

            if rule.delay_seconds > 0:
                await asyncio.sleep(rule.delay_seconds)

            await send_auto_message(session_name, reply_content)
```

**验收标准**:
- [ ] 欢迎语自动发送（首次咨询）
- [ ] 离线提示自动发送（非工作时间）
- [ ] 等待提示自动发送（排队>3人）
- [ ] 关键词触发（至少支持10个常见关键词）
- [ ] 管理员可配置规则开关
- [ ] 支持变量替换
- [ ] 支持延迟发送

**预估工时**: 3天

---

### 任务5: 智能提醒系统 ⭐ P0

**当前状态**:
- ❌ 无智能提醒

**目标**:
实现未回复提醒、VIP客户提醒、工单超时提醒

**功能需求**:

#### 5.1 未回复提醒

**触发条件**: 客户发送消息后超过30秒未回复

**提醒方式**:
- 会话卡片红色闪烁
- 浏览器通知（需授权）
- 声音提示（可关闭）

**UI效果**:
```css
.session-item.urgent {
  animation: flash 1s infinite;
  border-left: 4px solid #EF4444;
}

@keyframes flash {
  0%, 100% { background: #FEE2E2; }
  50% { background: #FEF2F2; }
}
```

#### 5.2 VIP客户提醒

**触发条件**: VIP客户发起咨询

**提醒方式**:
- 弹窗提醒（优先级最高）
- 特殊音效
- 会话置顶

**UI设计**:
```
┌─────────────────────────────────────┐
│ 🔔 VIP客户咨询                      │
├─────────────────────────────────────┤
│ 客户: John Smith                    │
│ 等级: VIP金卡                       │
│ 消费: €15,680                       │
│ 消息: 我想咨询D4S电池问题...        │
│                                      │
│ [立即接入]              [稍后处理]  │
└─────────────────────────────────────┘
```

#### 5.3 工单超时提醒

**触发条件**: 工单距离SLA截止时间<1小时

**提醒方式**:
- 顶部横幅提醒
- 工单卡片橙色/红色标记
- 邮件提醒（超时前30分钟）

#### 5.4 后端实现

```python
# 提醒服务
class NotificationService:
    async def check_unanswered_sessions(self):
        """检查未回复会话"""
        sessions = await get_all_active_sessions()
        now = time.time()

        for session in sessions:
            if session.last_message_role == 'user':
                time_since_last = now - session.last_message_time
                if time_since_last > 30:
                    await send_notification(
                        agent_id=session.assigned_agent,
                        type='unanswered',
                        session_name=session.session_name,
                        urgency='high' if time_since_last > 60 else 'medium'
                    )

    async def check_vip_sessions(self):
        """检查VIP客户会话"""
        vip_sessions = await get_sessions_by_tag('vip')

        for session in vip_sessions:
            if session.status == 'pending_manual':
                await send_notification(
                    type='vip_customer',
                    session_name=session.session_name,
                    urgency='critical'
                )

    async def check_ticket_sla(self):
        """检查工单SLA"""
        tickets = await get_active_tickets()
        now = time.time()

        for ticket in tickets:
            if ticket.sla_deadline:
                time_left = ticket.sla_deadline - now
                if time_left < 3600 and time_left > 0:  # <1小时
                    await send_notification(
                        agent_id=ticket.assignee_id,
                        type='ticket_sla',
                        ticket_id=ticket.ticket_id,
                        urgency='high'
                    )

# 定时任务
@app.on_event("startup")
async def start_notification_scheduler():
    """启动提醒调度器"""
    scheduler = BackgroundScheduler()

    # 每15秒检查一次未回复会话
    scheduler.add_job(
        notification_service.check_unanswered_sessions,
        'interval',
        seconds=15
    )

    # 每30秒检查一次VIP客户
    scheduler.add_job(
        notification_service.check_vip_sessions,
        'interval',
        seconds=30
    )

    # 每5分钟检查一次工单SLA
    scheduler.add_job(
        notification_service.check_ticket_sla,
        'interval',
        minutes=5
    )

    scheduler.start()
```

**验收标准**:
- [ ] 超过30秒未回复会话红色闪烁
- [ ] VIP客户咨询弹窗提醒
- [ ] 工单SLA<1小时橙色提醒
- [ ] 工单SLA超时红色提醒
- [ ] 支持浏览器通知（需授权）
- [ ] 支持声音提示开关
- [ ] 提醒历史记录

**预估工时**: 2天

---

## 📦 Phase 1 总结

**总预估工时**: 11天
**版本号**: v3.5.0
**发布时间**: 预计2周后

**核心成果**:
- ✅ 快捷回复系统（分类+变量+快捷键）
- ✅ 会话标签系统（系统标签+自定义标签）
- ✅ 会话置顶功能
- ✅ 自动回复机制（欢迎语+离线+关键词）
- ✅ 智能提醒系统（未回复+VIP+SLA）

**对标系统**:
- 拼多多: ✅ 快捷回复、会话标签
- 聚水潭: ✅ 自动回复、智能提醒

---

## 🚀 Phase 2-4 任务清单

由于篇幅限制，Phase 2-4的详细任务拆解将在后续文档中补充：

**Phase 2: 功能完善 (v3.6.0 - 4周)**
- 商品/订单卡片
- 图片/文件发送
- 知识库系统
- 实时数据统计
- 物流追踪集成

**Phase 3: 高级特性 (v3.7.0 - 8周)**
- 多店铺管理
- 绩效报表
- 工单模板
- 消费数据统计
- 会话备注

**Phase 4: 智能化 (v3.8.0 - 12周)**
- 智能路由
- AI推荐
- 行为数据分析
- 营销工具
- 高级报表

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**版本**: v1.0
**状态**: ✅ 待评审
