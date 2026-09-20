import base64
import io
import json
import os

from groq import Groq
from PIL import Image

# Groq's current vision-capable model (multimodal, text + image input)
MODEL_NAME = "qwen/qwen3.8-27b"

PROMPT = """You are a document-tracking assistant for Indian consumers and small businesses.
Look at this photo of a document and extract the key details needed to track its expiry.

Common document types include: PUC (Pollution Under Control) certificate, vehicle insurance,
driving licence, passport, FSSAI licence, GST registration certificate, fixed deposit (FD)
receipt, RC (registration certificate), AMC/warranty card, rent agreement, or any other
document with a validity/expiry date.

Report:
- document_type: your best guess at what kind of document this is (e.g. "Vehicle Insurance",
  "Driving Licence", "Passport", "FSSAI Licence", "GST Registration", "FD Receipt")
- holder_name: the name of the person/entity the document belongs to, if visible
- document_number: the policy/licence/registration number if visible, else empty string
- issue_date: issue/start date in YYYY-MM-DD format if visible, else null
- expiry_date: expiry/validity-until/maturity date in YYYY-MM-DD format. This is the most
  important field — look carefully for "valid until", "expiry", "valid upto", "maturity date",
  etc. If you truly cannot find any expiry date, use null.
- issuing_authority: who issued the document, if visible, else empty string
- notes: anything else useful (e.g. "premium amount", "coverage type"), 1 short sentence, or
  empty string

Respond with ONLY valid JSON matching this shape, no markdown fences:
{
  "document_type": str,
  "holder_name": str,
  "document_number": str,
  "issue_date": str | null,
  "expiry_date": str | null,
  "issuing_authority": str,
  "notes": str
}
"""


def _get_client() -> Groq:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Groq(api_key=api_key)


def _image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG")
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def extract_document(image: Image.Image) -> dict:
    client = _get_client()
    data_url = _image_to_data_url(image)

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": PROMPT},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        response_format={"type": "json_object"},
        reasoning_effort="none",
        temperature=0.2,
    )

    return json.loads(response.choices[0].message.content)
