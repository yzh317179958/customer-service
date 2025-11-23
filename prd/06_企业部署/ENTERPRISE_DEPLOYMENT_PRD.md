# 企业级部署需求文档 - 独立站AI客服系统

> 版本: v1.0.0 | 创建时间: 2025-11-23
> 目标: 将AI客服系统部署到独立站，实现生产环境可用

---

## 一、当前状态评估

### 已完成功能 (可用)
- ✅ AI对话核心功能
- ✅ 会话隔离机制
- ✅ 多轮对话支持
- ✅ 人工接管流程 (升级/接入/转接/释放)
- ✅ 监管策略引擎
- ✅ 坐席工作台UI
- ✅ 用户端聊天界面
- ✅ SSE实时消息推送
- ✅ 工作时间判断
- ✅ 邮件通知

### 生产环境缺失项 (必须完成)

| 优先级 | 功能模块 | 当前状态 | 生产风险 |
|--------|----------|----------|----------|
| P0 | 数据持久化 | 内存存储，重启丢失 | 🔴 致命 |
| P0 | 坐席认证系统 | 硬编码账号 | 🔴 致命 |
| P0 | HTTPS部署 | 无 | 🔴 致命 |
| P0 | 前端嵌入方案 | 无 | 🔴 致命 |
| P1 | 日志监控 | 仅console | 🟠 严重 |
| P1 | 错误处理 | 基础 | 🟠 严重 |
| P2 | 性能优化 | 未优化 | 🟡 中等 |

---

## 二、P0-必须完成 (部署前提)

### 2.1 数据持久化 (Redis)

**问题**: 当前会话数据存储在内存中，服务重启后所有会话丢失

**需求**:
```
- 会话状态持久化到Redis
- 支持服务重启后恢复会话
- 支持多实例部署共享数据
```

**实现方案**:
```python
# src/redis_session_store.py
import redis
import json

class RedisSessionStore:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def save(self, session: SessionState):
        key = f"session:{session.session_name}"
        self.redis.setex(key, 86400, session.json())  # 24小时过期

    async def get(self, session_name: str) -> SessionState:
        data = self.redis.get(f"session:{session_name}")
        return SessionState.parse_raw(data) if data else None
```

**配置**:
```env
# .env
REDIS_URL=redis://localhost:6379/0
SESSION_EXPIRE_SECONDS=86400
```

**验收标准**:
- [ ] 服务重启后会话数据保留
- [ ] 多个后端实例可共享会话
- [ ] 过期会话自动清理

---

### 2.2 坐席认证系统

**问题**: 当前坐席登录是硬编码，任何人都可以登录

**需求**:
```
- 坐席账号数据库存储
- 登录验证 + JWT Token
- Token刷新和过期处理
- 权限控制 (普通坐席/管理员)
```

**API设计**:
```
POST /api/agent/login      - 坐席登录
POST /api/agent/logout     - 坐席登出
GET  /api/agent/profile    - 获取坐席信息
POST /api/agent/refresh    - 刷新Token
```

**数据模型**:
```python
class Agent(BaseModel):
    id: str
    username: str
    password_hash: str
    name: str
    role: str  # agent / admin
    status: str  # online / offline / busy
    max_sessions: int = 5  # 最大同时服务数
    created_at: float
```

**验收标准**:
- [ ] 坐席必须登录才能访问工作台
- [ ] Token过期自动跳转登录页
- [ ] 密码加密存储
- [ ] 登录失败次数限制

---

### 2.3 HTTPS + 反向代理

**问题**: 生产环境必须使用HTTPS，当前无部署配置

**需求**:
```
- Nginx反向代理配置
- SSL证书 (Let's Encrypt)
- HTTP自动跳转HTTPS
- 静态资源缓存
- Gzip压缩
```

**Nginx配置示例**:
```nginx
# /etc/nginx/sites-available/fiido-kefu
server {
    listen 80;
    server_name kefu.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name kefu.yourdomain.com;

    ssl_certificate /etc/letsencrypt/live/kefu.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/kefu.yourdomain.com/privkey.pem;

    # 后端API
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # SSE长连接
    }

    # 用户端前端
    location / {
        root /var/www/fiido-kefu/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 坐席工作台
    location /agent {
        alias /var/www/fiido-kefu/agent-workbench/dist;
        try_files $uri $uri/ /agent/index.html;
    }
}
```

**验收标准**:
- [ ] HTTPS访问正常
- [ ] HTTP自动跳转HTTPS
- [ ] SSE长连接不中断
- [ ] 静态资源有缓存

---

### 2.4 前端嵌入方案 (独立站集成)

**问题**: 需要将聊天窗口嵌入到独立站页面

**需求**:
```
- 提供嵌入式JS SDK
- 支持iframe嵌入
- 可配置外观和位置
- 跨域通信支持
```

**嵌入代码示例**:
```html
<!-- 方式1: JS SDK嵌入 -->
<script>
  window.FiidoKefuConfig = {
    serverUrl: 'https://kefu.yourdomain.com',
    position: 'bottom-right',
    theme: 'light',
    welcomeMessage: '您好，有什么可以帮您？'
  };
</script>
<script src="https://kefu.yourdomain.com/sdk/fiido-kefu.js"></script>

<!-- 方式2: iframe嵌入 -->
<iframe
  src="https://kefu.yourdomain.com/embed?shop=yourshop"
  style="position:fixed;bottom:20px;right:20px;width:380px;height:520px;border:none;"
></iframe>
```

**SDK功能**:
```javascript
// fiido-kefu.js
class FiidoKefu {
  // 初始化
  init(config) {}

  // 打开聊天窗口
  open() {}

  // 关闭聊天窗口
  close() {}

  // 发送自定义消息
  sendMessage(content) {}

  // 设置用户信息
  setUser(userInfo) {}

  // 监听事件
  on(event, callback) {}
}
```

**验收标准**:
- [ ] 一行代码即可嵌入
- [ ] 不影响宿主页面性能
- [ ] 支持移动端适配
- [ ] 可自定义样式

---

## 三、P1-应该完成 (稳定运行)

### 3.1 日志和监控

**需求**:
```
- 结构化日志 (JSON格式)
- 日志分级 (INFO/WARN/ERROR)
- 关键指标监控 (QPS/延迟/错误率)
- 告警通知 (邮件/企微)
```

**日志格式**:
```json
{
  "timestamp": "2025-11-23T10:30:00Z",
  "level": "INFO",
  "event": "chat_request",
  "session_name": "user_123",
  "duration_ms": 1500,
  "status": "success"
}
```

**监控指标**:
- 每分钟请求数
- 平均响应时间
- 错误率
- 活跃会话数
- 等待人工数

---

### 3.2 错误处理和重试

**需求**:
```
- Coze API调用失败重试
- 网络超时处理
- 优雅降级 (AI不可用时提示)
- 错误信息用户友好
```

**重试策略**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(httpx.TimeoutException)
)
async def call_coze_api(...):
    pass
```

---

### 3.3 安全加固

**需求**:
```
- CORS白名单限制
- 请求速率限制
- 输入验证和XSS防护
- SQL注入防护 (如使用数据库)
- 敏感信息脱敏
```

**速率限制配置**:
```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)

@app.post("/api/chat")
@limiter.limit("20/minute")  # 每分钟最多20次
async def chat(...):
    pass
```

---

## 四、P2-可以完成 (体验优化)

### 4.1 会话历史查询

**需求**:
- 用户可查看历史对话
- 坐席可查看服务记录
- 支持按时间/关键词搜索

### 4.2 数据统计报表

**需求**:
- 每日/周/月对话量统计
- 人工接管率统计
- 坐席工作量统计
- 用户满意度统计

### 4.3 多语言支持

**需求**:
- 界面多语言 (中/英)
- 系统消息多语言

### 4.4 移动端适配

**需求**:
- 响应式布局
- 触摸优化
- 移动端坐席工作台

---

## 五、部署架构

### 5.1 单机部署 (初期)

```
用户浏览器 → Nginx(443) → Backend(8000)
                       → Frontend静态文件
                       → Redis(6379)
```

**适用**: 日活 < 1000，单服务器

### 5.2 分布式部署 (扩展)

```
用户 → CDN → 负载均衡 → Backend集群
                     → Redis集群
                     → 日志服务
```

**适用**: 日活 > 1000，需要高可用

---

## 六、开发计划

### 第1周: P0基础
- Day 1-2: Redis持久化
- Day 3-4: 坐席认证系统
- Day 5: HTTPS部署

### 第2周: P0完成 + P1开始
- Day 1-2: 前端嵌入SDK
- Day 3-4: 日志监控
- Day 5: 安全加固

### 第3周: P1完成 + 测试
- Day 1-2: 错误处理完善
- Day 3-4: 集成测试
- Day 5: 上线准备

---

## 七、验收清单

### 部署前必须通过

- [ ] 服务重启后会话不丢失
- [ ] 坐席必须登录才能操作
- [ ] HTTPS访问正常
- [ ] 嵌入代码可用
- [ ] 所有API返回正确
- [ ] 错误有友好提示
- [ ] 日志可查询
- [ ] 回归测试 12/12 通过

### 上线后监控

- [ ] 服务可用性 > 99%
- [ ] API响应时间 < 2s
- [ ] 错误率 < 1%
- [ ] 无数据丢失

---

## 八、技术选型

| 组件 | 选型 | 理由 |
|------|------|------|
| 数据持久化 | Redis | 高性能、支持过期、易部署 |
| 认证 | JWT | 无状态、跨域友好 |
| 反向代理 | Nginx | 成熟稳定、SSL支持好 |
| 日志 | Python logging + JSON | 简单够用 |
| 部署 | Docker Compose | 易于管理和迁移 |

---

## 九、成本估算

### 服务器
- 2核4G云服务器: ¥100-200/月
- Redis: 内置或云服务 ¥50/月

### 域名和证书
- 域名: ¥50-100/年
- SSL证书: Let's Encrypt 免费

### 总计
- 初期: ¥150-300/月
- 扩展后: ¥500-1000/月

