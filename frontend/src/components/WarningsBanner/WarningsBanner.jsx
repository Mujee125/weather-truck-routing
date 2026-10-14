export default function WarningsBanner({ warnings }) {
  if (!warnings?.length) return null;

  return (
    <div
      role="alert"
      style={{
        background: "#fff8e1",
        border: "1px solid #f0d777",
        borderRadius: "var(--radius)",
        padding: "12px 18px",
        margin: "0 0 20px",
      }}
    >
      <strong style={{ fontSize: 13, color: "var(--color-warning)" }}>
        Notices
      </strong>
      <ul
        style={{
          margin: "6px 0 0",
          paddingLeft: 20,
          fontSize: 13,
          color: "var(--color-text)",
        }}
      >
        {warnings.map((w) => (
          <li key={w}>{w}</li>
        ))}
      </ul>
    </div>
  );
}
