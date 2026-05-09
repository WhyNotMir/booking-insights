from datetime import date
from typing import Literal

from pydantic import BaseModel


class JournalLine(BaseModel):
    company_code: str
    posting_date: date
    document_id: str
    line_id: int
    gl_account: str
    amount: float
    currency: str
    debit_credit: Literal["D", "C", "S", "H"]
    booking_text: str
    cost_center: str | None = None
    vendor_id: str | None = None
    customer_id: str | None = None
    tax_code: str | None = None
