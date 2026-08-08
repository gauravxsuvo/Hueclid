"use client";

import { type ReactNode, useEffect, useState } from "react";
import { ReactLenis } from "lenis/react";
import { useReducedMotion } from "framer-motion";

/* Wheel/trackpad smooth scrolling for the whole page.

   Lenis drives native window scroll rather than replacing it, so
   framer-motion's useScroll (the scroll progress bar and every
   parallax on the page) keeps reading the right position with no
   extra wiring.

   Two guards matter here. First, reduced motion: a visitor who has
   asked the system to cut animation should not have their scrolling
   reinterpreted, so Lenis is skipped entirely and the browser's own
   scrolling is used. Second, the CSS `scroll-behavior: smooth` in
   globals.css fights Lenis (both try to own anchor-link jumps); the
   `lenis` class Lenis adds to <html> resets that via lenis's own
   stylesheet, imported below. */
export function SmoothScroll({ children }: { children: ReactNode }) {
  const reduce = useReducedMotion();

  /* useReducedMotion reads a media query, so it is null on the server
     and resolves on the client. Deferring the branch to an effect
     keeps the server and first client render identical: both mount
     the plain wrapper, and Lenis only turns on once we know motion is
     wanted. */
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const frame = requestAnimationFrame(() => setReady(true));
    return () => cancelAnimationFrame(frame);
  }, []);

  if (!ready || reduce) return <>{children}</>;

  return (
    <ReactLenis root options={{ duration: 1.1, smoothWheel: true }}>
      {children}
    </ReactLenis>
  );
}
