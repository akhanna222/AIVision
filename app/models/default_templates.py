"""
Default document templates for common document types across Ireland, UK, and US.
These templates serve as starting points and can be customized by users.
"""

from .templates import (
    DocumentTemplate,
    DocumentCategory,
    CountryCode,
    FieldDefinition,
    FieldType
)

# ============================================================================
# IRELAND TEMPLATES
# ============================================================================

IRELAND_MORTGAGE_APPLICATION = DocumentTemplate(
    template_id="ie_mortgage_app_v1",
    category=DocumentCategory.MORTGAGE_APPLICATION,
    country=CountryCode.IRELAND,
    template_name="Irish Mortgage Application Form",
    description="Standard mortgage application for Irish banks (AIB, BOI, PTSB, Permanent TSB)",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="applicant_name",
            field_name="Applicant Full Name",
            field_type=FieldType.TEXT,
            description="Primary applicant's full legal name",
            required=True,
            examples=["John Michael O'Brien", "Mary Kate Murphy"],
            extraction_hints="Usually in the first section, may be labeled as 'Name' or 'Applicant Name'"
        ),
        FieldDefinition(
            field_id="pps_number",
            field_name="PPS Number",
            field_type=FieldType.TEXT,
            description="Irish Personal Public Service Number (format: 7 digits + 1-2 letters)",
            required=True,
            validation_rules={"pattern": r"^\d{7}[A-Z]{1,2}$"},
            examples=["1234567A", "9876543WX"],
            extraction_hints="Format is 7 digits followed by 1 or 2 uppercase letters"
        ),
        FieldDefinition(
            field_id="date_of_birth",
            field_name="Date of Birth",
            field_type=FieldType.DATE,
            description="Applicant's date of birth",
            required=True,
            examples=["1985-03-15", "15/03/1985"],
            extraction_hints="May be in DD/MM/YYYY or YYYY-MM-DD format"
        ),
        FieldDefinition(
            field_id="phone_number",
            field_name="Contact Phone Number",
            field_type=FieldType.PHONE,
            description="Primary contact phone number",
            required=True,
            validation_rules={"pattern": r"^(\+353|0)[0-9]{8,9}$"},
            examples=["+353871234567", "0871234567"]
        ),
        FieldDefinition(
            field_id="email",
            field_name="Email Address",
            field_type=FieldType.EMAIL,
            description="Primary email address",
            required=True,
            validation_rules={"format": "email"}
        ),
        FieldDefinition(
            field_id="property_address",
            field_name="Property Address",
            field_type=FieldType.ADDRESS,
            description="Full address of property being mortgaged including Eircode",
            required=True,
            examples=["123 Main Street, Dublin 1, D01 XY45"],
            extraction_hints="Should include Eircode (Irish postal code)"
        ),
        FieldDefinition(
            field_id="property_value",
            field_name="Property Valuation",
            field_type=FieldType.CURRENCY,
            description="Estimated property value in EUR",
            required=True,
            validation_rules={"currency": "EUR", "min": 0},
            examples=["€450,000", "450000"]
        ),
        FieldDefinition(
            field_id="loan_amount",
            field_name="Loan Amount Requested",
            field_type=FieldType.CURRENCY,
            description="Mortgage amount requested in EUR",
            required=True,
            validation_rules={"currency": "EUR", "min": 0},
            examples=["€360,000", "360000"]
        ),
        FieldDefinition(
            field_id="ltv_ratio",
            field_name="Loan-to-Value Ratio",
            field_type=FieldType.PERCENTAGE,
            description="LTV percentage (max 90% for FTB, 80% for non-FTB in Ireland)",
            required=False,
            validation_rules={"min": 0, "max": 100},
            examples=["80%", "0.80"]
        ),
        FieldDefinition(
            field_id="employment_status",
            field_name="Employment Status",
            field_type=FieldType.TEXT,
            description="Current employment status",
            required=True,
            examples=["Permanent", "Contract", "Self-Employed", "Temporary"]
        ),
        FieldDefinition(
            field_id="employer_name",
            field_name="Employer Name",
            field_type=FieldType.TEXT,
            description="Current employer name",
            required=True
        ),
        FieldDefinition(
            field_id="annual_income",
            field_name="Gross Annual Income",
            field_type=FieldType.CURRENCY,
            description="Total gross annual income in EUR",
            required=True,
            validation_rules={"currency": "EUR", "min": 0}
        ),
        FieldDefinition(
            field_id="first_time_buyer",
            field_name="First Time Buyer",
            field_type=FieldType.BOOLEAN,
            description="Is applicant a first-time buyer?",
            required=True,
            examples=["Yes", "No", "True", "False"]
        ),
        FieldDefinition(
            field_id="term_years",
            field_name="Mortgage Term (Years)",
            field_type=FieldType.NUMBER,
            description="Requested mortgage term in years",
            required=True,
            validation_rules={"min": 1, "max": 40},
            examples=["25", "30", "35"]
        )
    ],
    tags=["mortgage", "ireland", "banking", "property"]
)

IRELAND_BANK_STATEMENT = DocumentTemplate(
    template_id="ie_bank_stmt_v1",
    category=DocumentCategory.BANK_STATEMENT,
    country=CountryCode.IRELAND,
    template_name="Irish Bank Statement",
    description="Bank statement from Irish financial institutions with IBAN and transaction details",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="account_holder",
            field_name="Account Holder Name",
            field_type=FieldType.TEXT,
            description="Name on the bank account",
            required=True
        ),
        FieldDefinition(
            field_id="iban",
            field_name="IBAN",
            field_type=FieldType.TEXT,
            description="Irish IBAN (starts with IE, 22 characters)",
            required=True,
            validation_rules={"pattern": r"^IE\d{2}[A-Z]{4}\d{14}$"},
            examples=["IE12BOFI90000112345678"]
        ),
        FieldDefinition(
            field_id="bic",
            field_name="BIC/SWIFT Code",
            field_type=FieldType.TEXT,
            description="Bank Identifier Code",
            required=False,
            examples=["BOFIIE2D", "AIBKIE2D"]
        ),
        FieldDefinition(
            field_id="account_number",
            field_name="Account Number",
            field_type=FieldType.TEXT,
            description="Bank account number",
            required=True
        ),
        FieldDefinition(
            field_id="statement_period_start",
            field_name="Statement Period Start",
            field_type=FieldType.DATE,
            description="Start date of statement period",
            required=True
        ),
        FieldDefinition(
            field_id="statement_period_end",
            field_name="Statement Period End",
            field_type=FieldType.DATE,
            description="End date of statement period",
            required=True
        ),
        FieldDefinition(
            field_id="opening_balance",
            field_name="Opening Balance",
            field_type=FieldType.CURRENCY,
            description="Balance at start of period in EUR",
            required=True,
            validation_rules={"currency": "EUR"}
        ),
        FieldDefinition(
            field_id="closing_balance",
            field_name="Closing Balance",
            field_type=FieldType.CURRENCY,
            description="Balance at end of period in EUR",
            required=True,
            validation_rules={"currency": "EUR"}
        ),
        FieldDefinition(
            field_id="total_credits",
            field_name="Total Credits",
            field_type=FieldType.CURRENCY,
            description="Sum of all credits in period",
            required=False,
            validation_rules={"currency": "EUR"}
        ),
        FieldDefinition(
            field_id="total_debits",
            field_name="Total Debits",
            field_type=FieldType.CURRENCY,
            description="Sum of all debits in period",
            required=False,
            validation_rules={"currency": "EUR"}
        )
    ],
    page_structure={
        "metadata_page": 1,
        "transactions_start_page": 1,
        "transactions_per_page": "variable"
    },
    tags=["bank", "statement", "ireland", "iban"]
)

# ============================================================================
# UK TEMPLATES
# ============================================================================

UK_MORTGAGE_APPLICATION = DocumentTemplate(
    template_id="gb_mortgage_app_v1",
    category=DocumentCategory.MORTGAGE_APPLICATION,
    country=CountryCode.UNITED_KINGDOM,
    template_name="UK Mortgage Application",
    description="Standard UK mortgage application (FCA compliant)",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="applicant_name",
            field_name="Applicant Full Name",
            field_type=FieldType.TEXT,
            description="Primary applicant's full legal name",
            required=True
        ),
        FieldDefinition(
            field_id="ni_number",
            field_name="National Insurance Number",
            field_type=FieldType.TEXT,
            description="UK NI Number (format: 2 letters, 6 digits, 1 letter)",
            required=True,
            validation_rules={"pattern": r"^[A-Z]{2}\d{6}[A-D]$"},
            examples=["AB123456C", "JK987654D"]
        ),
        FieldDefinition(
            field_id="date_of_birth",
            field_name="Date of Birth",
            field_type=FieldType.DATE,
            description="Applicant's date of birth",
            required=True
        ),
        FieldDefinition(
            field_id="phone_number",
            field_name="Contact Phone Number",
            field_type=FieldType.PHONE,
            description="UK phone number",
            required=True,
            validation_rules={"pattern": r"^(\+44|0)[0-9]{10}$"}
        ),
        FieldDefinition(
            field_id="email",
            field_name="Email Address",
            field_type=FieldType.EMAIL,
            description="Primary email address",
            required=True
        ),
        FieldDefinition(
            field_id="property_address",
            field_name="Property Address",
            field_type=FieldType.ADDRESS,
            description="Full UK address including postcode",
            required=True,
            examples=["10 Downing Street, London, SW1A 2AA"]
        ),
        FieldDefinition(
            field_id="property_value",
            field_name="Property Valuation",
            field_type=FieldType.CURRENCY,
            description="Property value in GBP",
            required=True,
            validation_rules={"currency": "GBP"}
        ),
        FieldDefinition(
            field_id="loan_amount",
            field_name="Loan Amount",
            field_type=FieldType.CURRENCY,
            description="Mortgage amount in GBP",
            required=True,
            validation_rules={"currency": "GBP"}
        ),
        FieldDefinition(
            field_id="deposit_amount",
            field_name="Deposit Amount",
            field_type=FieldType.CURRENCY,
            description="Deposit amount in GBP",
            required=True,
            validation_rules={"currency": "GBP"}
        ),
        FieldDefinition(
            field_id="term_years",
            field_name="Mortgage Term",
            field_type=FieldType.NUMBER,
            description="Mortgage term in years",
            required=True,
            validation_rules={"min": 1, "max": 40}
        ),
        FieldDefinition(
            field_id="employment_status",
            field_name="Employment Status",
            field_type=FieldType.TEXT,
            description="Employment type",
            required=True,
            examples=["Employed", "Self-Employed", "Retired"]
        ),
        FieldDefinition(
            field_id="annual_income",
            field_name="Gross Annual Income",
            field_type=FieldType.CURRENCY,
            description="Gross annual income in GBP",
            required=True,
            validation_rules={"currency": "GBP"}
        )
    ],
    tags=["mortgage", "uk", "fca", "property"]
)

# ============================================================================
# US TEMPLATES
# ============================================================================

US_MORTGAGE_APPLICATION = DocumentTemplate(
    template_id="us_mortgage_app_v1",
    category=DocumentCategory.MORTGAGE_APPLICATION,
    country=CountryCode.UNITED_STATES,
    template_name="US Uniform Residential Loan Application (Form 1003)",
    description="Fannie Mae Form 1003 - standard US mortgage application",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="borrower_name",
            field_name="Borrower Name",
            field_type=FieldType.TEXT,
            description="Primary borrower's full legal name",
            required=True
        ),
        FieldDefinition(
            field_id="ssn",
            field_name="Social Security Number",
            field_type=FieldType.TEXT,
            description="US SSN (format: XXX-XX-XXXX)",
            required=True,
            validation_rules={"pattern": r"^\d{3}-\d{2}-\d{4}$"},
            examples=["123-45-6789"]
        ),
        FieldDefinition(
            field_id="date_of_birth",
            field_name="Date of Birth",
            field_type=FieldType.DATE,
            description="Borrower's date of birth",
            required=True
        ),
        FieldDefinition(
            field_id="phone_number",
            field_name="Phone Number",
            field_type=FieldType.PHONE,
            description="Primary phone number",
            required=True,
            validation_rules={"pattern": r"^(\+1|1)?[0-9]{10}$"}
        ),
        FieldDefinition(
            field_id="email",
            field_name="Email Address",
            field_type=FieldType.EMAIL,
            description="Primary email address",
            required=True
        ),
        FieldDefinition(
            field_id="property_address",
            field_name="Subject Property Address",
            field_type=FieldType.ADDRESS,
            description="Full address of property including ZIP code",
            required=True,
            examples=["1600 Pennsylvania Avenue NW, Washington, DC 20500"]
        ),
        FieldDefinition(
            field_id="property_value",
            field_name="Purchase Price",
            field_type=FieldType.CURRENCY,
            description="Property purchase price in USD",
            required=True,
            validation_rules={"currency": "USD"}
        ),
        FieldDefinition(
            field_id="loan_amount",
            field_name="Loan Amount",
            field_type=FieldType.CURRENCY,
            description="Requested loan amount in USD",
            required=True,
            validation_rules={"currency": "USD"}
        ),
        FieldDefinition(
            field_id="down_payment",
            field_name="Down Payment",
            field_type=FieldType.CURRENCY,
            description="Down payment amount in USD",
            required=True,
            validation_rules={"currency": "USD"}
        ),
        FieldDefinition(
            field_id="loan_purpose",
            field_name="Loan Purpose",
            field_type=FieldType.TEXT,
            description="Purpose of loan",
            required=True,
            examples=["Purchase", "Refinance", "Construction", "Other"]
        ),
        FieldDefinition(
            field_id="property_type",
            field_name="Property Type",
            field_type=FieldType.TEXT,
            description="Type of property",
            required=True,
            examples=["Single Family", "Condominium", "Townhouse", "Cooperative"]
        ),
        FieldDefinition(
            field_id="occupancy",
            field_name="Occupancy Type",
            field_type=FieldType.TEXT,
            description="How property will be used",
            required=True,
            examples=["Primary Residence", "Secondary Residence", "Investment Property"]
        ),
        FieldDefinition(
            field_id="gross_monthly_income",
            field_name="Gross Monthly Income",
            field_type=FieldType.CURRENCY,
            description="Total gross monthly income in USD",
            required=True,
            validation_rules={"currency": "USD"}
        ),
        FieldDefinition(
            field_id="employment_status",
            field_name="Employment Status",
            field_type=FieldType.TEXT,
            description="Current employment status",
            required=True
        )
    ],
    tags=["mortgage", "usa", "form1003", "fanniemae"]
)

# ============================================================================
# UNIVERSAL TEMPLATES (PASSPORT, RECEIPT)
# ============================================================================

PASSPORT_UNIVERSAL = DocumentTemplate(
    template_id="passport_universal_v1",
    category=DocumentCategory.PASSPORT,
    country=CountryCode.IRELAND,  # Default, but works for all countries
    template_name="Universal Passport Extraction",
    description="MRZ-compliant passport data extraction for all countries",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="document_type",
            field_name="Document Type",
            field_type=FieldType.TEXT,
            description="Should be 'P' for passport",
            required=True,
            examples=["P"]
        ),
        FieldDefinition(
            field_id="country_code",
            field_name="Issuing Country",
            field_type=FieldType.TEXT,
            description="ISO 3166-1 alpha-3 country code",
            required=True,
            examples=["IRL", "GBR", "USA"]
        ),
        FieldDefinition(
            field_id="surname",
            field_name="Surname",
            field_type=FieldType.TEXT,
            description="Last name/surname as shown on passport",
            required=True
        ),
        FieldDefinition(
            field_id="given_names",
            field_name="Given Names",
            field_type=FieldType.TEXT,
            description="First and middle names",
            required=True
        ),
        FieldDefinition(
            field_id="passport_number",
            field_name="Passport Number",
            field_type=FieldType.TEXT,
            description="Unique passport number",
            required=True
        ),
        FieldDefinition(
            field_id="nationality",
            field_name="Nationality",
            field_type=FieldType.TEXT,
            description="Nationality of passport holder",
            required=True
        ),
        FieldDefinition(
            field_id="date_of_birth",
            field_name="Date of Birth",
            field_type=FieldType.DATE,
            description="Birth date in YYYY-MM-DD format",
            required=True
        ),
        FieldDefinition(
            field_id="sex",
            field_name="Sex",
            field_type=FieldType.TEXT,
            description="Gender (M/F/X)",
            required=True,
            examples=["M", "F", "X"]
        ),
        FieldDefinition(
            field_id="issue_date",
            field_name="Date of Issue",
            field_type=FieldType.DATE,
            description="Passport issue date",
            required=True
        ),
        FieldDefinition(
            field_id="expiry_date",
            field_name="Date of Expiry",
            field_type=FieldType.DATE,
            description="Passport expiry date",
            required=True
        ),
        FieldDefinition(
            field_id="place_of_birth",
            field_name="Place of Birth",
            field_type=FieldType.TEXT,
            description="City/country of birth",
            required=False
        )
    ],
    tags=["passport", "identity", "mrz", "travel"]
)

RECEIPT_UNIVERSAL = DocumentTemplate(
    template_id="receipt_universal_v1",
    category=DocumentCategory.RECEIPT,
    country=CountryCode.IRELAND,
    template_name="Universal Receipt Extraction",
    description="Universal receipt/expense extraction for all currencies",
    version="1.0.0",
    fields=[
        FieldDefinition(
            field_id="merchant_name",
            field_name="Merchant Name",
            field_type=FieldType.TEXT,
            description="Name of business/store",
            required=True
        ),
        FieldDefinition(
            field_id="merchant_address",
            field_name="Merchant Address",
            field_type=FieldType.ADDRESS,
            description="Store address",
            required=False
        ),
        FieldDefinition(
            field_id="transaction_date",
            field_name="Transaction Date",
            field_type=FieldType.DATE,
            description="Date of purchase",
            required=True
        ),
        FieldDefinition(
            field_id="transaction_time",
            field_name="Transaction Time",
            field_type=FieldType.TEXT,
            description="Time of purchase (HH:MM format)",
            required=False,
            examples=["14:35", "2:35 PM"]
        ),
        FieldDefinition(
            field_id="receipt_number",
            field_name="Receipt Number",
            field_type=FieldType.TEXT,
            description="Receipt/transaction ID",
            required=False
        ),
        FieldDefinition(
            field_id="subtotal",
            field_name="Subtotal",
            field_type=FieldType.CURRENCY,
            description="Subtotal before tax",
            required=False
        ),
        FieldDefinition(
            field_id="tax_amount",
            field_name="Tax Amount",
            field_type=FieldType.CURRENCY,
            description="Total tax amount",
            required=False
        ),
        FieldDefinition(
            field_id="total_amount",
            field_name="Total Amount",
            field_type=FieldType.CURRENCY,
            description="Final total amount paid",
            required=True
        ),
        FieldDefinition(
            field_id="payment_method",
            field_name="Payment Method",
            field_type=FieldType.TEXT,
            description="Method of payment",
            required=False,
            examples=["Cash", "Credit Card", "Debit Card", "Mobile Payment"]
        ),
        FieldDefinition(
            field_id="currency",
            field_name="Currency",
            field_type=FieldType.TEXT,
            description="Currency code",
            required=False,
            examples=["EUR", "GBP", "USD"]
        )
    ],
    tags=["receipt", "expense", "purchase"]
)

# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

DEFAULT_TEMPLATES = {
    # Ireland
    "ie_mortgage_app_v1": IRELAND_MORTGAGE_APPLICATION,
    "ie_bank_stmt_v1": IRELAND_BANK_STATEMENT,

    # UK
    "gb_mortgage_app_v1": UK_MORTGAGE_APPLICATION,

    # US
    "us_mortgage_app_v1": US_MORTGAGE_APPLICATION,

    # Universal
    "passport_universal_v1": PASSPORT_UNIVERSAL,
    "receipt_universal_v1": RECEIPT_UNIVERSAL,
}
