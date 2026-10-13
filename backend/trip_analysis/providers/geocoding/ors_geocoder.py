import requests

from .base import GeocodingProvider
from ..exceptions import GeocodingError, LocationNotFoundError, describe_request_error


class ORSGeocoder(GeocodingProvider):
    """OpenRouteService geocoding adapter."""

    BASE_URL = "https://api.openrouteservice.org/geocode/search"

    def __init__(self, api_key: str, timeout: int = 10):
        self.api_key = api_key
        self.timeout = timeout

    def geocode(self, location_text: str) -> tuple[float, float]:
        try:
            response = requests.get(
                self.BASE_URL,
                params={"api_key": self.api_key, "text": location_text, "size": 1},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            # `from None`: the original exception's message contains the URL (and key).
            raise GeocodingError(f"Geocoding request failed: {describe_request_error(exc)}") from None

        features = data.get("features", [])
        if not features:
            raise LocationNotFoundError(f"No location found for '{location_text}'.")

        lng, lat = features[0]["geometry"]["coordinates"]
        return (lat, lng)