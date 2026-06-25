# Build the React console before assembling the Python runtime image.
FROM node:22-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build


# DocSentinel API and console runtime.
FROM python:3.11-slim

WORKDIR /app

# System dependencies for PyMuPDF and embedding models.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmupdf-dev mupdf-tools \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
ARG TORCH_VERSION=2.12.1
ARG TORCHVISION_VERSION=0.27.1
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    "torch==${TORCH_VERSION}" \
    "torchvision==${TORCHVISION_VERSION}"
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY docs/ ./docs/
COPY --from=frontend-builder /frontend/dist ./frontend/dist

# Chroma and uploads persist here.
ENV CHROMA_PERSIST_DIR=/data/chroma
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
