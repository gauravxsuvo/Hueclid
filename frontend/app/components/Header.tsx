"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "framer-motion";
import { EASE } from "./motion";
import { HoverLink } from "./HoverLink";
import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "#extract", label: "Try it" },
  { href: "#palettes", label: "Palettes" },
  { href: "#method", label: "Method" },
  { href: "#roadmap", label: "Roadmap" },
  { href: "https://github.com/gauravxsuvo/Hueclid", label: "GitHub", external: true },
];

const PRIMARY_LINKS = LINKS.slice(0, -1);
const GITHUB_LINK = LINKS[LINKS.length - 1];

export function Header() {
  const { scrollY } = useScroll();
  const lastY = useRef(0);
  const [scrolled, setScrolled] = useState(false);
  const [pinned, setPinned] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [focusInside, setFocusInside] = useState(false);

  useMotionValueEvent(scrollY, "change", (y) => {
    setScrolled(y > 24);

    /* Slides away on the way down and comes straight back on the way
       up, so the header is out of the way while reading but never
       more than a flick of the wheel from returning. Held open
       whenever the mobile panel is, otherwise the menu would leave
       with the bar it is attached to. */
    const delta = y - lastY.current;
    if (!menuOpen && Math.abs(delta) > 6) {
      setPinned(delta < 0 || y < 120);
    }
    lastY.current = y;
  });

  /* A hidden header still holds focusable links. Tabbing into one
     while it is off screen leaves a keyboard user with a focus ring
     they cannot see, so any focus landing inside brings it back. */
  const visible = pinned || menuOpen || focusInside;

  return (
    <motion.header
      onFocus={() => setFocusInside(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocusInside(false);
      }}
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: 1, y: visible ? 0 : "-100%" }}
      transition={{ duration: 0.35, ease: EASE }}
      className={`fixed top-3 inset-x-3 z-50 mx-auto max-w-5xl overflow-hidden border shadow-[0_18px_60px_rgba(0,0,0,0.12)] transition-[background-color,border-color,backdrop-filter,box-shadow,border-radius] duration-500 before:pointer-events-none before:absolute before:inset-0 before:bg-[linear-gradient(110deg,rgba(75,49,212,0.12),transparent_34%,rgba(216,65,42,0.12))] before:opacity-70 sm:top-4 sm:inset-x-4 dark:shadow-[0_18px_70px_rgba(0,0,0,0.35)] dark:before:bg-[linear-gradient(110deg,rgba(163,148,255,0.12),transparent_34%,rgba(255,124,94,0.10))] ${
        menuOpen ? "rounded-[1.75rem]" : "rounded-full"
      } ${
        scrolled || menuOpen
          ? "border-line bg-background/80 backdrop-blur-xl"
          : "border-line bg-background/60 backdrop-blur-xl"
      }`}
    >
      <div className="relative flex h-14 items-center justify-between px-4 sm:h-16 sm:px-6">
        <div className="flex min-w-0 items-center gap-8 lg:gap-12">
          <a href="#top" className="group flex shrink-0 items-center gap-3">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/icon.svg"
              alt=""
              width={28}
              height={28}
              className="transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:rotate-90 dark:hidden"
            />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/icon-dark.svg"
              alt=""
              width={28}
              height={28}
              className="hidden transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:rotate-90 dark:block"
            />
            <span className="text-lg font-semibold tracking-tight text-foreground sm:text-xl">Hueclid</span>
          </a>

          <nav className="hidden items-center gap-7 md:flex lg:gap-8">
            {PRIMARY_LINKS.map((link) => (
              <HoverLink
                key={link.href}
                href={link.href}
                external={link.external}
                className="text-sm font-medium"
                variant="nav"
              >
                {link.label}
              </HoverLink>
            ))}
          </nav>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-4">
          <ThemeToggle />

          <a
            href={GITHUB_LINK.href}
            target="_blank"
            rel="noreferrer"
            className="hidden rounded-full bg-foreground px-5 py-2.5 text-sm font-semibold text-background shadow-[0_10px_30px_rgba(0,0,0,0.12)] transition-[transform,box-shadow,background-color] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-0.5 hover:scale-[1.03] hover:shadow-[0_14px_34px_rgba(0,0,0,0.18)] active:scale-95 md:block"
          >
            {GITHUB_LINK.label}
          </a>

          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition-colors hover:text-foreground md:hidden"
          >
            <span aria-hidden className="relative block h-[10px] w-[18px]">
              <motion.span
                className="absolute left-0 block h-px w-full bg-current"
                animate={menuOpen ? { top: 5, rotate: 45 } : { top: 0, rotate: 0 }}
                transition={{ duration: 0.35, ease: EASE }}
              />
              <motion.span
                className="absolute left-0 block h-px w-full bg-current"
                animate={menuOpen ? { top: 5, rotate: -45 } : { top: 9, rotate: 0 }}
                transition={{ duration: 0.35, ease: EASE }}
              />
            </span>
          </button>
        </div>
      </div>

      <AnimatePresence initial={false}>
        {menuOpen && (
          <motion.nav
            id="mobile-nav"
            key="mobile-nav"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.45, ease: EASE }}
            className="overflow-hidden border-t border-line md:hidden"
          >
            <ul className="flex flex-col px-5 py-2">
              {LINKS.map((link, i) => (
                <motion.li
                  key={link.href}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.45, ease: EASE, delay: 0.06 + i * 0.05 }}
                  className="border-b border-line last:border-b-0"
                >
                  <HoverLink
                    href={link.href}
                    external={link.external}
                    onClick={() => setMenuOpen(false)}
                    className="block py-3.5 text-base"
                  >
                    {link.label}
                  </HoverLink>
                </motion.li>
              ))}
            </ul>
          </motion.nav>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
