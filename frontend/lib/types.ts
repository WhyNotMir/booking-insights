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
  type?: string;
  title?: string;
  reason?: string;
  explanation?: string;
  validation_check?: string;
  confidence?: number;
  evidence_count?: number;
  line_ids?: string[];
  affected_lines?: JournalLineSample[];
  evidence_examples?: JournalLineSample[];
  expected_gl_account?: string;
  actual_gl_account?: string;
}

export interface DuplicateCandidate {
  type?: string;
  title?: string;
  confidence: number;
  evidence_count?: number;
  criteria: string[];
  lines: JournalLineSample[];
}

export interface JournalLineSample {
  document_id: string;
  line_id: number;
  posting_date: string;
  gl_account: string;

  cost_center?: string | null;
  vendor_id?: string | null;
  customer_id?: string | null;
  tax_code?: string | null;

  amount: number;
  currency: string;
  debit_credit: "D" | "C" | "S" | "H";
  booking_text: string;
}
