import logging
import math
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from trip_analysis.domain.types import Checkpoint, Route, RiskLevel, WeatherSample, SEVERITY_ORDER
from trip_analysis.domain.risk_rules import classify_checkpoint_risk
from trip_analysis.domain.recommendation import compute_route_summary, is_route_eligible, rank_routes
from trip_analysis.providers.exceptions import (
    ProviderError, GeocodingError, LocationNotFoundError, RoutingError,
)
from trip_analysis.providers.geocoding.base import GeocodingProvider
from trip_analysis.providers.routing.base import RoutingProvider, RouteOption
from trip_analysis.providers.weather.base import WeatherProvider, HourlySample
from trip_analysis.services.checkpoint_service import generate_checkpoints, PlannedCheckpoint

logger = logging.getLogger(__name__)

WEATHER_MATCH_TOLERANCE_MINUTES = 30
COORDINATE_ROUND_DECIMALS = 3   # ~111 m; used to dedupe weather lookups
WEATHER_MAX_WORKERS = 3
HEATMAP_HOURS = 48


@dataclass
class TripRequest:
    origin: str
    destination: str
    departure_time: datetime
    load_weight_lb: float
    checkpoint_interval_miles: float


@dataclass
class AnalysisResult:
    recommended_route_id: str | None
    routes: list[Route]
    heatmap: dict
    warnings: list[str]


class TripAnalysisError(Exception):
    """Analysis cannot proceed. `code` is machine-readable; `message` is user-safe."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _to_analysis_error(exc: ProviderError) -> TripAnalysisError:
    logger.warning("Provider failure: %s", exc)  # detail stays in server logs only
    if isinstance(exc, LocationNotFoundError):
        return TripAnalysisError("LOCATION_NOT_FOUND", str(exc))
    if isinstance(exc, GeocodingError):
        return TripAnalysisError("GEOCODING_PROVIDER_UNAVAILABLE", "Location lookup is temporarily unavailable.")
    if isinstance(exc, RoutingError):
        return TripAnalysisError("ROUTING_PROVIDER_UNAVAILABLE", "Route data is temporarily unavailable.")
    return TripAnalysisError("PROVIDER_UNAVAILABLE", "An external data provider is temporarily unavailable.")


def _round_coord(lat: float, lng: float) -> tuple[float, float]:
    return (round(lat, COORDINATE_ROUND_DECIMALS), round(lng, COORDINATE_ROUND_DECIMALS))


def _compute_forecast_days(now: datetime, departure_time: datetime, max_duration_minutes: float) -> int:
    """Size the forecast window to cover both the 48h heatmap and the trip's ETAs."""
    required_end = max(now + timedelta(hours=HEATMAP_HOURS), departure_time + timedelta(minutes=max_duration_minutes))
    days_needed = math.ceil((required_end - now).total_seconds() / 86400) + 1
    return max(2, min(days_needed, 16))


def _find_closest_sample(samples: list[HourlySample], target_time: datetime) -> HourlySample | None:
    if not samples:
        return None
    closest = min(samples, key=lambda s: abs((s.timestamp - target_time).total_seconds()))
    if abs((closest.timestamp - target_time).total_seconds()) / 60 > WEATHER_MATCH_TOLERANCE_MINUTES:
        return None
    return closest


def _to_weather_sample(s: HourlySample) -> WeatherSample:
    return WeatherSample(wind_mph=s.wind_mph, rain_in_per_hour=s.rain_in_per_hour, snow_in_per_hour=s.snow_in_per_hour)


def _build_heatmap(now: datetime, weather_by_coord: dict, load_weight_lb: float) -> dict:
    """Corridor heatmap data.

    reference_time = current UTC hour (server now, floored), so forecast hour 0 is
    "this hour". Risk is evaluated server-side per point per hour (same rules and
    load weight as checkpoints), so the frontend never re-implements business rules.
    """
    reference_time = now.replace(minute=0, second=0, microsecond=0)
    data = []
    max_offset = 0

    for (lat, lng), samples in sorted(weather_by_coord.items()):
        start = next((i for i, s in enumerate(samples) if s.timestamp >= reference_time), None)
        if start is None:
            continue
        window = samples[start:start + HEATMAP_HOURS + 1]
        max_offset = max(max_offset, len(window) - 1)

        forecast = []
        for offset, s in enumerate(window):
            risk = classify_checkpoint_risk(_to_weather_sample(s), load_weight_lb)
            forecast.append({
                "hour_offset": offset,
                "wind_mph": s.wind_mph,
                "rain_in_per_hour": s.rain_in_per_hour,
                "snow_in_per_hour": s.snow_in_per_hour,
                "risk_level": risk.value,
                "risk_score": SEVERITY_ORDER.get(risk),   # None when unknown
            })
        data.append({"latitude": lat, "longitude": lng, "forecast": forecast})

    return {
        "reference_time": reference_time.isoformat(),
        "available_forecast_hours": list(range(max_offset + 1)) if data else [],
        "data": data,
    }


class TripAnalysisService:
    def __init__(self, geocoder: GeocodingProvider, router: RoutingProvider, weather: WeatherProvider):
        self.geocoder = geocoder
        self.router = router
        self.weather = weather

    def analyze(self, trip: TripRequest) -> AnalysisResult:
        warnings: list[str] = []
        now = datetime.now(timezone.utc)

        route_options = self._resolve_routes(trip)
        if len(route_options) < 3:
            warnings.append(f"Only {len(route_options)} route option(s) returned by the routing provider.")

        planned_by_route = [
            generate_checkpoints(r, trip.departure_time, trip.checkpoint_interval_miles) for r in route_options
        ]
        max_duration = max(r.duration_minutes for r in route_options)
        forecast_days = _compute_forecast_days(now, trip.departure_time, max_duration)

        unique_coords = sorted({
            _round_coord(cp.latitude, cp.longitude) for planned in planned_by_route for cp in planned
        })
        weather_by_coord = self._fetch_weather(unique_coords, forecast_days, warnings)

        routes = [
            self._assess_route(f"route-{i + 1}", option, planned, weather_by_coord, trip.load_weight_lb)
            for i, (option, planned) in enumerate(zip(route_options, planned_by_route))
        ]

        routes, recommended_route_id = rank_routes(routes)
        if recommended_route_id is None:
            warnings.append("No eligible route available; all routes contain a No Travel checkpoint.")

        return AnalysisResult(
            recommended_route_id=recommended_route_id,
            routes=routes,
            heatmap=_build_heatmap(now, weather_by_coord, trip.load_weight_lb),
            warnings=warnings,
        )

    def _resolve_routes(self, trip: TripRequest) -> list[RouteOption]:
        try:
            origin = self.geocoder.geocode(trip.origin)
            destination = self.geocoder.geocode(trip.destination)
            return self.router.get_route_options(origin, destination, target_count=3)
        except ProviderError as exc:
            raise _to_analysis_error(exc) from None

    def _fetch_weather(self, coords, forecast_days, warnings) -> dict:
        def fetch(coord):
            try:
                return coord, self.weather.get_hourly_forecast(coord[0], coord[1], forecast_days)
            except ProviderError as exc:
                logger.warning("Weather fetch failed for %s: %s", coord, exc)
                return coord, None

        with ThreadPoolExecutor(max_workers=WEATHER_MAX_WORKERS) as pool:
            results = list(pool.map(fetch, coords))

        weather_by_coord = {coord: samples for coord, samples in results if samples is not None}
        failed = len(results) - len(weather_by_coord)

        if not weather_by_coord:
            raise TripAnalysisError("WEATHER_PROVIDER_UNAVAILABLE", "Weather data is temporarily unavailable.")
        if failed:
            warnings.append(
                f"Weather unavailable for {failed} of {len(results)} checkpoint locations; "
                "affected checkpoints are marked unknown."
            )
        return weather_by_coord

    @staticmethod
    def _assess_route(route_id, option, planned: list[PlannedCheckpoint], weather_by_coord, load_weight_lb) -> Route:
        checkpoints: list[Checkpoint] = []
        unknown_count = 0

        for pc in planned:
            samples = weather_by_coord.get(_round_coord(pc.latitude, pc.longitude), [])
            matched = _find_closest_sample(samples, pc.eta)
            weather_sample = _to_weather_sample(matched) if matched else None

            risk_level = classify_checkpoint_risk(weather_sample, load_weight_lb)
            cp_warnings = []
            if risk_level == RiskLevel.UNKNOWN:
                unknown_count += 1
                cp_warnings.append("Weather data unavailable for this checkpoint's location/time.")

            checkpoints.append(Checkpoint(
                distance_from_origin_miles=pc.distance_from_origin_miles,
                latitude=pc.latitude,
                longitude=pc.longitude,
                eta=pc.eta.isoformat(),
                weather=weather_sample,
                risk_level=risk_level,
                warnings=cp_warnings,
            ))

        route_warnings = []
        if unknown_count:
            route_warnings.append(
                f"{unknown_count} of {len(checkpoints)} checkpoints have unknown risk (weather unavailable); "
                "they are excluded from mile totals and average risk."
            )

        eligible = is_route_eligible(checkpoints)
        if not eligible:
            route_warnings.append("Route contains a No Travel checkpoint and is ineligible for recommendation.")

        return Route(
            id=route_id,
            geometry=option.geometry,
            distance_miles=round(option.distance_miles, 2),
            duration_minutes=round(option.duration_minutes, 1),
            eligible=eligible,
            summary=compute_route_summary(checkpoints, option.distance_miles),
            checkpoints=checkpoints,
            warnings=route_warnings,
        )