# Fiido 智能客服系统 - Claude 开发指令

## 项目概述

基于 Coze API 的智能客服系统，包含用户端、坐席工作台和后端服务。

---

## 铁律 0: 渐进式增量化开发（最高优先级）

**强制要求**：所有开发工作必须严格遵守渐进式增量化开发方式，禁止一次性大规模修改。

### 核心原则

1. **小步快跑，频繁验证**
   - ❌ 禁止一次性开发多个功能
   - ❌ 禁止一次性修改 10+ 个文件
   - ✅ 每个增量独立开发 → 测试 → 提交 → 打tag

2. **每个增量必须是完整可验证的**
   - ✅ 一个完整的后端API（包含测试）
   - ✅ 一个完整的前端功能模块（包含自测）
   - ✅ 一个Bug修复（包含验证）
   - ❌ 半成品功能（缺少测试）
   - ❌ 跨多个模块的大规模改动

3. **每个增量独立提交和版本标记**
   ```bash
   # ✅ 正确
   git commit -m "feat: 功能描述 v3.8.1"
   git tag v3.8.1

   # ❌ 错误 - 批量提交多个功能
   git commit -m "feat: 功能1+功能2+功能3 v3.8.5"
   ```

### 增量粒度标准

**后端开发**：

| 增量类型 | 最大修改范围 | 提交周期 |
|---------|-------------|---------|
| 单个API端点 | 1个文件，< 100行代码 | 立即提交 |
| 数据模型变更 | 1-2个文件 | 立即提交 |
| 业务逻辑模块 | 1个模块文件 | 立即提交 |
| Bug修复 | 最小改动 | 立即提交 |
| ❌ 禁止大规模重构 | 修改 > 5个文件 | 必须拆分增量 |

**前端开发**：

| 增量类型 | 最大修改范围 | 提交周期 |
|---------|-------------|---------|
| 单个组件 | 1个.vue文件 | 自测后立即提交 |
| 样式调整 | 1个组件的CSS | 立即提交 |
| 交互逻辑 | 1个composable | 立即提交 |
| UI测试验证 | 用户确认后 | 用户确认后提交 |
| ❌ 禁止批量修改 | 修改 > 3个组件 | 必须拆分为多次 |

**文档更新**：

| 增量类型 | 最大修改范围 | 提交周期 |
|---------|-------------|---------|
| 单个功能文档 | 1个.md文件 | 立即提交 |
| 进度更新 | 任务拆解文档状态更新 | 功能完成后 |
| ❌ 禁止批量更新 | 修改 > 3个文档 | 必须拆分增量 |

### 开发流程强制要求

**阶段1: 需求拆解**（开发前）
- 将大需求拆解为独立的小增量
- 每个增量：可独立开发、可独立测试、可独立部署、有明确验收标准

**阶段2: 增量开发**（开发中）
1. 开发（最多1小时）
2. 自测（立即）
3. 编写测试（后端必须，前端可选）
4. 运行回归测试（必须）
5. 提交代码（立即）
6. 打版本标签（立即）
7. 用户测试（前端UI功能）
8. 修复问题（如有）→ 新增量

⚠️ 禁止：开发超过2小时不提交、跳过测试、批量提交

**阶段3: 集成验证**（开发后）
- 回归测试（所有增量集成后）
- 性能测试（如需要）
- 用户验收（完整功能）
- 文档更新（同步更新进度）

### 违规后果

- 🔴 严重违规（立即回滚）：修改 > 10个文件、> 500行代码、开发超过4小时不提交、跳过测试、回归测试未通过
- 🟡 轻度违规（警告并拆分）：修改 5-10个文件、300-500行代码、开发超过2小时不提交

```bash
# 提交前自检
git diff --stat  # 检查修改文件数
git diff | wc -l  # 检查代码行数
# 如果超标 → 拆分为多次提交
```

### 开发效率指标

| 指标 | 目标值 | 警戒值 |
|-----|-------|-------|
| 单次提交文件数 | < 3个 | > 5个 |
| 单次提交代码行数 | < 200行 | > 500行 |
| 提交频率 | 每2小时至少1次 | > 4小时无提交 |
| 回归测试通过率 | 100% | < 100% |

**质量指标**：测试覆盖率 > 80%、代码review通过率 100%、用户测试通过率 > 95%

📚 详细示例：参见 `prd/02_约束与原则/INCREMENTAL_DEVELOPMENT_GUIDE.md`

---

## 必读文档

开发任何功能前，必须阅读以下文档：

### 1. 约束与原则（最高优先级）
- `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` - 核心约束与开发原则
- `prd/02_约束与原则/TECHNICAL_CONSTRAINTS.md` - 技术约束详细说明
- `prd/02_约束与原则/coze.md` - Coze API 使用约束和规范

### 2. 全局指导
- `prd/01_全局指导/prd.md` - 主PRD文档，系统需求定义和开发流程规范
- `prd/01_全局指导/PRD_COMPLETE_v3.0.md` - 完整版PRD，详细功能规格
- `prd/01_全局指导/README.md` - 项目概述和快速入门

### 3. 技术方案
- `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md` - 技术架构方案
- `prd/03_技术方案/api_contract.md` - API 接口契约文档

### 4. 任务拆解
- `prd/04_任务拆解/IMPLEMENTATION_TASKS_v1.0.md` - 总体任务拆解
- `prd/04_任务拆解/backend_tasks.md` - 后端开发任务
- `prd/04_任务拆解/frontend_client_tasks.md` - 用户端前端任务
- `prd/04_任务拆解/agent_workbench_tasks.md` - 坐席工作台任务
- `prd/04_任务拆解/admin_management_tasks.md` - 管理员功能任务拆解
- `prd/04_任务拆解/email_and_monitoring_tasks.md` - 邮件和监控任务

### 5. 验收与记录
- `prd/05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md` - 详细验收标准
- `prd/05_验收与记录/TESTING_GUIDE.md` - 测试流程规范
- `prd/05_验收与记录/implementation_notes.md` - 实施过程笔记
- `prd/05_验收与记录/PRD_REVIEW.md` - PRD 评审记录
- `prd/05_验收与记录/DOCUMENTATION_SUMMARY.md` - 文档总结

### 6. 企业部署
- `prd/06_企业部署/ENTERPRISE_DEPLOYMENT_PRD.md` - 企业级部署需求
- `prd/06_企业部署/DEPLOYMENT_TASKS.md` - 部署开发任务拆解

---

## 核心铁律

### 铁律 1: 不可修改的核心接口

以下接口是系统基石，**严禁修改其核心逻辑**：

```
🔴 不可修改:
- POST /api/chat              (同步AI对话)
- POST /api/chat/stream       (流式AI对话)
- POST /api/conversation/new  (创建会话)
```

**允许的操作**:
- ✅ 在调用前添加前置检查（如状态检查）
- ✅ 在返回后添加后置处理（如日志记录）
- ❌ **禁止**修改 Coze API 调用方式
- ❌ **禁止**修改返回的数据结构
- ❌ **禁止**修改 payload 的必需字段格式

### 铁律 2: Coze API 调用规范

#### 必须使用 SSE 流式响应

```python
# ✅ 正确 - 使用 stream() 方法
with http_client.stream('POST', url, json=payload, headers=headers) as response:
    for line in response.iter_lines():
        # 解析SSE流

# ❌ 错误 - Coze返回的是SSE流,不是JSON!
response = http_client.post(...)
data = response.json()
```

#### 必须从顶层提取字段

```python
# ✅ 正确
event_data = json.loads(data_content)
if event_data.get("type") == "answer":
    content = event_data["content"]

# ❌ 错误 - Coze不返回嵌套结构
content = event_data["message"]["content"]
```

#### 必需的请求参数

```python
payload = {
    "workflow_id": WORKFLOW_ID,      # 必需
    "app_id": APP_ID,                # 必需
    "session_name": session_id,      # 必需 - 会话隔离
    "additional_messages": [...],    # 必需
    "conversation_id": conv_id,      # 可选(多轮对话需要)
}
```

### 铁律 3: OAuth + JWT 鉴权机制

```python
# ✅ 正确 - 使用 token_manager
access_token = token_manager.get_access_token(
    session_name=session_id  # 必须包含session_name实现隔离
)

# ❌ 错误 - 硬编码Token
access_token = "hardcoded_token"

# ❌ 错误 - 所有用户共用一个Token
access_token = token_manager.get_access_token()  # 缺少session_name!
```

### 铁律 4: 会话隔离机制

**强制要求**：基于 `session_name` 实现会话隔离，conversation_id 由 Coze 自动管理

**核心原理** (详见 `docs/process/会话隔离实现总结.md`):
1. ✅ **首次对话不传 conversation_id**，由 Coze 自动生成
2. ✅ **后续对话传入相同的 conversation_id** 维持上下文
3. ✅ **验证标准**: 不同 session_name 获得不同的 conversation_id

```python
# ✅ 正确方式 - Coze 自动管理 conversation_id
@app.post("/api/chat")
async def chat(request: ChatRequest):
    session_id = request.user_id or generate_user_id()
    access_token = token_manager.get_access_token(session_name=session_id)
    conversation_id = conversation_cache.get(session_id)

    payload = {
        "workflow_id": WORKFLOW_ID,
        "app_id": APP_ID,
        "session_name": session_id,  # ← 关键！会话隔离核心
        "parameters": {"USER_INPUT": request.message}
    }

    if conversation_id:
        payload["conversation_id"] = conversation_id

    response = httpx.post(url, json=payload, headers=headers)

    if not conversation_id and returned_conversation_id:
        conversation_cache[session_id] = returned_conversation_id

# ❌ 错误方式 - 手动生成 conversation_id
conversation_id = f"conv_{uuid.uuid4()}"  # 禁止！
```

**关键约束**:
- ❌ 禁止手动生成 conversation_id
- ❌ 禁止修改 conversation_id 管理逻辑
- ✅ 必须保存 Coze 返回的 conversation_id
- ✅ 必须在 JWT 和 API payload 中都传入 session_name

### 铁律 5: 状态机约束

```
bot_active → pending_manual → manual_live → bot_active
```

- 状态转换必须按顺序，不可跳跃
- 人工接管期间**必须阻止 AI 对话**（返回 409）
- `conversation_id` 由 Coze 自动生成，**禁止手动创建**

---

## 开发流程规范

### 阶段1: 开发前审查

#### 1.1 开发进度管理要求

**进度查询规范**：
- 查询开发进度时，**优先从 `prd/04_任务拆解/` 文件夹下搜索**
- 每个模块对应一个独立的 `.md` 文件
- 文件命名格式：`{模块名称}_tasks.md`

**任务拆解文件结构要求**：

```markdown
# {模块名称}功能需求文档与任务拆解

> 文档版本: v{版本号}
> 状态: ✅ P0 已完成 / ⚠️ P0 开发中 / ❌ P0 待开发
> 更新时间: YYYY-MM-DD

## 1. 功能列表
| 功能ID | 功能名称 | 优先级 | 状态 | 完成时间 |

## 2. 当前模块开发进度
## 3. 技术方案（同步到 prd/03_技术方案/）
## 4. 约束与原则（同步到 prd/02_约束与原则/）
## 5. API 接口（同步到 prd/03_技术方案/api_contract.md）
## 6. 验收标准
```

**同步更新要求**：

| 更新内容 | 同步位置 |
|---------|---------|
| 技术方案 | `prd/03_技术方案/{模块名称}_solution.md` 或 `TECHNICAL_SOLUTION_v1.0.md` |
| 约束与原则 | `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md` |
| API 接口 | `prd/03_技术方案/api_contract.md` |
| 任务进度 | `prd/04_任务拆解/{模块名称}_tasks.md` |

#### 1.2 版本号规范

**版本号格式**: `v主版本.次版本.补丁版本`（如 v3.8.1）

1. **补丁版本（第三位）** - 日常功能开发和Bug修复
   - **触发条件**: 常规功能开发、Bug修复、小优化
   - **更新方式**: 只更新第三位数字（如 v3.8.1 → v3.8.2）

2. **次版本（第二位）** - 用户明确要求的大版本更新
   - **触发条件**: 用户明确说"更新一个大版本"
   - **更新方式**: 更新第二位数字，第三位归零（如 v3.8.3 → v3.9.0）

3. **主版本（第一位）** - 重大架构变更（极少使用）
   - **触发条件**: 系统架构重大变更、不兼容更新
   - **更新方式**: 更新第一位数字，后两位归零（如 v3.9.0 → v4.0.0）

**重要约束**：
- ❌ **禁止**自行决定更新次版本（第二位）
- ✅ **默认**每次开发完成后更新补丁版本（第三位）
- ✅ **仅当用户明确要求**时才更新次版本（第二位）

#### 1.3 约束文档审查清单

- [ ] 阅读 `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- [ ] 阅读 `prd/03_技术方案/TECHNICAL_SOLUTION_v1.0.md`
- [ ] 确认新功能是否涉及 Coze API 调用
- [ ] 确认新功能是否会修改现有接口
- [ ] 检查是否引入新的外部依赖

#### 1.4 基线验证

```bash
# 在开始开发前，运行基线测试确保当前系统正常
./tests/regression_test.sh
# 预期: 全部通过，否则不得开始新功能开发
```

#### 1.5 设计审查

- [ ] 新功能是否遵循"前置检查 + 后置处理"模式？
- [ ] 新功能失败时是否会影响核心 AI 对话？（必须是"否"）
- [ ] 是否需要添加新的约束条款？

### 阶段2: 开发中约束

#### 2.1 代码实现检查清单

- [ ] 新增代码是否遵循现有代码风格？
- [ ] 是否添加了充足的错误处理？
- [ ] 新功能失败时是否会阻塞核心功能？（不应阻塞）
- [ ] 是否添加了结构化日志记录？
- [ ] 敏感信息是否已脱敏？

#### 2.2 正确的扩展模式

```python
# ✅ 正确 - 前置检查，不修改核心逻辑
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 【新增】前置检查
    if session_state.status in [PENDING_MANUAL, MANUAL_LIVE]:
        raise HTTPException(status_code=409, detail="MANUAL_IN_PROGRESS")

    # 原有 Coze API 调用逻辑（完全不动）
    access_token = token_manager.get_access_token(session_name=session_id)
    # ...
```

#### 2.3 编写自动化测试

**创建测试脚本**：
```bash
# 命名规范: tests/test_{功能名称}.sh 或 tests/test_{功能名称}.py
tests/test_admin_apis.sh           # 管理员功能测试
tests/test_customer_profile.sh     # 客户画像测试
tests/test_session_tags.sh         # 会话标签测试
```

**测试脚本要求**：
- ✅ 覆盖新功能的所有核心API
- ✅ 包含正常场景测试（Happy Path）
- ✅ 包含异常场景测试（错误处理、边界条件）
- ✅ 验证返回数据格式、字段完整性和状态码
- ✅ 测试权限控制（如适用）
- ✅ 输出清晰的测试结果（✅ PASS / ❌ FAIL）

**测试示例模板**：
```bash
#!/bin/bash
BASE_URL="http://localhost:8000"
PASSED=0
FAILED=0

echo "测试1: 创建资源 - 正常场景"
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/api/resource" \
  -H "Content-Type: application/json" \
  -d '{"name": "test"}')

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
if [ "$HTTP_CODE" -eq 200 ]; then
    echo "✅ PASS"
    ((PASSED++))
else
    echo "❌ FAIL - 预期200，实际$HTTP_CODE"
    ((FAILED++))
fi

echo "========================================"
echo "通过: $PASSED / 失败: $FAILED"
[ $FAILED -eq 0 ] && exit 0 || exit 1
```

#### 2.4 自测环节

**强制要求**：在通知用户进行 UI 测试之前，开发者必须先进行自测

**自测流程**：
- ✅ 检查代码是否编译通过（TypeScript 类型检查）
- ✅ 检查前端服务是否能正常启动（npm run dev）
- ✅ 检查浏览器控制台是否有错误
- ✅ 测试核心功能是否可用
- ✅ 确认没有明显的 UI 渲染问题

```bash
# 1. TypeScript 类型检查
cd agent-workbench && npx vue-tsc --noEmit

# 2. 启动前端服务
npm run dev
# 预期: 服务正常启动在 http://localhost:5174
```

**自测通过标准**：无编译错误、无类型错误、前端服务正常运行、核心功能可用、无控制台错误

**自测失败处理**：如发现错误，立即修复，重新自测。不得将有明显错误的代码提交给用户测试。

#### 2.5 UI 手动测试

**强制要求**：对于涉及前端UI的功能，必须先经过自测，然后通知用户进行 UI 手动测试

**流程**：
1. 自测通过后，提交代码到Git，标记为"待UI验证"
2. 通知用户进行UI手动测试
3. 等待用户确认UI功能正常
4. 用户确认后，才能集成到回归测试

**适用场景**：前端界面改动、用户交互流程变更、视觉效果优化

**不适用场景**（直接集成回归测试）：纯后端API功能、Bug修复、性能优化

#### 2.6 集成到回归测试

**强制要求**：
- 纯后端功能：API测试通过后，直接集成到 `tests/regression_test.sh`
- 前端功能：必须经过自测和用户UI测试确认后，才能集成到回归测试

```bash
# 编辑 tests/regression_test.sh，添加新功能测试
echo "测试 15: 客户画像功能"
bash tests/test_customer_profile.sh
if [ $? -eq 0 ]; then
    echo "✅ 客户画像功能测试通过"
    ((passed++))
else
    echo "❌ 客户画像功能测试失败"
    ((failed++))
fi
((total++))
```

### 阶段3: 开发后验证

#### 3.1 回归测试验证

```bash
cd /home/yzh/AI客服/鉴权
./tests/regression_test.sh
# 预期: 所有测试通过（包括新增的功能测试）
```

**验证要求**：
1. 核心对话功能不受影响
2. 会话隔离机制完整
3. 错误隔离：新功能异常不导致核心功能失败
4. 新功能测试已集成到回归测试中

#### 3.2 开发完成检查清单

- [ ] 新功能测试脚本已创建并验证通过
- [ ] 测试脚本已集成到 `tests/regression_test.sh`
- [ ] 回归测试全部通过
- [ ] `prd/04_任务拆解/{模块名称}_tasks.md` 状态已更新
- [ ] 新增约束已写入 `prd/02_约束与原则/`
- [ ] 新增API已写入 `prd/03_技术方案/api_contract.md`
- [ ] Git commit 完成并已推送，commit message 包含进度信息
- [ ] 已打版本tag

---

## 允许的扩展方向

以下功能**完全自由设计**，不受 Coze 平台限制：

1. **会话状态管理** (`src/session_state.py`) - 可自由定义状态枚举、添加任意字段、自定义数据模型
2. **监管引擎** (`src/regulator.py`) - 关键词检测规则、AI 失败计数逻辑、自动升级触发条件
3. **新增 API 接口** - 人工接管相关接口、统计查询接口、坐席管理接口
4. **SSE 事件扩展** - 可添加新的事件类型（如 `type:'manual_message'`），不得替换核心 AI 对话的 SSE 流

---

## 项目结构

```
/home/yzh/AI客服/鉴权/
├── backend.py              # 后端主服务
├── src/                    # 后端模块
│   ├── session_state.py    # 会话状态机
│   ├── regulator.py        # 监管引擎
│   ├── shift_config.py     # 工作时间配置
│   ├── email_service.py    # 邮件服务
│   └── oauth_token_manager.py  # Token管理
├── frontend/               # 用户端 Vue 项目
├── agent-workbench/        # 坐席工作台 Vue 项目
├── prd/                    # PRD 文档
│   └── INDEX.md            # 文档索引
└── tests/                  # 测试脚本
    └── regression_test.sh  # 回归测试
```

---

## 常用命令

### 启动服务

```bash
# 启动后端
python3 backend.py
# 访问: http://localhost:8000
# API文档: http://localhost:8000/docs

# 启动用户端
cd frontend && npm run dev
# 访问: http://localhost:5173

# 启动坐席工作台
cd agent-workbench && npm run dev
# 访问: http://localhost:5174
# 默认账号: admin/admin123, agent001/agent123
```

### 端口管理规范

| 服务 | 端口 | 说明 |
|------|------|------|
| 后端 API | 8000 | FastAPI 后端服务 |
| 用户端 | 5173 | 客户聊天界面 |
| 坐席工作台 | 5174 | 坐席管理系统（必须） |

**强制要求**：
- ✅ 坐席工作台必须运行在 5174 端口
- ✅ 如果端口被占用，必须先清除旧进程
- ❌ 禁止让 Vite 自动切换到其他端口（5175、5176等）

```bash
# 端口被占用时的处理
pkill -f "agent-workbench.*vite"
sleep 2
lsof -i :5174 || echo "✅ 端口 5174 已释放"
cd agent-workbench && npm run dev
```

### 前端 API 地址配置规范

**所有前端项目中的 API 调用必须使用环境变量配置，禁止硬编码地址！**

```javascript
// ✅ 正确 - 使用环境变量
const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'
const response = await fetch(`${API_BASE}/api/quick-replies`)

// ❌ 错误 - 硬编码地址
const response = await fetch('http://localhost:8000/api/quick-replies')
```

环境变量配置（`.env` 文件）：
```bash
VITE_API_BASE=http://localhost:8000
```

### 测试命令

```bash
./tests/regression_test.sh              # 回归测试
curl http://localhost:8000/api/health   # 健康检查
curl http://localhost:8000/api/sessions/stats  # 会话统计
```

---

## 环境变量 (.env)

关键配置：
- `COZE_WORKFLOW_ID` - 工作流ID
- `COZE_APP_ID` - 应用ID
- `COZE_OAUTH_CLIENT_ID` - OAuth客户端ID
- `REGULATOR_KEYWORDS` - 人工接管触发关键词
- `REGULATOR_FAIL_THRESHOLD` - AI连续失败阈值
- `JWT_SECRET_KEY` - JWT密钥（生产环境必须使用强随机密钥）

---

## 坐席认证与权限约束

### 约束19: 字段级访问控制

**坐席只能修改自己的 name 和 avatar_url**

```python
# ✅ 正确 - 只允许修改非敏感字段
@app.put("/api/agent/profile")
async def update_profile(request: UpdateProfileRequest, agent: Dict = Depends(require_agent)):
    if request.name is not None:
        current_agent.name = request.name
    if request.avatar_url is not None:
        current_agent.avatar_url = request.avatar_url

# ❌ 错误 - 允许修改敏感字段
for key, value in request_data.items():
    setattr(current_agent, key, value)
```

**禁止修改的字段**：`role`, `username`, `max_sessions`, `status`, `created_at`, `last_login`, `password_hash`

**允许修改**：`name` (1-50字符), `avatar_url` (URL字符串)

### 约束20: 密码修改安全性

**三重验证机制**：

```python
@app.post("/api/agent/change-password")
async def change_password(request: ChangePasswordRequest, agent: Dict = Depends(require_agent)):
    # 验证1: 旧密码正确性
    if not PasswordHasher.verify_password(request.old_password, current_agent.password_hash):
        raise HTTPException(400, "OLD_PASSWORD_INCORRECT")

    # 验证2: 新密码强度（至少8字符，包含字母和数字）
    if not validate_password(request.new_password):
        raise HTTPException(400, "INVALID_PASSWORD")

    # 验证3: 新旧密码不能相同
    if PasswordHasher.verify_password(request.new_password, current_agent.password_hash):
        raise HTTPException(400, "PASSWORD_SAME")
```

**生产环境基准值**：最小密码长度 8 字符，必须包含字母 + 数字，禁止新旧密码相同

### 约束21: JWT 权限分级

**三级权限模型**：

```python
@app.get("/api/agents")  # 管理员功能
async def get_agents(admin: Dict = Depends(require_admin)):
    pass

@app.post("/api/agent/change-password")  # 任何登录用户
async def change_password(agent: Dict = Depends(require_agent)):
    pass

@app.post("/api/chat")  # 用户端 API 无需认证
async def chat(request: ChatRequest):
    pass
```

| 权限 | 适用对象 | 典型API |
|------|---------|---------|
| 无需认证 | 用户端前端 | `/api/chat`, `/api/manual/escalate` |
| `require_agent()` | 任何登录坐席 | 修改密码、修改资料、会话查询 |
| `require_admin()` | 管理员 | 坐席CRUD、密码重置、权限管理 |

**生产环境基准值**：
- Token过期时间：1小时（Access Token）
- Refresh Token：7天
- 401 错误：Token无效或过期
- 403 错误：权限不足

---

## 禁止事项

1. **不要修改** `.env` 中的 Coze 凭证
2. **不要删除** 任何现有的 API 端点
3. **不要修改** Coze API 的调用方式和返回解析
4. **不要绕过** token_manager 直接生成 Token
5. **不要使用** WebSocket 替换 SSE 流式响应
6. **不要跳过** 回归测试就提交代码
7. **不要在** 人工接管期间允许 AI 对话
8. **不要允许** 坐席修改自己的 role、username、max_sessions 等敏感字段
9. **不要跳过** 旧密码验证直接修改密码
10. **不要混用** JWT 权限级别（如用 require_agent 保护管理员 API）
11. **不要自动** 执行 git commit、git push 操作，除非用户明确要求提交或推送

---

## 企业生产环境要求

### 1. 并发性要求

#### 1.1 连接池管理

```python
# ✅ 正确 - 使用连接池限制并发连接数
redis_pool = redis.ConnectionPool(
    host='localhost',
    port=6379,
    max_connections=50,
    socket_timeout=5.0,
    socket_connect_timeout=5.0,
    socket_keepalive=True
)

# ❌ 错误 - 无限制创建连接
for i in range(1000):
    redis_client = redis.Redis(host='localhost')
```

**生产环境基准值**：
- Redis 连接池：50 连接
- HTTP 客户端连接池：100 连接
- 数据库连接池：20-50 连接

#### 1.2 请求速率限制

```python
# ✅ 正确 - 实现速率限制
@app.post("/api/chat")
@limiter.limit("20/minute")
async def chat(request: ChatRequest):
    pass
```

**生产环境基准值**：普通用户 20 请求/分钟，VIP 用户 100 请求/分钟，坐席账号无限制

#### 1.3 并发 SSE 连接管理

```python
MAX_SSE_PER_USER = 3  # 每个用户最多3个并发 SSE 连接

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    if sse_connections.get(session_id, 0) >= MAX_SSE_PER_USER:
        raise HTTPException(429, "Too many concurrent connections")
```

**生产环境基准值**：每用户最多 3 个并发 SSE 连接，全局最大 1000，超时 5 分钟自动断开

#### 1.4 消息队列长度限制

```python
# ✅ 正确 - 限制队列长度
sse_queues[session_id] = asyncio.Queue(maxsize=100)
```

### 2. 实时性要求

#### 2.1 SSE 优于轮询

**强制要求**：所有实时更新必须使用 SSE，禁止使用短轮询

```typescript
// ✅ 正确 - 使用 SSE 实时推送
const eventSource = new EventSource(`/api/chat/stream`)

// ❌ 错误 - 使用轮询
setInterval(async () => {
  await fetch('/api/sessions/stats')
}, 5000)
```

#### 2.2 消息推送延迟要求

```python
# ✅ 正确 - 立即推送消息，不缓冲
if session_name in sse_queues:
    await sse_queues[session_name].put({
        "type": "manual_message",
        "content": request.get("content"),
        "timestamp": time.time()
    })
```

**生产环境基准值**：
- 人工消息推送延迟：< 100ms
- 状态变化通知延迟：< 50ms
- AI 响应流式推送：< 50ms 首字延迟

#### 2.3 前端响应性能

```typescript
// ✅ 正确 - 超过100条消息时启用虚拟滚动
<VirtualList :items="messages" :item-height="80" v-if="messages.length > 100">
```

**性能目标**：消息列表滚动 60 FPS，新消息追加 < 16ms，支持 10,000+ 条消息

#### 2.4 Coze API 超时设置

```python
HTTP_TIMEOUT = httpx.Timeout(
    connect=5.0,   # 连接超时 5秒
    read=30.0,     # 读取超时 30秒
    write=10.0,    # 写入超时 10秒
    pool=10.0      # 连接池超时 10秒
)
```

### 3. 资源限制与监控

#### 3.1 内存限制

```python
# redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru

# 会话数据 TTL
REDIS_SESSION_TTL = 86400  # 24 小时自动过期
```

#### 3.2 性能监控

```python
@app.middleware("http")
async def log_slow_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    if duration > 1.0:
        logger.warning(f"慢请求: {request.method} {request.url.path} 耗时 {duration:.2f}s")
    return response
```

**监控指标**：API 响应时间 P50 < 200ms, P99 < 1s，SSE 连接数实时监控，Redis 内存 < 80%，CPU < 70%

### 4. 生产环境检查清单

**并发性检查**：
- [ ] Redis 连接池大小配置（建议 50）
- [ ] HTTP 客户端使用连接池
- [ ] SSE 连接数限制（建议每用户 3 个）
- [ ] 消息队列长度限制（建议 100）
- [ ] 实现速率限制

**实时性检查**：
- [ ] 使用 SSE 替代轮询
- [ ] 消息推送立即执行
- [ ] 超时配置合理（连接 5s，读取 30s）
- [ ] 前端使用虚拟滚动（> 100 条消息）
- [ ] 性能监控

### 5. 典型场景性能要求

| 场景 | 并发要求 | 实时性要求 |
|-----|---------|-----------|
| 用户发送消息 | 100+ 并发 | AI 响应 < 2s |
| 坐席接入会话 | 10 坐席同时 | 状态通知 < 50ms |
| 人工消息推送 | 50+ 并发会话 | 推送延迟 < 100ms |
| 会话列表刷新 | 10 坐席同时 | SSE 自动更新 |
| 历史消息加载 | 1000+ 条消息 | 首屏 < 500ms |

---

## 文档索引

完整文档结构见 `prd/INDEX.md`

```
prd/
├── 01_全局指导/     # 系统需求和指导
├── 02_约束与原则/   # 技术约束（最重要)
├── 03_技术方案/     # 架构和API
├── 04_任务拆解/     # 开发任务
├── 05_验收与记录/   # 测试和验收
└── 06_企业部署/     # 部署相关
```

---

**文档版本**: v2.0
**最后更新**: 2025-12-09
