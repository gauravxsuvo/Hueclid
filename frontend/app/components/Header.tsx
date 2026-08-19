"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useMotionValueEvent, useScroll } from "framer-motion";
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
  const headerRef = useRef<HTMLElement>(null);
  const lastY = useRef(0);
  const [scrolled, setScrolled] = useState(false);
  const [pinned, setPinned] = useState(true);
  const [menuOpen, setMenuOpen] = useState(false);
  const [focusInside, setFocusInside] = useState(false);
  const [hiddenY, setHiddenY] = useState(-100);

  useEffect(() => {
    const header = headerRef.current;
    if (!header) return;

    const measureHiddenPosition = () => {
      const top = Number.parseFloat(window.getComputedStyle(header).top) || 0;
      setHiddenY(-(header.offsetHeight + top));
    };

    measureHiddenPosition();
    const observer = new ResizeObserver(measureHiddenPosition);
    observer.observe(header);
    window.addEventListener("resize", measureHiddenPosition);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", measureHiddenPosition);
    };
  }, []);

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
      ref={headerRef}
      onFocus={() => setFocusInside(true)}
      onBlur={(e) => {
        if (!e.currentTarget.contains(e.relatedTarget as Node | null)) setFocusInside(false);
      }}
      initial={{ opacity: 0, y: -16 }}
      animate={{ opacity: visible ? 1 : 0, y: visible ? 0 : hiddenY }}
      transition={{ duration: 0.35, ease: EASE }}
      className={`fixed top-3 inset-x-3 z-50 mx-auto max-w-5xl overflow-hidden rounded-[1.75rem] border shadow-[0_18px_60px_rgba(0,0,0,0.12)] transition-[background-color,border-color,backdrop-filter,box-shadow] duration-500 before:pointer-events-none before:absolute before:inset-0 before:bg-[linear-gradient(110deg,rgba(75,49,212,0.12),transparent_34%,rgba(216,65,42,0.12))] before:opacity-70 sm:top-4 sm:inset-x-4 md:rounded-full dark:shadow-[0_18px_70px_rgba(0,0,0,0.35)] dark:before:bg-[linear-gradient(110deg,rgba(163,148,255,0.12),transparent_34%,rgba(255,124,94,0.10))] ${
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
                className="absolute top-0 left-0 block h-px w-full origin-center bg-current"
                animate={menuOpen ? { y: 4.5, rotate: 45 } : { y: 0, rotate: 0 }}
                transition={{ duration: 0.25, ease: EASE }}
              />
              <motion.span
                className="absolute bottom-0 left-0 block h-px w-full origin-center bg-current"
                animate={menuOpen ? { y: -4.5, rotate: -45 } : { y: 0, rotate: 0 }}
                transition={{ duration: 0.25, ease: EASE }}
              />
            </span>
          </button>
        </div>
      </div>

      <div
        className={`grid transition-[grid-template-rows] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] md:hidden ${
          menuOpen ? "grid-rows-[1fr]" : "grid-rows-[0fr]"
        }`}
      >
        <div className="min-h-0 overflow-hidden">
          <motion.nav
            id="mobile-nav"
            aria-hidden={!menuOpen}
            inert={!menuOpen}
            animate={menuOpen ? { opacity: 1, y: 0 } : { opacity: 0, y: -8 }}
            transition={{ duration: 0.25, ease: EASE }}
            className="border-t border-line"
          >
            <ul className="flex flex-col px-5 py-2">
              {LINKS.map((link) => (
                <li
                  key={link.href}
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
                </li>
              ))}
            </ul>
          </motion.nav>
        </div>
      </div>
    </motion.header>
  );
}
