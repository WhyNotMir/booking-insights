"use client";

import { useEffect, useState } from "react";
import { fetchAnomalies } from "@/lib/api";
import type { Insight } from "@/lib/types";

export default function AnomalySection() {
  const [items, setItems] = useState<Insight[]>([]);

  useEffect(() => {
    fetchAnomalies().then(setItems);
  }, []);

  if (items.length === 0) {
    return <p className="empty-state">No anomaly detection results yet.</p>;
  }

  return <pre>{JSON.stringify(items, null, 2)}</pre>;
}
