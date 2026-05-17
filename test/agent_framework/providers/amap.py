from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


class AMapError(RuntimeError):
    """Base error for AMap provider failures."""


class AMapConfigurationError(AMapError):
    """Raised when the AMap provider is not configured."""


class AMapAPIError(AMapError):
    """Raised when AMap returns a failed response."""


@dataclass(frozen=True)
class AMapAddress:
    city: str
    address: str


class AMapClient:
    def __init__(
        self,
        api_key: str,
        *,
        timeout: float = 8.0,
        session: requests.Session | None = None,
        base_url: str = "https://restapi.amap.com",
    ) -> None:
        if not api_key:
            raise AMapConfigurationError("AMAP_API_KEY is required for realtime map tools.")
        self.api_key = api_key
        self.timeout = timeout
        self.session = session or requests.Session()
        self.base_url = base_url.rstrip("/")

    @classmethod
    def from_env(cls, *, required: bool = True) -> "AMapClient | None":
        api_key = get_amap_api_key(required=required)
        if not api_key:
            return None
        return cls(api_key=api_key)

    def resolve_location(self, city: str, address: str) -> dict[str, Any] | None:
        normalized = normalize_address(city=city, address=address)
        if not normalized.city or not normalized.address:
            return None

        poi_data = self._get(
            "/v5/place/text",
            {
                "keywords": normalized.address,
                "region": normalized.city,
                "citylimit": "true",
                "show_fields": "business",
            },
        )
        pois = poi_data.get("pois") or []
        if pois:
            return _shape_location_from_poi(pois[0], normalized)

        geocode_data = self._get(
            "/v3/geocode/geo",
            {
                "address": normalized.address,
                "city": normalized.city,
            },
        )
        geocodes = geocode_data.get("geocodes") or []
        if geocodes:
            return _shape_location_from_geocode(geocodes[0], normalized)

        return None

    def search_hotels(
        self,
        city: str,
        address: str,
        *,
        radius: int = 5000,
        limit: int = 6,
    ) -> dict[str, Any]:
        center = self.resolve_location(city, address)
        if not center:
            return _not_found_response(city=city, address=address, item_key="hotels")

        data = self._search_around(
            center["location"],
            radius=radius,
            types="100000",
            keywords="酒店",
            sortrule="weight",
        )
        items = _shape_pois(data.get("pois") or [], limit=limit)
        return {
            "ok": True,
            "source": "amap",
            "query": {"city": city, "address": address, "radius": radius},
            "center": center,
            "count": _safe_int(data.get("count"), len(items)),
            "hotels": items,
        }

    def search_restaurants(
        self,
        city: str,
        address: str,
        *,
        radius: int = 3000,
        keyword: str | None = None,
        limit: int = 6,
    ) -> dict[str, Any]:
        center = self.resolve_location(city, address)
        if not center:
            return _not_found_response(city=city, address=address, item_key="restaurants")

        data = self._search_around(
            center["location"],
            radius=radius,
            types="050000",
            keywords=keyword or "",
            sortrule="weight",
        )
        items = _shape_pois(data.get("pois") or [], limit=limit)
        return {
            "ok": True,
            "source": "amap",
            "query": {
                "city": city,
                "address": address,
                "radius": radius,
                "keyword": keyword or "",
            },
            "center": center,
            "count": _safe_int(data.get("count"), len(items)),
            "restaurants": items,
        }

    def summarize_route(
        self,
        origin_city: str,
        origin_address: str,
        destination_city: str,
        destination_address: str,
        *,
        limit: int = 3,
    ) -> dict[str, Any]:
        origin = self.resolve_location(origin_city, origin_address)
        destination = self.resolve_location(destination_city, destination_address)
        if not origin or not destination:
            return {
                "ok": False,
                "source": "amap",
                "error": "location_not_found",
                "origin": origin,
                "destination": destination,
            }

        routes: dict[str, Any] = {}
        warnings: list[str] = []

        transit_data = self._try_get(
            "/v5/direction/transit/integrated",
            {
                "origin": origin["location"],
                "destination": destination["location"],
                "city1": origin.get("citycode") or origin_city,
                "city2": destination.get("citycode") or destination_city,
                "strategy": "7",
                "alternativeRoute": str(limit),
                "show_fields": "cost",
            },
            warnings,
            "transit",
        )
        routes["transit"] = _shape_transit_routes(transit_data, limit=limit) if transit_data else []

        driving_data = self._try_get(
            "/v5/direction/driving",
            {
                "origin": origin["location"],
                "destination": destination["location"],
                "strategy": "32",
                "show_fields": "cost",
            },
            warnings,
            "driving",
        )
        routes["driving"] = _shape_driving_routes(driving_data, limit=limit) if driving_data else []

        walking_data = self._try_get(
            "/v5/direction/walking",
            {
                "origin": origin["location"],
                "destination": destination["location"],
                "show_fields": "cost",
            },
            warnings,
            "walking",
        )
        routes["walking"] = _shape_walking_routes(walking_data, limit=1) if walking_data else []

        return {
            "ok": True,
            "source": "amap",
            "origin": origin,
            "destination": destination,
            "routes": routes,
            "warnings": warnings,
        }

    def _search_around(
        self,
        location: str,
        *,
        radius: int,
        types: str,
        keywords: str,
        sortrule: str,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "location": location,
            "radius": max(500, min(int(radius), 50000)),
            "types": types,
            "sortrule": sortrule,
            "show_fields": "business,contact",
        }
        if keywords:
            params["keywords"] = keywords
        return self._get("/v5/place/around", params)

    def _try_get(
        self,
        path: str,
        params: dict[str, Any],
        warnings: list[str],
        label: str,
    ) -> dict[str, Any] | None:
        try:
            return self._get(path, params)
        except AMapError as exc:
            warnings.append(f"{label}: {exc}")
            return None

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        url = f"{self.base_url}{path}"
        request_params = {"key": self.api_key, **params}
        try:
            response = self.session.get(url, params=request_params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise AMapAPIError(f"AMap request failed: {exc}") from exc
        except ValueError as exc:
            raise AMapAPIError("AMap returned a non-JSON response.") from exc

        if data.get("status") not in (None, "1", 1):
            info = data.get("info") or "unknown_error"
            infocode = data.get("infocode")
            detail = f"{info} ({infocode})" if infocode else str(info)
            raise AMapAPIError(detail)

        return data


def get_amap_api_key(*, required: bool = True) -> str | None:
    api_key = os.getenv("AMAP_API_KEY")
    if api_key:
        return api_key
    if required:
        raise AMapConfigurationError("AMAP_API_KEY is required for realtime map tools.")
    return None


def has_amap_api_key() -> bool:
    return bool(os.getenv("AMAP_API_KEY"))


def normalize_address(city: str | None = None, address: str | None = None, **payload: Any) -> AMapAddress:
    source = dict(payload)
    if city is not None:
        source["city"] = city
    if address is not None:
        source["address"] = address

    resolved_city = (
        source.get("city")
        or source.get("city_name")
        or source.get("origin_city")
        or source.get("destination_city")
        or ""
    )
    resolved_address = (
        source.get("address")
        or source.get("location_name")
        or source.get("poi")
        or source.get("business_location")
        or source.get("keyword")
        or source.get("query")
        or ""
    )
    return AMapAddress(city=str(resolved_city).strip(), address=str(resolved_address).strip())


def _shape_location_from_poi(poi: dict[str, Any], query: AMapAddress) -> dict[str, Any]:
    return {
        "name": _as_text(poi.get("name")) or query.address,
        "address": _as_text(poi.get("address")) or query.address,
        "location": _as_text(poi.get("location")),
        "city": _as_text(poi.get("cityname")) or query.city,
        "citycode": _as_text(poi.get("citycode")),
        "adcode": _as_text(poi.get("adcode")),
        "poi_id": _as_text(poi.get("id")),
        "source_type": "poi",
    }


def _shape_location_from_geocode(geocode: dict[str, Any], query: AMapAddress) -> dict[str, Any]:
    return {
        "name": query.address,
        "address": _as_text(geocode.get("formatted_address")) or query.address,
        "location": _as_text(geocode.get("location")),
        "city": _as_text(geocode.get("city")) or query.city,
        "citycode": _as_text(geocode.get("citycode")),
        "adcode": _as_text(geocode.get("adcode")),
        "poi_id": "",
        "source_type": "geocode",
    }


def _shape_pois(pois: list[dict[str, Any]], *, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for poi in pois[: max(1, limit)]:
        business = poi.get("business") if isinstance(poi.get("business"), dict) else {}
        items.append(
            {
                "name": _as_text(poi.get("name")),
                "address": _join_address_parts(poi),
                "distance_meters": _safe_int(poi.get("distance")),
                "type": _as_text(poi.get("type")),
                "rating": _as_text(business.get("rating")),
                "cost": _as_text(business.get("cost")),
                "tag": _as_text(business.get("keytag")),
                "tel": _as_text(poi.get("tel")),
                "location": _as_text(poi.get("location")),
            }
        )
    return items


def _shape_transit_routes(data: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    transits = ((data.get("route") or {}).get("transits") or [])[: max(1, limit)]
    results: list[dict[str, Any]] = []
    for index, transit in enumerate(transits, start=1):
        cost = transit.get("cost") if isinstance(transit.get("cost"), dict) else {}
        results.append(
            {
                "rank": index,
                "distance_meters": _safe_int(transit.get("distance")),
                "duration_minutes": _seconds_to_minutes(cost.get("duration")),
                "walking_distance_meters": _safe_int(transit.get("walking_distance")),
                "fee": _as_text(cost.get("transit_fee")),
                "segments_count": len(transit.get("segments") or []),
            }
        )
    return results


def _shape_driving_routes(data: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    route = data.get("route") or {}
    paths = (route.get("paths") or [])[: max(1, limit)]
    results: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        cost = path.get("cost") if isinstance(path.get("cost"), dict) else {}
        results.append(
            {
                "rank": index,
                "distance_meters": _safe_int(path.get("distance")),
                "duration_minutes": _seconds_to_minutes(cost.get("duration")),
                "tolls": _as_text(cost.get("tolls")),
                "taxi_fee": _as_text(cost.get("taxi_fee") or route.get("taxi_cost")),
            }
        )
    return results


def _shape_walking_routes(data: dict[str, Any], *, limit: int) -> list[dict[str, Any]]:
    paths = ((data.get("route") or {}).get("paths") or [])[: max(1, limit)]
    results: list[dict[str, Any]] = []
    for index, path in enumerate(paths, start=1):
        cost = path.get("cost") if isinstance(path.get("cost"), dict) else {}
        results.append(
            {
                "rank": index,
                "distance_meters": _safe_int(path.get("distance")),
                "duration_minutes": _seconds_to_minutes(cost.get("duration")),
            }
        )
    return results


def _not_found_response(city: str, address: str, item_key: str) -> dict[str, Any]:
    return {
        "ok": False,
        "source": "amap",
        "error": "location_not_found",
        "query": {"city": city, "address": address},
        "count": 0,
        item_key: [],
    }


def _join_address_parts(poi: dict[str, Any]) -> str:
    parts = [
        _as_text(poi.get("cityname")),
        _as_text(poi.get("adname")),
        _as_text(poi.get("address")),
    ]
    return "".join(part for part in parts if part)


def _seconds_to_minutes(value: Any) -> int | None:
    seconds = _safe_int(value)
    if seconds is None:
        return None
    if seconds <= 0:
        return 0
    return max(1, round(seconds / 60))


def _safe_int(value: Any, default: int | None = None) -> int | None:
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return default


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return " ".join(str(item) for item in value if item)
    return str(value).strip()
