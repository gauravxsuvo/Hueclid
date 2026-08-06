"use client";

import { useEffect, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "framer-motion";
import { extractPalette, type ExtractResult } from "../lib/api";
import { Swatch } from "./Swatch";
import { EASE, Rise, RevealText } from "./motion";

const VALID_FILE_TYPES = ["image/png", "image/jpeg", "image/webp"];
const MIN_K = 1;
const MAX_K = 12;

function clampK(value: number): number {
  if (Number.isNaN(value)) return MIN_K;
  return Math.min(MAX_K, Math.max(MIN_K, Math.round(value)));
}

export function ExtractTool() {
  const reduce = useReducedMotion();
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [k, setK] = useState(5);
  const [kText, setKText] = useState("5");
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [copiedAll, setCopiedAll] = useState(false);

  /* Swapping files already revokes the outgoing URL, but the last
     one selected stayed allocated for the life of the tab. Mirroring
     it into a ref and revoking from an unmount-only cleanup covers
     that without tying the revoke to the value's own effect, which
     under Strict Mode's double invoke would tear down a URL the
     preview is still pointing at. */
  const previewRef = useRef<string | null>(null);
  useEffect(() => {
    previewRef.current = previewUrl;
  }, [previewUrl]);
  useEffect(() => {
    return () => {
      if (previewRef.current) URL.revokeObjectURL(previewRef.current);
    };
  }, []);

  function handleFileChange(selected: File | null) {
    setFile(selected);
    setResult(null);
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  function setColors(next: number) {
    const clamped = clampK(next);
    setK(clamped);
    setKText(String(clamped));
  }

  function handleDragOver(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDragging(true);
  }

  function handleDragLeave(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDragging(false);
  }

  function handleDrop(e: React.DragEvent<HTMLLabelElement>) {
    e.preventDefault();
    setIsDragging(false);

    const droppedFile = e.dataTransfer.files?.[0];
    if (droppedFile) {
      if (VALID_FILE_TYPES.includes(droppedFile.type)) {
        handleFileChange(droppedFile);
      } else {
        setError("Invalid file type. Please upload a PNG, JPEG, or WEBP.");
      }
    }
  }

  async function handleExtract() {
    if (!file) return;
    setLoading(true);
    setError(null);
    try {
      const data = await extractPalette(file, k);
      setResult(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function copyAll() {
    if (!result) return;
    try {
      await navigator.clipboard.writeText(result.palette.map((s) => s.hex).join("\n"));
      setCopiedAll(true);
      setTimeout(() => setCopiedAll(false), 1600);
    } catch {
      // clipboard is unavailable on insecure origins, the per swatch
      // hex codes are still on screen to read
    }
  }

  return (
    <section
      id="extract"
      className="relative mx-auto w-full max-w-[1500px] scroll-mt-24 px-5 py-24 sm:px-10 md:py-32 lg:px-16"
    >
      <div className="grid gap-10 lg:grid-cols-12 lg:gap-16">
        <div className="lg:col-span-4">
          <div className="lg:sticky lg:top-28">
            <span className="font-mono text-[11px] tracking-[0.22em] text-muted uppercase">
              Live
            </span>
            <RevealText
              as="h2"
              text="Run it on your own image"
              className="mt-5 block text-[clamp(1.8rem,3.6vw,3rem)] leading-[1.05] font-medium tracking-[-0.03em]"
              stagger={0.035}
            />
            <p className="mt-5 max-w-sm text-muted">
              PNG, JPEG or WEBP. The image is processed and thrown away, nothing is stored. Pick
              how many colors you want back and the palette comes out ranked by coverage.
            </p>
          </div>
        </div>

        <Rise className="lg:col-span-8" y={56}>
          <div className="rounded-2xl border border-line bg-surface p-4 sm:p-7">
            {/* The input is sr-only rather than hidden. display:none
                takes it out of the tab order, which made the whole
                uploader unreachable without a mouse, this keeps it
                focusable and the label lights up with it. */}
            <label
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
              className={`flex cursor-pointer flex-col items-center justify-center gap-4 rounded-xl border border-dashed px-4 py-14 text-center transition-colors duration-300 has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-offset-4 has-[:focus-visible]:outline-foreground sm:px-6 sm:py-20 ${
                isDragging
                  ? "border-violet bg-violet/5 text-foreground"
                  : "border-line-strong text-muted hover:border-foreground/45 hover:text-foreground"
              }`}
            >
              <motion.svg
                width="32"
                height="32"
                viewBox="0 0 24 24"
                fill="none"
                aria-hidden
                animate={isDragging && !reduce ? { y: [-3, 3, -3] } : { y: 0 }}
                transition={{ duration: 1.2, repeat: isDragging ? Infinity : 0 }}
              >
                <path
                  d="M12 16V4m0 0-4 4m4-4 4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </motion.svg>
              <input
                type="file"
                accept={VALID_FILE_TYPES.join(",")}
                className="sr-only"
                onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
              />
              <span className="text-sm break-all">
                {file ? file.name : "Drop an image here, or click to choose one"}
              </span>
            </label>

            <AnimatePresence initial={false}>
              {previewUrl && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.5, ease: EASE }}
                  className="overflow-hidden"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img
                    src={previewUrl}
                    alt="Selected preview"
                    className="mt-4 max-h-72 w-full rounded-xl object-contain"
                  />
                </motion.div>
              )}
            </AnimatePresence>

            <div className="mt-5 flex flex-wrap items-center gap-x-4 gap-y-3 border-t border-line pt-5">
              <label
                htmlFor="k"
                className="font-mono text-[11px] tracking-[0.18em] text-muted uppercase"
              >
                Colors
              </label>

              {/* A stepper as well as the field: on a phone the number
                  spinners are invisible, and typing into a clamped
                  input fights you when you clear it to retype. */}
              <div className="flex items-center rounded-full border border-line">
                <button
                  type="button"
                  onClick={() => setColors(k - 1)}
                  disabled={k <= MIN_K}
                  aria-label="One fewer color"
                  className="px-3 py-2 text-base leading-none text-muted transition-colors hover:text-foreground disabled:opacity-30"
                >
                  &minus;
                </button>
                <input
                  id="k"
                  type="number"
                  inputMode="numeric"
                  min={MIN_K}
                  max={MAX_K}
                  value={kText}
                  onChange={(e) => {
                    setKText(e.target.value);
                    const parsed = Number(e.target.value);
                    if (e.target.value !== "" && !Number.isNaN(parsed)) setK(clampK(parsed));
                  }}
                  onBlur={() => setColors(Number(kText))}
                  className="w-10 [appearance:textfield] bg-transparent text-center text-sm outline-none [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none"
                />
                <button
                  type="button"
                  onClick={() => setColors(k + 1)}
                  disabled={k >= MAX_K}
                  aria-label="One more color"
                  className="px-3 py-2 text-base leading-none text-muted transition-colors hover:text-foreground disabled:opacity-30"
                >
                  +
                </button>
              </div>

              <button
                onClick={handleExtract}
                disabled={!file || loading}
                className="group relative w-full overflow-hidden rounded-full bg-foreground px-6 py-3 text-sm font-medium text-background transition-opacity disabled:pointer-events-none disabled:opacity-35 sm:ml-auto sm:w-auto"
              >
                <span className="relative z-10">
                  {loading ? "Extracting" : "Extract palette"}
                </span>
                <span
                  aria-hidden
                  className="absolute inset-0 origin-bottom scale-y-0 bg-violet transition-transform duration-500 ease-[cubic-bezier(0.16,1,0.3,1)] group-hover:scale-y-100"
                />
              </button>
            </div>

            <div role="status" aria-live="polite" className="min-h-6 pt-3 text-sm">
              {error && <p className="text-coral">{error}</p>}
              {loading && (
                <p className="flex items-center gap-2 text-muted">
                  <motion.span
                    aria-hidden
                    className="h-1.5 w-1.5 rounded-full bg-violet"
                    initial={{ opacity: 1 }}
                    animate={reduce ? { opacity: 1 } : { opacity: [1, 0.2, 1] }}
                    transition={reduce ? { duration: 0 } : { duration: 1.1, repeat: Infinity }}
                  />
                  Reading the image, this takes under a second.
                </p>
              )}
            </div>
          </div>
        </Rise>
      </div>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: reduce ? 0 : 0.7, ease: EASE }}
            className="mt-14"
          >
            <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-2 border-t border-line pt-6">
              <h3 className="text-xl font-medium tracking-tight">Your palette</h3>
              <div className="flex flex-wrap items-center gap-4">
                <p className="font-mono text-[11px] tracking-[0.16em] text-faint uppercase">
                  {result.image_size.width}&times;{result.image_size.height}px &nbsp;/&nbsp;{" "}
                  {result.histogram_bins} bins
                </p>
                <button
                  type="button"
                  onClick={copyAll}
                  className="rounded-full border border-line px-3.5 py-1.5 text-xs transition-colors hover:border-line-strong hover:text-foreground"
                >
                  {copiedAll ? "Copied all" : "Copy all"}
                </button>
              </div>
            </div>

            <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4 xl:grid-cols-6">
              {result.palette.map((swatch, i) => (
                <motion.div
                  key={swatch.rank}
                  initial={{ opacity: 0, y: 34, scale: 0.94, filter: "blur(8px)" }}
                  animate={{ opacity: 1, y: 0, scale: 1, filter: "blur(0px)" }}
                  transition={{
                    duration: reduce ? 0 : 0.85,
                    delay: reduce ? 0 : i * 0.07,
                    ease: EASE,
                  }}
                >
                  <Swatch swatch={swatch} />
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </section>
  );
}
