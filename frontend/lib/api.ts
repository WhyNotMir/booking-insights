import type { DuplicateCandidate, Insight, JournalLine } from "./types";

async function get<T>(path: string): Promise<T> {
  const response = await fetch(`/api${path}`, { cache: "no-store" });

  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`);
  }

  return response.json();
}

export const fetchEntries = () => get<JournalLine[]>("/entries");
export const fetchAnomalies = () => get<Insight[]>("/insights/anomalies");
export const fetchDuplicates = () => get<DuplicateCandidate[]>("/insights/duplicates");
export const fetchManual = () => get<Insight[]>("/insights/manual");
