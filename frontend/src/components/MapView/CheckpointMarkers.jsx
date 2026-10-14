import { CircleMarker, Popup } from "react-leaflet";

import { RISK_COLORS } from "./riskColors";

function formatEta(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      weekday: "short",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function CheckpointMarkers({ route }) {
  if (!route) return null;

  return route.checkpoints.map((cp, i) => (
    <CircleMarker
      key={i}
      center={[cp.latitude, cp.longitude]}
      radius={7}
      pathOptions={{
        color: "#222",
        weight: 1,
        fillColor: RISK_COLORS[cp.risk_level] ?? RISK_COLORS.unknown,
        fillOpacity: 0.9,
      }}
    >
      <Popup>
        <div style={{ fontSize: 13 }}>
          <strong>{Math.round(cp.distance_from_origin_miles)} mi</strong> —{" "}
          {cp.risk_level}
          <br />
          ETA: {formatEta(cp.eta)}
          <br />
          {cp.weather ? (
            <>
              Wind: {cp.weather.wind_mph} mph
              <br />
              Rain: {cp.weather.rain_in_per_hour} in/hr
              <br />
              Snow: {cp.weather.snow_in_per_hour} in/hr
            </>
          ) : (
            <em>Weather unavailable</em>
          )}
          {cp.warnings?.length > 0 && (
            <div style={{ color: "#b00020", marginTop: 4 }}>
              {cp.warnings.join(" ")}
            </div>
          )}
        </div>
      </Popup>
    </CircleMarker>
  ));
}
