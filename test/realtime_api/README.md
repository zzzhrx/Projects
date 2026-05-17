# Realtime API - 旅行API工具包

整合查车票、机票、酒店、餐厅、导航、地址查询等功能的Python包。

## 配置API密钥

本包使用高德地图API，需要设置环境变量 `AMAP_API_KEY`：

```bash
# Linux/macOS
export AMAP_API_KEY=你的高德地图API密钥

# Windows PowerShell
$env:AMAP_API_KEY=你的高德地图API密钥

# Windows CMD
set AMAP_API_KEY=你的高德地图API密钥
```

或者在Python中设置（临时）：
```python
import os
os.environ['AMAP_API_KEY'] = '你的高德地图API密钥'
```

---

## 安装依赖

```bash
pip install requests selenium beautifulsoup4
```

**注意**：
- 查机票需要 Chrome 浏览器 + chromedriver
- 查火车票需要 Edge 浏览器 + edgedriver

---

## 文件结构

```
realtime_api/
├── __init__.py          # 包入口，导出所有API
├── nav.py               # 导航（地址解析+路线规划+路径优化）
├── hotel.py             # 酒店查询
├── restaurant.py        # 餐厅查询
├── train_and_flight.py  # 火车票/机票查询
└── README.md
```

---

## API调用示例

### 1. 地址位置查询

`loc_info(event)` - 根据城市和地址获取经纬度坐标

```python
from realtime_api import loc_info

event = {"city": "南京", "address": "南京大学仙林校区"}
loc = loc_info(event)
print(loc)
# 输出: {'location': '118.947786,32.116722', 'citycode': '025', ...}
```

`parse_formatted_address(location)` - 根据经纬度获取格式化地址

```python
from realtime_api import parse_formatted_address

address = parse_formatted_address("118.947786,32.116722")
print(address)  # "江苏省南京市栖霞区仙林大道163号"
```

---

### 2. 酒店查询

`get_hotel_info(event, radius=5000, sortrule="weight")` - 查询周边酒店

```python
from realtime_api import get_hotel_info

event = {"city": "南京", "address": "南京大学仙林校区"}
result = get_hotel_info(event)

print(f"找到 {result['count']} 家酒店")
for h in result['hotels'][:3]:
    print(f"  {h['name']}")
    print(f"    地址: {h['address']}")
    print(f"    距离: {h['distance']}")
    print(f"    类型: {h['type']}")
    print(f"    评分: {h['rating']}")
```

**参数**：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| event | 必填 | `{"city": "城市", "address": "地址"}` |
| radius | 5000 | 搜索半径（米） |
| sortrule | "weight" | 排序方式：`"weight"`权重 / `"distance"`距离 |

---

### 3. 餐厅查询

`get_restaurant_info(event, radius=3000, types=None, sortrule="weight")` - 按位置查找餐厅

```python
from realtime_api import get_restaurant_info

event = {"city": "南京", "address": "南京大学仙林校区"}
result = get_restaurant_info(event, radius=3000)

print(f"找到 {result['count']} 家餐厅")
for r in result['restaurants'][:3]:
    print(f"  {r['name']} | {r['type']} | 距{r['distance']} | 人均{r['cost']}")
```

`get_restaurants_by_keyword(event, keyword, radius=5000)` - 按关键词搜索餐厅

```python
from realtime_api import get_restaurants_by_keyword

event = {"city": "南京", "address": "南京大学仙林校区"}
result = get_restaurants_by_keyword(event, "川菜")

for r in result['restaurants'][:5]:
    print(f"{r['name']} - {r['address']}")
```

**餐饮类型代码**：

| 代码 | 类型 | 代码 | 类型 |
|------|------|------|------|
| 050000 | 中餐 | 050700 | 蛋糕甜点 |
| 050100 | 火锅 | 050800 | 酒吧 |
| 050200 | 烧烤 | 051000 | 日本料理 |
| 050300 | 小吃 | 051100 | 韩国料理 |
| 050400 | 快餐 | 051200 | 东南亚菜 |
| 050500 | 茶饮 | 051300 | 西餐 |
| 050600 | 咖啡 | 051400 | 面包甜点 |

---

### 4. 火车票查询

`get_12306_table_json_cache(出发站, 到达站, 日期)` - 查询火车票（带7天缓存）

```python
from realtime_api import get_12306_table_json_cache, filter_trains_by_start_time

# 查询南京到上海的火车
trains = get_12306_table_json_cache("南京", "上海", "2025-07-30")

for train in trains[:5]:
    print(f"{train['number']} | {train['from_station']} → {train['to_station']}")
    print(f"  出发: {train['start_time']} 到达: {train['end_time']}")
    print(f"  用时: {train['duration']} | 最低价: {train['price']}")
```

`filter_trains_by_start_time(trains, time_range)` - 按出发时间筛选

```python
# 筛选8点到10点出发的车次
filtered = filter_trains_by_start_time(trains, "8~10")

# 单个小时：筛选9点左右（±2小时）的车次
filtered = filter_trains_by_start_time(trains, "9")
```

---

### 5. 机票查询

`get_fliggy_flight_table_json_cache(出发城市, 到达城市, 日期)` - 查询机票（带7天缓存）

```python
from realtime_api import get_fliggy_flight_table_json_cache, filter_and_sort_flight_list

# 查询南京到成都的航班
flights = get_fliggy_flight_table_json_cache("南京", "成都", "2025-07-30")

for f in flights[:5]:
    print(f"{f['航司航班号']}")
    print(f"  {f['出发时间']} → {f['到达时间']}")
    print(f"  {f['出发机场']} → {f['到达机场']} | 机型: {f['机型']}")
    print(f"  票价: {f['票价']} | 余票: {f['余票']}")
```

`filter_and_sort_flight_list(flights, strategy=None, company=None)` - 筛选排序

```python
# 按价格升序
sorted_price = filter_and_sort_flight_list(flights, strategy='price')

# 按出发时间排序
sorted_time = filter_and_sort_flight_list(flights, strategy='time')

# 按航司筛选（模糊匹配）
filtered = filter_and_sort_flight_list(flights, company='国航')

# 组合使用
filtered = filter_and_sort_flight_list(flights, strategy='price', company='东航')
```

---

### 6. 导航路线

`get_routes(event1, event2, totext=True, simple=False)` - 查询公交/驾车/步行路线

```python
from realtime_api import get_routes

event1 = {"city": "南京", "address": "南京大学仙林校区"}
event2 = {"city": "南京", "address": "中山陵"}

# 获取易读的路线文本
route_text = get_routes(event1, event2, totext=True)
print(route_text)

# 获取结构化数据
route_data = get_routes(event1, event2, totext=False, simple=True)
# route_data 包含: transit_route, driving_route, walking_route
```

**参数说明**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| totext | bool | True | True返回易读字符串，False返回结构体 |
| simple | bool | False | True简化输出，不含详细路段信息 |

---

### 7. 路径优化

`generate_optimal_path(events)` - 使用最近邻算法优化多地点访问顺序

```python
from realtime_api import generate_optimal_path

# 需要先获取各点的location（用loc_info）
events = [
    {"city": "深圳", "address": "华侨城", "location": "113.978615,22.537872"},
    {"city": "深圳", "address": "大梅沙", "location": "114.304642,22.594236"},
    {"city": "深圳", "address": "世界之窗", "location": "113.997275,22.531446"},
]

optimal = generate_optimal_path(events)
print("最优访问顺序:")
for i, e in enumerate(optimal, 1):
    print(f"  {i}. {e['address']}")
```

---

## 注意事项

1. **API配额**：高德地图API有每日配额限制，请勿频繁调用
2. **缓存**：火车票和机票查询结果会缓存在本地 `cache_12306/` 和 `cache_fliggy/` 目录
3. **浏览器驱动**：机票查询需要Chrome，火车票查询需要Edge
4. **查询时间限制**：火车票支持查询15天内，机票支持30天内