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

/** Shown when fetch rejects before any HTTP response (offline, origin down, CORS). */
export const NETWORK_ERROR_MESSAGE =
  "Couldn't reach the server. Check your connection and try again.";

/** Map unknown thrown values to a stable, user-facing string. */
export function messageFromUnknownError(
  err: unknown,
  fallback = "Something went wrong",
): string {
  /* fetch rejects with TypeError when the request never yields a readable
     response. Browsers disagree on the wording ("Failed to fetch",
     "Load failed", …), so replace that with one message callers can show. */
  if (err instanceof TypeError) return NETWORK_ERROR_MESSAGE;
  if (err instanceof Error) return err.message;
  return fallback;
}

export async function extractPalette(file: File, k: number): Promise<ExtractResult> {
  const formData = new FormData();
  formData.append("file", file);

  let res: Response;
  try {
    res = await fetch(`${API_BASE}/api/v1/extract?k=${k}`, {
      method: "POST",
      body: formData,
    });
  } catch (err) {
    throw new Error(messageFromUnknownError(err));
  }

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Request failed with status ${res.status}`);
  }

  return res.json();
}
