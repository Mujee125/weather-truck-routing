import { useState } from "react";
import { RISK_COLORS } from "../MapView/riskColors";

const LABELS = {
  low: "Low",
  moderate: "Moderate",
  high: "High",
  severe: "Severe",
  no_travel: "No travel",
  unknown: "Unknown",
};

const DESCRIPTIONS = {
  low: "Safe conditions for normal operation.",
  moderate: "Minor caution advised.",
  high: "Significant risk — consider delaying.",
  severe: "Dangerous conditions for this load.",
  no_travel: "Travel not recommended at all.",
  unknown: "Weather data unavailable at this checkpoint.",
};

export default function Legend() {
  const [open, setOpen] = useState(false);

  return (
    <div className="legend">
      <button
        type="button"
        className="legend-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        Legend
        <span
          className={`legend-chevron ${open ? "legend-chevron--open" : ""}`}
        >
          ▾
        </span>
      </button>

      {open && (
        <div className="legend-panel">
          {Object.entries(RISK_COLORS).map(([key, color]) => (
            <div key={key} className="legend-row">
              <span
                className="legend-dot"
                style={{ background: color }}
                aria-hidden="true"
              />
              <div>
                <div className="legend-label">{LABELS[key]}</div>
                <div className="legend-desc">{DESCRIPTIONS[key]}</div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
