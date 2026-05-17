import os

# === 缓存目录配置 ===
# 定位到 backend 目录
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# 缓存目录
CACHE_12306_DIR = os.path.join(PROJECT_ROOT, 'cache_12306')
CACHE_FLIGGY_DIR = os.path.join(PROJECT_ROOT, "cache_fliggy")

from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import os, json, re, time
from bs4 import BeautifulSoup

# from app.recommend_model import train_model


def calculate_end_time(start_time, duration):
    """
    计算结束时间的函数

    :param start_time: 开始时间，格式为 'HH:MM'
    :duration: 历时长度，格式为 'HH:MM'，可能为空字符串
    :return: 计算后的结束时间，格式为 'YYYY-MM-DD HH:MM'
    """

    # 解析 start_time
    start_datetime = datetime.strptime(start_time, '%Y-%m-%d %H:%M')

    # 如果 duration 为空字符串，则直接返回 start_datetime 的格式化字符串
    if not duration:
        end_time = start_datetime
    else:
        # 解析 duration
        hours, minutes = map(int,duration.split(':'))
        duration = timedelta(hours=hours, minutes=minutes)

        # 计算 end_time
        end_time = start_datetime + duration

    return end_time.strftime('%Y-%m-%d %H:%M')


def filter_trains_by_start_time(trains, time_range):
    """
    支持多种 time_range 格式，按小时筛选 start_time。
    :param trains: [{'start_time': '2024-07-23 08:15'}, ...]
    :param time_range: '8~10' 或 '7:00~18:20' 或 '12' 等
    :return: 筛选后的列表
    """

    # ----------- 解析 time_range -----------
    def parse_time_part(s):
        """返回整数小时，无法解析返回None"""
        m = re.match(r'(\d{1,2})', s.strip())
        if m:
            h = int(m.group(1))
            if 0 <= h <= 24:  # 0点~24点
                return h
        return None

    def get_range(range_str):
        # 空字符串或None，通配不过滤
        if not range_str or range_str.strip() == '':
            return 0, 24
        s = range_str.replace("—", "~").replace("-", "~").replace("：", ":")
        parts = [p.strip() for p in s.split("~") if p.strip()]
        # 单个数字，变成n-2~n+2，边界收缩到0~24
        if len(parts) == 1:
            h = parse_time_part(parts[0])
            if h is not None:
                return max(0, h-2), min(24, h+2)
            else:
                return 0, 24
        # 区间写法
        if len(parts) == 2:
            h1 = parse_time_part(parts[0])
            h2 = parse_time_part(parts[1])
            if h1 is not None and h2 is not None:
                a, b = min(h1, h2), max(h1, h2)
                # 不能写23~4/ 25~6 这类
                return max(0, a), min(24, b)
            else:
                return 0, 24
        # 其他异常
        return 0, 24

    range_start, range_end = get_range(time_range)

    # ------------ 过滤 ----------------
    filtered = []
    for t in trains:
        v = t.get("start_time")
        if not v or len(v) < 13:
            continue
        try:
            hour = int(v.split()[1].split(':')[0])
        except Exception:
            continue
        if range_start <= hour <= range_end:
            filtered.append(t)

    return filtered


def is_within_15_days(date_str, days = 15):
    """
    判断date_str是否在今天起的15天以内（含今天）
    :param date_str: 字符串，格式 'YYYY-MM-DD'
    :param days: 从当日起的时间限制，默认15天
    :return: bool
    """
    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        today = datetime.today().date()
        delta = target_date - today
        # 0 <= delta.days < 15 表示今天到第14天（含）。如果想包括第15天，用 <= 15。
        return 0 <= delta.days < days
    except Exception:
        return False


def parse_12306_train_info(driver, date_str):
    from selenium.webdriver.common.by import By
    import re

    # 第一次性获取所有结果块
    train_items = driver.find_elements(By.CSS_SELECTOR, ".ticket-result-item")
    results = []

    for item in train_items:
        try:
            html = item.get_attribute("outerHTML")
            soup = BeautifulSoup(html, "lxml")

            # 车次
            num = soup.select_one(".train-num-station span")
            number = num.text.strip() if num else ""

            # 出发-到达站、时间
            stations = soup.select(".ticket-station")
            start_time = from_station = to_station = end_time = ""
            if len(stations) >= 2:
                st1 = stations[0]
                st2 = stations[1]
                st1_time = st1.select_one(".ticket-station-num")
                st2_time = st2.select_one(".ticket-station-num")
                st1_city = st1.select_one(".ticket-station-info")
                st2_city = st2.select_one(".ticket-station-info")
                start_time = st1_time.text.strip() if st1_time else ""
                from_station = st1_city.find_all(string=True)[-1].strip() if st1_city else ""
                end_time = st2_time.text.strip() if st2_time else ""
                to_station = st2_city.find_all(string=True)[-1].strip() if st2_city else ""

            duration_soup = soup.select_one(".ticket-alltime-text")
            duration = duration_soup.text.strip() if duration_soup else ""

            # 票价信息（字符串提速）
            all_price = {}
            price_blocks = soup.select('.ticket-price-item-drop')
            for pb in price_blocks:
                # 主票种价
                seat_div = pb.select_one(".ticket-price-seat")
                price_div = pb.select_one(".ticket-price-num .txt-price")
                seat_type = seat_div.text.strip() if seat_div else ""
                price_val = price_div.text.strip().replace('\n','') if price_div else ""
                if seat_type and price_val:
                    all_price[seat_type] = price_val
                # 子铺
                for sub in pb.select('.ticket-price-item-group .ticket-price-item'):
                    gseat = sub.select_one(".ticket-price-seat")
                    gprice = sub.select_one(".ticket-price-num .txt-price")
                    gseat = gseat.text.strip() if gseat else ""
                    gprice = gprice.text.strip().replace('\n','') if gprice else ""
                    if gseat and gprice:
                        all_price[f"{seat_type}-{gseat}"] = gprice

            # 最低价
            min_price = ""
            price_numbers = []
            for p in all_price.values():
                m = re.search(r"¥([0-9.]+)", p)
                if m:
                    price_numbers.append(float(m.group(1)))
            if price_numbers:
                min_val = min(price_numbers)
                min_price = f"¥{min_val}起"

            # 备注略（有需要也一样提）

            results.append({
                'number': number,
                'from_station': from_station,
                'to_station': to_station,
                'start_time': f"{date_str} {start_time}",
                'end_time': calculate_end_time(f"{date_str} {start_time}", duration),
                'duration': duration,
                'price': min_price,
                'all_price': all_price,
                'remark': "",
            })
        except Exception as e:
            print("解析异常:", e)
            continue

    return results


def get_12306_table_json(depart_station, arrive_station, date_str):
    """
    depart_station/arrive_station: 出发/到达城市，如"南京"/"上海"
    date_str: "YYYY-MM-DD"
    ——
    新版12306：用selenium和js查DOM数据，不用OCR
    返回：所有车次结构化list[dict]
    """
    print("========================= Start Connecting To 12306 ===========================")
    if not is_within_15_days(date_str):
        return [{"ExceptionInfo":"查询时间超出限制"}]

    # 初始化Edge/Chrome，可选headless
    edge_options = Options()
    edge_options.add_argument('--disable-gpu')
    edge_options.add_argument('--force-device-scale-factor=2')
    edge_options.add_argument('--headless=new') # 本地开发可选注释
    # user agent
    user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 S```afari/537.36'
    edge_options.add_argument(f'user-agent={user_agent}')
    # 关闭浏览器上部提示语：Chrome正在受到自动软件的控制(改修js特征)
    edge_options.add_experimental_option('excludeSwitches', ['enable-automation'])
    edge_options.add_experimental_option('useAutomationExtension', False)

    service = EdgeService(executable_path=r"D:\softwares\edgedriver_win64\msedgedriver.exe")
    driver = webdriver.Edge(service=service, options=edge_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        　　 Object.defineProperty(navigator, 'webdriver', {
        　　 get: () => undefined
        　　 })
        　　 """
    })

    # 链接12306
    url = "https://kyfw.12306.cn/otn/view/queryPublicIndex.html"
    driver.get(url)
    time.sleep(1.5)  # 等待页面渲染加载

    # 录入出发地
    from_input = driver.find_element(By.ID, "fromStationText")
    from_input.click()
    from_input.clear()
    from_input.send_keys(depart_station)
    time.sleep(0.5)
    from_input.send_keys(Keys.ENTER)
    time.sleep(0.3)

    # 录入到达地
    to_input = driver.find_element(By.ID, "toStationText")
    to_input.click()
    to_input.clear()
    to_input.send_keys(arrive_station)
    time.sleep(0.5)
    to_input.send_keys(Keys.ENTER)
    time.sleep(0.3)

    # 录入日期
    date_input = driver.find_element(By.ID, "train_date")
    driver.execute_script("arguments[0].removeAttribute('readonly')", date_input)  # 解除readonly
    date_input.clear()
    date_input.send_keys(date_str)
    date_input.send_keys(Keys.ENTER)
    time.sleep(0.3)

    # 点击查询
    driver.find_element(By.ID, "query_ticket").click()
    time.sleep(2.0)  # 等待加载，如果网络慢可以延长到3秒

    data = parse_12306_train_info(driver, date_str)
    print(data)
    driver.quit()
    return data


def get_12306_table_json_cache(depart_station, arrive_station, date_str):
    """
    获取带缓存功能的12306列车信息（自动管理本地缓存，7天有效）

    :param depart_station: 出发站（字符串）
    :param arrive_station: 到达站（字符串）
    :param date_str: 查询日期（格式: YYYY-MM-DD）
    :return: 查询结果json对象
    """
    os.makedirs(CACHE_12306_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    cache_pattern = f"{date_str}_{depart_station}_{arrive_station}_"
    cache_file = None
    latest_time = None

    for fname in os.listdir(CACHE_12306_DIR):
        if fname.startswith(cache_pattern) and fname.endswith(".json"):
            updatetime_str = fname.replace(cache_pattern, "").replace(".json", "")
            try:
                updatetime = datetime.strptime(updatetime_str, "%Y-%m-%d")
                if (datetime.now() - updatetime).days <= 7:
                    if latest_time is None or updatetime > latest_time:
                        cache_file = os.path.join(CACHE_12306_DIR, fname)
                        latest_time = updatetime
            except Exception:
                continue

    if cache_file and os.path.isfile(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[WARN] 读取缓存异常({cache_file}): {e}")

    # 获取最新数据并缓存
    data = get_12306_table_json(depart_station, arrive_station, date_str)
    if data[0] == "查询时间超出范围":
        return data
    new_cache_file = os.path.join(
        CACHE_12306_DIR, f"{date_str}_{depart_station}_{arrive_station}_{today_str}.json"
    )
    try:
        with open(new_cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] 写缓存异常({new_cache_file}): {e}")
    return data


def get_full_arrival_time(dep_date: str, dep_time: str, arr_time: str):
    """
    dep_date: "2024-08-01"
    dep_time: "22:30"
    arr_time: "01:05"
    返回："2024-08-02 01:05"
    """
    dt_dep = datetime.strptime(f"{dep_date} {dep_time}", "%Y-%m-%d %H:%M")
    dt_arr = datetime.strptime(f"{dep_date} {arr_time}", "%Y-%m-%d %H:%M")
    if dt_arr < dt_dep:
        # 跨天
        dt_arr += timedelta(days=1)
    return dt_arr.strftime("%Y-%m-%d %H:%M")


def extract_hhmm(raw_time):
    """
    从字符串中提取出 hh:mm 格式的时间
    :param raw_time: 原始时间字符串，可能混有日期和时间
    :return: hh:mm 或原样字符串
    """
    # 查找 hh:mm
    m = re.search(r'(\d{1,2}):(\d{2})', raw_time)
    return f"{m.group(1).zfill(2)}:{m.group(2)}" if m else raw_time


def get_fliggy_flight_table_json(dep_city, arr_city, dep_date):
    """
    dep_city/arr_city: 出发/到达城市中文名, 例："南京"/"北京"
    dep_date: 出发日期，"YYYY-MM-DD" 格式
    pipeline: 已初始化的结构化 OCR（如paddleocr，与你12306相同）
    返回：航班表结构文本的识别结构（list of dict）
    """


    print("========================= Start Connecting To Fliggy ===========================")
    if not is_within_15_days(dep_date, days=30):
        return [{"ExceptionInfo":"查询时间超出限制"}]

    url = "https://sjipiao.fliggy.com/flight_search_result.htm"

    # ---- 1、打开WebDriver ----
    options = webdriver.ChromeOptions()
    options.add_argument('--disable-gpu')
    options.add_argument('--force-device-scale-factor=2')
    options.add_argument('--headless=new')  # 生产环境可开启无头
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36")
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    driver = webdriver.Chrome(options=options)
    driver.set_window_size(1600, 1200)

    driver.get(url)
    time.sleep(1.5)   # 页面较大

    # ---- 2、填写查询表单 ----
    dep_input = driver.find_element(By.CSS_SELECTOR, "input.pi-input.J_DepCity.ks-autocomplete-input[name='depCityName']")
    dep_input.clear()
    dep_input.send_keys(dep_city)
    time.sleep(0.5)

    arr_input = driver.find_element(By.CSS_SELECTOR, "input.pi-input.J_ArrCity.ks-autocomplete-input[name='arrCityName']")
    arr_input.clear()
    arr_input.send_keys(arr_city)
    time.sleep(0.5)

    date_input = driver.find_element(By.CSS_SELECTOR, "input.pi-input.J_DepDate.trigger-node-602[name='depDate']")
    date_input.clear()
    date_input.send_keys(dep_date)
    time.sleep(0.5)

    search_btn = driver.find_element(By.CSS_SELECTOR, "input.pi-btn.pi-btn-primary[type='submit']")
    search_btn.click()
    time.sleep(0.8)

    # ---- 3、如弹窗“我知道了”出现，自动点掉 ----
    try:
        popup_btn = WebDriverWait(driver, 4).until(
            EC.element_to_be_clickable((By.ID, "J_Flight_Notify_Close_Btn"))
        )
        popup_btn.click()
        print("弹窗『我知道了』已自动关闭.")
        time.sleep(1.5)
    except Exception:
        print("未检测到『我知道了』弹窗，无需关闭.")

    # 等航班表出现
    wait = WebDriverWait(driver, 12)
    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".flight-item-tr")))

    # 1. 获取所有航班行
    rows = driver.find_elements(By.CSS_SELECTOR, ".flight-item-tr")
    flight_list = []
    for row in rows:
        try:
            # 航班号、航空公司
            airline = row.find_element(By.CSS_SELECTOR, ".airline-name .J_line").text.strip()
            # 机型/飞机类型
            flight_type = row.find_element(By.CSS_SELECTOR, ".J_FlightType").text.strip()
            # 起飞/到达时间
            dep_time = row.find_element(By.CSS_SELECTOR, ".flight-time-deptime").text.strip()
            dep_time = extract_hhmm(dep_time)

            arr_time = row.find_element(By.CSS_SELECTOR, ".flight-time .s-time").text.strip()
            arr_time = extract_hhmm(arr_time)
            # 机场
            dep_port = row.find_element(By.CSS_SELECTOR, ".port-dep").text.strip()
            arr_port = row.find_element(By.CSS_SELECTOR, ".port-arr").text.strip()
            # 时长
            # total_time = row.find_element(By.CSS_SELECTOR, ".flight-total-time p").text.strip()
            # 票价
            price = row.find_element(By.CSS_SELECTOR, ".J_FlightListPrice").text.strip()
            # 是否有余票&购票
            stock_info = ""
            try:
                stock_info = row.find_element(By.CSS_SELECTOR, ".less-tag").text.strip()
            except:
                stock_info = "充足"
            # 订票按钮可点/不可点
            # btn = row.find_element(By.CSS_SELECTOR, ".J_SelectFlight")
            flight = {
                "航司航班号": airline,
                "机型": flight_type,
                "出发时间": dep_date + ' ' + dep_time,
                "到达时间": get_full_arrival_time(dep_date, dep_time, arr_time),
                "出发机场": dep_port,
                "到达机场": arr_port,
                # "用时": total_time,
                "票价": price,
                "余票": stock_info,
                # "按钮": btn.is_enabled()  # 可选
            }
            flight_list.append(flight)
        except Exception as e:
            print("某行提取有误:", e)

    print(flight_list)
    driver.quit()
    return flight_list


def get_fliggy_flight_table_json_cache(dep_city, arr_city, dep_date):
    """
    获取带缓存功能的Fliggy机票信息（本地缓存，7天内有效自动复用）

    :param dep_city: 出发城市（字符串）
    :param arr_city: 到达城市（字符串）
    :param dep_date: 出发日期 (YYYY-MM-DD)
    :return: 查询结果json对象
    """
    os.makedirs(CACHE_FLIGGY_DIR, exist_ok=True)
    today_str = datetime.now().strftime("%Y-%m-%d")
    cache_pattern = f"{dep_date}_{dep_city}_{arr_city}_"
    cache_file = None
    latest_time = None

    # 查找最匹配、在7天内的缓存文件
    for fname in os.listdir(CACHE_FLIGGY_DIR):
        if fname.startswith(cache_pattern) and fname.endswith(".json"):
            updatetime_str = fname.replace(cache_pattern, "").replace(".json", "")
            try:
                updatetime = datetime.strptime(updatetime_str, "%Y-%m-%d")
                if (datetime.now() - updatetime).days <= 7:
                    if latest_time is None or updatetime > latest_time:
                        cache_file = os.path.join(CACHE_FLIGGY_DIR, fname)
                        latest_time = updatetime
            except Exception:
                continue

    # 1. 使用缓存
    if cache_file and os.path.isfile(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"[WARN] 读取缓存异常({cache_file}): {e}")

    # 2. 拉取最新数据
    data = get_fliggy_flight_table_json(dep_city, arr_city, dep_date)
    if data[0] == "查询时间超出限制": # 未进行有效查询，不缓存
        return data
    new_cache_file = os.path.join(
        CACHE_FLIGGY_DIR, f"{dep_date}_{dep_city}_{arr_city}_{today_str}.json"
    )
    try:
        with open(new_cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[WARN] 写缓存异常({new_cache_file}): {e}")
    return data


def filter_and_sort_flight_list(flight_list, strategy=None, company=None, start_time_limit=None):
    """
    :param flight_list: list of dict，须有 "出发时间"、"票价"、"航司航班号"
    :param strategy: 排序方式 'price' 或 'time'
    :param company: 航司名或缩写，模糊筛选
    :param start_time_limit: 出发时间段筛选，支持'8~10', '7:00~18:20', '12'等
    :return: 排好序的、筛好的列表
    """
    def parse_time_part(s):
        m = re.match(r'(\d{1,2})', s.strip())
        if m:
            h = int(m.group(1))
            if 0 <= h <= 24:
                return h
        return None

    def get_range(range_str):
        if not range_str or str(range_str).strip() == '':
            return 0, 24  # 兜底不过滤
        s = str(range_str).replace("—", "~").replace("-", "~").replace("：", ":")
        parts = [p.strip() for p in s.split("~") if p.strip()]
        if len(parts) == 1:
            h = parse_time_part(parts[0])
            if h is not None:
                return max(0, h-2), min(24, h+2)
            else:
                return 0, 24
        if len(parts) == 2:
            h1 = parse_time_part(parts[0])
            h2 = parse_time_part(parts[1])
            if h1 is not None and h2 is not None:
                a, b = min(h1, h2), max(h1, h2)
                return max(0, a), min(24, b)
            else:
                return 0, 24
        return 0, 24

    # ===== 过滤 start_time_limit =====
    range_start, range_end = get_range(start_time_limit)
    filtered = flight_list

    def get_hour(val):
        try:
            if " " in val:
                time_block = val.split()[1]
            else:
                time_block = val
            return int(time_block.split(":")[0])
        except Exception:
            return None

    if not (range_start == 0 and range_end == 24):  # 只有有效时间才过滤
        tmp = []
        for f in filtered:
            v = f.get("出发时间") or f.get("start_time")
            hour = get_hour(v) if v and len(v) >= 4 else None
            if hour is not None and range_start <= hour <= range_end:
                tmp.append(f)
        filtered = tmp

    # ===== 过滤 company =====
    if company:
        filtered = [
            f for f in filtered
            if company in f.get('航司航班号', '') or company in f.get('航司', '')
        ]

    # ===== 排序 =====
    if strategy == 'price':
        def price_key(f):
            price_str = str(f.get("票价", "0")).replace('¥', '').replace(',', '')
            return int(price_str) if price_str.isdigit() else 9999999
        filtered = sorted(filtered, key=price_key)

    elif strategy == 'time':
        def time_key(f):
            time_str = f.get("出发时间", "00:00")
            try:
                t = datetime.strptime(time_str, "%H:%M") if ':' in time_str and len(time_str)<=5 else datetime.strptime(time_str.split()[1], "%H:%M")
            except Exception:
                t = datetime.strptime("00:00", "%H:%M")
            return t
        filtered = sorted(filtered, key=time_key)

    return filtered




# 用法举例：
if __name__=="__main__":
    # pipeline = init_ocr_pipeline()
    # pipeline = 1
    json_table = get_12306_table_json("南京", "上海", "2025-07-30")
    # json_table = get_fliggy_flight_table_json_cache("南京","成都", "2025-07-30")
    print(len(json_table))
    #for train in json_table:
    #    print(train['number'],train['start_time'],train['end_time'],train['from_station'],train['to_station'],train['duration'])