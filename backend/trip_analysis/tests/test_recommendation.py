import pytest
from trip_analysis.domain.types import Checkpoint, Route, RiskLevel
from trip_analysis.domain.recommendation import (
    compute_route_summary, is_route_eligible, rank_routes,
)


def make_checkpoint(distance, risk_level):
    return Checkpoint(
        distance_from_origin_miles=distance,
        latitude=0, longitude=0, eta="2026-01-01T00:00:00Z",
        weather=None, risk_level=risk_level,
    )


def test_compute_route_summary_basic():
    checkpoints = [
        make_checkpoint(25, RiskLevel.LOW),
        make_checkpoint(50, RiskLevel.HIGH),
        make_checkpoint(75, RiskLevel.SEVERE),
    ]
    summary = compute_route_summary(checkpoints, total_distance_miles=75)
    assert summary.high_miles == 25
    assert summary.severe_miles == 25
    # weighted: (0*25 + 2*25 + 3*25) / 75 = 125/75 = 1.667
    assert summary.average_risk_score == pytest.approx(1.667, abs=0.01)


def test_compute_route_summary_excludes_unknown():
    checkpoints = [
        make_checkpoint(25, RiskLevel.LOW),
        make_checkpoint(50, RiskLevel.UNKNOWN),
        make_checkpoint(75, RiskLevel.SEVERE),
    ]
    summary = compute_route_summary(checkpoints, total_distance_miles=75)
    # unknown segment (25mi) excluded from both miles and average denominator
    assert summary.severe_miles == 25
    known_distance = 25 + 25  # low segment + severe segment
    expected_avg = (0 * 25 + 3 * 25) / known_distance
    assert summary.average_risk_score == pytest.approx(expected_avg, abs=0.01)


def test_route_ineligible_if_any_no_travel_checkpoint():
    checkpoints = [
        make_checkpoint(25, RiskLevel.LOW),
        make_checkpoint(50, RiskLevel.NO_TRAVEL),
    ]
    assert is_route_eligible(checkpoints) is False


def test_route_eligible_without_no_travel():
    checkpoints = [make_checkpoint(25, RiskLevel.SEVERE)]
    assert is_route_eligible(checkpoints) is True


def make_route(id, severe_miles, high_miles, avg_risk, duration, eligible=True):
    from trip_analysis.domain.types import RouteSummary
    return Route(
        id=id, geometry={}, distance_miles=100, duration_minutes=duration,
        eligible=eligible,
        summary=RouteSummary(severe_miles=severe_miles, high_miles=high_miles, average_risk_score=avg_risk),
        checkpoints=[],
    )


def test_rank_routes_prefers_fewest_severe_miles():
    routes = [
        make_route("a", severe_miles=10, high_miles=0, avg_risk=1, duration=100),
        make_route("b", severe_miles=0, high_miles=5, avg_risk=2, duration=200),
    ]
    _, recommended = rank_routes(routes)
    assert recommended == "b"


def test_rank_routes_tiebreak_on_high_miles():
    routes = [
        make_route("a", severe_miles=0, high_miles=10, avg_risk=1, duration=100),
        make_route("b", severe_miles=0, high_miles=5, avg_risk=1, duration=200),
    ]
    _, recommended = rank_routes(routes)
    assert recommended == "b"


def test_rank_routes_tiebreak_on_avg_risk():
    routes = [
        make_route("a", severe_miles=0, high_miles=0, avg_risk=2, duration=100),
        make_route("b", severe_miles=0, high_miles=0, avg_risk=1, duration=200),
    ]
    _, recommended = rank_routes(routes)
    assert recommended == "b"


def test_rank_routes_tiebreak_on_duration():
    routes = [
        make_route("a", severe_miles=0, high_miles=0, avg_risk=1, duration=200),
        make_route("b", severe_miles=0, high_miles=0, avg_risk=1, duration=100),
    ]
    _, recommended = rank_routes(routes)
    assert recommended == "b"


def test_rank_routes_excludes_ineligible():
    routes = [
        make_route("a", severe_miles=0, high_miles=0, avg_risk=0, duration=50, eligible=False),
        make_route("b", severe_miles=5, high_miles=0, avg_risk=1, duration=200, eligible=True),
    ]
    _, recommended = rank_routes(routes)
    assert recommended == "b"


def test_rank_routes_all_ineligible_returns_none():
    routes = [
        make_route("a", severe_miles=0, high_miles=0, avg_risk=0, duration=50, eligible=False),
        make_route("b", severe_miles=0, high_miles=0, avg_risk=0, duration=60, eligible=False),
    ]
    _, recommended = rank_routes(routes)
    assert recommended is None