import base64
import csv
import hashlib
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
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
ACTIVITY_CSV = DATA_DIR / "license_activity.csv"

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
    targetOS: str = Field(pattern="^(linux|windows|macos)$")
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    institution: str = Field(min_length=2, max_length=200)
    purpose: str = Field(min_length=5, max_length=1500)
    source: str = Field(default="inzira-labs-landing", max_length=64)
    submittedAt: str


CSV_HEADERS = [
    "ts",
    "event",
    "ok",
    "email",
    "email_hash",
    "platform",
    "target_os",
    "institution",
    "source",
    "asset_name",
    "asset_id",
    "token_exp",
    "client_ip",
    "error",
]


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()


def append_activity_csv(row: Dict[str, Any]) -> None:
    first_write = not ACTIVITY_CSV.exists()
    with ACTIVITY_CSV.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        if first_write:
            writer.writeheader()
        out = {k: row.get(k, "") for k in CSV_HEADERS}
        writer.writerow(out)


def _default_asset_allowed(name: str) -> bool:
    allowed_ext = (".appimage", ".deb", ".exe", ".msi", ".dmg", ".pkg", ".zip")
    lowered = name.lower()
    if lowered.endswith(allowed_ext):
        return True
    if lowered.startswith("install-nir-") and lowered.endswith((".sh", ".cmd", ".ps1")):
        return True
    if lowered.startswith("desktop-release-sha256") and lowered.endswith(".txt"):
        return True
    return False


def _asset_priority(name: str) -> int:
    lowered = name.lower()
    if lowered.startswith("install-nir-"):
        return 0
    if lowered.startswith("desktop-release-sha256-"):
        return 1
    if lowered.startswith("desktop-release-sha256"):
        return 2
    if lowered.endswith((".appimage", ".deb", ".exe", ".msi", ".dmg", ".pkg", ".zip")):
        return 3
    return 9


def _asset_platform(name: str) -> Optional[str]:
    lowered = name.lower()
    if "linux" in lowered or lowered.endswith(".appimage") or lowered.endswith(".deb"):
        return "linux"
    if "windows" in lowered or lowered.endswith(".exe") or lowered.endswith(".msi"):
        return "windows"
    if "macos" in lowered or lowered.endswith(".dmg") or lowered.endswith(".pkg") or lowered.endswith(".zip"):
        return "macos"
    return None


def _recommended_assets(assets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    by_platform: Dict[str, Dict[str, Dict[str, Any]]] = {
        "linux": {},
        "windows": {},
        "macos": {},
    }
    for asset in assets:
        name = str(asset.get("name", ""))
        platform = _asset_platform(name)
        if not platform:
            continue
        lowered = name.lower()
        slot = "installer"
        if lowered.startswith("install-nir-"):
            slot = "helper"
        elif lowered == f"desktop-release-sha256-{platform}.txt":
            slot = "checksum"
        if slot not in by_platform[platform]:
            by_platform[platform][slot] = asset

    out: List[Dict[str, Any]] = []
    for platform in ("linux", "windows", "macos"):
        pick = by_platform[platform]
        if "helper" in pick:
            out.append(pick["helper"])
        if "checksum" in pick:
            out.append(pick["checksum"])
        if "installer" in pick:
            out.append(pick["installer"])
    return out


def _filter_assets_for_target_os(
    assets: List[Dict[str, Any]], target_os: str
) -> List[Dict[str, Any]]:
    wanted = str(target_os or "").strip().lower()
    if wanted not in {"linux", "windows", "macos"}:
        return assets

    out: List[Dict[str, Any]] = []
    for asset in assets:
        name = str(asset.get("name", ""))
        platform = _asset_platform(name)
        lowered = name.lower()
        if platform == wanted:
            out.append(asset)
            continue
        # Keep generic checksum file for support workflows.
        if lowered == "desktop-release-sha256.txt":
            out.append(asset)
    return out


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
        "target_os": req.targetOS,
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
        f"target_os={req.targetOS}\n"
        f"name={req.name}\n"
        f"email={req.email}\n"
        f"institution={req.institution}\n"
        f"issued_at={issued_at.isoformat()}\n"
        f"expires_at={expires_at.isoformat()}\n"
        f"source={req.source}\n"
        f"signature={signature}\n"
    )


async def send_email_with_license(
    req: LicenseRequest,
    license_text: str,
    secure_links: Optional[List[Dict[str, str]]] = None,
    recommended_links: Optional[List[Dict[str, str]]] = None,
) -> None:
    if not RESEND_API_KEY or not RESEND_FROM_EMAIL:
        raise RuntimeError("Email service is not configured.")

    attachment_name = "nir_license.txt"
    encoded = base64.b64encode(license_text.encode("utf-8")).decode("utf-8")
    subject = f"Inzira Labs License - {req.requestedPlatform} ({req.targetOS})"
    download_links_html = ""
    secure_links = secure_links if secure_links is not None else []
    recommended_links = recommended_links if recommended_links is not None else []
    if secure_links:
        recommended_html = ""
        if recommended_links:
            recommended_items = "\n".join(
                [f'<li><a href="{item["url"]}">{item["name"]}</a></li>' for item in recommended_links]
            )
            recommended_html = f"""
            <p><strong>Recommended first:</strong> run platform helper, then install.</p>
            <ul>{recommended_items}</ul>
            """
        link_items = "\n".join(
            [f'<li><a href="{item["url"]}">{item["name"]}</a></li>' for item in secure_links]
        )
        download_links_html = f"""
        <p>Your secure private download links (valid for {DOWNLOAD_TOKEN_TTL_HOURS}h):</p>
        {recommended_html}
        <p>All assets:</p>
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
    <p>Selected operating system: <strong>{req.targetOS}</strong></p>
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


async def build_secure_download_links(email: str, target_os: str = "") -> List[Dict[str, str]]:
    assets = await get_release_assets()
    assets = sorted(
        assets,
        key=lambda a: (_asset_priority(str(a.get("name", ""))), str(a.get("name", "")).lower()),
    )
    assets = _filter_assets_for_target_os(assets, target_os)
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


async def build_secure_link_sets(
    email: str, target_os: str = ""
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    assets = await get_release_assets()
    assets = sorted(
        assets,
        key=lambda a: (_asset_priority(str(a.get("name", ""))), str(a.get("name", "")).lower()),
    )
    assets = _filter_assets_for_target_os(assets, target_os)
    recommended_assets = _recommended_assets(assets)

    def _to_links(picks: List[Dict[str, Any]]) -> List[Dict[str, str]]:
        out: List[Dict[str, str]] = []
        for asset in picks:
            token = make_download_token(asset["id"], asset["name"], email)
            if DOWNLOAD_LINK_BASE_URL:
                url = f"{DOWNLOAD_LINK_BASE_URL}/download/{token}"
            else:
                url = f"/download/{token}"
            out.append({"name": asset["name"], "url": url})
        return out

    return _to_links(assets), _to_links(recommended_assets)


def log_request(req: LicenseRequest, ok: bool, error: str = "", client_ip: str = "") -> None:
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
    append_activity_csv(
        {
            "ts": entry["ts"],
            "event": "license_request",
            "ok": ok,
            "email": req.email,
            "email_hash": hashlib.sha256(req.email.lower().encode("utf-8")).hexdigest(),
            "platform": req.requestedPlatform,
            "target_os": req.targetOS,
            "institution": req.institution,
            "source": req.source,
            "asset_name": "",
            "asset_id": "",
            "token_exp": "",
            "client_ip": client_ip,
            "error": error,
        }
    )


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/download/{token}")
async def download_private_asset(token: str, request: Request) -> Response:
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
            append_activity_csv(
                {
                    "ts": datetime.now(timezone.utc).isoformat(),
                    "event": "download_attempt",
                    "ok": False,
                    "email": "",
                    "email_hash": payload.get("eh", ""),
                    "platform": _asset_platform(filename) or "",
                    "institution": "",
                    "source": "download-token",
                    "asset_name": filename,
                    "asset_id": asset_id,
                    "token_exp": payload.get("exp", ""),
                    "client_ip": request.client.host if request.client else "",
                    "error": f"github_asset_fetch_{resp.status_code}",
                }
            )
            raise HTTPException(
                status_code=502,
                detail=f"Could not fetch private asset from GitHub ({resp.status_code}).",
            )
        append_activity_csv(
            {
                "ts": datetime.now(timezone.utc).isoformat(),
                "event": "download_granted",
                "ok": True,
                "email": "",
                "email_hash": payload.get("eh", ""),
                "platform": _asset_platform(filename) or "",
                "institution": "",
                "source": "download-token",
                "asset_name": filename,
                "asset_id": asset_id,
                "token_exp": payload.get("exp", ""),
                "client_ip": request.client.host if request.client else "",
                "error": "",
            }
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
async def request_license(req: LicenseRequest, request: Request) -> dict:
    try:
        license_text = build_license_text(req)
        secure_links, recommended_links = await build_secure_link_sets(req.email, req.targetOS)
        await send_email_with_license(req, license_text, secure_links, recommended_links)
        log_request(req, ok=True, client_ip=request.client.host if request.client else "")
        return {
            "ok": True,
            "message": "License generated and emailed with secure download links.",
            "recommendedLinks": recommended_links,
            "downloadLinks": secure_links,
        }
    except Exception as exc:  # noqa: BLE001
        log_request(
            req,
            ok=False,
            error=str(exc),
            client_ip=request.client.host if request.client else "",
        )
        raise HTTPException(status_code=502, detail=f"License dispatch failed: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8080")),
        reload=False,
    )
