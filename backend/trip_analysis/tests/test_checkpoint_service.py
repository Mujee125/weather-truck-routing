from datetime import datetime, timezone

from trip_analysis.providers.routing.base import RouteOption, RouteStep
from trip_analysis.services.checkpoint_service import generate_checkpoints, _generate_markers


def test_generate_markers_even_interval():
    assert _generate_markers(100, 25) == [25, 50, 75, 100]


def test_generate_markers_uneven_total():
    assert _generate_markers(90, 25) == [25, 50, 75]


def test_generate_markers_shorter_than_interval():
    assert _generate_markers(8, 25) == [8]


def test_generate_checkpoints_eta_interpolation():
    route = RouteOption(
        geometry={"type": "LineString", "coordinates": [[-96.8, 32.8], [-96.5, 33.0], [-96.0, 33.5]]},
        distance_miles=100,
        duration_minutes=120,
        steps=[
            RouteStep(distance_miles=50, duration_minutes=60),
            RouteStep(distance_miles=50, duration_minutes=60),
        ],
    )
    departure = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

    checkpoints = generate_checkpoints(route, departure, interval_miles=25)

    assert len(checkpoints) == 4
    # checkpoint at mile 25 is halfway through the first 50-mile/60-min step -> +30 min
    assert checkpoints[0].eta == datetime(2026, 1, 1, 8, 30, tzinfo=timezone.utc)
    # checkpoint at mile 50 is exactly at the end of the first step -> +60 min
    assert checkpoints[1].eta == datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)
    # checkpoint at mile 100 is at the end of both steps -> +120 min
    assert checkpoints[3].eta == datetime(2026, 1, 1, 10, 0, tzinfo=timezone.utc)