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
- Not deployed publicly. That's deliberate for now: the project runs and gets tested entirely on localhost while it's being built, and public hosting is a separate step that happens once the work is further along.

For the color-science background and reasoning behind the approach, see `math-explained/` and `blueprint/`.

## Why this approach

Two prior projects do related work. Colorgorical optimizes perceptual distance and pairwise preference for categorical visualization palettes. Palettailor does data-aware palette generation via optimization. Both are worth reading before assuming this is untouched ground.

What's different here is the combination of three things: treating APCA as a hard constraint inside the generation process rather than a filter applied afterward, generating typed design-system roles with a directed constraint graph rather than a flat set of mutually distinguishable colors, and solving the constrained selection step exactly (via CP-SAT) rather than through stochastic search, so the result is either provably correct or provably infeasible, with a clear answer for which constraint is the problem when it is infeasible.

## Setup

The backend is Python. From `backend/`:

```
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe -m pytest
.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
```

That installs NumPy, scikit-learn, Pillow, FastAPI, and the test tooling, runs the full test suite, and starts the API on `http://localhost:8000`.

The frontend is Next.js. From `frontend/`:

```
npm install
npm run dev
```

That starts the web app on `http://localhost:3000`, pointed at the local API by default. To point it at a different backend, copy `.env.local.example` to `.env.local` and set `NEXT_PUBLIC_API_BASE_URL`.

## Contributing

Contributions are welcome, this is early enough that there's real room to shape it. See `CONTRIBUTING.md` for setup details, the one convention that actually matters (verifying color math against a reference, not just your own derivation), and how to propose larger changes. Please also read `CODE_OF_CONDUCT.md`.

## License

MIT. See `LICENSE`.
