import type { Swatch as SwatchType } from "../lib/api";

export function Swatch({ swatch }: { swatch: SwatchType }) {
  return (
    <div className="flex flex-col overflow-hidden rounded-lg border border-black/10 dark:border-white/15">
      <div className="h-24 w-full" style={{ backgroundColor: swatch.hex }} />
      <div className="flex flex-col gap-0.5 px-3 py-2 text-sm">
        <span className="font-mono font-medium uppercase">{swatch.hex}</span>
        <span className="text-xs text-black/60 dark:text-white/60">
          {(swatch.weight * 100).toFixed(1)}% of image
        </span>
      </div>
    </div>
  );
}
