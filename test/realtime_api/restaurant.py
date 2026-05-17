"""
餐厅搜索API - 根据位置查询周边餐厅
"""

import requests

from ._config import get_amap_api_key
from .nav import loc_info


def get_restaurant_info(event, radius=3000, types=None, sortrule="weight"):
    """
    根据event中的城市和中心地址，查询周边餐厅信息

    :param event: {"city": "上海", "address": "上海交通大学闵行校区"}
    :param radius: 搜索半径（米），默认3000米
    :param types: 餐饮类型筛选，可选：
                  050000=中餐, 050100=火锅, 050200=烧烤, 050300=小吃
                  050400=快餐, 050500=茶饮, 050600=咖啡, 050700=蛋糕
                  050800=酒吧, 050900=清真, 051000=日本料理, 051100=韩国料理
                  051200=东南亚菜, 051300=西餐, 051400=面包甜点
                  默认None表示全部餐饮类型
    :param sortrule: 排序规则，默认"weight"权重排序，可选：
                    "weight"=权重排序, "distance"=距离排序, "price"=价格排序
    :return: {
        "count": poi_count,
        "restaurants": restaurants
    }
    where restaurants: [{
            "name": name,
            "address": cityname + adname + address,
            "distance": str(distance) + '米',
            "type": type,
            "tel": telephone,
            "rating": rating,
            "cost": cost  # 人均消费
        }, ...]
    """
    api_key = get_amap_api_key()
    loc = loc_info(event)
    base_url = "https://restapi.amap.com/v5/place/around"

    # 默认餐饮类型：全部餐饮
    if types is None:
        types = "050000"  # 中餐作为默认

    params = {
        "key": api_key,
        "location": loc['location'],
        "radius": radius,
        "types": types,
        "sortrule": sortrule,
        "show_fields": "business,contact"
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return parse_restaurant_response(data)
    else:
        print("HTTP request failed with status code:", response.status_code)
        return None


def parse_restaurant_response(response_json):
    """解析POI响应为餐厅信息列表"""
    poi_count = int(response_json.get('count', 0))
    if poi_count == 0:
        print("没有找到任何餐厅")
        return {
            "count": 0,
            "restaurants": None
        }

    pois = response_json.get('pois', [])
    restaurants = []
    for poi in pois:
        name = poi.get('name', 'N/A')
        address = poi.get('address', 'N/A')
        distance = poi.get('distance', 'N/A')
        cityname = poi.get('cityname', 'N/A')
        adname = poi.get('adname', 'N/A')
        type = poi.get('type', 'N/A')
        business = poi.get('business', {})

        # 获取评分和人均消费
        rating = business.get('rating', 'N/A')
        cost = business.get('cost', 'N/A')

        # 获取电话
        tel = poi.get('tel', 'N/A')

        restaurant = {
            "name": name,
            "address": cityname + adname + address,
            "distance": str(distance) + '米',
            "type": type,
            "tel": tel,
            "rating": rating,
            "cost": cost
        }
        restaurants.append(restaurant)

    return {
        "count": poi_count,
        "restaurants": restaurants
    }


def get_restaurants_by_keyword(event, keyword, radius=5000):
    """
    根据关键词搜索餐厅

    :param event: {"city": "上海", "address": "上海交通大学闵行校区"}
    :param keyword: 搜索关键词，如"火锅"、"川菜"、"日本料理"等
    :param radius: 搜索半径（米），默认5000米
    :return: {
        "count": poi_count,
        "restaurants": restaurants
    }
    """
    api_key = get_amap_api_key()
    loc = loc_info(event)
    base_url = "https://restapi.amap.com/v5/place/text"

    params = {
        "key": api_key,
        "keywords": keyword,
        "region": loc['citycode'],
        "citylimit": True,
        "show_fields": "business,contact"
    }

    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        return parse_restaurant_response(data)
    else:
        print("HTTP request failed with status code:", response.status_code)
        return None


if __name__ == '__main__':
    # 示例：查找南京大学附近的餐厅
    event = {
        "city": "南京",
        "address": "南京大学仙林校区"
    }

    print("=== 查找周边3000米内的餐厅 ===")
    restaurants = get_restaurant_info(event, radius=3000)
    if restaurants and restaurants['restaurants']:
        for r in restaurants['restaurants']:
            print(f"名称: {r['name']}")
            print(f"  地址: {r['address']}")
            print(f"  距离: {r['distance']}")
            print(f"  类型: {r['type']}")
            print(f"  评分: {r['rating']}")
            print(f"  人均: {r['cost']}")
            print("-" * 40)

    print("\n=== 搜索关键词'川菜'的餐厅 ===")
    results = get_restaurants_by_keyword(event, "川菜")
    if results and results['restaurants']:
        for r in results['restaurants'][:5]:
            print(f"{r['name']} - {r['address']}")
