import math

EARTH_RADIUS_MILES = 3958.8


def haversine_miles(lat1, lng1, lat2, lng2) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_MILES * math.asin(math.sqrt(a))


def point_at_distance(coordinates: list[list[float]], target_distance_miles: float) -> tuple[float, float]:
    """
    coordinates: GeoJSON-style [lng, lat] pairs forming the route polyline.
    Walks the polyline, returns (lat, lng) at target_distance_miles via linear
    interpolation between the two surrounding points. Returns the last point
    if target_distance_miles exceeds the polyline's total length.
    """
    if not coordinates:
        raise ValueError("coordinates cannot be empty")

    if len(coordinates) == 1:
        lng, lat = coordinates[0]
        return (lat, lng)

    accumulated = 0.0
    for i in range(len(coordinates) - 1):
        lng1, lat1 = coordinates[i]
        lng2, lat2 = coordinates[i + 1]
        segment_length = haversine_miles(lat1, lng1, lat2, lng2)

        if accumulated + segment_length >= target_distance_miles:
            remaining = target_distance_miles - accumulated
            fraction = (remaining / segment_length) if segment_length > 0 else 0
            lat = lat1 + (lat2 - lat1) * fraction
            lng = lng1 + (lng2 - lng1) * fraction
            return (lat, lng)

        accumulated += segment_length

    lng, lat = coordinates[-1]
    return (lat, lng)