"use client";

import { useEffect, useState } from "react";
import { fetchAnomalies } from "@/lib/api";
import type { Insight, JournalLineSample } from "@/lib/types";

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

export default function AnomalySection() {
  const [items, setItems] = useState<Insight[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnomalies()
      .then(setItems)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <p className="empty-state">Loading anomaly findings...</p>;
  }

  if (error) {
    return <p className="error-state">Could not load anomaly findings: {error}</p>;
  }

  if (items.length === 0) {
    return <p className="empty-state">No suspicious booking text patterns detected.</p>;
  }

  return (
    <div className="findings">
      {items.map((item, index) => (
        <article className="finding" key={`${item.title}-${index}`}>
          <header className="finding-header">
            <strong>{item.title ?? "Anomaly finding"}</strong>
            {typeof item.confidence === "number" && (
              <span>{Math.round(item.confidence * 100)}%</span>
            )}
          </header>
          <p>{item.reason}</p>
          {item.explanation && <p className="muted">{item.explanation}</p>}
          {item.line_ids && item.line_ids.length > 0 && (
            <p className="finding-meta">Lines: {item.line_ids.join(", ")}</p>
          )}
          {typeof item.evidence_count === "number" && (
            <p className="finding-meta">Evidence: {item.evidence_count} similar postings</p>
          )}
          {item.affected_lines && item.affected_lines.length > 0 && (
            <div className="finding-samples">
              <span>Affected line</span>
              <ul>
                {item.affected_lines.map((line) => (
                  <LineSample line={line} key={`${line.document_id}-${line.line_id}`} />
                ))}
              </ul>
            </div>
          )}
          {item.evidence_examples && item.evidence_examples.length > 0 && (
            <div className="finding-samples">
              <span>Evidence examples</span>
              <ul>
                {item.evidence_examples.map((line) => (
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
