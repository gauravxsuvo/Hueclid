"use client";

import { useRef } from "react";
import {
  motion,
  useAnimationFrame,
  useMotionValue,
  useReducedMotion,
  useScroll,
  useSpring,
  useTransform,
  useVelocity,
  wrap,
} from "framer-motion";

const ITEMS = [
  "area weighted",
  "CIEDE2000",
  "perceptually uniform",
  "gamut mapped",
  "contrast checked",
  "verified against references",
  "ranked by coverage",
  "built for real UI",
];

const BASE_SPEED = 2.4; // percent of one row per second

function Row() {
  return (
    <div className="flex shrink-0 items-center">
      {ITEMS.map((item) => (
        <span key={item} className="flex items-center whitespace-nowrap">
          <span className="px-6 text-sm tracking-tight text-muted sm:px-8 sm:text-base">
            {item}
          </span>
          <span className="h-1 w-1 rounded-full bg-line-strong" />
        </span>
      ))}
    </div>
  );
}

/* The strip drifts on its own, but scrolling drives it: the faster
   you scroll the faster it runs, scrolling up runs it backwards, and
   it skews slightly in whichever direction it is being pushed. That
   coupling is the whole trick, it makes the page feel like it has
   weight instead of like a loop playing next to a scrollbar.

   Four rows are laid end to end and the offset wraps at -50%, so
   there is always a full row filling the gap the wrap leaves behind.

   Marked aria-hidden throughout: it is a texture, and a screen
   reader announcing the same eight fragments twice is noise. */
export function Marquee() {
  const reduce = useReducedMotion();
  const baseX = useMotionValue(0);
  const direction = useRef(1);

  const { scrollY } = useScroll();
  const scrollVelocity = useVelocity(scrollY);
  const smoothVelocity = useSpring(scrollVelocity, { damping: 50, stiffness: 380 });
  const velocityFactor = useTransform(smoothVelocity, [0, 1200], [0, 6], { clamp: false });
  /* Symmetric around zero so a still page renders skew 0 whether
     or not motion is reduced, which keeps the server and client
     markup identical. */
  const skew = useTransform(smoothVelocity, [-2500, 2500], reduce ? [0, 0] : [4, -4], {
    clamp: true,
  });

  useAnimationFrame((_, delta) => {
    if (reduce) return;

    let moveBy = direction.current * BASE_SPEED * (delta / 1000);

    const factor = velocityFactor.get();
    if (factor < 0) direction.current = -1;
    else if (factor > 0) direction.current = 1;

    moveBy += moveBy * Math.abs(factor);
    baseX.set(baseX.get() + moveBy);
  });

  const x = useTransform(baseX, (v) => `${wrap(-50, 0, v)}%`);

  return (
    <div
      aria-hidden
      className="relative flex w-full overflow-hidden border-b border-line py-6"
    >
      <motion.div className="flex" style={{ x, skewX: skew }}>
        <Row />
        <Row />
        <Row />
        <Row />
      </motion.div>

      {/* fade the ends into the page so the strip does not look like
          it is being cut off by the viewport */}
      <div className="pointer-events-none absolute inset-y-0 left-0 w-16 bg-gradient-to-r from-background to-transparent sm:w-24" />
      <div className="pointer-events-none absolute inset-y-0 right-0 w-16 bg-gradient-to-l from-background to-transparent sm:w-24" />
    </div>
  );
}
