---
name: deploy-guide
description: 部署 Fiido 项目到生产服务器时，自动检查部署前提条件、生成部署命令、提供回滚方案。当用户说"部署"、"上线"、"发布到服务器"时自动激活
---

# Fiido 部署指南

## 何时使用
- 用户说"部署到服务器"
- 用户说"上线"
- 用户说"发布"
- 用户说"更新生产环境"

## 服务器配置（铁律）

| 配置项 | 值 |
|--------|-----|
| 服务器地址 | 8.211.27.199 |
| 项目目录 | /opt/fiido-ai-service/ |
| 前端部署 | /var/www/fiido-frontend/ |
| 后端服务名 | fiido-ai-backend |
| 用户端地址 | https://ai.fiido.com/chat-test/ |
| SSH 认证 | 密码登录（使用 sshpass） |

## SSH 连接方式

服务器使用密码登录，Claude Code 中需使用 sshpass：

```bash
# 密码存储在环境变量中（安全）
export FIIDO_SSH_PASS="你的密码"

# 使用 sshpass 执行命令
sshpass -e ssh root@8.211.27.199 '命令'
```

**注意**：如果 sshpass 未安装，先安装：
```bash
sudo apt-get install sshpass
```

## 部署前检查清单（必须全部通过）

```
□ 1. 本地测试通过
□ 2. 代码已提交并推送到 Git
□ 3. 版本号已更新（git tag）
□ 4. progress.md 已更新
□ 5. 没有包含敏感信息
□ 6. 已通知相关人员（如需要）
```

## 部署命令

> **前提**：已设置环境变量 `export FIIDO_SSH_PASS="密码"`

### 方式一：仅后端部署

```bash
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git pull && systemctl restart fiido-ai-backend'
```

### 方式二：仅前端部署（AI 客服）

```bash
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service/products/ai_chatbot/frontend && npm run build && rm -rf /var/www/fiido-frontend/* && cp -r dist/* /var/www/fiido-frontend/'
```

### 方式三：完整部署（后端+前端）

```bash
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git pull && \
  systemctl restart fiido-ai-backend && \
  cd products/ai_chatbot/frontend && npm run build && \
  rm -rf /var/www/fiido-frontend/* && \
  cp -r dist/* /var/www/fiido-frontend/'
```

## 部署后验证

```bash
# 1. 检查后端服务状态
sshpass -e ssh root@8.211.27.199 'systemctl status fiido-ai-backend'

# 2. 检查后端健康
curl https://ai.fiido.com/api/health

# 3. 访问前端页面
# 浏览器打开 https://ai.fiido.com/chat-test/
```

## 回滚方案

### 紧急回滚（回到上一个版本）

```bash
# 1. 查看最近的版本
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git log --oneline -5'

# 2. 回滚到指定版本
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git reset --hard HEAD~1 && systemctl restart fiido-ai-backend'

# 3. 如果前端也需要回滚
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service/products/ai_chatbot/frontend && npm run build && rm -rf /var/www/fiido-frontend/* && cp -r dist/* /var/www/fiido-frontend/'
```

### 回滚到指定版本号

```bash
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service && git checkout vX.X.X && systemctl restart fiido-ai-backend'
```

## 常见问题处理

### 后端启动失败

```bash
# 查看错误日志
sshpass -e ssh root@8.211.27.199 'journalctl -u fiido-ai-backend -n 50'

# 常见原因：
# 1. Python 依赖缺失 → pip install -r requirements.txt
# 2. 端口被占用 → 检查并杀死占用进程
# 3. 配置文件错误 → 检查 .env
```

### 前端构建失败

```bash
# 查看 npm 错误
sshpass -e ssh root@8.211.27.199 'cd /opt/fiido-ai-service/products/ai_chatbot/frontend && npm run build'

# 常见原因：
# 1. 依赖缺失 → npm install
# 2. TypeScript 错误 → 本地先修复再部署
```

## 部署禁止事项（铁律）

- ❌ 禁止未经测试就部署
- ❌ 禁止未提交代码就部署（本地改动会丢失）
- ❌ 禁止直接在服务器上修改代码
- ❌ 禁止删除 /opt/fiido-ai-service 目录
- ❌ 禁止修改服务器 nginx 配置（除非明确需要）

## 部署流程图

```
┌─────────────────────────────────────────────────────┐
│  1. 本地开发完成                                     │
│         ↓                                           │
│  2. 本地测试通过                                     │
│         ↓                                           │
│  3. Git commit + tag + push                         │
│         ↓                                           │
│  4. 执行部署前检查清单                               │
│         ↓                                           │
│  5. 选择部署方式（后端/前端/完整）                   │
│         ↓                                           │
│  6. 执行部署命令                                     │
│         ↓                                           │
│  7. 部署后验证                                       │
│         ↓                                           │
│  8. 验证通过? ─── 否 ──→ 执行回滚                    │
│         │                                           │
│        是                                           │
│         ↓                                           │
│  9. 部署成功！通知相关人员                           │
└─────────────────────────────────────────────────────┘
```
