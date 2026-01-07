# 开发进度追踪

> 产品模块：products/agent_workbench
> 开始日期：2025-12-21
> 当前步骤：Step 18 ✅ 已完成（前端改造全部完成）

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

### Step 17: 系统设置功能

**完成时间:** 2025-12-24
**版本号:** v7.4.7

**完成内容:**
- 创建 `components/ProfileSettings.tsx`：个人配置页面
  - 头像预览（使用 dicebear 生成默认头像）
  - 头像 URL 输入（留空使用默认）
  - 显示名称修改
  - 用户名、角色只读显示
  - 表单提交调用 authApi.updateProfile
  - 成功后自动刷新用户信息
- 创建 `components/PasswordSettings.tsx`：密码修改页面
  - 当前密码输入
  - 新密码输入（带密码强度指示器）
  - 确认新密码输入（实时校验一致性）
  - 密码显示/隐藏切换
  - 安全建议提示卡片
  - 表单提交调用 authApi.changePassword
- 修改 `components/Settings.tsx`：集成子页面
  - 添加 clickable 属性控制卡片可点击状态
  - 个人配置 → ProfileSettings
  - 账号与合规 → PasswordSettings
  - 话术短语库 → QuickReplyManager
  - 其他功能卡片暂不可用（opacity-60 样式）

**功能说明:**
| 设置项 | 可用状态 | 说明 |
|--------|----------|------|
| 个人配置 | ✅ 可用 | 修改头像、显示名称 |
| 账号与合规 | ✅ 可用 | 修改密码 |
| 话术短语库 | ✅ 可用 | 管理快捷回复模版 |
| 通知与提醒 | ⚠️ 待开发 | 需后端支持 |
| 语言与时区 | ⚠️ 待开发 | 需后端支持 |
| 外部集成 | ⚠️ 待开发 | 需后端支持 |

**测试结果:**
- ✅ 个人配置页面正常显示
- ✅ 修改显示名称成功
- ✅ 密码修改页面正常显示
- ✅ 密码强度指示器正常工作
- ✅ 密码一致性校验正常
- ✅ 返回按钮功能正常

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
| | Step 17 | 系统设置功能 | ✅ 已完成 |
| **Phase 7** | Step 18 | 核心功能测试与生产构建 | ✅ 已完成 |

---

### Step 18: 核心功能测试与生产构建

**完成时间:** 2025-12-24
**版本号:** v7.4.8

**完成内容:**
- 清理 `index.html`：移除无用的 importmap CDN 依赖
- 验证生产环境配置：`.env.production` 已配置 `VITE_API_BASE_URL=/workbench-api`
- 执行生产构建：`npm run build` 成功
- 验证构建产物：`npm run preview` 返回 200

**构建产物:**
```
dist/
├── index.html           (0.67 KB, gzip: 0.47 KB)
├── assets/
│   ├── index-*.css      (57.40 KB, gzip: 9.80 KB)
│   └── index-*.js       (777.32 KB, gzip: 231.74 KB)
```

**后续优化建议:**
- JS 包大小 777KB 超过 500KB 警告阈值
- 建议实施代码分割（动态 import）
- 可使用 manualChunks 拆分第三方库

**测试结果:**
- ✅ 构建成功无错误
- ✅ 预览服务器正常启动
- ✅ 页面可正常访问

---

## 🎉 前端改造完成总结

**总耗时:** 2025-12-21 ~ 2025-12-24（4 天）
**最终版本:** v7.4.8

### 已完成功能

| 功能模块 | 状态 | 说明 |
|----------|------|------|
| 登录/登出 | ✅ | JWT 认证，自动刷新 |
| 会话工作台 | ✅ | SSE 实时消息，接管/释放 |
| 工单中心 | ✅ | CRUD、SLA、列表/看板视图 |
| 快捷回复 | ✅ | 话术管理、变量替换 |
| 订单查询 | ✅ | 跨站点查询、物流轨迹 |
| 效能报表 | ✅ | 部分真实 API + Mock |
| 系统设置 | ✅ | 个人配置、密码修改 |
| 路由导航 | ✅ | react-router-dom |

### 待后续迭代

| 功能 | 说明 |
|------|------|
| 登录安全增强 | 失败次数限制、账号锁定、审计日志 |
| Dashboard 完善 | 历史趋势 API、满意度 API、导出功能 |
| 设置页面完善 | 通知提醒、语言时区、外部集成 |
| 性能优化 | 代码分割、懒加载 |

### 部署说明

```bash
# 1. 构建
cd products/agent_workbench/frontend
npm run build

# 2. 部署到服务器
rsync -avz dist/ root@8.211.27.199:/var/www/fiido-workbench/

# 3. 访问地址
https://ai.fiido.com/workbench/
```

---

## Cross-module: chat-history-storage - Step 6

**完成时间:** 2026-01-07
**所属模块:** products/agent_workbench

**完成内容:**
- 在 `products/agent_workbench/dependencies.py` 增加 MessageStoreService 注入与获取（`set_message_store()` / `get_message_store()`）
- 在 `products/agent_workbench/lifespan.py` 启动/关闭 `MessageStoreService`
- 在 `products/agent_workbench/handlers/sessions.py` 的 `agent_send_message` 写入点 best-effort enqueue 保存 `role=agent` 消息（包含 agent_id/agent_name）

**涉及文件:**
- `products/agent_workbench/dependencies.py`
- `products/agent_workbench/lifespan.py`
- `products/agent_workbench/handlers/sessions.py`

**测试结果:**
- ✅ 单元级自测通过（mock session_store + message_store + SSE enqueue），验证 enqueue 被调用且字段完整（`STEP6_AGENT_PERSIST_OK`）

---

## Cross-module: chat-history-storage - Step 7

**完成时间:** 2026-01-07
**所属模块:** products/agent_workbench

**完成内容:**
- 新增聊天记录历史 API（受 JWT 坐席认证保护）：
  - `GET /api/history/sessions`
  - `GET /api/history/sessions/{session_name}`
  - `GET /api/history/search`（q 参数，FTS）
  - `GET /api/history/statistics`
  - `GET /api/history/export`（CSV）
- 路由注册到 workbench 主 router

**涉及文件:**
- `products/agent_workbench/handlers/history.py`（新增）
- `products/agent_workbench/routes.py`（修改，注册 history router）

**测试结果:**
- ✅ 单元级自测通过（mock MessageStoreService），验证各端点可调用并返回预期结构（`STEP7_HISTORY_API_OK`）

---

## Cross-module: chat-history-storage - Step 8

**完成时间:** 2026-01-07  
**所属模块:** `products/agent_workbench/frontend`

**完成内容:**
- 新增聊天记录页面（会话列表/详情/搜索/导出 CSV），按 `session_name` 聚合会话列表。
- 新增前端 API 封装 `historyApi` 对接 `/api/history/*`。
- 在 Sidebar 增加菜单项，并在 `App.tsx` 注册 `/history` 路由。

**涉及文件:**
- `products/agent_workbench/frontend/src/api/history.ts`（新增）
- `products/agent_workbench/frontend/src/api/index.ts`（修改，导出 historyApi）
- `products/agent_workbench/frontend/components/ChatHistoryView.tsx`（新增）
- `products/agent_workbench/frontend/components/Sidebar.tsx`（修改，新增入口）
- `products/agent_workbench/frontend/App.tsx`（修改，新增路由）

**测试结果:**
- ✅ `npm -C products/agent_workbench/frontend run build`

---

## Cross-module: chat-history-storage - Step 9（History UI 业务友好性优化）

**完成时间:** 2026-01-07  
**所属模块:** `products/agent_workbench/frontend`

**完成内容:**
- 批量导出入口调整：将“批量导出”从会话详情区按钮组迁移到左侧时间筛选工具条，更符合运营/质检“先选时间范围再导出”的使用路径。
- 批量导出交互升级：改为“批量导出中心”弹窗（异步任务列表 + 下载），降低主界面拥挤度并提升高频导出可用性。
- 翻译 UI 体验优化：开启翻译后，消息卡片不再出现横向溢出/宽度抖动（增加 overflow-x 保护 + flex wrap 布局）。

**涉及文件:**
- `products/agent_workbench/frontend/components/ChatHistoryView.tsx`

**测试结果:**
- ✅ `npm -C products/agent_workbench/frontend run build`

---

## Cross-module: chat-history-storage - Step 10（History UI 交互修复）

**完成时间:** 2026-01-07  
**所属模块:** `products/agent_workbench/frontend` + `products/agent_workbench`

**完成内容:**
- 翻译开关导致“消息卡片宽度抖动”：将右侧消息列表滚动容器改为固定滚动条占位（避免滚动条出现/消失导致布局宽度变化）。
- 搜索区布局：将“搜索框 + 范围 + 角色 + 搜索按钮”改为同一行对齐（按钮不再换行）。
- 404 排查结论：`会话备注(meta)` 与 `批量导出(export-jobs)` 的 404 来自后端仍在运行旧版本；更新代码后需重启 workbench 后端进程使路由生效（验证现已返回 403/401 而非 404）。

**涉及文件:**
- `products/agent_workbench/frontend/components/ChatHistoryView.tsx`

**测试结果:**
- ✅ `npm -C products/agent_workbench/frontend run build`
