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
COPY ml/requirements.txt ml/requirements.txt

RUN python -m pip install --upgrade pip setuptools wheel

# Ensure a recent NumPy is present before installing pandas to avoid
# pandas C-extension / ABI mismatches (pandas requires numpy >=1.26 for
# modern pandas releases). Install numpy explicitly first.
RUN pip install "numpy>=1.26"

# Install regular requirements and ML requirements
RUN pip install -r requirements.txt
RUN pip install -r ml/requirements.txt

# Install TensorFlow (CPU). Pin a version if you require reproducibility.
RUN pip install tensorflow==2.12.0

# Copy repository
COPY . .

# Default: run the Keras autoencoder trainer (override at runtime)
CMD ["python", "ml/train_autoencoder.py", "--input", "data/metrics.csv", "--out", "ml/models/autoencoder"]
