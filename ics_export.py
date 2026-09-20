import uuid
from datetime import date, datetime, timedelta


def _fold(line: str) -> str:
    # RFC5545 line length is a soft limit; skip folding for our short lines.
    return line


def build_ics(documents: list[dict], reminder_days_before: int = 14) -> bytes:
    """Build an .ics calendar file with one all-day reminder event per document,
    placed `reminder_days_before` days ahead of each document's expiry date."""

    now_stamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Document Expiry Reminder//EN",
        "CALSCALE:GREGORIAN",
    ]

    for doc in documents:
        expiry_str = doc.get("expiry_date")
        if not expiry_str:
            continue
        try:
            expiry = date.fromisoformat(expiry_str)
        except ValueError:
            continue

        reminder_date = expiry - timedelta(days=reminder_days_before)
        doc_type = doc.get("document_type", "Document")
        holder = doc.get("holder_name", "")
        summary = f"Renew {doc_type}" + (f" - {holder}" if holder else "")
        description = (
            f"Document: {doc_type}\\n"
            f"Holder: {holder}\\n"
            f"Number: {doc.get('document_number', '')}\\n"
            f"Expires: {expiry_str}\\n"
            f"Issued by: {doc.get('issuing_authority', '')}"
        )

        lines += [
            "BEGIN:VEVENT",
            f"UID:{uuid.uuid4()}@document-expiry-reminder",
            f"DTSTAMP:{now_stamp}",
            f"DTSTART;VALUE=DATE:{reminder_date.strftime('%Y%m%d')}",
            f"DTEND;VALUE=DATE:{(reminder_date + timedelta(days=1)).strftime('%Y%m%d')}",
            f"SUMMARY:{_fold(summary)}",
            f"DESCRIPTION:{_fold(description)}",
            "END:VEVENT",
        ]

    lines.append("END:VCALENDAR")
    return ("\r\n".join(lines) + "\r\n").encode("utf-8")
