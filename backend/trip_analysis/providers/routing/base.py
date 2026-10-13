from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class RouteStep:
    distance_miles: float
    duration_minutes: float


@dataclass
class RouteOption:
    geometry: dict          # GeoJSON LineString: {"type": "LineString", "coordinates": [[lng, lat], ...]}
    distance_miles: float
    duration_minutes: float
    steps: list[RouteStep]  # ordered, used for ETA interpolation


class RoutingProvider(ABC):
    @abstractmethod
    def get_route_options(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        target_count: int = 3,
    ) -> list[RouteOption]:
        """origin/destination are (lat, lng). Returns up to target_count alternatives.
        Never fabricates routes — may return fewer than target_count."""