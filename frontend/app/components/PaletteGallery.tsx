"use client";

import { useRef, useState } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { EASE, RevealText } from "./motion";

type Palette = { name: string; colors: string[] };

/* Examples of the shape of the output, not extractions of any
   particular photo. Each one is ordered dark to light the way a real
   result is. */
const PALETTES: Palette[] = [
  { name: "Coastline", colors: ["#0B2A3A", "#14606E", "#2E9B8F", "#A8D5BA", "#F0EAD6"] },
  { name: "Dusk", colors: ["#2B1B2F", "#6B2D5C", "#D94F3D", "#F2A65A", "#F5E3C3"] },
  { name: "Studio", colors: ["#17161C", "#4B31D4", "#8E82F0", "#D8412A", "#E9E4DA"] },
  { name: "Orchard", colors: ["#23301F", "#4F6B35", "#97B04A", "#E4C15A", "#F6EFD9"] },
  { name: "Rooftop", colors: ["#1B1D2A", "#3B4A6B", "#7E8FA6", "#C9A227", "#EFE7D6"] },
  { name: "Darkroom", colors: ["#101014", "#2E2A38", "#5C4B6B", "#B57A8C", "#E8D8CE"] },
];

/* Dealt round robin so the columns read left to right. */
const COLUMNS: Palette[][] = [[], [], []];
PALETTES.forEach((p, i) => COLUMNS[i % 3].push(p));

/* Distance each column travels over the section. Different per
   column, which is the whole effect, and every one starts at 0 so
   the server and a reduced-motion client render the same transform.
   See the note in motion.tsx. */
const COLUMN_DRIFT = [-70, -150, -30];

/* WCAG relative luminance, so the hex printed on a swatch is legible
   on that swatch rather than guessed at. The same curve the contrast
   ratio formula uses. */
function inkFor(hex: string): string {
  const channel = (i: number) => {
    const c = parseInt(hex.slice(1 + i * 2, 3 + i * 2), 16) / 255;
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4;
  };
  const luminance = 0.2126 * channel(0) + 0.7152 * channel(1) + 0.0722 * channel(2);
  return luminance > 0.4 ? "#12121a" : "#ffffff";
}

function PaletteCard({ palette, index }: { palette: Palette; index: number }) {
  const reduce = useReducedMotion();
  const [copied, setCopied] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  async function copy(hex: string) {
    try {
      await navigator.clipboard.writeText(hex);
      setCopied(hex);
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(() => setCopied(null), 1200);
    } catch {
      // blocked on insecure origins, the hex is on screen to read
    }
  }

  return (
    <motion.article
      initial={{ opacity: 0, y: 56, scale: 0.96, filter: "blur(12px)" }}
      whileInView={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
      transition={{
        duration: reduce ? 0 : 1.05,
        ease: EASE,
        delay: reduce ? 0 : (index % 3) * 0.08,
      }}
      className="overflow-hidden rounded-2xl border border-line bg-surface transition-transform duration-[350ms] ease-[cubic-bezier(0.16,1,0.3,1)] [@media(hover:hover)]:hover:-translate-y-1.5"
    >
      {/* Each color grows up out of the bottom edge in sequence, so
          the palette assembles itself rather than fading in whole.
          Every swatch is a button: the hex is right there, clicking
          takes it. */}
      <div className="flex h-44 sm:h-52">
        {palette.colors.map((hex, i) => (
          <motion.button
            key={hex}
            type="button"
            onClick={() => copy(hex)}
            aria-label={`Copy ${hex}`}
            className="group/sw relative flex-1 origin-bottom cursor-pointer transition-[flex-grow] duration-[450ms] ease-[cubic-bezier(0.16,1,0.3,1)] [@media(hover:hover)]:hover:grow-[1.7]"
            style={{ backgroundColor: hex }}
            initial={{ scaleY: 0 }}
            whileInView={{ scaleY: 1 }}
            viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
            transition={{
              duration: reduce ? 0 : 0.85,
              ease: EASE,
              delay: reduce ? 0 : 0.18 + i * 0.075,
            }}
          >
            <span
              className="absolute inset-x-0 bottom-2 text-center font-mono text-[9px] tracking-tight opacity-70 transition-opacity duration-300 group-hover/sw:opacity-100"
              style={{ color: inkFor(hex) }}
            >
              {copied === hex ? "copied" : hex.toUpperCase()}
            </span>
          </motion.button>
        ))}
      </div>

      <div className="flex flex-wrap items-center justify-between gap-x-3 gap-y-1 border-t border-line px-4 py-3">
        <span className="text-sm font-medium tracking-tight">{palette.name}</span>
        <span className="font-mono text-[10px] tracking-wider text-faint uppercase">
          Tap to copy
        </span>
      </div>
    </motion.article>
  );
}

function Column({ palettes, index }: { palettes: Palette[]; index: number }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [0, COLUMN_DRIFT[index]]);

  return (
    <motion.div
      ref={ref}
      style={{ y }}
      /* Below the three column layout the columns stack, and three
         different drift rates on a single stack just reads as uneven
         gaps between groups. The utility kills the transform with
         !important, which beats the inline style framer writes. */
      className="stack-no-parallax flex flex-col gap-5 sm:gap-6"
    >
      {palettes.map((p, i) => (
        <PaletteCard key={p.name} palette={p} index={index + i * 3} />
      ))}
    </motion.div>
  );
}

export function PaletteGallery() {
  const reduce = useReducedMotion();

  return (
    <section id="palettes" className="shell section scroll-mt-24">
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <div className="lg:sticky lg:top-28">
            <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
              Palettes
            </span>
            <RevealText
              as="h2"
              text="What comes out the other side"
              className="mt-5 block text-[clamp(1.75rem,3.6vw,3rem)] leading-[1.05] font-medium tracking-[-0.03em]"
              stagger={0.035}
            />
            <motion.p
              className="mt-5 max-w-sm text-muted"
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-8% 0px" }}
              transition={{ duration: reduce ? 0 : 0.9, ease: EASE, delay: reduce ? 0 : 0.2 }}
            >
              A few examples of the shape of the output. Ordered dark to light, weighted by how
              much of the frame each color actually covers, and mapped back into colors a screen
              can display. Click any swatch to take the hex.
            </motion.p>
          </div>
        </div>

        {/* the extra bottom padding absorbs the travel of the column
            that drifts furthest, so the section never ends ragged */}
        <div className="grid gap-5 sm:grid-cols-2 sm:gap-6 lg:col-span-8 lg:grid-cols-3 lg:pb-10">
          {COLUMNS.map((col, i) => (
            <Column key={i} palettes={col} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
