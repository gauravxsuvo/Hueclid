# Hueclid 3D Viewer Foundation

This journal records the first implementation of Hueclid's interactive CIELAB viewer: what was
decided, why it was decided, what changed, and how the result was verified. It is intended to keep
the API and UI work understandable while the ACCORD model is still evolving.

## Scope and fixed decisions

- **Product name:** Hueclid.
- **Runtime architecture:** Next.js frontend with a FastAPI computation service.
- **Viewer purpose:** explain model output; it does not perform clustering or color conversion.
- **First displayed space:** CIELAB under D65, matching the current extraction model.
- **Compatibility rule:** existing API callers receive the original compact response unless they
  explicitly request visualization points.

The first release visualizes the existing weighted Lab k-means baseline. It must not be presented as
the future constrained ACCORD result. The UI calls this out in its footer.

## Implementation process

### 1. Define the data boundary before the scene

The prior endpoint returned only palette centroids. A useful color-space view also needs the occupied
histogram bins, their weights, and their assigned clusters. Rendering raw image pixels would be both
unnecessary and unbounded, so the API now exposes a versioned, optional visualization object.

Request parameters:

```text
include_points=true
max_points=4000
```

The maximum accepted value is 10,000 points. Omitting `include_points` preserves the earlier response
shape and cost.

### 2. Make point selection deterministic and cluster-aware

When the histogram contains fewer points than the requested limit, every occupied bin is returned.
When it is larger:

1. reserve a small quota for the heaviest bins in every cluster;
2. fill the remaining budget with the heaviest bins across the whole image;
3. use original bin indices as a deterministic tie-breaker;
4. report the fraction of original pixel weight represented by the returned subset.

This is deliberately different from random pixel sampling. A small brand-color cluster cannot vanish
solely because a global top-N list was dominated by the background.

### 3. Version the viewer schema

The additive response object is validated by Pydantic:

```json
{
  "visualization": {
    "schema_version": 1,
    "space": "cielab-d65",
    "axes": { "x": "a*", "y": "L*", "z": "b*" },
    "points": [
      {
        "lab": [53.2, 28.1, -61.4],
        "rgb": [83, 111, 220],
        "weight": 0.0042,
        "cluster": 2
      }
    ],
    "total_bins": 6184,
    "displayed_bins": 4000,
    "displayed_weight": 0.973,
    "truncated": true
  }
}
```

`cluster` refers to the public palette rank, not scikit-learn's internal cluster index. This matters
because the public palette is reordered by descending pixel mass.

### 4. Build one GPU point cloud, not thousands of React meshes

The frontend uses React Three Fiber 9 with Three.js. Histogram-bin positions and vertex colors are
packed into one `BufferGeometry` and rendered in one point-cloud draw path. Only the palette
centroids—at most twelve—use individual sphere meshes.

Coordinate mapping:

```text
x = a* / 55
y = (L* - 50) / 25
z = b* / 55
```

This keeps the real Lab relationships while fitting typical sRGB coordinates comfortably into the
camera view. Point colors use the returned sRGB values; Lab coordinates are never treated as RGB.

The canvas uses on-demand rendering, orbit controls, bounded zoom, a ground grid, axis lines, hover
readouts, and cluster isolation. The adjacent palette list exposes the same clusters to keyboard and
screen-reader users, because the WebGL canvas is explanatory rather than the only data interface.

### 5. Establish a visual language

The interface direction is a scientific instrument presented like an editorial color study:

- warm paper and ink-black analysis surfaces;
- graph-paper structure rather than decorative gradients;
- Newsreader for expressive display type;
- IBM Plex Sans and Mono for controls and measurements;
- Hueclid coral and blue for axes and state;
- restrained motion with a reduced-motion mode.

The upload control now implements the drag-and-drop behavior it advertises. Requests can be aborted,
old results are cleared when a new source is selected, client-side file checks mirror the backend,
and result status is announced through a live region.

### 6. Verify with real output, not only fixtures

The first rendered extraction exposed a preprocessing bug that the flat-color tests did not cover.
Lanczos resizing can overshoot below zero and above one around sharp edges. Those non-physical linear
RGB values produced an impossible negative L* centroid in the viewer. The resize path now clamps its
result to `[0, 1]`, and a regression test uses a high-contrast edge that reproduces the ringing.

The same pass also improved the upload target: the native file input now covers the full drop zone and
receives a visible keyboard-focus outline. Three.js is pinned to r182 because React Three Fiber 9 still
uses `THREE.Clock`; r183 and later deprecate it and emit a warning until the renderer updates upstream.

During collaborator setup, the Next.js 16 Turbopack development server also produced an incomplete
React Client Manifest for both `app/page.tsx` and Next's built-in global error component. A cold run of
the same application under Webpack returned HTTP 200 normally, while optimized Turbopack production
builds continued to pass. `npm run dev` therefore uses Webpack for a reliable local feedback loop, and
`npm run dev:turbo` keeps the upstream path available for periodic retesting.

## Files introduced or changed

- `backend/app/api/schemas.py` — typed, versioned response models.
- `backend/app/api/extract.py` — viewer query parameters and response validation.
- `backend/app/clustering/kmeans.py` — cluster-aware point selection and payload construction.
- `frontend/app/components/ColorSpaceViewer.tsx` — R3F scene and accessible readout.
- `frontend/app/components/Swatch.tsx` — cluster focus and copy controls.
- `frontend/app/page.tsx` — upload workflow and results workspace.
- `frontend/app/globals.css` — full responsive visual system.
- `frontend/app/lib/api.ts` — viewer types and abortable request.

## Verification record

The required checks are:

```bash
cd backend
ruff check .
ruff format --check .
pytest -q

cd ../frontend
npm run lint
npx tsc --noEmit
npm run build
```

Rendered verification must cover:

- initial desktop and mobile layouts;
- click-to-upload and actual drag-and-drop behavior;
- a complete extraction against the local FastAPI service;
- orbit, zoom, point hover, cluster isolation, and reset;
- long filenames, 12-swatch palettes, and a truncated point cloud;
- no horizontal overflow or clipped controls at narrow widths;
- browser console errors.

### Completed verification — 2026-08-03

- Backend: Ruff lint and format checks passed; `56` Pytest tests passed. The suite reports one
  dependency-level Starlette/httpx deprecation warning.
- Frontend: ESLint, `tsc --noEmit`, and the optimized Next.js production build passed on Node 24
  against the declared Node 22+ runtime floor.
- End to end: the 1200 × 630 Hueclid banner uploaded through the native file control, FastAPI returned
  251 occupied bins, and the WebGL scene rendered all 251 with 100% represented pixel weight.
- Interaction: selecting the blue swatch activated its pressed state and isolated cluster 4; **Show
  all clusters** reset the view.
- Responsive layout: the default desktop viewport and a 390 × 844 mobile viewport were inspected.
  At 390px the document width equaled the viewport width, the stats collapsed to two columns, and the
  viewer and palette stacked without horizontal overflow.
- Browser diagnostics: a fresh production run completed with no console warnings or errors after the
  Three.js compatibility pin.
- Bounded payload: a 12-cluster API request with `max_points=100` returned exactly 100 of 251 bins,
  included every cluster, set `truncated=true`, represented 99.78% of pixel weight, and kept L* in the
  physical 0–100 range.

Still to exercise in a later visual-regression pass: a real drag-and-drop gesture (click upload is
verified), pointer orbit/zoom/hover automation, an unusually long filename, and the 12-swatch/truncated
states in the rendered UI. Their underlying handlers and API path are implemented and covered by the
checks above, but they are not recorded here as visually verified.

## Known limitations and next model work

1. The visible centroids still come from Euclidean Lab k-means, not CIEDE2000 k-medoids.
2. Lab-to-sRGB output still hard-clips out-of-gamut centroids. A verified Oklch gamut mapper should
   land before constrained palette repair.
3. The point payload contains rounded JSON objects. A future high-density viewer could negotiate a
   compact binary format, but 4,000 points is intentionally small enough that this is not necessary
   yet.
4. EXIF orientation, alpha compositing, and embedded ICC profiles still need explicit preprocessing.
5. The viewer contract is versioned so future ACCORD candidates, role assignments, constraint edges,
   before/after paths, or uncertainty metadata can be added without redefining version 1 points.

The next model-facing contribution should implement WCAG/APCA diagnostics and a typed role graph.
Those outputs can then appear as edges and role markers in the same scene without coupling the viewer
to solver internals.
