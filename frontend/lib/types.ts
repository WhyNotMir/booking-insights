export interface JournalLine {
  company_code: string;
  posting_date: string;
  document_id: string;
  line_id: number;
  gl_account: string;
  amount: number;
  currency: string;
  debit_credit: "D" | "C" | "S" | "H";
  booking_text: string;
  cost_center?: string | null;
  vendor_id?: string | null;
  customer_id?: string | null;
  tax_code?: string | null;
}

export interface Insight {
  title?: string;
  reason?: string;
  explanation?: string;
  confidence?: number;
  evidence_count?: number;
  line_ids?: string[];
}

export interface DuplicateCandidate {
  confidence: number;
  criteria: string[];
  lines: JournalLine[];
}
