
import logging

import requests

from .base import RoutingProvider, RouteOption, RouteStep
from ..exceptions import RoutingError, describe_request_error
from ...domain.geo import haversine_miles

logger = logging.getLogger(__name__)

METERS_PER_MILE = 1609.344

# ORS rejects alternative_routes once the *road* distance exceeds 100km (error
# code 2004), and it can take ~30s+ to compute that rejection. We only know
# straight-line (haversine) distance before calling ORS, and road distance is
# always >= straight-line distance, so we use a conservative threshold below
# the 100km-in-miles equivalent (~62.1mi) to pre-emptively skip doomed
# alternative_routes requests. Borderline trips (straight-line under the cap
# but an actual winding road route over it) may still hit ORS's slow
# rejection path; the retry-without-alternatives fallback below covers that.

ALTERNATIVE_ROUTES_DISTANCE_CAP_MILES = 55


class ORSRoutingProvider(RoutingProvider):
    """OpenRouteService directions adapter (driving-hgv profile).

    Known simplification: HGV restrictions (height/weight/hazmat) are not sent.
    Known limitation: alternative_routes is skipped pre-emptively for trips
    whose straight-line distance already implies the route will exceed ORS's
    100km cap for that feature (error 2004). See ALTERNATIVE_ROUTES_DISTANCE_CAP_MILES.
    The service layer always requests target_count=3; this adapter is
    responsible for degrading that request when ORS cannot fulfill it.
    """

    BASE_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv/geojson"

    def __init__(self, api_key: str, timeout: int = 40):
        self.api_key = api_key
        self.timeout = timeout

    def _post(self, body: dict) -> dict:
        response = requests.post(
            self.BASE_URL,
            json=body,
            headers={"Authorization": self.api_key, "Content-Type": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def get_route_options(self, origin, destination, target_count: int = 3) -> list[RouteOption]:
        (o_lat, o_lng), (d_lat, d_lng) = origin, destination

        # instructions=True is REQUIRED: without it ORS omits per-step data we need for ETAs.
        plain_body = {"coordinates": [[o_lng, o_lat], [d_lng, d_lat]], "instructions": True}

        wants_alternatives = target_count > 1
        straight_line_miles = haversine_miles(o_lat, o_lng, d_lat, d_lng)
        can_request_alternatives = (
            wants_alternatives and straight_line_miles < ALTERNATIVE_ROUTES_DISTANCE_CAP_MILES
        )

        if wants_alternatives and not can_request_alternatives:
            logger.info(
                "Skipping ORS alternative_routes: straight-line distance %.1fmi >= %.1fmi cap.",
                straight_line_miles,
                ALTERNATIVE_ROUTES_DISTANCE_CAP_MILES,
            )

        body = (
            {**plain_body, "alternative_routes": {"target_count": target_count, "share_factor": 0.6, "weight_factor": 1.4}}
            if can_request_alternatives
            else plain_body
        )

        try:
            try:
                data = self._post(body)
            except requests.HTTPError as exc:
                rejected = exc.response is not None and exc.response.status_code == 400
                if not (can_request_alternatives and rejected):
                    raise
                # Borderline case: straight-line distance was under the cap, but ORS
                # still rejected alternatives (e.g. winding road route exceeded the
                # limit). Degrade to the single best route; the service adds a
                # "fewer than 3 routes" warning.
                logger.warning(
                    "ORS rejected alternative_routes (%s); retrying for a single route.",
                    describe_request_error(exc),
                )
                data = self._post(plain_body)
        except requests.RequestException as exc:
            raise RoutingError(f"Routing request failed: {describe_request_error(exc)}") from None

        features = data.get("features", [])
        if not features:
            raise RoutingError("No route options returned by routing provider.")

        return [self._parse_feature(f) for f in features]

    @staticmethod
    def _parse_feature(feature: dict) -> RouteOption:
        properties = feature["properties"]
        summary = properties["summary"]
        distance_miles = summary["distance"] / METERS_PER_MILE
        duration_minutes = summary["duration"] / 60

        steps = [
            RouteStep(distance_miles=s["distance"] / METERS_PER_MILE, duration_minutes=s["duration"] / 60)
            for segment in properties.get("segments", [])
            for s in segment.get("steps", [])
        ]
        if not steps:
            # Fallback: assume uniform speed over the whole route.
            steps = [RouteStep(distance_miles=distance_miles, duration_minutes=duration_minutes)]

        return RouteOption(
            geometry=feature["geometry"],
            distance_miles=distance_miles,
            duration_minutes=duration_minutes,
            steps=steps,
        )