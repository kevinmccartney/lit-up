FROM python:3.13-slim

# A tiny SAM CLI runner image for local dev.
# - Installs aws-sam-cli
# - Installs docker CLI so SAM can run `sam build --use-container` and start Lambda containers
#
# Note: this container needs the host Docker daemon socket mounted at /var/run/docker.sock.

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
  && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    curl \
    git \
    unzip \
    docker.io \
  && rm -rf /var/lib/apt/lists/*

# Pin loosely; project can tighten later if needed.
RUN pip install --no-cache-dir "aws-sam-cli>=1.110.0"

WORKDIR /workspace/projects/api/local


