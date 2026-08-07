"use client";

import { motion, useReducedMotion } from "framer-motion";
import { EASE } from "./motion";
import { HoverLink } from "./HoverLink";

const LINKS = [
  { href: "https://github.com/gauravxsuvo/Hueclid", label: "GitHub" },
  { href: "https://github.com/gauravxsuvo/Hueclid/wiki", label: "Wiki" },
  { href: "https://github.com/gauravxsuvo/Hueclid/releases", label: "Releases" },
  {
    href: "https://github.com/gauravxsuvo/Hueclid/blob/main/CONTRIBUTING.md",
    label: "Contributing",
  },
];

export function Footer() {
  const reduce = useReducedMotion();

  return (
    <footer className="relative mt-8 overflow-hidden border-t border-line">
      {/* A broad wash that fills the bottom of the footer and
          brightens toward the centre, so the whole area lights up as
          you reach the end of the page and the wordmark sits inside
          the light. Built from the page's own accents, and tuned per
          theme through the --footer-glow-* tokens: gentle on the warm
          paper theme, strong on the dark one. Fades in once on view
          and then holds steady, no flicker. Behind everything, no
          pointer events. The opacity token lives on this outer wrapper
          so framer only ever animates a plain 0 to 1 on the inner
          layer. */}
      <div
        aria-hidden
        className="pointer-events-none absolute inset-x-0 bottom-0 -z-10 h-[120%] opacity-[var(--footer-glow-opacity)]"
      >
        <motion.div
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(120% 90% at 50% 100%, color-mix(in srgb, var(--violet) var(--footer-glow-1), transparent) 0%, color-mix(in srgb, var(--plum) var(--footer-glow-2), transparent) 34%, color-mix(in srgb, var(--violet) var(--footer-glow-3), transparent) 56%, transparent 82%)",
          }}
          initial={{ opacity: 0 }}
          whileInView={{ opacity: 1 }}
          viewport={{ once: true, margin: "-4% 0px" }}
          transition={{ duration: reduce ? 0 : 1.2, ease: EASE }}
        />
      </div>
      <div className="shell relative pt-16">
        <div className="grid gap-8 pb-14 sm:grid-cols-2">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true, margin: "-8% 0px" }}
            transition={{ duration: reduce ? 0 : 0.9, ease: EASE }}
          >
            <p className="max-w-sm text-muted">
              An open source color pipeline. Built in phases, each one checked against published
              reference values before the next one starts.
            </p>
            <p className="mt-4 font-mono text-[11px] tracking-[0.18em] text-faint uppercase">
              MIT licensed
            </p>
          </motion.div>

          {/* items-start matters: this nav is a grid item, so it is
              stretched to the height of the row, and without it the
              links stretch with it. */}
          <nav className="flex flex-wrap items-start gap-x-8 gap-y-2 sm:justify-end">
            {LINKS.map((link, i) => (
              <motion.div
                key={link.href}
                initial={{ opacity: 0, y: 18 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-8% 0px" }}
                transition={{
                  duration: reduce ? 0 : 0.8,
                  ease: EASE,
                  delay: reduce ? 0 : 0.08 + i * 0.07,
                }}
              >
                <HoverLink href={link.href} external className="text-sm">
                  {link.label}
                </HoverLink>
              </motion.div>
            ))}
          </nav>
        </div>

        {/* At this size the name is a mark, not a heading, so it is
            hidden from assistive tech and the readable name lives in
            the copy above it. The wrapper masks the slide so the
            letters rise out of the page edge, and the tight leading
            plus the negative margin keep the glyphs whole while
            still closing the gap the line box would otherwise leave
            under them. */}
        {/* Driven by whileInView rather than by scroll position. The
            footer is the last thing on the page, so at full scroll
            the mark still sits three quarters of the way down the
            viewport and can never travel far enough to finish a
            scroll-linked range, which left it stuck at opacity zero. */}
        <div aria-hidden className="relative -mb-[0.1em] overflow-hidden pb-1">
          <motion.p
            initial={{ y: "26%", opacity: 0 }}
            whileInView={{ y: "0%", opacity: 1 }}
            viewport={{ once: true, margin: "-4% 0px" }}
            transition={{ duration: reduce ? 0 : 1.3, ease: EASE }}
            className="relative text-center text-[clamp(3.5rem,17vw,16rem)] leading-[0.92] font-medium tracking-[-0.05em] text-foreground/90 select-none"
          >
            Hueclid
          </motion.p>
        </div>
      </div>
    </footer>
  );
}
