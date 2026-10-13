import TripForm from "./components/TripForm/TripForm";
import DebugResults from "./components/DebugResults";
import { useTripAnalysis } from "./hooks/useTripAnalysis";

export default function App() {
  const { status, data, error, analyze } = useTripAnalysis();
  const loading = status === "loading";

  return (
    <main
      style={{
        maxWidth: 960,
        margin: "0 auto",
        padding: 24,
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <h1>Weather-Aware Truck Routing</h1>
      <TripForm
        onSubmit={analyze}
        loading={loading}
        serverErrors={error?.details}
      />

      {loading && <p>Analyzing routes and weather…</p>}
      {status === "error" && (
        <div
          role="alert"
          style={{ background: "#fdecea", padding: 12, borderRadius: 4 }}
        >
          <strong>{error.code}</strong>: {error.message}
        </div>
      )}
      {status === "success" && <DebugResults data={data} />}
    </main>
  );
}
