import pytest
from trip_analysis.domain.types import RiskLevel, WeatherSample
from trip_analysis.domain.risk_rules import (
    classify_wind, classify_rain, classify_snow,
    classify_checkpoint_risk, apply_load_overrides,
)


# ---- Wind boundaries ----
@pytest.mark.parametrize("wind,expected", [
    (0, RiskLevel.LOW),
    (24.9, RiskLevel.LOW),
    (25, RiskLevel.MODERATE),
    (34.9, RiskLevel.MODERATE),
    (35, RiskLevel.HIGH),
    (44.9, RiskLevel.HIGH),
    (45, RiskLevel.SEVERE),
    (54.9, RiskLevel.SEVERE),
    (55, RiskLevel.NO_TRAVEL),
    (100, RiskLevel.NO_TRAVEL),
])
def test_classify_wind(wind, expected):
    assert classify_wind(wind) == expected


# ---- Rain boundaries ----
@pytest.mark.parametrize("rain,expected", [
    (0, RiskLevel.LOW),
    (0.09, RiskLevel.LOW),
    (0.10, RiskLevel.MODERATE),
    (0.24, RiskLevel.MODERATE),
    (0.25, RiskLevel.HIGH),
    (0.49, RiskLevel.HIGH),
    (0.50, RiskLevel.SEVERE),
    (1.00, RiskLevel.SEVERE),
    (1.01, RiskLevel.NO_TRAVEL),
])
def test_classify_rain(rain, expected):
    assert classify_rain(rain) == expected


# ---- Snow boundaries ----
@pytest.mark.parametrize("snow,expected", [
    (0, RiskLevel.LOW),
    (0.49, RiskLevel.LOW),
    (0.5, RiskLevel.MODERATE),
    (0.99, RiskLevel.MODERATE),
    (1.0, RiskLevel.HIGH),
    (1.99, RiskLevel.HIGH),
    (2.0, RiskLevel.SEVERE),
    (3.0, RiskLevel.SEVERE),
    (3.01, RiskLevel.NO_TRAVEL),
])
def test_classify_snow(snow, expected):
    assert classify_snow(snow) == expected


# ---- Load override rules ----
def test_load_override_wind_55_always_no_travel():
    assert apply_load_overrides(RiskLevel.LOW, wind_mph=55, load_weight_lb=1000) == RiskLevel.NO_TRAVEL


def test_load_override_45_54_heavy_load_no_travel():
    assert apply_load_overrides(RiskLevel.MODERATE, wind_mph=50, load_weight_lb=35000) == RiskLevel.NO_TRAVEL


def test_load_override_45_54_light_load_not_escalated():
    # base risk preserved when load is not over the threshold
    assert apply_load_overrides(RiskLevel.SEVERE, wind_mph=50, load_weight_lb=20000) == RiskLevel.SEVERE


def test_load_override_35_44_heavy_load_becomes_severe():
    assert apply_load_overrides(RiskLevel.MODERATE, wind_mph=40, load_weight_lb=45000) == RiskLevel.SEVERE


def test_load_override_35_44_heavy_load_does_not_downgrade_higher_base():
    # if base was already NO_TRAVEL (e.g. from rain), stays NO_TRAVEL
    assert apply_load_overrides(RiskLevel.NO_TRAVEL, wind_mph=40, load_weight_lb=45000) == RiskLevel.NO_TRAVEL


def test_load_override_35_44_light_load_not_escalated():
    assert apply_load_overrides(RiskLevel.LOW, wind_mph=40, load_weight_lb=30000) == RiskLevel.LOW


# ---- Full checkpoint classification ----
def test_checkpoint_combines_max_severity():
    weather = WeatherSample(wind_mph=10, rain_in_per_hour=0.30, snow_in_per_hour=0)
    # wind=low, rain=high, snow=low -> max = high
    assert classify_checkpoint_risk(weather, load_weight_lb=20000) == RiskLevel.HIGH


def test_checkpoint_missing_weather_is_unknown():
    weather = WeatherSample(wind_mph=None, rain_in_per_hour=0.1, snow_in_per_hour=0)
    assert classify_checkpoint_risk(weather, load_weight_lb=20000) == RiskLevel.UNKNOWN


def test_checkpoint_none_weather_is_unknown():
    assert classify_checkpoint_risk(None, load_weight_lb=20000) == RiskLevel.UNKNOWN


def test_checkpoint_heavy_load_escalates_moderate_wind_rain():
    weather = WeatherSample(wind_mph=40, rain_in_per_hour=0, snow_in_per_hour=0)
    # base = high (wind 35-44), load override (35-44 + >40000lb) -> severe
    assert classify_checkpoint_risk(weather, load_weight_lb=42000) == RiskLevel.SEVERE