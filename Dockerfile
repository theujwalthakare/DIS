FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       libglib2.0-0 \
       libsm6 \
       libxrender1 \
       libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install core dependencies
COPY requirements.txt ./

RUN python -m pip install --upgrade pip setuptools wheel

RUN pip install "numpy>=1.26"

# Install all requirements from single file
RUN pip install -r requirements.txt

# Copy repository
COPY . .

# Default: run the sklearn autoencoder trainer
CMD ["python", "ml/train_autoencoder_sklearn.py", "--input", "data/metrics.csv", "--out", "models/ae_sklearn.joblib"]