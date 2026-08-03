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
}

const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export async function extractPalette(file: File, k: number): Promise<ExtractResult> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/v1/extract?k=${k}`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json();
}
