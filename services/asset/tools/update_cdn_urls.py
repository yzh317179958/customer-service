#!/usr/bin/env python3
"""
更新 assets_mapping.json 中的 CDN URL
从 Fiido 官网获取最新的图片 CDN 地址
"""

import httpx
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any

ASSETS_DIR = Path(__file__).parent.parent / "data"
MAPPING_FILE = ASSETS_DIR / "assets_mapping.json"


async def get_cdn_url(handle: str) -> Optional[str]:
    """从官网获取产品/配件的 CDN 图片 URL"""
    url = f"https://www.fiido.com/products/{handle}.json"
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                images = data.get('product', {}).get('images', [])
                if images:
                    return images[0].get('src')
    except Exception as e:
        print(f"  ⚠️ 请求失败: {e}")
    return None


async def update_mapping():
    """更新映射表中的所有 CDN URL"""
    # 读取现有映射
    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    updated_count = 0
    failed_count = 0

    # 更新配件
    print("\n=== 更新配件 CDN URL ===")
    accessories = mapping.get('accessories', {})
    for key, info in accessories.items():
        handle = info.get('handle')
        if handle:
            cdn_url = await get_cdn_url(handle)
            if cdn_url:
                info['cdn_url'] = cdn_url
                updated_count += 1
                print(f"✅ {info.get('title', key)[:40]}")
            else:
                failed_count += 1
                print(f"❌ {info.get('title', key)[:40]} - 获取失败")
        await asyncio.sleep(0.1)  # 避免请求过快

    # 更新产品
    print("\n=== 更新产品 CDN URL ===")
    products = mapping.get('products', {})
    for key, info in products.items():
        handle = info.get('handle')
        if handle:
            cdn_url = await get_cdn_url(handle)
            if cdn_url:
                info['cdn_url'] = cdn_url
                updated_count += 1
                print(f"✅ {info.get('title', key)[:40]}")
            else:
                failed_count += 1
                print(f"❌ {info.get('title', key)[:40]} - 获取失败")
        await asyncio.sleep(0.1)

    # 更新版本和时间
    from datetime import datetime
    mapping['updated_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
    mapping['cdn_mode'] = True  # 标记使用 CDN 模式

    # 保存
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"\n=== 完成 ===")
    print(f"成功: {updated_count}")
    print(f"失败: {failed_count}")
    print(f"已保存到: {MAPPING_FILE}")


if __name__ == "__main__":
    asyncio.run(update_mapping())
