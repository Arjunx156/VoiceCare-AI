/**
 * Fine film-grain texture overlay for atmosphere. Decorative only
 * (aria-hidden), fixed to its positioned parent, never blocks pointer events.
 * See `.grain` in globals.css.
 */
export function GrainOverlay() {
  return <div aria-hidden="true" className="grain" />;
}
