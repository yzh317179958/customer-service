"""
素材服务模块

提供产品图片匹配、场景素材获取等功能
支持官网 CDN URL 和本地资源两种模式
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from difflib import SequenceMatcher

# 配置
ASSETS_DIR = Path(__file__).parent.parent / "assets"
MAPPING_FILE = ASSETS_DIR / "assets_mapping.json"

# 缓存
_mapping_cache: Optional[Dict] = None


def load_mapping() -> Dict:
    """加载素材映射表"""
    global _mapping_cache

    if _mapping_cache is not None:
        return _mapping_cache

    if not MAPPING_FILE.exists():
        return {"products": {}, "accessories": {}, "brand": {}, "scenes": {}, "cdn_mode": False}

    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        _mapping_cache = json.load(f)

    return _mapping_cache


def is_cdn_mode() -> bool:
    """检查是否启用 CDN 模式"""
    mapping = load_mapping()
    return mapping.get("cdn_mode", False)


def reload_mapping():
    """重新加载映射表（用于更新后刷新）"""
    global _mapping_cache
    _mapping_cache = None
    return load_mapping()


def get_asset_url(asset_path: str, base_url: str = "") -> str:
    """
    获取素材的完整 URL

    Args:
        asset_path: 素材相对路径 (如 "products/c11-pro.webp")
        base_url: 基础 URL (如 "https://ai.fiido.com/assets")

    Returns:
        完整的素材 URL
    """
    if not base_url:
        mapping = load_mapping()
        base_url = mapping.get("base_url", "/assets")

    return f"{base_url.rstrip('/')}/{asset_path}"


def match_product_image(
    product_name: str,
    sku: Optional[str] = None,
    base_url: str = "",
    use_thumb: bool = True
) -> Optional[Dict]:
    """
    根据产品名称或 SKU 匹配产品或配件图片

    Args:
        product_name: 产品/配件名称（如 "Titan Fat Tire Touring Ebike" 或 "Bike Rack Pannier Bag"）
        sku: 产品/配件 SKU（如 "M25-145H-US" 或 "A5901"）
        base_url: 素材基础 URL
        use_thumb: 是否使用缩略图（仅产品支持）

    Returns:
        匹配结果，包含 title, image_url, product_url 等
    """
    mapping = load_mapping()
    products = mapping.get("products", {})
    accessories = mapping.get("accessories", {})

    if not products and not accessories:
        return None

    best_match = None
    best_score = 0.0
    is_accessory = False

    # 先搜索配件（SKU匹配通常更准确）
    for key, acc_info in accessories.items():
        score = 0.0

        # SKU 匹配（最高优先级）
        if sku:
            acc_skus = acc_info.get("skus", [])
            for acc_sku in acc_skus:
                if sku.upper() == acc_sku.upper():
                    score = 1.0  # 精确匹配
                    break
                elif sku.upper() in acc_sku.upper() or acc_sku.upper() in sku.upper():
                    score = 0.95  # 部分匹配
                    break

        # 配件名称匹配
        if score < 1.0 and product_name:
            title = acc_info.get("title", "")

            # 精确匹配
            if product_name.lower() == title.lower():
                score = 0.95
            else:
                # 模糊匹配
                name_score = SequenceMatcher(
                    None,
                    product_name.lower(),
                    title.lower()
                ).ratio()
                score = max(score, min(name_score, 0.9))

        if score > best_score:
            best_score = score
            best_match = (key, acc_info)
            is_accessory = True

    # 再搜索产品
    for key, product_info in products.items():
        score = 0.0

        # SKU 匹配（最高优先级）
        if sku:
            product_skus = product_info.get("skus", [])
            for product_sku in product_skus:
                if sku.upper() in product_sku.upper() or product_sku.upper() in sku.upper():
                    score = 1.0
                    break

        # 产品名称匹配
        if score < 1.0 and product_name:
            title = product_info.get("title", "")

            # 精确匹配
            if product_name.lower() == title.lower():
                score = 0.95
            else:
                # 模糊匹配
                name_score = SequenceMatcher(
                    None,
                    product_name.lower(),
                    title.lower()
                ).ratio()

                # 关键词匹配加分
                keywords = _extract_keywords(product_name)
                for kw in keywords:
                    if kw.lower() in title.lower():
                        name_score += 0.1

                score = max(score, min(name_score, 0.9))

        if score > best_score:
            best_score = score
            best_match = (key, product_info)
            is_accessory = False

    # 只有匹配度大于 0.5 才返回
    if best_match and best_score > 0.5:
        key, item_info = best_match
        use_cdn = is_cdn_mode()

        if is_accessory:
            # 配件图片
            # 优先使用 CDN URL
            if use_cdn and item_info.get("cdn_url"):
                image_url = item_info["cdn_url"]
            else:
                image_file = item_info.get("image", "")
                image_url = get_asset_url(image_file, base_url)

            return {
                "title": item_info.get("title"),
                "image_url": image_url,
                "image_url_full": image_url,
                "product_url": f"https://www.fiido.com/products/{item_info.get('handle', '')}",
                "match_score": best_score,
                "type": "accessory",
                "cdn_mode": use_cdn,
            }
        else:
            # 产品图片
            # 优先使用 CDN URL
            if use_cdn and item_info.get("cdn_url"):
                image_url = item_info["cdn_url"]
                image_url_full = item_info["cdn_url"]
            else:
                image_file = item_info.get("main_image", "")
                if use_thumb:
                    image_file = image_file.replace(".webp", "_thumb.webp")
                image_url = get_asset_url(image_file, base_url)
                image_url_full = get_asset_url(item_info.get("main_image", ""), base_url)

            return {
                "title": item_info.get("title"),
                "image_url": image_url,
                "image_url_full": image_url_full,
                "product_url": item_info.get("product_url"),
                "match_score": best_score,
                "type": "product",
                "cdn_mode": use_cdn,
            }

    return None


def match_order_items_images(
    line_items: List[Dict],
    base_url: str = ""
) -> List[Dict]:
    """
    为订单商品列表匹配图片

    Args:
        line_items: 订单商品列表，每项包含 title, sku 等
        base_url: 素材基础 URL

    Returns:
        带有图片 URL 的商品列表
    """
    result = []

    for item in line_items:
        item_copy = item.copy()

        # 匹配图片
        match = match_product_image(
            product_name=item.get("title", ""),
            sku=item.get("sku"),
            base_url=base_url,
            use_thumb=True
        )

        if match:
            item_copy["image_url"] = match["image_url"]
            item_copy["product_url"] = match["product_url"]

        result.append(item_copy)

    return result


def get_scene_assets(
    scene: str,
    base_url: str = ""
) -> Dict:
    """
    获取场景对应的素材

    Args:
        scene: 场景名称（welcome, order_query, product_consult, after_sales, goodbye）
        base_url: 素材基础 URL

    Returns:
        场景素材信息
    """
    mapping = load_mapping()
    scenes = mapping.get("scenes", {})

    scene_info = scenes.get(scene, {})
    if not scene_info:
        return {}

    result = {
        "description": scene_info.get("description"),
        "assets": [],
    }

    # 获取素材
    for asset_ref in scene_info.get("assets", []):
        if asset_ref == "brand/logo":
            brand = mapping.get("brand", {}).get("logo", {})
            if brand:
                result["assets"].append({
                    "type": "logo",
                    "url": get_asset_url(brand.get("image", ""), base_url),
                    "description": brand.get("description"),
                })

    return result


def get_brand_logo(base_url: str = "", white: bool = False) -> Optional[str]:
    """
    获取品牌 Logo URL

    Args:
        base_url: 素材基础 URL
        white: 是否使用白色版 Logo

    Returns:
        Logo URL
    """
    mapping = load_mapping()
    brand = mapping.get("brand", {})

    logo_key = "logo_white" if white else "logo"
    logo_info = brand.get(logo_key, {})

    if logo_info:
        return get_asset_url(logo_info.get("image", ""), base_url)

    return None


def get_all_products(base_url: str = "") -> List[Dict]:
    """
    获取所有产品信息（用于产品咨询场景）

    Returns:
        产品列表
    """
    mapping = load_mapping()
    products = mapping.get("products", {})
    use_cdn = is_cdn_mode()

    result = []
    for key, info in products.items():
        # 优先使用 CDN URL
        if use_cdn and info.get("cdn_url"):
            image_url = info["cdn_url"]
            thumb_url = info["cdn_url"]  # CDN 无缩略图
        else:
            image_url = get_asset_url(info.get("main_image", ""), base_url)
            thumb_url = get_asset_url(
                info.get("main_image", "").replace(".webp", "_thumb.webp"),
                base_url
            )

        result.append({
            "key": key,
            "title": info.get("title"),
            "image_url": image_url,
            "thumb_url": thumb_url,
            "product_url": info.get("product_url"),
            "skus": info.get("skus", []),
            "cdn_mode": use_cdn,
        })

    return result


def _extract_keywords(text: str) -> List[str]:
    """提取关键词"""
    # 常见产品关键词
    keywords = []

    patterns = [
        r'(C\d+)',  # C11, C21
        r'(D\d+)',  # D3
        r'(L\d+)',  # L3
        r'(M\d+)',  # M1
        r'(T\d+)',  # T1, T2
        r'(Titan)',
        r'(Air)',
        r'(Nomads?)',
        r'(Pro)',
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        keywords.extend(matches)

    return keywords


def generate_product_image_markdown(
    product_name: str,
    sku: Optional[str] = None,
    base_url: str = "",
    alt_text: Optional[str] = None
) -> str:
    """
    生成产品图片的 Markdown 格式

    Args:
        product_name: 产品名称
        sku: 产品 SKU
        base_url: 素材基础 URL
        alt_text: 图片替代文本

    Returns:
        Markdown 格式的图片标签，如 ![Fiido C11 Pro](https://...)
    """
    match = match_product_image(product_name, sku, base_url, use_thumb=True)

    if match:
        alt = alt_text or match.get("title", product_name)
        url = match.get("image_url", "")
        return f"![{alt}]({url})"

    return ""


# 测试
if __name__ == "__main__":
    print("=== 素材服务测试 ===\n")
    print(f"CDN 模式: {'启用' if is_cdn_mode() else '禁用'}\n")

    # 测试产品匹配
    test_cases = [
        ("Titan Fat Tire Touring Ebike", None),
        ("Fiido C11 Pro", None),
        ("Unknown Product", "C11PRO-104B-US"),
        # 配件测试
        ("Bike Rack Pannier Bag", None),
        ("Bike Rack Pannier Bag", "A5901"),  # 精确 SKU
        ("Fiido Electric Bike Display for D4S", None),
        ("Unknown", "3.005.000068"),  # D4S Display SKU
        ("Fiido Electric Bike Brake Pads", None),
    ]

    base_url = "https://ai.fiido.com/assets"

    for name, sku in test_cases:
        result = match_product_image(name, sku, base_url)
        if result:
            item_type = result.get('type', 'unknown')
            cdn_mode = result.get('cdn_mode', False)
            print(f"{'[CDN]' if cdn_mode else '[本地]'} {name} (SKU: {sku})")
            print(f"   类型: {item_type}")
            print(f"   匹配: {result['title']}")
            print(f"   图片: {result['image_url'][:80]}...")
            print(f"   分数: {result['match_score']:.2f}")
        else:
            print(f"❌ {name} (SKU: {sku}) - 未匹配")
        print()

    # 测试 Markdown 生成
    print("=== Markdown 生成测试 ===")
    md = generate_product_image_markdown("Fiido C11 Pro", base_url=base_url)
    print(md)
