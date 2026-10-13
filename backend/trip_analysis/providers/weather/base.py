from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass
class HourlySample:
    timestamp: datetime  # UTC-aware
    wind_mph: float
    rain_in_per_hour: float
    snow_in_per_hour: float


class WeatherProvider(ABC):
    @abstractmethod
    def get_hourly_forecast(self, lat: float, lng: float, forecast_days: int) -> list[HourlySample]:
        """Returns hourly samples starting from the beginning of the current day (UTC)."""