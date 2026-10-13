"""
Pure data types for the domain layer.
No Django, no I/O. These mirror the API contract field names so that
serialization later is a near-direct mapping.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class RiskLevel(str, Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    SEVERE = "severe"
    NO_TRAVEL = "no_travel"
    UNKNOWN = "unknown"   # weather data missing — never defaults to LOW


# Numeric severity used for averaging and comparisons.
# UNKNOWN is intentionally excluded from averages (handled in recommendation.py).
SEVERITY_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MODERATE: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.SEVERE: 3,
    RiskLevel.NO_TRAVEL: 4,
}


@dataclass
class WeatherSample:
    wind_mph: Optional[float]
    rain_in_per_hour: Optional[float]
    snow_in_per_hour: Optional[float]

    @property
    def is_missing(self) -> bool:
        return self.wind_mph is None or self.rain_in_per_hour is None or self.snow_in_per_hour is None


@dataclass
class Checkpoint:
    distance_from_origin_miles: float
    latitude: float
    longitude: float
    eta: str                      # ISO 8601 string
    weather: Optional[WeatherSample]
    risk_level: RiskLevel
    warnings: list[str] = field(default_factory=list)


@dataclass
class RouteSummary:
    severe_miles: float
    high_miles: float
    average_risk_score: float


@dataclass
class Route:
    id: str
    geometry: dict                 # GeoJSON LineString, [lng, lat] pairs
    distance_miles: float
    duration_minutes: float
    eligible: bool
    summary: RouteSummary
    checkpoints: list[Checkpoint]
    warnings: list[str] = field(default_factory=list)