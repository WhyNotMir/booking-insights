"use client";

import { useEffect, useState } from "react";
import { fetchEntries } from "@/lib/api";
import type { JournalLine } from "@/lib/types";

export default function BookingTable() {
  const [entries, setEntries] = useState<JournalLine[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEntries()
      .then(setEntries)
      .catch((err: Error) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="empty-state">Loading entries...</p>;
  if (error) return <p className="error-state">Could not load entries: {error}</p>;
  if (entries.length === 0) return <p className="empty-state">No journal entries loaded yet.</p>;

  return (
    <table>
      <thead>
        <tr>
          <th>Date</th>
          <th>Document</th>
          <th>Line</th>
          <th>Account</th>
          <th>D/C</th>
          <th>Amount</th>
          <th>Text</th>
        </tr>
      </thead>
      <tbody>
        {entries.slice(0, 50).map((entry) => (
          <tr key={`${entry.document_id}-${entry.line_id}`}>
            <td>{entry.posting_date}</td>
            <td>{entry.document_id}</td>
            <td>{entry.line_id}</td>
            <td>{entry.gl_account}</td>
            <td>{entry.debit_credit}</td>
            <td>{entry.amount.toFixed(2)} {entry.currency}</td>
            <td>{entry.booking_text}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
