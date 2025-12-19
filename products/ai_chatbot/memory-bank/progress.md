# AI 智能客服 - 进度追踪

## Step A1: 创建目录结构

**完成时间:** 2025-12-19
**状态:** 已完成

**已创建文件:**
- products/ai_chatbot/__init__.py
- products/ai_chatbot/routes.py
- products/ai_chatbot/models.py
- products/ai_chatbot/handlers/__init__.py
- products/ai_chatbot/memory-bank/*.md

## Step A2: 迁移 prompts 文件夹

**完成时间:** 2025-12-19
**状态:** 已完成

- 移动 prompts/ -> products/ai_chatbot/prompts/
- 在根目录创建符号链接保持兼容性

## Step A3: 创建共享依赖 dependencies.py

**完成时间:** 2025-12-19
**状态:** 已完成

- products/ai_chatbot/dependencies.py

## Step A4: 迁移聊天 API

**完成时间:** 2025-12-19
**状态:** 已完成

- products/ai_chatbot/handlers/chat.py
- 端点: /chat, /chat/stream, /bot/info

## Step A5: 迁移会话 API

**完成时间:** 2025-12-19
**状态:** 已完成

- products/ai_chatbot/handlers/conversation.py
- 端点: /conversation/create, /conversation/new, /conversation/clear

## Step A6: 迁移配置 API

**完成时间:** 2025-12-19
**状态:** 已完成

- products/ai_chatbot/handlers/config.py
- 端点: /config, /health, /shift/config, /shift/status, /token/info, /token/refresh

## Step A7: 注册路由 + 测试

**完成时间:** 2025-12-19
**状态:** 已完成

- 更新 routes.py 注册所有子路由
- 测试导入：12 个路由成功加载

## 待办

- 在 backend.py 注册 ai_chatbot 路由
- 集成测试
- 提交版本 v7.3.0
