/**
 * Ambient aurora backdrop — four slowly drifting, heavily-blurred coral blobs
 * on the dark canvas. Adapted from a 21st.dev concept and rethemed to our
 * tokens (no Tailwind, no extra deps). Decorative only: aria-hidden, never
 * intercepts pointer events, and freezes under prefers-reduced-motion (via the
 * global reduced-motion override in globals.css). See `.aurora` there.
 */
export function AuroraBackdrop() {
  return (
    <div className="aurora" aria-hidden="true">
      <span className="aurora-blob b1" />
      <span className="aurora-blob b2" />
      <span className="aurora-blob b3" />
      <span className="aurora-blob b4" />
    </div>
  );
}
