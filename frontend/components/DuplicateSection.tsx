"use client";

import { useEffect, useState } from "react";
import { fetchDuplicates } from "@/lib/api";
import type { DuplicateCandidate } from "@/lib/types";

export default function DuplicateSection() {
  const [items, setItems] = useState<DuplicateCandidate[]>([]);

  useEffect(() => {
    fetchDuplicates().then(setItems);
  }, []);

  if (items.length === 0) {
    return <p className="empty-state">No duplicate detection results yet.</p>;
  }

  return <pre>{JSON.stringify(items, null, 2)}</pre>;
}
