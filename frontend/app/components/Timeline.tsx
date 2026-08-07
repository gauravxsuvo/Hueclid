"use client";

import { useRef } from "react";
import { motion, useReducedMotion, useScroll, useSpring, useTransform } from "framer-motion";
import { EASE, RevealText } from "./motion";

type Milestone = {
  tag: string;
  title: string;
  detail: string;
  status: "released" | "active" | "planned";
};

const MILESTONES: Milestone[] = [
  {
    tag: "v0.1.0",
    title: "Foundation",
    detail:
      "The color math, verified against published reference values before anything got built on top of it. Upload an image, get back a ranked, area weighted, gamut mapped palette.",
    status: "released",
  },
  {
    tag: "next",
    title: "In progress",
    detail:
      "The next piece of the pipeline, being built and checked the same way the first one was.",
    status: "active",
  },
  {
    tag: "then",
    title: "Planned",
    detail: "More of the roadmap, not public yet, one verified step at a time.",
    status: "planned",
  },
  {
    tag: "later",
    title: "And beyond",
    detail: "The rest of the plan. Follow the repository to watch it land.",
    status: "planned",
  },
];

const STATUS_LABEL: Record<Milestone["status"], string> = {
  released: "Released",
  active: "In progress",
  planned: "Planned",
};

/* Unreleased phases are held slightly out of focus, which says "not
   yet" without a line of copy about it. The blur is gated behind
   hover:hover: on a phone there is no pointer to clear it with, so
   an ungated blur would just be text a touch user can never read.
   Those devices get the dimming alone, and focus-within clears it
   for anyone arriving by keyboard. */
const PLANNED_CLASSES =
  "opacity-60 transition-all duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] focus-within:opacity-100 [@media(hover:hover)]:blur-[1.5px] [@media(hover:hover)]:hover:opacity-100 [@media(hover:hover)]:hover:blur-none [@media(hover:hover)]:focus-within:blur-none";

function Node({
  milestone,
  index,
  last,
}: {
  milestone: Milestone;
  index: number;
  last: boolean;
}) {
  const reduce = useReducedMotion();
  const planned = milestone.status === "planned";
  const base = reduce ? 0 : index * 0.04;

  return (
    <div
      className={`relative grid grid-cols-[24px_1fr] gap-x-4 sm:grid-cols-[28px_1fr] sm:gap-x-8 ${
        last ? "" : "pb-14 sm:pb-20"
      }`}
    >
      <div className="flex justify-center pt-2">
        <motion.span
          aria-hidden
          initial={{ scale: 0 }}
          whileInView={{ scale: 1 }}
          viewport={{ once: true, margin: "-12% 0px -12% 0px" }}
          transition={{ duration: reduce ? 0 : 0.7, ease: EASE, delay: base }}
          className={`relative block h-3.5 w-3.5 rounded-full border-[3px] border-background ${
            milestone.status === "released"
              ? "bg-violet"
              : milestone.status === "active"
                ? "bg-coral"
                : "bg-line-strong"
          }`}
        >
          {milestone.status === "active" && (
            <motion.span
              className="absolute -inset-1.5 rounded-full bg-coral"
              initial={{ opacity: 0.35, scale: 0.8 }}
              animate={
                reduce
                  ? { opacity: 0, scale: 0.8 }
                  : { opacity: [0.35, 0, 0.35], scale: [0.8, 1.6, 0.8] }
              }
              transition={
                reduce
                  ? { duration: 0 }
                  : { duration: 2.6, repeat: Infinity, ease: "easeInOut" }
              }
            />
          )}
        </motion.span>
      </div>

      <div>
        <motion.div
          className="flex flex-wrap items-center gap-3"
          initial={{ opacity: 0, x: -14 }}
          whileInView={{ opacity: 1, x: 0 }}
          viewport={{ once: true, margin: "-12% 0px -12% 0px" }}
          transition={{ duration: reduce ? 0 : 0.7, ease: EASE, delay: base + (reduce ? 0 : 0.08) }}
        >
          <span className="font-mono text-[11px] tracking-[0.2em] text-muted uppercase">
            {milestone.tag}
          </span>
          <span
            className={`rounded-full border px-2.5 py-0.5 text-[11px] ${
              milestone.status === "released"
                ? "border-violet/40 text-violet"
                : milestone.status === "active"
                  ? "border-coral/40 text-coral"
                  : "border-line text-faint"
            }`}
          >
            {STATUS_LABEL[milestone.status]}
          </span>
        </motion.div>

        <div className={planned ? PLANNED_CLASSES : ""}>
          <motion.div
            initial={{ opacity: 0, y: 34, filter: "blur(9px)" }}
            whileInView={{ opacity: 1, y: 0, filter: "blur(0px)" }}
            viewport={{ once: true, margin: "-12% 0px -12% 0px" }}
            transition={{
              duration: reduce ? 0 : 0.95,
              ease: EASE,
              delay: base + (reduce ? 0 : 0.14),
            }}
          >
            <h3 className="mt-3 text-2xl leading-tight font-medium tracking-tight sm:text-4xl">
              {milestone.title}
            </h3>
            <p className="mt-3 max-w-xl leading-relaxed text-muted">{milestone.detail}</p>
          </motion.div>
        </div>
      </div>
    </div>
  );
}

export function Timeline() {
  const reduce = useReducedMotion();
  const sectionRef = useRef<HTMLElement>(null);
  const railRef = useRef<HTMLDivElement>(null);

  const { scrollYProgress } = useScroll({
    target: railRef,
    offset: ["start 0.85", "end 0.65"],
  });
  const scaleY = useSpring(scrollYProgress, { stiffness: 90, damping: 26, restDelta: 0.001 });

  const { scrollYProgress: sectionProgress } = useScroll({
    target: sectionRef,
    offset: ["start end", "end start"],
  });
  const headingY = useTransform(sectionProgress, [0, 1], reduce ? [0, 0] : [0, -80]);

  return (
    <section
      ref={sectionRef}
      id="roadmap"
      className="shell section scroll-mt-24"
    >
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <motion.div style={{ y: headingY }} className="lg:sticky lg:top-28">
            <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
              Roadmap
            </span>
            <RevealText
              as="h2"
              text="Shipped in phases, verified one at a time"
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
              What is real today is below in full. What is not out yet is deliberately vague, the
              detail lands when the phase does.
            </motion.p>
          </motion.div>
        </div>

        <div ref={railRef} className="relative lg:col-span-8">
          {/* The rail dissolves toward the bottom rather than stopping
              on a hard edge, which says the same thing the blurred
              phases below it say: the road keeps going, it is just
              not drawn yet. */}
          <div
            aria-hidden
            className="absolute top-3 bottom-0 left-[11.5px] w-px bg-line [mask-image:linear-gradient(to_bottom,black_62%,transparent_100%)] sm:left-[13.5px]"
          >
            <motion.div
              className="h-full w-px origin-top bg-gradient-to-b from-violet to-coral"
              style={{ scaleY }}
            />
          </div>

          {MILESTONES.map((m, i) => (
            <Node key={m.tag} milestone={m} index={i} last={i === MILESTONES.length - 1} />
          ))}
        </div>
      </div>
    </section>
  );
}
