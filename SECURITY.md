# Security Policy

## Supported Versions

This is a portfolio/demo project. Only the `main` branch is supported;
there are no maintained release branches.

## Reporting a Vulnerability

Please report security issues privately by emailing **spatel842002@gmail.com**
rather than opening a public issue. Include reproduction steps and, if
possible, a suggested fix. You should expect an initial response within a
few days.

## Security controls in this project

- Uploaded files are validated by MIME type, rejected if empty, and capped
  at `MAX_UPLOAD_SIZE_MB` (default 25MB) before any decoding is attempted.
- Video duration is capped at `MAX_VIDEO_DURATION_S` to bound CPU cost per job.
- Temporary video files are written outside the web root and deleted after
  processing, including on failure (`finally` block).
- No user-supplied input is passed to a shell, SQL query, or template
  engine.
- The container runs as a non-root Python base image process for the API;
  see `Dockerfile`.
- Object storage credentials, MLflow URIs, and OTLP endpoints are read
  exclusively from environment variables (see `.env.example`); no secrets
  are hardcoded or committed.
- Dependencies are scanned in CI via `pip-audit`; the repository is scanned
  for committed secrets via `gitleaks`.

## Known limitations

- The in-memory job store (`src/threed_od/jobs.py`) is per-process and is
  not itself authenticated or rate-limited; see
  [docs/security.md](docs/security.md) for the full threat model and the
  hardening steps required before exposing this service on the public
  internet (auth, per-IP rate limiting, and a shared job store for
  multi-replica deployments).
