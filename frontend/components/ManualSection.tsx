"use client";

import { useEffect, useState } from "react";
import { fetchManual } from "@/lib/api";
import type { Insight, JournalLineSample } from "@/lib/types";

function EvidenceLine({ line }: { line: JournalLineSample }) {
  return (
    <li>
      <code>{line.document_id}/{line.line_id}</code>
      <span>{line.posting_date}</span>
      <span>G/L {line.gl_account}</span>
      <strong>
        {line.amount.toFixed(2)} {line.currency} {line.debit_credit}
      </strong>
      <span>{line.booking_text}</span>
      <span>{line.cost_center}</span>
      <span>{line.vendor_id}</span>
      <span>{line.tax_code}</span>
    </li>
  );
}

export default function ManualSection() {
  const [items, setItems] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchManual()
      .then(setItems)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="empty-state">Loading booking rules...</p>;
  }

  if (error) {
    return <p className="error-state">Could not load booking rules: {error}</p>;
  }

  if (items.length === 0) {
    return <p className="empty-state">No booking rules derived yet.</p>;
  }

  return (
    <div className="findings">
      {items.map((item, index) => (
        <article className="finding" key={`${item.title}-${index}`}>
          <header className="finding-header">
            <strong>{item.title ?? "Booking rule"}</strong>
            {typeof item.confidence === "number" && (
              <span>{Math.round(item.confidence * 100)}%</span>
            )}
          </header>
          {item.validation_check && <p>{item.validation_check}</p>}
          {item.explanation && <p className="muted">{item.explanation}</p>}
          {item.evidence_examples && item.evidence_examples.length > 0 && (
            <div className="finding-samples">
              <span>Evidence examples</span>
              <ul>
                {item.evidence_examples.map((line) => (
                  <EvidenceLine line={line} key={`${line.document_id}-${line.line_id}`} />
                ))}
              </ul>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
