"""
旅行API包 - 整合查车票、机票、酒店、餐厅、导航、地址查询等功能

配置方式：
    export AMAP_API_KEY=你的高德地图API密钥

Usage:
    from realtime_api import (
        get_hotel_info, get_restaurant_info,
        get_12306_table_json_cache, get_fliggy_flight_table_json_cache,
        get_routes, loc_info
    )
"""

import os

from ._config import get_amap_api_key, has_amap_api_key

API_KEY = os.getenv('AMAP_API_KEY')

__all__ = [
    'API_KEY',
    'get_amap_api_key',
    'has_amap_api_key',
    # 基础工具
    'loc_info',
    'parse_formatted_address',
    # 酒店与餐饮
    'get_hotel_info',
    'get_restaurant_info',
    'get_restaurants_by_keyword',
    # 交通
    'get_12306_table_json_cache',
    'get_fliggy_flight_table_json_cache',
    'filter_trains_by_start_time',
    'filter_and_sort_flight_list',
    # 导航
    'get_routes',
    'get_transit_route',
    'get_driving_route',
    'get_walking_route',
    'get_2p_nav_route',
    # 路径优化
    'generate_optimal_path',
    'haversine',
]

# 导入基础工具和导航
from .nav import (
    loc_info,
    parse_formatted_address,
    get_routes,
    get_transit_route,
    get_driving_route,
    get_walking_route,
    get_2p_nav_route,
    generate_optimal_path,
    haversine,
)

# 导入酒店和餐厅搜索
from .hotel import get_hotel_info
from .restaurant import get_restaurant_info, get_restaurants_by_keyword

# 导入交通查询
from .train_and_flight import (
    get_12306_table_json_cache,
    get_fliggy_flight_table_json_cache,
    filter_trains_by_start_time,
    filter_and_sort_flight_list,
)
