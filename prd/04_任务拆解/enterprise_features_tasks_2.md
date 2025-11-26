# 企业级客服工作台功能任务拆解 - Phase 2 功能完善

> **文档版本**: v1.0
> **创建时间**: 2025-11-26
> **前置文档**: `enterprise_features_tasks.md` (Phase 1)
> **关联文档**: `prd/01_全局指导/REFERENCE_SYSTEMS.md`
> **适用版本**: v3.6.0

---

## 📋 Phase 2 概览

**版本号**: v3.6.0
**预估工时**: 4周 (20个工作日)
**开发周期**: 预计1个月

**核心目标**:
- ✅ 商品/订单卡片功能
- ✅ 图片/文件发送能力
- ✅ 知识库系统
- ✅ 实时数据统计
- ✅ 物流追踪集成

**对标系统**:
- 拼多多: 商品卡片、订单卡片、实时数据
- 聚水潭: 知识库系统、物流追踪
- Zendesk: 文件管理、知识库

---

## 🎯 Phase 2: 功能完善 (v3.6.0 - 4周)

### 任务6: 商品/订单卡片发送 ⭐ P1

**当前状态**:
- ✅ Shopify客户信息集成
- ✅ 订单列表显示
- ❌ 无商品卡片发送
- ❌ 无订单卡片发送

**目标**:
实现商品和订单卡片快速发送，提升沟通效率

**功能需求**:

#### 6.1 商品卡片设计

**数据模型**:
```typescript
interface ProductCard {
  id: string
  type: 'product_card'
  product_id: string
  title: string
  image_url: string
  price: {
    amount: number
    currency: string
    original_price?: number  // 原价（如有折扣）
  }
  variants?: {
    name: string     // 如 "颜色"
    options: string[] // ["黑色", "白色", "灰色"]
  }[]
  stock: {
    available: boolean
    quantity?: number
    warehouse?: string  // 仓库名称
  }
  sku: string
  url: string  // 商品详情页链接
  description?: string  // 简短描述
}
```

**UI设计 - 坐席端**:
```
┌─────────────────────────────────────┐
│ 🔍 搜索商品（名称/SKU）              │
├─────────────────────────────────────┤
│ 搜索结果:                            │
│ ┌─────────────────────────────────┐ │
│ │ [图] D4S Pro 电动车             │ │
│ │     SKU: FD-D4S-BK-EU           │ │
│ │     €1,299.00  库存: 45台       │ │
│ │     [发送卡片]                   │ │
│ ├─────────────────────────────────┤ │
│ │ [图] D11 折叠电动车             │ │
│ │     SKU: FD-D11-GY-EU           │ │
│ │     €899.00   库存: 12台        │ │
│ │     [发送卡片]                   │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**UI设计 - 用户端接收**:
```
┌──────────────────────────────────────┐
│ 坐席小李 发送了商品卡片              │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │ [商品图片]                        │ │
│ │                                   │ │
│ │ D4S Pro 电动车                    │ │
│ │ €1,299.00  原价: €1,499.00       │ │
│ │                                   │ │
│ │ ✅ 有货 (45台)                    │ │
│ │ 🚚 3-5天发货                      │ │
│ │                                   │ │
│ │ [查看详情] [立即购买]             │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

#### 6.2 订单卡片设计

**数据模型**:
```typescript
interface OrderCard {
  id: string
  type: 'order_card'
  order_id: string
  order_number: string
  status: 'pending' | 'paid' | 'shipped' | 'delivered' | 'cancelled'
  created_at: number
  items: {
    product_name: string
    product_image: string
    quantity: number
    price: number
    sku: string
  }[]
  total_amount: {
    amount: number
    currency: string
  }
  shipping: {
    address: string
    method: string
    tracking_number?: string
    carrier?: string
    estimated_delivery?: string
  }
  payment_method: string
  customer_note?: string
}
```

**UI设计 - 坐席端**:
```
┌─────────────────────────────────────┐
│ 🔍 搜索订单（订单号/客户邮箱）       │
├─────────────────────────────────────┤
│ 搜索结果:                            │
│ ┌─────────────────────────────────┐ │
│ │ 订单号: #FD20241126001          │ │
│ │ 状态: 🟢 待发货                  │ │
│ │ 金额: €1,299.00                 │ │
│ │ 商品: D4S Pro 黑色 x1           │ │
│ │ 时间: 2024-11-26 14:30          │ │
│ │ [发送卡片] [查看详情]            │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

**UI设计 - 用户端接收**:
```
┌──────────────────────────────────────┐
│ 坐席小李 发送了订单信息              │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │ 📦 订单 #FD20241126001           │ │
│ │                                   │ │
│ │ 状态: 🟢 待发货                   │ │
│ │ 下单时间: 2024-11-26 14:30       │ │
│ │                                   │ │
│ │ 商品清单:                         │ │
│ │ • D4S Pro 电动车 (黑色) x1       │ │
│ │   €1,299.00                      │ │
│ │                                   │ │
│ │ 总计: €1,299.00                  │ │
│ │                                   │ │
│ │ 配送地址: 德国慕尼黑...           │ │
│ │ 物流方式: DHL 标准配送            │ │
│ │                                   │ │
│ │ [查看详情] [追踪物流]             │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
```

#### 6.3 后端API实现

```python
# 商品搜索
@app.get("/api/products/search")
async def search_products(
    query: str,
    limit: int = 10,
    agent: dict = Depends(require_agent)
):
    """
    搜索商品（名称、SKU）

    查询来源: Shopify Products API
    """
    shopify_client = ShopifyClient()
    products = await shopify_client.search_products(query, limit=limit)

    return {
        "products": [
            {
                "id": p.id,
                "title": p.title,
                "image_url": p.images[0].src if p.images else None,
                "price": {
                    "amount": float(p.variants[0].price),
                    "currency": "EUR"
                },
                "sku": p.variants[0].sku,
                "stock": {
                    "available": p.variants[0].inventory_quantity > 0,
                    "quantity": p.variants[0].inventory_quantity
                },
                "url": f"https://fiido.com/products/{p.handle}"
            }
            for p in products
        ]
    }

# 订单搜索
@app.get("/api/orders/search")
async def search_orders(
    query: str,  # 订单号或邮箱
    limit: int = 10,
    agent: dict = Depends(require_agent)
):
    """
    搜索订单

    查询来源: Shopify Orders API
    """
    shopify_client = ShopifyClient()

    # 优先按订单号搜索
    if query.startswith('#'):
        orders = await shopify_client.get_order_by_name(query[1:])
    else:
        # 按邮箱或客户名搜索
        orders = await shopify_client.search_orders(email=query)

    return {
        "orders": [
            {
                "id": o.id,
                "order_number": o.name,
                "status": map_order_status(o.financial_status, o.fulfillment_status),
                "created_at": o.created_at.timestamp(),
                "total_amount": {
                    "amount": float(o.total_price),
                    "currency": o.currency
                },
                "items": [
                    {
                        "product_name": item.name,
                        "quantity": item.quantity,
                        "price": float(item.price),
                        "sku": item.sku
                    }
                    for item in o.line_items
                ]
            }
            for o in orders
        ]
    }

# 发送商品卡片
@app.post("/api/sessions/{session_name}/send-product-card")
async def send_product_card(
    session_name: str,
    request: SendProductCardRequest,
    agent: dict = Depends(require_agent)
):
    """
    发送商品卡片到用户会话

    request.product_id: Shopify产品ID
    """
    # 1. 获取商品详情
    shopify_client = ShopifyClient()
    product = await shopify_client.get_product(request.product_id)

    # 2. 构建卡片消息
    card_message = {
        "type": "product_card",
        "product_id": product.id,
        "title": product.title,
        "image_url": product.images[0].src if product.images else None,
        "price": {
            "amount": float(product.variants[0].price),
            "currency": "EUR"
        },
        "stock": {
            "available": product.variants[0].inventory_quantity > 0,
            "quantity": product.variants[0].inventory_quantity
        },
        "sku": product.variants[0].sku,
        "url": f"https://fiido.com/products/{product.handle}"
    }

    # 3. 保存到会话历史
    session_state = await session_store.get_session_state(session_name)
    session_state.messages.append({
        "role": "assistant",
        "content": json.dumps(card_message, ensure_ascii=False),
        "timestamp": time.time(),
        "agent_id": agent["agent_id"]
    })
    await session_store.save_session_state(session_state)

    # 4. 推送到用户SSE
    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "product_card",
            "data": card_message
        })

    return {"success": True}

# 发送订单卡片
@app.post("/api/sessions/{session_name}/send-order-card")
async def send_order_card(
    session_name: str,
    request: SendOrderCardRequest,
    agent: dict = Depends(require_agent)
):
    """发送订单卡片到用户会话"""
    shopify_client = ShopifyClient()
    order = await shopify_client.get_order(request.order_id)

    card_message = {
        "type": "order_card",
        "order_id": order.id,
        "order_number": order.name,
        "status": map_order_status(order.financial_status, order.fulfillment_status),
        "created_at": order.created_at.timestamp(),
        "items": [
            {
                "product_name": item.name,
                "quantity": item.quantity,
                "price": float(item.price),
                "sku": item.sku
            }
            for item in order.line_items
        ],
        "total_amount": {
            "amount": float(order.total_price),
            "currency": order.currency
        },
        "shipping": {
            "address": f"{order.shipping_address.city}, {order.shipping_address.country}",
            "method": order.shipping_lines[0].title if order.shipping_lines else "标准配送",
            "tracking_number": order.tracking_numbers[0] if order.tracking_numbers else None
        }
    }

    # 保存并推送
    session_state = await session_store.get_session_state(session_name)
    session_state.messages.append({
        "role": "assistant",
        "content": json.dumps(card_message, ensure_ascii=False),
        "timestamp": time.time(),
        "agent_id": agent["agent_id"]
    })
    await session_store.save_session_state(session_state)

    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "order_card",
            "data": card_message
        })

    return {"success": True}
```

#### 6.4 前端实现 (坐席工作台)

```vue
<template>
  <div class="card-sender">
    <!-- 商品搜索 -->
    <div class="search-section">
      <el-input
        v-model="searchQuery"
        placeholder="搜索商品（名称/SKU）或订单号..."
        prefix-icon="Search"
        @input="handleSearch"
      />
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchType === 'product'" class="product-results">
      <div
        v-for="product in searchResults"
        :key="product.id"
        class="product-item"
      >
        <img :src="product.image_url" alt="" class="product-image" />
        <div class="product-info">
          <h4>{{ product.title }}</h4>
          <p class="sku">SKU: {{ product.sku }}</p>
          <div class="price-stock">
            <span class="price">€{{ product.price.amount }}</span>
            <span
              class="stock"
              :class="{ 'out-of-stock': !product.stock.available }"
            >
              {{ product.stock.available ? `库存: ${product.stock.quantity}` : '缺货' }}
            </span>
          </div>
        </div>
        <el-button type="primary" size="small" @click="sendProductCard(product)">
          发送卡片
        </el-button>
      </div>
    </div>

    <!-- 订单搜索结果 -->
    <div v-else-if="searchType === 'order'" class="order-results">
      <div
        v-for="order in searchResults"
        :key="order.id"
        class="order-item"
      >
        <div class="order-header">
          <span class="order-number">{{ order.order_number }}</span>
          <span class="order-status" :class="`status-${order.status}`">
            {{ orderStatusText(order.status) }}
          </span>
        </div>
        <p class="order-amount">€{{ order.total_amount.amount }}</p>
        <p class="order-items">
          {{ order.items.map(i => `${i.product_name} x${i.quantity}`).join(', ') }}
        </p>
        <el-button type="primary" size="small" @click="sendOrderCard(order)">
          发送卡片
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { searchProducts, searchOrders, sendProductCard as apiSendProductCard, sendOrderCard as apiSendOrderCard } from '@/api/cards'

const searchQuery = ref('')
const searchType = ref<'product' | 'order'>('product')
const searchResults = ref([])

async function handleSearch() {
  if (!searchQuery.value) {
    searchResults.value = []
    return
  }

  // 判断搜索类型
  if (searchQuery.value.startsWith('#')) {
    searchType.value = 'order'
    const { data } = await searchOrders(searchQuery.value)
    searchResults.value = data.orders
  } else {
    searchType.value = 'product'
    const { data } = await searchProducts(searchQuery.value)
    searchResults.value = data.products
  }
}

async function sendProductCard(product) {
  await apiSendProductCard(currentSession.value, product.id)
  ElMessage.success('商品卡片已发送')
}

async function sendOrderCard(order) {
  await apiSendOrderCard(currentSession.value, order.id)
  ElMessage.success('订单卡片已发送')
}
</script>
```

#### 6.5 前端实现 (用户端)

```vue
<template>
  <div class="message-card">
    <!-- 商品卡片 -->
    <div v-if="message.type === 'product_card'" class="product-card">
      <img :src="message.data.image_url" alt="" class="card-image" />
      <div class="card-content">
        <h3>{{ message.data.title }}</h3>
        <div class="price-section">
          <span class="current-price">€{{ message.data.price.amount }}</span>
          <span v-if="message.data.price.original_price" class="original-price">
            €{{ message.data.price.original_price }}
          </span>
        </div>
        <div class="stock-info">
          <span v-if="message.data.stock.available" class="in-stock">
            ✅ 有货 ({{ message.data.stock.quantity }}台)
          </span>
          <span v-else class="out-of-stock">
            ❌ 暂时缺货
          </span>
        </div>
        <div class="card-actions">
          <a :href="message.data.url" target="_blank" class="btn-secondary">
            查看详情
          </a>
          <button class="btn-primary" @click="buyNow">
            立即购买
          </button>
        </div>
      </div>
    </div>

    <!-- 订单卡片 -->
    <div v-else-if="message.type === 'order_card'" class="order-card">
      <div class="card-header">
        <span class="order-title">📦 订单 {{ message.data.order_number }}</span>
        <span class="order-status" :class="`status-${message.data.status}`">
          {{ orderStatusText(message.data.status) }}
        </span>
      </div>
      <div class="card-content">
        <p class="order-date">
          下单时间: {{ formatDate(message.data.created_at) }}
        </p>

        <div class="order-items">
          <h4>商品清单:</h4>
          <div v-for="item in message.data.items" :key="item.sku" class="item">
            • {{ item.product_name }} x{{ item.quantity }} - €{{ item.price }}
          </div>
        </div>

        <div class="order-total">
          总计: €{{ message.data.total_amount.amount }}
        </div>

        <div class="shipping-info">
          <p>配送地址: {{ message.data.shipping.address }}</p>
          <p>物流方式: {{ message.data.shipping.method }}</p>
          <p v-if="message.data.shipping.tracking_number">
            物流单号: {{ message.data.shipping.tracking_number }}
          </p>
        </div>

        <div class="card-actions">
          <button class="btn-secondary" @click="viewOrderDetails">
            查看详情
          </button>
          <button
            v-if="message.data.shipping.tracking_number"
            class="btn-primary"
            @click="trackShipment"
          >
            追踪物流
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

**验收标准**:
- [ ] 商品搜索支持名称和SKU
- [ ] 订单搜索支持订单号和邮箱
- [ ] 商品卡片显示图片、价格、库存
- [ ] 订单卡片显示状态、商品列表、物流信息
- [ ] 用户端卡片可点击查看详情
- [ ] 卡片消息保存到会话历史
- [ ] SSE实时推送卡片到用户端
- [ ] 缺货商品显示"暂时缺货"提示
- [ ] 订单状态实时更新

**预估工时**: 4天

---

### 任务7: 图片/文件发送功能 ⭐ P1

**当前状态**:
- ❌ 仅支持文本消息
- ❌ 无文件上传

**目标**:
支持图片、PDF、Excel等文件发送

**功能需求**:

#### 7.1 支持的文件类型

```typescript
const ALLOWED_FILE_TYPES = {
  images: {
    extensions: ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
    mimeTypes: ['image/jpeg', 'image/png', 'image/gif', 'image/webp'],
    maxSize: 10 * 1024 * 1024, // 10MB
  },
  documents: {
    extensions: ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.txt'],
    mimeTypes: [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      'application/vnd.ms-excel',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'text/plain'
    ],
    maxSize: 20 * 1024 * 1024, // 20MB
  },
  archives: {
    extensions: ['.zip', '.rar', '.7z'],
    mimeTypes: ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed'],
    maxSize: 50 * 1024 * 1024, // 50MB
  }
}
```

#### 7.2 文件存储策略

**存储方案**: 阿里云OSS / AWS S3 / 本地存储

```python
# 文件上传配置
class FileUploadConfig:
    STORAGE_TYPE = "aliyun_oss"  # or "aws_s3", "local"

    # 阿里云OSS配置
    OSS_ENDPOINT = "oss-eu-central-1.aliyuncs.com"
    OSS_BUCKET = "fiido-customer-service"
    OSS_ACCESS_KEY_ID = os.getenv("OSS_ACCESS_KEY_ID")
    OSS_ACCESS_KEY_SECRET = os.getenv("OSS_ACCESS_KEY_SECRET")

    # 文件路径规则
    FILE_PATH_PATTERN = "{type}/{year}/{month}/{session_name}/{filename}"
    # 示例: images/2024/11/session_xxx/abc123.jpg

    # CDN加速
    CDN_DOMAIN = "https://cdn.fiido-cs.com"
```

#### 7.3 后端API实现

```python
import oss2
from fastapi import UploadFile, File
import hashlib
import mimetypes

class FileService:
    def __init__(self):
        auth = oss2.Auth(
            FileUploadConfig.OSS_ACCESS_KEY_ID,
            FileUploadConfig.OSS_ACCESS_KEY_SECRET
        )
        self.bucket = oss2.Bucket(
            auth,
            FileUploadConfig.OSS_ENDPOINT,
            FileUploadConfig.OSS_BUCKET
        )

    async def upload_file(
        self,
        file: UploadFile,
        session_name: str,
        file_type: str
    ) -> dict:
        """上传文件到OSS"""
        # 1. 读取文件内容
        content = await file.read()

        # 2. 验证文件大小
        file_size = len(content)
        max_size = self._get_max_size(file_type)
        if file_size > max_size:
            raise HTTPException(400, f"文件大小超过限制 ({max_size / 1024 / 1024}MB)")

        # 3. 验证文件类型
        mime_type = file.content_type
        if not self._is_allowed_type(mime_type, file_type):
            raise HTTPException(400, "不支持的文件类型")

        # 4. 生成文件名（使用MD5防止重复）
        file_hash = hashlib.md5(content).hexdigest()
        file_ext = os.path.splitext(file.filename)[1]
        filename = f"{file_hash}{file_ext}"

        # 5. 构建OSS路径
        now = datetime.now()
        oss_path = FileUploadConfig.FILE_PATH_PATTERN.format(
            type=file_type,
            year=now.year,
            month=f"{now.month:02d}",
            session_name=session_name,
            filename=filename
        )

        # 6. 上传到OSS
        self.bucket.put_object(
            oss_path,
            content,
            headers={'Content-Type': mime_type}
        )

        # 7. 生成访问URL
        if FileUploadConfig.CDN_DOMAIN:
            file_url = f"{FileUploadConfig.CDN_DOMAIN}/{oss_path}"
        else:
            file_url = self.bucket.sign_url('GET', oss_path, 3600 * 24 * 7)  # 7天有效期

        return {
            "file_id": file_hash,
            "file_name": file.filename,
            "file_size": file_size,
            "file_type": file_type,
            "mime_type": mime_type,
            "oss_path": oss_path,
            "file_url": file_url,
            "uploaded_at": time.time()
        }

# API接口
file_service = FileService()

@app.post("/api/sessions/{session_name}/upload")
async def upload_file(
    session_name: str,
    file: UploadFile = File(...),
    agent: dict = Depends(require_agent)
):
    """
    上传文件

    支持的文件类型:
    - 图片: jpg, png, gif, webp (最大10MB)
    - 文档: pdf, doc, docx, xls, xlsx (最大20MB)
    - 压缩包: zip, rar, 7z (最大50MB)
    """
    # 1. 判断文件类型
    file_type = _detect_file_type(file.content_type)

    # 2. 上传文件
    file_info = await file_service.upload_file(file, session_name, file_type)

    # 3. 构建消息
    message = {
        "type": f"{file_type}_message",  # image_message, document_message
        "file_id": file_info["file_id"],
        "file_name": file_info["file_name"],
        "file_size": file_info["file_size"],
        "file_url": file_info["file_url"],
        "mime_type": file_info["mime_type"],
        "uploaded_by": agent["agent_id"],
        "timestamp": time.time()
    }

    # 4. 保存到会话历史
    session_state = await session_store.get_session_state(session_name)
    session_state.messages.append({
        "role": "assistant",
        "content": json.dumps(message, ensure_ascii=False),
        "timestamp": time.time(),
        "agent_id": agent["agent_id"]
    })
    await session_store.save_session_state(session_state)

    # 5. 推送到用户SSE
    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "file_message",
            "data": message
        })

    return {
        "success": True,
        "file_info": file_info
    }

def _detect_file_type(mime_type: str) -> str:
    """根据MIME类型判断文件分类"""
    if mime_type.startswith('image/'):
        return 'images'
    elif mime_type in ALLOWED_FILE_TYPES['documents']['mimeTypes']:
        return 'documents'
    elif mime_type in ALLOWED_FILE_TYPES['archives']['mimeTypes']:
        return 'archives'
    else:
        raise HTTPException(400, "不支持的文件类型")
```

#### 7.4 前端实现 (坐席工作台)

```vue
<template>
  <div class="file-uploader">
    <!-- 图片上传 -->
    <el-upload
      ref="imageUpload"
      action="#"
      :auto-upload="false"
      :on-change="handleImageSelect"
      :show-file-list="false"
      accept="image/jpeg,image/png,image/gif,image/webp"
      drag
    >
      <div class="upload-area">
        <el-icon class="upload-icon"><Picture /></el-icon>
        <p>点击或拖拽上传图片</p>
        <p class="upload-hint">支持 JPG、PNG、GIF、WebP，最大 10MB</p>
      </div>
    </el-upload>

    <!-- 文件上传 -->
    <el-upload
      ref="fileUpload"
      action="#"
      :auto-upload="false"
      :on-change="handleFileSelect"
      :show-file-list="false"
      accept=".pdf,.doc,.docx,.xls,.xlsx,.txt,.zip,.rar,.7z"
    >
      <el-button type="primary" :icon="Document">
        上传文件
      </el-button>
    </el-upload>

    <!-- 粘贴上传提示 -->
    <p class="paste-hint">💡 提示: 可直接粘贴 (Ctrl+V) 截图发送</p>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { uploadFile } from '@/api/files'
import { ElMessage } from 'element-plus'

const imageUpload = ref()
const fileUpload = ref()

async function handleImageSelect(file) {
  // 验证文件大小
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.error('图片大小不能超过 10MB')
    return
  }

  await uploadAndSend(file.raw)
}

async function handleFileSelect(file) {
  // 验证文件大小
  const maxSize = getMaxSize(file.raw.type)
  if (file.size > maxSize) {
    ElMessage.error(`文件大小不能超过 ${maxSize / 1024 / 1024}MB`)
    return
  }

  await uploadAndSend(file.raw)
}

async function uploadAndSend(file: File) {
  const loading = ElMessage.loading('上传中...')

  try {
    const formData = new FormData()
    formData.append('file', file)

    const { data } = await uploadFile(currentSession.value, formData)

    ElMessage.success('文件已发送')
  } catch (error) {
    ElMessage.error('上传失败: ' + error.message)
  } finally {
    loading.close()
  }
}

// 监听粘贴事件
function handlePaste(event: ClipboardEvent) {
  const items = event.clipboardData?.items
  if (!items) return

  for (let i = 0; i < items.length; i++) {
    const item = items[i]

    // 粘贴的是图片
    if (item.type.startsWith('image/')) {
      event.preventDefault()

      const file = item.getAsFile()
      if (file) {
        uploadAndSend(file)
      }
      break
    }
  }
}

onMounted(() => {
  document.addEventListener('paste', handlePaste)
})

onUnmounted(() => {
  document.removeEventListener('paste', handlePaste)
})
</script>
```

#### 7.5 前端实现 (用户端)

```vue
<template>
  <div class="file-message">
    <!-- 图片消息 -->
    <div v-if="message.type === 'image_message'" class="image-message">
      <img
        :src="message.data.file_url"
        :alt="message.data.file_name"
        class="message-image"
        @click="previewImage"
      />
      <p class="image-name">{{ message.data.file_name }}</p>
    </div>

    <!-- 文档消息 -->
    <div v-else-if="message.type === 'document_message'" class="document-message">
      <div class="document-icon">
        <el-icon size="40"><Document /></el-icon>
      </div>
      <div class="document-info">
        <h4>{{ message.data.file_name }}</h4>
        <p class="file-size">{{ formatFileSize(message.data.file_size) }}</p>
      </div>
      <a
        :href="message.data.file_url"
        download
        class="download-btn"
        target="_blank"
      >
        <el-icon><Download /></el-icon>
        下载
      </a>
    </div>

    <!-- 压缩包消息 -->
    <div v-else-if="message.type === 'archive_message'" class="archive-message">
      <div class="archive-icon">
        <el-icon size="40"><FolderOpened /></el-icon>
      </div>
      <div class="archive-info">
        <h4>{{ message.data.file_name }}</h4>
        <p class="file-size">{{ formatFileSize(message.data.file_size) }}</p>
      </div>
      <a
        :href="message.data.file_url"
        download
        class="download-btn"
        target="_blank"
      >
        <el-icon><Download /></el-icon>
        下载
      </a>
    </div>
  </div>

  <!-- 图片预览弹窗 -->
  <el-image-viewer
    v-if="showImagePreview"
    :url-list="[currentImage]"
    @close="showImagePreview = false"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'

const showImagePreview = ref(false)
const currentImage = ref('')

function previewImage() {
  currentImage.value = message.data.file_url
  showImagePreview.value = true
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}
</script>
```

**验收标准**:
- [ ] 支持拖拽上传图片
- [ ] 支持粘贴截图 (Ctrl+V)
- [ ] 支持PDF、Word、Excel文件上传
- [ ] 图片消息可点击预览大图
- [ ] 文档消息可下载
- [ ] 文件大小限制验证
- [ ] 文件类型限制验证
- [ ] 上传进度显示
- [ ] 文件存储到OSS/S3
- [ ] CDN加速访问

**预估工时**: 3天

---

### 任务8: 知识库系统 ⭐ P1

**当前状态**:
- ❌ 无知识库功能

**目标**:
实现知识库管理和快速插入功能

**功能需求**:

#### 8.1 知识库数据模型

```typescript
interface KnowledgeArticle {
  id: string
  title: string
  content: string  // Markdown格式
  category_id: string
  tags: string[]
  is_public: boolean  // 是否对外公开
  status: 'draft' | 'published' | 'archived'
  created_by: string
  created_at: number
  updated_at: number
  view_count: number
  use_count: number  // 被插入使用的次数
  helpful_count: number  // 客户点赞数
  attachments?: {
    file_name: string
    file_url: string
    file_size: number
  }[]
}

interface KnowledgeCategory {
  id: string
  name: string
  icon: string
  parent_id?: string  // 支持二级分类
  sort_order: number
  article_count: number
}
```

#### 8.2 分类体系

```typescript
const DEFAULT_CATEGORIES = [
  {
    id: 'pre_sales',
    name: '售前咨询',
    icon: 'QuestionFilled',
    children: [
      { id: 'product_selection', name: '选型建议' },
      { id: 'product_specs', name: '参数说明' },
      { id: 'pricing', name: '价格政策' },
      { id: 'promotions', name: '优惠活动' }
    ]
  },
  {
    id: 'orders',
    name: '订单相关',
    icon: 'ShoppingCart',
    children: [
      { id: 'order_payment', name: '支付方式' },
      { id: 'order_modify', name: '订单修改' },
      { id: 'order_cancel', name: '取消订单' },
      { id: 'invoice', name: '发票开具' }
    ]
  },
  {
    id: 'shipping',
    name: '物流配送',
    icon: 'Van',
    children: [
      { id: 'shipping_time', name: '配送时效' },
      { id: 'tracking', name: '物流追踪' },
      { id: 'customs', name: '清关说明' },
      { id: 'shipping_cost', name: '运费说明' }
    ]
  },
  {
    id: 'after_sales',
    name: '售后服务',
    icon: 'Tools',
    children: [
      { id: 'return_policy', name: '退换货政策' },
      { id: 'warranty', name: '保修条款' },
      { id: 'repair', name: '维修服务' },
      { id: 'spare_parts', name: '配件购买' }
    ]
  },
  {
    id: 'technical',
    name: '技术支持',
    icon: 'Setting',
    children: [
      { id: 'troubleshooting', name: '故障排查' },
      { id: 'user_manual', name: '使用教程' },
      { id: 'maintenance', name: '保养指南' },
      { id: 'firmware_update', name: '固件升级' }
    ]
  },
  {
    id: 'policies',
    name: '政策条款',
    icon: 'Document',
    children: [
      { id: 'privacy_policy', name: '隐私政策' },
      { id: 'terms_of_service', name: '服务条款' },
      { id: 'gdpr', name: 'GDPR合规' },
      { id: 'cookie_policy', name: 'Cookie政策' }
    ]
  }
]
```

#### 8.3 后端API实现

```python
from typing import List, Optional
from pydantic import BaseModel

# 数据模型
class KnowledgeArticle(BaseModel):
    id: str
    title: str
    content: str
    category_id: str
    tags: List[str] = Field(default_factory=list)
    is_public: bool = False
    status: Literal['draft', 'published', 'archived'] = 'draft'
    created_by: str
    created_at: float
    updated_at: float
    view_count: int = 0
    use_count: int = 0
    helpful_count: int = 0

class KnowledgeCategory(BaseModel):
    id: str
    name: str
    icon: str
    parent_id: Optional[str] = None
    sort_order: int = 0
    article_count: int = 0

# Redis存储
class KnowledgeStore:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.article_key_prefix = "knowledge:article:"
        self.category_key_prefix = "knowledge:category:"
        self.index_key = "knowledge:index"

    async def create_article(self, article: KnowledgeArticle) -> str:
        """创建知识库文章"""
        article_id = f"kb_{int(time.time() * 1000)}"
        article.id = article_id
        article.created_at = time.time()
        article.updated_at = time.time()

        # 保存文章
        await self.redis.set(
            f"{self.article_key_prefix}{article_id}",
            article.json(),
            ex=86400 * 365  # 1年过期
        )

        # 添加到索引
        await self.redis.sadd(f"knowledge:category:{article.category_id}", article_id)
        await self.redis.sadd(self.index_key, article_id)

        # 全文搜索索引（使用Redis Search）
        await self._index_article(article)

        return article_id

    async def search_articles(
        self,
        query: str,
        category_id: Optional[str] = None,
        limit: int = 20
    ) -> List[KnowledgeArticle]:
        """搜索知识库文章"""
        # 使用Redis Search进行全文搜索
        # 或者简单实现：遍历所有文章匹配标题和内容

        article_ids = await self.redis.smembers(self.index_key)
        results = []

        for article_id in article_ids:
            article_json = await self.redis.get(f"{self.article_key_prefix}{article_id}")
            if not article_json:
                continue

            article = KnowledgeArticle.parse_raw(article_json)

            # 仅返回已发布的文章
            if article.status != 'published':
                continue

            # 分类过滤
            if category_id and article.category_id != category_id:
                continue

            # 关键词匹配
            if query:
                if (query.lower() in article.title.lower() or
                    query.lower() in article.content.lower() or
                    any(query.lower() in tag.lower() for tag in article.tags)):
                    results.append(article)
            else:
                results.append(article)

        # 按使用次数排序
        results.sort(key=lambda x: x.use_count, reverse=True)

        return results[:limit]

knowledge_store = KnowledgeStore(redis_client)

# API接口
@app.get("/api/knowledge/articles")
async def get_knowledge_articles(
    query: Optional[str] = None,
    category_id: Optional[str] = None,
    status: Optional[str] = 'published',
    limit: int = 20,
    agent: dict = Depends(require_agent)
):
    """获取知识库文章列表"""
    articles = await knowledge_store.search_articles(query, category_id, limit)
    return {"articles": articles}

@app.get("/api/knowledge/articles/{article_id}")
async def get_knowledge_article(
    article_id: str,
    agent: dict = Depends(require_agent)
):
    """获取知识库文章详情"""
    article_json = await redis_client.get(f"knowledge:article:{article_id}")
    if not article_json:
        raise HTTPException(404, "文章不存在")

    article = KnowledgeArticle.parse_raw(article_json)

    # 增加浏览次数
    article.view_count += 1
    await redis_client.set(
        f"knowledge:article:{article_id}",
        article.json(),
        ex=86400 * 365
    )

    return {"article": article}

@app.post("/api/knowledge/articles")
async def create_knowledge_article(
    request: CreateKnowledgeArticleRequest,
    agent: dict = Depends(require_admin)  # 仅管理员可创建
):
    """创建知识库文章"""
    article = KnowledgeArticle(
        id="",  # 自动生成
        title=request.title,
        content=request.content,
        category_id=request.category_id,
        tags=request.tags,
        is_public=request.is_public,
        status=request.status,
        created_by=agent["agent_id"],
        created_at=0,  # 自动设置
        updated_at=0,
        view_count=0,
        use_count=0,
        helpful_count=0
    )

    article_id = await knowledge_store.create_article(article)

    return {
        "success": True,
        "article_id": article_id
    }

@app.put("/api/knowledge/articles/{article_id}")
async def update_knowledge_article(
    article_id: str,
    request: UpdateKnowledgeArticleRequest,
    agent: dict = Depends(require_admin)
):
    """更新知识库文章"""
    article_json = await redis_client.get(f"knowledge:article:{article_id}")
    if not article_json:
        raise HTTPException(404, "文章不存在")

    article = KnowledgeArticle.parse_raw(article_json)

    # 更新字段
    if request.title is not None:
        article.title = request.title
    if request.content is not None:
        article.content = request.content
    if request.category_id is not None:
        article.category_id = request.category_id
    if request.tags is not None:
        article.tags = request.tags
    if request.status is not None:
        article.status = request.status

    article.updated_at = time.time()

    await redis_client.set(
        f"knowledge:article:{article_id}",
        article.json(),
        ex=86400 * 365
    )

    return {"success": True}

@app.post("/api/sessions/{session_name}/insert-knowledge")
async def insert_knowledge_article(
    session_name: str,
    request: InsertKnowledgeRequest,
    agent: dict = Depends(require_agent)
):
    """
    在会话中插入知识库文章

    request.article_id: 知识库文章ID
    """
    # 1. 获取文章内容
    article_json = await redis_client.get(f"knowledge:article:{request.article_id}")
    if not article_json:
        raise HTTPException(404, "文章不存在")

    article = KnowledgeArticle.parse_raw(article_json)

    # 2. 增加使用次数
    article.use_count += 1
    await redis_client.set(
        f"knowledge:article:{request.article_id}",
        article.json(),
        ex=86400 * 365
    )

    # 3. 构建消息（发送文章内容）
    message_content = f"📚 {article.title}\n\n{article.content}"

    # 4. 保存到会话历史
    session_state = await session_store.get_session_state(session_name)
    session_state.messages.append({
        "role": "assistant",
        "content": message_content,
        "timestamp": time.time(),
        "agent_id": agent["agent_id"],
        "knowledge_article_id": request.article_id
    })
    await session_store.save_session_state(session_state)

    # 5. 推送到用户SSE
    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "manual_message",
            "content": message_content,
            "agent_id": agent["agent_id"],
            "timestamp": time.time()
        })

    return {"success": True}

@app.get("/api/knowledge/categories")
async def get_knowledge_categories():
    """获取知识库分类"""
    # 返回预设分类
    return {"categories": DEFAULT_CATEGORIES}
```

#### 8.4 前端实现 (坐席工作台)

```vue
<template>
  <div class="knowledge-base">
    <!-- 搜索栏 -->
    <div class="search-section">
      <el-input
        v-model="searchQuery"
        placeholder="🔍 搜索知识库..."
        prefix-icon="Search"
        @input="handleSearch"
        clearable
      />
    </div>

    <!-- 分类导航 -->
    <div class="category-nav">
      <el-menu
        :default-active="activeCategory"
        @select="handleCategorySelect"
      >
        <el-menu-item index="all">
          <el-icon><Document /></el-icon>
          <span>全部文章</span>
        </el-menu-item>

        <el-sub-menu
          v-for="category in categories"
          :key="category.id"
          :index="category.id"
        >
          <template #title>
            <el-icon :component="category.icon" />
            <span>{{ category.name }}</span>
          </template>

          <el-menu-item
            v-for="subCategory in category.children"
            :key="subCategory.id"
            :index="subCategory.id"
          >
            {{ subCategory.name }}
          </el-menu-item>
        </el-sub-menu>
      </el-menu>
    </div>

    <!-- 文章列表 -->
    <div class="article-list">
      <div
        v-for="article in articles"
        :key="article.id"
        class="article-item"
        @click="viewArticle(article)"
      >
        <h3>{{ article.title }}</h3>
        <p class="article-excerpt">
          {{ getExcerpt(article.content) }}
        </p>
        <div class="article-meta">
          <span class="use-count">📊 使用 {{ article.use_count }} 次</span>
          <span class="helpful-count">👍 {{ article.helpful_count }}</span>
          <el-button
            type="primary"
            size="small"
            @click.stop="insertArticle(article)"
          >
            快速插入
          </el-button>
        </div>
      </div>
    </div>

    <!-- 文章详情弹窗 -->
    <el-dialog
      v-model="showArticleDialog"
      :title="currentArticle?.title"
      width="60%"
    >
      <div class="article-content" v-html="renderMarkdown(currentArticle?.content)"></div>

      <template #footer>
        <el-button @click="showArticleDialog = false">关闭</el-button>
        <el-button type="primary" @click="insertArticle(currentArticle)">
          插入到会话
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { searchKnowledgeArticles, insertKnowledgeArticle } from '@/api/knowledge'
import { marked } from 'marked'

const searchQuery = ref('')
const activeCategory = ref('all')
const articles = ref([])
const categories = ref([])
const showArticleDialog = ref(false)
const currentArticle = ref(null)

async function handleSearch() {
  const { data } = await searchKnowledgeArticles({
    query: searchQuery.value,
    category_id: activeCategory.value === 'all' ? null : activeCategory.value
  })
  articles.value = data.articles
}

function handleCategorySelect(categoryId: string) {
  activeCategory.value = categoryId
  handleSearch()
}

function getExcerpt(content: string): string {
  // 提取前100个字符作为摘要
  return content.substring(0, 100) + '...'
}

function viewArticle(article) {
  currentArticle.value = article
  showArticleDialog.value = true
}

async function insertArticle(article) {
  await insertKnowledgeArticle(currentSession.value, article.id)
  ElMessage.success('知识库文章已插入')
  showArticleDialog.value = false
}

function renderMarkdown(content: string): string {
  return marked(content)
}

onMounted(async () => {
  // 加载分类
  const { data: categoryData } = await getKnowledgeCategories()
  categories.value = categoryData.categories

  // 加载文章
  handleSearch()
})
</script>

<style scoped>
.knowledge-base {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.search-section {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
}

.category-nav {
  border-right: 1px solid #e5e7eb;
  overflow-y: auto;
}

.article-list {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
}

.article-item {
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.article-item:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.article-excerpt {
  color: #6b7280;
  font-size: 14px;
  margin: 8px 0;
}

.article-meta {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 13px;
  color: #9ca3af;
}
</style>
```

**验收标准**:
- [ ] 支持6个主分类，每个分类4个子分类
- [ ] 支持Markdown格式文章
- [ ] 支持全文搜索（标题、内容、标签）
- [ ] 支持按分类筛选
- [ ] 文章详情弹窗预览
- [ ] 一键插入文章到会话
- [ ] 记录使用次数统计
- [ ] 管理员可创建/编辑文章
- [ ] 支持草稿/发布/归档状态
- [ ] 支持文章附件

**预估工时**: 5天

---

### 任务9: 实时数据统计 ⭐ P1

**当前状态**:
- ✅ 基础会话统计 (GET /api/sessions/stats)
- ❌ 无实时数据看板

**目标**:
实现实时数据统计看板，展示关键指标

**功能需求**:

#### 9.1 统计指标定义

```typescript
interface RealtimeStats {
  // 今日数据
  today: {
    total_sessions: number       // 总会话数
    active_sessions: number       // 活跃会话数
    completed_sessions: number    // 已完成会话数
    avg_response_time: number     // 平均响应时间(秒)
    avg_session_duration: number  // 平均会话时长(秒)
    customer_satisfaction: number // 客户满意度(0-5)
  }

  // 坐席数据
  agents: {
    online_count: number          // 在线坐席数
    total_count: number           // 总坐席数
    busy_count: number            // 繁忙坐席数
    idle_count: number            // 空闲坐席数
  }

  // 排队数据
  queue: {
    waiting_count: number         // 排队人数
    avg_wait_time: number         // 平均等待时间(秒)
    max_wait_time: number         // 最长等待时间(秒)
  }

  // 个人数据(当前坐席)
  personal: {
    today_sessions: number        // 今日接待量
    avg_response_time: number     // 平均响应时间
    customer_satisfaction: number // 客户满意度
    rank: number                  // 团队排名
  }
}
```

#### 9.2 UI设计

**看板布局**:
```
┌─────────────────────────────────────────────────────────────┐
│ 📊 实时数据看板                         刷新时间: 14:35:22   │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────┬─────────────┬─────────────┬─────────────┐  │
│ │ 今日会话    │ 活跃会话    │ 平均响应    │ 客户满意度  │  │
│ │    156      │    12       │    8.5s     │   4.8/5.0   │  │
│ │ ↑ 12%       │             │ ↓ 2.1s      │  ⭐⭐⭐⭐⭐   │  │
│ └─────────────┴─────────────┴─────────────┴─────────────┘  │
│                                                              │
│ ┌──────────────────────────┬──────────────────────────┐    │
│ │ 🧑‍💼 坐席状态             │ 📋 排队情况              │    │
│ │                          │                          │    │
│ │ 在线: 8/12               │ 排队人数: 3              │    │
│ │ 繁忙: 5                  │ 平均等待: 2分15秒        │    │
│ │ 空闲: 3                  │ 最长等待: 5分30秒        │    │
│ └──────────────────────────┴──────────────────────────┘    │
│                                                              │
│ ┌──────────────────────────────────────────────────────┐   │
│ │ 📈 我的今日数据                                       │   │
│ │                                                       │   │
│ │ 接待量: 23  响应时间: 7.2s  满意度: 4.9  排名: 2/12  │   │
│ │                                                       │   │
│ │ [查看详细报表]                                        │   │
│ └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

#### 9.3 后端实现

```python
class StatsService:
    def __init__(self, redis_client):
        self.redis = redis_client

    async def get_realtime_stats(self, agent_id: Optional[str] = None) -> dict:
        """获取实时统计数据"""
        now = time.time()
        today_start = datetime.now().replace(hour=0, minute=0, second=0).timestamp()

        # 1. 今日会话数据
        all_sessions = await self._get_all_sessions()
        today_sessions = [s for s in all_sessions if s.created_at >= today_start]
        active_sessions = [s for s in today_sessions if s.status in ['bot_active', 'pending_manual', 'manual_live']]
        completed_sessions = [s for s in today_sessions if s.status == 'ended']

        # 2. 计算平均响应时间
        response_times = []
        for session in today_sessions:
            if len(session.messages) >= 2:
                # 客户消息 -> 坐席响应的时间差
                user_msg_time = None
                for msg in session.messages:
                    if msg['role'] == 'user':
                        user_msg_time = msg['timestamp']
                    elif msg['role'] == 'assistant' and user_msg_time:
                        response_time = msg['timestamp'] - user_msg_time
                        response_times.append(response_time)
                        user_msg_time = None

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # 3. 计算平均会话时长
        session_durations = []
        for session in completed_sessions:
            if session.messages:
                duration = session.messages[-1]['timestamp'] - session.messages[0]['timestamp']
                session_durations.append(duration)

        avg_session_duration = sum(session_durations) / len(session_durations) if session_durations else 0

        # 4. 坐席状态
        all_agents = await self._get_all_agents()
        online_agents = [a for a in all_agents if await self._is_agent_online(a.agent_id)]
        busy_agents = [a for a in online_agents if await self._is_agent_busy(a.agent_id)]
        idle_agents = [a for a in online_agents if not await self._is_agent_busy(a.agent_id)]

        # 5. 排队数据
        waiting_sessions = [s for s in active_sessions if s.status == 'pending_manual']
        wait_times = []
        for session in waiting_sessions:
            wait_time = now - session.created_at
            wait_times.append(wait_time)

        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        max_wait_time = max(wait_times) if wait_times else 0

        # 6. 个人数据(如果提供agent_id)
        personal_stats = None
        if agent_id:
            personal_sessions = [s for s in today_sessions if s.assigned_agent == agent_id]
            personal_response_times = [rt for rt, s in zip(response_times, today_sessions) if s.assigned_agent == agent_id]
            personal_avg_response = sum(personal_response_times) / len(personal_response_times) if personal_response_times else 0

            # 计算排名
            agent_session_counts = {}
            for agent in all_agents:
                agent_session_counts[agent.agent_id] = len([s for s in today_sessions if s.assigned_agent == agent.agent_id])

            sorted_agents = sorted(agent_session_counts.items(), key=lambda x: x[1], reverse=True)
            rank = next((i + 1 for i, (aid, _) in enumerate(sorted_agents) if aid == agent_id), 0)

            personal_stats = {
                "today_sessions": len(personal_sessions),
                "avg_response_time": round(personal_avg_response, 1),
                "customer_satisfaction": 4.8,  # TODO: 实现满意度评分
                "rank": rank
            }

        return {
            "today": {
                "total_sessions": len(today_sessions),
                "active_sessions": len(active_sessions),
                "completed_sessions": len(completed_sessions),
                "avg_response_time": round(avg_response_time, 1),
                "avg_session_duration": round(avg_session_duration, 1),
                "customer_satisfaction": 4.7  # TODO: 实现满意度评分
            },
            "agents": {
                "online_count": len(online_agents),
                "total_count": len(all_agents),
                "busy_count": len(busy_agents),
                "idle_count": len(idle_agents)
            },
            "queue": {
                "waiting_count": len(waiting_sessions),
                "avg_wait_time": round(avg_wait_time, 1),
                "max_wait_time": round(max_wait_time, 1)
            },
            "personal": personal_stats,
            "timestamp": now
        }

stats_service = StatsService(redis_client)

@app.get("/api/stats/realtime")
async def get_realtime_stats(agent: dict = Depends(require_agent)):
    """获取实时统计数据"""
    stats = await stats_service.get_realtime_stats(agent_id=agent["agent_id"])
    return stats

# SSE推送实时数据
@app.get("/api/stats/stream")
async def stream_realtime_stats(agent: dict = Depends(require_agent)):
    """SSE流式推送实时数据"""
    async def generate():
        while True:
            stats = await stats_service.get_realtime_stats(agent_id=agent["agent_id"])
            yield f"data: {json.dumps(stats)}\n\n"
            await asyncio.sleep(5)  # 每5秒推送一次

    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 9.4 前端实现

```vue
<template>
  <div class="statistics-dashboard">
    <!-- 刷新时间 -->
    <div class="header">
      <h2>📊 实时数据看板</h2>
      <span class="refresh-time">刷新时间: {{ formatTime(stats.timestamp) }}</span>
    </div>

    <!-- 核心指标卡片 -->
    <div class="metrics-cards">
      <div class="metric-card">
        <div class="metric-label">今日会话</div>
        <div class="metric-value">{{ stats.today.total_sessions }}</div>
        <div class="metric-trend positive">↑ 12%</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">活跃会话</div>
        <div class="metric-value">{{ stats.today.active_sessions }}</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">平均响应</div>
        <div class="metric-value">{{ stats.today.avg_response_time }}s</div>
        <div class="metric-trend negative">↓ 2.1s</div>
      </div>

      <div class="metric-card">
        <div class="metric-label">客户满意度</div>
        <div class="metric-value">{{ stats.today.customer_satisfaction }}/5.0</div>
        <el-rate
          :model-value="stats.today.customer_satisfaction"
          disabled
          show-score
          text-color="#ff9900"
        />
      </div>
    </div>

    <!-- 坐席和排队 -->
    <div class="info-panels">
      <div class="panel">
        <h3>🧑‍💼 坐席状态</h3>
        <div class="panel-content">
          <div class="stat-row">
            <span>在线:</span>
            <strong>{{ stats.agents.online_count }}/{{ stats.agents.total_count }}</strong>
          </div>
          <div class="stat-row">
            <span>繁忙:</span>
            <strong class="text-orange">{{ stats.agents.busy_count }}</strong>
          </div>
          <div class="stat-row">
            <span>空闲:</span>
            <strong class="text-green">{{ stats.agents.idle_count }}</strong>
          </div>
        </div>
      </div>

      <div class="panel">
        <h3>📋 排队情况</h3>
        <div class="panel-content">
          <div class="stat-row">
            <span>排队人数:</span>
            <strong class="text-red">{{ stats.queue.waiting_count }}</strong>
          </div>
          <div class="stat-row">
            <span>平均等待:</span>
            <strong>{{ formatDuration(stats.queue.avg_wait_time) }}</strong>
          </div>
          <div class="stat-row">
            <span>最长等待:</span>
            <strong class="text-orange">{{ formatDuration(stats.queue.max_wait_time) }}</strong>
          </div>
        </div>
      </div>
    </div>

    <!-- 个人数据 -->
    <div v-if="stats.personal" class="personal-panel">
      <h3>📈 我的今日数据</h3>
      <div class="personal-stats">
        <div class="personal-stat">
          <span>接待量</span>
          <strong>{{ stats.personal.today_sessions }}</strong>
        </div>
        <div class="personal-stat">
          <span>响应时间</span>
          <strong>{{ stats.personal.avg_response_time }}s</strong>
        </div>
        <div class="personal-stat">
          <span>满意度</span>
          <strong>{{ stats.personal.customer_satisfaction }}</strong>
        </div>
        <div class="personal-stat">
          <span>排名</span>
          <strong class="rank">{{ stats.personal.rank }}/{{ stats.agents.total_count }}</strong>
        </div>
      </div>
      <el-button type="primary" @click="viewDetailedReport">
        查看详细报表
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const stats = ref({
  today: {},
  agents: {},
  queue: {},
  personal: null,
  timestamp: 0
})

let eventSource: EventSource | null = null

onMounted(() => {
  // 连接SSE接收实时数据
  eventSource = new EventSource('/api/stats/stream')

  eventSource.onmessage = (event) => {
    stats.value = JSON.parse(event.data)
  }

  eventSource.onerror = () => {
    console.error('SSE connection error')
    // 重连逻辑
    setTimeout(() => {
      eventSource?.close()
      onMounted()
    }, 5000)
  }
})

onUnmounted(() => {
  eventSource?.close()
})

function formatTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleTimeString('zh-CN')
}

function formatDuration(seconds: number): string {
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}分${secs}秒`
}
</script>

<style scoped>
.statistics-dashboard {
  padding: 24px;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.metric-card {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.metric-value {
  font-size: 32px;
  font-weight: bold;
  margin: 8px 0;
}

.metric-trend {
  font-size: 14px;
  font-weight: 500;
}

.metric-trend.positive {
  color: #10b981;
}

.metric-trend.negative {
  color: #ef4444;
}

.info-panels {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.panel {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

.stat-row {
  display: flex;
  justify-content: space-between;
  margin: 12px 0;
}

.personal-panel {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 24px;
  border-radius: 8px;
}

.personal-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 16px 0;
}

.personal-stat {
  text-align: center;
}

.personal-stat strong {
  display: block;
  font-size: 24px;
  margin-top: 8px;
}
</style>
```

**验收标准**:
- [ ] 显示今日会话总数、活跃数、已完成数
- [ ] 显示平均响应时间、会话时长
- [ ] 显示客户满意度评分
- [ ] 显示在线坐席数、繁忙/空闲状态
- [ ] 显示排队人数、平均等待时间
- [ ] 显示个人今日数据和团队排名
- [ ] SSE实时推送数据(每5秒更新)
- [ ] 趋势对比(与昨日对比)
- [ ] 响应式布局

**预估工时**: 3天

---

### 任务10: 物流追踪集成 ⭐ P1

**当前状态**:
- ✅ Shopify订单中包含物流单号
- ❌ 无物流追踪功能

**目标**:
集成DHL、FedEx、UPS物流查询API

**功能需求**:

#### 10.1 支持的物流公司

```typescript
enum Carrier {
  DHL = 'dhl',
  FEDEX = 'fedex',
  UPS = 'ups',
  USPS = 'usps',
  DPD = 'dpd',
  HERMES = 'hermes'
}

interface TrackingInfo {
  tracking_number: string
  carrier: Carrier
  status: 'in_transit' | 'out_for_delivery' | 'delivered' | 'exception' | 'pending'
  current_location: string
  estimated_delivery: string
  events: TrackingEvent[]
}

interface TrackingEvent {
  timestamp: number
  location: string
  status: string
  description: string
}
```

#### 10.2 物流API集成

```python
import httpx
from typing import Optional

class DHLTrackingService:
    """DHL物流追踪服务"""

    def __init__(self):
        self.api_key = os.getenv("DHL_API_KEY")
        self.base_url = "https://api-eu.dhl.com/track/shipments"

    async def track(self, tracking_number: str) -> dict:
        """查询DHL物流信息"""
        url = f"{self.base_url}?trackingNumber={tracking_number}"
        headers = {
            "DHL-API-Key": self.api_key
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()

        # 解析DHL响应
        shipment = data['shipments'][0]
        events = shipment.get('events', [])

        return {
            "tracking_number": tracking_number,
            "carrier": "dhl",
            "status": self._map_status(shipment['status']['statusCode']),
            "current_location": events[0]['location']['address']['addressLocality'] if events else "",
            "estimated_delivery": shipment.get('estimatedTimeOfDelivery'),
            "events": [
                {
                    "timestamp": event['timestamp'],
                    "location": event['location']['address']['addressLocality'],
                    "status": event['statusCode'],
                    "description": event['description']
                }
                for event in events
            ]
        }

    def _map_status(self, dhl_status: str) -> str:
        """映射DHL状态到统一状态"""
        mapping = {
            'transit': 'in_transit',
            'delivered': 'delivered',
            'failure': 'exception',
            'pre-transit': 'pending'
        }
        return mapping.get(dhl_status, 'in_transit')

class FedExTrackingService:
    """FedEx物流追踪服务"""

    def __init__(self):
        self.api_key = os.getenv("FEDEX_API_KEY")
        self.secret_key = os.getenv("FEDEX_SECRET_KEY")
        self.base_url = "https://apis.fedex.com/track/v1/trackingnumbers"

    async def track(self, tracking_number: str) -> dict:
        """查询FedEx物流信息"""
        # FedEx需要OAuth认证
        access_token = await self._get_access_token()

        url = self.base_url
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        payload = {
            "trackingInfo": [
                {
                    "trackingNumberInfo": {
                        "trackingNumber": tracking_number
                    }
                }
            ],
            "includeDetailedScans": True
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        # 解析FedEx响应
        track_result = data['output']['completeTrackResults'][0]['trackResults'][0]

        return {
            "tracking_number": tracking_number,
            "carrier": "fedex",
            "status": self._map_status(track_result['latestStatusDetail']['code']),
            "current_location": track_result['latestStatusDetail']['scanLocation'].get('city', ''),
            "estimated_delivery": track_result.get('estimatedDeliveryTime'),
            "events": [
                {
                    "timestamp": event['date'],
                    "location": event.get('scanLocation', {}).get('city', ''),
                    "status": event['eventDescription'],
                    "description": event['eventDescription']
                }
                for event in track_result.get('scanEvents', [])
            ]
        }

    async def _get_access_token(self) -> str:
        """获取FedEx OAuth Token"""
        # 实现OAuth流程
        pass

class UnifiedTrackingService:
    """统一物流追踪服务"""

    def __init__(self):
        self.services = {
            Carrier.DHL: DHLTrackingService(),
            Carrier.FEDEX: FedExTrackingService(),
            # ...其他物流公司
        }

    async def track(
        self,
        tracking_number: str,
        carrier: Optional[Carrier] = None
    ) -> dict:
        """
        查询物流信息

        如果不指定carrier，自动识别
        """
        if not carrier:
            carrier = self._detect_carrier(tracking_number)

        service = self.services.get(carrier)
        if not service:
            raise HTTPException(400, f"不支持的物流公司: {carrier}")

        return await service.track(tracking_number)

    def _detect_carrier(self, tracking_number: str) -> Carrier:
        """根据单号格式识别物流公司"""
        # DHL: 10位数字
        if re.match(r'^\d{10}$', tracking_number):
            return Carrier.DHL

        # FedEx: 12位数字
        if re.match(r'^\d{12}$', tracking_number):
            return Carrier.FEDEX

        # UPS: 1Z开头
        if tracking_number.startswith('1Z'):
            return Carrier.UPS

        raise HTTPException(400, "无法识别物流公司，请手动指定")

tracking_service = UnifiedTrackingService()

# API接口
@app.get("/api/tracking/{tracking_number}")
async def track_shipment(
    tracking_number: str,
    carrier: Optional[Carrier] = None,
    agent: dict = Depends(require_agent)
):
    """查询物流信息"""
    try:
        tracking_info = await tracking_service.track(tracking_number, carrier)
        return tracking_info
    except Exception as e:
        raise HTTPException(500, f"物流查询失败: {str(e)}")

@app.post("/api/sessions/{session_name}/send-tracking")
async def send_tracking_info(
    session_name: str,
    request: SendTrackingRequest,
    agent: dict = Depends(require_agent)
):
    """发送物流信息到用户会话"""
    # 1. 查询物流信息
    tracking_info = await tracking_service.track(
        request.tracking_number,
        request.carrier
    )

    # 2. 构建消息
    message = {
        "type": "tracking_info",
        "data": tracking_info
    }

    # 3. 保存到会话历史
    session_state = await session_store.get_session_state(session_name)
    session_state.messages.append({
        "role": "assistant",
        "content": json.dumps(message, ensure_ascii=False),
        "timestamp": time.time(),
        "agent_id": agent["agent_id"]
    })
    await session_store.save_session_state(session_state)

    # 4. 推送到用户SSE
    if session_name in sse_queues:
        await sse_queues[session_name].put({
            "type": "tracking_info",
            "data": tracking_info
        })

    return {"success": True}
```

#### 10.3 前端实现 (用户端)

```vue
<template>
  <div class="tracking-info">
    <!-- 物流状态卡片 -->
    <div class="tracking-card">
      <div class="tracking-header">
        <h3>📦 物流信息</h3>
        <span class="carrier-badge">{{ carrierName(tracking.carrier) }}</span>
      </div>

      <div class="tracking-number">
        运单号: {{ tracking.tracking_number }}
        <el-button text @click="copyTrackingNumber">复制</el-button>
      </div>

      <div class="current-status">
        <div
          class="status-badge"
          :class="`status-${tracking.status}`"
        >
          {{ statusText(tracking.status) }}
        </div>
        <p class="current-location">
          当前位置: {{ tracking.current_location }}
        </p>
        <p v-if="tracking.estimated_delivery" class="estimated-delivery">
          预计送达: {{ formatDate(tracking.estimated_delivery) }}
        </p>
      </div>

      <!-- 物流轨迹时间线 -->
      <div class="tracking-timeline">
        <h4>物流轨迹</h4>
        <el-timeline>
          <el-timeline-item
            v-for="(event, index) in tracking.events"
            :key="index"
            :timestamp="formatDateTime(event.timestamp)"
            :color="index === 0 ? '#3b82f6' : '#9ca3af'"
          >
            <div class="event-location">{{ event.location }}</div>
            <div class="event-description">{{ event.description }}</div>
          </el-timeline-item>
        </el-timeline>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { defineProps } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps<{
  tracking: TrackingInfo
}>()

function carrierName(carrier: string): string {
  const names = {
    'dhl': 'DHL',
    'fedex': 'FedEx',
    'ups': 'UPS',
    'usps': 'USPS',
    'dpd': 'DPD'
  }
  return names[carrier] || carrier.toUpperCase()
}

function statusText(status: string): string {
  const texts = {
    'in_transit': '运输中',
    'out_for_delivery': '派送中',
    'delivered': '已签收',
    'exception': '异常',
    'pending': '待揽收'
  }
  return texts[status] || status
}

function copyTrackingNumber() {
  navigator.clipboard.writeText(props.tracking.tracking_number)
  ElMessage.success('运单号已复制')
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('zh-CN')
}

function formatDateTime(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleString('zh-CN')
}
</script>

<style scoped>
.tracking-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  max-width: 600px;
}

.tracking-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.carrier-badge {
  background: #3b82f6;
  color: white;
  padding: 4px 12px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.tracking-number {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 4px;
  margin-bottom: 20px;
  font-family: monospace;
}

.current-status {
  margin-bottom: 24px;
}

.status-badge {
  display: inline-block;
  padding: 6px 16px;
  border-radius: 20px;
  font-weight: 500;
  margin-bottom: 12px;
}

.status-in_transit {
  background: #dbeafe;
  color: #1e40af;
}

.status-out_for_delivery {
  background: #fef3c7;
  color: #92400e;
}

.status-delivered {
  background: #d1fae5;
  color: #065f46;
}

.status-exception {
  background: #fee2e2;
  color: #991b1b;
}

.tracking-timeline {
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

.event-location {
  font-weight: 500;
  margin-bottom: 4px;
}

.event-description {
  color: #6b7280;
  font-size: 14px;
}
</style>
```

**验收标准**:
- [ ] 支持DHL、FedEx、UPS物流查询
- [ ] 自动识别物流公司(根据单号格式)
- [ ] 显示当前物流状态和位置
- [ ] 显示预计送达时间
- [ ] 物流轨迹时间线展示
- [ ] 运单号一键复制
- [ ] 异常件红色提醒
- [ ] 已签收绿色标记
- [ ] 物流信息卡片发送到用户
- [ ] 缓存物流查询结果(5分钟)

**预估工时**: 4天

---

## 📦 Phase 2 总结

**总预估工时**: 19天 (约4周)
**版本号**: v3.6.0
**发布时间**: 预计1个月后

**核心成果**:
- ✅ 商品/订单卡片发送 (4天)
- ✅ 图片/文件发送功能 (3天)
- ✅ 知识库系统 (5天)
- ✅ 实时数据统计 (3天)
- ✅ 物流追踪集成 (4天)

**技术栈新增**:
- 阿里云OSS/AWS S3 (文件存储)
- DHL/FedEx/UPS API (物流追踪)
- Marked.js (Markdown渲染)
- Element Plus Timeline (时间线组件)

**后续计划**:
- Phase 3: 高级特性 (多店铺、绩效、消费统计)
- Phase 4: 智能化 (智能路由、AI推荐)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-26
**版本**: v1.0
**状态**: ✅ 待评审
