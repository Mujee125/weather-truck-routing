import React from "react";
import { Polyline } from "react-leaflet";
import { toLatLng } from "./geo";

const RECOMMENDED_COLOR = "#1a73e8";
const OTHER_COLOR = "#9aa0a6";
const SELECTED_COLOR = "#8430ce";
const INELIGIBLE_COLOR = "#d93025";

export default function RouteLayer({
  routes,
  recommendedRouteId,
  selectedRouteId,
  onSelectRoute,
}) {
  const ordered = [...routes].sort((a, b) => {
    const aTop = a.id === recommendedRouteId || a.id === selectedRouteId;
    const bTop = b.id === recommendedRouteId || b.id === selectedRouteId;
    return aTop === bTop ? 0 : aTop ? 1 : -1;
  });

  return ordered.map((route) => {
    const positions = route.geometry.coordinates.map(toLatLng);
    const isRecommended = route.id === recommendedRouteId;
    const isSelected = route.id === selectedRouteId;
    const color = !route.eligible
      ? INELIGIBLE_COLOR
      : isSelected && !isRecommended
        ? SELECTED_COLOR
        : isRecommended
          ? RECOMMENDED_COLOR
          : OTHER_COLOR;

    return (
      <React.Fragment key={route.id}>
        {/* Invisible wide line: makes the route much easier to click than the thin visible stroke. */}
        <Polyline
          positions={positions}
          pathOptions={{ color: "#000", weight: 20, opacity: 0 }}
          eventHandlers={{ click: () => onSelectRoute?.(route.id) }}
        />
        <Polyline
          positions={positions}
          pathOptions={{
            color,
            weight: isSelected || isRecommended ? 5 : 3,
            opacity: isSelected || isRecommended ? 0.9 : 0.6,
            dashArray: !route.eligible ? "6 6" : undefined,
          }}
          eventHandlers={{ click: () => onSelectRoute?.(route.id) }}
        />
      </React.Fragment>
    );
  });
}
