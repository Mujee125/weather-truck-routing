import { useState } from "react";

const INTERVALS = [10, 25, 50];
const pad = (n) => String(n).padStart(2, "0");


function defaultDeparture() {
  const d = new Date(Date.now() + 60 * 60 * 1000);
  d.setMinutes(0, 0, 0);
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}


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
 
    departure_time: new Date(values.departure).toISOString(),
    load_weight_lb: Number(values.loadWeight),
    checkpoint_interval_miles: Number(values.interval),
  };
}

function Field({ label, error, dot, children }) {
  return (
    <label className="field">
      <span className="field-label">
        {dot && (
          <span className={`field-dot field-dot--${dot}`} aria-hidden="true" />
        )}
        {label}
      </span>
      {children}
      {error && <span className="field-error">{error}</span>}
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
    <div className="trip-form">
     
      <form onSubmit={handleSubmit} noValidate className="trip-form-fields">
        <Field label="From" dot="green" error={errorFor("origin")}>
          <input
            placeholder="Starting location…"
            value={values.origin}
            onChange={update("origin")}
          />
        </Field>

        <Field label="To" dot="red" error={errorFor("destination")}>
          <input
            placeholder="Destination…"
            value={values.destination}
            onChange={update("destination")}
          />
        </Field>

        <Field
          label="Departure"
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

        <button type="submit" className="trip-form-submit" disabled={loading}>
          <span className="trip-form-submit-icon" aria-hidden="true">
          </span>
          {loading ? "Analyzing…" : "Check conditions"}
        </button>
      </form>
    </div>
  );
}
