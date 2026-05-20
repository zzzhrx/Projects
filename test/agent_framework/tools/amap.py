from __future__ import annotations

from typing import Any, Callable

from agent_framework.providers.amap import AMapClient


def location_lookup(city: str, address: str, *, client: AMapClient | None = None) -> dict[str, Any]:
    amap_client = client or AMapClient.from_env()
    location = amap_client.resolve_location(city, address)
    if not location:
        return {
            "ok": False,
            "source": "amap",
            "error": "location_not_found",
            "query": {"city": city, "address": address},
        }
    return {
        "ok": True,
        "source": "amap",
        "query": {"city": city, "address": address},
        "location": location,
    }


def route_summary(
    origin_city: str,
    origin_address: str,
    destination_city: str,
    destination_address: str,
    *,
    client: AMapClient | None = None,
) -> dict[str, Any]:
    amap_client = client or AMapClient.from_env()
    return amap_client.summarize_route(
        origin_city=origin_city,
        origin_address=origin_address,
        destination_city=destination_city,
        destination_address=destination_address,
    )


def hotel_search(
    city: str,
    address: str,
    radius: int = 5000,
    *,
    client: AMapClient | None = None,
) -> dict[str, Any]:
    amap_client = client or AMapClient.from_env()
    return amap_client.search_hotels(city=city, address=address, radius=radius)


def restaurant_search(
    city: str,
    address: str,
    radius: int = 3000,
    keyword: str = "",
    *,
    client: AMapClient | None = None,
) -> dict[str, Any]:
    amap_client = client or AMapClient.from_env()
    return amap_client.search_restaurants(
        city=city,
        address=address,
        radius=radius,
        keyword=keyword or None,
    )


def weather_forecast(
    city: str,
    address: str = "",
    *,
    client: AMapClient | None = None,
) -> dict[str, Any]:
    amap_client = client or AMapClient.from_env()
    return amap_client.weather_forecast(city=city, address=address or None)


def build_amap_location_tool(client: AMapClient | None = None):
    def amap_location_lookup(city: str, address: str) -> dict[str, Any]:
        """Resolve a city and address into AMap location metadata."""
        return location_lookup(city=city, address=address, client=client)

    return _wrap_tool(
        name="amap_location_lookup",
        description="Resolve a city and address into structured location metadata using AMap.",
        func=amap_location_lookup,
    )


def build_amap_route_tool(client: AMapClient | None = None):
    def amap_route_summary(
        origin_city: str,
        origin_address: str,
        destination_city: str,
        destination_address: str,
    ) -> dict[str, Any]:
        """Summarize transit, driving, and walking routes between two addresses."""
        return route_summary(
            origin_city=origin_city,
            origin_address=origin_address,
            destination_city=destination_city,
            destination_address=destination_address,
            client=client,
        )

    return _wrap_tool(
        name="amap_route_summary",
        description="Summarize transit, driving, and walking routes between two locations using AMap.",
        func=amap_route_summary,
    )


def build_amap_hotel_tool(client: AMapClient | None = None):
    def amap_hotel_search(city: str, address: str, radius: int = 5000) -> dict[str, Any]:
        """Search hotels around a business location using AMap POI data."""
        return hotel_search(city=city, address=address, radius=radius, client=client)

    return _wrap_tool(
        name="amap_hotel_search",
        description="Search hotels around a business location using AMap POI data.",
        func=amap_hotel_search,
    )


def build_amap_restaurant_tool(client: AMapClient | None = None):
    def amap_restaurant_search(
        city: str,
        address: str,
        radius: int = 3000,
        keyword: str = "",
    ) -> dict[str, Any]:
        """Search restaurants around a business location using AMap POI data."""
        return restaurant_search(
            city=city,
            address=address,
            radius=radius,
            keyword=keyword,
            client=client,
        )

    return _wrap_tool(
        name="amap_restaurant_search",
        description="Search restaurants around a business location using AMap POI data.",
        func=amap_restaurant_search,
    )


def build_amap_weather_tool(client: AMapClient | None = None):
    def amap_weather_forecast(city: str, address: str = "") -> dict[str, Any]:
        """Get a weather forecast for a city or business location using AMap."""
        return weather_forecast(city=city, address=address, client=client)

    return _wrap_tool(
        name="amap_weather_forecast",
        description="Get a weather forecast for a city or business location using AMap.",
        func=amap_weather_forecast,
    )


def _wrap_tool(name: str, description: str, func: Callable[..., dict[str, Any]]):
    try:
        from langchain_core.tools import StructuredTool
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "Missing dependency `langchain-core`. Install the packages in requirements.txt first."
        ) from exc

    return StructuredTool.from_function(
        name=name,
        description=description,
        func=func,
    )
