# 开发进度追踪

> 产品模块：products/agent_workbench
> 开始日期：2025-12-21
> 当前步骤：Step 16 ✅ 已完成

---

## 完成记录

### Step 1: 创建正式前端项目

**完成时间:** 2025-12-21
**版本号:** v7.3.0

**完成内容:**
- 将 `fronted_origin/` 重命名为 `frontend/`
- 更新 `package.json`：
  - name: "fiido-agent-workbench"
  - version: "1.0.0"
  - 移除 @google/genai 依赖
- 修改 `Workspace.tsx`：移除 GoogleGenAI import，改用 Mock 数据
- 修改 `index.html`：从 importmap 移除 @google/genai

**测试结果:**
- ✅ npm install 成功
- ✅ Vite 开发服务器正常启动（端口 3002）
- ✅ 页面显示原型界面

**备注:**
- 端口 5173/3000/3001 被占用，Vite 自动选择 3002
- AI 建议功能暂用 Mock 数据，后续接入真实服务

---

### Step 2: 安装核心依赖

**完成时间:** 2025-12-21
**版本号:** v7.3.1

**完成内容:**
- 安装运行时依赖：axios@1.13.2, zustand@5.0.9, react-router-dom@7.11.0, clsx@2.1.1
- 安装开发依赖：@types/react@19.2.7, tailwindcss@4.1.18, postcss@8.5.6, autoprefixer@10.4.23

**测试结果:**
- ✅ 所有依赖安装成功（无版本冲突）
- ✅ 开发服务器正常运行（端口 5174）

---

### Step 3: Tailwind CSS 本地化

**完成时间:** 2025-12-21
**版本号:** v7.3.2

**完成内容:**
- 创建 `tailwind.config.js`（内容扫描配置）
- 创建 `postcss.config.js`（使用 @tailwindcss/postcss）
- 创建 `index.css`（使用 Tailwind v4 @import 语法 + @theme 定义品牌色）
- 修改 `index.html`：移除 CDN 脚本和内联样式
- 修改 `index.tsx`：添加 CSS 导入
- 安装 `@tailwindcss/postcss` 依赖（Tailwind v4 新架构）

**测试结果:**
- ✅ index.html 无 CDN script 标签
- ✅ Tailwind v4.1.18 正常编译
- ✅ 自定义 fiido 品牌色生效（--color-fiido）
- ✅ 开发服务器正常运行（端口 5175）

**备注:**
- Tailwind v4 使用 CSS-first 配置，通过 @theme 定义颜色变量
- 需使用 @tailwindcss/postcss 而非直接使用 tailwindcss

---

### Step 4: 创建 Axios 客户端

**完成时间:** 2025-12-21
**版本号:** v7.3.3

**完成内容:**
- 创建 `src/api/client.ts`：Axios 实例 + JWT 自动注入 + 401 拦截跳转
- 创建 `src/vite-env.d.ts`：Vite 环境变量类型声明
- 更新 `tsconfig.json`：添加 vite/client 类型 + include 配置

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ apiClient 实例可正常导入

**备注:**
- 使用 localStorage 存储 Token
- 401 响应触发 auth:logout 自定义事件

---

### Step 5: 封装认证 API

**完成时间:** 2025-12-21
**版本号:** v7.3.4

**完成内容:**
- 创建 `src/api/auth.ts`：封装全部认证相关 API
  - login/logout/refreshToken
  - getProfile/updateProfile
  - getStatus/updateStatus
  - changePassword/heartbeat/getTodayStats

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ 类型定义完整（AgentInfo, AgentStatus 等）

**备注:**
- login 自动存储 token 到 localStorage
- logout 自动清除 tokens

---

### Step 6: 封装会话 API

**完成时间:** 2025-12-22
**版本号:** v7.3.5

**完成内容:**
- 创建 `src/api/sessions.ts`：封装全部会话管理 API
  - getList/getStats/getQueue/getSession
  - takeover/release/transfer
  - sendMessage/addNote/createTicket
  - subscribeEvents (SSE 事件流订阅)

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ 类型定义完整（SessionInfo, MessageInfo, QueueItem 等）

**备注:**
- SSE 订阅返回 EventSource 实例，调用方需管理生命周期
- 所有接口与后端 handlers/sessions.py 对应

---

### Step 7: 封装工单和快捷回复 API

**完成时间:** 2025-12-22
**版本号:** v7.3.6

**完成内容:**
- 创建 `src/api/tickets.ts`：封装全部工单管理 API
  - 基础 CRUD：create/createManual/getList/getDetail/update
  - 搜索筛选：search/filter/exportTickets
  - 批量操作：batchAssign/batchClose/batchPriority
  - 评论附件：addComment/getComments/deleteComment/getAttachments/uploadAttachment
  - SLA 管理：getSLADashboard/getSLASummary/getSLAAlerts/getTicketSLA
  - 生命周期：assign/reopen/archive/autoArchive/getArchived/getAuditLogs
- 创建 `src/api/quickReplies.ts`：封装全部快捷回复 API
  - getCategories/getStats/getList
  - create/getDetail/update/remove
  - use（变量替换并计数）
- 创建 `src/api/index.ts`：统一导出所有 API 模块
  - 导出 apiClient、authApi、sessionsApi、ticketsApi、quickRepliesApi
  - 导出所有相关类型定义

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ 所有 API 模块可通过 index.ts 统一导出

**备注:**
- tickets.ts 包含 30+ 个 API 函数，覆盖工单全生命周期
- quickReplies.ts 支持变量替换功能
- 类型定义与后端 handlers 保持一致

---

### Step 8: 创建认证状态 Store

**完成时间:** 2025-12-22
**版本号:** v7.3.7

**完成内容:**
- 创建 `src/stores/authStore.ts`：使用 Zustand 管理认证状态
  - 状态管理：isAuthenticated, isLoading, error, agent, status
  - 认证操作：login, logout, refreshToken
  - 状态操作：setStatus, fetchProfile, fetchStatus, fetchTodayStats
  - 心跳保活：startHeartbeat, stopHeartbeat（30秒间隔）
  - 持久化：使用 zustand/middleware persist 存储关键状态
  - 选择器：selectIsAuthenticated, selectAgent, selectStatus 等
- 监听 auth:logout 事件，自动登出

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ Store 可正常导入

**备注:**
- 使用 zustand persist 中间件持久化 isAuthenticated、agent、status
- 心跳间隔 30 秒，保持坐席在线状态
- 监听 client.ts 发出的 auth:logout 事件

---

### Step 9: 创建会话和工单 Store

**完成时间:** 2025-12-22
**版本号:** v7.3.8

**完成内容:**
- 创建 `src/stores/sessionStore.ts`：会话状态管理
  - 列表操作：fetchSessions, fetchQueue, fetchStats
  - 会话操作：selectSession, takeover, release, transfer
  - 消息操作：sendMessage, addNote
  - SSE 订阅：subscribeToSession, unsubscribeFromSession
  - 选择器：selectSessions, selectQueue, selectCurrentSession 等

- 创建 `src/stores/ticketStore.ts`：工单状态管理
  - 列表操作：fetchTickets, searchTickets, refreshTickets
  - 工单操作：selectTicket, createTicket, updateTicket, assignTicket
  - 批量操作：batchAssign, batchClose, batchPriority
  - 评论操作：fetchComments, addComment
  - SLA：fetchSLADashboard, fetchSLASummary
  - 筛选/视图：setFilters, setViewMode
  - 批量选择：toggleSelect, selectAll, clearSelection

- 创建 `src/stores/index.ts`：统一导出所有 Store

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ 所有 Store 可通过 index.ts 统一导出

**备注:**
- sessionStore 集成 SSE 事件订阅，自动处理消息推送
- ticketStore 支持列表/看板两种视图模式
- 两个 Store 都实现了完整的 CRUD 和批量操作

---

### Step 10: 登录页功能接入

**完成时间:** 2025-12-22
**版本号:** v7.3.9

**完成内容:**
- 修改 `components/LoginView.tsx`：接入 authStore
  - 使用 useAuthStore 获取 login, isLoading, error, clearError
  - 表单提交调用 authStore.login()
  - 显示 isLoading 时的 loading 动画
  - 显示 error 时的红色错误提示框
- 修改 `App.tsx`：接入认证状态
  - 使用 useAuthStore 获取 isAuthenticated, agent, status, logout
  - 未登录时显示 LoginView
  - 构建 currentUser 对象传递给 Topbar

**测试结果:**
- ✅ TypeScript 编译无错误
- ✅ 登录按钮显示 loading 动画
- ✅ 登录失败显示红色错误提示框
- ✅ 发送请求到 /api/agent/login

**备注:**
- 登录成功后 authStore.isAuthenticated 自动变为 true
- App.tsx 会自动切换到工作台界面
- 心跳保活在登录成功后自动启动

---

### Step 11: 会话工作台接入

**完成时间:** 2025-12-22
**版本号:** v7.4.1

**完成内容:**
- 修改 `components/Workspace.tsx`：接入 sessionStore
  - 使用 useSessionStore 获取 sessions, queue, currentSession, currentMessages
  - 实现 handleTakeover, handleRelease, handleSendMessage, handleSelectSession
  - 初始化时加载会话列表和待接入队列
  - 消息列表自动滚动到底部
- 修复 `src/api/sessions.ts` 多个 API 返回格式适配：
  - `takeover`: 传递 agent_id, agent_name 参数，适配 `{ success, data }`
  - `release`: 传递 agent_id 参数
  - `sendMessage`: 适配 `{ success, data: { message } }`
  - `getSession`: 适配 `{ success, data: { session } }`
- 修复 `src/stores/sessionStore.ts`：
  - `takeover` 方法从 authStore 获取坐席信息
  - `release` 方法从 authStore 获取 agent_id
- 修复后端 SSE events 认证：
  - 新增 `dependencies.py` 中 `verify_agent_token_from_query` 函数
  - `sessions.py` events 端点改用 query 参数验证 token

**测试结果:**
- ✅ 待接入队列从 API 加载
- ✅ 点击"接管"按钮成功接管会话
- ✅ 消息发送成功
- ✅ SSE 实时推送正常
- ✅ 点击"结束会话"成功释放

**备注:**
- 后端 API 返回格式统一为 `{ success, data: {...} }`，前端需逐一适配
- SSE EventSource 不支持自定义 headers，需通过 query 参数传递 token

---

### Step 12: 工单中心接入

**完成时间:** 2025-12-22
**版本号:** v7.4.2

**完成内容:**
- 修改 `components/TicketsView.tsx`：接入 ticketStore
  - 工单列表从 API 加载（ticketsApi.filter）
  - 列表/看板视图切换
  - 搜索功能（防抖 300ms）
  - SLA 倒计时计算与显示
- 新建工单弹窗：标题、描述、类型、优先级、客户信息
- 编辑工单弹窗：状态、优先级、受理人
- 修复 `src/api/tickets.ts`：TicketType 枚举与后端一致（pre_sale/after_sale/complaint）
- 修复登录页输入框样式：未聚焦灰色背景，聚焦白色+绿边
- 修复 `index.css`：覆盖浏览器自动填充黄色背景

**测试结果:**
- ✅ 工单列表正确加载
- ✅ 列表/看板视图切换正常
- ✅ 创建新工单成功
- ✅ 编辑工单状态/优先级/受理人成功
- ✅ SLA 倒计时显示正确
- ✅ 搜索功能正常
- ✅ 登录页输入框样式符合设计稿

**备注:**
- 工单类型只支持 pre_sale/after_sale/complaint（后端限制）
- 受理人目前为手动输入，后续可改为下拉选择

---

### Step 13: 快捷回复接入

**完成时间:** 2025-12-24
**版本号:** v7.4.3

**完成内容:**
- 创建 `components/QuickReplyPanel.tsx`：快捷回复弹出面板
  - 分类筛选（全部、问候语、结束语、道歉、物流、退款、产品、技术、自定义）
  - 关键词搜索（300ms 防抖）
  - 点击快捷回复自动插入输入框
  - 变量替换（通过 API `/api/quick-replies/{id}/use`）
  - ESC 键关闭、点击外部关闭
- 修改 `components/Workspace.tsx`：集成快捷回复面板
  - 添加 ⚡ 闪电图标按钮（工具栏）
  - 传递 sessionContext 和 agentContext 用于变量替换
- 创建 `components/QuickReplyManager.tsx`：话术短语库管理页面
  - 话术列表展示（卡片式布局）
  - 新增/编辑/删除话术（带确认弹窗）
  - 分类筛选、关键词搜索
  - 支持快捷键、共享开关
  - 变量提示说明
- 修改 `components/Settings.tsx`：点击"话术短语库"进入管理页面

**测试结果:**
- ✅ Workspace 闪电图标可弹出快捷回复面板
- ✅ 点击快捷回复内容插入输入框
- ✅ 变量替换正常（{agent_name}, {current_time} 等）
- ✅ Settings 点击"话术短语库"进入管理页面
- ✅ 话术 CRUD 功能正常

**备注:**
- 变量使用单花括号 `{变量名}`
- 当前可用变量：{agent_name}, {customer_name}, {current_time}, {current_date}
- {order_id} 等 Shopify 相关变量需 Step 14 集成后可用

---

### Step 14: 客户信息与订单查询

**完成时间:** 2025-12-24
**版本号:** v7.4.4

**完成内容:**
- 创建 `src/api/shopify.ts`：Shopify 订单 API 封装
  - getSites：获取已配置站点列表
  - getOrdersByEmail：按邮箱查询指定站点订单
  - searchOrder：按订单号搜索指定站点订单
  - searchOrderGlobal：跨站点订单号搜索（自动识别站点前缀）
  - searchOrdersByEmailGlobal：跨站点邮箱搜索（遍历所有站点）
  - getOrderDetail：获取订单详情
  - getOrderTracking：获取订单物流信息
  - getTrackingGlobal：跨站点物流查询
  - checkSiteHealth / checkAllSitesHealth：站点健康检查
- 创建 `components/OrderPanel.tsx`：订单面板组件
  - 通过邮箱或订单号查询客户订单（跨站点）
  - 自动检测搜索类型（邮箱 vs 订单号）
  - 订单列表展示（支付状态、物流状态、金额）
  - 订单详情展开（商品明细、收货地址）
  - 物流信息查询与轨迹展示
  - 关联订单到会话功能
- 更新 `src/api/index.ts`：导出 shopifyApi

**测试结果:**
- ✅ 按邮箱查询订单正常（跨站点）
- ✅ 按订单号查询订单正常（自动识别站点）
- ✅ 订单详情展开显示商品、地址
- ✅ 物流信息加载与轨迹展示正常
- ✅ 搜索类型自动切换（@符号检测）

**备注:**
- 使用 normalizeOrder 函数统一处理后端返回的 id/order_id 字段
- 物流轨迹支持中英文双语显示
- 展开订单时自动加载物流信息

---

### Step 15: 侧边栏导航与路由

**完成时间:** 2025-12-24
**版本号:** v7.4.5

**完成内容:**
- 修改 `index.tsx`：添加 BrowserRouter 包裹整个应用
- 修改 `App.tsx`：
  - 用 Routes/Route 替代 switch/case 渲染逻辑
  - 移除 activeTab 状态管理
  - 添加根路径 `/` 重定向到 `/workspace`
  - 添加 `*` 通配符路由显示 ComingSoon 组件
- 修改 `components/Sidebar.tsx`：
  - 用 NavLink 替代 button 实现导航
  - 使用 useNavigate 处理"加油包"跳转
  - 移除 activeTab/onTabChange props
  - NavLink 自动处理 isActive 状态高亮

**路由配置:**
| 路径 | 组件 |
|------|------|
| `/` | → `/workspace` |
| `/workspace` | Workspace |
| `/tickets` | TicketsView |
| `/knowledge` | KnowledgeBase |
| `/monitoring` | Monitoring |
| `/dashboard` | Dashboard |
| `/audit` | QualityAudit |
| `/billing` | BillingView |
| `/settings` | Settings |

**测试结果:**
- ✅ 点击侧边栏菜单页面切换正常
- ✅ 浏览器地址栏 URL 正确变化
- ✅ 刷新页面保持当前路由
- ✅ 根路径自动重定向到 /workspace

---

### Step 16: 效能报表 Dashboard

**完成时间:** 2025-12-24
**版本号:** v7.4.6

**完成内容:**
- 创建 `src/api/stats.ts`：统计数据 API 封装
  - getSessionStats：获取会话统计
  - getAgentTodayStats：获取坐席今日统计
  - getSLADashboard：获取 SLA 仪表盘数据
  - getDashboardStats：并行请求所有统计
- 修改 `components/Dashboard.tsx`：接入真实数据 + Mock
  - 核心指标卡片接入 API（今日会话、响应时长）
  - 添加刷新按钮和 loading 状态
  - 自动刷新（60秒间隔）
  - 更新时间显示真实时间
- 更新 `src/api/index.ts`：导出 statsApi

**数据来源说明:**
| 功能 | 数据来源 | 状态 |
|------|----------|------|
| 今日会话总数 | `/api/agent/stats/today` | ✅ 真实 API |
| 平均响应时长 | `/api/sessions/stats` | ✅ 真实 API |
| 全渠道满意度 | Mock | ⚠️ 待完善 |
| 服务质检评级 | Mock | ⚠️ 待完善 |
| 近7日趋势图 | Mock | ⚠️ 待完善（需后端历史统计 API）|
| 满意度分布 | Mock | ⚠️ 待完善（需后端满意度 API）|
| 导出报告按钮 | 占位 | ⚠️ 待完善 |

**测试结果:**
- ✅ Dashboard 页面正常显示
- ✅ 统计卡片显示数据（真实/Mock）
- ✅ 图表正常渲染
- ✅ 刷新按钮功能正常
- ✅ 无 JS 错误

**待后续完善:**
1. 后端需新增历史统计 API（近7日/30日趋势）
2. 后端需新增满意度详细分布 API
3. 后端需新增质检评级 API
4. 实现导出满意度报告功能

---

## 待完成步骤

| Phase | Step | 标题 | 状态 |
|-------|------|------|------|
| **Phase 1** | Step 1 | 创建正式前端项目 | ✅ 已完成 |
| | Step 2 | 安装核心依赖 | ✅ 已完成 |
| | Step 3 | Tailwind CSS 本地化 | ✅ 已完成 |
| **Phase 2** | Step 4 | 创建 Axios 客户端 | ✅ 已完成 |
| | Step 5 | 封装认证 API | ✅ 已完成 |
| | Step 6 | 封装会话 API | ✅ 已完成 |
| | Step 7 | 封装工单和快捷回复 API | ✅ 已完成 |
| **Phase 3** | Step 8 | 创建认证状态 Store | ✅ 已完成 |
| | Step 9 | 创建会话和工单 Store | ✅ 已完成 |
| **Phase 4** | Step 10 | 登录页功能接入 | ✅ 已完成 |
| | Step 11 | 会话工作台接入 | ✅ 已完成 |
| | Step 12 | 工单中心接入 | ✅ 已完成 |
| **Phase 5** | Step 13 | 快捷回复接入 | ✅ 已完成 |
| | Step 14 | 客户信息与订单查询 | ✅ 已完成 |
| | Step 15 | 侧边栏导航与路由 | ✅ 已完成 |
| **Phase 6** | Step 16 | 效能报表 Dashboard | ✅ 已完成 |
| | Step 17 | 系统设置功能 | ⏳ 待开始 |
| **Phase 7** | Step 18 | 核心功能测试与生产构建 | ⏳ 待开始 |
