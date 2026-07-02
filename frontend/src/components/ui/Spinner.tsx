type Props = {
  size?: number;
  label?: string;
};

/** Single loading indicator — uses the .spinner class from globals.css. */
export function Spinner({ size = 24, label = "Loading" }: Props) {
  return (
    <span role="status" style={{ display: "inline-flex" }}>
      <span
        className="spinner"
        style={{ width: size, height: size }}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </span>
  );
}

/** Centered spinner for panel/page loading states. */
export function LoadingBlock({ label = "Loading" }: { label?: string }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "64px 0",
      }}
    >
      <Spinner label={label} />
    </div>
  );
}
