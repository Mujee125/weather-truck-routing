# views.py
from rest_framework.response import Response
from rest_framework.views import APIView

from trip_analysis.composition import build_default_service
from trip_analysis.services.trip_analysis_service import TripAnalysisError, TripRequest

from .exceptions import ApiError
from .serializers import AnalyzeRequestSerializer, serialize_analysis

ERROR_STATUS = {
    "LOCATION_NOT_FOUND": 400,
    "GEOCODING_PROVIDER_UNAVAILABLE": 502,
    "ROUTING_PROVIDER_UNAVAILABLE": 502,
    "WEATHER_PROVIDER_UNAVAILABLE": 502,
}


class AnalyzeRoutesView(APIView):
    authentication_classes = []   # no auth required by the brief
    permission_classes = []

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        if not serializer.is_valid():
            # Rejected BEFORE any provider is constructed or called.
            raise ApiError("INVALID_REQUEST", "Request validation failed.", 400, details=serializer.errors)

        data = serializer.validated_data
        trip = TripRequest(
            origin=data["origin"].strip(),
            destination=data["destination"].strip(),
            departure_time=data["departure_time"],
            load_weight_lb=data["load_weight_lb"],
            checkpoint_interval_miles=data["checkpoint_interval_miles"],
        )

        try:
            result = build_default_service().analyze(trip)
        except TripAnalysisError as exc:
            raise ApiError(exc.code, exc.message, ERROR_STATUS.get(exc.code, 502)) from None

        return Response(serialize_analysis(result))