#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-govlexops:latest}"

echo "[build] docker image: ${IMAGE_TAG}"
docker build -t "${IMAGE_TAG}" -f docker/Dockerfile .
echo "[done] built ${IMAGE_TAG}"
