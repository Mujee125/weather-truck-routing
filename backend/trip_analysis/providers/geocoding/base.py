from abc import ABC, abstractmethod


class GeocodingProvider(ABC):
    @abstractmethod
    def geocode(self, location_text: str) -> tuple[float, float]:
        """Returns (latitude, longitude). Raises GeocodingError on failure."""