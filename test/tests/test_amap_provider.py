import os
import unittest
from unittest.mock import patch

from agent_framework.core.settings import SearchSettings
from agent_framework.providers.amap import AMapClient, normalize_address
from agent_framework.tools.amap import hotel_search, location_lookup, route_summary
from agent_framework.tools.registry import build_default_tool_registry


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params, timeout):
        self.calls.append({"url": url, "params": params, "timeout": timeout})
        return FakeResponse(self.responses.pop(0))


class AMapProviderTests(unittest.TestCase):
    def test_normalize_address_accepts_business_location_alias(self):
        normalized = normalize_address(city_name="上海", business_location="上海中心大厦")

        self.assertEqual(normalized.city, "上海")
        self.assertEqual(normalized.address, "上海中心大厦")

    def test_location_lookup_shapes_poi_result(self):
        client = AMapClient(
            "test-key",
            session=FakeSession(
                [
                    {
                        "status": "1",
                        "count": "1",
                        "pois": [
                            {
                                "id": "B001",
                                "name": "上海中心大厦",
                                "address": "银城中路501号",
                                "location": "121.50109,31.23691",
                                "cityname": "上海市",
                                "citycode": "021",
                                "adcode": "310115",
                            }
                        ],
                    }
                ]
            ),
        )

        result = location_lookup("上海", "上海中心大厦", client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(result["location"]["name"], "上海中心大厦")
        self.assertEqual(result["location"]["source_type"], "poi")

    def test_hotel_search_shapes_poi_items(self):
        client = AMapClient(
            "test-key",
            session=FakeSession(
                [
                    {
                        "status": "1",
                        "count": "1",
                        "pois": [
                            {
                                "id": "B001",
                                "name": "上海中心大厦",
                                "address": "银城中路501号",
                                "location": "121.50109,31.23691",
                                "cityname": "上海市",
                                "citycode": "021",
                                "adcode": "310115",
                            }
                        ],
                    },
                    {
                        "status": "1",
                        "count": "1",
                        "pois": [
                            {
                                "name": "全季酒店",
                                "address": "商城路1号",
                                "cityname": "上海市",
                                "adname": "浦东新区",
                                "distance": "850",
                                "type": "住宿服务;宾馆酒店",
                                "business": {"rating": "4.6", "keytag": "经济型"},
                                "tel": "021-00000000",
                                "location": "121.50,31.23",
                            }
                        ],
                    },
                ]
            ),
        )

        result = hotel_search("上海", "上海中心大厦", client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["hotels"][0]["name"], "全季酒店")
        self.assertEqual(result["hotels"][0]["distance_meters"], 850)

    def test_route_summary_shapes_transit_driving_and_walking(self):
        client = AMapClient(
            "test-key",
            session=FakeSession(
                [
                    {
                        "status": "1",
                        "count": "1",
                        "pois": [
                            {
                                "name": "东昌路",
                                "address": "东昌路",
                                "location": "121.51,31.23",
                                "cityname": "上海市",
                                "citycode": "021",
                            }
                        ],
                    },
                    {
                        "status": "1",
                        "count": "1",
                        "pois": [
                            {
                                "name": "上海中心大厦",
                                "address": "银城中路501号",
                                "location": "121.50,31.23",
                                "cityname": "上海市",
                                "citycode": "021",
                            }
                        ],
                    },
                    {
                        "status": "1",
                        "route": {
                            "transits": [
                                {
                                    "distance": "1500",
                                    "walking_distance": "300",
                                    "cost": {"duration": "720", "transit_fee": "3"},
                                    "segments": [{"bus": {}}],
                                }
                            ]
                        },
                    },
                    {
                        "status": "1",
                        "route": {
                            "taxi_cost": "18",
                            "paths": [
                                {
                                    "distance": "1700",
                                    "cost": {"duration": "600", "taxi_fee": "18"},
                                }
                            ],
                        },
                    },
                    {
                        "status": "1",
                        "route": {
                            "paths": [
                                {
                                    "distance": "1200",
                                    "cost": {"duration": "900"},
                                }
                            ]
                        },
                    },
                ]
            ),
        )

        result = route_summary("上海", "东昌路", "上海", "上海中心大厦", client=client)

        self.assertTrue(result["ok"])
        self.assertEqual(result["routes"]["transit"][0]["duration_minutes"], 12)
        self.assertEqual(result["routes"]["driving"][0]["taxi_fee"], "18")
        self.assertEqual(result["routes"]["walking"][0]["distance_meters"], 1200)


class AMapToolRegistryTests(unittest.TestCase):
    def test_amap_tools_are_hidden_without_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            registry = build_default_tool_registry(SearchSettings())

        self.assertNotIn("amap_location_lookup", [tool.name for tool in registry.tools])

    def test_amap_tools_are_registered_with_api_key(self):
        with patch.dict(os.environ, {"AMAP_API_KEY": "test-key"}, clear=True):
            registry = build_default_tool_registry(SearchSettings())

        names = [tool.name for tool in registry.tools]
        self.assertIn("amap_location_lookup", names)
        self.assertIn("amap_route_summary", names)
        self.assertIn("amap_hotel_search", names)
        self.assertIn("amap_restaurant_search", names)


if __name__ == "__main__":
    unittest.main()
