import { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
import L from "leaflet";
import { toLatLng } from "./geo";

function ResizeFix() {
  const map = useMap();

  useEffect(() => {
    const container = map.getContainer();
    const timers = [100, 300, 700].map((ms) =>
      setTimeout(() => map.invalidateSize(), ms),
    );

    const observer = new ResizeObserver(() => map.invalidateSize());
    observer.observe(container);

    return () => {
      timers.forEach(clearTimeout);
      observer.disconnect();
    };
  }, [map]);

  return null;
}

function FitBounds({ routes, selectedRouteId }) {
  const map = useMap();

  useEffect(() => {
    if (!routes || routes.length === 0) return;


    const target = selectedRouteId
      ? routes.find((route) => route.id === selectedRouteId)
      : null;

    const routesToFit = target ? [target] : routes;

    const points = routesToFit.flatMap((route) =>
      (route.geometry?.coordinates ?? []).map(toLatLng),
    );

    if (points.length === 0) return;

    const bounds = L.latLngBounds(points);
    map.fitBounds(bounds, { padding: [64, 64], maxZoom: 12 });
  }, [map, routes, selectedRouteId]);

  return null;
}


const DEFAULT_CENTER = [39.5, -98.35];

export default function MapView({ routes = [], selectedRouteId, children }) {
  const hasRoutes = routes.length > 0;
  const firstPoint = routes[0]?.geometry?.coordinates?.[0];
  const center = firstPoint ? toLatLng(firstPoint) : DEFAULT_CENTER;

  return (
    <MapContainer
      center={center}
      zoom={hasRoutes ? 7 : 4}
      style={{ height: "100%", width: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <ResizeFix />
      {hasRoutes && (
        <FitBounds routes={routes} selectedRouteId={selectedRouteId} />
      )}
      {children}
    </MapContainer>
  );
}
