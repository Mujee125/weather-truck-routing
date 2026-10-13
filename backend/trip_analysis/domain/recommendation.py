"""
Route-level aggregation and ranking.

Implements DECISIONS.md sections 3 and 4:
- Checkpoint risk -> segment miles -> severe_miles / high_miles / average_risk_score
- No Travel checkpoint -> route ineligible
- Ranking order: fewest severe miles, fewest high miles, lowest avg risk, shortest duration
"""

from .types import Checkpoint, Route, RouteSummary, RiskLevel, SEVERITY_ORDER


def compute_route_summary(checkpoints: list[Checkpoint], total_distance_miles: float) -> RouteSummary:
    """
    Each checkpoint represents the segment ENDING at it.
    Segment length = distance from the previous checkpoint (or origin for the first).
    UNKNOWN-risk checkpoints are excluded from mile totals and the average.
    """
    severe_miles = 0.0
    high_miles = 0.0
    weighted_sum = 0.0
    known_distance = 0.0

    previous_distance = 0.0
    for cp in checkpoints:
        segment_length = cp.distance_from_origin_miles - previous_distance
        previous_distance = cp.distance_from_origin_miles

        if cp.risk_level == RiskLevel.UNKNOWN:
            continue

        if cp.risk_level == RiskLevel.SEVERE:
            severe_miles += segment_length
        elif cp.risk_level == RiskLevel.HIGH:
            high_miles += segment_length

        weighted_sum += SEVERITY_ORDER[cp.risk_level] * segment_length
        known_distance += segment_length

    average_risk_score = (weighted_sum / known_distance) if known_distance > 0 else 0.0

    return RouteSummary(
        severe_miles=round(severe_miles, 2),
        high_miles=round(high_miles, 2),
        average_risk_score=round(average_risk_score, 3),
    )


def is_route_eligible(checkpoints: list[Checkpoint]) -> bool:
    """A route is ineligible if ANY checkpoint is NO_TRAVEL."""
    return not any(cp.risk_level == RiskLevel.NO_TRAVEL for cp in checkpoints)


def rank_routes(routes: list[Route]) -> tuple[list[Route], str | None]:
    """
    Returns (routes_sorted_by_preference, recommended_route_id_or_None).

    Ranking order (only among eligible routes):
      1. Fewest severe miles
      2. Fewest high miles
      3. Lowest average risk
      4. Shortest duration
    """
    eligible = [r for r in routes if r.eligible]

    if not eligible:
        return routes, None

    ranked = sorted(
        eligible,
        key=lambda r: (
            r.summary.severe_miles,
            r.summary.high_miles,
            r.summary.average_risk_score,
            r.duration_minutes,
        ),
    )

    return routes, ranked[0].id