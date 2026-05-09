"use client";

import { useEffect, useState } from "react";
import { fetchManual } from "@/lib/api";
import type { Insight } from "@/lib/types";

export default function ManualSection() {
  const [items, setItems] = useState<Insight[]>([]);

  useEffect(() => {
    fetchManual().then(setItems);
  }, []);

  if (items.length === 0) {
    return <p className="empty-state">No booking rules derived yet.</p>;
  }

  return <pre>{JSON.stringify(items, null, 2)}</pre>;
}
