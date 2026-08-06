import type { Swatch as SwatchType } from "../lib/api";

export function Swatch({
  swatch,
  active,
  onSelect,
  onCopy,
  copied,
}: {
  swatch: SwatchType;
  active: boolean;
  onSelect: () => void;
  onCopy: () => void;
  copied: boolean;
}) {
  return (
    <article className={`swatch-card${active ? " is-active" : ""}`}>
      <button
        type="button"
        className="swatch-select"
        onClick={onSelect}
        aria-pressed={active}
        aria-label={`Focus cluster ${swatch.rank + 1}, ${swatch.hex}`}
      >
        <span className="swatch-color" style={{ backgroundColor: swatch.hex }} />
        <span className="swatch-index">C{String(swatch.rank + 1).padStart(2, "0")}</span>
        <span className="swatch-value">{swatch.hex}</span>
        <span className="swatch-weight">{(swatch.weight * 100).toFixed(1)}%</span>
      </button>
      <div className="swatch-meta">
        <span>
          L* {swatch.lab[0].toFixed(1)} · a* {swatch.lab[1].toFixed(1)} · b*{" "}
          {swatch.lab[2].toFixed(1)}
        </span>
        <button type="button" onClick={onCopy} aria-label={`Copy ${swatch.hex}`}>
          {copied ? "copied" : "copy"}
        </button>
      </div>
    </article>
  );
}
