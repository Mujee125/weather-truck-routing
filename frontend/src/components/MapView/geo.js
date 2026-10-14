// GeoJSON coordinates are [lng, lat]; Leaflet wants [lat, lng].
export function toLatLng([lng, lat]) {
  return [lat, lng];
}
