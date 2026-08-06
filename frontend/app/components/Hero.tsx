"use client";

import { useRef } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { EASE, RevealText } from "./motion";
import { ColorBand } from "./ColorBand";

/* Three very large, very soft color fields drifting behind the type.
   At this blur radius they read as a tint on the paper rather than
   as shapes, which is the point: they give the background depth
   without competing with the headline. */
function AmbientField() {
  const reduce = useReducedMotion();
  const blobs = [
    { color: "var(--violet)", size: 620, left: "-8%", top: "-20%", dur: 26 },
    { color: "var(--coral)", size: 520, left: "55%", top: "-14%", dur: 31 },
    { color: "var(--teal)", size: 480, left: "22%", top: "40%", dur: 37 },
  ];

  return (
    <div aria-hidden className="pointer-events-none absolute inset-0 overflow-hidden">
      {blobs.map((b, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-[120px]"
          style={{
            width: b.size,
            height: b.size,
            left: b.left,
            top: b.top,
            background: b.color,
            opacity: "var(--blob-opacity)",
          }}
          /* explicit initial so the server and a reduced-motion
             client agree on the rendered transform, see the note in
             motion.tsx */
          initial={{ x: 0, y: 0, scale: 1 }}
          animate={
            reduce
              ? { x: 0, y: 0, scale: 1 }
              : { x: [0, 60, -40, 0], y: [0, -40, 30, 0], scale: [1, 1.12, 0.94, 1] }
          }
          transition={
            reduce
              ? { duration: 0 }
              : { duration: b.dur, repeat: Infinity, ease: "easeInOut" }
          }
        />
      ))}
    </div>
  );
}

/* The stroke is revealed by scaling a wrapper rather than animating
   pathLength. The SVG is stretched non-uniformly to sit under a word
   of arbitrary width, and a dash based reveal does not survive that
   scaling cleanly, it leaves the end cap floating ahead of the line
   while it draws. Wiping a clip from the left has none of that
   problem and reads identically. */
function UnderlineStroke() {
  const reduce = useReducedMotion();
  return (
    <motion.span
      aria-hidden
      className="absolute -bottom-[0.05em] left-0 block h-[0.16em] w-full origin-left"
      initial={{ scaleX: 0, opacity: 0 }}
      animate={{ scaleX: 1, opacity: 1 }}
      transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 1 }}
    >
      <svg
        viewBox="0 0 200 12"
        preserveAspectRatio="none"
        className="h-full w-full overflow-visible"
      >
        <path
          d="M1.5 8.5C42 3.2 108 2.4 198.5 6.6"
          fill="none"
          stroke="var(--coral)"
          strokeWidth="6"
          strokeLinecap="round"
          vectorEffect="non-scaling-stroke"
        />
      </svg>
    </motion.span>
  );
}

export function Hero() {
  const copyRef = useRef<HTMLDivElement>(null);
  const reduce = useReducedMotion();

  /* Measured on the untransformed wrapper, not on the element being
     moved, otherwise the transform feeds back into its own scroll
     measurement. Progress hits 1 exactly when the copy has fully
     left the top of the viewport, so the fade can never dim text
     that is still sitting on screen. */
  const { scrollYProgress } = useScroll({
    target: copyRef,
    offset: ["start start", "end start"],
  });

  /* Flattening the output range rather than dropping the style keeps
     the rendered transform identical between server and client, and
     at rest both ranges resolve to the same "no transform" anyway. */
  const copyY = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [0, -80]);
  const copyOpacity = useTransform(scrollYProgress, [0.35, 1], reduce ? [1, 1] : [1, 0]);

  return (
    <section id="top" className="relative overflow-hidden">
      <AmbientField />

      <div
        ref={copyRef}
        className="relative mx-auto w-full max-w-[1500px] px-5 pt-20 pb-14 sm:px-10 md:pt-28 lg:px-16 lg:pt-32"
      >
      <motion.div style={{ y: copyY, opacity: copyOpacity }}>
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8, ease: EASE }}
          className="flex items-center gap-4"
        >
          <motion.span
            aria-hidden
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 1, ease: EASE, delay: 0.15 }}
            className="h-px w-12 origin-left bg-line-strong sm:w-20"
          />
          <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
            v0.1.0 &nbsp;/&nbsp; foundation released
          </span>
        </motion.div>

        <h1 className="mt-8 max-w-[16ch] text-[clamp(2.9rem,8.2vw,7.5rem)] leading-[0.94] font-medium tracking-[-0.035em] lg:max-w-[18ch]">
          <RevealText text="Turn any image" delay={0.1} />
          <br />
          <RevealText text="into an" delay={0.22} />{" "}
          <span className="relative inline-block overflow-visible">
            <RevealText
              text="accessible"
              delay={0.32}
              className="font-display pr-[0.06em] italic"
            />
            <UnderlineStroke />
          </span>
          <br />
          <RevealText text="color palette" delay={0.44} />
        </h1>

        {/* Deliberately pushed to the right half at desktop. A full
            width paragraph under a full width headline reads like a
            document, the offset reads like a layout. */}
        <div className="mt-12 grid gap-8 md:mt-14 md:grid-cols-12 md:gap-8">
          <motion.p
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.85 }}
            className="text-base leading-relaxed text-muted md:col-span-6 md:col-start-6 lg:col-span-5 lg:col-start-7 lg:text-lg"
          >
            Hueclid reads the colors that actually make up a photo or screenshot and returns a
            ranked, area weighted palette. Backgrounds, surfaces, text and accents that were
            checked against each other, not five swatches that happen to look fine alone.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.98 }}
            className="flex flex-wrap items-center gap-3 md:col-span-12 md:col-start-6 lg:col-start-7"
          >
            <a
              href="#extract"
              className="group relative overflow-hidden rounded-full bg-foreground px-6 py-3 text-sm font-medium text-background"
            >
              <span className="relative z-10">Try it on an image</span>
              {/* the fill sweeps up from the bottom edge on hover */}
              <span
                aria-hidden
                className="absolute inset-0 origin-bottom scale-y-0 bg-violet transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-y-100"
              />
            </a>
            <a
              href="https://github.com/gauravxsuvo/Hueclid"
              target="_blank"
              rel="noreferrer"
              className="rounded-full border border-line-strong px-6 py-3 text-sm font-medium transition-colors hover:bg-foreground hover:text-background"
            >
              View the source
            </a>
          </motion.div>
        </div>
      </motion.div>
      </div>

      <ColorBand />
    </section>
  );
}
