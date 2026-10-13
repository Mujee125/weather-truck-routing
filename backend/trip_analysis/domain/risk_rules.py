"""
Weather threshold classification and load-override rules.

Implements DECISIONS.md sections 1 and 2:
- Half-open interval boundaries
- Base risk = max severity across wind/rain/snow
- Load rules escalate risk, never reduce it
"""

from .types import RiskLevel, SEVERITY_ORDER, WeatherSample


def classify_wind(wind_mph: float) -> RiskLevel:
    if wind_mph < 25:
        return RiskLevel.LOW
    if wind_mph < 35:
        return RiskLevel.MODERATE
    if wind_mph < 45:
        return RiskLevel.HIGH
    if wind_mph < 55:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_rain(rain_in_per_hour: float) -> RiskLevel:
    if rain_in_per_hour < 0.10:
        return RiskLevel.LOW
    if rain_in_per_hour < 0.25:
        return RiskLevel.MODERATE
    if rain_in_per_hour < 0.50:
        return RiskLevel.HIGH
    if rain_in_per_hour <= 1.00:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def classify_snow(snow_in_per_hour: float) -> RiskLevel:
    if snow_in_per_hour < 0.5:
        return RiskLevel.LOW
    if snow_in_per_hour < 1.0:
        return RiskLevel.MODERATE
    if snow_in_per_hour < 2.0:
        return RiskLevel.HIGH
    if snow_in_per_hour <= 3.0:
        return RiskLevel.SEVERE
    return RiskLevel.NO_TRAVEL


def _max_severity(levels: list[RiskLevel]) -> RiskLevel:
    return max(levels, key=lambda lvl: SEVERITY_ORDER[lvl])


def apply_load_overrides(base_risk: RiskLevel, wind_mph: float, load_weight_lb: float) -> RiskLevel:
    """
    DECISIONS.md section 2 — load rules escalate risk, never reduce it.
    """
    if wind_mph >= 55:
        return RiskLevel.NO_TRAVEL

    if 45 <= wind_mph <= 54 and load_weight_lb > 30_000:
        return RiskLevel.NO_TRAVEL

    if 35 <= wind_mph <= 44 and load_weight_lb > 40_000:
        return _max_severity([base_risk, RiskLevel.SEVERE])

    return base_risk


def classify_checkpoint_risk(weather: WeatherSample, load_weight_lb: float) -> RiskLevel:
    """
    Combines wind/rain/snow into a single risk level for a checkpoint,
    then applies load-weight overrides.

    Returns RiskLevel.UNKNOWN if any weather value is missing — never
    silently defaults to LOW (per DECISIONS.md section 5).
    """
    if weather is None or weather.is_missing:
        return RiskLevel.UNKNOWN

    wind_level = classify_wind(weather.wind_mph)
    rain_level = classify_rain(weather.rain_in_per_hour)
    snow_level = classify_snow(weather.snow_in_per_hour)

    base_risk = _max_severity([wind_level, rain_level, snow_level])

    return apply_load_overrides(base_risk, weather.wind_mph, load_weight_lb)