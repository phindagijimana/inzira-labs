import base64
import hashlib
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "").strip()
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "").strip()
LICENSE_SIGNING_SECRET = os.getenv("LICENSE_SIGNING_SECRET", "change-me")
NIR_RELEASE_URL = os.getenv(
    "NIR_RELEASE_URL", "https://github.com/phindagijimana/neuroinsight_research/releases"
)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "").strip()
GITHUB_REPO = os.getenv("GITHUB_REPO", "phindagijimana/neuroinsight_research").strip()
GITHUB_RELEASE_TAG = os.getenv("GITHUB_RELEASE_TAG", "latest").strip()
DOWNLOAD_LINK_BASE_URL = os.getenv("DOWNLOAD_LINK_BASE_URL", "").strip().rstrip("/")
DOWNLOAD_TOKEN_TTL_HOURS = int(os.getenv("DOWNLOAD_TOKEN_TTL_HOURS", "24"))
ASSET_NAME_ALLOWLIST = [
    s.strip()
    for s in os.getenv("ASSET_NAME_ALLOWLIST", "").split(",")
    if s.strip()
]

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


def _default_asset_allowed(name: str) -> bool:
    allowed_ext = (".appimage", ".deb", ".exe", ".msi", ".dmg", ".pkg", ".zip")
    return name.lower().endswith(allowed_ext)


def _token_b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _token_b64_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + pad).encode("utf-8"))


def _sign_payload(payload: bytes) -> bytes:
    return hmac.new(
        LICENSE_SIGNING_SECRET.encode("utf-8"), payload, hashlib.sha256
    ).digest()


def make_download_token(asset_id: int, filename: str, email: str) -> str:
    exp = int((datetime.now(timezone.utc) + timedelta(hours=DOWNLOAD_TOKEN_TTL_HOURS)).timestamp())
    payload: Dict[str, Any] = {
        "aid": int(asset_id),
        "fn": filename,
        "exp": exp,
        "eh": hashlib.sha256(email.lower().encode("utf-8")).hexdigest(),
    }
    raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = _sign_payload(raw)
    return f"{_token_b64_encode(raw)}.{_token_b64_encode(sig)}"


def parse_download_token(token: str) -> Dict[str, Any]:
    try:
        raw_part, sig_part = token.split(".", 1)
        raw = _token_b64_decode(raw_part)
        sig = _token_b64_decode(sig_part)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid download token format.") from exc

    expected_sig = _sign_payload(raw)
    if not hmac.compare_digest(sig, expected_sig):
        raise HTTPException(status_code=403, detail="Invalid download token signature.")

    try:
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail="Invalid download token payload.") from exc

    exp = int(payload.get("exp", 0))
    if exp < int(datetime.now(timezone.utc).timestamp()):
        raise HTTPException(status_code=410, detail="Download token has expired.")

    if "aid" not in payload or "fn" not in payload:
        raise HTTPException(status_code=400, detail="Download token missing required fields.")
    return payload


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
    download_links_html = ""
    secure_links = await build_secure_download_links(req.email)
    if secure_links:
        link_items = "\n".join(
            [f'<li><a href="{item["url"]}">{item["name"]}</a></li>' for item in secure_links]
        )
        download_links_html = f"""
        <p>Your secure private download links (valid for {DOWNLOAD_TOKEN_TTL_HOURS}h):</p>
        <ul>{link_items}</ul>
        """
    else:
        download_links_html = (
            f'<p>No private assets matched filters. Use releases page: '
            f'<a href="{NIR_RELEASE_URL}">{NIR_RELEASE_URL}</a></p>'
        )

    html = f"""
    <p>Hello {req.name},</p>
    <p>Your license request for <strong>{req.requestedPlatform}</strong> has been approved.</p>
    <p>Your license file is attached as <code>{attachment_name}</code>.</p>
    {download_links_html}
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


async def get_release_assets() -> List[Dict[str, Any]]:
    if not GITHUB_TOKEN:
        raise RuntimeError("GITHUB_TOKEN is required for private release downloads.")
    if "/" not in GITHUB_REPO:
        raise RuntimeError("GITHUB_REPO must be in 'owner/repo' format.")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_RELEASE_TAG.lower() == "latest":
        endpoint = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    else:
        endpoint = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{GITHUB_RELEASE_TAG}"

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(endpoint, headers=headers)
        if resp.status_code >= 300:
            raise RuntimeError(f"GitHub release lookup failed {resp.status_code}: {resp.text}")
        payload = resp.json()
    assets = payload.get("assets", [])
    out: List[Dict[str, Any]] = []
    for asset in assets if isinstance(assets, list) else []:
        name = str(asset.get("name", ""))
        if not name:
            continue
        if ASSET_NAME_ALLOWLIST:
            if name not in ASSET_NAME_ALLOWLIST:
                continue
        elif not _default_asset_allowed(name):
            continue
        out.append(
            {
                "id": int(asset.get("id")),
                "name": name,
                "size": int(asset.get("size", 0)),
            }
        )
    return out


async def build_secure_download_links(email: str) -> List[Dict[str, str]]:
    assets = await get_release_assets()
    links: List[Dict[str, str]] = []
    for asset in assets:
        token = make_download_token(asset["id"], asset["name"], email)
        if DOWNLOAD_LINK_BASE_URL:
            url = f"{DOWNLOAD_LINK_BASE_URL}/download/{token}"
        else:
            # Fallback for local use; set DOWNLOAD_LINK_BASE_URL in production.
            url = f"/download/{token}"
        links.append({"name": asset["name"], "url": url})
    return links


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


@app.get("/download/{token}")
async def download_private_asset(token: str) -> Response:
    payload = parse_download_token(token)
    asset_id = int(payload["aid"])
    filename = str(payload["fn"])
    if not GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured.")
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/octet-stream",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{asset_id}"
    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        resp = await client.get(url, headers=headers)
        if resp.status_code >= 300:
            raise HTTPException(
                status_code=502,
                detail=f"Could not fetch private asset from GitHub ({resp.status_code}).",
            )
        content_type = resp.headers.get("Content-Type", "application/octet-stream")
        return Response(
            content=resp.content,
            media_type=content_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Cache-Control": "no-store",
            },
        )


@app.post("/api/license/request")
async def request_license(req: LicenseRequest) -> dict:
    try:
        license_text = build_license_text(req)
        await send_email_with_license(req, license_text)
        log_request(req, ok=True)
        return {
            "ok": True,
            "message": "License generated and emailed with secure download links.",
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
