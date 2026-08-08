"use client";

import { useRef } from "react";
import { motion, useReducedMotion, useScroll, useTransform } from "framer-motion";
import { EASE, RevealText } from "./motion";

const STEPS = [
  {
    n: "01",
    accent: "text-violet",
    title: "Count in a space that matches the eye",
    body: "Pixels are binned in CIELAB, not RGB. Two greens that a screen calls different numbers but a person reads as the same green get counted as the same green, so the palette reflects what the image looks like rather than how it happens to be encoded.",
  },
  {
    n: "02",
    accent: "text-coral",
    title: "Rank by how much of the image it owns",
    body: "Every color comes back with the share of the frame it actually covers. The order is coverage, not saturation, so the first swatch is the one you would name if someone asked you to describe the picture in one word.",
  },
  {
    n: "03",
    accent: "text-teal",
    title: "Map it back to something a screen can show",
    body: "Averaging in a perceptual space can land outside what sRGB can display. Those colors are gamut mapped in Oklch, which walks chroma down while holding hue and lightness, instead of clipping each channel and shifting the hue on the way.",
  },
];

function Step({ step, index }: { step: (typeof STEPS)[number]; index: number }) {
  const reduce = useReducedMotion();
  const ref = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: ref,
    offset: ["start end", "end start"],
  });
  /* The numeral drifts up through the row a little slower than the
     row itself scrolls. Small enough that you feel it rather than
     watch it, which is the difference between depth and gimmick.

     The range starts at 0 on purpose. A range that starts anywhere
     else renders a different transform on the server than it does
     for a reduced-motion client, and that is a hydration mismatch,
     which costs a full client re-render of the page. */
  const numberY = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [0, -52]);

  return (
    <div ref={ref} className="group relative">
      <motion.div
        aria-hidden
        className="h-px w-full origin-left bg-line"
        initial={{ scaleX: 0 }}
        whileInView={{ scaleX: 1 }}
        viewport={{ once: true, margin: "-5% 0px" }}
        transition={{ duration: reduce ? 0 : 1.1, ease: EASE }}
      />

      <div className="grid gap-3 py-10 sm:grid-cols-[auto_1fr] sm:gap-10 md:py-14">
        <motion.span
          style={{ y: numberY }}
          initial={{ opacity: 0, scale: 0.7, filter: "blur(10px)" }}
          whileInView={{ opacity: 1, scale: 1, filter: "blur(0px)" }}
          viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
          transition={{
            duration: reduce ? 0 : 1,
            ease: EASE,
            delay: reduce ? 0 : 0.05 + index * 0.03,
          }}
          className={`block ${step.accent}`}
        >
          {/* The hover lift has to live on a child. Framer writes the
              parallax to this element's inline transform, and an
              inline transform beats a Tailwind translate class, so
              on the same element the lift silently did nothing. */}
          <span className="font-display block text-[2.5rem] leading-none transition-transform duration-[350ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:-translate-y-1 sm:text-6xl">
            {step.n}
          </span>
        </motion.span>

        <div className="max-w-2xl">
          <RevealText
            as="h3"
            text={step.title}
            className="block text-xl leading-tight font-medium tracking-tight sm:text-3xl"
            stagger={0.03}
            duration={0.8}
          />
          <motion.p
            className="mt-3 leading-relaxed text-muted"
            initial={{ opacity: 0, y: 22 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
            transition={{ duration: reduce ? 0 : 0.9, ease: EASE, delay: reduce ? 0 : 0.18 }}
          >
            {step.body}
          </motion.p>
        </div>
      </div>
    </div>
  );
}

export function Method() {
  const reduce = useReducedMotion();
  const sectionRef = useRef<HTMLElement>(null);
  const { scrollYProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"],
  });
  const headingY = useTransform(scrollYProgress, [0, 1], reduce ? [0, 0] : [0, -80]);

  return (
    <section
      ref={sectionRef}
      id="method"
      className="shell section scroll-mt-24"
    >
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <motion.div style={{ y: headingY }} className="lg:sticky lg:top-28">
            <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
              Method
            </span>
            <RevealText
              as="h2"
              text="Three decisions the palette hangs on"
              className="mt-5 block text-[clamp(1.8rem,3.6vw,3rem)] leading-[1.05] font-medium tracking-[-0.03em]"
              stagger={0.035}
            />
            <motion.p
              className="mt-5 max-w-sm text-muted"
              initial={{ opacity: 0, y: 22 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: "-8% 0px" }}
              transition={{ duration: reduce ? 0 : 0.9, ease: EASE, delay: reduce ? 0 : 0.25 }}
            >
              None of this is a filter over a thumbnail. Each step is a piece of color science
              that was checked against published reference values before anything was built on
              top of it.
            </motion.p>
          </motion.div>
        </div>

        <div className="lg:col-span-8">
          {STEPS.map((step, i) => (
            <Step key={step.n} step={step} index={i} />
          ))}
        </div>
      </div>
    </section>
  );
}
