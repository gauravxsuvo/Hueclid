"use client";

import { Fragment, type ReactNode } from "react";
import { motion, useReducedMotion } from "framer-motion";

/* A single easing curve used everywhere, so every reveal on the page
   decelerates the same way. This is the "expo out" curve, slow to
   settle, which is what makes a reveal read as considered rather
   than snappy. */
export const EASE: [number, number, number, number] = [0.16, 1, 0.3, 1];

/* ---------------------------------------------------------------
   A note that applies to every component in this file.

   useReducedMotion() reads a media query, so it is false on the
   server and can be true on the client. Anything branched on it
   that changes markup or `initial` values produces a hydration
   mismatch, and React answers a mismatch by throwing the server
   tree away and re-rendering the whole page on the client.

   So the rule here is: reduced motion only ever changes a
   `transition`, never the structure and never an `initial`. Every
   component below renders byte identical HTML either way and simply
   runs its animation in zero seconds when motion is not wanted.
   --------------------------------------------------------------- */

/* ---------------------------------------------------------------
   RevealText

   Word-by-word mask reveal. Each word sits in an overflow-hidden
   box and slides up from below it, staggered left to right. The
   real string stays on the container as an aria-label and every
   split piece is hidden from assistive tech, so screen readers and
   search engines still see one sentence, not a pile of fragments.
   --------------------------------------------------------------- */
export function RevealText({
  text,
  className,
  delay = 0,
  stagger = 0.045,
  duration = 0.9,
  as: Tag = "span",
}: {
  text: string;
  className?: string;
  delay?: number;
  stagger?: number;
  duration?: number;
  as?: "span" | "h1" | "h2" | "h3" | "p";
}) {
  const reduce = useReducedMotion();
  const words = text.split(" ");
  const MotionTag = motion[Tag];

  return (
    <MotionTag
      className={className}
      aria-label={text}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-12% 0px -12% 0px" }}
      transition={{
        staggerChildren: reduce ? 0 : stagger,
        delayChildren: reduce ? 0 : delay,
      }}
    >
      {words.map((word, i) => (
        <Fragment key={`${word}-${i}`}>
          <span
            aria-hidden
            /* the padding/margin pair keeps descenders from being
               sliced off by the mask once the word has landed */
            className="inline-block overflow-hidden pb-[0.14em] mb-[-0.14em] align-bottom"
          >
            <motion.span
              className="inline-block will-change-transform"
              variants={{
                hidden: { y: "110%", opacity: 0 },
                visible: { y: "0%", opacity: 1 },
              }}
              transition={{ duration: reduce ? 0 : duration, ease: EASE }}
            >
              {word}
            </motion.span>
          </span>
          {i < words.length - 1 ? " " : null}
        </Fragment>
      ))}
    </MotionTag>
  );
}

/* ---------------------------------------------------------------
   Reveal

   The workhorse: fade and rise into view once, never replayed on
   scroll back up. `y` is deliberately small, a long distance reads
   as a slide, a short one reads as a settle.
   --------------------------------------------------------------- */
export function Reveal({
  children,
  className,
  delay = 0,
  y = 28,
  duration = 0.9,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  duration?: number;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
      transition={{
        duration: reduce ? 0 : duration,
        ease: EASE,
        delay: reduce ? 0 : delay,
      }}
    >
      {children}
    </motion.div>
  );
}

/* ---------------------------------------------------------------
   Rise

   The heavier entrance: the element lifts, grows the last few
   percent into place, and resolves out of a blur. The blur is what
   separates this from a plain fade, it reads as something coming
   into focus rather than something turning opaque, and it is what
   makes a card feel like it popped rather than appeared.

   Kept off text-heavy blocks at small sizes, animating a filter on
   a paragraph is expensive and the payoff is invisible.
   --------------------------------------------------------------- */
export function Rise({
  children,
  className,
  delay = 0,
  y = 44,
  duration = 1,
  blur = 10,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  y?: number;
  duration?: number;
  blur?: number;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y, scale: 0.965, filter: `blur(${blur}px)` }}
      whileInView={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
      viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
      transition={{
        duration: reduce ? 0 : duration,
        ease: EASE,
        delay: reduce ? 0 : delay,
      }}
    >
      {children}
    </motion.div>
  );
}

/* ---------------------------------------------------------------
   MaskReveal

   A block wipes into view from the bottom edge instead of fading.
   Used for anything with its own surface, cards and images, where a
   fade would look washed out against the paper background.
   --------------------------------------------------------------- */
export function MaskReveal({
  children,
  className,
  delay = 0,
  duration = 1.1,
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  duration?: number;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={className}
      initial={{ clipPath: "inset(0 0 100% 0)", opacity: 0 }}
      whileInView={{ clipPath: "inset(0 0 0% 0)", opacity: 1 }}
      viewport={{ once: true, margin: "-8% 0px -8% 0px" }}
      transition={{
        duration: reduce ? 0 : duration,
        ease: EASE,
        delay: reduce ? 0 : delay,
      }}
    >
      {children}
    </motion.div>
  );
}

/* ---------------------------------------------------------------
   Stagger / StaggerItem

   For lists where the children should arrive in sequence. The
   parent owns the timing so items stay in order regardless of how
   they are composed.
   --------------------------------------------------------------- */
export function Stagger({
  children,
  className,
  stagger = 0.09,
  delay = 0,
}: {
  children: ReactNode;
  className?: string;
  stagger?: number;
  delay?: number;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={className}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-10% 0px -10% 0px" }}
      transition={{
        staggerChildren: reduce ? 0 : stagger,
        delayChildren: reduce ? 0 : delay,
      }}
    >
      {children}
    </motion.div>
  );
}

export function StaggerItem({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      className={className}
      variants={{
        hidden: { opacity: 0, y: 24 },
        visible: {
          opacity: 1,
          y: 0,
          transition: { duration: reduce ? 0 : 0.85, ease: EASE },
        },
      }}
    >
      {children}
    </motion.div>
  );
}

/* ---------------------------------------------------------------
   Line

   A hairline rule that draws itself left to right when it scrolls
   into view. Cheap, and it does a lot of work sectioning the page.
   --------------------------------------------------------------- */
export function Line({ className = "" }: { className?: string }) {
  const reduce = useReducedMotion();

  return (
    <motion.div
      aria-hidden
      className={`h-px w-full origin-left bg-line ${className}`}
      initial={{ scaleX: 0 }}
      whileInView={{ scaleX: 1 }}
      viewport={{ once: true, margin: "-5% 0px" }}
      transition={{ duration: reduce ? 0 : 1.2, ease: EASE }}
    />
  );
}
