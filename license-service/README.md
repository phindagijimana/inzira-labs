# Inzira Labs License Service (No-Admin, Auto-Issue)

This service receives landing-page form submissions, auto-generates a `license.txt`, emails it to the requester, then allows frontend redirect to NIR releases.

## API

- `GET /health`
- `POST /api/license/request`

Request body:

```json
{
  "requestedPlatform": "nir-desktop",
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
- `NIR_RELEASE_URL` (download destination)
- `LICENSE_SIGNING_SECRET`

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

## Landing site integration

In `../js/script.js`, set:

```js
window.INZIRA_LICENSE_ENDPOINT = "https://<your-service-domain>/api/license/request";
```

or change the constant directly.

## Notes

- This version is intentionally no-admin and auto-approves all requests.
- Request logs are appended to `license-service/data/license_requests.jsonl`.
- Add an admin/review workflow later when you are ready.
