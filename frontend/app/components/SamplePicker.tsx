"use client";

import { motion, useReducedMotion } from "framer-motion";
import { EASE } from "./motion";

export type Sample = { id: string; name: string; src: string };

export const SAMPLES: Sample[] = [
  { id: "sunset", name: "Sunset", src: "/samples/sunset.jpg" },
  { id: "coast", name: "Coast", src: "/samples/coast.jpg" },
  { id: "studio", name: "Studio", src: "/samples/studio.jpg" },
  { id: "forest", name: "Forest", src: "/samples/forest.jpg" },
];

/* Asking someone to go and find a file before they can see what the
   thing does is a lot to ask of a first visit. One click on any of
   these runs the real pipeline on a real image instead. */
export function SamplePicker({
  onPick,
  busyId,
  disabled,
}: {
  onPick: (sample: Sample) => void;
  busyId: string | null;
  disabled: boolean;
}) {
  const reduce = useReducedMotion();

  return (
    <div className="mt-5 border-t border-line pt-5">
      <p className="font-mono text-[11px] tracking-[0.18em] text-muted uppercase">
        Or start with one of these
      </p>

      <div className="mt-3 grid grid-cols-4 gap-2 sm:gap-3">
        {SAMPLES.map((sample, i) => {
          const busy = busyId === sample.id;
          return (
            <motion.button
              key={sample.id}
              type="button"
              onClick={() => onPick(sample)}
              disabled={disabled}
              aria-label={`Extract the palette from the ${sample.name} sample`}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                duration: reduce ? 0 : 0.7,
                ease: EASE,
                delay: reduce ? 0 : 0.55 + i * 0.06,
              }}
              className="group relative overflow-hidden rounded-xl border border-line transition-transform duration-[350ms] ease-[cubic-bezier(0.16,1,0.3,1)] disabled:cursor-not-allowed disabled:opacity-50 [@media(hover:hover)]:hover:-translate-y-1"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src={sample.src}
                alt=""
                width={900}
                height={675}
                loading="lazy"
                className="aspect-[4/3] w-full object-cover transition-transform duration-[550ms] ease-[cubic-bezier(0.16,1,0.3,1)] [@media(hover:hover)]:group-hover:scale-110"
              />

              {/* the name only rides in under the pointer, so the row
                  reads as four colours at rest rather than four cards
                  with labels competing for attention */}
              <span
                aria-hidden
                className="absolute inset-x-0 bottom-0 translate-y-full bg-foreground/80 py-1 text-center text-[10px] font-medium text-background transition-transform duration-[350ms] ease-[cubic-bezier(0.16,1,0.3,1)] [@media(hover:hover)]:group-hover:translate-y-0"
              >
                {sample.name}
              </span>

              {busy && (
                <span className="absolute inset-0 flex items-center justify-center bg-foreground/70">
                  <motion.span
                    aria-hidden
                    className="block h-4 w-4 rounded-full border-2 border-background border-t-transparent"
                    animate={reduce ? undefined : { rotate: 360 }}
                    transition={{ duration: 0.8, repeat: Infinity, ease: "linear" }}
                  />
                </span>
              )}
            </motion.button>
          );
        })}
      </div>
    </div>
  );
}
