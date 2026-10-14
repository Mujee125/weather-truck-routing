import { useEffect, useState } from "react";

export default function ForecastSlider({ hour, onHourChange, referenceTime }) {
  const [prevHour, setPrevHour] = useState(hour);
  const [local, setLocal] = useState(hour);

  
  if (hour !== prevHour) {
    setPrevHour(hour);
    setLocal(hour);
  }

 
  useEffect(() => {
    if (local === hour) return;
    const t = setTimeout(() => onHourChange(local), 120);
    return () => clearTimeout(t);

  }, [local]);

  let label = `+${local}h`;
  if (referenceTime) {
    try {
      const d = new Date(new Date(referenceTime).getTime() + local * 3600e3);
      label =
        d.toLocaleString(undefined, {
          weekday: "short",
          hour: "2-digit",
          minute: "2-digit",
        }) + ` (+${local}h)`;
    } catch {
      /* keep fallback */
    }
  }

  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 12,
        margin: "12px 0",
      }}
    >
      <span style={{ fontSize: 14, whiteSpace: "nowrap" }}>
        Forecast: <strong>{label}</strong>
      </span>
      <input
        type="range"
        min={0}
        max={48}
        step={1}
        value={local}
        onChange={(e) => setLocal(Number(e.target.value))}
        style={{ flex: 1 }}
        aria-label="Forecast hour (0-48)"
      />
      <span style={{ fontSize: 12, color: "var(--color-text-muted)" }}>
        0–48h
      </span>
    </div>
  );
}
