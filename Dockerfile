# Marker (https://github.com/datalab-to/marker) for Railway.
# Upstream publishes no Docker image, so this pins the official Python image by
# digest and installs the released marker-pdf package at a fixed version.
FROM python:3.12-slim-bookworm@sha256:935c3c5b12357a7e10caa9c1e6ca5692344d97cf229832ef584be2cec9fc03df

ARG MARKER_VERSION=2.2.0
ARG TORCH_VERSION=2.15.0

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TORCH_DEVICE=cpu \
    TOKENIZERS_PARALLELISM=false

# Pango and HarfBuzz are needed by WeasyPrint, which Marker uses to convert
# DOCX, PPTX, XLSX, EPUB and HTML into PDF before parsing.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libharfbuzz-subset0 \
      libfontconfig1 fonts-dejavu-core curl ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# One resolve with the CPU-only PyTorch wheel pinned, so pip never swaps in the
# multi-GB CUDA build. The checks fail the build if a CUDA package sneaks in.
RUN pip install --extra-index-url https://download.pytorch.org/whl/cpu \
      "torch==${TORCH_VERSION}+cpu" "marker-pdf[full]==${MARKER_VERSION}" \
      "fastapi==0.139.2" "uvicorn==0.51.0" "python-multipart==0.0.32" \
 && python -c "import torch; assert torch.__version__.endswith('+cpu'), torch.__version__" \
 && ! pip list 2>/dev/null | grep -qiE '^(nvidia|cuda)-'

WORKDIR /app
COPY app.py warmup.py start.sh ./

# Download the CPU models (Indra ONNX layout and OCR) and the rendering font at
# build time, so the container starts without fetching anything.
RUN mkdir -p /root/.cache/datalab/marker/fonts \
 && curl -fsSL --retry 5 --retry-all-errors -o /root/.cache/datalab/marker/fonts/GoNotoCurrent-Regular.ttf \
      https://models.datalab.to/artifacts/GoNotoCurrent-Regular.ttf \
 && python warmup.py && chmod +x start.sh

ENV PORT=8000
EXPOSE 8000
CMD ["./start.sh"]
