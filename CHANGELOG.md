# Changelog
## 2.2.0-2 (2026-11-16)

Docs only, no change to the app or the image.

- README: Deploy on Railway button for the published template (`marker`), and measured memory use.


## 2.2.0-1 (2026-11-16)

First release of the Railway template.

- Marker 2.2.0 (`marker-pdf[full]`) on `python:3.12-slim-bookworm` (pinned by digest), with CPU-only PyTorch 2.15.0.
- The server and viewer sit behind `MARKER_API_KEY` (Bearer, `X-API-Key` or the basic-auth password). `/health` stays open for Railway's health check.
- The CPU models (Indra ONNX layout and OCR) and the rendering font are downloaded at build time.
