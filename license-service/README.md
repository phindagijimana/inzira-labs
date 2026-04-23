# Inzira Labs License Service (No-Admin, Auto-Issue, Private Download Proxy)

This service receives landing-page form submissions, auto-generates a
`license.txt`, emails it to the requester, and includes **time-limited secure
links** to private GitHub release assets.

It also returns helper-first links in API response so the landing modal can
offer: verify checksum -> install.

## API

- `GET /health`
- `POST /api/license/request`
- `GET /download/{token}`
`POST /api/license/request` success response includes:

- `recommendedLinks` (helper/checksum/installer set for selected OS)
- `downloadLinks` (selected OS assets only)


Request body:

```json
{
  "requestedPlatform": "nir-desktop",
  "targetOS": "linux",
  "name": "Jane Doe",
  "email": "jane@example.org",
  "institution": "Example University",
  "purpose": "Clinical neuroimaging research workflows.",
  "source": "inzira-labs-landing",
  "submittedAt": "2026-03-13T05:00:00Z"
}
```

## Environment

Copy `.env.example` to `.env` and set:

- `RESEND_API_KEY`
- `RESEND_FROM_EMAIL` (verified sender/domain)
- `ALLOWED_ORIGINS` (include your GitHub Pages origin)
- `LICENSE_SIGNING_SECRET`
- `GITHUB_TOKEN` (must have access to private repo releases)
- `GITHUB_REPO` (`owner/repo`)
- `GITHUB_RELEASE_TAG` (`latest` or specific tag)
- `DOWNLOAD_LINK_BASE_URL` (public URL of this service)
- optional `ASSET_NAME_ALLOWLIST` (comma-separated exact names)

## Run locally

```bash
cd license-service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Service default URL:

- `http://localhost:8080`

## Deploy on Railway

This repository includes `railway.json` at the repo root with build/start
commands targeting `license-service/`.

1. Create a new Railway project from this GitHub repo.
2. Add required environment variables in Railway (same keys as `.env.example`):
   - `RESEND_API_KEY`
   - `RESEND_FROM_EMAIL`
   - `ALLOWED_ORIGINS` (for example `https://phindagijimana.github.io`)
   - `LICENSE_SIGNING_SECRET`
   - `GITHUB_TOKEN`
   - `GITHUB_REPO`
   - `GITHUB_RELEASE_TAG`
   - `DOWNLOAD_LINK_BASE_URL` (set to your Railway public URL)
   - `DOWNLOAD_TOKEN_TTL_HOURS`
   - optional `ASSET_NAME_ALLOWLIST`
   - optional `NIR_RELEASE_URL`
3. Deploy and verify:
   - `GET https://<your-railway-domain>/health` returns `{"ok": true}`.
4. Update landing endpoint config in `index.html`:
   - set `window.INZIRA_LICENSE_ENDPOINTS` to include your Railway URL
     (`https://<your-railway-domain>/api/license/request`).

## Landing site integration

In `../js/script.js`, set:

```js
window.INZIRA_LICENSE_ENDPOINT = "https://<your-service-domain>/api/license/request";
```

or change the constant directly.

## How private downloads work

1. Service reads private assets from GitHub Releases API.
2. It generates tokenized `/download/{token}` links (time-limited, signed).
3. Links are emailed to requester and returned in API response.
4. `/download/{token}` validates token and proxies the private asset from GitHub.

## Notes

- This version is intentionally no-admin and auto-approves requests.
- Request logs are appended to `license-service/data/license_requests.jsonl`.
- CSV activity tracking is appended to `license-service/data/license_activity.csv`
  (license requests + download events), suitable for spreadsheet review.
- Add admin/review workflow later when you are ready.
