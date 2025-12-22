# 坐席工作台 - 实现计划

> 产品模块：products/agent_workbench
> 创建日期：2025-12-21
> 预计步骤数：18
> 核心功能步骤：Step 1-12
> 扩展功能步骤：Step 13-18

---

## 开发顺序说明

遵循 `CLAUDE.md` 自底向上原则：

```
前端工程化 → API 服务层 → 状态管理 → 核心页面 → 扩展功能 → 测试部署
```

**关键前提**：
- 后端 API 已完整实现（handlers/*.py）
- 前端原型已存在（fronted_origin/）
- 本计划聚焦前端改造和 API 接入

---

## Phase 1: 前端工程化（Step 1-3）

---

## Step 1: 创建正式前端项目

**任务描述：**
将 `fronted_origin/` 重命名为 `frontend/`，更新 package.json 添加生产环境必需依赖。

**涉及文件：**
- `fronted_origin/` → `frontend/`（重命名）
- `frontend/package.json`（修改）

**测试方法：**
```bash
cd products/agent_workbench/frontend
npm install
npm run dev
# 浏览器访问 http://localhost:5173
```

**预期结果：**
- 目录已重命名为 frontend/
- npm install 成功
- Vite 开发服务器正常启动
- 页面显示原型界面

---

## Step 2: 安装核心依赖

**任务描述：**
安装 axios、zustand、react-router-dom、clsx 等核心依赖。

**涉及文件：**
- `frontend/package.json`（修改）

**测试方法：**
```bash
cd products/agent_workbench/frontend
npm install axios zustand react-router-dom clsx
npm install -D @types/react tailwindcss postcss autoprefixer
npm run dev
```

**预期结果：**
- 所有依赖安装成功
- 无版本冲突
- 开发服务器正常运行

---

## Step 3: Tailwind CSS 本地化

**任务描述：**
将 CDN 引入的 Tailwind 改为本地构建，移除 index.html 中的 CDN 脚本。

**涉及文件：**
- `frontend/tailwind.config.js`（新增）
- `frontend/postcss.config.js`（新增）
- `frontend/src/index.css`（新增）
- `frontend/index.html`（修改，移除 CDN）
- `frontend/src/main.tsx`（修改，引入 index.css）

**测试方法：**
```bash
npm run dev
# 检查页面样式是否正常
# 检查 bg-fiido、text-fiido-dark 等自定义类是否生效
```

**预期结果：**
- index.html 中无 CDN script 标签
- Tailwind 样式正常编译
- 自定义 fiido 品牌色生效
- 页面视觉与原型一致

---

## Phase 2: API 服务层（Step 4-7）

---

## Step 4: 创建 Axios 客户端

**任务描述：**
创建 Axios 实例，配置 baseURL、JWT 自动注入、401 拦截跳转。

**涉及文件：**
- `frontend/src/api/client.ts`（新增）

**测试方法：**
```bash
npm run dev
# 在浏览器控制台验证：
# import { apiClient } from './api/client'
# apiClient.get('/api/health')
```

**预期结果：**
- Axios 实例创建成功
- 请求自动携带 Authorization header（如有 token）
- 401 响应触发登录跳转逻辑

---

## Step 5: 封装认证 API

**任务描述：**
封装登录、登出、刷新 Token、获取/更新坐席信息等接口。

**涉及文件：**
- `frontend/src/api/auth.ts`（新增）

**测试方法：**
```bash
# 启动后端
uvicorn backend:app --reload --port 8000

# 启动前端
npm run dev

# 浏览器控制台测试
# import { authApi } from './api/auth'
# authApi.login({ username: 'test', password: 'test' })
```

**预期结果：**
- login/logout/refresh/getProfile 函数可调用
- 接口请求发送成功
- 返回数据结构正确

---

## Step 6: 封装会话 API

**任务描述：**
封装会话列表、队列、接管、转接、释放、消息发送等接口。

**涉及文件：**
- `frontend/src/api/sessions.ts`（新增）

**测试方法：**
```bash
# 浏览器控制台测试
# import { sessionsApi } from './api/sessions'
# sessionsApi.getQueue()
# sessionsApi.getList()
```

**预期结果：**
- 所有会话相关接口函数可调用
- GET/POST 请求正常发送

---

## Step 7: 封装工单和快捷回复 API

**任务描述：**
封装工单 CRUD、SLA 仪表盘、快捷回复管理等接口。

**涉及文件：**
- `frontend/src/api/tickets.ts`（新增）
- `frontend/src/api/quickReplies.ts`（新增）
- `frontend/src/api/index.ts`（新增，统一导出）

**测试方法：**
```bash
# 浏览器控制台测试
# import { ticketsApi, quickRepliesApi } from './api'
# ticketsApi.getList()
# quickRepliesApi.getList()
```

**预期结果：**
- 所有 API 模块可通过 index.ts 统一导出
- 接口调用正常

---

## Phase 3: 状态管理（Step 8-9）

---

## Step 8: 创建认证状态 Store

**任务描述：**
使用 Zustand 创建 authStore，管理登录状态、Token、坐席信息。

**涉及文件：**
- `frontend/src/stores/authStore.ts`（新增）

**测试方法：**
```bash
npm run dev
# 浏览器控制台测试
# import { useAuthStore } from './stores/authStore'
# useAuthStore.getState().login({ username: 'test', password: 'test' })
```

**预期结果：**
- authStore 创建成功
- login/logout 方法可调用
- Token 存储到 localStorage
- isAuthenticated 状态正确

---

## Step 9: 创建会话和工单 Store

**任务描述：**
创建 sessionStore 和 ticketStore，管理列表数据和当前选中项。

**涉及文件：**
- `frontend/src/stores/sessionStore.ts`（新增）
- `frontend/src/stores/ticketStore.ts`（新增）
- `frontend/src/stores/index.ts`（新增，统一导出）

**测试方法：**
```bash
npm run dev
# 验证 store 可正常导入
# 验证 fetchSessions/fetchTickets 可调用
```

**预期结果：**
- 两个 store 创建成功
- 列表加载方法可调用
- 状态变更触发组件更新

---

## Phase 4: 核心页面接入（Step 10-12）

---

## Step 10: 登录页功能接入

**任务描述：**
将 LoginView 组件接入真实登录 API，实现完整登录流程。

**涉及文件：**
- `frontend/src/components/LoginView.tsx`（修改）
- `frontend/src/App.tsx`（修改，添加路由守卫）

**测试方法：**
```bash
# 1. 访问 http://localhost:5173
# 2. 使用测试账号登录
# 3. 验证登录成功跳转
# 4. 刷新页面验证登录状态保持
```

**预期结果：**
- 正确账号可登录成功
- 错误账号显示错误提示
- Token 存储到 localStorage
- 登录后跳转到工作台
- 未登录访问工作台自动跳转登录页

---

## Step 11: 会话工作台接入

**任务描述：**
接入会话列表、队列、接管、消息收发功能，实现 SSE 实时推送。

**涉及文件：**
- `frontend/src/components/Workspace.tsx`（修改）
- `frontend/src/hooks/useSSE.ts`（新增）

**测试方法：**
```bash
# 1. 登录后进入工作台
# 2. 查看待接入队列
# 3. 接管一个会话
# 4. 发送消息
# 5. 验证消息实时显示
```

**预期结果：**
- 会话队列从 API 加载
- 可接管会话
- 消息发送成功
- SSE 推送正常接收

---

## Step 12: 工单中心接入

**任务描述：**
接入工单列表、创建、编辑、SLA 管理功能。

**涉及文件：**
- `frontend/src/components/TicketsView.tsx`（修改）

**测试方法：**
```bash
# 1. 进入工单中心
# 2. 查看工单列表
# 3. 创建新工单
# 4. 编辑工单状态
# 5. 验证 SLA 倒计时
```

**预期结果：**
- 工单列表正确加载
- 列表/看板视图切换正常
- 工单 CRUD 功能完整
- SLA 倒计时显示正确

---

## Phase 5: 辅助功能（Step 13-15）

---

## Step 13: 快捷回复接入

**任务描述：**
接入快捷回复列表、创建、编辑、删除功能。

**涉及文件：**
- `frontend/src/components/Workspace.tsx`（修改，右侧面板）

**测试方法：**
```bash
# 1. 在对话中点击快捷回复
# 2. 验证可插入到输入框
# 3. 创建/编辑/删除快捷回复
```

**预期结果：**
- 快捷回复列表加载
- 可插入到对话输入框
- CRUD 功能正常

---

## Step 14: 客户信息与订单查询

**任务描述：**
接入客户档案显示、Shopify 订单查询功能。

**涉及文件：**
- `frontend/src/api/shopify.ts`（新增）
- `frontend/src/components/Workspace.tsx`（修改）

**测试方法：**
```bash
# 1. 选中一个会话
# 2. 查看客户信息面板
# 3. 查询客户订单
```

**预期结果：**
- 客户标签显示正确
- 订单信息加载成功
- 订单详情可展开

---

## Step 15: 侧边栏导航与路由

**任务描述：**
实现 react-router-dom 路由，侧边栏导航切换页面。

**涉及文件：**
- `frontend/src/App.tsx`（修改）
- `frontend/src/components/Sidebar.tsx`（修改）

**测试方法：**
```bash
# 1. 点击侧边栏各菜单
# 2. 验证页面切换
# 3. 验证 URL 变化
# 4. 刷新后页面保持
```

**预期结果：**
- 路由切换正常
- 浏览器地址栏 URL 正确
- 刷新页面保持当前路由

---

## Phase 6: 扩展功能（Step 16-17）

---

## Step 16: 效能报表 Dashboard

**任务描述：**
接入统计数据 API，实现图表展示（可用 Mock 数据）。

**涉及文件：**
- `frontend/src/components/Dashboard.tsx`（修改）
- `frontend/src/api/stats.ts`（新增，可选）

**测试方法：**
```bash
# 1. 进入 Dashboard 页面
# 2. 查看各统计卡片
# 3. 查看图表渲染
```

**预期结果：**
- 统计数据显示（真实或 Mock）
- 图表正确渲染
- 无 JS 错误

---

## Step 17: 系统设置功能

**任务描述：**
接入个人配置修改、密码修改功能。

**涉及文件：**
- `frontend/src/components/Settings.tsx`（修改）

**测试方法：**
```bash
# 1. 进入设置页面
# 2. 修改个人信息
# 3. 修改密码
```

**预期结果：**
- 配置信息加载
- 修改保存成功
- 密码修改流程正常

---

## Phase 7: 测试与部署（Step 18）

---

## Step 18: 核心功能测试与生产构建

**任务描述：**
完整流程测试，修复问题，配置生产构建。

**涉及文件：**
- `frontend/vite.config.ts`（修改）
- `frontend/.env.production`（新增）

**测试方法：**
```bash
# 完整流程测试：
# 1. 登录 → 2. 查看队列 → 3. 接管会话 → 4. 发消息
# → 5. 创建工单 → 6. 结束会话 → 7. 登出

# 生产构建测试：
npm run build
npm run preview
```

**预期结果：**
- 核心流程无阻塞性 Bug
- 构建成功无错误
- 构建产物可正常运行
- 首屏加载 < 2s

---

## 依赖关系图

```
Step 1 (项目重命名)
    ↓
Step 2 (安装依赖)
    ↓
Step 3 (Tailwind 本地化)
    ↓
Step 4 (Axios 客户端) ←── API 基础
    ↓
Step 5-7 (API 封装) ←── 并行可选
    ↓
Step 8-9 (Zustand Stores) ←── 依赖 API
    ↓
Step 10 (登录页) ←── 核心入口
    ↓
Step 11 (会话工作台) ←── 核心功能
    ↓
Step 12 (工单中心) ←── 核心功能
    ↓
Step 13-15 (辅助功能) ←── 可并行
    ↓
Step 16-17 (扩展功能) ←── 可并行
    ↓
Step 18 (测试部署) ←── 最终验收
```

---

## 开发过程中可能需要的信息

| 信息类型 | 说明 | 获取方式 |
|----------|------|----------|
| 后端 API 地址 | 开发环境 URL | 询问用户或检查 .env |
| 测试账号 | 登录测试用 | 询问用户或后端创建 |
| Shopify API | 订单查询配置 | 检查 .env 已有配置 |
