FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1
WORKDIR /app
# tesseract-ocr: the actual OCR engine pytesseract shells out to (receipt scanner) - missing this gives a
# TesseractNotFoundError at request time, not at build time, so it's easy to miss until production traffic hits it.
# libgomp1: OpenMP runtime torch needs at import time; not always present on the slim base image.
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr libgomp1 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY migrations ./migrations
COPY scripts ./scripts
COPY ml ./ml
COPY alembic.ini .
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
