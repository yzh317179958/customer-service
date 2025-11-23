# Fiido 智能客服系统 - 测试流程规范

> 版本: v1.0.0 | 更新时间: 2025-11-23

---

## 一、测试环境准备

### 1.1 启动服务

```bash
# 1. 启动后端服务
cd /home/yzh/AI客服/鉴权
python3 backend.py

# 2. 启动用户端前端 (新终端)
cd /home/yzh/AI客服/鉴权/frontend
npm run dev
# 访问: http://localhost:5173

# 3. 启动坐席工作台 (新终端)
cd /home/yzh/AI客服/鉴权/agent-workbench
npm run dev
# 访问: http://localhost:5174
```

### 1.2 测试账号

| 角色 | 账号 | 密码 | 用途 |
|------|------|------|------|
| 坐席1 | agent_001 | 123456 | 主测试坐席 |
| 坐席2 | agent_002 | 123456 | 转接测试 |
| 坐席3 | agent_003 | 123456 | 并发测试 |

---

## 二、功能开发测试流程

### 2.1 开发完成后必做步骤

```
1. 单元测试 → 2. 回归测试 → 3. 手动验证 → 4. 边界测试
```

### 2.2 回归测试脚本

每次功能开发完成后，**必须运行**回归测试：

```bash
cd /home/yzh/AI客服/鉴权
./tests/regression_test.sh
```

**预期结果**: 12/12 测试全部通过

### 2.3 测试报告记录

每次测试后记录：
- 测试时间
- 测试环境
- 通过/失败数量
- 失败原因（如有）

---

## 三、核心场景测试用例

### 3.1 AI 对话测试

**目的**: 验证基础 AI 对话功能正常

**步骤**:
1. 打开用户端 http://localhost:5173
2. 发送消息："你好"
3. 等待 AI 回复
4. 发送产品问题："D11 价格多少？"
5. 验证回复包含产品信息

**预期结果**:
- [ ] 消息发送成功，显示在对话框
- [ ] AI 在 5 秒内返回回复
- [ ] 回复内容与问题相关
- [ ] 状态栏显示"AI 服务中"（绿色）

**异常检查**:
- 网络断开时应显示错误提示
- 超时时应有重试机制

---

### 3.2 人工升级测试

**目的**: 验证用户主动请求人工和关键词触发

#### 3.2.1 主动请求人工

**步骤**:
1. 用户端发送："转人工"
2. 或点击"人工客服"按钮

**预期结果**:
- [ ] 状态变为 `pending_manual`
- [ ] 状态栏显示"等待人工接入"（橙色）
- [ ] 显示等待动画
- [ ] 后续 AI 对话被阻止

#### 3.2.2 关键词触发

**触发关键词**: `人工, 真人, 客服, 投诉, 无法解决`

**步骤**:
1. 发送包含关键词的消息
2. 观察状态变化

**预期结果**: 同上

---

### 3.3 坐席接入测试

**目的**: 验证坐席接入会话和消息收发

**步骤**:
1. 用户端触发人工升级
2. 坐席工作台登录 (agent_001)
3. 在"待接入"列表找到会话
4. 点击"接入"按钮
5. 发送消息给用户
6. 用户端回复消息

**预期结果**:
- [ ] 坐席工作台显示待接入会话
- [ ] 接入后状态变为 `manual_live`
- [ ] 用户端显示"客服【xxx】已接入"
- [ ] 双向消息实时显示
- [ ] 用户端状态栏显示"人工服务中"（蓝色）

**API 验证**:
```bash
# 查看会话状态
curl http://localhost:8000/api/sessions/{session_name}
```

---

### 3.4 会话释放测试

**目的**: 验证结束人工服务恢复 AI

**步骤**:
1. 在人工服务状态下
2. 坐席点击"结束服务"
3. 确认释放

**预期结果**:
- [ ] 状态变为 `bot_active`
- [ ] 用户端显示"人工服务已结束，AI 助手已接管"
- [ ] 用户可以继续与 AI 对话
- [ ] 状态栏恢复绿色

---

### 3.5 会话转接测试

**目的**: 验证坐席间会话转接

**步骤**:
1. 坐席1 (agent_001) 接入会话
2. 点击"转接"按钮
3. 选择目标坐席 (agent_002)
4. 填写转接原因
5. 确认转接
6. 坐席2 登录查看

**预期结果**:
- [ ] 转接成功提示
- [ ] 用户端显示转接系统消息
- [ ] 坐席2 工作台出现该会话
- [ ] 坐席1 工作台会话消失
- [ ] assigned_agent 更新为坐席2

**API 验证**:
```bash
curl -X POST http://localhost:8000/api/sessions/{session_name}/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_agent_id": "agent_001",
    "to_agent_id": "agent_002",
    "to_agent_name": "技术支持-小李",
    "reason": "专业问题转接"
  }'
```

---

### 3.6 防抢单测试

**目的**: 验证同一会话不能被多人接入

**步骤**:
1. 用户触发人工升级
2. 坐席1 和 坐席2 同时尝试接入
3. 观察结果

**预期结果**:
- [ ] 只有一个坐席接入成功
- [ ] 另一个收到 409 错误
- [ ] 错误信息显示"会话已被坐席【xxx】接入"

---

### 3.7 非工作时间测试

**目的**: 验证非工作时间邮件通知

**配置修改** (临时测试):
```python
# src/shift_config.py
# 将工作时间改为当前时间之外
```

**步骤**:
1. 修改工作时间配置
2. 用户请求人工
3. 检查邮件发送

**预期结果**:
- [ ] 返回 `is_in_shift: false`
- [ ] 邮件发送成功
- [ ] 状态保持 `bot_active`（不转人工）
- [ ] 用户可继续 AI 对话

---

### 3.8 快捷短语测试

**目的**: 验证坐席快捷短语功能

**步骤**:
1. 坐席接入会话
2. 点击快捷短语按钮
3. 选择分类
4. 点击短语
5. 发送

**预期结果**:
- [ ] 短语面板正常显示
- [ ] 分类切换正常
- [ ] 搜索过滤正常
- [ ] 点击后填入输入框
- [ ] 发送成功

---

### 3.9 会话隔离测试

**目的**: 验证不同用户会话完全隔离

**步骤**:
1. 浏览器A 打开用户端，发送消息
2. 浏览器B（或无痕模式）打开用户端，发送消息
3. 检查两个会话的 conversation_id

**预期结果**:
- [ ] 两个会话有不同的 session_id
- [ ] conversation_id 不同
- [ ] 对话历史完全隔离
- [ ] 一个触发人工不影响另一个

---

## 四、API 测试命令速查

### 4.1 健康检查
```bash
curl http://localhost:8000/api/health
```

### 4.2 获取会话列表
```bash
# 所有会话
curl "http://localhost:8000/api/sessions"

# 待接入会话
curl "http://localhost:8000/api/sessions?status=pending_manual"

# 服务中会话
curl "http://localhost:8000/api/sessions?status=manual_live"
```

### 4.3 获取统计信息
```bash
curl http://localhost:8000/api/sessions/stats
```

### 4.4 人工升级
```bash
curl -X POST http://localhost:8000/api/manual/escalate \
  -H "Content-Type: application/json" \
  -d '{"session_name": "test_session", "reason": "user_request"}'
```

### 4.5 坐席接入
```bash
curl -X POST http://localhost:8000/api/sessions/{session_name}/takeover \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_001", "agent_name": "测试坐席"}'
```

### 4.6 发送人工消息
```bash
curl -X POST http://localhost:8000/api/manual/messages \
  -H "Content-Type: application/json" \
  -d '{
    "session_name": "test_session",
    "role": "agent",
    "content": "您好，有什么可以帮您？",
    "agent_info": {"agent_id": "agent_001", "agent_name": "测试坐席"}
  }'
```

### 4.7 释放会话
```bash
curl -X POST http://localhost:8000/api/sessions/{session_name}/release \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent_001", "reason": "resolved"}'
```

### 4.8 工作时间状态
```bash
curl http://localhost:8000/api/shift/status
```

---

## 五、边界条件测试

### 5.1 异常输入测试

| 测试项 | 输入 | 预期结果 |
|--------|------|----------|
| 空消息 | "" | 阻止发送 |
| 超长消息 | 10000字符 | 截断或提示 |
| 特殊字符 | `<script>alert(1)</script>` | 转义显示 |
| 表情符号 | 😀🎉 | 正常显示 |

### 5.2 并发测试

| 场景 | 预期结果 |
|------|----------|
| 多用户同时请求人工 | 各自独立排队 |
| 多坐席同时接入同一会话 | 只有一个成功 |
| 高频消息发送 | 正常处理或限流 |

### 5.3 网络异常测试

| 场景 | 预期结果 |
|------|----------|
| 后端服务重启 | 前端显示重连提示 |
| 网络断开 | 消息发送失败提示 |
| 请求超时 | 显示超时错误 |

---

## 六、测试检查清单

### 6.1 功能开发完成检查

- [ ] 回归测试全部通过 (12/12)
- [ ] 新功能手动测试通过
- [ ] API 返回格式正确
- [ ] 错误处理完善
- [ ] 日志输出正常
- [ ] 无 console 错误

### 6.2 发布前检查

- [ ] 所有核心场景测试通过
- [ ] 边界条件测试通过
- [ ] 性能测试通过
- [ ] 安全检查通过
- [ ] 文档更新完成

---

## 七、常见问题排查

### 7.1 后端启动失败

```bash
# 检查端口占用
lsof -i :8000

# 检查环境变量
cat .env

# 检查依赖
pip3 list | grep -E "fastapi|coze"
```

### 7.2 前端连接失败

```bash
# 检查后端是否运行
curl http://localhost:8000/api/health

# 检查 CORS 配置
# backend.py 中 allow_origins
```

### 7.3 会话状态异常

```bash
# 查看会话详情
curl http://localhost:8000/api/sessions/{session_name}

# 查看后端日志
# 搜索 session_name 相关日志
```

### 7.4 SSE 消息不推送

检查:
1. 浏览器 Network 面板是否有 SSE 连接
2. 后端日志是否有 "SSE 推送" 输出
3. session_name 是否匹配

---

## 八、测试数据清理

```bash
# 重启后端会清空内存中的会话数据
# 如需保留，检查 SESSION_STATE_BACKUP_FILE 配置
```

---

## 附录：测试用例模板

```markdown
### 测试用例: [用例名称]

**ID**: TC-XXX
**优先级**: P0/P1/P2
**前置条件**:
- 条件1
- 条件2

**测试步骤**:
1. 步骤1
2. 步骤2
3. 步骤3

**预期结果**:
- [ ] 结果1
- [ ] 结果2

**实际结果**:
- 通过/失败
- 备注

**测试人员**:
**测试时间**:
```
