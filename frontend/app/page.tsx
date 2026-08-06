"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import { useCallback, useEffect, useRef, useState } from "react";
import { Swatch } from "./components/Swatch";
import { extractPalette, type ExtractResult } from "./lib/api";

const ColorSpaceViewer = dynamic(
  () => import("./components/ColorSpaceViewer").then((module) => module.ColorSpaceViewer),
  {
    ssr: false,
    loading: () => <div className="viewer-loading">Calibrating perceptual space…</div>,
  },
);

const MAX_FILE_SIZE = 15 * 1024 * 1024;
const ACCEPTED_TYPES = new Set(["image/png", "image/jpeg", "image/webp"]);

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [k, setK] = useState(5);
  const [result, setResult] = useState<ExtractResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeCluster, setActiveCluster] = useState<number | null>(null);
  const [copiedHex, setCopiedHex] = useState<string | null>(null);
  const requestController = useRef<AbortController | null>(null);

  useEffect(() => {
    return () => {
      requestController.current?.abort();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
    };
  }, [previewUrl]);

  useEffect(() => {
    if (!result) return;
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    document.getElementById("analysis")?.scrollIntoView({
      behavior: prefersReducedMotion ? "auto" : "smooth",
      block: "start",
    });
  }, [result]);

  const handleFileChange = useCallback(
    (selected: File | null) => {
      if (!selected) return;
      if (!ACCEPTED_TYPES.has(selected.type)) {
        setError("Choose a PNG, JPEG, or WebP image.");
        return;
      }
      if (selected.size > MAX_FILE_SIZE) {
        setError("That image is larger than the 15 MB limit.");
        return;
      }

      requestController.current?.abort();
      if (previewUrl) URL.revokeObjectURL(previewUrl);
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setResult(null);
      setActiveCluster(null);
      setError(null);
    },
    [previewUrl],
  );

  async function handleExtract() {
    if (!file || loading) return;
    const controller = new AbortController();
    requestController.current?.abort();
    requestController.current = controller;
    setLoading(true);
    setError(null);
    setResult(null);
    setActiveCluster(null);

    try {
      const data = await extractPalette(file, k, controller.signal);
      setResult(data);
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") return;
      setError(err instanceof Error ? err.message : "The color-space analysis could not finish.");
    } finally {
      if (requestController.current === controller) {
        setLoading(false);
        requestController.current = null;
      }
    }
  }

  async function copyHex(hex: string) {
    await navigator.clipboard.writeText(hex);
    setCopiedHex(hex);
    window.setTimeout(() => setCopiedHex((current) => (current === hex ? null : current)), 1400);
  }

  const cloud = result?.visualization;

  return (
    <div className={`app-shell${result ? " has-result" : ""}`}>
      <header className="site-header">
        <a className="brand-lockup" href="#top" aria-label="Hueclid home">
          <Image src="/icon.svg" alt="" width={30} height={30} priority />
          <span>Hueclid</span>
        </a>
        <div className="header-note">
          <span className="status-dot" />
          FastAPI model · CIELAB / D65
        </div>
      </header>

      <main id="top">
        <section className="hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow">Perceptual color instrument · 01</p>
            <h1 id="hero-title">
              Color, made
              <em> measurable.</em>
            </h1>
            <p className="hero-lede">
              Turn an image into a weighted map of human-perceived color. Inspect the cloud, isolate
              its clusters, and see exactly where every extracted swatch lives.
            </p>

            <dl className="method-strip">
              <div>
                <dt>reference</dt>
                <dd>D65</dd>
              </div>
              <div>
                <dt>bin size</dt>
                <dd>2 Lab</dd>
              </div>
              <div>
                <dt>difference</dt>
                <dd>ΔE00</dd>
              </div>
            </dl>
          </div>

          <div className="input-station">
            <div className="station-heading">
              <span>Source image</span>
              <span>PNG · JPEG · WEBP / 15 MB</span>
            </div>

            <label
              className={`drop-zone${dragging ? " is-dragging" : ""}${file ? " has-file" : ""}`}
              onDragEnter={(event) => {
                event.preventDefault();
                setDragging(true);
              }}
              onDragOver={(event) => event.preventDefault()}
              onDragLeave={() => setDragging(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragging(false);
                handleFileChange(event.dataTransfer.files[0] ?? null);
              }}
            >
              <input
                type="file"
                aria-label="Choose source image"
                accept="image/png,image/jpeg,image/webp"
                onChange={(event) => handleFileChange(event.target.files?.[0] ?? null)}
              />
              {previewUrl ? (
                <>
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img className="drop-preview" src={previewUrl} alt="Selected source preview" />
                  <span className="drop-file-name">{file?.name}</span>
                  <span className="drop-change">Choose another image</span>
                </>
              ) : (
                <>
                  <span className="drop-mark" aria-hidden="true">+</span>
                  <strong>Drop an image into the lab</strong>
                  <span>or click to browse your device</span>
                </>
              )}
            </label>

            <div className="station-controls">
              <label htmlFor="cluster-count">
                <span>Palette resolution</span>
                <output htmlFor="cluster-count">{k} clusters</output>
              </label>
              <input
                id="cluster-count"
                type="range"
                min={2}
                max={12}
                step={1}
                value={k}
                onChange={(event) => setK(Number(event.target.value))}
              />
              <button type="button" onClick={handleExtract} disabled={!file || loading}>
                <span>{loading ? "Mapping color space" : result ? "Rebuild map" : "Map color space"}</span>
                <span aria-hidden="true">{loading ? <i className="spinner" /> : "↗"}</span>
              </button>
            </div>

            <p className="form-message" role="status" aria-live="polite">
              {error ?? (loading ? "Converting pixels, binning Lab coordinates, and fitting clusters…" : "")}
            </p>
          </div>
        </section>

        {result && (
          <section id="analysis" className="analysis-section" aria-labelledby="analysis-title">
            <div className="analysis-heading">
              <div>
                <p className="eyebrow">Perceptual map · 02</p>
                <h2 id="analysis-title">The image, as geometry.</h2>
              </div>
              <button
                type="button"
                className="reset-focus"
                onClick={() => setActiveCluster(null)}
                disabled={activeCluster === null}
              >
                Show all clusters
              </button>
            </div>

            <dl className="result-stats">
              <div>
                <dt>source</dt>
                <dd>{result.image_size.width} × {result.image_size.height}px</dd>
              </div>
              <div>
                <dt>occupied bins</dt>
                <dd>{result.histogram_bins.toLocaleString()}</dd>
              </div>
              <div>
                <dt>points drawn</dt>
                <dd>{cloud?.displayed_bins.toLocaleString() ?? "—"}</dd>
              </div>
              <div>
                <dt>pixel weight shown</dt>
                <dd>{cloud ? `${(cloud.displayed_weight * 100).toFixed(1)}%` : "—"}</dd>
              </div>
            </dl>

            <div className="analysis-grid">
              <div className="viewer-panel">
                <div className="panel-label">
                  <span>CIELAB / D65</span>
                  <span>{cloud?.truncated ? "cluster-aware display subset" : "complete histogram"}</span>
                </div>
                {cloud ? (
                  <ColorSpaceViewer
                    result={result}
                    activeCluster={activeCluster}
                    onClusterSelect={(cluster) =>
                      setActiveCluster((current) => (current === cluster ? null : cluster))
                    }
                  />
                ) : (
                  <div className="viewer-loading">Visualization payload unavailable.</div>
                )}
              </div>

              <aside className="palette-panel" aria-labelledby="palette-title">
                <div className="panel-label">
                  <span id="palette-title">Extracted palette</span>
                  <span>ranked by pixel mass</span>
                </div>
                <div className="palette-list">
                  {result.palette.map((swatch) => (
                    <Swatch
                      key={swatch.rank}
                      swatch={swatch}
                      active={activeCluster === swatch.rank}
                      copied={copiedHex === swatch.hex}
                      onSelect={() =>
                        setActiveCluster((current) =>
                          current === swatch.rank ? null : swatch.rank,
                        )
                      }
                      onCopy={() => copyHex(swatch.hex)}
                    />
                  ))}
                </div>
                <p className="palette-note">
                  Select a swatch to isolate its assigned histogram bins. The outlined spheres are
                  k-means centroids; the smaller points are weighted image-color bins.
                </p>
              </aside>
            </div>
          </section>
        )}
      </main>

      <footer>
        <span>Hueclid · provably accessible color</span>
        <span>Current view: extraction geometry, not yet constrained ACCORD output.</span>
      </footer>
    </div>
  );
}
