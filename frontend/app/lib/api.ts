export interface Swatch {
  rank: number;
  hex: string;
  rgb: [number, number, number];
  lab: [number, number, number];
  weight: number;
}

export interface ExtractResult {
  palette: Swatch[];
  k: number;
  image_size: { width: number; height: number };
  histogram_bins: number;
  visualization?: VisualizationPayload;
}

export interface VisualizationPoint {
  lab: [number, number, number];
  rgb: [number, number, number];
  weight: number;
  cluster: number;
}

export interface VisualizationPayload {
  schema_version: 1;
  space: "cielab-d65";
  axes: { x: "a*"; y: "L*"; z: "b*" };
  points: VisualizationPoint[];
  total_bins: number;
  displayed_bins: number;
  displayed_weight: number;
  truncated: boolean;
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function extractPalette(
  file: File,
  k: number,
  signal?: AbortSignal,
): Promise<ExtractResult> {
  const formData = new FormData();
  formData.append("file", file);

  const params = new URLSearchParams({
    k: String(k),
    include_points: "true",
    max_points: "4000",
  });

  const res = await fetch(`${API_BASE}/api/v1/extract?${params}`, {
    method: "POST",
    body: formData,
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json();
}
