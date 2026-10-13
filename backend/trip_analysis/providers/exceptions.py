class ProviderError(Exception):
    """Base class for third-party provider failures."""


class GeocodingError(ProviderError):
    pass


class LocationNotFoundError(GeocodingError):
    """The geocoder worked but found nothing (a user-input problem, not an outage)."""


class RoutingError(ProviderError):
    pass


class WeatherError(ProviderError):
    pass


def describe_request_error(exc: Exception) -> str:
    """Log-safe description of a `requests` failure.

    Never includes the request URL, which can contain API keys in the query string.
    """
    response = getattr(exc, "response", None)
    if response is not None:
        return f"{type(exc).__name__} (HTTP {response.status_code}): {response.text[:200]}"
    return type(exc).__name__