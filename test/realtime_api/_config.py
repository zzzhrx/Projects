from __future__ import annotations

import os


def get_amap_api_key(required: bool = True) -> str | None:
    key = os.getenv("AMAP_API_KEY")
    if key:
        return key
    if required:
        raise RuntimeError("请设置环境变量 AMAP_API_KEY")
    return None


def has_amap_api_key() -> bool:
    return bool(os.getenv("AMAP_API_KEY"))
