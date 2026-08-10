"use client";

import { motion, useReducedMotion } from "framer-motion";
import { EASE, RevealText } from "./motion";
import { ExtractTool } from "./ExtractTool";
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
      transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.85 }}
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

/* The tool is the product, so it sits in the first screen next to
   the headline rather than three sections down. Everything that
   explains it comes after, for the people who want it. */
export function Hero() {
  const reduce = useReducedMotion();

  return (
    <section id="top" className="relative overflow-hidden">
      <AmbientField />

      <div className="shell relative pt-28 pb-14 sm:pt-32 sm:pb-16 lg:pt-36">
        <div className="grid items-start gap-10 lg:grid-cols-12 lg:gap-14">
          <div className="lg:col-span-6 xl:col-span-5">
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ duration: reduce ? 0 : 0.8, ease: EASE }}
              className="flex items-center gap-4"
            >
              <motion.span
                aria-hidden
                initial={{ scaleX: 0 }}
                animate={{ scaleX: 1 }}
                transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.15 }}
                className="h-px w-10 origin-left bg-line-strong sm:w-16"
              />
              <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
                v0.1.0 &nbsp;/&nbsp; foundation released
              </span>
            </motion.div>

            <h1 className="mt-5 text-[clamp(2.05rem,4.8vw,4.3rem)] leading-[0.98] font-medium tracking-[-0.035em] sm:mt-6">
              <RevealText text="Turn any image" delay={0.08} />
              <br />
              <RevealText text="into an" delay={0.18} />{" "}
              <span className="relative inline-block overflow-visible">
                <RevealText
                  text="accessible"
                  delay={0.26}
                  className="font-display pr-[0.06em] italic"
                />
                <UnderlineStroke />
              </span>
              <br />
              <RevealText text="color palette" delay={0.36} />
            </h1>

            <motion.p
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.6 }}
              className="mt-5 max-w-md leading-relaxed text-muted"
            >
              Drop in a photo or a screenshot. Hueclid returns a ranked, area weighted palette
              built from the colors that actually make it up.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 24 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: reduce ? 0 : 1, ease: EASE, delay: reduce ? 0 : 0.72 }}
              className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-sm text-muted"
            >
              <span className="flex items-center gap-2">
                <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-teal" />
                Nothing is stored
              </span>
              <span className="flex items-center gap-2">
                <span aria-hidden className="h-1.5 w-1.5 rounded-full bg-violet" />
                Runs in under a second
              </span>
              {/* the same link is in the header, so on a phone it just
                  costs a line above the fold */}
              <a
                href="https://github.com/gauravxsuvo/Hueclid"
                target="_blank"
                rel="noreferrer"
                className="hidden underline decoration-line-strong underline-offset-4 transition-colors hover:text-foreground sm:inline"
              >
                Source on GitHub
              </a>
            </motion.div>
          </div>

          {/* ExtractTool renders two grid children of its own: the
              upload card for the right hand column, and the results,
              which span the full width on a row underneath. */}
          <ExtractTool />
        </div>
      </div>

      <ColorBand />
    </section>
  );
}
