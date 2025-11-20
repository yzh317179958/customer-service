# Fiido 智能客服系统

基于 Coze 对话流的智能客服系统，支持 OAuth+JWT 鉴权、完美的会话隔离和 Vue 3 前端。

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green.svg)](https://fastapi.tiangolo.com)
[![Vue](https://img.shields.io/badge/Vue-3.5-brightgreen.svg)](https://vuejs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-blue.svg)](https://www.typescriptlang.org)
[![Coze](https://img.shields.io/badge/Coze-Workflow-orange.svg)](https://www.coze.com)

---

## 🎯 重要文档（必读）

### 会话隔离解决方案

⚠️ **如果您在实现多用户会话隔离时遇到问题，必读此文档：**

📖 **[Coze会话隔离最终解决方案.md](./Coze会话隔离最终解决方案.md)** （亲测有效）

**核心要点**：
- ✅ 必须在用户打开页面时立即调用 `conversations.create()` API
- ❌ 不能依赖首次对话时 Coze 自动生成 conversation_id
- ✅ 这是基于 Coze 开发的正确实践，已实际验证通过

**问题示例**：
```
窗口 1: "我是子豪"
窗口 2: "我是谁？"
AI 回答: "你是子豪" ← 这是错误的！应该不知道
```

**解决方案见**: [完整文档](./Coze会话隔离最终解决方案.md)

---

## ✨ 特性

### 后端特性
- ✅ **OAuth+JWT 鉴权** - 安全的访问密钥管理
- ✅ **会话隔离** - 基于 `session_name` 的多用户会话隔离
- ✅ **对话历史管理** - 基于 `conversation_id` 的历史保留
- ✅ **流式/同步双接口** - 支持实时响应和批量响应
- ✅ **Token 自动管理** - 按会话缓存和刷新 JWT Token
- ✅ **Chat SDK 支持** - 提供前端 SDK token 生成接口

### 前端特性
- ✅ **Vue 3 框架版本** - 现代化的前端架构
- ✅ **Fiido 官网设计** - 完全复刻 fiido.com 界面风格
- ✅ **流式响应** - 逐字显示AI回复
- ✅ **Markdown 渲染** - 支持富文本消息
- ✅ **气泡菜单** - 优雅的浮动操作菜单
- ✅ **对话/会话管理** - 清除对话、新建会话功能
- ✅ **历史分隔线** - 清晰区分对话历史
- ✅ **产品咨询** - 快捷产品咨询入口
- ✅ **响应式设计** - 支持移动端和PC端
- ✅ **局域网访问** - 支持同一网络下多设备访问

---

## 🚀 快速开始

### 后端启动

#### 1. 环境要求

- Python 3.10+
- pip 或 pip3

#### 2. 安装依赖

```bash
pip3 install -r requirements.txt
```

#### 3. 配置环境变量

创建 `.env` 文件:

```bash
# Coze API 配置
COZE_API_BASE=https://api.coze.com
COZE_AUTH_MODE=OAUTH_JWT
COZE_WORKFLOW_ID=你的工作流ID
COZE_APP_ID=你的应用ID

# OAuth 配置
COZE_OAUTH_CLIENT_ID=你的ClientID
COZE_OAUTH_PUBLIC_KEY_ID=你的公钥指纹
COZE_OAUTH_PRIVATE_KEY_FILE=./private_key.pem

# 服务器配置
HOST=0.0.0.0
PORT=8000
```

详细配置说明见 [配置指南](docs/配置指南.md)

#### 4. 启动服务

```bash
python3 backend.py
```

服务将在 `http://localhost:8000` 启动

---

### 前端启动

本项目使用 **Vue 3 + TypeScript** 现代化前端框架。

#### 环境要求
- Node.js 16+
- npm 或 yarn

#### 启动方式

**方式 A: 手动启动**
```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

**方式 B: 使用启动脚本**
```bash
./启动-Vue前端.sh
# 访问 http://localhost:5173
```

**局域网访问**:
```
http://<你的IP>:5173
```

#### 前端特性
- ✅ Vue 3 + TypeScript + Pinia
- ✅ 组件化架构，易于维护
- ✅ 完全复刻 Fiido.com 设计
- ✅ 热重载开发体验
- ✅ 类型安全
- ✅ 支持局域网访问

---

## 📁 项目结构

```
fiido-customer-service/
├── README.md                       # 项目说明
├── requirements.txt                # Python 依赖
├── .env                            # 环境变量配置
├── private_key.pem                 # OAuth 私钥
│
├── backend.py                      # FastAPI 后端主程序
├── fiido2.png                      # 客服头像
├── 启动-Vue前端.sh                  # Vue 启动脚本
│
├── frontend/                       # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                 # 应用入口
│   │   ├── App.vue                 # 根组件
│   │   ├── components/             # Vue 组件 (8个)
│   │   │   ├── AppHeader.vue       # 导航栏
│   │   │   ├── HeroSection.vue     # Hero区域
│   │   │   ├── ProductsSection.vue # 产品展示
│   │   │   ├── AppFooter.vue       # 页脚
│   │   │   ├── ChatFloatButton.vue # 浮动按钮
│   │   │   ├── ChatPanel.vue       # 聊天面板
│   │   │   ├── ChatMessage.vue     # 消息组件
│   │   │   └── WelcomeScreen.vue   # 欢迎屏幕
│   │   ├── stores/
│   │   │   └── chatStore.ts        # Pinia 状态管理
│   │   ├── api/
│   │   │   └── chat.ts             # API 接口
│   │   ├── types/
│   │   │   └── index.ts            # TypeScript 类型
│   │   └── assets/
│   │       └── main.css            # 全局样式
│   ├── public/
│   │   └── fiido2.png              # 客服头像
│   ├── index.html                  # HTML 入口
│   ├── vite.config.ts              # Vite 配置
│   ├── package.json                # 依赖配置
│   └── .env                        # 环境变量
│
├── src/                            # 后端源代码
│   ├── __init__.py
│   ├── jwt_signer.py               # JWT 签名工具
│   └── oauth_token_manager.py      # OAuth Token 管理器
│
├── tests/                          # 测试脚本
│   ├── test_simple.py              # 简单会话隔离测试
│   └── test_session_name.py        # 完整会话隔离测试
│
├── docs/                           # 文档
│   ├── 配置指南.md                  # 配置说明
│   └── 会话隔离实现历程.md          # 实现过程记录
│
├── prd/                            # 需求文档
│   └── coze.md                     # Coze 集成需求文档
│
├── Coze会话隔离最终解决方案.md       # 会话隔离完整方案（亲测有效）
├── 文档清单.md                      # 文档索引
└── 文档整理完成总结.md              # 文档整理总结
```

---

## 🔌 API 接口

### 1. 聊天接口 (同步)

**请求**:
```bash
POST /api/chat
Content-Type: application/json

{
  "message": "你好",
  "user_id": "session_abc123",  # 可选,不提供则自动生成
  "conversation_id": "conv_123"  # 可选,用于保留历史
}
```

**响应**:
```json
{
  "success": true,
  "message": "您好！有什么可以帮助您的？"
}
```

### 2. 聊天接口 (流式)

**请求**:
```bash
POST /api/chat/stream
Content-Type: application/json

{
  "message": "你好",
  "user_id": "session_abc123",
  "conversation_id": "conv_123"  # 可选
}
```

**响应** (Server-Sent Events):
```
data: {"type": "message", "content": "您"}
data: {"type": "message", "content": "好"}
data: {"type": "message", "content": "！"}
data: {"type": "done", "content": ""}
```

### 3. 创建新对话

**请求**:
```bash
POST /api/conversation/new
Content-Type: application/json

{
  "user_id": "session_abc123"
}
```

**响应**:
```json
{
  "success": true,
  "conversation_id": "conv_7433558367123783713"
}
```

### 4. 生成 Chat SDK Token ⭐ 新增

**请求**:
```bash
POST /api/chat/token
Content-Type: application/json

{
  "user_id": "session_abc123"
}
```

**响应**:
```json
{
  "success": true,
  "token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600
}
```

### 5. 获取 Bot 信息 ⭐ 新增

**请求**:
```bash
GET /api/bot/info
```

**响应**:
```json
{
  "success": true,
  "bot": {
    "name": "Fiido 客服",
    "description": "Fiido 智能客服助手",
    "icon_url": "https://..."
  }
}
```

### 6. 健康检查

```bash
GET /api/health
```

---

## 会话隔离机制

本系统实现了基于 `session_name` 的多用户会话隔离:

### 工作原理

```
前端访问 → 生成 session_id
    ↓
后端接收 user_id (session_id)
    ↓
┌─────────────────────────────┐
│ 1. JWT 签署时添加           │
│    jwt_payload["session_name"] = user_id
│                             │
│ 2. API 请求时添加           │
│    api_payload["session_name"] = user_id
└─────────────────────────────┘
    ↓
扣子平台根据 session_name 隔离会话
```

### 关键实现

**JWT 签署** (`src/jwt_signer.py:117-118`):
```python
if session_name:
    payload["session_name"] = session_name
```

**API 请求** (`backend.py:324`):
```python
payload = {
    "workflow_id": WORKFLOW_ID,
    "app_id": APP_ID,
    "session_name": session_id,  # ← 关键字段
    "parameters": {"USER_INPUT": message}
}
```

详细实现过程见 [会话隔离实现历程](docs/会话隔离实现历程.md)

---

## 测试

### 简单测试 (推荐)

```bash
python3 tests/test_simple.py
```

**测试内容**:
- 用户 A: "我叫张三"
- 用户 B: "我叫李四"
- 用户 A 第二轮: "我叫什么?" → 期望回答 "张三"

### 完整测试

```bash
python3 tests/test_session_name.py
```

---

## 常见问题

### Q: 会话隔离不生效怎么办?

**A**: 检查以下几点:
1. 确认 `backend.py:324` 添加了 `"session_name": session_id`
2. 确认流式接口 `backend.py:449` 也添加了 session_name
3. 运行测试验证: `python3 tests/test_simple.py`

### Q: 提示 "COZE_WORKFLOW_ID 环境变量未设置"?

**A**:
1. 确认 `.env` 文件存在
2. 检查文件内容是否正确
3. 重启后端服务

更多问题见 [配置指南](docs/配置指南.md#常见问题)

---

## 技术栈

- **后端框架**: FastAPI
- **HTTP 客户端**: httpx
- **JWT 处理**: PyJWT
- **AI 平台**: Coze Workflow
- **鉴权方式**: OAuth 2.0 + JWT

---

## 📚 文档

- [CHANGELOG.md](CHANGELOG.md) - 详细更新日志 ⭐ 新增
- [完整总结.md](完整总结.md) - 三个前端版本完整对比 ⭐ 新增
- [使用说明-最终版.md](使用说明-最终版.md) - index2.html 使用指南 ⭐ 新增
- [frontend/README_CN.md](frontend/README_CN.md) - Vue 3 版本文档 ⭐ 新增
- [配置指南](docs/配置指南.md) - 环境配置和 Coze 平台设置
- [会话隔离实现历程](docs/会话隔离实现历程.md) - 从问题到解决的完整过程

---

## 🧪 测试

### 健康检查
```bash
curl http://localhost:8000/api/health
```

### 简单测试 (推荐)

```bash
python3 tests/test_simple.py
```

**测试内容**:
- 用户 A: "我叫张三"
- 用户 B: "我叫李四"
- 用户 A 第二轮: "我叫什么?" → 期望回答 "张三"

### 完整会话隔离测试 ⭐ 已修复

```bash
python3 tests/test_session_name.py
```

**测试步骤** (遵循正确的会话隔离实现):
1. 用户A打开页面 → 立即调用 `/api/conversation/new` 创建 conversation_A
2. 用户B打开页面 → 立即调用 `/api/conversation/new` 创建 conversation_B
3. 验证 conversation_A ≠ conversation_B
4. 用户A说 "我叫张三，我今年25岁"
5. 用户B说 "我叫李四，我是一名程序员"
6. 用户A问 "我叫什么？我多大了？" → 期望回答 "张三、25岁"
7. 用户B问 "我的名字和职业是什么？" → 期望回答 "李四、程序员"
8. **关键验证**: 用户A问 "你知道李四是谁吗？" → 期望**不知道**（证明会话隔离成功）

**注意**: 此测试脚本已修复，严格遵循《Coze会话隔离最终解决方案.md》的实现方式

---
## 📊 版本历史

### v2.2.2 (2025-11-20) - 修复测试脚本，验证会话隔离

**测试修复**:
- ✅ **修复 test_session_name.py** - 严格遵循《Coze会话隔离最终解决方案.md》实现
- ✅ **预先创建 conversation** - 用户打开页面时立即调用 `/api/conversation/new`
- ✅ **验证通过** - Conversation ID 不同，用户A/B上下文完全隔离
- ✅ **删除错误测试** - 移除依赖自动生成 conversation_id 的旧版本

**测试结果**:
```
Session A → Conversation: 7574681165306363909
Session B → Conversation: 7574686112397737989
✅ 用户A正确记住"张三、25岁"
✅ 用户B正确记住"李四、程序员"
✅ 用户A不知道用户B的信息（会话完全隔离）
```

**修改文件**:
- `tests/test_session_name.py` - 重写为正确的会话隔离测试

### v2.2.1 (2025-11-20) - 修复UI菜单交互问题

**Bug修复**:
- ✅ **修复气泡菜单交互** - 点击后菜单不会立即关闭
- ✅ **添加事件冒泡阻止** - 使用 `@click.stop` 防止意外关闭
- ✅ **改善用户体验** - 鼠标在菜单区域移动时保持显示

**修改文件**:
- `frontend/src/components/ChatPanel.vue` - 添加点击事件拦截

### v2.2.0 (2025-11-20) - 彻底解决会话隔离，优化UI界面 ⭐

**会话隔离重大突破**:
- ✅ **彻底解决会话隔离问题** - 用户打开页面时立即调用 `conversations.create()` API
- ✅ **完整文档体系** - 创建《Coze会话隔离最终解决方案.md》（亲测有效）
- ✅ **实测验证通过** - 每个session获得独立的conversation_id
- ✅ **更新PRD文档** - 在prd/coze.md中补充正确实现方式

**前端UI优化**:
- ✅ **气泡菜单设计** - 输入框左侧浮动气泡菜单，点击展开两个操作选项
- ✅ **清除对话功能** - 添加历史分隔线，不清空对话内容
- ✅ **新建会话功能** - 立即清空界面，异步创建新会话，无卡顿
- ✅ **头像优化** - 使用fiido2.png，42px尺寸，contain适配
- ✅ **分隔线组件** - 支持系统消息类型，渐变分隔线样式

**后端优化**:
- ✅ **图片服务** - 添加 `/fiido2.png` 路由，提供头像文件
- ✅ **会话初始化** - 前端页面加载时立即创建conversation

**文档整理**:
- ✅ 创建核心文档《Coze会话隔离最终解决方案.md》
- ✅ 创建《文档清单.md》索引所有文档
- ✅ 创建《文档整理完成总结.md》
- ✅ 更新 prd/coze.md 添加1.2节"会话隔离的正确实现方式"
- ✅ 删除所有过时的诊断文档

### v2.1.0 (2025-11-19) - 三前端版本发布

**后端更新**:
- ✅ 新增 `conversation_id` 参数支持
- ✅ 新增 `POST /api/conversation/new` API
- ✅ 新增 `POST /api/chat/token` API (为 Chat SDK 生成 JWT)
- ✅ 新增 `GET /api/bot/info` API
- ✅ 集成 `JWTOAuthApp` 用于 SDK token 生成

**前端更新**:
- ✅ 新增 Vue 3 + TypeScript 现代化版本 (`frontend/`)
- ✅ 新增 Coze Chat SDK 版本 (`index_chat_sdk.html`)
- ✅ 增强 index2.html - 添加"新对话"/"新会话"功能
- ✅ 完全复刻 Fiido.com 官网设计
- ✅ 支持局域网访问 (`host: true`)

**文档更新**:
- ✅ 新增 `CHANGELOG.md` - 详细更新日志
- ✅ 新增 `完整总结.md` - 版本对比文档
- ✅ 新增 `使用说明-最终版.md`
- ✅ 新增 `frontend/README_CN.md`
- ✅ 更新 `README.md` - 添加三版本说明

### v2.0.0 (2025-11-18) - 会话隔离实现

- ✅ 实现基于 session_name 的会话隔离
- ✅ 双重添加 session_name (JWT + API payload)
- ✅ 完整的测试验证
- ✅ 文档整理和规范化

---

**最后更新**: 2025-11-20
**当前版本**: v2.2.1

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request!

## 📄 许可证

MIT License

---

Made with ❤️ by Claude Code
