import { useState } from "react";
import TripForm from "./components/TripForm/TripForm";
import DebugResults from "./components/DebugResults";
import WarningsBanner from "./components/WarningsBanner/WarningsBanner";
import RouteSummaryCard from "./components/RouteSummaryCard/RouteSummaryCard";
import MapView from "./components/MapView/MapView";
import RouteLayer from "./components/MapView/RouteLayer";
import CheckpointMarkers from "./components/MapView/CheckpointMarkers";
import HeatmapLayer from "./components/MapView/HeatmapLayer";
import ForecastSlider from "./components/MapView/ForecastSlider";
import Legend from "./components/Legend/Legend";
import { useTripAnalysis } from "./hooks/useTripAnalysis";

export default function App() {
  const { status, data, error, analyze } = useTripAnalysis();
  const loading = status === "loading";
  const showAnalysis = status === "success";

  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [forecastHour, setForecastHour] = useState(0);

  const effectiveSelectedRouteId = showAnalysis
    ? (selectedRouteId ??
      data.recommended_route_id ??
      data.routes[0]?.id ??
      null)
    : null;

  const selectedRoute = showAnalysis
    ? data.routes.find((route) => route.id === effectiveSelectedRouteId)
    : null;

  const heatmap = showAnalysis ? (data.heatmap?.data ?? []) : [];
  const referenceTime = showAnalysis
    ? (data.heatmap?.reference_time ?? null)
    : null;

  return (
    <main
      className={`app-shell ${showAnalysis ? "app-shell--analysis" : "app-shell--landing"}`}
    >
      {/* Full-bleed map backdrop — always present, landing or analysis. */}
      <div className="map-backdrop">
        <MapView
          routes={showAnalysis ? data.routes : []}
          selectedRouteId={effectiveSelectedRouteId}
        >
          {showAnalysis && (
            <>
              <HeatmapLayer points={heatmap} selectedHour={forecastHour} />
              <RouteLayer
                routes={data.routes}
                recommendedRouteId={data.recommended_route_id}
                selectedRouteId={effectiveSelectedRouteId}
                onSelectRoute={setSelectedRouteId}
              />
              <CheckpointMarkers route={selectedRoute} />
            </>
          )}
        </MapView>
      </div>

      <header className="app-header">
        <p className="app-eyebrow">TRIP PLANNING · WEATHER INTELLIGENCE</p>
        <h1>Weather-Aware Truck Routing</h1>
      </header>

    
      {!showAnalysis && (
        <section className="panel trip-form-panel trip-form-panel--standalone">
          <TripForm
            onSubmit={analyze}
            loading={loading}
            serverErrors={error?.details}
          />
        </section>
      )}

      {loading && (
        <div className="map-loading-overlay" aria-live="polite">
          <span className="map-spinner" aria-hidden="true" />
          <span>Fetching route…</span>
        </div>
      )}

      {status === "error" && (
        <section
          className="panel error-panel error-panel--floating"
          role="alert"
        >
          <strong>{error.code}</strong>: {error.message}
        </section>
      )}

      {/* Analysis state: floating sidebar + floating map controls. */}
      {showAnalysis && (
        <>
          <aside className="analysis-sidebar">
            <section className="panel trip-form-panel">
              <div className="panel-heading">
                <div>
                  <p className="section-kicker">TRIP DETAILS</p>
                  <h2>Route analysis</h2>
                </div>
              </div>

              <TripForm
                onSubmit={analyze}
                loading={loading}
                serverErrors={error?.details}
              />
            </section>

            <WarningsBanner warnings={data.warnings} />

            <section className="panel route-options-panel">
              <div className="panel-heading">
                <div>
                  <p className="section-kicker">COMPARE OPTIONS</p>
                  <h2>Route options</h2>
                </div>
                <span className="route-count">
                  {data.routes.length}{" "}
                  {data.routes.length === 1 ? "route" : "routes"}
                </span>
              </div>

              <div className="route-card-list">
                {data.routes.map((route) => (
                  <RouteSummaryCard
                    key={route.id}
                    route={route}
                    isRecommended={route.id === data.recommended_route_id}
                    isSelected={route.id === effectiveSelectedRouteId}
                    onSelect={setSelectedRouteId}
                  />
                ))}
              </div>
            </section>
          </aside>

          <div className="map-panel-header">
            <Legend />
          </div>

          <div className="forecast-overlay">
            <ForecastSlider
              hour={forecastHour}
              onHourChange={setForecastHour}
              referenceTime={referenceTime}
            />
          </div>

          <details className="debug-details">
            <summary>Debug: raw response</summary>
            <DebugResults data={data} />
          </details>
        </>
      )}
    </main>
  );
}
