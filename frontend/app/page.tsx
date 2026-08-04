"use client";

import { useState } from "react";
import { extractPalette, type ExtractResult } from "./lib/api";
import { Swatch } from "./components/Swatch";

const VALID_FILE_TYPES = ["image/png", "image/jpeg", "image/webp"];

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [k, setK] = useState(5);
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging , setIsDragging] = useState(false);

  function handleFileChange(selected: File | null) {
    setFile(selected);
    setResult(null);
    setError(null);
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
  }

  function handleDragOver(e:React.DragEvent<HTMLLabelElement>) {
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

  return (
    <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col gap-8 px-6 py-16">
      <header className="flex flex-col gap-2">
        <div className="flex items-center gap-2.5">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/icon.svg" alt="" width={28} height={28} />
          <h1 className="text-2xl font-semibold">Hueclid</h1>
        </div>
        <p className="text-sm text-black/60 dark:text-white/60">
          Upload an image and extract a weighted color palette from it.
        </p>
      </header>

      <section className="flex flex-col gap-4">
        <label
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}  
        className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-black/20 px-6 py-10 text-center text-sm 
        transition-colors ${isDragging ? "border-black/60 bg-black/5 text-black/80 dark:border-white/60 dark:bg-white/10 dark:text-white/80"
              : "border-black/20 text-black/60 hover:border-black/40 dark:border-white/20 dark:text-white/60 dark:hover:border-white/40"
          }`}>
          <input
            type="file"
            accept={VALID_FILE_TYPES.join(",")}
            className="hidden"
            onChange={(e) => handleFileChange(e.target.files?.[0] ?? null)}
          />
          {file ? file.name : "Click to choose an image, or drop one here"}
        </label>

        {previewUrl && (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={previewUrl}
            alt="Selected preview"
            className="max-h-64 w-full rounded-lg object-contain"
          />
        )}

        <div className="flex items-center gap-3">
          <label htmlFor="k" className="text-sm text-black/70 dark:text-white/70">
            Colors
          </label>
          <input
            id="k"
            type="number"
            min={1}
            max={12}
            value={k}
            onChange={(e) => setK(Number(e.target.value))}
            className="w-16 rounded border border-black/15 px-2 py-1 text-sm dark:border-white/20 dark:bg-transparent"
          />
          <button
            onClick={handleExtract}
            disabled={!file || loading}
            className="ml-auto rounded-full bg-foreground px-4 py-2 text-sm font-medium text-background disabled:opacity-40"
          >
            {loading ? "Extracting..." : "Extract palette"}
          </button>
        </div>

        {error && <p className="text-sm text-red-600 dark:text-red-400">{error}</p>}
      </section>

      {result && (
        <section className="flex flex-col gap-3">
          <p className="text-xs text-black/50 dark:text-white/50">
            {result.image_size.width}x{result.image_size.height}px, {result.histogram_bins}{" "}
            histogram bins, {result.palette.length} colors
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {result.palette.map((swatch) => (
              <Swatch key={swatch.rank} swatch={swatch} />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
