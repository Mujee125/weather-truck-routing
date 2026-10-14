import { useEffect } from "react";
import { MapContainer, TileLayer, useMap } from "react-leaflet";
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

export default function MapView({ routes, children }) {
  const firstRoute = routes?.[0];
  const firstPoint = firstRoute?.geometry?.coordinates?.[0];
  const center = firstPoint ? toLatLng(firstPoint) : [32.7767, -96.797];

  return (
    <MapContainer
      center={center}
      zoom={7}
      style={{ height: 500, width: "100%" }}
    >
      <TileLayer
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
      />
      <ResizeFix />
      {children}
    </MapContainer>
  );
}
