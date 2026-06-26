# Enabling the License Flow Later

Status: **dormant**. The website is live on Railway; the license/download backend
ships with it but is intentionally not activated until the desktop app (NI / BIDSHub)
implements license verification.

This document explains exactly what to change, in order, to turn it on later.
No application code needs to be rewritten — the endpoints already exist in
[`license-service/main.py`](license-service/main.py). Turning it on is mostly
configuration plus a verification step in the desktop app.

---

## How the flow works (once enabled)

```
website form (Get NI / Get BIDSHub)
   │  POST /api/license/request   (same-origin, no CORS)
   ▼
license-service (FastAPI on Railway)
   1. generates a signed license.txt        (HMAC-SHA256 with LICENSE_SIGNING_SECRET)
   2. emails the license to the user         (via Resend)
   3. emails time-limited secure download links
   ▼
user clicks a link → GET /download/{token}
   • token signature checked (HMAC)
   • backend proxies the private GitHub release asset
```

Relevant code:
- Form endpoint: `@app.post("/api/license/request")` — [main.py:543](license-service/main.py#L543)
- License generation + signing: `build_license_text()` — [main.py:245](license-service/main.py#L245)
- Email send (Resend): `send_email_with_license()` — [main.py:280](license-service/main.py#L280)
- Secure download proxy: `@app.get("/download/{token}")` — [main.py:473](license-service/main.py#L473)
- Frontend endpoint resolver: `getLicenseServiceEndpoints()` — [js/script.js:45](js/script.js#L45)

---

## Step 1 — Set the Railway environment variables

The website serves fine with none of these. They are only read when the form is
submitted. Set them in **Railway → your service → Variables**:

| Variable | Required | Purpose |
|---|---|---|
| `RESEND_API_KEY` | ✅ | Resend API key for sending the license email |
| `RESEND_FROM_EMAIL` | ✅ | Verified sender, e.g. `licenses@inzira-labs.com` |
| `LICENSE_SIGNING_SECRET` | ✅ | Secret used to HMAC-sign licenses and download tokens. **Pick a strong random value and keep it stable** — changing it invalidates all previously issued licenses. |
| `GITHUB_TOKEN` | ✅ (for downloads) | PAT with read access to the private release repo |
| `GITHUB_REPO` | ✅ (for downloads) | e.g. `phindagijimana/neuroinsight_research` |
| `GITHUB_RELEASE_TAG` | optional | Defaults to `latest` |
| `DOWNLOAD_LINK_BASE_URL` | ✅ | Public base URL of THIS service (the Railway URL or custom domain) so emailed `/download/...` links resolve |
| `DOWNLOAD_TOKEN_TTL_HOURS` | optional | Secure-link lifetime, default `24` |
| `ASSET_NAME_ALLOWLIST` | optional | Comma-separated allowlist of release asset names to expose |
| `NIR_RELEASE_URL` | optional | Fallback release URL shown in the email if no assets are found |
| `ALLOWED_ORIGINS` | optional now | Only needed if the site is also served from another origin (e.g. GitHub Pages). Same-origin on Railway needs nothing. |

> Defaults live at the top of [`main.py`](license-service/main.py#L22-L41). If
> `LICENSE_SIGNING_SECRET` is left unset it falls back to `"change-me"` — never
> ship that; set a real secret.

After setting variables, redeploy (Railway redeploys automatically on variable
changes).

---

## Step 2 — Confirm the frontend points at the backend

Already done. The form posts to a relative path first, so when the site is served
by Railway it hits the same host with no hardcoded URL or CORS:

```js
// js/script.js → getLicenseServiceEndpoints()
return [
  "/api/license/request",                                   // same-origin (Railway)
  "https://license.inzira-labs.com/api/license/request",    // fallback
  "https://inzira-labs-license-service.onrender.com/api/license/request",
];
```

If you later move to a custom domain, no change is needed — the relative path
follows whatever origin serves the page.

---

## Step 3 — Implement license verification in the desktop app

This is the real "not yet implemented" piece. The backend already issues a signed
license file; the desktop app must **verify** it on startup/activation.

The license file format (`license.txt`):

```
INZIRA_LABS_LICENSE_V1
license_id=inzira-<uuid>
product=<platform>
target_os=<linux|windows|macos>
name=<name>
email=<email>
institution=<institution>
issued_at=<iso8601>
expires_at=<iso8601>     # currently issued_at + 90 days
source=<source>
signature=<hmac_sha256_hex>
```

To verify in the desktop app:

1. Read every line **except** `signature=`.
2. Rebuild the canonical payload exactly as the server does — see
   `build_license_text()` ([main.py:245](license-service/main.py#L245)):
   a JSON object of
   `{license_id, product, target_os, name, email, institution, issued_at, expires_at, source}`
   serialized with `json.dumps(payload, sort_keys=True, separators=(",", ":"))`.
3. Compute `HMAC-SHA256(LICENSE_SIGNING_SECRET, canonical)` and compare (constant-time)
   against the `signature=` value.
4. Reject if the signature mismatches or `expires_at` is in the past.

> The desktop app needs the **same `LICENSE_SIGNING_SECRET`** to verify. For a
> shared-secret (symmetric) scheme, embed/provision the secret securely in the app.
> If you'd rather not ship the secret in the client, switch signing to an
> **asymmetric** scheme (sign with a private key on the server, verify with a public
> key in the app) — this is a small change to `build_license_text()` and the verifier.

---

## Step 4 — Re-enable the request buttons (if they were disabled)

If the "Get NI" / "Get BIDSHub" buttons were turned into a "Coming soon" state while
the flow was dormant, restore the original `openLicenseModal(...)` handlers in
[`index.html`](index.html). (As of this writing the buttons are still active and
will simply error on submit until Step 1's variables are set.)

---

## Step 5 — Test end-to-end

1. Visit the Railway URL → website loads.
2. `GET /health` → `{"ok": true}`.
3. Submit the license form with a real email.
4. Confirm the license email arrives via Resend with download links.
5. Click a download link → `GET /download/{token}` streams the private release asset.
6. Install on the desktop app and confirm it accepts the signed license.

---

## Quick checklist

- [ ] Set `RESEND_API_KEY`, `RESEND_FROM_EMAIL`
- [ ] Set a strong, stable `LICENSE_SIGNING_SECRET`
- [ ] Set `GITHUB_TOKEN`, `GITHUB_REPO` (private release access)
- [ ] Set `DOWNLOAD_LINK_BASE_URL` to the Railway/custom domain
- [ ] Implement signature + expiry verification in the desktop app
- [ ] Re-enable request buttons if they were disabled
- [ ] End-to-end test (form → email → download → install)
