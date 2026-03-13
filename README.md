# Inzira Labs Landing Site

This is a standalone landing site for **Inzira Labs (Translational Biomedical Research)**.

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
  - why they need the platform

## Separate GitHub Repo / Service Architecture

This landing site can live in a different GitHub repository from NIR and still work cleanly:

1. Landing site (this static site) is deployed independently (e.g., GitHub Pages/Vercel).
2. License service is a separate backend repo/API endpoint.
3. NIR downloads come from NIR releases repo URL.

In `js/script.js`:

- `NIR_DOWNLOAD_URL` controls where users are sent after request.
- `LICENSE_SERVICE_ENDPOINT` is where form data is posted.

If `LICENSE_SERVICE_ENDPOINT` is empty, the site stores the request in local storage as a fallback.

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
