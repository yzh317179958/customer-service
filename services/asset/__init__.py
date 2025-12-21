"""素材服务模块"""
from services.asset.service import (
    load_mapping,
    find_best_product_image,
    get_scene_assets,
    clear_mapping_cache,
)

__all__ = [
    "load_mapping",
    "find_best_product_image",
    "get_scene_assets",
    "clear_mapping_cache",
]
