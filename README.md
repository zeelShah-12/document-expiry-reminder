# Document Expiry Reminder

Most people find out a PUC certificate, vehicle insurance, or FSSAI licence has expired only
when they're fined or turned away — because nobody tracks a stack of paper documents with
different renewal dates. **Document Expiry Reminder** fixes that:

- Upload a photo of any document once — PUC, vehicle insurance, driving licence, passport,
  FSSAI licence, GST registration, FD receipt, RC, AMC/warranty, rent agreement, etc.
- AI reads the document type, holder name, document number, and — most importantly — the
  **expiry/validity date**.
- Every scanned document is saved to a persistent local vault (`data/documents.json`), so it
  only needs to be scanned once, ever.
- Color-coded status (Expired / Expiring soon / Renew soon / Valid) sorted by urgency.
- Generates a **.ics calendar file** with one reminder event per document, N days before
  expiry — import it into Google Calendar, Outlook, or your phone to get notified.
- Export the full vault to Excel or CSV.

**Who pays:** Individual consumers (₹99–199/year), small business owners tracking FSSAI/GST
validity (₹499–999/year), fleet companies tracking many vehicles' documents at once
(₹5,000/month).

## Stack

- **Streamlit** — single-file UI
- **Groq** (`qwen/qwen3.8-27b`) — vision analysis, extracts structured document data
- **Pandas + openpyxl** — vault table + Excel export
- **Plain-text `.ics` generation** — no external calendar library needed, works with any
  calendar app that supports the iCalendar standard

## Local setup

```bash
cd "9 project"
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY (free at console.groq.com)
streamlit run app.py
```

Runs on `http://localhost:8501`.

## Project structure

```
9 project/
├── app.py              Streamlit UI — upload, vault table, cards, reminders, export
├── vision.py            Groq Vision call + prompt/schema for document extraction
├── storage.py            Simple JSON-file persistence for the document vault
├── ics_export.py         Builds a standards-compliant .ics calendar file, no dependency
├── data/                 documents.json lives here (created on first scan)
├── sample_images/        (drop demo document photos here for testing)
├── requirements.txt
└── .env.example
```

## Notes for the portfolio writeup

- The vault persists across app restarts via a flat JSON file — a real deployment would swap
  this for a per-user database row, but the interface (`load_documents`/`save_documents`) is
  already isolated in `storage.py` so that's a drop-in change.
- Calendar reminders are generated as a downloadable `.ics` file rather than push
  notifications — no backend/cron job needed, and it works with every major calendar app.
- Uses `reasoning_effort="none"` on the Groq call — required for reliable JSON output with
  this model (see project 7/8 for details on why).
