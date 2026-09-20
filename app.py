import io
import uuid
from datetime import date

import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image

from ics_export import build_ics
from storage import load_documents, save_documents
from vision import extract_document

load_dotenv()

st.set_page_config(
    page_title="Document Expiry Reminder",
    page_icon=":material/event:",
    layout="wide",
    initial_sidebar_state="expanded",
)

CUSTOM_CSS = """
<style>
    #MainMenu, footer, header {visibility: hidden;}

    .block-container {
        padding-top: 0;
        padding-bottom: 3rem;
        max-width: 1250px;
    }

    .hero {
        position: relative;
        overflow: hidden;
        background:
            radial-gradient(700px 420px at 30% 100%, rgba(255,255,255,0.55), transparent 60%),
            radial-gradient(600px 400px at 15% 80%, rgba(249,115,22,0.55), transparent 60%),
            radial-gradient(650px 450px at 75% 90%, rgba(56,189,248,0.45), transparent 60%),
            #05070c;
        border-radius: 20px;
        padding: 3.2rem 2.25rem 3.6rem 2.25rem;
        margin: 1.5rem 0 2rem 0;
        color: white;
        text-align: center;
    }
    .hero-eyebrow {
        display: inline-block;
        font-size: 0.78rem;
        color: #e5e7eb;
        background: rgba(255,255,255,0.08);
        border: 1px solid rgba(255,255,255,0.18);
        border-radius: 999px;
        padding: 0.4rem 1.1rem;
        margin-bottom: 1.4rem;
    }
    .hero h1 {
        margin: 0 auto 0.6rem auto;
        max-width: 640px;
        font-family: Georgia, 'Times New Roman', serif;
        font-weight: 500;
        font-size: 2.7rem;
        line-height: 1.15;
        color: white;
    }
    .hero p {
        margin: 0 auto;
        max-width: 480px;
        opacity: 0.85;
        font-size: 1rem;
        line-height: 1.6;
    }

    .platform-section { padding: 0.5rem 0 2rem 0; }
    .platform-eyebrow {
        font-size: 0.82rem; font-weight: 600; color: #6b7280; margin-bottom: 0.5rem;
    }
    .platform-title {
        font-family: Georgia, 'Times New Roman', serif;
        font-weight: 500;
        font-size: 2rem;
        margin: 0 0 0.4rem 0;
    }
    .platform-sub { color: #6b7280; font-size: 0.92rem; margin-bottom: 1.6rem; max-width: 560px; }

    .feature-grid { display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 2.5rem; }
    .feature-card { flex: 1; min-width: 180px; }
    .feature-thumb {
        height: 90px; border-radius: 12px; margin-bottom: 0.7rem;
        display: flex; align-items: center; justify-content: center;
    }
    .feature-thumb .material-symbols-outlined { font-size: 2rem; color: white; }
    .feature-thumb.f1 { background: linear-gradient(135deg, #05070c 0%, #f97316 55%, #38bdf8 100%); }
    .feature-thumb.f2 { background: linear-gradient(135deg, #1e3a8a 0%, #38bdf8 100%); }
    .feature-thumb.f3 { background: linear-gradient(135deg, #05070c 0%, #7c3aed 55%, #f97316 100%); }
    .feature-thumb.f4 { background: linear-gradient(135deg, #052e17 0%, #16a34a 100%); }
    .feature-card .ftitle { font-weight: 700; font-size: 0.95rem; margin-bottom: 0.3rem; }
    .feature-card .fdesc { font-size: 0.82rem; color: #6b7280; line-height: 1.5; }

    div[data-testid="stMetric"] {
        background: var(--secondary-background-color);
        border: 1px solid rgba(128,128,128,0.18);
        border-radius: 12px;
        padding: 0.9rem 1rem 0.7rem 1rem;
    }
    div[data-testid="stMetricLabel"] { font-size: 0.85rem; opacity: 0.75; }

    .upload-card {
        border: 1px solid rgba(128,128,128,0.18);
        border-radius: 14px;
        padding: 1.25rem;
        background: var(--secondary-background-color);
    }

    .doc-card {
        border: 1px solid rgba(128,128,128,0.18);
        border-left: 4px solid #7c3aed;
        border-radius: 10px;
        padding: 0.9rem 1rem;
        margin-bottom: 0.75rem;
        background: var(--secondary-background-color);
    }
    .doc-card.expired { border-left-color: #dc2626; }
    .doc-card.critical { border-left-color: #ea580c; }
    .doc-card.warning { border-left-color: #ca8a04; }
    .doc-card.ok { border-left-color: #16a34a; }

    .doc-card .title { font-weight: 700; font-size: 1.02rem; margin-bottom: 0.25rem; }
    .doc-card .meta { font-size: 0.82rem; opacity: 0.75; margin-bottom: 0.4rem; }

    .badge {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
    }
    .badge-expired { background: #fee2e2; color: #991b1b; }
    .badge-critical { background: #ffedd5; color: #9a3412; }
    .badge-warning { background: #fef3c7; color: #92400e; }
    .badge-ok { background: #dcfce7; color: #166534; }
    .badge-unknown { background: #e5e7eb; color: #374151; }

    section[data-testid="stFileUploaderDropzone"] { border-radius: 12px; }

    .stButton > button { border-radius: 10px; font-weight: 600; height: 2.7rem; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

st.markdown(
    """
    <div class="hero">
        <span class="hero-eyebrow">10+ document types &middot; one calendar file</span>
        <h1>Never Let a Document<br>Expire Again</h1>
        <p>Upload documents once — AI reads the expiry date automatically. Track PUC,
        insurance, licences, passports, FSSAI, GST, FDs, and more in one place.</p>
    </div>
    <div class="platform-section">
        <div class="platform-eyebrow">&#9635; Our Platform</div>
        <div class="platform-title">Track Every Renewal Date</div>
        <div class="platform-sub">One vault for every document you own — scanned once, checked automatically, and reminders sent before it's too late.</div>
        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-thumb f1"><span class="material-symbols-outlined">photo_camera</span></div>
                <div class="ftitle">Scan</div>
                <div class="fdesc">Photograph any document — AI reads type, holder, number, and expiry date.</div>
            </div>
            <div class="feature-card">
                <div class="feature-thumb f2"><span class="material-symbols-outlined">folder</span></div>
                <div class="ftitle">Vault</div>
                <div class="fdesc">Every scan is saved locally, sorted by urgency, editable if the AI misreads a field.</div>
            </div>
            <div class="feature-card">
                <div class="feature-thumb f3"><span class="material-symbols-outlined">calendar_month</span></div>
                <div class="ftitle">Reminders</div>
                <div class="fdesc">Generates a .ics calendar file — one reminder event per document, days before it expires.</div>
            </div>
            <div class="feature-card">
                <div class="feature-thumb f4"><span class="material-symbols-outlined">download</span></div>
                <div class="ftitle">Export</div>
                <div class="fdesc">Pull the full vault into Excel or CSV whenever you need a record.</div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


def status_for(expiry_date: str | None) -> tuple[str, str, int | None, str]:
    """Returns (status_label, css_class, days_left, timeline_text)"""
    if not expiry_date:
        return "Unknown", "unknown", None, "Unknown"
    try:
        expiry = date.fromisoformat(expiry_date)
    except ValueError:
        return "Unknown", "unknown", None, "Unknown"
    days_left = (expiry - date.today()).days
    if days_left < 0:
        days_ago = abs(days_left)
        timeline = f"Expired {days_ago} day{'s' if days_ago != 1 else ''} ago"
        return "Expired", "expired", days_left, timeline
    timeline = f"{days_left} day{'s' if days_left != 1 else ''} left"
    if days_left <= 30:
        return "Expiring soon", "critical", days_left, timeline
    if days_left <= 90:
        return "Renew soon", "warning", days_left, timeline
    return "Valid", "ok", days_left, timeline


if "documents" not in st.session_state:
    st.session_state.documents = load_documents()

with st.sidebar:
    st.markdown("### Settings")
    reminder_days = st.slider(
        "Remind me this many days before expiry",
        min_value=1,
        max_value=60,
        value=14,
        help="Used when generating the calendar reminder file",
    )

    st.markdown("---")
    st.markdown(
        "**Who this is for**\n\n"
        "Individuals tracking PUC/insurance/licence renewals, small business owners "
        "tracking FSSAI/GST validity, and fleet operators tracking multiple vehicle "
        "documents at once."
    )
    st.markdown("---")
    st.caption(f"{len(st.session_state.documents)} document(s) saved in your vault.")

left, right = st.columns([1, 1.4], gap="large")

with left:
    st.markdown("#### Upload documents")
    uploaded_files = st.file_uploader(
        "Document photos",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        new_files = [
            f for f in uploaded_files
            if not any(d.get("_source") == f.name for d in st.session_state.documents.values())
        ]
        st.caption(f"{len(uploaded_files)} file(s) selected, {len(new_files)} not yet scanned.")

        scan_clicked = st.button("Scan documents", icon=":material/auto_awesome:", type="primary", use_container_width=True)

        if scan_clicked and new_files:
            progress = st.progress(0.0, text="Reading documents...")
            for i, file in enumerate(new_files):
                image = Image.open(file).convert("RGB")
                doc_id = str(uuid.uuid4())
                try:
                    doc = extract_document(image)
                    doc["_source"] = file.name
                    doc["_error"] = False
                except Exception as exc:
                    doc = {
                        "document_type": "Error",
                        "holder_name": "",
                        "document_number": "",
                        "issue_date": None,
                        "expiry_date": None,
                        "issuing_authority": "",
                        "notes": str(exc),
                        "_source": file.name,
                        "_error": True,
                    }
                st.session_state.documents[doc_id] = doc
                progress.progress((i + 1) / len(new_files), text=f"Scanned {file.name}")
            progress.empty()
            save_documents(st.session_state.documents)
            st.rerun()
    else:
        st.markdown(
            '<div class="upload-card">Drop document photos above — PUC, insurance, '
            "driving licence, passport, FSSAI, GST certificate, FD receipt, etc. Each "
            "document only needs to be scanned once.</div>",
            unsafe_allow_html=True,
        )

    st.markdown("#### Manage vault")
    if st.session_state.documents:
        options = {
            f"{d.get('document_type', 'Document')} — {d.get('holder_name') or d.get('_source', doc_id)}": doc_id
            for doc_id, d in st.session_state.documents.items()
        }
        to_delete = st.multiselect("Select documents to remove", list(options.keys()))
        if st.button("Remove selected", icon=":material/delete:", use_container_width=True, disabled=not to_delete):
            for label in to_delete:
                st.session_state.documents.pop(options[label], None)
            save_documents(st.session_state.documents)
            st.rerun()
    else:
        st.caption("No documents in your vault yet.")

with right:
    st.markdown("#### Document vault")

    docs = st.session_state.documents
    valid_docs = {k: v for k, v in docs.items() if not v.get("_error")}
    error_docs = {k: v for k, v in docs.items() if v.get("_error")}

    if not docs:
        st.info("Scanned documents will appear here.")
    else:
        rows = []
        for doc_id, d in valid_docs.items():
            label, css_class, days_left, timeline = status_for(d.get("expiry_date"))
            rows.append(
                {
                    "_id": doc_id,
                    "Type": d.get("document_type", ""),
                    "Holder": d.get("holder_name", ""),
                    "Number": d.get("document_number", ""),
                    "Expires": d.get("expiry_date") or "",
                    "Days left": days_left if days_left is not None else "",
                    "Timeline": timeline,
                    "Status": label,
                    "_css": css_class,
                    "Authority": d.get("issuing_authority", ""),
                    "Notes": d.get("notes", ""),
                }
            )

        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values(
                by="Days left", key=lambda s: pd.to_numeric(s, errors="coerce").fillna(1e9)
            )

        expired = (df["Status"] == "Expired").sum() if not df.empty else 0
        expiring_soon = (df["Status"] == "Expiring soon").sum() if not df.empty else 0
        valid = (df["Status"] == "Valid").sum() if not df.empty else 0

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Documents", len(df))
        m2.metric("Expired", int(expired))
        m3.metric("Due soon", int(expiring_soon), help="Expiring within 30 days")
        m4.metric("Valid", int(valid))

        if error_docs:
            st.error(f"{len(error_docs)} document(s) failed to scan — see Errors tab.")

        tab_table, tab_cards, tab_edit, tab_reminders, tab_errors = st.tabs(
            ["Table", "Cards", "Edit vault", "Reminders", "Errors"]
        )

        with tab_table:
            if df.empty:
                st.info("No valid documents yet.")
            else:
                show_df = df.drop(columns=["_id", "_css", "Days left"])

                def highlight_status(row):
                    colors = {
                        "Expired": "background-color:#fee2e2; color:#991b1b; font-weight:600;",
                        "Expiring soon": "background-color:#ffedd5; color:#9a3412; font-weight:600;",
                        "Renew soon": "background-color:#fef3c7; color:#92400e; font-weight:600;",
                        "Valid": "background-color:#dcfce7; color:#166534; font-weight:600;",
                        "Unknown": "background-color:#e5e7eb; color:#374151; font-weight:600;",
                    }
                    style = colors.get(row["Status"], "")
                    idx = list(row.index).index("Status")
                    styles = [""] * len(row)
                    styles[idx] = style
                    return styles

                st.dataframe(
                    show_df.style.apply(highlight_status, axis=1),
                    use_container_width=True,
                    hide_index=True,
                )

                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
                    show_df.to_excel(writer, index=False, sheet_name="Documents")
                excel_buffer.seek(0)

                c1, c2 = st.columns(2)
                c1.download_button(
                    "Download as Excel",
                    excel_buffer,
                    file_name="document_vault.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    icon=":material/download:",
                    use_container_width=True,
                )
                c2.download_button(
                    "Download as CSV",
                    show_df.to_csv(index=False).encode("utf-8"),
                    file_name="document_vault.csv",
                    mime="text/csv",
                    icon=":material/download:",
                    use_container_width=True,
                )

        with tab_cards:
            if df.empty:
                st.info("No valid documents yet.")
            for _, row in df.iterrows():
                st.markdown(
                    f"""
                    <div class="doc-card {row['_css']}">
                        <div class="title">{row['Type']} {f"— {row['Holder']}" if row['Holder'] else ''}</div>
                        <div class="meta">
                            <span class="badge badge-{row['_css']}">{row['Status']}</span>
                            &nbsp; Expires: {row['Expires'] or 'Unknown'} · {row['Timeline']}
                        </div>
                        <div><b>Number:</b> {row['Number'] or '—'}</div>
                        <div><b>Authority:</b> {row['Authority'] or '—'}</div>
                        <div><b>Notes:</b> {row['Notes'] or '—'}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with tab_edit:
            if df.empty:
                st.info("No valid documents yet.")
            else:
                st.caption(
                    "Correct anything the AI misread — especially the expiry date, since "
                    "that's what drives reminders. Click into a cell to edit, then save."
                )

                edit_source = df[
                    ["_id", "Type", "Holder", "Number", "Expires", "Authority", "Notes"]
                ].copy()
                edit_source["Expires"] = edit_source["Expires"].apply(
                    lambda v: date.fromisoformat(v) if v else None
                )

                edited_df = st.data_editor(
                    edit_source,
                    use_container_width=True,
                    hide_index=True,
                    num_rows="fixed",
                    column_order=["Type", "Holder", "Number", "Expires", "Authority", "Notes"],
                    column_config={
                        "Expires": st.column_config.DateColumn(format="YYYY-MM-DD"),
                    },
                    key="vault_editor",
                )

                if st.button("Save changes", icon=":material/save:", type="primary", use_container_width=True):
                    for row in edited_df.to_dict("records"):
                        doc_id = row["_id"]
                        if doc_id not in st.session_state.documents:
                            continue
                        expires = row["Expires"]
                        st.session_state.documents[doc_id].update(
                            {
                                "document_type": row["Type"],
                                "holder_name": row["Holder"],
                                "document_number": row["Number"],
                                "expiry_date": expires.isoformat() if expires else None,
                                "issuing_authority": row["Authority"],
                                "notes": row["Notes"],
                            }
                        )
                    save_documents(st.session_state.documents)
                    st.success("Changes saved.")
                    st.rerun()

        with tab_reminders:
            docs_with_expiry = [d for d in valid_docs.values() if d.get("expiry_date")]
            if not docs_with_expiry:
                st.info("No documents with a detected expiry date yet.")
            else:
                st.caption(
                    f"Generates one calendar reminder per document, {reminder_days} day(s) "
                    "before its expiry date. Import the file into Google Calendar, Outlook, "
                    "or your phone's calendar app."
                )
                ics_bytes = build_ics(docs_with_expiry, reminder_days_before=reminder_days)
                st.download_button(
                    "Download calendar reminders (.ics)",
                    ics_bytes,
                    file_name="document_reminders.ics",
                    mime="text/calendar",
                    icon=":material/download:",
                    use_container_width=True,
                    type="primary",
                )

        with tab_errors:
            if not error_docs:
                st.success("No errors.")
            for d in error_docs.values():
                st.markdown(f"**{d.get('_source')}**: {d.get('notes')}")
