import { useState } from "react";

const INTERVALS = [10, 25, 50];
const pad = (n) => String(n).padStart(2, "0");

// <input type="datetime-local"> wants "YYYY-MM-DDTHH:mm" in LOCAL time.
function defaultDeparture() {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setMinutes(0, 0, 0);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

// Error keys use the API's field names so client and server errors render the same way.
function validate(values) {
  const errors = {};
  if (!values.origin.trim()) errors.origin = "Origin is required.";
  if (!values.destination.trim())
    errors.destination = "Destination is required.";
  if (!values.departure || Number.isNaN(new Date(values.departure).getTime())) {
    errors.departure_time = "Pick a valid departure date and time.";
  }
  const weight = Number(values.loadWeight);
  if (!values.loadWeight || !Number.isFinite(weight) || weight <= 0) {
    errors.load_weight_lb = "Enter a load weight greater than 0.";
  }
  return errors;
}

function toPayload(values) {
  return {
    origin: values.origin.trim(),
    destination: values.destination.trim(),
    // new Date(local).toISOString() converts local time to an unambiguous UTC instant.
    departure_time: new Date(values.departure).toISOString(),
    load_weight_lb: Number(values.loadWeight),
    checkpoint_interval_miles: Number(values.interval),
  };
}

function Field({ label, error, children }) {
  return (
    <label
      style={{ display: "flex", flexDirection: "column", gap: 4, fontSize: 14 }}
    >
      {label}
      {children}
      {error && <span style={{ color: "#b00020", fontSize: 12 }}>{error}</span>}
    </label>
  );
}

export default function TripForm({ onSubmit, loading, serverErrors }) {
  const [values, setValues] = useState({
    origin: "Dallas, TX",
    destination: "Houston, TX",
    departure: defaultDeparture(),
    loadWeight: "42000",
    interval: "25",
  });
  const [clientErrors, setClientErrors] = useState({});

  const update = (field) => (e) =>
    setValues((v) => ({ ...v, [field]: e.target.value }));
  const errorFor = (field) =>
    clientErrors[field] || [].concat(serverErrors?.[field] ?? []).join(" ");

  const handleSubmit = (e) => {
    e.preventDefault();
    const errors = validate(values);
    setClientErrors(errors);
    if (Object.keys(errors).length === 0) onSubmit(toPayload(values));
  };

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
        gap: 12,
        margin: "16px 0",
      }}
    >
      <Field label="Origin" error={errorFor("origin")}>
        <input value={values.origin} onChange={update("origin")} />
      </Field>
      <Field label="Destination" error={errorFor("destination")}>
        <input value={values.destination} onChange={update("destination")} />
      </Field>
      <Field
        label="Departure (your local time)"
        error={errorFor("departure_time")}
      >
        <input
          type="datetime-local"
          value={values.departure}
          onChange={update("departure")}
        />
      </Field>
      <Field label="Load weight (lb)" error={errorFor("load_weight_lb")}>
        <input
          type="number"
          min="1"
          value={values.loadWeight}
          onChange={update("loadWeight")}
        />
      </Field>
      <Field
        label="Checkpoint interval"
        error={errorFor("checkpoint_interval_miles")}
      >
        <select value={values.interval} onChange={update("interval")}>
          {INTERVALS.map((m) => (
            <option key={m} value={m}>
              {m} miles
            </option>
          ))}
        </select>
      </Field>
      <button
        type="submit"
        disabled={loading}
        style={{ alignSelf: "end", padding: "8px 16px" }}
      >
        {loading ? "Analyzing…" : "Analyze routes"}
      </button>
    </form>
  );
}
