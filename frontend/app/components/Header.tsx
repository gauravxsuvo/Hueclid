"use client";

import { useRef, useState } from "react";
import { AnimatePresence, motion, useMotionValueEvent, useScroll } from "framer-motion";
import { EASE } from "./motion";
import { HoverLink } from "./HoverLink";
import { ThemeToggle } from "./ThemeToggle";

const LINKS = [
  { href: "#method", label: "Method" },
  { href: "#extract", label: "Try it" },
  { href: "#roadmap", label: "Roadmap" },
  { href: "https://github.com/gauravxsuvo/Hueclid", label: "GitHub", external: true },
];

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
      transition={{ duration: 0.6, ease: EASE }}
      className={`sticky top-0 z-50 transition-[background-color,border-color,backdrop-filter] duration-500 ${
        scrolled || menuOpen
          ? "border-b border-line bg-background/80 backdrop-blur-xl"
          : "border-b border-transparent bg-transparent"
      }`}
    >
      <div className="mx-auto flex w-full max-w-[1500px] items-center justify-between px-5 py-4 sm:px-10 lg:px-16">
        <a href="#top" className="group flex items-center gap-2.5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/icon.svg"
            alt=""
            width={22}
            height={22}
            className="transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:rotate-90 dark:hidden"
          />
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src="/icon-dark.svg"
            alt=""
            width={22}
            height={22}
            className="hidden transition-transform duration-700 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:rotate-90 dark:block"
          />
          <span className="text-[15px] font-semibold tracking-tight">Hueclid</span>
        </a>

        <div className="flex items-center gap-2 sm:gap-7">
          <nav className="hidden items-center gap-7 sm:flex">
            {LINKS.map((link) => (
              <HoverLink
                key={link.href}
                href={link.href}
                external={link.external}
                className="text-sm"
              >
                {link.label}
              </HoverLink>
            ))}
          </nav>

          <ThemeToggle />

          <button
            type="button"
            onClick={() => setMenuOpen((v) => !v)}
            aria-expanded={menuOpen}
            aria-controls="mobile-nav"
            aria-label={menuOpen ? "Close menu" : "Open menu"}
            className="flex h-9 w-9 items-center justify-center rounded-full text-muted transition-colors hover:text-foreground sm:hidden"
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
            className="overflow-hidden border-t border-line sm:hidden"
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
