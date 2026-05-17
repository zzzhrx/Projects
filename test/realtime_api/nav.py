"""
地图与导航API - 地址解析、路线规划、路径优化

整合了以下功能：
- loc_info: 地址位置查询
- parse_formatted_address: 经纬度转地址
- get_routes: 公交/驾车/步行路线查询
- generate_optimal_path: 多点路径优化
- haversine: 两点间距离计算
"""

import math
import time
import concurrent.futures
import requests

from ._config import get_amap_api_key


# ============ 地址解析 ============

def loc_info(event):
    """
    根据结构化地址和城市得到具体位置信息
    样例input: {'city':'南京', 'address':'南京大学仙林校区'}
    样例output: {"location": "118.068351,24.444549", "citycode": "0592", "adcode": "350203", "city": "厦门", "address": "厦门市思明区鼓浪屿", "poi_id": "..."}
    """
    api_key = get_amap_api_key()
    poi_url = "https://restapi.amap.com/v5/place/text"
    poi_params = {
        "key": api_key,
        "keywords": event["address"],
        "region": event["city"]
    }
    response = requests.get(poi_url, params=poi_params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1' and data['count'] != '0':
            poi_info = data['pois'][0]
            return {
                'location': poi_info['location'],
                'citycode': poi_info['citycode'],
                'adcode': poi_info['adcode'],
                'city': poi_info['cityname'],
                'address': poi_info['address'],
                'poi_id': poi_info['id']
            }
        else:
            pass  # no matching poi, try geocode directly
    else:
        print("HTTP request failed with status code:", response.status_code)
        return None

    # 降级：使用地理编码
    base_url = "https://restapi.amap.com/v3/geocode/geo"
    params = {
        "key": api_key,
        "address": event["address"],
        "city": event["city"]
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['status'] == '1' and data['count'] != '0':
            geocode_info = data['geocodes'][0]
            return {
                'location': geocode_info['location'],
                'citycode': geocode_info['citycode'],
                'adcode': geocode_info['adcode'],
                'city': event["city"],
                'address': geocode_info['formatted_address'],
            }
        else:
            print("No results found or request failed:", data['info'])
            return None
    else:
        print("HTTP request failed with status code:", response.status_code)
        return None


def parse_formatted_address(location):
    """
    根据经纬度坐标获取格式化地址
    :param location: "经度,纬度"格式，如 "118.068351,24.444549"
    :return: 格式化地址字符串
    """
    start_time = time.time()
    api_key = get_amap_api_key()
    url = f"https://restapi.amap.com/v3/geocode/regeo?location={location}&key={api_key}"

    try:
        response = requests.get(url)
        data = response.json()

        if 'regeocode' in data and 'formatted_address' in data['regeocode']:
            formatted_address = data['regeocode']['formatted_address']
            end_time = time.time()
            execution_time_ms = (end_time - start_time) * 1000
            print(f"parse_formatted_address: {execution_time_ms} ms")
            return formatted_address
        else:
            return "未能找到formatted_address字段"

    except requests.exceptions.RequestException as e:
        return f"请求发生错误: {e}"


# ============ 路径优化 ============

def haversine(lat1, lon1, lat2, lon2):
    """
    计算两点间的距离（使用 Haversine 公式）
    :return: 距离（公里）
    """
    R = 6371.0
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def generate_optimal_path(events):
    """
    最近邻算法生成最优路径
    :param events: [{'location': '经度,纬度', ...}, ...]
    :return: 重新排序后的事件列表
    """
    points = [(float(event['location'].split(',')[1]), float(event['location'].split(',')[0])) for event in events]
    start_index = 0
    unvisited = set(points)
    current_point = points[start_index]
    path = [events[start_index]]
    unvisited.remove(current_point)

    while unvisited:
        nearest_point = min(unvisited, key=lambda x: haversine(current_point[0], current_point[1], x[0], x[1]))
        path.append(events[points.index(nearest_point)])
        current_point = nearest_point
        unvisited.remove(nearest_point)

    return path


# ============ 路线规划 ============

def get_nav_route(events_loc):
    """批量获取多点之间的导航路线"""
    nav_route = []
    for i in range(len(events_loc) - 1):
        res = get_transit_route(events_loc[i], events_loc[i + 1])
        if res is not None:
            nav_route.append(res)
    return {"route": nav_route}


def get_2p_nav_route(from_place, to_place):
    """获取两点之间的导航路线"""
    from_loc = loc_info(from_place)
    to_loc = loc_info(to_place)
    return get_transit_route(from_loc, to_loc)


def get_events_loc(events):
    """并发获取多个地址的位置信息"""
    start_time = time.time()
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(loc_info, event) for event in events]
        results = [future.result() for future in concurrent.futures.as_completed(futures)]
    print(f"get_events_loc time: {(time.time() - start_time) * 1000} ms")
    return results


def get_transit_route(event_loc1, event_loc2):
    """获取公交/地铁路线"""
    api_key = get_amap_api_key()
    url = "https://restapi.amap.com/v5/direction/transit/integrated"
    params = {
        "key": api_key,
        "origin": event_loc1["location"],
        "destination": event_loc2["location"],
        "city1": event_loc1["citycode"],
        "city2": event_loc2["citycode"],
        "strategy": "7",
        "alternativeRoute": "3",
        "show_fields": "cost"
    }
    if event_loc1.get('poi_id'):
        params["originpoi"] = event_loc1.get('poi_id')
    if event_loc2.get('poi_id'):
        params["destinationpoi"] = event_loc2.get('poi_id')

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] == "1" and data["info"] == "OK":
            return data["route"]
        else:
            print(f"Error: {data['info']}")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None


def get_driving_route(event_loc1, event_loc2):
    """获取驾车路线"""
    api_key = get_amap_api_key()
    url = "https://restapi.amap.com/v5/direction/driving"
    params = {
        "key": api_key,
        "origin": event_loc1["location"],
        "destination": event_loc2["location"],
        "show_fields": "cost",
        "strategy": "32",
    }
    if event_loc1.get('poi_id'):
        params["origin_id"] = event_loc1.get('poi_id')
    if event_loc2.get('poi_id'):
        params["destination_id"] = event_loc2.get('poi_id')

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] == "1" and data["info"] == "OK":
            return data["route"]
        else:
            print(f"Error: {data['info']}")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None


def get_walking_route(event_loc1, event_loc2):
    """获取步行路线"""
    api_key = get_amap_api_key()
    url = "https://restapi.amap.com/v5/direction/walking"
    params = {
        "key": api_key,
        "origin": event_loc1["location"],
        "destination": event_loc2["location"],
        "show_fields": "cost",
    }
    if event_loc1.get('poi_id'):
        params["origin_id"] = event_loc1.get('poi_id')
    if event_loc2.get('poi_id'):
        params["destination_id"] = event_loc2.get('poi_id')

    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data["status"] == "1" and data["info"] == "OK":
            return data["route"]
        else:
            print(f"Error: {data['info']}")
            return None
    except Exception as e:
        print(f"Exception occurred: {str(e)}")
        return None


def get_routes(event1, event2, totext=True, simple=False):
    """
    根据两处地点，返回公交、驾车、步行三类导航路线

    :param event1: {"city":"南京", "address":"出发地址"}
    :param event2: {"city":"南京", "address":"目标地址"}
    :param totext: 如果totext，查询结果会转化为易读的字符串，否则传回结构体
    :param simple: 如果simple，返回结果字符串中不会包含详细路段信息
    :return: 字符串或结构体
    """
    event_loc1 = loc_info(event1)
    event_loc2 = loc_info(event2)
    print(event_loc1, event_loc2)
    transit_route = get_transit_route(event_loc1, event_loc2)
    driving_route = get_driving_route(event_loc1, event_loc2)
    walking_route = {"content": "路程过长，不推荐"}
    try:
        if int(transit_route.get('distance', '2000')) <= 2000:
            walking_route = get_walking_route(event_loc1, event_loc2)
    except:
        pass
    if totext:
        return parse_navigation([transit_route, driving_route, walking_route], event_loc1, event_loc2, simple=simple)
    else:
        if simple:
            for trans in transit_route['transits']:
                trans['segments'] = []
            for drives in driving_route['paths']:
                drives['steps'] = []
            if walking_route.get('paths'):
                for walks in walking_route['paths']:
                    walks['steps'] = []
        return {'transit_route': transit_route, 'driving_route': driving_route, 'walking_route': walking_route}


def parse_navigation(routes, event_loc1, event_loc2, simple=False):
    """解析导航路线为易读文本"""
    parse_result = ""
    origin = event_loc1.get("address")
    destination = event_loc2.get("address")
    parse_result += f"起点: {origin}   终点: {destination}\n"

    # 公交地铁
    item = routes[0]
    parse_result += "【公交/地铁方案】\n"

    for idx, t in enumerate(item['transits']):
        parse_result += f"  路线{idx+1}：\n"
        cost = t.get('cost', {})
        total_time = int(cost.get('duration', 0)) // 60
        transit_fee = cost.get('transit_fee', '')
        dist = int(t.get('distance', 0))
        walking_dist = int(t.get('walking_distance', 0))
        parse_result += f"  总距离{dist}米，总用时约{total_time}分钟，步行{walking_dist}米，费用{transit_fee}元。\n"

        if not simple:
            for seg in t.get('segments', []):
                if 'walking' in seg and seg['walking']:
                    walk_obj = seg['walking']
                    walk_dist = int(walk_obj.get('distance', 0))
                    walk_time = int(walk_obj.get('cost', {}).get('duration', 0)) // 60
                    parse_result += f"    步行约{walk_dist}米，用时{walk_time}分钟。\n"
                if 'bus' in seg and seg['bus']:
                    for line in seg['bus'].get('buslines', []):
                        bus_name = line.get('name', '')
                        from_stop = line.get('departure_stop', {}).get('name', '')
                        to_stop = line.get('arrival_stop', {}).get('name', '')
                        bus_dist = int(line.get('distance', 0))
                        bus_time = int(line.get('cost', {}).get('duration', 0)) // 60
                        parse_result += f"    乘坐{bus_name}，从「{from_stop}」到「{to_stop}」，约{bus_dist}米/{bus_time}分钟\n"

    parse_result += "-" * 50 + "\n"

    # 驾车路线
    item = routes[1]
    parse_result += "【驾车方案】\n"
    taxi_fee = None
    if 'cost' in item and isinstance(item['cost'], dict):
        taxi_fee = item['cost'].get('taxi_fee') or item.get('taxi_cost')
    elif 'taxi_cost' in item:
        taxi_fee = item['taxi_cost']
    if taxi_fee:
        parse_result += f"打车预计费用: {taxi_fee}元\n"
    for pi, path in enumerate(item['paths']):
        dist = int(path.get('distance', 0))
        duration = int(path.get('cost', {}).get('duration', 0))
        duration_min = duration // 60
        if duration_min == 0 and duration > 0:
            duration_min = 1
        parse_result += f"  路线{pi + 1}: 距离{dist}米，预计用时约{duration_min}分钟。\n"
        if not simple:
            if 'steps' in path:
                parse_result += "    主要路段简要：\n"
                for step in path['steps']:
                    inst = step.get('instruction', '')
                    step_dist = int(step.get('step_distance', step.get('distance', 0)))
                    if '沿' in inst or '到达目的地' in inst or '步行' in inst:
                        parse_result += f"      {inst} 约{step_dist}米\n"
            else:
                parse_result += "    步行为主线路。\n"

    parse_result += "-" * 50 + "\n"

    # 步行线路
    item = routes[2]
    parse_result += "【步行方案】\n"
    if 'paths' not in item:
        parse_result += "路程过长，不推荐步行。\n"
    else:
        for pi, path in enumerate(item['paths']):
            dist = int(path.get('distance', 0))
            duration = int(path.get('cost', {}).get('duration', 0))
            duration_min = duration // 60
            if duration_min == 0 and duration > 0:
                duration_min = 1
            parse_result += f"  路线{pi + 1}: 距离{dist}米，预计用时约{duration_min}分钟。\n"
            if not simple:
                if 'steps' in path:
                    parse_result += "    主要路段简要：\n"
                    for step in path['steps']:
                        inst = step.get('instruction', '')
                        step_dist = int(step.get('step_distance', step.get('distance', 0)))
                        if '沿' in inst or '到达目的地' in inst or '步行' in inst:
                            parse_result += f"      {inst} 约{step_dist}米\n"
                else:
                    parse_result += "    步行为主线路。\n"

    return parse_result


if __name__ == '__main__':
    # 测试地址解析
    event = {"city": "南京", "address": "南京大学仙林校区"}
    print("loc_info:", loc_info(event))

    # 测试经纬度转地址
    address = parse_formatted_address("118.947786,32.116722")
    print("formatted_address:", address)

    # 测试导航
    events = [
        {"city": "南京", "address": "南京市玄武区进香河路33号"},
        {"city": "南京", "address": "南京大学仙林校区"}
    ]
    res = get_routes(events[0], events[1])
    print(res)
