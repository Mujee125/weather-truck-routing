import requests
from datetime import datetime, timezone

from .base import WeatherProvider, HourlySample
from ..exceptions import WeatherError


class OpenMeteoProvider(WeatherProvider):
    """Open-Meteo adapter. No API key required."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def get_hourly_forecast(self, lat: float, lng: float, forecast_days: int = 2) -> list[HourlySample]:
        forecast_days = max(1, min(forecast_days, 16))  # Open-Meteo's max supported range

        try:
            response = requests.get(
                self.BASE_URL,
                params={
                    "latitude": lat,
                    "longitude": lng,
                    "hourly": "wind_speed_10m,rain,snowfall",
                    "wind_speed_unit": "mph",
                    "precipitation_unit": "inch",
                    "forecast_days": forecast_days,
                    "timezone": "UTC",
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise WeatherError(f"Weather request failed: {exc}") from exc

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