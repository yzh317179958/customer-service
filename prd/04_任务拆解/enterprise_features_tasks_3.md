# 企业级客服工作台功能任务拆解 - Phase 3 高级特性

> **文档版本**: v1.0
> **创建时间**: 2025-11-26
> **前置文档**: `enterprise_features_tasks.md` (Phase 1), `enterprise_features_tasks_2.md` (Phase 2)
> **关联文档**: `prd/01_全局指导/REFERENCE_SYSTEMS.md`
> **适用版本**: v3.7.0

---

## 📋 Phase 3 概览

**版本号**: v3.7.0
**预估工时**: 8周 (40个工作日)
**开发周期**: 预计2个月

**核心目标**:
- ✅ 多店铺管理
- ✅ 绩效报表系统
- ✅ 工单模板功能
- ✅ 消费数据统计
- ✅ 会话备注功能

**对标系统**:
- 聚水潭: 多店铺管理、绩效报表
- 拼多多: 消费数据统计
- Zendesk: 会话备注、工单模板

---

## 🎯 Phase 3: 高级特性 (v3.7.0 - 8周)

### 任务11: 多店铺管理 ⭐ P2

**当前状态**:
- ❌ 仅支持单店铺

**目标**:
支持Fiido多个独立站（欧洲站、美国站、亚洲站）统一管理

**功能需求**:

#### 11.1 店铺数据模型

```typescript
interface Store {
  id: string
  name: string
  domain: string          // fiido.de, fiido.com, fiido.cn
  region: 'europe' | 'america' | 'asia'
  currency: string        // EUR, USD, CNY
  timezone: string        // Europe/Berlin, America/New_York
  logo_url: string
  shopify_config: {
    store_name: string    // fiido-de.myshopify.com
    access_token: string
    api_version: string
  }
  is_active: boolean
  created_at: number
}

interface StoreAgent {
  agent_id: string
  store_ids: string[]     // 坐席可管理的店铺列表
  default_store_id: string  // 默认店铺
}
```

#### 11.2 店铺配置管理

**UI设计 - 管理员店铺配置**:
```
┌─────────────────────────────────────────────────────────┐
│ 店铺管理                                         [+ 新增]│
├─────────────────────────────────────────────────────────┤
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🇪🇺 Fiido Europe                         [编辑]  │   │
│ │ 域名: fiido.de                                    │   │
│ │ 地区: 欧洲  货币: EUR  时区: Europe/Berlin       │   │
│ │ Shopify: fiido-de.myshopify.com                  │   │
│ │ 状态: ✅ 活跃  坐席: 8人                          │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🇺🇸 Fiido America                        [编辑]  │   │
│ │ 域名: fiido.com                                   │   │
│ │ 地区: 美洲  货币: USD  时区: America/New_York    │   │
│ │ Shopify: fiido-us.myshopify.com                  │   │
│ │ 状态: ✅ 活跃  坐席: 5人                          │   │
│ └──────────────────────────────────────────────────┘   │
│                                                          │
│ ┌──────────────────────────────────────────────────┐   │
│ │ 🇨🇳 Fiido Asia                           [编辑]  │   │
│ │ 域名: fiido.cn                                    │   │
│ │ 地区: 亚洲  货币: CNY  时区: Asia/Shanghai       │   │
│ │ Shopify: fiido-cn.myshopify.com                  │   │
│ │ 状态: ⚠️  维护中  坐席: 3人                       │   │
│ └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

**UI设计 - 坐席端店铺切换**:
```
┌─────────────────────────────────────┐
│ 当前店铺: Fiido Europe       [切换▾]│
├─────────────────────────────────────┤
│ ✓ 🇪🇺 Fiido Europe                  │
│   🇺🇸 Fiido America                 │
│   🇨🇳 Fiido Asia                    │
└─────────────────────────────────────┘
```

#### 11.3 后端实现

```python
from typing import List

class Store(BaseModel):
    id: str
    name: str
    domain: str
    region: Literal['europe', 'america', 'asia']
    currency: str
    timezone: str
    logo_url: str
    shopify_config: dict
    is_active: bool = True
    created_at: float

class StoreService:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.store_key_prefix = "store:"

    async def create_store(self, store: Store) -> str:
        """创建店铺配置"""
        store_id = f"store_{int(time.time() * 1000)}"
        store.id = store_id
        store.created_at = time.time()

        await self.redis.set(
            f"{self.store_key_prefix}{store_id}",
            store.json(),
            ex=86400 * 365
        )

        # 添加到店铺索引
        await self.redis.sadd("stores:all", store_id)

        return store_id

    async def get_all_stores(self, active_only: bool = True) -> List[Store]:
        """获取所有店铺"""
        store_ids = await self.redis.smembers("stores:all")
        stores = []

        for store_id in store_ids:
            store_json = await self.redis.get(f"{self.store_key_prefix}{store_id}")
            if not store_json:
                continue

            store = Store.parse_raw(store_json)

            if active_only and not store.is_active:
                continue

            stores.append(store)

        return stores

    async def assign_agent_to_stores(
        self,
        agent_id: str,
        store_ids: List[str]
    ):
        """分配坐席到店铺"""
        await self.redis.set(
            f"agent:stores:{agent_id}",
            json.dumps({
                "store_ids": store_ids,
                "default_store_id": store_ids[0] if store_ids else None
            }),
            ex=86400 * 365
        )

    async def get_agent_stores(self, agent_id: str) -> List[str]:
        """获取坐席可管理的店铺"""
        data = await self.redis.get(f"agent:stores:{agent_id}")
        if not data:
            return []

        config = json.loads(data)
        return config.get("store_ids", [])

store_service = StoreService(redis_client)

# API接口
@app.get("/api/stores")
async def get_stores(
    active_only: bool = True,
    agent: dict = Depends(require_agent)
):
    """获取店铺列表"""
    # 管理员可以看所有店铺
    if agent["role"] == "admin":
        stores = await store_service.get_all_stores(active_only)
    else:
        # 普通坐席只能看分配给自己的店铺
        agent_store_ids = await store_service.get_agent_stores(agent["agent_id"])
        all_stores = await store_service.get_all_stores(active_only)
        stores = [s for s in all_stores if s.id in agent_store_ids]

    return {"stores": stores}

@app.post("/api/stores")
async def create_store(
    request: CreateStoreRequest,
    agent: dict = Depends(require_admin)
):
    """创建店铺配置（仅管理员）"""
    store = Store(
        id="",  # 自动生成
        name=request.name,
        domain=request.domain,
        region=request.region,
        currency=request.currency,
        timezone=request.timezone,
        logo_url=request.logo_url,
        shopify_config=request.shopify_config,
        is_active=True,
        created_at=0
    )

    store_id = await store_service.create_store(store)

    return {
        "success": True,
        "store_id": store_id
    }

@app.post("/api/agents/{agent_id}/stores")
async def assign_agent_stores(
    agent_id: str,
    request: AssignStoresRequest,
    admin: dict = Depends(require_admin)
):
    """分配坐席到店铺（仅管理员）"""
    await store_service.assign_agent_to_stores(agent_id, request.store_ids)
    return {"success": True}

# 会话API需要支持店铺过滤
@app.get("/api/sessions")
async def get_sessions(
    status: Optional[str] = None,
    store_id: Optional[str] = None,  # 新增店铺过滤
    agent: dict = Depends(require_agent)
):
    """获取会话列表（支持按店铺过滤）"""
    sessions = await session_store.get_all_sessions()

    # 过滤店铺
    if store_id:
        sessions = [s for s in sessions if s.store_id == store_id]

    # 过滤状态
    if status:
        sessions = [s for s in sessions if s.status == status]

    return {"sessions": sessions}
```

#### 11.4 会话数据模型调整

```python
# SessionState 需要添加 store_id 字段
class SessionState(BaseModel):
    session_name: str
    store_id: str  # ⭐ 新增字段
    user_id: Optional[str]
    status: SessionStatus
    assigned_agent: Optional[str]
    # ...其他字段
```

#### 11.5 前端实现

```vue
<template>
  <div class="multi-store-layout">
    <!-- 店铺切换下拉 -->
    <div class="store-selector">
      <el-select
        v-model="currentStoreId"
        placeholder="选择店铺"
        @change="handleStoreChange"
      >
        <el-option
          v-for="store in stores"
          :key="store.id"
          :label="store.name"
          :value="store.id"
        >
          <span class="store-flag">{{ getFlag(store.region) }}</span>
          <span>{{ store.name }}</span>
        </el-option>
      </el-select>
    </div>

    <!-- 会话列表（过滤当前店铺） -->
    <SessionList :store-id="currentStoreId" />

    <!-- 店铺统计信息 -->
    <div class="store-stats">
      <h3>{{ currentStore?.name }} 今日数据</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span>会话数</span>
          <strong>{{ storeStats.today_sessions }}</strong>
        </div>
        <div class="stat-item">
          <span>订单数</span>
          <strong>{{ storeStats.today_orders }}</strong>
        </div>
        <div class="stat-item">
          <span>转化率</span>
          <strong>{{ storeStats.conversion_rate }}%</strong>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { getStores, getStoreStats } from '@/api/stores'

const stores = ref([])
const currentStoreId = ref('')
const storeStats = ref({})

const currentStore = computed(() => {
  return stores.value.find(s => s.id === currentStoreId.value)
})

async function loadStores() {
  const { data } = await getStores()
  stores.value = data.stores

  // 默认选择第一个店铺
  if (stores.value.length > 0) {
    currentStoreId.value = stores.value[0].id
    loadStoreStats()
  }
}

async function loadStoreStats() {
  const { data } = await getStoreStats(currentStoreId.value)
  storeStats.value = data
}

function handleStoreChange() {
  loadStoreStats()
  // 刷新会话列表
}

function getFlag(region: string): string {
  const flags = {
    'europe': '🇪🇺',
    'america': '🇺🇸',
    'asia': '🇨🇳'
  }
  return flags[region] || '🌍'
}

onMounted(() => {
  loadStores()
})
</script>
```

**验收标准**:
- [ ] 管理员可创建/编辑/停用店铺
- [ ] 支持配置Shopify不同店铺
- [ ] 坐席可在多个店铺间切换
- [ ] 会话列表按店铺过滤
- [ ] 店铺独立统计数据
- [ ] 不同店铺显示对应logo
- [ ] 时区自动转换
- [ ] 货币自动转换
- [ ] 坐席权限控制（只能看分配的店铺）

**预估工时**: 5天

---

### 任务12: 绩效报表系统 ⭐ P2

**当前状态**:
- ✅ 实时数据统计 (任务9)
- ❌ 无历史报表

**目标**:
实现坐席绩效报表和导出功能

**功能需求**:

#### 12.1 绩效指标定义

```typescript
interface AgentPerformance {
  agent_id: string
  agent_name: string
  time_range: {
    start: number
    end: number
  }
  metrics: {
    // 接待指标
    total_sessions: number           // 总接待量
    avg_sessions_per_day: number     // 日均接待量
    completed_sessions: number       // 已完成会话数
    completion_rate: number          // 完成率 %

    // 响应指标
    avg_first_response_time: number  // 平均首次响应时间(秒)
    avg_response_time: number        // 平均响应时间(秒)
    response_rate: number            // 响应率 % (回复的会话/总会话)

    // 时长指标
    avg_session_duration: number     // 平均会话时长(秒)
    total_online_time: number        // 总在线时长(秒)
    utilization_rate: number         // 利用率 % (接待时长/在线时长)

    // 质量指标
    customer_satisfaction: number    // 客户满意度(0-5)
    satisfaction_count: number       // 评分人数
    resolution_rate: number          // 问题解决率 %

    // 业务指标
    conversion_rate: number          // 转化率 % (下单/咨询)
    ticket_created: number           // 创建工单数
    ticket_resolved: number          // 解决工单数
  }
  ranking: {
    sessions_rank: number            // 接待量排名
    satisfaction_rank: number        // 满意度排名
    response_rank: number            // 响应速度排名
  }
}
```

#### 12.2 UI设计 - 绩效报表

```
┌─────────────────────────────────────────────────────────────┐
│ 📊 坐席绩效报表                                              │
├─────────────────────────────────────────────────────────────┤
│ 时间范围: [本周▾]  自定义: [2024-11-20] 至 [2024-11-26]    │
│ 坐席筛选: [全部坐席▾]                            [导出Excel]│
├─────────────────────────────────────────────────────────────┤
│ ┌──────┬─────┬──────┬──────┬──────┬──────┬──────┬──────┐  │
│ │ 排名 │坐席 │接待量│响应  │时长  │满意度│转化率│评分  │  │
│ ├──────┼─────┼──────┼──────┼──────┼──────┼──────┼──────┤  │
│ │ 🥇 1 │小李 │ 156  │ 8.5s │ 12m  │ 4.9  │ 28%  │ 95   │  │
│ │ 🥈 2 │小王 │ 143  │ 12s  │ 15m  │ 4.7  │ 25%  │ 88   │  │
│ │ 🥉 3 │小张 │ 128  │ 15s  │ 18m  │ 4.5  │ 22%  │ 82   │  │
│ │    4 │小刘 │ 112  │ 18s  │ 20m  │ 4.3  │ 20%  │ 76   │  │
│ │    5 │小陈 │  98  │ 22s  │ 22m  │ 4.1  │ 18%  │ 70   │  │
│ └──────┴─────┴──────┴──────┴──────┴──────┴──────┴──────┘  │
│                                                              │
│ 📈 趋势图                                                    │
│ ┌────────────────────────────────────────────────────────┐ │
│ │  接待量                                                  │ │
│ │  160┤                                          ●        │ │
│ │  140┤                                     ●              │ │
│ │  120┤                                ●                   │ │
│ │  100┤                           ●                        │ │
│ │   80┤                      ●                             │ │
│ │     └──────────────────────────────────────────────     │ │
│ │      周一  周二  周三  周四  周五  周六  周日            │ │
│ └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

#### 12.3 后端实现

```python
from datetime import datetime, timedelta

class PerformanceService:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def calculate_agent_performance(
        self,
        agent_id: str,
        start_time: float,
        end_time: float
    ) -> AgentPerformance:
        """计算坐席绩效"""
        # 1. 获取时间范围内的会话
        all_sessions = await session_store.get_all_sessions()
        agent_sessions = [
            s for s in all_sessions
            if s.assigned_agent == agent_id and
               start_time <= s.created_at <= end_time
        ]

        # 2. 计算接待指标
        total_sessions = len(agent_sessions)
        completed_sessions = len([s for s in agent_sessions if s.status == 'ended'])
        completion_rate = (completed_sessions / total_sessions * 100) if total_sessions > 0 else 0

        days = (end_time - start_time) / 86400
        avg_sessions_per_day = total_sessions / days if days > 0 else 0

        # 3. 计算响应时间
        first_response_times = []
        response_times = []

        for session in agent_sessions:
            messages = session.messages
            if len(messages) < 2:
                continue

            # 首次响应时间
            user_msg_time = None
            agent_response_time = None
            for msg in messages:
                if msg['role'] == 'user' and user_msg_time is None:
                    user_msg_time = msg['timestamp']
                elif msg['role'] == 'assistant' and msg.get('agent_id') == agent_id and user_msg_time:
                    agent_response_time = msg['timestamp']
                    first_response_times.append(agent_response_time - user_msg_time)
                    break

            # 平均响应时间
            user_msg_time = None
            for msg in messages:
                if msg['role'] == 'user':
                    user_msg_time = msg['timestamp']
                elif msg['role'] == 'assistant' and msg.get('agent_id') == agent_id and user_msg_time:
                    response_times.append(msg['timestamp'] - user_msg_time)
                    user_msg_time = None

        avg_first_response_time = sum(first_response_times) / len(first_response_times) if first_response_times else 0
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        response_rate = (len(response_times) / total_sessions * 100) if total_sessions > 0 else 0

        # 4. 计算会话时长
        session_durations = []
        for session in agent_sessions:
            if session.messages and len(session.messages) >= 2:
                duration = session.messages[-1]['timestamp'] - session.messages[0]['timestamp']
                session_durations.append(duration)

        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0

        # 5. 在线时长（从登录记录计算）
        total_online_time = await self._calculate_online_time(agent_id, start_time, end_time)
        total_session_time = sum(session_durations)
        utilization_rate = (total_session_time / total_online_time * 100) if total_online_time > 0 else 0

        # 6. 质量指标（TODO: 需要实现满意度评分系统）
        customer_satisfaction = 4.7
        satisfaction_count = int(completed_sessions * 0.6)  # 假设60%的客户评分
        resolution_rate = 85.0  # TODO: 需要实现问题解决标记

        # 7. 业务指标
        # 转化率: 需要关联Shopify订单数据
        conversion_rate = await self._calculate_conversion_rate(agent_sessions)

        # 工单数据
        all_tickets = await ticket_store.get_all_tickets()
        agent_tickets = [t for t in all_tickets if t.assignee_id == agent_id]
        ticket_created = len([t for t in agent_tickets if start_time <= t.created_at <= end_time])
        ticket_resolved = len([t for t in agent_tickets if t.status == 'resolved' and start_time <= t.resolved_at <= end_time])

        # 8. 计算排名
        all_agents = await agent_store.get_all_agents()
        rankings = await self._calculate_rankings(all_agents, start_time, end_time)

        return AgentPerformance(
            agent_id=agent_id,
            agent_name=await self._get_agent_name(agent_id),
            time_range={"start": start_time, "end": end_time},
            metrics={
                "total_sessions": total_sessions,
                "avg_sessions_per_day": round(avg_sessions_per_day, 1),
                "completed_sessions": completed_sessions,
                "completion_rate": round(completion_rate, 1),
                "avg_first_response_time": round(avg_first_response_time, 1),
                "avg_response_time": round(avg_response_time, 1),
                "response_rate": round(response_rate, 1),
                "avg_session_duration": round(avg_session_duration, 1),
                "total_online_time": round(total_online_time, 1),
                "utilization_rate": round(utilization_rate, 1),
                "customer_satisfaction": customer_satisfaction,
                "satisfaction_count": satisfaction_count,
                "resolution_rate": resolution_rate,
                "conversion_rate": round(conversion_rate, 1),
                "ticket_created": ticket_created,
                "ticket_resolved": ticket_resolved
            },
            ranking=rankings.get(agent_id, {})
        )

    async def _calculate_online_time(
        self,
        agent_id: str,
        start_time: float,
        end_time: float
    ) -> float:
        """计算在线时长"""
        # 从Redis获取登录记录
        # 格式: agent:online:{agent_id} -> list of {"login": ts, "logout": ts}
        online_records_json = await self.redis.get(f"agent:online:{agent_id}")
        if not online_records_json:
            return 0

        online_records = json.loads(online_records_json)
        total_time = 0

        for record in online_records:
            login = record.get("login", 0)
            logout = record.get("logout", time.time())

            # 只计算时间范围内的在线时长
            if logout < start_time or login > end_time:
                continue

            actual_login = max(login, start_time)
            actual_logout = min(logout, end_time)
            total_time += (actual_logout - actual_login)

        return total_time

    async def _calculate_conversion_rate(self, sessions: List[SessionState]) -> float:
        """计算转化率"""
        # 需要关联Shopify订单数据
        # 判断客户在咨询后是否下单
        converted_count = 0

        for session in sessions:
            customer_email = session.customer_email
            if not customer_email:
                continue

            # 查询客户是否在会话后24小时内下单
            shopify_client = ShopifyClient()
            orders = await shopify_client.get_customer_orders(customer_email)

            for order in orders:
                order_time = order.created_at.timestamp()
                if session.created_at <= order_time <= session.created_at + 86400:
                    converted_count += 1
                    break

        return (converted_count / len(sessions) * 100) if sessions else 0

    async def _calculate_rankings(
        self,
        agents: List,
        start_time: float,
        end_time: float
    ) -> dict:
        """计算所有坐席排名"""
        agent_metrics = []

        for agent in agents:
            perf = await self.calculate_agent_performance(agent.agent_id, start_time, end_time)
            agent_metrics.append({
                "agent_id": agent.agent_id,
                "total_sessions": perf.metrics["total_sessions"],
                "customer_satisfaction": perf.metrics["customer_satisfaction"],
                "avg_response_time": perf.metrics["avg_response_time"]
            })

        # 按接待量排名
        sorted_by_sessions = sorted(agent_metrics, key=lambda x: x["total_sessions"], reverse=True)
        sessions_ranks = {item["agent_id"]: i + 1 for i, item in enumerate(sorted_by_sessions)}

        # 按满意度排名
        sorted_by_satisfaction = sorted(agent_metrics, key=lambda x: x["customer_satisfaction"], reverse=True)
        satisfaction_ranks = {item["agent_id"]: i + 1 for i, item in enumerate(sorted_by_satisfaction)}

        # 按响应速度排名（越小越好）
        sorted_by_response = sorted(agent_metrics, key=lambda x: x["avg_response_time"])
        response_ranks = {item["agent_id"]: i + 1 for i, item in enumerate(sorted_by_response)}

        # 组合排名
        rankings = {}
        for agent in agents:
            aid = agent.agent_id
            rankings[aid] = {
                "sessions_rank": sessions_ranks.get(aid, 0),
                "satisfaction_rank": satisfaction_ranks.get(aid, 0),
                "response_rank": response_ranks.get(aid, 0)
            }

        return rankings

performance_service = PerformanceService(redis_client)

# API接口
@app.get("/api/performance/agents")
async def get_agents_performance(
    start_time: Optional[float] = None,
    end_time: Optional[float] = None,
    agent_id: Optional[str] = None,
    admin: dict = Depends(require_admin)  # 仅管理员可查看
):
    """获取坐席绩效报表"""
    # 默认时间范围: 本周
    if not start_time or not end_time:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        start_of_week = today - timedelta(days=today.weekday())
        start_time = start_of_week.timestamp()
        end_time = time.time()

    # 如果指定agent_id，只返回该坐席
    if agent_id:
        perf = await performance_service.calculate_agent_performance(
            agent_id,
            start_time,
            end_time
        )
        return {"performance": [perf]}

    # 返回所有坐席
    all_agents = await agent_store.get_all_agents()
    performances = []

    for agent in all_agents:
        perf = await performance_service.calculate_agent_performance(
            agent.agent_id,
            start_time,
            end_time
        )
        performances.append(perf)

    # 按接待量排序
    performances.sort(key=lambda x: x.metrics["total_sessions"], reverse=True)

    return {"performances": performances}

@app.get("/api/performance/export")
async def export_performance_excel(
    start_time: float,
    end_time: float,
    admin: dict = Depends(require_admin)
):
    """导出绩效报表为Excel"""
    import pandas as pd
    from io import BytesIO

    # 获取绩效数据
    performances_data = await get_agents_performance(start_time, end_time)
    performances = performances_data["performances"]

    # 构建DataFrame
    data = []
    for i, perf in enumerate(performances):
        data.append({
            "排名": i + 1,
            "坐席": perf.agent_name,
            "接待量": perf.metrics["total_sessions"],
            "日均接待": perf.metrics["avg_sessions_per_day"],
            "完成率(%)": perf.metrics["completion_rate"],
            "首次响应(秒)": perf.metrics["avg_first_response_time"],
            "平均响应(秒)": perf.metrics["avg_response_time"],
            "平均时长(秒)": perf.metrics["avg_session_duration"],
            "在线时长(小时)": round(perf.metrics["total_online_time"] / 3600, 1),
            "利用率(%)": perf.metrics["utilization_rate"],
            "满意度": perf.metrics["customer_satisfaction"],
            "评分人数": perf.metrics["satisfaction_count"],
            "转化率(%)": perf.metrics["conversion_rate"],
            "创建工单": perf.metrics["ticket_created"],
            "解决工单": perf.metrics["ticket_resolved"]
        })

    df = pd.DataFrame(data)

    # 生成Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='坐席绩效', index=False)

    output.seek(0)

    # 返回文件
    from fastapi.responses import StreamingResponse
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=performance_{int(start_time)}_{int(end_time)}.xlsx"
        }
    )
```

#### 12.4 前端实现

```vue
<template>
  <div class="performance-report">
    <!-- 筛选条件 -->
    <div class="filters">
      <el-select v-model="timeRange" @change="handleTimeRangeChange">
        <el-option label="今日" value="today" />
        <el-option label="本周" value="week" />
        <el-option label="本月" value="month" />
        <el-option label="自定义" value="custom" />
      </el-select>

      <el-date-picker
        v-if="timeRange === 'custom'"
        v-model="customDateRange"
        type="daterange"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="loadPerformanceData"
      />

      <el-select v-model="selectedAgentId" placeholder="全部坐席" clearable>
        <el-option
          v-for="agent in agents"
          :key="agent.agent_id"
          :label="agent.name"
          :value="agent.agent_id"
        />
      </el-select>

      <el-button type="primary" :icon="Download" @click="exportExcel">
        导出Excel
      </el-button>
    </div>

    <!-- 绩效表格 -->
    <el-table :data="performances" stripe>
      <el-table-column label="排名" width="80">
        <template #default="{ $index }">
          <span v-if="$index === 0">🥇</span>
          <span v-else-if="$index === 1">🥈</span>
          <span v-else-if="$index === 2">🥉</span>
          <span v-else>{{ $index + 1 }}</span>
        </template>
      </el-table-column>

      <el-table-column prop="agent_name" label="坐席" width="100" />

      <el-table-column
        prop="metrics.total_sessions"
        label="接待量"
        width="90"
        sortable
      />

      <el-table-column
        label="响应时间"
        width="100"
        sortable
        :sort-method="(a, b) => a.metrics.avg_response_time - b.metrics.avg_response_time"
      >
        <template #default="{ row }">
          {{ row.metrics.avg_response_time }}s
        </template>
      </el-table-column>

      <el-table-column
        label="平均时长"
        width="100"
      >
        <template #default="{ row }">
          {{ formatDuration(row.metrics.avg_session_duration) }}
        </template>
      </el-table-column>

      <el-table-column
        prop="metrics.customer_satisfaction"
        label="满意度"
        width="100"
        sortable
      >
        <template #default="{ row }">
          <el-rate
            :model-value="row.metrics.customer_satisfaction"
            disabled
            show-score
            text-color="#ff9900"
          />
        </template>
      </el-table-column>

      <el-table-column
        prop="metrics.conversion_rate"
        label="转化率"
        width="90"
        sortable
      >
        <template #default="{ row }">
          {{ row.metrics.conversion_rate }}%
        </template>
      </el-table-column>

      <el-table-column
        label="综合评分"
        width="100"
        sortable
        :sort-method="calculateScore"
      >
        <template #default="{ row }">
          <el-tag :type="getScoreType(calculateScore(row))">
            {{ calculateScore(row) }}
          </el-tag>
        </template>
      </el-table-column>

      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="viewDetails(row)">
            查看详情
          </el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 趋势图 -->
    <div class="trend-charts">
      <h3>📈 趋势分析</h3>
      <div ref="chartContainer" style="height: 400px"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getAgentsPerformance, exportPerformanceExcel } from '@/api/performance'
import * as echarts from 'echarts'

const timeRange = ref('week')
const customDateRange = ref([])
const selectedAgentId = ref(null)
const performances = ref([])
const agents = ref([])

const chartContainer = ref()

async function loadPerformanceData() {
  const { start, end } = getTimeRange()

  const { data } = await getAgentsPerformance({
    start_time: start,
    end_time: end,
    agent_id: selectedAgentId.value
  })

  performances.value = data.performances

  // 绘制趋势图
  renderChart()
}

function getTimeRange() {
  const now = Date.now() / 1000
  const today = new Date().setHours(0, 0, 0, 0) / 1000

  switch (timeRange.value) {
    case 'today':
      return { start: today, end: now }
    case 'week':
      const weekStart = today - (new Date().getDay() * 86400)
      return { start: weekStart, end: now }
    case 'month':
      const monthStart = new Date().setDate(1) / 1000
      return { start: monthStart, end: now }
    case 'custom':
      return {
        start: customDateRange.value[0].getTime() / 1000,
        end: customDateRange.value[1].getTime() / 1000
      }
    default:
      return { start: today - 604800, end: now }
  }
}

function calculateScore(row): number {
  const m = row.metrics
  // 综合评分算法
  const score = (
    (m.total_sessions / 200 * 30) +  // 接待量权重30%
    (m.customer_satisfaction / 5 * 40) +  // 满意度权重40%
    ((30 - Math.min(m.avg_response_time, 30)) / 30 * 20) +  // 响应速度权重20%
    (m.conversion_rate / 100 * 10)  // 转化率权重10%
  )
  return Math.round(score)
}

function getScoreType(score: number): string {
  if (score >= 90) return 'success'
  if (score >= 80) return 'primary'
  if (score >= 70) return 'warning'
  return 'danger'
}

function renderChart() {
  const chart = echarts.init(chartContainer.value)

  const option = {
    title: {
      text: '接待量趋势'
    },
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: performances.value.map(p => p.agent_name)
    },
    xAxis: {
      type: 'category',
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
    },
    yAxis: {
      type: 'value'
    },
    series: performances.value.map(p => ({
      name: p.agent_name,
      type: 'line',
      data: [120, 132, 101, 134, 90, 230, 210]  // TODO: 实际数据
    }))
  }

  chart.setOption(option)
}

async function exportExcel() {
  const { start, end } = getTimeRange()
  window.open(`/api/performance/export?start_time=${start}&end_time=${end}`)
}

onMounted(() => {
  loadPerformanceData()
})
</script>
```

**验收标准**:
- [ ] 支持今日/本周/本月/自定义时间范围
- [ ] 显示12+个绩效指标
- [ ] 自动计算综合评分和排名
- [ ] 支持按指标排序
- [ ] 显示前三名奖牌图标
- [ ] 趋势图展示(ECharts)
- [ ] 导出Excel功能
- [ ] 仅管理员可查看全员数据
- [ ] 普通坐席只能查看自己数据

**预估工时**: 7天

---

### 任务13: 工单模板功能 ⭐ P2

**当前状态**:
- ✅ 基础工单CRUD (v3.4.0)
- ❌ 无工单模板

**目标**:
预设常见问题工单模板，快速创建

**功能需求**:

#### 13.1 工单模板数据模型

```typescript
interface TicketTemplate {
  id: string
  name: string
  category: string  // 对应工单分类
  description: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  default_fields: {
    title_template: string      // 标题模板
    description_template: string  // 描述模板
    custom_fields: Record<string, any>  // 自定义字段默认值
  }
  required_fields: string[]     // 必填字段
  suggested_sla_hours: number   // 建议SLA时长
  created_by: string
  created_at: number
  usage_count: number           // 使用次数统计
}
```

#### 13.2 预设模板

```typescript
const DEFAULT_TICKET_TEMPLATES = [
  {
    name: '退款申请',
    category: 'refund',
    description: '客户申请订单退款',
    priority: 'high',
    default_fields: {
      title_template: '退款申请 - 订单#{order_id}',
      description_template: `客户申请退款

订单信息:
- 订单号: {order_id}
- 商品: {product_name}
- 金额: {amount}
- 支付方式: {payment_method}

退款原因:
{refund_reason}

客户联系方式:
- 邮箱: {customer_email}
- 电话: {customer_phone}`,
      custom_fields: {
        'refund_type': '全额退款',
        'refund_method': '原路退回'
      }
    },
    required_fields: ['order_id', 'refund_reason', 'customer_email'],
    suggested_sla_hours: 24
  },
  {
    name: '换货申请',
    category: 'exchange',
    description: '客户申请商品换货',
    priority: 'medium',
    default_fields: {
      title_template: '换货申请 - 订单#{order_id}',
      description_template: `客户申请换货

原订单信息:
- 订单号: {order_id}
- 商品: {product_name}
- 规格: {variant}

换货原因:
{exchange_reason}

目标商品:
- 新规格: {new_variant}

物流信息:
- 退回快递: {return_tracking}`,
      custom_fields: {
        'exchange_type': '同款换货',
        'need_quality_check': true
      }
    },
    required_fields: ['order_id', 'exchange_reason', 'new_variant'],
    suggested_sla_hours: 48
  },
  {
    name: '质量问题',
    category: 'quality_issue',
    description: '产品质量问题报修',
    priority: 'high',
    default_fields: {
      title_template: '质量问题 - {product_name}',
      description_template: `产品质量问题

商品信息:
- 商品: {product_name}
- SKU: {sku}
- 购买日期: {purchase_date}

问题描述:
{issue_description}

故障现象:
{symptoms}

已尝试的解决方法:
{attempted_solutions}`,
      custom_fields: {
        'issue_type': '功能故障',
        'need_replacement': false
      }
    },
    required_fields: ['product_name', 'issue_description'],
    suggested_sla_hours: 72
  },
  {
    name: '物流异常',
    category: 'shipping_issue',
    description: '物流配送异常处理',
    priority: 'high',
    default_fields: {
      title_template: '物流异常 - 运单#{tracking_number}',
      description_template: `物流异常报告

订单信息:
- 订单号: {order_id}
- 运单号: {tracking_number}
- 物流公司: {carrier}

异常类型:
{issue_type}

当前状态:
{current_status}

客户诉求:
{customer_request}`,
      custom_fields: {
        'issue_type': '延迟配送',
        'compensation_needed': false
      }
    },
    required_fields: ['tracking_number', 'issue_type'],
    suggested_sla_hours: 24
  },
  {
    name: '技术咨询',
    category: 'technical_support',
    description: '产品技术问题咨询',
    priority: 'medium',
    default_fields: {
      title_template: '技术咨询 - {product_name}',
      description_template: `技术咨询

产品: {product_name}

咨询问题:
{question}

使用场景:
{usage_scenario}

期望解决方案:
{expected_solution}`,
      custom_fields: {
        'urgency': '不紧急',
        'need_callback': false
      }
    },
    required_fields: ['product_name', 'question'],
    suggested_sla_hours: 48
  },
  {
    name: '账户问题',
    category: 'account_issue',
    description: '账户登录或信息问题',
    priority: 'medium',
    default_fields: {
      title_template: '账户问题 - {customer_email}',
      description_template: `账户问题

客户邮箱: {customer_email}

问题类型:
{issue_type}

问题描述:
{issue_description}

已验证信息:
- 注册邮箱: {customer_email}
- 注册时间: {registration_date}
- 最后登录: {last_login}`,
      custom_fields: {
        'issue_type': '忘记密码',
        'verification_passed': false
      }
    },
    required_fields: ['customer_email', 'issue_type'],
    suggested_sla_hours: 24
  }
]
```

#### 13.3 后端实现

```python
class TicketTemplateStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.template_key_prefix = "ticket:template:"

    async def create_template(self, template: TicketTemplate) -> str:
        """创建工单模板"""
        template_id = f"tpl_{int(time.time() * 1000)}"
        template.id = template_id
        template.created_at = time.time()
        template.usage_count = 0

        await self.redis.set(
            f"{self.template_key_prefix}{template_id}",
            template.json(),
            ex=86400 * 365
        )

        await self.redis.sadd("ticket:templates:all", template_id)

        return template_id

    async def get_all_templates(self) -> List[TicketTemplate]:
        """获取所有模板"""
        template_ids = await self.redis.smembers("ticket:templates:all")
        templates = []

        for tid in template_ids:
            template_json = await self.redis.get(f"{self.template_key_prefix}{tid}")
            if template_json:
                templates.append(TicketTemplate.parse_raw(template_json))

        # 按使用次数排序
        templates.sort(key=lambda x: x.usage_count, reverse=True)

        return templates

    async def increment_usage(self, template_id: str):
        """增加模板使用次数"""
        template_json = await self.redis.get(f"{self.template_key_prefix}{template_id}")
        if not template_json:
            return

        template = TicketTemplate.parse_raw(template_json)
        template.usage_count += 1

        await self.redis.set(
            f"{self.template_key_prefix}{template_id}",
            template.json(),
            ex=86400 * 365
        )

ticket_template_store = TicketTemplateStore(redis_client)

# API接口
@app.get("/api/ticket-templates")
async def get_ticket_templates(
    category: Optional[str] = None,
    agent: dict = Depends(require_agent)
):
    """获取工单模板列表"""
    templates = await ticket_template_store.get_all_templates()

    if category:
        templates = [t for t in templates if t.category == category]

    return {"templates": templates}

@app.post("/api/ticket-templates")
async def create_ticket_template(
    request: CreateTicketTemplateRequest,
    agent: dict = Depends(require_admin)  # 仅管理员
):
    """创建工单模板"""
    template = TicketTemplate(
        id="",
        name=request.name,
        category=request.category,
        description=request.description,
        priority=request.priority,
        default_fields=request.default_fields,
        required_fields=request.required_fields,
        suggested_sla_hours=request.suggested_sla_hours,
        created_by=agent["agent_id"],
        created_at=0,
        usage_count=0
    )

    template_id = await ticket_template_store.create_template(template)

    return {
        "success": True,
        "template_id": template_id
    }

@app.post("/api/tickets/from-template")
async def create_ticket_from_template(
    request: CreateTicketFromTemplateRequest,
    agent: dict = Depends(require_agent)
):
    """
    从模板创建工单

    request.template_id: 模板ID
    request.variables: 变量替换值 {"order_id": "FD123", "refund_reason": "..."}
    request.session_name: 关联的会话（可选）
    """
    # 1. 获取模板
    template_json = await redis_client.get(f"ticket:template:{request.template_id}")
    if not template_json:
        raise HTTPException(404, "模板不存在")

    template = TicketTemplate.parse_raw(template_json)

    # 2. 验证必填字段
    for field in template.required_fields:
        if field not in request.variables:
            raise HTTPException(400, f"缺少必填字段: {field}")

    # 3. 替换变量
    title = template.default_fields["title_template"]
    description = template.default_fields["description_template"]

    for key, value in request.variables.items():
        title = title.replace(f"{{{key}}}", str(value))
        description = description.replace(f"{{{key}}}", str(value))

    # 4. 创建工单
    ticket = Ticket(
        ticket_id="",  # 自动生成
        title=title,
        description=description,
        category=template.category,
        priority=template.priority,
        status='open',
        session_name=request.session_name,
        customer_email=request.variables.get("customer_email"),
        assignee_id=agent["agent_id"],
        created_by=agent["agent_id"],
        created_at=time.time(),
        updated_at=time.time(),
        sla_deadline=time.time() + (template.suggested_sla_hours * 3600),
        custom_fields={
            **template.default_fields.get("custom_fields", {}),
            **request.variables
        }
    )

    ticket_id = await ticket_store.create_ticket(ticket)

    # 5. 增加模板使用次数
    await ticket_template_store.increment_usage(request.template_id)

    return {
        "success": True,
        "ticket_id": ticket_id
    }

# 初始化预设模板
@app.on_event("startup")
async def init_ticket_templates():
    """初始化预设模板"""
    existing_templates = await ticket_template_store.get_all_templates()
    if len(existing_templates) > 0:
        return  # 已初始化

    for tpl_data in DEFAULT_TICKET_TEMPLATES:
        template = TicketTemplate(
            id="",
            **tpl_data,
            created_by="system",
            created_at=time.time(),
            usage_count=0
        )
        await ticket_template_store.create_template(template)

    logger.info(f"Initialized {len(DEFAULT_TICKET_TEMPLATES)} ticket templates")
```

#### 13.4 前端实现

```vue
<template>
  <div class="ticket-templates">
    <!-- 模板选择器 -->
    <div class="template-selector">
      <h3>选择工单模板</h3>
      <div class="template-grid">
        <div
          v-for="template in templates"
          :key="template.id"
          class="template-card"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <h4>{{ template.name }}</h4>
            <el-tag :type="getPriorityType(template.priority)" size="small">
              {{ priorityText(template.priority) }}
            </el-tag>
          </div>
          <p class="template-description">{{ template.description }}</p>
          <div class="template-meta">
            <span>📊 使用 {{ template.usage_count }} 次</span>
            <span>⏱️ SLA: {{ template.suggested_sla_hours }}h</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 工单创建表单 -->
    <el-dialog
      v-model="showCreateDialog"
      :title="selectedTemplate?.name"
      width="60%"
    >
      <el-form
        ref="formRef"
        :model="formData"
        label-width="120px"
      >
        <!-- 动态渲染必填字段 -->
        <el-form-item
          v-for="field in selectedTemplate?.required_fields"
          :key="field"
          :label="getFieldLabel(field)"
          :prop="field"
          :rules="{ required: true, message: '此字段必填' }"
        >
          <!-- 订单号字段 - 自动补全 -->
          <el-autocomplete
            v-if="field === 'order_id'"
            v-model="formData[field]"
            :fetch-suggestions="searchOrders"
            placeholder="输入订单号搜索..."
            @select="handleOrderSelect"
          />

          <!-- 商品名称 - 下拉选择 -->
          <el-select
            v-else-if="field === 'product_name'"
            v-model="formData[field]"
            placeholder="选择商品"
            filterable
          >
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="product.title"
              :value="product.title"
            />
          </el-select>

          <!-- 其他文本字段 -->
          <el-input
            v-else
            v-model="formData[field]"
            :placeholder="`请输入${getFieldLabel(field)}`"
          />
        </el-form-item>

        <!-- 工单描述预览 -->
        <el-form-item label="工单描述">
          <div class="description-preview">
            {{ renderDescription() }}
          </div>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createTicket">
          创建工单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { getTicketTemplates, createTicketFromTemplate } from '@/api/tickets'
import { searchOrders } from '@/api/orders'

const templates = ref([])
const selectedTemplate = ref(null)
const showCreateDialog = ref(false)
const formData = reactive({})
const products = ref([])

async function loadTemplates() {
  const { data } = await getTicketTemplates()
  templates.value = data.templates
}

function selectTemplate(template) {
  selectedTemplate.value = template
  showCreateDialog.value = true

  // 重置表单数据
  Object.keys(formData).forEach(key => delete formData[key])

  // 填充默认值
  const customFields = template.default_fields.custom_fields || {}
  Object.assign(formData, customFields)
}

function getFieldLabel(field: string): string {
  const labels = {
    'order_id': '订单号',
    'product_name': '商品名称',
    'refund_reason': '退款原因',
    'exchange_reason': '换货原因',
    'issue_description': '问题描述',
    'tracking_number': '运单号',
    'customer_email': '客户邮箱',
    'question': '咨询问题'
  }
  return labels[field] || field
}

function renderDescription(): string {
  let description = selectedTemplate.value.default_fields.description_template

  // 替换变量
  for (const [key, value] of Object.entries(formData)) {
    description = description.replace(new RegExp(`\\{${key}\\}`, 'g'), value || `{${key}}`)
  }

  return description
}

async function createTicket() {
  const { data } = await createTicketFromTemplate({
    template_id: selectedTemplate.value.id,
    variables: formData,
    session_name: currentSession.value  // 关联当前会话
  })

  ElMessage.success('工单创建成功')
  showCreateDialog.value = false

  // 跳转到工单详情
  router.push(`/tickets/${data.ticket_id}`)
}

function priorityText(priority: string): string {
  const texts = {
    'low': '低',
    'medium': '中',
    'high': '高',
    'urgent': '紧急'
  }
  return texts[priority] || priority
}

function getPriorityType(priority: string): string {
  const types = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'urgent': 'danger'
  }
  return types[priority] || 'info'
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.template-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.template-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.template-description {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 12px;
}

.template-meta {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  color: #9ca3af;
}

.description-preview {
  background: #f9fafb;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  font-family: monospace;
  font-size: 13px;
}
</style>
```

**验收标准**:
- [ ] 预设6个常用工单模板
- [ ] 管理员可创建自定义模板
- [ ] 模板支持变量替换
- [ ] 必填字段验证
- [ ] 订单号自动补全
- [ ] 商品名称下拉选择
- [ ] 实时预览工单描述
- [ ] 统计模板使用次数
- [ ] 自动设置SLA截止时间
- [ ] 关联当前会话

**预估工时**: 4天

---

### 任务14: 消费数据统计 ⭐ P2

**当前状态**:
- ✅ Shopify客户订单列表
- ❌ 无消费统计分析

**目标**:
展示客户消费总额、客单价、复购率等数据

**功能需求**:

#### 14.1 消费数据指标

```typescript
interface CustomerConsumptionStats {
  customer_email: string
  customer_name: string

  // 消费指标
  total_amount: number          // 消费总额
  order_count: number           // 订单数量
  avg_order_value: number       // 客单价
  max_order_value: number       // 最大单笔金额
  min_order_value: number       // 最小单笔金额

  // 时间指标
  first_order_date: number      // 首次下单时间
  last_order_date: number       // 最近下单时间
  customer_lifetime_days: number  // 客户生命周期(天)

  // 行为指标
  repurchase_rate: number       // 复购率 %
  avg_days_between_orders: number  // 平均复购间隔(天)
  refund_count: number          // 退款次数
  refund_rate: number           // 退款率 %

  // 商品偏好
  favorite_products: {
    product_name: string
    purchase_count: number
    total_amount: number
  }[]

  // VIP等级
  vip_level: 'bronze' | 'silver' | 'gold' | 'platinum'
  vip_score: number             // VIP积分
}
```

#### 14.2 VIP等级规则

```typescript
function calculateVIPLevel(totalAmount: number, orderCount: number): {
  level: string
  score: number
} {
  let score = 0

  // 消费金额积分 (每€100 = 10分)
  score += (totalAmount / 100) * 10

  // 订单数量积分 (每单 = 5分)
  score += orderCount * 5

  // 根据积分确定等级
  let level = 'bronze'
  if (score >= 500) level = 'platinum'    // €5000+ 或 100单+
  else if (score >= 200) level = 'gold'   // €2000+ 或 40单+
  else if (score >= 50) level = 'silver'  // €500+ 或 10单+

  return { level, score }
}
```

#### 14.3 后端实现

```python
class ConsumptionStatsService:
    def __init__(self, shopify_client):
        self.shopify = shopify_client

    async def calculate_customer_stats(
        self,
        customer_email: str
    ) -> CustomerConsumptionStats:
        """计算客户消费统计"""
        # 1. 获取客户所有订单
        orders = await self.shopify.get_customer_orders(customer_email)

        if not orders:
            raise HTTPException(404, "未找到订单记录")

        # 2. 消费指标
        order_amounts = [float(order.total_price) for order in orders]
        total_amount = sum(order_amounts)
        order_count = len(orders)
        avg_order_value = total_amount / order_count if order_count > 0 else 0
        max_order_value = max(order_amounts) if order_amounts else 0
        min_order_value = min(order_amounts) if order_amounts else 0

        # 3. 时间指标
        order_dates = [order.created_at.timestamp() for order in orders]
        first_order_date = min(order_dates)
        last_order_date = max(order_dates)
        customer_lifetime_days = (last_order_date - first_order_date) / 86400

        # 4. 行为指标
        # 复购率: 订单数>1的客户占比 (这里简化为: 订单数>1则100%，否则0%)
        repurchase_rate = 100 if order_count > 1 else 0

        # 平均复购间隔
        if order_count > 1:
            sorted_dates = sorted(order_dates)
            intervals = [sorted_dates[i+1] - sorted_dates[i] for i in range(len(sorted_dates) - 1)]
            avg_days_between_orders = (sum(intervals) / len(intervals)) / 86400
        else:
            avg_days_between_orders = 0

        # 退款统计
        refund_orders = [
            order for order in orders
            if order.financial_status in ['refunded', 'partially_refunded']
        ]
        refund_count = len(refund_orders)
        refund_rate = (refund_count / order_count * 100) if order_count > 0 else 0

        # 5. 商品偏好
        product_stats = {}
        for order in orders:
            for item in order.line_items:
                product_name = item.name
                if product_name not in product_stats:
                    product_stats[product_name] = {
                        "product_name": product_name,
                        "purchase_count": 0,
                        "total_amount": 0
                    }
                product_stats[product_name]["purchase_count"] += item.quantity
                product_stats[product_name]["total_amount"] += float(item.price) * item.quantity

        # 按购买次数排序
        favorite_products = sorted(
            product_stats.values(),
            key=lambda x: x["purchase_count"],
            reverse=True
        )[:3]  # Top 3

        # 6. VIP等级
        vip_info = self._calculate_vip_level(total_amount, order_count)

        # 7. 获取客户基本信息
        customer = orders[0].customer
        customer_name = customer.first_name + " " + customer.last_name if customer else "Unknown"

        return CustomerConsumptionStats(
            customer_email=customer_email,
            customer_name=customer_name,
            total_amount=round(total_amount, 2),
            order_count=order_count,
            avg_order_value=round(avg_order_value, 2),
            max_order_value=max_order_value,
            min_order_value=min_order_value,
            first_order_date=first_order_date,
            last_order_date=last_order_date,
            customer_lifetime_days=round(customer_lifetime_days, 1),
            repurchase_rate=repurchase_rate,
            avg_days_between_orders=round(avg_days_between_orders, 1),
            refund_count=refund_count,
            refund_rate=round(refund_rate, 1),
            favorite_products=favorite_products,
            vip_level=vip_info["level"],
            vip_score=vip_info["score"]
        )

    def _calculate_vip_level(self, total_amount: float, order_count: int) -> dict:
        """计算VIP等级"""
        score = 0

        # 消费金额积分 (每€100 = 10分)
        score += (total_amount / 100) * 10

        # 订单数量积分 (每单 = 5分)
        score += order_count * 5

        # 确定等级
        if score >= 500:
            level = 'platinum'
        elif score >= 200:
            level = 'gold'
        elif score >= 50:
            level = 'silver'
        else:
            level = 'bronze'

        return {"level": level, "score": int(score)}

consumption_stats_service = ConsumptionStatsService(ShopifyClient())

# API接口
@app.get("/api/customers/{customer_email}/consumption-stats")
async def get_customer_consumption_stats(
    customer_email: str,
    agent: dict = Depends(require_agent)
):
    """获取客户消费统计"""
    stats = await consumption_stats_service.calculate_customer_stats(customer_email)
    return {"stats": stats}

@app.get("/api/customers/top-spenders")
async def get_top_spenders(
    limit: int = 20,
    time_range: str = 'all',  # 'all', 'month', 'quarter', 'year'
    agent: dict = Depends(require_admin)  # 仅管理员
):
    """获取消费排行榜"""
    # 获取所有客户
    shopify = ShopifyClient()
    all_customers = await shopify.get_all_customers()

    customer_stats = []
    for customer in all_customers:
        try:
            stats = await consumption_stats_service.calculate_customer_stats(customer.email)
            customer_stats.append(stats)
        except:
            continue

    # 按消费总额排序
    customer_stats.sort(key=lambda x: x.total_amount, reverse=True)

    return {"top_spenders": customer_stats[:limit]}
```

#### 14.4 前端实现

```vue
<template>
  <div class="consumption-stats">
    <h3>💰 消费数据统计</h3>

    <!-- VIP等级 -->
    <div class="vip-badge" :class="`vip-${stats.vip_level}`">
      <span class="vip-icon">{{ vipIcon(stats.vip_level) }}</span>
      <div class="vip-info">
        <h4>{{ vipLevelText(stats.vip_level) }}</h4>
        <p>积分: {{ stats.vip_score }}</p>
      </div>
    </div>

    <!-- 核心指标 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">消费总额</div>
        <div class="stat-value">€{{ stats.total_amount }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">订单数量</div>
        <div class="stat-value">{{ stats.order_count }}单</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">客单价</div>
        <div class="stat-value">€{{ stats.avg_order_value }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-label">复购率</div>
        <div class="stat-value">{{ stats.repurchase_rate }}%</div>
      </div>
    </div>

    <!-- 时间线 -->
    <div class="timeline-section">
      <h4>客户生命周期</h4>
      <div class="timeline">
        <div class="timeline-item">
          <span>首次购买</span>
          <strong>{{ formatDate(stats.first_order_date) }}</strong>
        </div>
        <div class="timeline-arrow">→</div>
        <div class="timeline-item">
          <span>最近购买</span>
          <strong>{{ formatDate(stats.last_order_date) }}</strong>
        </div>
        <div class="timeline-duration">
          {{ stats.customer_lifetime_days }} 天
        </div>
      </div>
    </div>

    <!-- 商品偏好 -->
    <div class="favorite-products">
      <h4>偏好商品 Top 3</h4>
      <div
        v-for="(product, index) in stats.favorite_products"
        :key="index"
        class="product-item"
      >
        <span class="product-rank">{{ index + 1 }}</span>
        <div class="product-info">
          <h5>{{ product.product_name }}</h5>
          <p>购买 {{ product.purchase_count }} 次 · €{{ product.total_amount }}</p>
        </div>
      </div>
    </div>

    <!-- 退款情况 -->
    <div v-if="stats.refund_count > 0" class="refund-warning">
      <el-alert
        type="warning"
        :title="`退款 ${stats.refund_count} 次 (${stats.refund_rate}%)`"
        :closable="false"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'

const props = defineProps<{
  stats: CustomerConsumptionStats
}>()

function vipLevelText(level: string): string {
  const texts = {
    'bronze': '青铜会员',
    'silver': '白银会员',
    'gold': '黄金会员',
    'platinum': '铂金会员'
  }
  return texts[level] || level
}

function vipIcon(level: string): string {
  const icons = {
    'bronze': '🥉',
    'silver': '🥈',
    'gold': '🥇',
    'platinum': '💎'
  }
  return icons[level] || '📊'
}

function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString('zh-CN')
}
</script>

<style scoped>
.consumption-stats {
  padding: 20px;
}

.vip-badge {
  display: flex;
  align-items: center;
  padding: 16px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.vip-badge.vip-bronze {
  background: linear-gradient(135deg, #cd7f32 0%, #d4a574 100%);
  color: white;
}

.vip-badge.vip-silver {
  background: linear-gradient(135deg, #c0c0c0 0%, #e8e8e8 100%);
  color: #333;
}

.vip-badge.vip-gold {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4e 100%);
  color: #333;
}

.vip-badge.vip-platinum {
  background: linear-gradient(135deg, #e5e4e2 0%, #ffffff 100%);
  color: #333;
  border: 2px solid #b9f2ff;
}

.vip-icon {
  font-size: 48px;
  margin-right: 16px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: white;
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}

.stat-label {
  color: #6b7280;
  font-size: 14px;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #111827;
}

.timeline {
  display: flex;
  align-items: center;
  gap: 16px;
  background: #f9fafb;
  padding: 16px;
  border-radius: 8px;
}

.timeline-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.timeline-arrow {
  font-size: 24px;
  color: #9ca3af;
}

.favorite-products {
  margin-top: 20px;
}

.product-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.product-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3b82f6;
  color: white;
  font-weight: bold;
}
</style>
```

**验收标准**:
- [ ] 显示消费总额、订单数量、客单价
- [ ] 显示复购率、平均复购间隔
- [ ] 显示退款次数和退款率
- [ ] 显示客户生命周期时间线
- [ ] 显示Top 3偏好商品
- [ ] VIP等级自动计算(青铜/白银/黄金/铂金)
- [ ] VIP等级渐变背景样式
- [ ] 退款异常红色提醒
- [ ] 消费排行榜(管理员可查看)

**预估工时**: 4天

---

### 任务15: 会话备注功能 ⭐ P2

**当前状态**:
- ❌ 无备注功能

**目标**:
坐席可添加内部备注，客户不可见

**功能需求**:

#### 15.1 备注数据模型

```typescript
interface SessionNote {
  id: string
  session_name: string
  content: string
  created_by: string
  created_at: number
  is_pinned: boolean       // 是否置顶
  mentioned_agents?: string[]  // @提及的坐席
}
```

#### 15.2 UI设计

```
┌─────────────────────────────────────┐
│ 会话备注 (内部可见)          [+ 添加]│
├─────────────────────────────────────┤
│ 📌 客户要求修改收货地址到慕尼黑      │
│    - 坐席小李 · 2024-11-26 14:30   │
│    [删除]                            │
├─────────────────────────────────────┤
│ @小王 请协助处理物流问题             │
│    - 坐席小张 · 2024-11-26 10:15   │
│    [删除]                            │
└─────────────────────────────────────┘
```

#### 15.3 后端实现

```python
class SessionNote(BaseModel):
    id: str
    session_name: str
    content: str
    created_by: str
    created_at: float
    is_pinned: bool = False
    mentioned_agents: List[str] = Field(default_factory=list)

class SessionNoteStore:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def add_note(self, note: SessionNote) -> str:
        """添加备注"""
        note_id = f"note_{int(time.time() * 1000)}"
        note.id = note_id
        note.created_at = time.time()

        # 保存备注
        await self.redis.hset(
            f"session:notes:{note.session_name}",
            note_id,
            note.json()
        )

        # 如果@了其他坐席，发送通知
        if note.mentioned_agents:
            for agent_id in note.mentioned_agents:
                await self._send_mention_notification(agent_id, note)

        return note_id

    async def get_notes(self, session_name: str) -> List[SessionNote]:
        """获取会话所有备注"""
        notes_dict = await self.redis.hgetall(f"session:notes:{session_name}")

        notes = [
            SessionNote.parse_raw(note_json)
            for note_json in notes_dict.values()
        ]

        # 置顶的在前，时间倒序
        notes.sort(key=lambda x: (not x.is_pinned, -x.created_at))

        return notes

    async def delete_note(self, session_name: str, note_id: str):
        """删除备注"""
        await self.redis.hdel(f"session:notes:{session_name}", note_id)

    async def _send_mention_notification(self, agent_id: str, note: SessionNote):
        """发送@提及通知"""
        # 实现通知逻辑（如发送到坐席的消息队列）
        pass

session_note_store = SessionNoteStore(redis_client)

@app.post("/api/sessions/{session_name}/notes")
async def add_session_note(
    session_name: str,
    request: AddSessionNoteRequest,
    agent: dict = Depends(require_agent)
):
    """添加会话备注"""
    # 解析@提及的坐席
    mentioned_agents = extract_mentioned_agents(request.content)

    note = SessionNote(
        id="",
        session_name=session_name,
        content=request.content,
        created_by=agent["agent_id"],
        created_at=0,
        is_pinned=request.is_pinned or False,
        mentioned_agents=mentioned_agents
    )

    note_id = await session_note_store.add_note(note)

    return {
        "success": True,
        "note_id": note_id
    }

@app.get("/api/sessions/{session_name}/notes")
async def get_session_notes(
    session_name: str,
    agent: dict = Depends(require_agent)
):
    """获取会话备注"""
    notes = await session_note_store.get_notes(session_name)
    return {"notes": notes}

@app.delete("/api/sessions/{session_name}/notes/{note_id}")
async def delete_session_note(
    session_name: str,
    note_id: str,
    agent: dict = Depends(require_agent)
):
    """删除备注（仅创建者或管理员可删除）"""
    notes = await session_note_store.get_notes(session_name)
    note = next((n for n in notes if n.id == note_id), None)

    if not note:
        raise HTTPException(404, "备注不存在")

    if note.created_by != agent["agent_id"] and agent["role"] != "admin":
        raise HTTPException(403, "无权删除此备注")

    await session_note_store.delete_note(session_name, note_id)

    return {"success": True}

def extract_mentioned_agents(content: str) -> List[str]:
    """提取@提及的坐席"""
    import re
    # 匹配 @坐席名 或 @agent_id
    mentions = re.findall(r'@(\w+)', content)
    return mentions
```

#### 15.4 前端实现

```vue
<template>
  <div class="session-notes">
    <div class="notes-header">
      <h4>会话备注 (内部可见)</h4>
      <el-button type="primary" size="small" @click="showAddDialog = true">
        + 添加
      </el-button>
    </div>

    <!-- 备注列表 -->
    <div class="notes-list">
      <div
        v-for="note in notes"
        :key="note.id"
        class="note-item"
        :class="{ 'note-pinned': note.is_pinned }"
      >
        <div class="note-content">
          <span v-if="note.is_pinned" class="pin-icon">📌</span>
          {{ note.content }}
        </div>
        <div class="note-meta">
          <span>{{ getAgentName(note.created_by) }} · {{ formatTime(note.created_at) }}</span>
          <el-button
            v-if="canDelete(note)"
            text
            type="danger"
            size="small"
            @click="deleteNote(note.id)"
          >
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 添加备注对话框 -->
    <el-dialog v-model="showAddDialog" title="添加备注" width="500px">
      <el-form>
        <el-form-item label="备注内容">
          <el-input
            v-model="noteContent"
            type="textarea"
            :rows="4"
            placeholder="输入备注内容... 使用 @ 提及其他坐席"
          />
          <p class="hint">💡 提示: 使用 @坐席名 可以提及其他坐席</p>
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="isPinned">置顶此备注</el-checkbox>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="addNote">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { getSessionNotes, addSessionNote, deleteSessionNote } from '@/api/sessions'

const props = defineProps<{
  sessionName: string
}>()

const notes = ref([])
const showAddDialog = ref(false)
const noteContent = ref('')
const isPinned = ref(false)
const currentAgent = ref(null)

async function loadNotes() {
  const { data } = await getSessionNotes(props.sessionName)
  notes.value = data.notes
}

async function addNote() {
  await addSessionNote(props.sessionName, {
    content: noteContent.value,
    is_pinned: isPinned.value
  })

  ElMessage.success('备注已添加')
  noteContent.value = ''
  isPinned.value = false
  showAddDialog.value = false

  loadNotes()
}

async function deleteNote(noteId: string) {
  await ElMessageBox.confirm('确定删除此备注?', '提示', {
    type: 'warning'
  })

  await deleteSessionNote(props.sessionName, noteId)
  ElMessage.success('备注已删除')

  loadNotes()
}

function canDelete(note): boolean {
  return note.created_by === currentAgent.value?.agent_id || currentAgent.value?.role === 'admin'
}

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}

onMounted(() => {
  loadNotes()
})
</script>

<style scoped>
.session-notes {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
}

.notes-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.notes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.note-item {
  background: white;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
}

.note-item.note-pinned {
  border-color: #3b82f6;
  background: #eff6ff;
}

.note-content {
  margin-bottom: 8px;
  line-height: 1.6;
}

.pin-icon {
  margin-right: 8px;
}

.note-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #6b7280;
}

.hint {
  font-size: 12px;
  color: #9ca3af;
  margin-top: 4px;
}
</style>
```

**验收标准**:
- [ ] 坐席可添加备注
- [ ] 备注仅坐席可见，客户不可见
- [ ] 支持@提及其他坐席
- [ ] 支持置顶重要备注
- [ ] 仅创建者或管理员可删除
- [ ] 置顶备注显示在前
- [ ] 显示创建者和时间
- [ ] @提及时发送通知

**预估工时**: 3天

---

## 📦 Phase 3 总结

**总预估工时**: 23天 (约5周，考虑调试和优化可能需要8周)
**版本号**: v3.7.0
**发布时间**: 预计2个月后

**核心成果**:
- ✅ 多店铺管理 (5天)
- ✅ 绩效报表系统 (7天)
- ✅ 工单模板功能 (4天)
- ✅ 消费数据统计 (4天)
- ✅ 会话备注功能 (3天)

**技术栈新增**:
- Pandas + openpyxl (Excel导出)
- ECharts (数据可视化)
- Shopify多店铺集成

**后续计划**:
- Phase 4: 智能化 (智能路由、AI推荐、行为分析)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**版本**: v1.0
**状态**: ✅ 待评审
