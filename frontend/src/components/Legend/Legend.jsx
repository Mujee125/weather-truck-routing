import { RISK_COLORS } from "../MapView/riskColors";

const LABELS = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  severe: "Severe",
  no_travel: "No travel",
  unknown: "Unknown",
};

export default function Legend() {
  return (
    <div style={{ display: "flex", gap: 14, flexWrap: "wrap" }}>
      {Object.entries(RISK_COLORS).map(([key, color]) => (
        <span
          key={key}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            fontSize: 12,
            color: "var(--color-text-muted)",
          }}
        >
          <span
            style={{
              width: 10,
              height: 10,
              borderRadius: "50%",
              background: color,
              display: "inline-block",
            }}
          />
          {LABELS[key]}
        </span>
      ))}
    </div>
  );
}
