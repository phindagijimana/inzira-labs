# Inzira Labs Landing Site

This is a standalone landing site for **Inzira Labs (Translating Biomedical Research to Usable Tools)**.

It is modeled after the structure/style used in the ZeroGap landing repo and is intentionally isolated inside this repository at:

- `src/inzira-labs/`

## What it does

- shows Inzira Labs pages (`Home`, `Platforms`, `Downloads`)
- lists NIR as one of the platform services
- enforces a **pre-download license request form** before redirecting users to NIR downloads
- collects:
  - full name
  - email
  - institution
  - target operating system (linux/windows/macos)
  - why they need the platform

## Separate GitHub Repo / Service Architecture

This landing site can live in a different GitHub repository from NIR and still work cleanly:

1. Landing site (this static site) is deployed independently (e.g., GitHub Pages/Vercel).
2. License service is a separate backend repo/API endpoint.
3. NIR downloads come from NIR releases repo URL.

In `js/script.js`:

- `NIR_DOWNLOAD_URL` controls where users are sent after request.
- `LICENSE_SERVICE_ENDPOINT` is where form data is posted.
- It expects a successful backend response and now displays helper-first links
  (verify checksum then install) directly in the modal.

## Included no-admin license service

This repository now includes a lightweight backend under:

- `license-service/`

Flow:

1. landing form posts to `/api/license/request`
2. backend auto-generates `license.txt`
3. backend emails license to submitted email with secure download links
4. landing modal + email both prioritize platform install helpers first
5. user downloads installers through time-limited links served by backend proxy

Service setup details are in:

- `license-service/README.md`

## Local preview

Open `index.html` directly, or serve with a static server from `src/inzira-labs`.

## GitHub Hosting (Pages)

This repository is configured for GitHub Pages deployment via:

- `.github/workflows/pages.yml`

Deployment behavior:

- automatic deploy on push to `main`
- manual deploy from Actions tab via workflow dispatch

After first workflow run, enable Pages in repository settings:

1. GitHub repository -> Settings -> Pages
2. Source: `GitHub Actions`

Your site URL will be:

- `https://phindagijimana.github.io/inzira-labs/`
