"use client";

import { useEffect, useState } from "react";
import { fetchDuplicates } from "@/lib/api";
import type { DuplicateCandidate, JournalLineSample } from "@/lib/types";

function LineSample({ line }: { line: JournalLineSample }) {
  return (
    <li>
      <code>{line.document_id}/{line.line_id}</code>
      <span>{line.posting_date}</span>
      <span>G/L {line.gl_account}</span>
      <strong>
        {line.amount.toFixed(2)} {line.currency} {line.debit_credit}
      </strong>
      <span>{line.booking_text}</span>
    </li>
  );
}

export default function DuplicateSection() {
  const [items, setItems] = useState<DuplicateCandidate[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDuplicates()
      .then(setItems)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="empty-state">Loading duplicate candidates...</p>;
  }

  if (error) {
    return <p className="error-state">Could not load duplicate candidates: {error}</p>;
  }

  if (items.length === 0) {
    return <p className="empty-state">No duplicate candidates above threshold.</p>;
  }

  return (
    <div className="findings">
      {items.map((item, index) => (
        <article className="finding" key={`${item.title}-${index}`}>
          <header className="finding-header">
            <strong>{item.title ?? "Possible duplicate posting"}</strong>
            {typeof item.confidence === "number" && (
              <span>{Math.round(item.confidence * 100)}%</span>
            )}
          </header>
          <p className="muted">Matched on: {item.criteria.join(" · ")}</p>
          {typeof item.evidence_count === "number" && (
            <p className="finding-meta">
              Evidence: {item.evidence_count} matching line-pair
              {item.evidence_count === 1 ? "" : "s"}
            </p>
          )}
          {item.lines.length > 0 && (
            <div className="finding-samples">
              <span>Posting lines</span>
              <ul>
                {item.lines.map((line) => (
                  <LineSample line={line} key={`${line.document_id}-${line.line_id}`} />
                ))}
              </ul>
            </div>
          )}
        </article>
      ))}
    </div>
  );
}
