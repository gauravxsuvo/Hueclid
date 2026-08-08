"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { EASE } from "./motion";

/* Three plausible extractions, ordered dark to light the way the
   real output is ordered. */
const PALETTES: { name: string; colors: string[] }[] = [
  {
    name: "dusk",
    colors: ["#2B1B2F", "#6B2D5C", "#D94F3D", "#F2A65A", "#F5E3C3"],
  },
  {
    name: "coast",
    colors: ["#0B2A3A", "#14606E", "#2E9B8F", "#A8D5BA", "#F0EAD6"],
  },
  {
    name: "studio",
    colors: ["#17161C", "#4B31D4", "#8E82F0", "#D8412A", "#E9E4DA"],
  },
];

const CYCLE_MS = 5600;

/* How far each column drifts as the band crosses the viewport. The
   alternating sign is what makes it read as five separate panels
   rather than one image with a parallax on it. Every column starts
   at 0 so the server and a reduced-motion client agree on the
   rendered transform, see the note in motion.tsx. */
const DRIFT = [-32, 20, -20, 32, -26];

function Column({ index, cur, prev }: { index: number; cur: number; prev: number }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [0, DRIFT[index]]);

  return (
    <motion.div
      ref={ref}
      /* The hovered column takes room from its neighbours, the same
         thing the real palette does when one color dominates.

         A CSS transition rather than whileHover on purpose. Framer's
         `transition` prop is the default for every animation on a
         component, so the entrance timing was being applied to the
         hover as well: a quarter second of dead delay before the
         column even began moving, then more than a second to settle.
         Gated behind hover:hover so a tap on a phone cannot leave a
         column stuck wide with no pointer to move away with. */
      className="relative flex-1 origin-bottom overflow-hidden transition-[flex-grow] duration-[450ms] ease-[cubic-bezier(0.16,1,0.3,1)] [@media(hover:hover)]:hover:grow-[1.9]"
      initial={{ scaleY: 0 }}
      animate={{ scaleY: 1 }}
      transition={{
        duration: reduce ? 0 : 1.1,
        ease: EASE,
        delay: reduce ? 0 : 0.3 + index * 0.07,
      }}
    >
      {/* The fills are bled well past the top and bottom edges, by
          more than the largest drift, so the parallax can never
          expose the page behind the band. */}
      <motion.div className="absolute inset-x-0 -inset-y-12" style={{ y }}>
        {/* The palette change is a wipe, not a color tween.
            Interpolating between two swatches passes through every
            muddy color in between, which is the last thing a tool
            about color should be showing. The outgoing swatch sits
            underneath while the new one wipes down over it. */}
        <div
          className="absolute inset-0"
          style={{ backgroundColor: PALETTES[prev].colors[index] }}
        />
        <motion.div
          key={cur}
          className="absolute inset-0"
          style={{ backgroundColor: PALETTES[cur].colors[index] }}
          initial={{ clipPath: "inset(0 0 100% 0)" }}
          animate={{ clipPath: "inset(0 0 0% 0)" }}
          transition={{
            duration: reduce ? 0 : 0.9,
            ease: EASE,
            delay: reduce ? 0 : index * 0.07,
          }}
        />
      </motion.div>
    </motion.div>
  );
}

export function ColorBand() {
  const reduce = useReducedMotion();
  const [phase, setPhase] = useState({ prev: 0, cur: 0 });

  useEffect(() => {
    if (reduce) return;
    const id = setInterval(
      () => setPhase((p) => ({ prev: p.cur, cur: (p.cur + 1) % PALETTES.length })),
      CYCLE_MS,
    );
    return () => clearInterval(id);
  }, [reduce]);

  const { prev, cur } = phase;

  return (
    <div className="w-full">
      <div className="flex h-[26vh] max-h-[250px] min-h-[150px] w-full overflow-hidden">
        {PALETTES[cur].colors.map((_, column) => (
          <Column key={column} index={column} cur={cur} prev={prev} />
        ))}
      </div>

      <div className="flex w-full border-t border-line">
        {PALETTES[cur].colors.map((hex, column) => (
          <div
            key={column}
            className="flex flex-1 items-center justify-center overflow-hidden px-1 py-3"
          >
            <motion.span
              key={`${cur}-${column}`}
              initial={{ y: "130%" }}
              animate={{ y: "0%" }}
              transition={{
                duration: reduce ? 0 : 0.8,
                ease: EASE,
                delay: reduce ? 0 : column * 0.07,
              }}
              className="font-mono text-[9px] tracking-wider text-muted uppercase sm:text-xs"
            >
              {hex}
            </motion.span>
          </div>
        ))}
      </div>
    </div>
  );
}
