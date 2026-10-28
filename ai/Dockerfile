# Layanan AI HaloSIS (FastAPI). Model & indeks TIDAK di-copy ke image (berisi data tersamar, di-ignore git):
# keduanya di-mount dari ai/models dan ai/index oleh docker-compose.
FROM python:3.14-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 HF_HOME=/cache/huggingface

# PyTorch versi CPU (jauh lebih kecil dari versi CUDA)
RUN pip install --no-cache-dir torch==2.14.1 --index-url https://download.pytorch.org/whl/cpu
COPY requirements-service.txt .
RUN pip install --no-cache-dir -r requirements-service.txt

COPY halosis_ai ./halosis_ai
COPY service ./service

EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
