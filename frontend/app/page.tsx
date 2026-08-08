import { Header } from "./components/Header";
import { ScrollProgress } from "./components/ScrollProgress";
import { Hero } from "./components/Hero";
import { PaletteGallery } from "./components/PaletteGallery";
import { Method } from "./components/Method";
import { Timeline } from "./components/Timeline";
import { Footer } from "./components/Footer";

export default function Home() {
  return (
    <>
      {/* Visually out of the way until it is focused, at which point
          it is the first thing a keyboard user reaches. Without it
          they tab the whole header on every visit. */}
      <a
        href="#extract"
        className="sr-only focus:not-sr-only focus:absolute focus:top-3 focus:left-3 focus:z-[80] focus:rounded-full focus:bg-foreground focus:px-4 focus:py-2 focus:text-sm focus:text-background"
      >
        Skip to the tool
      </a>
      <ScrollProgress />
      <Header />
      <main className="flex flex-1 flex-col">
        {/* Hero carries the upload tool and the color band. The
            explanatory sections all sit behind it. */}
        <Hero />
        <PaletteGallery />
        <Method />
        <Timeline />
      </main>
      <Footer />
    </>
  );
}
