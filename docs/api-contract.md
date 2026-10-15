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

Return HTTP `200` with the available route options, checkpoint assessments, recommendation, warnings, and heatmap data needed by the UI. The example below illustrates the response shape; values and IDs come from the actual analysis.

```json
{
  "recommended_route_id": "route-2",
  "routes": [
    {
      "id": "route-2",
      "geometry": {
        "type": "LineString",
        "coordinates": []
      },
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
    "reference_time": "2026-10-13T21:00:00+00:00",
    "available_forecast_hours": [0, 1, 2, 3],
    "data": [
      {
        "latitude": 32.8,
        "longitude": -96.8,
        "forecast": [
          {
            "hour_offset": 0,
            "wind_mph": 22,
            "rain_in_per_hour": 0,
            "snow_in_per_hour": 0,
            "risk_level": "low",
            "risk_score": 0
          }
        ]
      }
    ]
  },
  "warnings": []
}
```

Contract notes:

- `routes` contains up to three **actual** route alternatives returned by the routing provider; never fabricate a missing option. Include a top-level warning if fewer than three are available.
- The OpenRouteService adapter may return only one route for longer trips because ORS does not support alternative routes beyond its distance limit. This provider limitation is handled explicitly and reported through the existing fewer-than-three warning.
- `geometry` uses GeoJSON `LineString` coordinates in `[longitude, latitude]` order.
- Each checkpoint's `eta` is its estimated arrival time. Its weather assessment corresponds to that checkpoint location and ETA.
- `risk_level` is one of `low`, `moderate`, `high`, `severe`, `no_travel`, or `unknown`.
- If no weather sample can be matched to a checkpoint, `weather` may be `null`, `risk_level` is `unknown`, and the checkpoint and route include warnings. Missing weather is never treated as Low risk.
- `summary` values are calculated from checkpoint/segment results according to the policy documented in [`DECISIONS.md`](./DECISIONS.md).
- `heatmap.reference_time` is the backend's current UTC hour, floored to the beginning of the hour.
- `heatmap.available_forecast_hours` contains the contiguous hourly offsets available to the slider, normally `0` through `48` inclusive. The example above is abbreviated.
- Each `heatmap.data` entry represents one route-corridor coordinate and contains hourly forecast entries.
- A heatmap forecast entry contains raw weather values plus the server-calculated `risk_level` and `risk_score`. This lets the frontend render the heatmap without duplicating business rules.
- `risk_score` uses `low = 0`, `moderate = 1`, `high = 2`, `severe = 3`, and `no_travel = 4`. It may be `null` when risk is unknown.
- Heatmap corridor points reuse deduplicated checkpoint coordinates from the analyzed routes. No provider keys or secrets are exposed.
- `recommended_route_id` is `null` when no route can be recommended safely. A top-level warning explains why.

## 3. Route Ranking

Eligible routes are ranked using the assessment's ordered preferences:

1. Fewest Severe miles
2. Fewest High miles
3. Lowest average risk
4. Shortest travel time

A route containing at least one `no_travel` checkpoint is marked ineligible and excluded from recommendation ranking. Ineligible routes remain in the response so the UI can display and explain them.

If all returned routes are ineligible, the API returns:

```json
{
  "recommended_route_id": null
}
```

The complete response also includes a top-level warning explaining that no eligible route is available.

## 4. Errors

Use a consistent error envelope:

```json
{
  "error": {
    "code": "WEATHER_PROVIDER_UNAVAILABLE",
    "message": "Weather data is temporarily unavailable."
  }
}
```

Invalid input returns HTTP `400` with code `INVALID_REQUEST`. It may include an optional `details` object containing field-level validation errors:

```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "Request validation failed.",
    "details": {
      "checkpoint_interval_miles": [
        "Must be one of 10, 25, or 50."
      ]
    }
  }
}
```

Error handling:

- `400 Bad Request`: invalid input or a location that cannot be resolved.
- `502 Bad Gateway`: a routing, geocoding, or weather provider failure that prevents analysis.
- Provider and internal diagnostic details are logged on the backend and are not exposed to clients.
- If weather is unavailable for only some checkpoint locations, return the partial analysis with explicit warnings rather than failing the entire request or silently treating missing weather as safe.
- If weather is unavailable for all checkpoint locations, the analysis fails with a provider-unavailable error.

## 5. Assessment-Specific Decisions

The assessment does not define all boundary and failure behaviors. The implemented policies for threshold boundaries, combining weather conditions, load overrides, route-level risk miles, route eligibility, missing weather, heatmap timing, and routing-provider limitations are documented in [`DECISIONS.md`](./DECISIONS.md).