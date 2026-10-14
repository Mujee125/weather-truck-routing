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

const panel = {
  background: "var(--color-surface)",
  border: "1px solid var(--color-border)",
  borderRadius: "var(--radius)",
  boxShadow: "var(--shadow)",
  padding: 20,
  marginBottom: 20,
};

export default function App() {
  const { status, data, error, analyze } = useTripAnalysis();
  const loading = status === "loading";

  const [selectedRouteId, setSelectedRouteId] = useState(null);
  const [forecastHour, setForecastHour] = useState(0);

  const effectiveSelectedRouteId =
    status === "success"
      ? (selectedRouteId ??
        data.recommended_route_id ??
        data.routes[0]?.id ??
        null)
      : null;

  return (
    <main
      style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 24px 64px" }}
    >
      <header style={{ marginBottom: 28 }}>
        <h1 style={{ margin: 0, fontSize: 30, fontWeight: 700 }}>
          Weather-Aware Truck Routing
        </h1>
        <p
          style={{
            margin: "6px 0 0",
            color: "var(--color-text-muted)",
            fontSize: 15,
          }}
        >
          Compare route options by weather risk along the way, and get a
          recommended route balancing safety and travel time.
        </p>
      </header>

      <section style={panel}>
        <TripForm
          onSubmit={analyze}
          loading={loading}
          serverErrors={error?.details}
        />
      </section>

      {loading && (
        <section
          style={{
            ...panel,
            textAlign: "center",
            color: "var(--color-text-muted)",
          }}
        >
          Analyzing routes and weather along the way…
        </section>
      )}

      {status === "error" && (
        <section
          role="alert"
          style={{
            ...panel,
            background: "#fdecea",
            borderColor: "#f3c4c0",
            color: "var(--color-danger)",
          }}
        >
          <strong>{error.code}</strong>: {error.message}
        </section>
      )}

      {status === "success" &&
        (() => {
          const heatmap = data.heatmap?.data ?? [];
          const referenceTime = data.heatmap?.reference_time ?? null;
          const selectedRoute = data.routes.find(
            (r) => r.id === effectiveSelectedRouteId,
          );

          return (
            <>
              <WarningsBanner warnings={data.warnings} />

              <section style={panel}>
                <h2 style={{ margin: "0 0 12px", fontSize: 18 }}>
                  Route options
                </h2>
                {data.routes.map((route) => (
                  <RouteSummaryCard
                    key={route.id}
                    route={route}
                    isRecommended={route.id === data.recommended_route_id}
                    isSelected={route.id === effectiveSelectedRouteId}
                    onSelect={setSelectedRouteId}
                  />
                ))}
              </section>

              <section style={panel}>
                <div
                  style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    marginBottom: 12,
                  }}
                >
                  <h2 style={{ margin: 0, fontSize: 18 }}>
                    Weather forecast map
                  </h2>
                  <Legend />
                </div>
                <p
                  style={{
                    margin: "0 0 12px",
                    fontSize: 13,
                    color: "var(--color-text-muted)",
                  }}
                >
                  Solid lines are routes (click to compare). Translucent circles
                  are the weather heatmap, sampled at each checkpoint along the
                  corridor — drag the slider to see how risk changes over the
                  next 48 hours.
                </p>
                <ForecastSlider
                  hour={forecastHour}
                  onHourChange={setForecastHour}
                  referenceTime={referenceTime}
                />
                <div
                  style={{
                    borderRadius: "var(--radius)",
                    overflow: "hidden",
                    border: "1px solid var(--color-border)",
                  }}
                >
                  <MapView routes={data.routes}>
                    <HeatmapLayer
                      points={heatmap}
                      selectedHour={forecastHour}
                    />
                    <RouteLayer
                      routes={data.routes}
                      recommendedRouteId={data.recommended_route_id}
                      selectedRouteId={effectiveSelectedRouteId}
                      onSelectRoute={setSelectedRouteId}
                    />
                    <CheckpointMarkers route={selectedRoute} />
                  </MapView>
                </div>
              </section>

              <details
                style={{ fontSize: 13, color: "var(--color-text-muted)" }}
              >
                <summary style={{ cursor: "pointer" }}>
                  Debug: raw response
                </summary>
                <DebugResults data={data} />
              </details>
            </>
          );
        })()}
    </main>
  );
}
