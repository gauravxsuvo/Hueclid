"use client";

import { motion, useScroll, useSpring } from "framer-motion";

/* A hairline at the very top of the viewport that fills as you move
   down the page. The spring is what keeps it from twitching on a
   trackpad, raw scroll progress alone looks nervous. */
export function ScrollProgress() {
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, {
    stiffness: 120,
    damping: 30,
    restDelta: 0.001,
  });

  return (
    <motion.div
      aria-hidden
      style={{ scaleX }}
      className="fixed inset-x-0 top-0 z-[60] h-[2px] origin-left bg-gradient-to-r from-violet via-plum to-coral"
    />
  );
}
