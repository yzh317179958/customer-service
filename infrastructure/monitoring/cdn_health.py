"""
CDN URL 健康检查服务

定期检查 assets_mapping.json 中的 CDN URL 是否有效
自动更新失效的 URL
"""

import json
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import httpx

# 配置
REPO_ROOT = Path(__file__).resolve().parents[2]
PRIMARY_ASSETS_DIR = REPO_ROOT / "assets"
SERVICE_ASSETS_DIR = REPO_ROOT / "services" / "asset" / "data"

PRIMARY_MAPPING_FILE = PRIMARY_ASSETS_DIR / "assets_mapping.json"
SERVICE_MAPPING_FILE = SERVICE_ASSETS_DIR / "assets_mapping.json"
PRIMARY_LOG_FILE = PRIMARY_ASSETS_DIR / "cdn_health_log.json"
SERVICE_LOG_FILE = SERVICE_ASSETS_DIR / "cdn_health_log.json"

# 优先使用 services/asset/data/（服务层依赖的数据源），并兼容项目根目录 assets/
MAPPING_FILE = SERVICE_MAPPING_FILE if SERVICE_MAPPING_FILE.exists() else PRIMARY_MAPPING_FILE
LOG_FILE = PRIMARY_LOG_FILE if PRIMARY_ASSETS_DIR.exists() else SERVICE_LOG_FILE

# 日志
logger = logging.getLogger(__name__)


async def check_url_validity(url: str, timeout: float = 10.0) -> Tuple[bool, int, str]:
    """
    检查单个 URL 是否有效

    Args:
        url: 要检查的 URL
        timeout: 超时时间（秒）

    Returns:
        (is_valid, status_code, error_message)
    """
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.head(url)
            is_valid = response.status_code in [200, 301, 302]
            return is_valid, response.status_code, ""
    except httpx.TimeoutException:
        return False, 0, "请求超时"
    except httpx.RequestError as e:
        return False, 0, str(e)
    except Exception as e:
        return False, 0, f"未知错误: {e}"


async def fetch_new_cdn_url(handle: str) -> Optional[str]:
    """
    从官网获取新的 CDN URL

    Args:
        handle: 产品/配件的 handle

    Returns:
        新的 CDN URL，获取失败返回 None
    """
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
        logger.warning(f"获取 {handle} 的 CDN URL 失败: {e}")
    return None


async def check_all_urls(auto_fix: bool = False) -> Dict:
    """
    检查所有 CDN URL 的有效性

    Args:
        auto_fix: 是否自动修复失效的 URL

    Returns:
        检查结果报告
    """
    # 读取映射表
    if not MAPPING_FILE.exists():
        raise FileNotFoundError(
            f"assets_mapping.json 未找到，已检查: {PRIMARY_MAPPING_FILE} / {SERVICE_MAPPING_FILE}"
        )

    with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    results = {
        "check_time": datetime.now().isoformat(),
        "total": 0,
        "valid": 0,
        "invalid": 0,
        "fixed": 0,
        "details": {
            "products": [],
            "accessories": []
        }
    }

    # 收集所有要检查的 URL
    check_items = []

    # 产品
    for key, info in mapping.get("products", {}).items():
        cdn_url = info.get("cdn_url")
        if cdn_url:
            check_items.append({
                "type": "products",
                "key": key,
                "title": info.get("title", key),
                "handle": info.get("handle"),
                "cdn_url": cdn_url
            })

    # 配件
    for key, info in mapping.get("accessories", {}).items():
        cdn_url = info.get("cdn_url")
        if cdn_url:
            check_items.append({
                "type": "accessories",
                "key": key,
                "title": info.get("title", key),
                "handle": info.get("handle"),
                "cdn_url": cdn_url
            })

    results["total"] = len(check_items)

    # 并发检查所有 URL
    print(f"开始检查 {len(check_items)} 个 CDN URL...")

    # 分批检查，每批 20 个
    batch_size = 20
    need_update = False

    for i in range(0, len(check_items), batch_size):
        batch = check_items[i:i+batch_size]
        tasks = [check_url_validity(item["cdn_url"]) for item in batch]
        batch_results = await asyncio.gather(*tasks)

        for item, (is_valid, status_code, error) in zip(batch, batch_results):
            detail = {
                "key": item["key"],
                "title": item["title"][:40],
                "valid": is_valid,
                "status_code": status_code,
                "error": error
            }

            if is_valid:
                results["valid"] += 1
                detail["status"] = "OK"
            else:
                results["invalid"] += 1
                detail["status"] = f"FAIL ({error or status_code})"
                detail["cdn_url"] = item["cdn_url"][:60] + "..."

                # 自动修复
                if auto_fix and item.get("handle"):
                    print(f"  尝试修复: {item['title'][:30]}...")
                    new_url = await fetch_new_cdn_url(item["handle"])
                    if new_url:
                        # 更新映射表
                        mapping[item["type"]][item["key"]]["cdn_url"] = new_url
                        detail["fixed"] = True
                        detail["new_url"] = new_url[:60] + "..."
                        results["fixed"] += 1
                        need_update = True
                        print(f"    ✅ 已修复")
                    else:
                        detail["fixed"] = False
                        print(f"    ❌ 修复失败")

            results["details"][item["type"]].append(detail)

        # 进度提示
        checked = min(i + batch_size, len(check_items))
        print(f"  已检查: {checked}/{len(check_items)}")

        # 避免请求过快
        await asyncio.sleep(0.5)

    # 保存更新后的映射表
    if need_update:
        mapping["updated_at"] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        mapping_files_to_write = [MAPPING_FILE]
        other_mapping_file = PRIMARY_MAPPING_FILE if MAPPING_FILE == SERVICE_MAPPING_FILE else SERVICE_MAPPING_FILE
        if other_mapping_file.exists() and other_mapping_file not in mapping_files_to_write:
            mapping_files_to_write.append(other_mapping_file)

        for path in mapping_files_to_write:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(mapping, f, ensure_ascii=False, indent=2)
        print(f"\n已更新映射表，修复 {results['fixed']} 个失效 URL")

    # 保存检查日志
    log_files_to_write = [LOG_FILE]
    # 同步写入另一份日志（如存在），避免双目录数据漂移
    other_log_file = SERVICE_LOG_FILE if LOG_FILE == PRIMARY_LOG_FILE else PRIMARY_LOG_FILE
    if other_log_file.parent.exists() and other_log_file not in log_files_to_write:
        log_files_to_write.append(other_log_file)

    for path in log_files_to_write:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    return results


async def check_all_cdn_urls(auto_fix: bool = False) -> Dict:
    """
    兼容别名：检查所有 CDN URL

    历史版本对外暴露过 `check_all_cdn_urls`，目前实现函数为 `check_all_urls`。
    为保持向后兼容，这里保留别名。
    """
    return await check_all_urls(auto_fix=auto_fix)


def print_report(results: Dict):
    """打印检查报告"""
    print("\n" + "=" * 50)
    print("CDN URL 健康检查报告")
    print("=" * 50)
    print(f"检查时间: {results['check_time']}")
    print(f"总计: {results['total']} 个 URL")
    print(f"有效: {results['valid']} ({results['valid']/max(results['total'],1)*100:.1f}%)")
    print(f"无效: {results['invalid']} ({results['invalid']/max(results['total'],1)*100:.1f}%)")
    if results.get('fixed'):
        print(f"已修复: {results['fixed']}")

    # 显示失效的 URL
    if results['invalid'] > 0:
        print("\n失效的 URL:")
        for item_type in ["products", "accessories"]:
            for item in results["details"].get(item_type, []):
                if not item.get("valid"):
                    status = "已修复" if item.get("fixed") else "未修复"
                    print(f"  [{status}] {item['title']}")
                    if item.get("error"):
                        print(f"         错误: {item['error']}")


async def run_health_check(auto_fix: bool = False):
    """运行健康检查的入口函数"""
    results = await check_all_urls(auto_fix=auto_fix)
    print_report(results)
    return results


# 命令行入口
if __name__ == "__main__":
    import sys

    auto_fix = "--fix" in sys.argv

    print("=" * 50)
    print("CDN URL 健康检查工具")
    print("=" * 50)
    if auto_fix:
        print("模式: 自动修复")
    else:
        print("模式: 仅检查 (使用 --fix 参数启用自动修复)")
    print()

    asyncio.run(run_health_check(auto_fix=auto_fix))
