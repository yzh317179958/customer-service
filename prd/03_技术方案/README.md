# 技术方案文档

本目录包含系统的技术架构设计和 API 接口定义。

## 文档说明

| 文档 | 说明 | 用途 |
|------|------|------|
| TECHNICAL_SOLUTION_v1.0.md | 技术架构方案 | 架构参考 |
| api_contract.md | API 接口契约 | 接口开发 |

## 技术栈

### 后端
- FastAPI (Python)
- Coze API / SDK
- OAuth + JWT 鉴权

### 前端
- Vue 3 + TypeScript
- Pinia 状态管理
- Vite 构建

## 核心模块

### SessionState 会话状态
- 状态机管理
- 历史消息存储
- 升级信息记录

### Regulator 监管引擎
- 关键词检测
- AI 失败计数
- 自动升级触发

### SSE 实时通信
- 消息推送
- 状态变更通知

## API 分类

### 对话类
- `/api/chat` - 同步对话
- `/api/chat/stream` - 流式对话

### 会话管理类
- `/api/sessions` - 会话列表
- `/api/sessions/{name}` - 会话详情
- `/api/sessions/{name}/takeover` - 接入
- `/api/sessions/{name}/release` - 释放
- `/api/sessions/{name}/transfer` - 转接

### 人工接管类
- `/api/manual/escalate` - 升级
- `/api/manual/messages` - 消息

## 使用建议

1. **后端开发**: 参考 api_contract.md 实现接口
2. **前端开发**: 根据 API 契约对接
3. **架构理解**: 阅读 TECHNICAL_SOLUTION_v1.0.md
