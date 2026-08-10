import type { ReactNode } from "react";

/* One link style shared by the header and the footer, because they
   had drifted into two copies of the same markup and only one of
   them was right.

   The rule lives on a leading-none inline-block wrapped around the
   text, not on the anchor. Anchored to the anchor it inherits the
   anchor's box, and a link that is a flex or grid item gets
   stretched to the height of its row, which is how the footer ended
   up drawing its underline eighty pixels below the word. Tied to the
   text's own box it sits the same distance under every link
   regardless of what the layout does around it. */
export function HoverLink({
  href,
  external,
  onClick,
  className = "",
  variant = "default",
  children,
}: {
  href: string;
  external?: boolean;
  onClick?: () => void;
  className?: string;
  variant?: "default" | "nav";
  children: ReactNode;
}) {
  if (variant === "nav") {
    return (
      <a
        href={href}
        onClick={onClick}
        {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
        className={`group relative self-center overflow-hidden rounded-full px-3.5 py-2 text-muted transition-[color,background-color,transform] duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] hover:-translate-y-0.5 hover:bg-foreground/[0.06] hover:text-foreground focus-visible:bg-foreground/[0.06] focus-visible:text-foreground dark:hover:bg-foreground/[0.08] dark:focus-visible:bg-foreground/[0.08] ${className}`}
      >
        <span
          aria-hidden
          className="absolute inset-x-3 bottom-1 h-px origin-center scale-x-0 rounded-full bg-gradient-to-r from-violet via-plum to-coral transition-transform duration-300 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-x-100 group-focus-visible:scale-x-100"
        />
        <span className="relative z-10 leading-none">{children}</span>
      </a>
    );
  }

  return (
    <a
      href={href}
      onClick={onClick}
      {...(external ? { target: "_blank", rel: "noreferrer" } : {})}
      className={`group self-center py-1 text-muted transition-colors hover:text-foreground ${className}`}
    >
      <span className="relative inline-block leading-none">
        {children}
        <span
          aria-hidden
          /* clears the descenders on words like Roadmap and
             Contributing, at -3px the rule grazed the tail of the g */
          className="absolute inset-x-0 -bottom-[5px] h-px origin-left scale-x-0 bg-foreground transition-transform duration-[400ms] ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-x-100"
        />
      </span>
    </a>
  );
}
