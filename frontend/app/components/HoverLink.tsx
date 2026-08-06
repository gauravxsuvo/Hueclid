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
  children,
}: {
  href: string;
  external?: boolean;
  onClick?: () => void;
  className?: string;
  children: ReactNode;
}) {
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
