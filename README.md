<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand/banner-wide-dark.svg">
  <img src="brand/banner-wide.svg" alt="Hueclid">
</picture>

[![CI](https://github.com/gauravxsuvo/Hueclid/actions/workflows/ci.yml/badge.svg)](https://github.com/gauravxsuvo/Hueclid/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Hueclid generates accessible color palettes from images. Give it a screenshot or a photo and it produces a set of colors that actually work as a UI design system: a background, a surface color, text colors, a primary action color, a danger color, and so on, all checked against each other for contrast, not just checked one at a time against a neutral background.

## The idea

Most palette generators pull five or six dominant colors out of an image and call it done. That's a fine start, but it misses the part that actually matters for a design system: colors don't get used in isolation. Your body text sits on your background, but it also sits on your card surfaces. Your button label sits on your button color. Each of those pairings has its own contrast requirement, and satisfying one can quietly break another.

Hueclid treats this as what it actually is: a constrained optimization problem. You give it a role graph, background, surface, text, primary, danger, and the contrast thresholds each pair needs to clear (using APCA, not the older WCAG 2 contrast ratio, which has known blind spots around color polarity and saturation). Hueclid then searches for a palette that stays faithful to the image's actual colors while satisfying every constraint in that graph at once, and it can prove when no such palette exists rather than silently producing something that fails one of the edges.

The algorithm behind this is called ACCORD. Hueclid is the name of the tool built on top of it.

## Where this stands right now

This is an early-stage project, built openly and in phases rather than all at once. The current state:

- The core color math is implemented and verified: sRGB to CIELAB conversion, and CIEDE2000 color difference, both vectorized in NumPy and checked against the published Sharma et al. (2005) reference test data, all 34 pairs passing to within 1e-4.
- Round-trip conversion has been property-tested across 10,000 random colors with a maximum error well under one part in a million.
- Lab-space histogram binning and a weighted k-means palette extractor are implemented and verified against a real test image with known color regions.
- A working API (FastAPI) and a working web page (Next.js) exist, and have been tested together end to end: upload an image, get back a ranked, weighted palette.
- The web app includes an interactive 3D CIELAB viewer backed by a versioned, bounded API payload: weighted histogram bins, cluster assignments, and palette centroids can be inspected without sending raw pixels to the browser.
- Not deployed publicly. That's deliberate for now: the project runs and gets tested entirely on localhost while it's being built, and public hosting is a separate step that happens once the work is further along.

For the color-science background and reasoning behind the approach, see `math-explained/` and `blueprint/`.

## Why this approach

Two prior projects do related work. Colorgorical optimizes perceptual distance and pairwise preference for categorical visualization palettes. Palettailor does data-aware palette generation via optimization. Both are worth reading before assuming this is untouched ground.

What's different here is the combination of three things: treating APCA as a hard constraint inside the generation process rather than a filter applied afterward, generating typed design-system roles with a directed constraint graph rather than a flat set of mutually distinguishable colors, and solving the constrained selection step exactly (via CP-SAT) rather than through stochastic search, so the result is either provably correct or provably infeasible, with a clear answer for which constraint is the problem when it is infeasible.

## Prerequisites

- Python 3.12
- Node.js 22 or newer

Check the versions that your shell will use before creating an environment:

```bash
python3.12 --version
node --version
```

## Run and test locally

### 1. Start the FastAPI backend

From `backend/` on macOS or Linux:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest
python -m uvicorn app.main:app --reload --port 8000
```

On Windows PowerShell, create and activate the environment with:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

Keep this terminal running. The API is available at `http://localhost:8000`; verify it in another
terminal with:

```bash
curl http://localhost:8000/health
```

The expected response is `{"status":"ok"}`.

### 2. Start the Next.js frontend

Open a second terminal and run from `frontend/`:

```bash
npm install
npm run dev
```

The development command uses Webpack because the current Next.js 16 Turbopack dev server can emit
an incomplete React Client Manifest for the client-only 3D viewer. Production builds are unaffected.
`npm run dev:turbo` remains available for retesting Turbopack after dependency updates.

Open `http://localhost:3000`. Upload a PNG, JPEG, or WebP image, choose 2–12 clusters, and select
**Map color space**. A successful smoke test shows the ranked palette and interactive 3D CIELAB
point cloud; selecting a swatch should isolate its cluster and **Show all clusters** should reset it.

The frontend points at the local API by default. To use a different backend, copy
`.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL`.

### 3. Run all development checks

Backend, from `backend/` with the Python 3.12 environment active:

```bash
python -m ruff check .
python -m ruff format --check .
python -m pytest
```

Frontend, from `frontend/`:

```bash
npm run lint
npx tsc --noEmit
npm run build
```

If pytest reports that it cannot evaluate `VisualizationPayload | None`, the existing virtual
environment was created with an older Python. Deactivate it, move or remove `.venv`, then recreate it
with `python3.12 -m venv .venv` as shown above.

The viewer's API contract, point-selection rules, implementation process, and verification checklist are documented in [`docs/3d-viewer-foundation.md`](docs/3d-viewer-foundation.md).

## Contributing

Contributions are welcome, this is early enough that there's real room to shape it. See `CONTRIBUTING.md` for setup details, the one convention that actually matters (verifying color math against a reference, not just your own derivation), and how to propose larger changes. Please also read `CODE_OF_CONDUCT.md`.

## License

MIT. See `LICENSE`.
