export default function DebugResults({ data }) {
  // Keep the raw JSON readable: collapse big arrays to their length.
  const raw = JSON.stringify(
    data,
    (key, value) =>
      key === "coordinates"
        ? `[${value.length} points]`
        : key === "forecast"
          ? `[${value.length} hours]`
          : value,
    2,
  );

  return (
    <section>
      {data.warnings.length > 0 && (
        <ul style={{ background: "#fff8e1", padding: "8px 24px" }}>
          {data.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}

      <table
        border="1"
        cellPadding="6"
        style={{ borderCollapse: "collapse", width: "100%" }}
      >
        <thead>
          <tr>
            <th>Route</th>
            <th>Miles</th>
            <th>Minutes</th>
            <th>Eligible</th>
            <th>Severe mi</th>
            <th>High mi</th>
            <th>Avg risk</th>
            <th>Checkpoints</th>
            <th>Last ETA</th>
          </tr>
        </thead>
        <tbody>
          {data.routes.map((r) => (
            <tr key={r.id}>
              <td>
                {r.id === data.recommended_route_id ? "★ " : ""}
                {r.id}
              </td>
              <td>{r.distance_miles}</td>
              <td>{r.duration_minutes}</td>
              <td>{String(r.eligible)}</td>
              <td>{r.summary.severe_miles}</td>
              <td>{r.summary.high_miles}</td>
              <td>{r.summary.average_risk_score}</td>
              <td>{r.checkpoints.length}</td>
              <td>{r.checkpoints.at(-1)?.eta}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <details style={{ marginTop: 16 }}>
        <summary>Raw response (arrays collapsed)</summary>
        <pre style={{ overflow: "auto", maxHeight: 400 }}>{raw}</pre>
      </details>
    </section>
  );
}
