# 企业级客服工作台功能任务拆解 - Phase 4 智能化

> **文档版本**: v1.0
> **创建时间**: 2025-11-26
> **前置文档**: Phase 1-3 任务文档
> **关联文档**: `prd/01_全局指导/REFERENCE_SYSTEMS.md`
> **适用版本**: v3.8.0

---

## 📋 Phase 4 概览

**版本号**: v3.8.0
**预估工时**: 12周 (60个工作日)
**开发周期**: 预计3个月

**核心目标**:
- ✅ 智能路由系统
- ✅ AI推荐引擎
- ✅ 行为数据分析
- ✅ 营销工具
- ✅ 高级报表系统

**对标系统**:
- 拼多多: 智能路由、营销工具
- Zendesk: AI推荐、高级分析
- Intercom: 行为数据、客户画像

---

## 🤖 Phase 4: 智能化 (v3.8.0 - 12周)

### 任务16: 智能路由系统 ⭐ P3

**当前状态**:
- ❌ 会话随机分配或手动接入

**目标**:
基于客户属性、坐席能力智能分配会话

**功能需求**:

#### 16.1 路由规则引擎

```typescript
interface RoutingRule {
  id: string
  name: string
  priority: number          // 优先级 (数字越大越优先)
  enabled: boolean
  conditions: RoutingCondition[]
  actions: RoutingAction[]
}

interface RoutingCondition {
  type: 'customer_vip_level' | 'customer_language' | 'customer_country' |
        'issue_category' | 'time_of_day' | 'customer_tag'
  operator: 'equals' | 'contains' | 'greater_than' | 'in_list'
  value: any
}

interface RoutingAction {
  type: 'assign_to_agent' | 'assign_to_team' | 'set_priority' | 'add_tag'
  value: any
}
```

#### 16.2 预设路由规则

```typescript
const DEFAULT_ROUTING_RULES = [
  {
    name: 'VIP客户优先分配',
    priority: 100,
    enabled: true,
    conditions: [
      {
        type: 'customer_vip_level',
        operator: 'in_list',
        value: ['gold', 'platinum']
      }
    ],
    actions: [
      {
        type: 'assign_to_team',
        value: 'senior_agents'  // 高级坐席团队
      },
      {
        type: 'set_priority',
        value: 'high'
      }
    ]
  },
  {
    name: '德语客户分配',
    priority: 80,
    enabled: true,
    conditions: [
      {
        type: 'customer_language',
        operator: 'equals',
        value: 'de'
      }
    ],
    actions: [
      {
        type: 'assign_to_team',
        value: 'german_speakers'
      }
    ]
  },
  {
    name: '退款问题优先处理',
    priority: 90,
    enabled: true,
    conditions: [
      {
        type: 'issue_category',
        operator: 'contains',
        value: 'refund'
      }
    ],
    actions: [
      {
        type: 'assign_to_team',
        value: 'refund_specialists'
      },
      {
        type: 'set_priority',
        value: 'high'
      }
    ]
  },
  {
    name: '工作时间外转AI',
    priority: 70,
    enabled: true,
    conditions: [
      {
        type: 'time_of_day',
        operator: 'not_in_range',
        value: { start: '09:00', end: '18:00' }
      }
    ],
    actions: [
      {
        type: 'assign_to_agent',
        value: 'ai_bot'
      }
    ]
  },
  {
    name: '负载均衡',
    priority: 10,  // 最低优先级，兜底规则
    enabled: true,
    conditions: [],  // 无条件，始终生效
    actions: [
      {
        type: 'assign_to_agent',
        value: 'least_busy'  // 分配给最空闲的坐席
      }
    ]
  }
]
```

#### 16.3 坐席能力标签

```typescript
interface AgentSkills {
  agent_id: string
  languages: string[]       // ['zh', 'en', 'de']
  specialties: string[]     // ['refund', 'technical', 'sales']
  vip_service: boolean      // 是否有VIP服务权限
  max_concurrent_sessions: number  // 最大并发会话数
  current_load: number      // 当前负载 (0-100%)
  availability: 'online' | 'busy' | 'away' | 'offline'
}
```

#### 16.4 后端实现

```python
from typing import List, Optional

class RoutingEngine:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.rules = []

    async def load_rules(self):
        """加载路由规则"""
        rules_json = await self.redis.get("routing:rules")
        if rules_json:
            self.rules = json.loads(rules_json)
        else:
            # 使用默认规则
            self.rules = DEFAULT_ROUTING_RULES

        # 按优先级排序
        self.rules.sort(key=lambda x: x['priority'], reverse=True)

    async def find_best_agent(
        self,
        session_state: SessionState,
        customer_profile: dict
    ) -> Optional[str]:
        """
        根据规则找到最佳坐席

        返回: agent_id 或 None
        """
        await self.load_rules()

        # 收集上下文信息
        context = {
            'customer_vip_level': customer_profile.get('vip_level'),
            'customer_language': customer_profile.get('language'),
            'customer_country': customer_profile.get('country'),
            'customer_tags': customer_profile.get('tags', []),
            'issue_category': await self._detect_issue_category(session_state),
            'time_of_day': datetime.now().strftime('%H:%M')
        }

        # 应用规则
        for rule in self.rules:
            if not rule['enabled']:
                continue

            # 检查条件
            if self._match_conditions(rule['conditions'], context):
                # 执行动作
                agent_id = await self._execute_actions(rule['actions'], session_state)
                if agent_id:
                    logger.info(f"Routing rule '{rule['name']}' matched, assigned to {agent_id}")
                    return agent_id

        return None

    def _match_conditions(self, conditions: List[dict], context: dict) -> bool:
        """检查所有条件是否匹配"""
        if not conditions:
            return True  # 无条件，始终匹配

        for condition in conditions:
            cond_type = condition['type']
            operator = condition['operator']
            expected_value = condition['value']
            actual_value = context.get(cond_type)

            if not self._evaluate_condition(actual_value, operator, expected_value):
                return False

        return True

    def _evaluate_condition(self, actual, operator: str, expected) -> bool:
        """评估单个条件"""
        if operator == 'equals':
            return actual == expected
        elif operator == 'contains':
            return expected in str(actual)
        elif operator == 'in_list':
            return actual in expected
        elif operator == 'greater_than':
            return actual > expected
        elif operator == 'not_in_range':
            # 检查时间是否在范围外
            from datetime import datetime
            current_time = datetime.now().strftime('%H:%M')
            return not (expected['start'] <= current_time <= expected['end'])
        return False

    async def _execute_actions(
        self,
        actions: List[dict],
        session_state: SessionState
    ) -> Optional[str]:
        """执行路由动作"""
        assigned_agent = None

        for action in actions:
            action_type = action['type']
            value = action['value']

            if action_type == 'assign_to_agent':
                if value == 'least_busy':
                    assigned_agent = await self._find_least_busy_agent()
                elif value == 'ai_bot':
                    assigned_agent = 'ai_bot'
                else:
                    assigned_agent = value

            elif action_type == 'assign_to_team':
                # 从团队中选择负载最低的坐席
                assigned_agent = await self._find_agent_in_team(value)

            elif action_type == 'set_priority':
                # 设置会话优先级
                session_state.priority = value

            elif action_type == 'add_tag':
                # 添加标签
                if not session_state.tags:
                    session_state.tags = []
                session_state.tags.append(value)

        return assigned_agent

    async def _find_least_busy_agent(self) -> Optional[str]:
        """找到负载最低的在线坐席"""
        all_agents = await agent_store.get_all_agents()
        online_agents = []

        for agent in all_agents:
            skills_json = await self.redis.get(f"agent:skills:{agent.agent_id}")
            if not skills_json:
                continue

            skills = json.loads(skills_json)
            if skills['availability'] == 'online':
                online_agents.append((agent.agent_id, skills['current_load']))

        if not online_agents:
            return None

        # 返回负载最低的
        online_agents.sort(key=lambda x: x[1])
        return online_agents[0][0]

    async def _find_agent_in_team(self, team_name: str) -> Optional[str]:
        """从团队中找到最佳坐席"""
        # 获取团队成员
        team_agents_json = await self.redis.get(f"team:{team_name}:agents")
        if not team_agents_json:
            return None

        team_agent_ids = json.loads(team_agents_json)

        # 找到负载最低的在线坐席
        best_agent = None
        min_load = 100

        for agent_id in team_agent_ids:
            skills_json = await self.redis.get(f"agent:skills:{agent_id}")
            if not skills_json:
                continue

            skills = json.loads(skills_json)
            if skills['availability'] == 'online' and skills['current_load'] < min_load:
                best_agent = agent_id
                min_load = skills['current_load']

        return best_agent

    async def _detect_issue_category(self, session_state: SessionState) -> Optional[str]:
        """检测问题类别（基于关键词）"""
        if not session_state.messages:
            return None

        # 获取最近的用户消息
        user_messages = [
            msg['content']
            for msg in session_state.messages
            if msg['role'] == 'user'
        ]

        if not user_messages:
            return None

        recent_message = user_messages[-1].lower()

        # 关键词匹配
        if any(keyword in recent_message for keyword in ['refund', '退款', 'return', '退货']):
            return 'refund'
        elif any(keyword in recent_message for keyword in ['technical', '技术', 'problem', '问题', 'broken', '坏了']):
            return 'technical'
        elif any(keyword in recent_message for keyword in ['shipping', '物流', 'delivery', '配送']):
            return 'shipping'
        elif any(keyword in recent_message for keyword in ['product', '产品', '商品', 'price', '价格']):
            return 'sales'

        return None

routing_engine = RoutingEngine(redis_client)

# 新会话自动路由
@app.post("/api/sessions/auto-route")
async def auto_route_session(
    request: AutoRouteRequest
):
    """
    自动路由新会话

    request.session_name: 会话ID
    """
    # 1. 获取会话状态
    session_state = await session_store.get_session_state(request.session_name)

    # 2. 获取客户画像
    customer_email = session_state.customer_email or session_state.user_id
    if customer_email:
        customer_profile = await customer_profile_service.get_profile(customer_email)
    else:
        customer_profile = {}

    # 3. 智能路由
    assigned_agent = await routing_engine.find_best_agent(session_state, customer_profile)

    if assigned_agent:
        # 4. 分配坐席
        session_state.assigned_agent = assigned_agent
        session_state.status = SessionStatus.MANUAL_LIVE

        await session_store.save_session_state(session_state)

        # 5. 通知坐席
        await notify_agent_new_session(assigned_agent, request.session_name)

        return {
            "success": True,
            "assigned_agent": assigned_agent
        }
    else:
        # 无可用坐席，保持排队状态
        session_state.status = SessionStatus.PENDING_MANUAL
        await session_store.save_session_state(session_state)

        return {
            "success": False,
            "message": "No available agent"
        }

# 管理路由规则
@app.get("/api/routing/rules")
async def get_routing_rules(admin: dict = Depends(require_admin)):
    """获取路由规则"""
    await routing_engine.load_rules()
    return {"rules": routing_engine.rules}

@app.post("/api/routing/rules")
async def create_routing_rule(
    request: CreateRoutingRuleRequest,
    admin: dict = Depends(require_admin)
):
    """创建路由规则"""
    await routing_engine.load_rules()

    new_rule = {
        "id": f"rule_{int(time.time() * 1000)}",
        "name": request.name,
        "priority": request.priority,
        "enabled": True,
        "conditions": request.conditions,
        "actions": request.actions
    }

    routing_engine.rules.append(new_rule)
    routing_engine.rules.sort(key=lambda x: x['priority'], reverse=True)

    # 保存
    await redis_client.set(
        "routing:rules",
        json.dumps(routing_engine.rules, ensure_ascii=False)
    )

    return {"success": True, "rule_id": new_rule["id"]}

# 坐席技能管理
@app.put("/api/agents/{agent_id}/skills")
async def update_agent_skills(
    agent_id: str,
    request: UpdateAgentSkillsRequest,
    admin: dict = Depends(require_admin)
):
    """更新坐席技能标签"""
    skills = {
        "agent_id": agent_id,
        "languages": request.languages,
        "specialties": request.specialties,
        "vip_service": request.vip_service,
        "max_concurrent_sessions": request.max_concurrent_sessions,
        "current_load": 0,  # 初始负载
        "availability": "online"
    }

    await redis_client.set(
        f"agent:skills:{agent_id}",
        json.dumps(skills),
        ex=86400 * 365
    )

    return {"success": True}

# 团队管理
@app.post("/api/teams")
async def create_team(
    request: CreateTeamRequest,
    admin: dict = Depends(require_admin)
):
    """创建坐席团队"""
    team_id = request.team_name
    await redis_client.set(
        f"team:{team_id}:agents",
        json.dumps(request.agent_ids),
        ex=86400 * 365
    )

    return {"success": True, "team_id": team_id}
```

#### 16.5 前端实现 - 路由规则配置

```vue
<template>
  <div class="routing-rules">
    <h2>智能路由配置</h2>

    <el-button type="primary" @click="showCreateDialog = true">
      + 新建规则
    </el-button>

    <!-- 规则列表 -->
    <div class="rules-list">
      <div
        v-for="rule in rules"
        :key="rule.id"
        class="rule-card"
      >
        <div class="rule-header">
          <div>
            <h3>{{ rule.name }}</h3>
            <el-tag size="small">优先级: {{ rule.priority }}</el-tag>
          </div>
          <el-switch
            v-model="rule.enabled"
            @change="updateRule(rule)"
          />
        </div>

        <div class="rule-conditions">
          <h4>条件:</h4>
          <ul>
            <li v-for="(cond, i) in rule.conditions" :key="i">
              {{ formatCondition(cond) }}
            </li>
          </ul>
        </div>

        <div class="rule-actions">
          <h4>动作:</h4>
          <ul>
            <li v-for="(action, i) in rule.actions" :key="i">
              {{ formatAction(action) }}
            </li>
          </ul>
        </div>

        <div class="rule-footer">
          <el-button text @click="editRule(rule)">编辑</el-button>
          <el-button text type="danger" @click="deleteRule(rule.id)">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- 创建/编辑规则对话框 -->
    <el-dialog
      v-model="showCreateDialog"
      title="路由规则配置"
      width="60%"
    >
      <el-form :model="formData" label-width="120px">
        <el-form-item label="规则名称">
          <el-input v-model="formData.name" />
        </el-form-item>

        <el-form-item label="优先级">
          <el-input-number v-model="formData.priority" :min="1" :max="100" />
        </el-form-item>

        <el-form-item label="触发条件">
          <div
            v-for="(cond, i) in formData.conditions"
            :key="i"
            class="condition-row"
          >
            <el-select v-model="cond.type" placeholder="选择条件类型">
              <el-option label="VIP等级" value="customer_vip_level" />
              <el-option label="客户语言" value="customer_language" />
              <el-option label="客户国家" value="customer_country" />
              <el-option label="问题类别" value="issue_category" />
              <el-option label="时间段" value="time_of_day" />
            </el-select>

            <el-select v-model="cond.operator" placeholder="操作符">
              <el-option label="等于" value="equals" />
              <el-option label="包含" value="contains" />
              <el-option label="属于" value="in_list" />
            </el-select>

            <el-input v-model="cond.value" placeholder="值" />

            <el-button
              type="danger"
              text
              @click="formData.conditions.splice(i, 1)"
            >
              删除
            </el-button>
          </div>

          <el-button @click="formData.conditions.push({})">
            + 添加条件
          </el-button>
        </el-form-item>

        <el-form-item label="执行动作">
          <div
            v-for="(action, i) in formData.actions"
            :key="i"
            class="action-row"
          >
            <el-select v-model="action.type" placeholder="选择动作">
              <el-option label="分配到坐席" value="assign_to_agent" />
              <el-option label="分配到团队" value="assign_to_team" />
              <el-option label="设置优先级" value="set_priority" />
              <el-option label="添加标签" value="add_tag" />
            </el-select>

            <el-input v-model="action.value" placeholder="值" />

            <el-button
              type="danger"
              text
              @click="formData.actions.splice(i, 1)"
            >
              删除
            </el-button>
          </div>

          <el-button @click="formData.actions.push({})">
            + 添加动作
          </el-button>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="saveRule">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { getRoutingRules, createRoutingRule, updateRoutingRule } from '@/api/routing'

const rules = ref([])
const showCreateDialog = ref(false)
const formData = reactive({
  name: '',
  priority: 50,
  conditions: [],
  actions: []
})

async function loadRules() {
  const { data } = await getRoutingRules()
  rules.value = data.rules
}

function formatCondition(cond): string {
  const typeLabels = {
    'customer_vip_level': 'VIP等级',
    'customer_language': '客户语言',
    'issue_category': '问题类别'
  }

  const opLabels = {
    'equals': '等于',
    'in_list': '属于'
  }

  return `${typeLabels[cond.type]} ${opLabels[cond.operator]} ${cond.value}`
}

function formatAction(action): string {
  const typeLabels = {
    'assign_to_team': '分配到团队',
    'set_priority': '设置优先级'
  }

  return `${typeLabels[action.type]}: ${action.value}`
}

async function saveRule() {
  await createRoutingRule(formData)
  ElMessage.success('规则已保存')
  showCreateDialog.value = false
  loadRules()
}

onMounted(() => {
  loadRules()
})
</script>

<style scoped>
.rules-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-top: 20px;
}

.rule-card {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.condition-row,
.action-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}
</style>
```

**验收标准**:
- [ ] 支持5+种路由条件类型
- [ ] 支持4+种路由动作
- [ ] VIP客户优先分配到高级坐席
- [ ] 按语言自动分配坐席
- [ ] 负载均衡分配
- [ ] 规则优先级排序
- [ ] 管理员可配置规则
- [ ] 规则启用/禁用开关
- [ ] 坐席技能标签管理
- [ ] 团队管理功能

**预估工时**: 8天

---

### 任务17: AI推荐引擎 ⭐ P3

**当前状态**:
- ✅ 知识库系统 (任务8)
- ❌ 无AI推荐

**目标**:
根据用户问题自动推荐知识库文章和商品

**功能需求**:

#### 17.1 推荐算法

```python
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class AIRecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(max_features=1000)
        self.knowledge_base_vectors = None
        self.knowledge_articles = []

    async def index_knowledge_base(self):
        """索引知识库文章"""
        # 获取所有已发布的文章
        articles = await knowledge_store.search_articles(query="", limit=1000)

        self.knowledge_articles = articles
        article_texts = [f"{a.title} {a.content}" for a in articles]

        # 构建TF-IDF向量
        self.knowledge_base_vectors = self.vectorizer.fit_transform(article_texts)

    async def recommend_knowledge_articles(
        self,
        user_message: str,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        推荐知识库文章

        返回: [(article_id, relevance_score), ...]
        """
        if not self.knowledge_base_vectors:
            await self.index_knowledge_base()

        # 将用户消息转为向量
        user_vector = self.vectorizer.transform([user_message])

        # 计算余弦相似度
        similarities = cosine_similarity(user_vector, self.knowledge_base_vectors)[0]

        # 获取Top K
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # 相似度阈值
                article = self.knowledge_articles[idx]
                recommendations.append((article.id, float(similarities[idx])))

        return recommendations

    async def recommend_products(
        self,
        user_message: str,
        customer_profile: dict,
        top_k: int = 3
    ) -> List[Tuple[str, float]]:
        """
        推荐商品

        综合考虑:
        1. 用户问题相关性
        2. 客户历史购买偏好
        3. 热销商品
        """
        shopify = ShopifyClient()
        all_products = await shopify.get_all_products()

        # 1. 基于问题的相关性推荐
        product_texts = [f"{p.title} {p.description}" for p in all_products]
        product_vectors = self.vectorizer.fit_transform(product_texts)
        user_vector = self.vectorizer.transform([user_message])

        similarities = cosine_similarity(user_vector, product_vectors)[0]

        # 2. 基于历史购买的协同过滤
        favorite_products = customer_profile.get('favorite_products', [])
        if favorite_products:
            for i, product in enumerate(all_products):
                if product.title in [fp['product_name'] for fp in favorite_products]:
                    similarities[i] *= 1.5  # 提升相似商品的权重

        # 3. 考虑库存和价格
        for i, product in enumerate(all_products):
            if product.variants[0].inventory_quantity == 0:
                similarities[i] *= 0.5  # 降低缺货商品权重

        # Top K
        top_indices = np.argsort(similarities)[-top_k:][::-1]

        recommendations = []
        for idx in top_indices:
            if similarities[idx] > 0.1:
                product = all_products[idx]
                recommendations.append((product.id, float(similarities[idx])))

        return recommendations

ai_recommender = AIRecommendationEngine()

# API接口
@app.post("/api/ai/recommend-knowledge")
async def ai_recommend_knowledge(
    request: AIRecommendRequest,
    agent: dict = Depends(require_agent)
):
    """AI推荐知识库文章"""
    recommendations = await ai_recommender.recommend_knowledge_articles(
        request.user_message,
        top_k=3
    )

    # 获取文章详情
    articles = []
    for article_id, score in recommendations:
        article_json = await redis_client.get(f"knowledge:article:{article_id}")
        if article_json:
            article = KnowledgeArticle.parse_raw(article_json)
            articles.append({
                "article": article,
                "relevance_score": score
            })

    return {"recommendations": articles}

@app.post("/api/ai/recommend-products")
async def ai_recommend_products(
    request: AIRecommendRequest,
    agent: dict = Depends(require_agent)
):
    """AI推荐商品"""
    # 获取客户画像
    customer_profile = await customer_profile_service.get_profile(request.customer_email)

    recommendations = await ai_recommender.recommend_products(
        request.user_message,
        customer_profile,
        top_k=3
    )

    # 获取商品详情
    shopify = ShopifyClient()
    products = []
    for product_id, score in recommendations:
        product = await shopify.get_product(product_id)
        products.append({
            "product": {
                "id": product.id,
                "title": product.title,
                "image_url": product.images[0].src if product.images else None,
                "price": float(product.variants[0].price)
            },
            "relevance_score": score
        })

    return {"recommendations": products}

# 定时重建索引
from apscheduler.schedulers.asyncio import AsyncIOScheduler

@app.on_event("startup")
async def start_ai_indexer():
    """启动AI推荐索引器"""
    scheduler = AsyncIOScheduler()

    # 每小时重建一次知识库索引
    scheduler.add_job(
        ai_recommender.index_knowledge_base,
        'interval',
        hours=1
    )

    scheduler.start()

    # 立即构建一次索引
    await ai_recommender.index_knowledge_base()
```

#### 17.2 前端实现 - AI推荐面板

```vue
<template>
  <div class="ai-recommendations">
    <h4>🤖 AI推荐</h4>

    <!-- 知识库推荐 -->
    <div v-if="knowledgeRecommendations.length > 0" class="recommendations-section">
      <h5>💡 相关知识库文章</h5>
      <div
        v-for="item in knowledgeRecommendations"
        :key="item.article.id"
        class="recommendation-item"
      >
        <div class="item-header">
          <h6>{{ item.article.title }}</h6>
          <el-tag size="small">
            匹配度: {{ (item.relevance_score * 100).toFixed(0) }}%
          </el-tag>
        </div>
        <p class="item-excerpt">{{ getExcerpt(item.article.content) }}</p>
        <div class="item-actions">
          <el-button size="small" @click="insertKnowledge(item.article.id)">
            插入到会话
          </el-button>
          <el-button size="small" text @click="viewArticle(item.article)">
            查看详情
          </el-button>
        </div>
      </div>
    </div>

    <!-- 商品推荐 -->
    <div v-if="productRecommendations.length > 0" class="recommendations-section">
      <h5>🛍️ 推荐商品</h5>
      <div
        v-for="item in productRecommendations"
        :key="item.product.id"
        class="recommendation-item product-item"
      >
        <img :src="item.product.image_url" alt="" class="product-image" />
        <div class="product-info">
          <h6>{{ item.product.title }}</h6>
          <p class="price">€{{ item.product.price }}</p>
          <el-tag size="small">
            匹配度: {{ (item.relevance_score * 100).toFixed(0) }}%
          </el-tag>
        </div>
        <el-button size="small" type="primary" @click="sendProductCard(item.product.id)">
          发送卡片
        </el-button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading"><Loading /></el-icon>
      <span>AI分析中...</span>
    </div>

    <!-- 无推荐 -->
    <div v-if="!loading && knowledgeRecommendations.length === 0 && productRecommendations.length === 0" class="empty-state">
      <p>暂无推荐内容</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { aiRecommendKnowledge, aiRecommendProducts } from '@/api/ai'

const props = defineProps<{
  sessionName: string
  lastUserMessage: string
  customerEmail: string
}>()

const knowledgeRecommendations = ref([])
const productRecommendations = ref([])
const loading = ref(false)

// 监听用户消息变化
watch(() => props.lastUserMessage, async (newMessage) => {
  if (!newMessage) return

  loading.value = true

  try {
    // 并行请求知识库和商品推荐
    const [knowledgeRes, productRes] = await Promise.all([
      aiRecommendKnowledge({
        user_message: newMessage,
        customer_email: props.customerEmail
      }),
      aiRecommendProducts({
        user_message: newMessage,
        customer_email: props.customerEmail
      })
    ])

    knowledgeRecommendations.value = knowledgeRes.data.recommendations
    productRecommendations.value = productRes.data.recommendations
  } catch (error) {
    console.error('AI推荐失败:', error)
  } finally {
    loading.value = false
  }
}, { immediate: true })

function getExcerpt(content: string): string {
  return content.substring(0, 100) + '...'
}

async function insertKnowledge(articleId: string) {
  await insertKnowledgeArticle(props.sessionName, articleId)
  ElMessage.success('知识库文章已插入')
}

async function sendProductCard(productId: string) {
  await sendProductCardToSession(props.sessionName, productId)
  ElMessage.success('商品卡片已发送')
}
</script>

<style scoped>
.ai-recommendations {
  padding: 16px;
  background: #f9fafb;
  border-radius: 8px;
  max-height: 600px;
  overflow-y: auto;
}

.recommendations-section {
  margin-bottom: 24px;
}

.recommendation-item {
  background: white;
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
}

.product-item {
  display: flex;
  gap: 12px;
  align-items: center;
}

.product-image {
  width: 80px;
  height: 80px;
  object-fit: cover;
  border-radius: 4px;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 32px;
  color: #9ca3af;
}
</style>
```

**验收标准**:
- [ ] 基于TF-IDF的相似度计算
- [ ] 自动推荐Top 3知识库文章
- [ ] 自动推荐Top 3相关商品
- [ ] 匹配度评分显示
- [ ] 一键插入推荐内容
- [ ] 考虑客户历史偏好
- [ ] 考虑商品库存状态
- [ ] 定时重建索引
- [ ] 实时响应用户消息

**预估工时**: 6天

---

由于篇幅限制，Phase 4 剩余任务18-20将继续在此文档中：

### 任务18: 行为数据分析 ⭐ P3

**当前状态**:
- ❌ 无行为追踪

**目标**:
追踪客户浏览、搜索、购物车行为

**功能需求**:

#### 18.1 行为数据模型

```typescript
interface CustomerBehavior {
  customer_id: string
  behaviors: {
    // 浏览行为
    viewed_products: {
      product_id: string
      product_name: string
      viewed_at: number
      duration: number  // 停留时间(秒)
    }[]

    // 搜索行为
    search_queries: {
      query: string
      searched_at: number
      results_count: number
    }[]

    // 购物车行为
    cart_items: {
      product_id: string
      product_name: string
      added_at: number
      removed_at?: number  // 如果移除
      purchased: boolean   // 是否最终购买
    }[]

    // 收藏行为
    wishlisted_products: {
      product_id: string
      added_at: number
    }[]
  }

  // 行为统计
  stats: {
    total_page_views: number
    total_time_spent: number  // 秒
    bounce_rate: number       // 跳出率 %
    cart_abandonment_rate: number  // 购物车放弃率 %
  }
}
```

**预估工时**: 5天

---

### 任务19: 营销工具 ⭐ P3

**当前状态**:
- ❌ 无营销功能

**目标**:
优惠券发送、跟进提醒、客户打标签

**功能需求**:

#### 19.1 优惠券系统

```typescript
interface Coupon {
  code: string
  type: 'percentage' | 'fixed_amount' | 'free_shipping'
  value: number
  min_purchase: number
  expires_at: number
  usage_limit: number
  usage_count: number
}
```

**预估工时**: 6天

---

### 任务20: 高级报表系统 ⭐ P3

**当前状态**:
- ✅ 基础绩效报表 (任务12)
- ❌ 无高级分析

**目标**:
咨询来源、高峰时段、转化漏斗分析

**功能需求**:

#### 20.1 漏斗分析

```typescript
interface ConversionFunnel {
  stages: {
    name: string
    count: number
    conversion_rate: number
  }[]
}

// 示例: 访问 → 咨询 → 加购 → 下单
```

**预估工时**: 7天

---

## 📦 Phase 4 总结

**总预估工时**: 32天 (约7周，考虑集成调试可能需要12周)
**版本号**: v3.8.0
**发布时间**: 预计3个月后

**核心成果**:
- ✅ 智能路由系统 (8天)
- ✅ AI推荐引擎 (6天)
- ✅ 行为数据分析 (5天)
- ✅ 营销工具 (6天)
- ✅ 高级报表系统 (7天)

**技术栈新增**:
- scikit-learn (机器学习)
- APScheduler (定时任务)
- ECharts高级图表 (漏斗图、热力图)

**系统成熟度**:
- v3.8.0 完成后，系统将达到企业级成熟度
- 对标拼多多/聚水潭核心功能覆盖率: 85%+
- 可支持 100+ 并发用户，1000+ 日会话量

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**版本**: v1.0
**状态**: ✅ 待评审
