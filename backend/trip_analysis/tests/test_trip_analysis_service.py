from datetime import datetime, timedelta, timezone

from trip_analysis.providers.geocoding.base import GeocodingProvider
from trip_analysis.providers.routing.base import RoutingProvider, RouteOption, RouteStep
from trip_analysis.providers.weather.base import WeatherProvider, HourlySample
from trip_analysis.services.trip_analysis_service import TripAnalysisService, TripRequest
import pytest

from trip_analysis.services.trip_analysis_service import TripAnalysisService, TripAnalysisError
from trip_analysis.tests.fakes import (
    FakeGeocoder, FakeRouter, FakeWeatherCalm, FakeWeatherSevere,
    FakeWeatherDown, FakeWeatherPartial, make_trip_request,
)


def test_partial_weather_failure_marks_unknown_never_low():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=1), FakeWeatherPartial())
    result = service.analyze(make_trip_request())

    levels = [cp.risk_level.value for cp in result.routes[0].checkpoints]
    assert levels == ["low", "unknown"]
    assert any("Weather unavailable for" in w for w in result.warnings)
    assert result.routes[0].eligible is True


def test_all_weather_failing_raises_analysis_error():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=1), FakeWeatherDown())
    with pytest.raises(TripAnalysisError) as exc_info:
        service.analyze(make_trip_request())
    assert exc_info.value.code == "WEATHER_PROVIDER_UNAVAILABLE"


def make_trip_request():
    return TripRequest(
        origin="Origin City",
        destination="Destination City",
        departure_time=datetime.now(timezone.utc),
        load_weight_lb=20000,
        checkpoint_interval_miles=25,
    )


def test_analyze_happy_path_calm_weather():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=3), FakeWeatherCalm())
    result = service.analyze(make_trip_request())

    assert len(result.routes) == 3
    assert result.recommended_route_id is not None
    assert all(r.eligible for r in result.routes)
    assert all(cp.risk_level.value == "low" for r in result.routes for cp in r.checkpoints)


def test_analyze_fewer_than_three_routes_adds_warning():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=1), FakeWeatherCalm())
    result = service.analyze(make_trip_request())

    assert len(result.routes) == 1
    assert any("Only 1 route option" in w for w in result.warnings)


def test_analyze_severe_wind_makes_routes_ineligible():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=2), FakeWeatherSevere())
    result = service.analyze(make_trip_request())

    assert all(not r.eligible for r in result.routes)
    assert result.recommended_route_id is None
    assert any("No eligible route" in w for w in result.warnings)


def test_heatmap_structure():
    service = TripAnalysisService(FakeGeocoder(), FakeRouter(route_count=1), FakeWeatherCalm())
    result = service.analyze(make_trip_request())

    assert "reference_time" in result.heatmap
    assert result.heatmap["available_forecast_hours"][0] == 0
    assert len(result.heatmap["data"]) > 0
    assert "forecast" in result.heatmap["data"][0]