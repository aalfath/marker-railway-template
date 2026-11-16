# Marker on Railway

This repo is the source of the **Marker** template on Railway. It runs [Marker](https://github.com/datalab-to/marker) by Datalab, which converts PDFs, images and Office documents (DOCX, PPTX, XLSX, EPUB, HTML) into Markdown, HTML, JSON or RAG-ready chunks. You get Marker's own web viewer and its REST API, protected by an API key.

- **Marker version:** 2.2.0 (`marker-pdf[full]==2.2.0` from PyPI)
- **Base image:** `python:3.12-slim-bookworm`, pinned by digest. Upstream publishes no Docker image, so the `Dockerfile` installs the released package at a fixed version, with CPU-only PyTorch 2.15.0.
- **Mode:** CPU only. Marker's `fast` mode (default on CPU: in-process ONNX layout and OCR) and `no_ocr` mode run here with no GPU. The models and font are downloaded at build time, so a deploy starts in seconds and fetches nothing.

## What the template deploys

One service, `Marker`, built from this repo's `Dockerfile`:

| Item | Value |
|---|---|
| Public port | `8000` (`PORT`) |
| Health check | `/health` (open, no key needed) |
| Volume | none: Marker is stateless (uploads go to a temp folder and are deleted after each conversion) |

## Variables

| Variable | Default | Notes |
|---|---|---|
| `MARKER_API_KEY` | `${{secret(48)}}` | Generated on deploy. Every route except `/health` needs it. |
| `PORT` | `8000` | Port the server listens on. |

The key is accepted three ways:

- `Authorization: Bearer <key>`
- `X-API-Key: <key>`
- HTTP basic auth with any user name and the key as the password. Your browser asks for it when you open the viewer.

Optional settings you can add yourself:

- `MARKER_MAX_UPLOAD_BYTES`: largest accepted upload, default `104857600` (100 MB).
- `GOOGLE_API_KEY`: a Gemini key, needed only if you send `use_llm=true`.
- `SURYA_INFERENCE_URL`: an OpenAI-compatible Surya inference server (for example one you run on a GPU host). Only the `balanced` and `vllm` modes need it.
- `OMP_NUM_THREADS`: CPU threads per conversion. By default the start script sizes it from the service's CPU limit, at most 8.
- `MARKER_ALLOW_NO_API_KEY=true`: run with no key at all. Don't do this on a public domain.

## Using it

Open `https://YOUR-DOMAIN/` for the viewer. Your browser asks for a user name (anything) and a password (your `MARKER_API_KEY`). The API docs are at `/docs`.

Convert a file from the command line:

```sh
curl -s -H "Authorization: Bearer $MARKER_API_KEY" \
  -F file=@paper.pdf -F output_format=markdown \
  https://YOUR-DOMAIN/marker/upload | jq -r .output
```

Other form fields: `page_range` (for example `0,5-10`), `mode` (`fast` or `no_ocr` on CPU), `force_ocr`, `disable_ocr`, `paginate_output`, `keep_headers_footers`, `use_llm`, and `output_format` (`markdown`, `html`, `json` or `chunks`). The response is JSON with `output`, base64 `images` and `metadata`.

## Sizing

Marker loads its ONNX models once at start. In our tests it used about 0.4 GB of RAM idle and about 0.9 GB while converting a 15-page paper. Give it a few vCPUs for faster conversions: the start script uses up to 8 threads.

## Licensing

Marker's code is Apache-2.0. Its model weights use Datalab's modified AI Pubs OpenRAIL-M license ([MODEL_LICENSE](https://github.com/datalab-to/marker/blob/master/MODEL_LICENSE)). They're free for personal use, research, and organisations under US$5M in yearly revenue and under US$5M in funding, and not for services that compete with Datalab. Other commercial use needs a licence from [Datalab](https://www.datalab.to/).

## How updates reach you

Railway builds your service from this repo. When a new Marker version is merged to `main`, Railway shows you an "update available" notice in your project, and you choose when to apply it. Read `CHANGELOG.md` before you update.

## Files

- `Dockerfile`: pinned base image, Marker and CPU PyTorch, build-time model download.
- `start.sh`: refuses to start without an API key and sizes the CPU thread pools.
- `app.py`: Marker's FastAPI server plus the API-key check and `/health`.
- `warmup.py`: converts a small test PDF at build time so the models are inside the image.
