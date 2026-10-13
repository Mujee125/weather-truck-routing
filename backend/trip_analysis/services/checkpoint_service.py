from dataclasses import dataclass
from datetime import datetime, timedelta

from trip_analysis.domain.geo import point_at_distance
from trip_analysis.providers.routing.base import RouteOption, RouteStep


@dataclass
class PlannedCheckpoint:
    distance_from_origin_miles: float
    latitude: float
    longitude: float
    eta: datetime


def _generate_markers(total_distance_miles: float, interval_miles: float) -> list[float]:
    """
    Markers at each interval up to total_distance_miles. If the route is shorter
    than one interval, a single checkpoint is placed at the destination so the
    trip still gets at least one risk assessment. (Documented decision.)
    """
    markers = []
    marker = interval_miles
    while marker <= total_distance_miles:
        markers.append(round(marker, 2))
        marker += interval_miles

    if not markers:
        markers.append(round(total_distance_miles, 2))

    return markers


def _elapsed_minutes_at_distance(steps: list[RouteStep], target_distance_miles: float) -> float:
    """Piecewise-linear interpolation of elapsed time using per-step distance/duration."""
    accumulated_distance = 0.0
    accumulated_time = 0.0
    for step in steps:
        if accumulated_distance + step.distance_miles >= target_distance_miles:
            remaining = target_distance_miles - accumulated_distance
            fraction = (remaining / step.distance_miles) if step.distance_miles > 0 else 0
            return accumulated_time + step.duration_minutes * fraction
        accumulated_distance += step.distance_miles
        accumulated_time += step.duration_minutes
    return accumulated_time  # target beyond total steps distance — return full duration


def generate_checkpoints(
    route: RouteOption,
    departure_time: datetime,
    interval_miles: float,
) -> list[PlannedCheckpoint]:
    markers = _generate_markers(route.distance_miles, interval_miles)
    coordinates = route.geometry["coordinates"]

    checkpoints = []
    for marker in markers:
        lat, lng = point_at_distance(coordinates, marker)
        elapsed_minutes = _elapsed_minutes_at_distance(route.steps, marker)
        eta = departure_time + timedelta(minutes=elapsed_minutes)
        checkpoints.append(PlannedCheckpoint(
            distance_from_origin_miles=marker,
            latitude=lat,
            longitude=lng,
            eta=eta,
        ))

    return checkpoints