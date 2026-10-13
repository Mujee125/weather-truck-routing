from datetime import datetime, timedelta, timezone

from trip_analysis.providers.exceptions import LocationNotFoundError, RoutingError, WeatherError
from trip_analysis.providers.geocoding.base import GeocodingProvider
from trip_analysis.providers.routing.base import RoutingProvider, RouteOption, RouteStep
from trip_analysis.providers.weather.base import WeatherProvider, HourlySample
from trip_analysis.services.trip_analysis_service import TripRequest


class FakeGeocoder(GeocodingProvider):
    def geocode(self, location_text):
        return (32.8, -96.8) if "origin" in location_text.lower() else (33.5, -96.0)


class NotFoundGeocoder(GeocodingProvider):
    def geocode(self, location_text):
        raise LocationNotFoundError(f"No location found for '{location_text}'.")


class FakeRouter(RoutingProvider):
    def __init__(self, route_count=3):
        self.route_count = route_count

    def get_route_options(self, origin, destination, target_count=3):
        return [
            RouteOption(
                geometry={"type": "LineString", "coordinates": [[origin[1], origin[0]], [destination[1], destination[0]]]},
                distance_miles=50,
                duration_minutes=60,
                steps=[RouteStep(distance_miles=50, duration_minutes=60)],
            )
            for _ in range(min(self.route_count, target_count))
        ]


class FailingRouter(RoutingProvider):
    def get_route_options(self, origin, destination, target_count=3):
        # Message deliberately contains a fake secret to prove it never reaches the client.
        raise RoutingError("boom https://example.com?api_key=SECRET123")


def _hourly(wind):
    now = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return [HourlySample(now + timedelta(hours=i), wind, 0, 0) for i in range(49)]


class FakeWeatherCalm(WeatherProvider):
    def get_hourly_forecast(self, lat, lng, forecast_days):
        return _hourly(10)


class FakeWeatherSevere(WeatherProvider):
    def get_hourly_forecast(self, lat, lng, forecast_days):
        return _hourly(60)


class FakeWeatherDown(WeatherProvider):
    def get_hourly_forecast(self, lat, lng, forecast_days):
        raise WeatherError("weather down")


class FakeWeatherPartial(WeatherProvider):
    """Fails for eastern points (lng > -96.4); works elsewhere. Deterministic."""
    def get_hourly_forecast(self, lat, lng, forecast_days):
        if lng > -96.4:
            raise WeatherError("partial outage")
        return _hourly(10)


def make_trip_request():
    return TripRequest(
        origin="Origin City",
        destination="Destination City",
        departure_time=datetime.now(timezone.utc),
        load_weight_lb=20000,
        checkpoint_interval_miles=25,
    )