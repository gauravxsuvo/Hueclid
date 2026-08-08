"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import type { Swatch as SwatchType } from "../lib/api";
import { EASE } from "./motion";

export function Swatch({ swatch }: { swatch: SwatchType }) {
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(swatch.hex);
      setCopied(true);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(false), 1400);
    } catch {
      // clipboard is blocked on insecure origins and in some
      // browsers without a user gesture, the swatch is still useful
    }
  }

  const percent = swatch.weight * 100;

  return (
    <button
      type="button"
      onClick={copy}
      aria-label={`Copy ${swatch.hex}`}
      className="group flex w-full flex-col overflow-hidden rounded-xl border border-line bg-surface text-left transition-transform duration-[350ms] ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-1"
    >
      <div className="relative h-32 w-full overflow-hidden sm:h-36">
        <div
          className="absolute inset-0 transition-transform duration-[550ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-105"
          style={{ backgroundColor: swatch.hex }}
        />
        <AnimatePresence>
          {copied && (
            <motion.span
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25, ease: EASE }}
              className="absolute inset-0 flex items-center justify-center bg-foreground/85 font-mono text-xs tracking-widest text-background uppercase"
            >
              Copied
            </motion.span>
          )}
        </AnimatePresence>
      </div>

      <div className="flex flex-col gap-2 px-3.5 py-3">
        <div className="flex items-baseline justify-between gap-2">
          <span className="font-mono text-sm font-medium uppercase">{swatch.hex}</span>
          {/* ranks come off the API zero indexed, a swatch labelled
              "00" reads like a bug to anyone who is not reading the
              array, so the label is the human ordinal */}
          <span className="font-mono text-[11px] text-faint">
            {String(swatch.rank + 1).padStart(2, "0")}
          </span>
        </div>

        <div aria-hidden className="h-[3px] w-full overflow-hidden rounded-full bg-line">
          <motion.div
            className="h-full rounded-full"
            style={{ backgroundColor: swatch.hex }}
            initial={{ width: 0 }}
            animate={{ width: `${percent}%` }}
            transition={{ duration: 0.9, ease: EASE, delay: 0.2 }}
          />
        </div>

        <span className="text-xs text-muted">{percent.toFixed(1)}% of the image</span>
      </div>
    </button>
  );
}
