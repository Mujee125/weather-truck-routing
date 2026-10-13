import math
from datetime import datetime

from rest_framework import serializers

from trip_analysis.domain.types import Checkpoint, Route
from trip_analysis.services.trip_analysis_service import AnalysisResult

ALLOWED_INTERVALS = (10, 25, 50)


class AnalyzeRequestSerializer(serializers.Serializer):
    """Validates the request per api-contract.md section 1."""

    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure_time = serializers.CharField()
    load_weight_lb = serializers.FloatField()
    checkpoint_interval_miles = serializers.ChoiceField(choices=ALLOWED_INTERVALS)

    def validate_departure_time(self, value: str) -> datetime:
        try:
            parsed = datetime.fromisoformat(value.strip())
        except ValueError:
            raise serializers.ValidationError("Must be an ISO 8601 date-time.")
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise serializers.ValidationError("Must include a timezone offset, e.g. 2026-10-14T08:00:00-05:00.")
        return parsed

    def validate_load_weight_lb(self, value: float) -> float:
        if not math.isfinite(value) or value <= 0:
            raise serializers.ValidationError("Must be a positive number (pounds).")
        return value


# ---- Response mapping: domain objects -> contract JSON (single place to change) ----

def _serialize_checkpoint(cp: Checkpoint) -> dict:
    weather = None
    if cp.weather is not None:
        weather = {
            "wind_mph": cp.weather.wind_mph,
            "rain_in_per_hour": cp.weather.rain_in_per_hour,
            "snow_in_per_hour": cp.weather.snow_in_per_hour,
        }
    return {
        "distance_from_origin_miles": cp.distance_from_origin_miles,
        "latitude": cp.latitude,
        "longitude": cp.longitude,
        "eta": cp.eta,
        "weather": weather,
        "risk_level": cp.risk_level.value,
        "warnings": cp.warnings,
    }


def _serialize_route(route: Route) -> dict:
    return {
        "id": route.id,
        "geometry": route.geometry,
        "distance_miles": route.distance_miles,
        "duration_minutes": route.duration_minutes,
        "eligible": route.eligible,
        "summary": {
            "severe_miles": route.summary.severe_miles,
            "high_miles": route.summary.high_miles,
            "average_risk_score": route.summary.average_risk_score,
        },
        "checkpoints": [_serialize_checkpoint(cp) for cp in route.checkpoints],
        "warnings": route.warnings,
    }


def serialize_analysis(result: AnalysisResult) -> dict:
    return {
        "recommended_route_id": result.recommended_route_id,
        "routes": [_serialize_route(r) for r in result.routes],
        "heatmap": result.heatmap,
        "warnings": result.warnings,
    }