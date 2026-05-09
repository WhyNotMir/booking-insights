"""
Generate synthetic accounting journal entry data for an international hotel group.

Accounting assumptions:
- One JSON object represents one journal entry line.
- document_id connects multiple lines into one accounting document.
- Positive amount = debit, negative amount = credit.
- Every document balances to zero in EUR.
- VAT is simplified to V20, V10, and EXEMPT.
- Expense postings: expense/VAT receivable debit, accounts payable credit.
- Revenue postings: accounts receivable debit, revenue/VAT payable credit.
- The G/L accounts are SAP-like sample accounts, not a real chart of accounts.
"""

import json
import random
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path


random.seed(42)

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 2, 28)
OUTPUT_PATH = Path("app/data/journal_entries.json")
CURRENCY = "EUR"

# Journal entry schema:
# one row is one accounting line item inside a multi-line document.
SCHEMA_FIELDS = [
    "company_code",
    "posting_date",
    "document_id",
    "line_id",
    "gl_account",
    "cost_center",
    "amount",
    "currency",
    "debit_credit",
    "booking_text",
    "vendor_id",
    "customer_id",
    "tax_code",
]

COMPANY_CODES = ["AT01", "DE01", "NL01", "IT01", "ES01"]
CUSTOMERS = [
    "CUST_DIRECT_001",
    "CUST_CORPORATE_002",
    "CUST_TRAVEL_AGENCY_003",
    "CUST_EVENT_004",
    "CUST_RESTAURANT_005",
]

GL = {
    "bank": "100000",
    "accounts_receivable": "110000",
    "vat_receivable": "140000",
    "accounts_payable": "210000",
    "vat_payable": "220000",
    "room_revenue": "400000",
    "restaurant_revenue": "410000",
    "conference_revenue": "420000",
    "spa_revenue": "430000",
    "cleaning_expense": "500000",
    "laundry_expense": "510000",
    "utilities_expense": "520000",
    "software_expense": "530000",
    "maintenance_expense": "540000",
    "marketing_expense": "550000",
    "booking_platform_fees": "560000",
    "food_supplies": "570000",
    "legal_expense": "580000",
    "office_supplies": "590000",
    "staff_costs": "600000",
    "bank_fees": "610000",
    "insurance_expense": "620000",
    "training_expense": "630000",
    "travel_expense": "640000",
    "security_expense": "650000",
}

EXPENSE_TEMPLATES = [
    ("Laundry Services", GL["laundry_expense"], "HOUSEKEEPING", "VEND_LAUNDRY_001", "V20", 200, 1200),
    ("Cleaning Services", GL["cleaning_expense"], "HOUSEKEEPING", "VEND_CLEANING_002", "V20", 300, 2000),
    ("Electricity Invoice", GL["utilities_expense"], "HOTEL_OPERATIONS", "VEND_ENERGY_003", "V20", 800, 5000),
    ("Software Subscription", GL["software_expense"], "IT", "VEND_SOFTWARE_004", "V20", 100, 900),
    ("Maintenance Invoice", GL["maintenance_expense"], "HOTEL_OPERATIONS", "VEND_MAINT_005", "V20", 500, 3000),
    ("Food Supplies", GL["food_supplies"], "RESTAURANT", "VEND_FOOD_006", "V10", 400, 2500),
    ("Office Supplies", GL["office_supplies"], "ADMIN", "VEND_OFFICE_007", "V20", 50, 600),
    ("Booking Platform Commission", GL["booking_platform_fees"], "SALES_MARKETING", "VEND_BOOKING_008", "V20", 100, 1800),
    ("Marketing Campaign", GL["marketing_expense"], "SALES_MARKETING", "VEND_MARKETING_009", "V20", 300, 4000),
    ("Legal Consulting", GL["legal_expense"], "ADMIN", "VEND_LEGAL_010", "V20", 500, 5000),
    ("Monthly Payroll", GL["staff_costs"], "HOTEL_OPERATIONS", "VEND_PAYROLL_011", "EXEMPT", 5000, 18000),
    ("Bank Charges", GL["bank_fees"], "FINANCE", "VEND_BANK_012", "EXEMPT", 20, 250),
    ("Insurance Premium", GL["insurance_expense"], "ADMIN", "VEND_INSURANCE_013", "EXEMPT", 600, 4500),
    ("Staff Training", GL["training_expense"], "ADMIN", "VEND_TRAINING_014", "V20", 300, 2500),
    ("Business Travel", GL["travel_expense"], "SALES_MARKETING", "VEND_TRAVEL_015", "V20", 150, 1800),
    ("Security Services", GL["security_expense"], "HOTEL_OPERATIONS", "VEND_SECURITY_016", "V20", 400, 2800),
]

REVENUE_TEMPLATES = [
    ("Room Revenue", GL["room_revenue"], "HOTEL_OPERATIONS", "CUST_DIRECT_001", "V10", 150, 3000),
    ("Restaurant Revenue", GL["restaurant_revenue"], "RESTAURANT", "CUST_RESTAURANT_005", "V10", 80, 1500),
    ("Conference Revenue", GL["conference_revenue"], "CONFERENCE", "CUST_EVENT_004", "V20", 500, 7000),
    ("Spa Revenue", GL["spa_revenue"], "SPA", "CUST_DIRECT_001", "V20", 50, 800),
]

TAX_RATES = {"V20": 0.20, "V10": 0.10, "EXEMPT": 0.00}


def random_date():
    return START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))


def debit_credit(amount):
    return "D" if amount > 0 else "C"


# Create one journal entry line with the same schema everywhere.
def line(company_code, posting_date, document_id, line_id, gl_account, cost_center,
         amount, booking_text, vendor_id=None, customer_id=None, tax_code="EXEMPT"):
    return {
        "company_code": company_code,
        "posting_date": posting_date.isoformat(),
        "document_id": document_id,
        "line_id": line_id,
        "gl_account": gl_account,
        "cost_center": cost_center,
        "amount": round(amount, 2),
        "currency": CURRENCY,
        "debit_credit": debit_credit(amount),
        "booking_text": booking_text,
        "vendor_id": vendor_id,
        "customer_id": customer_id,
        "tax_code": tax_code,
    }


# Build one balanced expense document:
# expense + VAT receivable debit, accounts payable credit.
def expense_document(document_id, template=None):
    text, account, cost_center, vendor_id, tax_code, min_amount, max_amount = template or random.choice(EXPENSE_TEMPLATES)
    company_code = random.choice(COMPANY_CODES)
    posting_date = random_date()
    net = round(random.uniform(min_amount, max_amount), 2)
    tax = round(net * TAX_RATES[tax_code], 2)
    gross = round(net + tax, 2)

    lines = [
        line(company_code, posting_date, document_id, 1, account, cost_center, net, text, vendor_id=vendor_id, tax_code=tax_code),
    ]
    if tax:
        lines.append(line(company_code, posting_date, document_id, 2, GL["vat_receivable"], cost_center, tax, f"{text} VAT", vendor_id=vendor_id, tax_code=tax_code))
    lines.append(line(company_code, posting_date, document_id, len(lines) + 1, GL["accounts_payable"], cost_center, -gross, f"{text} Payable", vendor_id=vendor_id, tax_code=tax_code))
    return lines


# Build one balanced revenue document:
# receivable debit, revenue + VAT payable credit.
def revenue_document(document_id, template=None):
    text, account, cost_center, customer_id, tax_code, min_amount, max_amount = template or random.choice(REVENUE_TEMPLATES)
    company_code = random.choice(COMPANY_CODES)
    posting_date = random_date()
    net = round(random.uniform(min_amount, max_amount), 2)
    tax = round(net * TAX_RATES[tax_code], 2)
    gross = round(net + tax, 2)

    return [
        line(company_code, posting_date, document_id, 1, GL["accounts_receivable"], cost_center, gross, f"{text} Receivable", customer_id=customer_id, tax_code=tax_code),
        line(company_code, posting_date, document_id, 2, account, cost_center, -net, text, customer_id=customer_id, tax_code=tax_code),
        line(company_code, posting_date, document_id, 3, GL["vat_payable"], cost_center, -tax, f"{text} VAT", customer_id=customer_id, tax_code=tax_code),
    ]


# Build a mixed revenue document with several revenue line items.
def mixed_revenue_document(document_id):
    company_code = random.choice(COMPANY_CODES)
    posting_date = random_date()
    customer_id = random.choice(CUSTOMERS)
    room = round(random.uniform(500, 2500), 2)
    restaurant = round(random.uniform(100, 800), 2)
    spa = round(random.uniform(50, 400), 2)
    net = round(room + restaurant + spa, 2)
    tax = round(net * TAX_RATES["V10"], 2)
    gross = round(net + tax, 2)

    return [
        line(company_code, posting_date, document_id, 1, GL["accounts_receivable"], "HOTEL_OPERATIONS", gross, "Hotel Guest Invoice", customer_id=customer_id, tax_code="V10"),
        line(company_code, posting_date, document_id, 2, GL["room_revenue"], "HOTEL_OPERATIONS", -room, "Room Revenue", customer_id=customer_id, tax_code="V10"),
        line(company_code, posting_date, document_id, 3, GL["restaurant_revenue"], "RESTAURANT", -restaurant, "Restaurant Revenue", customer_id=customer_id, tax_code="V10"),
        line(company_code, posting_date, document_id, 4, GL["spa_revenue"], "SPA", -spa, "Spa Revenue", customer_id=customer_id, tax_code="V10"),
        line(company_code, posting_date, document_id, 5, GL["vat_payable"], "FINANCE", -tax, "Guest Invoice VAT", customer_id=customer_id, tax_code="V10"),
    ]


# Add suspicious cases on top of otherwise normal accounting templates.
def inject_suspicious_cases(rows):
    for row in rows:
        if row["booking_text"] == "Software Subscription":
            row["booking_text"] = "Sofware Subscription"
            break

    for row in rows:
        if row["booking_text"] == "Office Supplies":
            row["booking_text"] = "Office Supply Invoice"
            break

    for row in rows:
        if row["booking_text"] == "Maintenance Invoice":
            row["booking_text"] = "Maintenence Invoice"
            break

    source_documents = sorted({row["document_id"] for row in rows})
    for duplicate_index, source_document in enumerate(random.sample(source_documents, 3), start=1):
        duplicate_document = [row.copy() for row in rows if row["document_id"] == source_document]
        duplicate_document_id = f"DOC999{duplicate_index}"
        day_shift = duplicate_index
        for row in duplicate_document:
            row["document_id"] = duplicate_document_id
            posting_date = date.fromisoformat(row["posting_date"])
            shifted_date = posting_date + timedelta(days=day_shift)
            if shifted_date > END_DATE:
                shifted_date = posting_date - timedelta(days=day_shift)
            row["posting_date"] = shifted_date.isoformat()
            rows.append(row)

    for row in rows:
        if row["booking_text"] == "Room Revenue":
            row["gl_account"] = GL["legal_expense"]
            break


# Validate accounting consistency and suspicious-case coverage.
def validate(rows):
    required_fields = set(SCHEMA_FIELDS)
    assert all(required_fields == set(row) for row in rows), "Unexpected schema"
    assert 200 <= len(rows) <= 800, "Dataset size outside required range"

    documents = defaultdict(list)
    for row in rows:
        documents[row["document_id"]].append(row)

    assert all(len(lines) >= 2 for lines in documents.values()), "Found document with less than 2 lines"
    assert all(round(sum(row["amount"] for row in lines), 2) == 0 for lines in documents.values()), "Found unbalanced document"

    dates = [date.fromisoformat(row["posting_date"]) for row in rows]
    assert min(dates) >= START_DATE and max(dates) <= END_DATE, "Date outside expected range"
    assert (max(dates) - min(dates)).days >= 50, "Date coverage is shorter than roughly two months"

    gl_count = len({row["gl_account"] for row in rows})
    assert gl_count >= 20, "Not enough unique G/L accounts"

    texts = Counter(row["booking_text"] for row in rows)
    assert texts["Sofware Subscription"] >= 1, "Missing typo suspicious case"
    assert texts["Office Supply Invoice"] >= 1, "Missing near-duplicate suspicious case"
    assert texts["Maintenence Invoice"] >= 1, "Missing second typo suspicious case"
    duplicate_document_ids = {"DOC9991", "DOC9992", "DOC9993"}
    assert duplicate_document_ids.issubset(documents), "Missing possible duplicate postings"
    assert any(row["booking_text"] == "Room Revenue" and row["gl_account"] == GL["legal_expense"] for row in rows), "Missing unusual account/text combination"


# Generate documents first, then flatten their line items into rows.
def generate_rows():
    rows = []
    document_number = 1
    generators = {
        "expense": expense_document,
        "revenue": revenue_document,
        "mixed_revenue": mixed_revenue_document,
    }

    # Force each template to appear at least once so the generated file always
    # satisfies the required G/L account diversity.
    for template in EXPENSE_TEMPLATES:
        rows.extend(expense_document(f"DOC{1000 + document_number}", template))
        document_number += 1

    for template in REVENUE_TEMPLATES:
        rows.extend(revenue_document(f"DOC{1000 + document_number}", template))
        document_number += 1

    while document_number <= 140:
        document_id = f"DOC{1000 + document_number}"
        document_type = random.choices(
            ["expense", "revenue", "mixed_revenue"],
            weights=[55, 30, 15],
            k=1,
        )[0]

        rows.extend(generators[document_type](document_id))

        document_number += 1

    inject_suspicious_cases(rows)
    validate(rows)
    return rows


def main():
    rows = generate_rows()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    dates = [row["posting_date"] for row in rows]
    print(f"Dataset rows: {len(rows)}")
    print(f"Unique documents: {len({row['document_id'] for row in rows})}")
    print(f"Date range: {min(dates)} -> {max(dates)}")
    print(f"Unique GL accounts: {len({row['gl_account'] for row in rows})}")
    print(f"Dataset saved to: {OUTPUT_PATH}")
    print("Validation passed.")


if __name__ == "__main__":
    main()
