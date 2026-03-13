import base64
import hashlib
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()
LICENSE_SIGNING_SECRET = os.getenv("LICENSE_SIGNING_SECRET", "change-me")
NIR_RELEASE_URL = os.getenv(
    "NIR_RELEASE_URL", "https://github.com/phindagijimana/neuroinsight_research/releases"
)
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()]
if not ALLOWED_ORIGINS:
    ALLOWED_ORIGINS = ["https://phindagijimana.github.io"]

DATA_DIR = Path(__file__).resolve().parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
REQUEST_LOG = DATA_DIR / "license_requests.jsonl"

app = FastAPI(title="Inzira Labs License Service", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)


class LicenseRequest(BaseModel):
    requestedPlatform: str = Field(min_length=3, max_length=64)
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    institution: str = Field(min_length=2, max_length=200)
    purpose: str = Field(min_length=5, max_length=1500)
    source: str = Field(default="inzira-labs-landing", max_length=64)
    submittedAt: str


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def build_license_text(req: LicenseRequest) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(days=90)
    license_id = f"inzira-{uuid.uuid4()}"
    payload = {
        "license_id": license_id,
        "product": req.requestedPlatform,
        "name": req.name,
        "email": req.email,
        "institution": req.institution,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "source": req.source,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(
        LICENSE_SIGNING_SECRET.encode("utf-8"), canonical, hashlib.sha256
    ).hexdigest()

    return (
        "INZIRA_LABS_LICENSE_V1\n"
        f"license_id={license_id}\n"
        f"product={req.requestedPlatform}\n"
        f"name={req.name}\n"
        f"email={req.email}\n"
        f"institution={req.institution}\n"
        f"issued_at={issued_at.isoformat()}\n"
        f"expires_at={expires_at.isoformat()}\n"
        f"source={req.source}\n"
        f"signature={signature}\n"
    )


async def send_email_with_license(req: LicenseRequest, license_text: str) -> None:
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        raise RuntimeError("Email service is not configured.")

    attachment_name = f"license-{_slug(req.requestedPlatform)}.txt"
    encoded = base64.b64encode(license_text.encode("utf-8")).decode("utf-8")
    subject = f"Inzira Labs License - {req.requestedPlatform}"
    html = f"""
    <p>Hello {req.name},</p>
    <p>Your license request for <strong>{req.requestedPlatform}</strong> has been approved.</p>
    <p>Your license file is attached as <code>{attachment_name}</code>.</p>
    <p>You can now download NIR releases here:</p>
    <p><a href="{NIR_RELEASE_URL}">{NIR_RELEASE_URL}</a></p>
    <p>Regards,<br/>Inzira Labs</p>
    """

    body = {
        "from": RESEND_FROM_EMAIL,
        "to": [req.email],
        "subject": subject,
        "html": html,
        "attachments": [
            {
                "filename": attachment_name,
                "content": encoded,
            }
        ],
    }

    headers = {
        "Authorization": f"Bearer {RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post("https://api.resend.com/emails", headers=headers, json=body)
        if resp.status_code >= 300:
            raise RuntimeError(f"Resend error {resp.status_code}: {resp.text}")


def log_request(req: LicenseRequest, ok: bool, error: str = "") -> None:
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "email": req.email,
        "platform": req.requestedPlatform,
        "institution": req.institution,
        "ok": ok,
        "error": error,
    }
    with REQUEST_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.post("/api/license/request")
async def request_license(req: LicenseRequest) -> dict:
    try:
        license_text = build_license_text(req)
        await send_email_with_license(req, license_text)
        log_request(req, ok=True)
        return {
            "ok": True,
            "message": "License generated and emailed.",
            "download_url": NIR_RELEASE_URL,
        }
    except Exception as exc:  # noqa: BLE001
        log_request(req, ok=False, error=str(exc))
        raise HTTPException(status_code=502, detail=f"License dispatch failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        reload=False,
    )
