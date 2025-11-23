# 企业级部署 - 开发任务拆解

> 版本: v1.0.0 | 创建时间: 2025-11-23

---

## P0-1: Redis 数据持久化

### 任务目标
将内存会话存储迁移到 Redis，支持服务重启后数据保留

### 开发任务

#### 1.1 创建 Redis 存储模块
```
文件: src/redis_session_store.py
工作量: 4小时
```

**接口定义**:
```python
class RedisSessionStore:
    async def get(session_name: str) -> SessionState
    async def save(session: SessionState)
    async def delete(session_name: str)
    async def list_by_status(status: SessionStatus, limit: int, offset: int) -> List[SessionState]
    async def count_by_status(status: SessionStatus) -> int
    async def get_stats() -> dict
```

#### 1.2 修改 backend.py
```
工作量: 2小时
```
- 添加 Redis 连接初始化
- 替换 InMemorySessionStore 为 RedisSessionStore
- 添加连接失败降级处理

#### 1.3 更新 .env 配置
```env
REDIS_URL=redis://localhost:6379/0
SESSION_EXPIRE_SECONDS=86400
REDIS_MAX_CONNECTIONS=10
```

#### 1.4 测试验证
- [ ] 创建会话后 Redis 有数据
- [ ] 重启服务后会话恢复
- [ ] 过期会话自动清理
- [ ] 回归测试通过

---

## P0-2: 坐席认证系统

### 任务目标
实现坐席登录认证，替换硬编码账号

### 开发任务

#### 2.1 创建认证模块
```
文件: src/agent_auth.py
工作量: 4小时
```

**数据模型**:
```python
class Agent(BaseModel):
    id: str
    username: str
    password_hash: str
    name: str
    role: str  # agent / admin
    status: str  # online / offline
    max_sessions: int = 5

class AgentToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    agent_id: str
    agent_name: str
```

#### 2.2 添加认证 API
```
文件: backend.py
工作量: 3小时
```

**接口**:
```python
POST /api/agent/login
  Request: {"username": "...", "password": "..."}
  Response: {"success": true, "token": "...", "agent": {...}}

POST /api/agent/logout
  Header: Authorization: Bearer <token>
  Response: {"success": true}

GET /api/agent/profile
  Header: Authorization: Bearer <token>
  Response: {"success": true, "agent": {...}}

POST /api/agent/refresh
  Request: {"refresh_token": "..."}
  Response: {"success": true, "token": "..."}
```

#### 2.3 添加认证中间件
```python
async def verify_agent_token(request: Request) -> Agent:
    """验证坐席Token，返回坐席信息"""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    # 验证并返回坐席信息
```

#### 2.4 保护坐席接口
需要认证的接口：
- `POST /api/sessions/{name}/takeover`
- `POST /api/sessions/{name}/release`
- `POST /api/sessions/{name}/transfer`
- `POST /api/manual/messages`
- `GET /api/sessions`
- `GET /api/sessions/stats`

#### 2.5 前端工作台改造
```
文件: agent-workbench/src/stores/agentStore.ts
工作量: 3小时
```
- 登录页面调用真实API
- Token 存储到 localStorage
- 请求拦截器添加 Authorization
- Token 过期自动跳转登录

#### 2.6 测试验证
- [ ] 无Token访问返回401
- [ ] 错误密码返回403
- [ ] Token过期返回401
- [ ] 登录成功可正常操作

---

## P0-3: HTTPS + Nginx 部署

### 任务目标
配置生产环境反向代理和SSL

### 开发任务

#### 3.1 创建 Nginx 配置
```
文件: deploy/nginx/fiido-kefu.conf
工作量: 2小时
```

#### 3.2 创建 Docker Compose
```
文件: docker-compose.yml
工作量: 3小时
```

```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx:/etc/nginx/conf.d
      - ./frontend/dist:/var/www/frontend
      - ./agent-workbench/dist:/var/www/agent

volumes:
  redis_data:
```

#### 3.3 创建 Dockerfile
```
文件: Dockerfile
工作量: 1小时
```

#### 3.4 SSL 证书配置
- Let's Encrypt 自动续期
- 或使用云服务商证书

#### 3.5 测试验证
- [ ] docker-compose up 正常启动
- [ ] HTTPS 访问正常
- [ ] SSE 长连接不中断
- [ ] 静态资源有缓存

---

## P0-4: 前端嵌入 SDK

### 任务目标
提供独立站嵌入方案

### 开发任务

#### 4.1 创建嵌入式前端
```
目录: embed/
工作量: 6小时
```

**功能**:
- 独立的聊天窗口组件
- 可配置外观和位置
- 最小化/最大化切换
- 未读消息提示

#### 4.2 创建 JS SDK
```
文件: embed/dist/fiido-kefu.js
工作量: 4小时
```

**API**:
```javascript
window.FiidoKefu = {
  init(config),    // 初始化
  open(),          // 打开窗口
  close(),         // 关闭窗口
  toggle(),        // 切换状态
  setUser(info),   // 设置用户信息
  on(event, fn)    // 监听事件
}
```

#### 4.3 嵌入页面路由
```
GET /embed - 返回嵌入式聊天页面
GET /sdk/fiido-kefu.js - 返回SDK文件
```

#### 4.4 测试验证
- [ ] 一行代码可嵌入
- [ ] 跨域通信正常
- [ ] 移动端适配
- [ ] 不影响宿主页面

---

## P1-1: 日志和监控

### 任务目标
实现结构化日志和关键指标监控

### 开发任务

#### 1.1 结构化日志
```
文件: src/logger.py
工作量: 3小时
```

```python
import structlog

logger = structlog.get_logger()

# 使用
logger.info("chat_request",
    session_name=session_id,
    duration_ms=1500,
    status="success"
)
```

#### 1.2 关键指标收集
```python
# 指标
- request_count: 请求总数
- request_duration: 请求耗时
- active_sessions: 活跃会话数
- pending_manual: 等待人工数
- error_count: 错误数
```

#### 1.3 监控端点
```
GET /api/metrics - Prometheus 格式指标
GET /api/health/detailed - 详细健康状态
```

---

## P1-2: 安全加固

### 任务目标
添加安全防护措施

### 开发任务

#### 2.1 CORS 白名单
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourshop.com"],  # 仅允许独立站
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

#### 2.2 速率限制
```python
from slowapi import Limiter

@app.post("/api/chat")
@limiter.limit("30/minute")
async def chat(...):
    pass
```

#### 2.3 输入验证
- 消息长度限制
- XSS 过滤
- SQL 注入防护

---

## 开发顺序

```
Week 1:
├── Day 1-2: P0-1 Redis持久化
├── Day 3-4: P0-2 坐席认证
└── Day 5: P0-3 Docker部署

Week 2:
├── Day 1-2: P0-4 嵌入SDK
├── Day 3: P1-1 日志监控
├── Day 4: P1-2 安全加固
└── Day 5: 集成测试

Week 3:
├── Day 1-2: Bug修复
├── Day 3: 性能优化
└── Day 4-5: 上线部署
```

---

## 验收标准

### P0 完成标准
- [ ] 服务重启会话不丢失
- [ ] 坐席必须登录才能操作
- [ ] HTTPS 访问正常
- [ ] 嵌入代码可用
- [ ] 回归测试 12/12 通过

### P1 完成标准
- [ ] 日志可查询
- [ ] 指标可监控
- [ ] 安全防护生效
