from django.conf import settings

from trip_analysis.providers.geocoding.ors_geocoder import ORSGeocoder
from trip_analysis.providers.routing.ors_provider import ORSRoutingProvider
from trip_analysis.providers.weather.open_meteo_provider import OpenMeteoProvider
from trip_analysis.services.trip_analysis_service import TripAnalysisService


def build_default_service() -> TripAnalysisService:
    if not settings.ORS_API_KEY:
        raise RuntimeError("ORS_API_KEY is not configured.")
    return TripAnalysisService(
        geocoder=ORSGeocoder(settings.ORS_API_KEY),
        router=ORSRoutingProvider(settings.ORS_API_KEY),
        weather=OpenMeteoProvider(),
    )