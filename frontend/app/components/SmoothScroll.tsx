"use client";

import { type ReactNode } from "react";
import { ReactLenis } from "lenis/react";
import { useReducedMotion } from "framer-motion";

/* Wheel/trackpad smooth scrolling for the whole page.

   Lenis drives native window scroll rather than replacing it, so
   framer-motion's useScroll (the scroll progress bar and every
   parallax on the page) keeps reading the right position with no
   extra wiring.

   Two guards matter here. First, reduced motion: a visitor who has
   asked the system to cut animation should not have wheel smoothing
   applied. Second, the CSS `scroll-behavior: smooth` in
   globals.css fights Lenis (both try to own anchor-link jumps); the
   `lenis` class Lenis adds to <html> resets that via lenis's own
   stylesheet, imported below. */
export function SmoothScroll({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();

  return (
    <ReactLenis root options={{ duration: 1.1, smoothWheel: !reduce }}>
      {children}
    </ReactLenis>
  );
}
