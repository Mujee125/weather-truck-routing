from datetime import datetime, timezone

import pytest
from rest_framework.test import APIClient

from trip_analysis.services.trip_analysis_service import TripAnalysisService
from trip_analysis.tests.fakes import (
    FakeGeocoder, NotFoundGeocoder, FakeRouter, FailingRouter,
    FakeWeatherCalm, FakeWeatherDown,
)

URL = "/api/routes/analyze"


def valid_payload(**overrides):
    payload = {
        "origin": "Origin City",
        "destination": "Destination City",
        "departure_time": datetime.now(timezone.utc).isoformat(),
        "load_weight_lb": 20000,
        "checkpoint_interval_miles": 25,
    }
    payload.update(overrides)
    return payload


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def use_service(monkeypatch):
    """Injects a service built from fakes; returns a list recording factory calls."""
    def _use(service):
        calls = []

        def factory():
            calls.append(1)
            return service

        monkeypatch.setattr("trip_analysis.api.views.build_default_service", factory)
        return calls
    return _use


def test_success_matches_contract_shape(client, use_service):
    use_service(TripAnalysisService(FakeGeocoder(), FakeRouter(3), FakeWeatherCalm()))
    response = client.post(URL, valid_payload(), format="json")

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"recommended_route_id", "routes", "heatmap", "warnings"}
    assert len(body["routes"]) == 3

    route = body["routes"][0]
    assert set(route) == {"id", "geometry", "distance_miles", "duration_minutes",
                          "eligible", "summary", "checkpoints", "warnings"}
    assert set(route["summary"]) == {"severe_miles", "high_miles", "average_risk_score"}

    checkpoint = route["checkpoints"][0]
    assert set(checkpoint) == {"distance_from_origin_miles", "latitude", "longitude",
                               "eta", "weather", "risk_level", "warnings"}
    assert checkpoint["risk_level"] == "low"
    assert set(checkpoint["weather"]) == {"wind_mph", "rain_in_per_hour", "snow_in_per_hour"}

    assert set(body["heatmap"]) == {"reference_time", "available_forecast_hours", "data"}
    first_hour = body["heatmap"]["data"][0]["forecast"][0]
    assert {"risk_level", "risk_score"} <= set(first_hour)


@pytest.mark.parametrize("overrides,field", [
    ({"origin": ""}, "origin"),
    ({"origin": "   "}, "origin"),
    ({"destination": ""}, "destination"),
    ({"departure_time": "2026-10-14T08:00:00"}, "departure_time"),   # no timezone
    ({"departure_time": "not-a-date"}, "departure_time"),
    ({"load_weight_lb": 0}, "load_weight_lb"),
    ({"load_weight_lb": -5}, "load_weight_lb"),
    ({"load_weight_lb": "heavy"}, "load_weight_lb"),
    ({"checkpoint_interval_miles": 30}, "checkpoint_interval_miles"),
])
def test_invalid_input_returns_400_and_never_calls_providers(client, use_service, overrides, field):
    calls = use_service(TripAnalysisService(FakeGeocoder(), FakeRouter(3), FakeWeatherCalm()))
    response = client.post(URL, valid_payload(**overrides), format="json")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "INVALID_REQUEST"
    assert field in error["details"]
    assert calls == []


def test_missing_field_returns_400(client, use_service):
    calls = use_service(TripAnalysisService(FakeGeocoder(), FakeRouter(3), FakeWeatherCalm()))
    payload = valid_payload()
    payload.pop("origin")
    response = client.post(URL, payload, format="json")

    assert response.status_code == 400
    assert calls == []


def test_unknown_location_returns_400(client, use_service):
    use_service(TripAnalysisService(NotFoundGeocoder(), FakeRouter(3), FakeWeatherCalm()))
    response = client.post(URL, valid_payload(), format="json")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "LOCATION_NOT_FOUND"


def test_routing_failure_returns_502_without_leaking_secrets(client, use_service):
    use_service(TripAnalysisService(FakeGeocoder(), FailingRouter(), FakeWeatherCalm()))
    response = client.post(URL, valid_payload(), format="json")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "ROUTING_PROVIDER_UNAVAILABLE"
    assert "SECRET123" not in response.content.decode()


def test_total_weather_failure_returns_502(client, use_service):
    use_service(TripAnalysisService(FakeGeocoder(), FakeRouter(3), FakeWeatherDown()))
    response = client.post(URL, valid_payload(), format="json")

    assert response.status_code == 502
    assert response.json()["error"]["code"] == "WEATHER_PROVIDER_UNAVAILABLE"


def test_malformed_json_uses_contract_error_shape(client):
    response = client.post(URL, data="{bad json", content_type="application/json")
    assert response.status_code == 400
    assert set(response.json()["error"]) >= {"code", "message"}


def test_wrong_method_uses_contract_error_shape(client):
    response = client.get(URL)
    assert response.status_code == 405
    assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"