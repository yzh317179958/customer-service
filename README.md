# Fifo 智能客服系统

基于 Coze Workflow 的企业级智能客服解决方案，支持 **AI 自动应答 + 人工接管** 双模式。

## 核心功能

- **AI 智能对话** - 基于 Coze Workflow，多轮对话和上下文理解
- **人工无缝接管** - AI 无法解决时自动/手动转人工
- **实时消息推送** - SSE 长连接，坐席消息即时送达
- **坐席工作台** - 独立的坐席管理系统，支持多坐席协作
- **工单系统** - 完整的工单管理、SLA 计时、自动化规则

## 技术栈

| 模块 | 技术 |
|------|------|
| 后端 | FastAPI + Python 3.10+ |
| 前端 | Vue 3 + TypeScript + Pinia |
| AI 引擎 | Coze Workflow API |
| 鉴权 | OAuth 2.0 + JWT |
| 数据存储 | Redis |
| 实时通信 | SSE |

## 快速开始

### 1. 安装依赖

```bash
pip3 install -r requirements.txt
```

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）:

```bash
# Coze API 配置
COZE_API_BASE=https://api.coze.com
COZE_WORKFLOW_ID=你的工作流ID
COZE_APP_ID=你的应用ID

# OAuth 配置
COZE_OAUTH_CLIENT_ID=你的ClientID
COZE_OAUTH_PUBLIC_KEY_ID=你的公钥指纹
COZE_OAUTH_PRIVATE_KEY_FILE=./private_key.pem

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 3. 启动服务

```bash
# 后端
python3 backend.py
# 访问: http://localhost:8000
# API文档: http://localhost:8000/docs

# 用户端
cd frontend && npm install && npm run dev
# 访问: http://localhost:5173

# 坐席工作台
cd agent-workbench && npm install && npm run dev
# 访问: http://localhost:5174
# 默认账号: admin/admin123, agent001/agent123
```

## 项目结构

```
├── backend.py              # 后端主服务
├── src/                    # 后端模块
│   ├── session_state.py    # 会话状态机
│   ├── ticket_store.py     # 工单存储
│   ├── agent_auth.py       # 坐席认证
│   └── redis_session_store.py  # Redis 存储
├── frontend/               # 用户端 Vue 项目
├── agent-workbench/        # 坐席工作台 Vue 项目
├── tests/                  # 测试脚本
│   └── regression_test.sh  # 回归测试
├── prd/                    # 需求和技术文档
│   ├── 02_约束与原则/      # 核心约束（必读）
│   └── 03_技术方案/        # API 契约
└── CLAUDE.md               # 开发指令（AI 开发必读）
```

## 核心 API

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/chat` | POST | AI 对话（同步） |
| `/api/chat/stream` | POST | AI 对话（流式） |
| `/api/manual/escalate` | POST | 转人工 |
| `/api/sessions/{name}/takeover` | POST | 坐席接入 |
| `/api/sessions/{name}/release` | POST | 释放会话 |
| `/api/tickets` | GET/POST | 工单管理 |

完整 API 文档见: `prd/03_技术方案/api_contract.md`

## 会话状态流转

```
bot_active → pending_manual → manual_live → bot_active
  (AI服务)    (等待人工)      (人工服务)    (恢复AI)
```

## 测试

```bash
# 回归测试
./tests/regression_test.sh

# 健康检查
curl http://localhost:8000/api/health
```

## 开发指南

开发前必读：
1. `CLAUDE.md` - 开发指令和核心约束
2. `prd/02_约束与原则/` - 技术约束
3. `prd/03_技术方案/api_contract.md` - API 契约

## 许可证

MIT License
