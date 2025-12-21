# 素材服务规范

> **服务定位**：产品图片匹配、场景素材获取、CDN 分发
> **服务状态**：已完成
> **最后更新**：2025-12-21

---

## 一、服务职责

- 产品/配件图片智能匹配（支持名称和 SKU 模糊匹配）
- 场景素材获取（欢迎、订单查询、产品咨询等）
- 品牌 Logo 资源管理
- 支持 CDN 模式和本地资源两种分发方式

---

## 二、公开接口

```python
# 核心匹配函数
def match_product_image(
    product_name: str,
    sku: Optional[str] = None,
    base_url: str = "",
    use_thumb: bool = True
) -> Optional[Dict]:
    """根据产品名称或 SKU 匹配产品图片"""

def match_order_items_images(
    line_items: List[Dict],
    base_url: str = ""
) -> List[Dict]:
    """为订单商品列表批量匹配图片"""

# 场景素材
def get_scene_assets(scene: str, base_url: str = "") -> Dict:
    """获取场景对应的素材"""

# 品牌资源
def get_brand_logo(base_url: str = "", white: bool = False) -> Optional[str]:
    """获取品牌 Logo URL"""

# 产品列表
def get_all_products(base_url: str = "") -> List[Dict]:
    """获取所有产品信息"""

# 工具函数
def is_cdn_mode() -> bool:
    """检查是否启用 CDN 模式"""

def reload_mapping():
    """重新加载映射表"""
```

---

## 三、目录结构

```
services/asset/
├── __init__.py          # 模块初始化
├── README.md            # 本文档
├── service.py           # 素材匹配服务
├── data/                # 素材数据
│   ├── assets_mapping.json   # 产品/配件/场景映射表
│   ├── products/        # 产品图片
│   ├── accessories/     # 配件图片
│   └── brand/           # 品牌资源
└── tools/               # 素材处理工具
    └── crawler.py       # 爬虫工具（可选）
```

---

## 四、素材匹配规则

| 匹配方式 | 优先级 | 匹配度 |
|----------|--------|--------|
| SKU 精确匹配 | 最高 | 1.0 |
| SKU 部分匹配 | 高 | 0.95 |
| 名称精确匹配 | 中 | 0.95 |
| 名称模糊匹配 | 低 | 0.5-0.9 |

**匹配阈值**：匹配度 > 0.5 才返回结果

---

## 五、配置说明

### 5.1 CDN 模式

在 `data/assets_mapping.json` 中配置：

```json
{
  "cdn_mode": true,
  "base_url": "https://ai.fiido.com/assets",
  "products": {
    "c11-pro": {
      "title": "Fiido C11 Pro",
      "cdn_url": "https://cdn.fiido.com/..."
    }
  }
}
```

### 5.2 本地模式

将 `cdn_mode` 设为 `false`，使用 `base_url` + 相对路径拼接。

---

## 六、使用示例

```python
from services.asset.service import match_product_image, get_brand_logo

# 匹配产品图片
result = match_product_image(
    product_name="Fiido C11 Pro",
    sku="C11PRO-104B-US",
    base_url="https://ai.fiido.com/assets"
)
if result:
    print(f"图片: {result['image_url']}")
    print(f"匹配度: {result['match_score']}")

# 获取品牌 Logo
logo_url = get_brand_logo(base_url="https://ai.fiido.com/assets")
```

---

## 七、文档更新记录

| 版本 | 日期 | 变更 |
|------|------|------|
| v1.0 | 2025-12-21 | 初始版本 |
