#!/usr/bin/env python3
"""
Fiido 官网素材爬虫

爬取 www.fiido.com 的产品图片、配件图片、Logo、Banner 等素材
保存到本地素材库，并生成映射表
"""

import os
import json
import requests
import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urlparse

# 配置
BASE_URL = "https://www.fiido.com"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
ASSETS_DIR = Path("/home/yzh/AI客服/鉴权/assets")
MAPPING_FILE = ASSETS_DIR / "assets_mapping.json"

# 素材目录结构
ASSET_DIRS = {
    "products": "电动自行车产品主图",
    "accessories": "配件图片",
    "brand": "品牌素材（Logo、Banner）",
    "lifestyle": "生活场景图",
    "icons": "图标素材",
}

# 电动自行车产品列表（排除滑板车、配件）
EBIKE_PRODUCTS = [
    "fiido-air-carbon-fiber-electric-bike",
    "fiido-c11-electric-commuter-bike",
    "fiido-c11-pro-city-e-bike",
    "fiido-c21-lightweight-step-over-urban-gravel-ebikes",
    "fiido-d3-pro-mini-electric-bike",
    "fiido-l3-long-range-electric-bike",
    "fiido-m1-pro-fat-tire-electric-bike",
    "fiido-nomads-trekking-e-bike",
    "fiido-t1-utility-electric-bike",
    "fiido-t2-longtail-cargo-ebike-for-versatile-all-terrain",
    "fiido-titan-robust-cargo-electric-bike-with-ul-certified",
]

# 配件产品列表
ACCESSORY_PRODUCTS = [
    "fiido-smart-helmet",
    "fiido-bike-phone-mount",
    "fiido-bike-rack-pannier-bag",
    "fiido-front-basket",
    "fiido-rear-rack",
    "fiido-extra-battery",
    "fiido-charger",
    "fiido-seat-cover",
    "fiido-fenders",
    "fiido-lights",
]


class FiidoAssetCrawler:
    """Fiido 素材爬虫"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self.assets_mapping = {
            "version": "1.0.0",
            "updated_at": datetime.now().isoformat(),
            "base_url": "",  # 将在部署时设置
            "products": {},
            "accessories": {},
            "brand": {},
            "scenes": {},
        }

    def setup_dirs(self):
        """创建素材目录结构"""
        for dir_name, description in ASSET_DIRS.items():
            dir_path = ASSETS_DIR / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 创建目录: {dir_path} ({description})")

    def download_image(self, url: str, save_path: Path, max_width: int = 800) -> bool:
        """
        下载图片

        Args:
            url: 图片URL
            save_path: 保存路径
            max_width: 最大宽度（Shopify CDN 支持 URL 参数调整尺寸）
        """
        try:
            # Shopify CDN 支持通过 URL 参数调整图片尺寸
            if "cdn.shopify.com" in url and max_width:
                # 移除现有的尺寸参数，添加新的
                url = re.sub(r'\?.*$', '', url)
                url = f"{url}?width={max_width}&quality=80"

            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # 确保目录存在
            save_path.parent.mkdir(parents=True, exist_ok=True)

            with open(save_path, 'wb') as f:
                f.write(response.content)

            size_kb = len(response.content) / 1024
            print(f"  ✅ 下载: {save_path.name} ({size_kb:.1f} KB)")
            return True

        except Exception as e:
            print(f"  ❌ 下载失败 {url}: {e}")
            return False

    def get_product_data(self, product_handle: str) -> Optional[Dict]:
        """获取产品 JSON 数据"""
        try:
            url = f"{BASE_URL}/products/{product_handle}.json"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return response.json().get("product", {})
        except Exception as e:
            print(f"  ❌ 获取产品数据失败 {product_handle}: {e}")
            return None

    def crawl_ebike_products(self):
        """爬取电动自行车产品图片"""
        print("\n" + "="*50)
        print("📦 爬取电动自行车产品图片")
        print("="*50)

        products_dir = ASSETS_DIR / "products"

        for handle in EBIKE_PRODUCTS:
            print(f"\n🚲 处理: {handle}")

            product_data = self.get_product_data(handle)
            if not product_data:
                continue

            title = product_data.get("title", handle)
            images = product_data.get("images", [])
            variants = product_data.get("variants", [])

            # 提取 SKU 列表
            skus = list(set([v.get("sku", "") for v in variants if v.get("sku")]))

            # 生成简短的文件名
            short_name = self._generate_short_name(handle)

            # 下载主图（第一张）
            if images:
                main_image_url = images[0].get("src", "")
                main_image_path = products_dir / f"{short_name}.webp"

                if self.download_image(main_image_url, main_image_path):
                    self.assets_mapping["products"][short_name] = {
                        "title": title,
                        "handle": handle,
                        "skus": skus,
                        "main_image": f"products/{short_name}.webp",
                        "image_count": len(images),
                        "product_url": f"{BASE_URL}/products/{handle}",
                    }

            # 下载缩略图（用于聊天嵌入，尺寸更小）
            if images:
                thumb_path = products_dir / f"{short_name}_thumb.webp"
                self.download_image(images[0].get("src", ""), thumb_path, max_width=200)

    def crawl_accessories(self):
        """爬取配件图片"""
        print("\n" + "="*50)
        print("🔧 爬取配件图片")
        print("="*50)

        accessories_dir = ASSETS_DIR / "accessories"

        # 从官网配件集合获取
        try:
            # 尝试获取配件集合
            response = self.session.get(
                f"{BASE_URL}/collections/accessories.json",
                timeout=10
            )
            if response.status_code == 200:
                products = response.json().get("products", [])
                for product in products[:10]:  # 限制数量
                    handle = product.get("handle", "")
                    title = product.get("title", "")
                    images = product.get("images", [])

                    if images:
                        short_name = self._generate_short_name(handle)
                        image_path = accessories_dir / f"{short_name}.webp"

                        print(f"\n🔧 处理: {title}")
                        if self.download_image(images[0].get("src", ""), image_path):
                            self.assets_mapping["accessories"][short_name] = {
                                "title": title,
                                "handle": handle,
                                "image": f"accessories/{short_name}.webp",
                            }
        except Exception as e:
            print(f"  ⚠️ 获取配件列表失败: {e}")

    def crawl_brand_assets(self):
        """爬取品牌素材（Logo、Banner）"""
        print("\n" + "="*50)
        print("🎨 创建品牌素材")
        print("="*50)

        brand_dir = ASSETS_DIR / "brand"

        # Fiido Logo（从官网获取或使用已知URL）
        brand_assets = {
            "logo": {
                "url": "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/fiido-logo.png",
                "fallback": "https://www.fiido.com/cdn/shop/files/logo.png",
                "description": "Fiido Logo",
            },
            "logo_white": {
                "url": "https://cdn.shopify.com/s/files/1/0511/3308/7940/files/fiido-logo-white.png",
                "description": "Fiido Logo (白色版)",
            },
        }

        for name, info in brand_assets.items():
            print(f"\n🎨 处理: {name}")
            image_path = brand_dir / f"{name}.png"

            # 尝试主URL
            success = self.download_image(info["url"], image_path, max_width=None)

            # 尝试备用URL
            if not success and info.get("fallback"):
                success = self.download_image(info["fallback"], image_path, max_width=None)

            if success:
                self.assets_mapping["brand"][name] = {
                    "description": info["description"],
                    "image": f"brand/{name}.png",
                }

        # 创建占位符说明
        readme_path = brand_dir / "README.md"
        readme_path.write_text("""# Fiido 品牌素材

## 素材列表
- logo.png - Fiido Logo
- logo_white.png - Fiido Logo (白色版)

## 使用场景
- 欢迎消息
- 品牌介绍
- 邮件签名

## 更新说明
如需更新 Logo，请从 Fiido 官网下载最新版本替换。
""")

    def create_scene_mappings(self):
        """创建场景素材映射"""
        print("\n" + "="*50)
        print("🎬 创建场景映射")
        print("="*50)

        self.assets_mapping["scenes"] = {
            "welcome": {
                "description": "欢迎/问候场景",
                "assets": ["brand/logo"],
                "trigger_keywords": ["hello", "hi", "你好", "嗨"],
            },
            "order_query": {
                "description": "订单查询场景",
                "assets": ["products/*"],  # 根据商品匹配
                "trigger_intents": ["order_query", "order_list"],
            },
            "product_consult": {
                "description": "产品咨询场景",
                "assets": ["products/*"],
                "trigger_intents": ["product_consult"],
            },
            "after_sales": {
                "description": "售后服务场景",
                "assets": ["accessories/*", "products/*"],
                "trigger_keywords": ["repair", "维修", "warranty", "质保", "broken", "坏了"],
            },
            "goodbye": {
                "description": "告别场景",
                "assets": ["brand/logo"],
                "trigger_keywords": ["bye", "goodbye", "再见", "谢谢"],
            },
        }

        print("✅ 场景映射已创建")

    def _generate_short_name(self, handle: str) -> str:
        """生成简短的文件名"""
        # fiido-c11-pro-city-e-bike -> c11-pro
        name = handle.replace("fiido-", "").replace("-electric-bike", "").replace("-e-bike", "")
        name = name.replace("-ebike", "").replace("-city", "").replace("-utility", "")
        # 截取前15个字符
        return name[:20]

    def save_mapping(self):
        """保存映射表"""
        print("\n" + "="*50)
        print("💾 保存映射表")
        print("="*50)

        self.assets_mapping["updated_at"] = datetime.now().isoformat()

        with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.assets_mapping, f, ensure_ascii=False, indent=2)

        print(f"✅ 映射表已保存: {MAPPING_FILE}")

        # 统计
        print(f"\n📊 素材统计:")
        print(f"  - 电动自行车: {len(self.assets_mapping['products'])} 款")
        print(f"  - 配件: {len(self.assets_mapping['accessories'])} 款")
        print(f"  - 品牌素材: {len(self.assets_mapping['brand'])} 个")
        print(f"  - 场景映射: {len(self.assets_mapping['scenes'])} 个")

    def run(self):
        """运行爬虫"""
        print("="*50)
        print("🚀 Fiido 素材爬虫启动")
        print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*50)

        # 1. 创建目录
        self.setup_dirs()

        # 2. 爬取电动自行车
        self.crawl_ebike_products()

        # 3. 爬取配件
        self.crawl_accessories()

        # 4. 品牌素材
        self.crawl_brand_assets()

        # 5. 场景映射
        self.create_scene_mappings()

        # 6. 保存映射
        self.save_mapping()

        print("\n" + "="*50)
        print("✅ 爬取完成!")
        print("="*50)


if __name__ == "__main__":
    crawler = FiidoAssetCrawler()
    crawler.run()
