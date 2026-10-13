# Weather-Aware Truck Routing — API Contract

**Scope:** Minimal React–Django contract for the Spotter.ai assessment. No database or authentication is required by the brief.

## 1. Analyze Routes

`POST /api/routes/analyze`

Request (`application/json`):

```json
{
  "origin": "Dallas, TX",
  "destination": "Houston, TX",
  "departure_time": "2026-10-14T08:00:00-05:00",
  "load_weight_lb": 42000,
  "checkpoint_interval_miles": 25
}
```

Rules:
- `origin`, `destination`: non-empty location text.
- `departure_time`: ISO 8601 date-time with timezone.
- `load_weight_lb`: positive number, in pounds.
- `checkpoint_interval_miles`: one of `10`, `25`, or `50`.
- Reject invalid input with HTTP `400`; do not call external providers for invalid requests.

## 2. Successful Response

Return HTTP `200` with the available route options, checkpoint assessments, recommendation, warnings, and heatmap data needed by the UI. The example below illustrates the shape only; values and IDs must come from actual analysis.

```json
{
  "recommended_route_id": "route-2",
  "routes": [
    {
      "id": "route-2",
      "geometry": { "type": "LineString", "coordinates": [] },
      "distance_miles": 240,
      "duration_minutes": 230,
      "eligible": true,
      "summary": {
        "severe_miles": 0,
        "high_miles": 12,
        "average_risk_score": 1.4
      },
      "checkpoints": [
        {
          "distance_from_origin_miles": 25,
          "latitude": 32.8,
          "longitude": -96.8,
          "eta": "2026-10-14T08:25:00-05:00",
          "weather": {
            "wind_mph": 22,
            "rain_in_per_hour": 0,
            "snow_in_per_hour": 0
          },
          "risk_level": "low",
          "warnings": []
        }
      ],
      "warnings": []
    }
  ],
  "heatmap": {
    "reference_time": "2026-10-13T21:00:00-05:00",
    "available_forecast_hours": [0, 1, 2, 3, 48],
    "data": []
  },
  "warnings": []
}
```

Contract notes:
- `routes` contains up to three **actual** route alternatives returned by the provider; never fabricate a missing option. Include a warning if fewer than three are available.
- `geometry` uses GeoJSON `LineString` coordinates in `[longitude, latitude]` order.
- Each checkpoint's `eta` is its estimated arrival time; weather should correspond to that location and time.
- `risk_level` is one of `low`, `moderate`, `high`, `severe`, or `no_travel`. Use an explicit unknown/missing-data representation rather than assigning Low risk when weather is unavailable.
- `summary` values must be calculated from checkpoint/segment results. Document how checkpoint risk is converted into risk miles and average risk.
- `heatmap.data` is provider-neutral data for the route-corridor weather layer. Its exact shape depends on the selected map/weather provider; it must support the required 0–48-hour forecast slider. Do not expose private provider keys.
- `recommended_route_id` is `null` when no route can be recommended safely or validly; explain why in `warnings`.

## 3. Route Ranking

Rank routes by the assessment's ordered preferences:

1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel time

**Proposed policy to document:** mark a route containing a `no_travel` checkpoint as ineligible. If all routes are ineligible, return `recommended_route_id: null`. The assessment brief does not explicitly define this behavior.

## 4. Errors

Use a consistent error shape:

```json
{
  "error": {
    "code": "WEATHER_PROVIDER_UNAVAILABLE",
    "message": "Weather data is temporarily unavailable."
  }
}
```

Suggested handling:
- `400 Bad Request`: invalid input.
- `502 Bad Gateway`: routing, geocoding, or weather provider failure that prevents analysis.
- `503 Service Unavailable`: required service temporarily unavailable, if that distinction is useful in implementation.

If some checkpoint weather is missing but a partial analysis can still be returned, include an explicit checkpoint warning and do not silently treat it as safe. Keep error messages user-safe; log provider details on the backend without returning secrets.

## 5. Assessment-Specific Decisions

The brief does not resolve overlapping rain/snow boundaries, combining multiple weather risks, risk-mile calculation, or the heatmap's reference time. Define these consistently in the risk engine and README. Keep this contract small; add endpoints only if the implementation genuinely needs them.
