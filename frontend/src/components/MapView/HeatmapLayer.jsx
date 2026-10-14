import { CircleMarker, Tooltip } from "react-leaflet";
import { RISK_COLORS } from "./riskColors";

export default function HeatmapLayer({ points, selectedHour }) {
  if (!points?.length) return null;

  return points.map((p, i) => {
    const lat = p.latitude ?? p.lat;
    const lng = p.longitude ?? p.lng;
    if (lat == null || lng == null) return null;

    const entry = p.forecast?.find((f) => f.hour_offset === selectedHour);
    const level = entry?.risk_level ?? "unknown";

    return (
      <CircleMarker
        key={i}
        center={[lat, lng]}
        radius={22}
        pathOptions={{
          stroke: true,
          color: RISK_COLORS[level] ?? RISK_COLORS.unknown,
          weight: 1,
          fillColor: RISK_COLORS[level] ?? RISK_COLORS.unknown,
          fillOpacity: 0.45,
        }}
      >
        <Tooltip>
          +{selectedHour}h — {level}
          {entry && (
            <>
              <br />
              Wind {entry.wind_mph} mph / Rain {entry.rain_in_per_hour} / Snow{" "}
              {entry.snow_in_per_hour}
            </>
          )}
        </Tooltip>
      </CircleMarker>
    );
  });
}
