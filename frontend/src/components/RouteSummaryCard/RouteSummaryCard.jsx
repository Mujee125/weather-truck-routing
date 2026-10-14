function formatMinutes(min) {
  const h = Math.floor(min / 60);
  const m = Math.round(min % 60);
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}

export default function RouteSummaryCard({
  route,
  isRecommended,
  isSelected,
  onSelect,
}) {
  const { summary } = route;

  return (
    <button
      type="button"
      onClick={() => onSelect(route.id)}
      style={{
        display: "block",
        textAlign: "left",
        width: "100%",
        cursor: "pointer",
        border: isSelected
          ? "2px solid var(--color-accent)"
          : "1px solid var(--color-border)",
        borderRadius: "var(--radius)",
        padding: 14,
        margin: "0 0 10px",
        background: !route.eligible
          ? "#fdecea"
          : isRecommended
            ? "var(--color-accent-soft)"
            : "var(--color-surface)",
      }}
    >
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          gap: 12,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <strong style={{ color: "var(--color-text)", fontSize: 15 }}>
            {route.id}
          </strong>
          {isRecommended && (
            <span
              style={{
                background: "var(--color-accent)",
                color: "#fff",
                fontSize: 11,
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: 999,
              }}
            >
              ★ Recommended
            </span>
          )}
          {!route.eligible && (
            <span
              style={{
                background: "var(--color-danger)",
                color: "#fff",
                fontSize: 11,
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: 999,
              }}
            >
              Not eligible
            </span>
          )}
        </div>
        <span
          style={{
            fontSize: 13,
            color: "var(--color-text-muted)",
            whiteSpace: "nowrap",
          }}
        >
          {route.distance_miles.toFixed(1)} mi ·{" "}
          {formatMinutes(route.duration_minutes)}
        </span>
      </div>

      <div
        style={{
          display: "flex",
          gap: 18,
          marginTop: 10,
          fontSize: 13,
          color: "var(--color-text)",
        }}
      >
        <span>Severe mi: {summary.severe_miles.toFixed(1)}</span>
        <span>High mi: {summary.high_miles.toFixed(1)}</span>
        <span>Avg risk: {summary.average_risk_score.toFixed(2)}</span>
        <span>Checkpoints: {route.checkpoints.length}</span>
      </div>

      {route.warnings?.length > 0 && (
        <div
          style={{ marginTop: 8, fontSize: 12, color: "var(--color-warning)" }}
        >
          {route.warnings.join(" ")}
        </div>
      )}
    </button>
  );
}
