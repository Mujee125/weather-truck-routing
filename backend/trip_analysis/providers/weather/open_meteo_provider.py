import time
import requests
from datetime import datetime, timezone

from .base import WeatherProvider, HourlySample
from ..exceptions import WeatherError


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo adapter. No API key required.

    Retries on HTTP 429 (rate limit) with a short backoff, since concurrent
    checkpoint weather fetches can briefly exceed Open-Meteo's burst rate
    limit even well under its daily volume cap.
    """

    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    MAX_RETRIES = 2
    BACKOFF_SECONDS = 1.5

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def _get(self, params: dict) -> dict:
        last_exc = None
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = requests.get(self.BASE_URL, params=params, timeout=self.timeout)
                if response.status_code == 429 and attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_SECONDS * (attempt + 1))
                    continue
                response.raise_for_status()
                return response.json()
            except requests.RequestException as exc:
                last_exc = exc
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.BACKOFF_SECONDS * (attempt + 1))
                    continue
                raise WeatherError(f"Weather request failed: {exc}") from exc
        # Unreachable in practice, but satisfies static analysis.
        raise WeatherError(f"Weather request failed: {last_exc}")

    def get_hourly_forecast(self, lat: float, lng: float, forecast_days: int = 2) -> list[HourlySample]:
        forecast_days = max(1, min(forecast_days, 16))  # Open-Meteo's max supported range

        data = self._get({
            "latitude": lat,
            "longitude": lng,
            "hourly": "wind_speed_10m,rain,snowfall",
            "wind_speed_unit": "mph",
            "precipitation_unit": "inch",
            "forecast_days": forecast_days,
            "timezone": "UTC",
        })

        hourly = data.get("hourly")
        if not hourly:
            raise WeatherError("Weather provider returned no hourly data")

        samples = [
            HourlySample(
                timestamp=datetime.fromisoformat(t).replace(tzinfo=timezone.utc),
                wind_mph=w,
                rain_in_per_hour=r,
                snow_in_per_hour=s,
            )
            for t, w, r, s in zip(hourly["time"], hourly["wind_speed_10m"], hourly["rain"], hourly["snowfall"])
        ]
        return samples