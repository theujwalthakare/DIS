"""
Generate synthetic realistic metrics for DIS experiments.

Creates data/metrics.csv with ~1000 samples, multiple features, and labeled
anomalies (CPU spike, memory leak, network issues, etc.).

Usage:
  python scripts/generate_metrics.py
"""
import numpy as np
import pandas as pd
from pathlib import Path

np.random.seed(42)

N = 1000

# Normal baseline (70% of data)
normal_idx = int(N * 0.7)

# Generate normal baseline
cpu = np.random.uniform(3, 15, normal_idx)
mem = np.random.uniform(25, 40, normal_idx)
net_tx = np.random.uniform(80, 150, normal_idx)
net_rx = np.random.uniform(90, 160, normal_idx)
disk_read = np.random.uniform(10, 50, normal_idx)
disk_write = np.random.uniform(5, 30, normal_idx)
http_req_rate = np.random.uniform(50, 120, normal_idx)
response_ms = np.random.uniform(20, 80, normal_idx)
pod_restarts = np.zeros(normal_idx)
label = np.zeros(normal_idx)

# Anomaly patterns
anomalies = []

# 1. CPU spike (50 samples)
cpu_spike = np.random.uniform(80, 98, 50)
mem_spike = np.random.uniform(35, 50, 50)
net_spike = np.random.uniform(100, 200, 50)
anomalies.append({
    'cpu_percent': cpu_spike, 'mem_percent': mem_spike, 'net_tx': net_spike, 'net_rx': net_spike * 1.1,
    'disk_read': np.random.uniform(20, 80, 50), 'disk_write': np.random.uniform(10, 50, 50),
    'http_req_rate': np.random.uniform(100, 200, 50), 'response_ms': np.random.uniform(100, 300, 50),
    'pod_restarts': np.zeros(50), 'label': np.ones(50)
})

# 2. Memory leak (gradual ramp, 80 samples)
mem_leak = np.linspace(30, 92, 80) + np.random.normal(0, 2, 80)
anomalies.append({
    'cpu_percent': np.random.uniform(10, 25, 80), 'mem_percent': mem_leak, 
    'net_tx': np.random.uniform(90, 150, 80), 'net_rx': np.random.uniform(95, 160, 80),
    'disk_read': np.random.uniform(15, 60, 80), 'disk_write': np.random.uniform(8, 40, 80),
    'http_req_rate': np.random.uniform(60, 110, 80), 'response_ms': np.linspace(50, 250, 80),
    'pod_restarts': np.zeros(80), 'label': np.ones(80)
})

# 3. Network congestion (60 samples)
net_cong_tx = np.random.uniform(2000, 8000, 60)
net_cong_rx = np.random.uniform(2200, 8500, 60)
anomalies.append({
    'cpu_percent': np.random.uniform(15, 40, 60), 'mem_percent': np.random.uniform(30, 50, 60),
    'net_tx': net_cong_tx, 'net_rx': net_cong_rx,
    'disk_read': np.random.uniform(20, 70, 60), 'disk_write': np.random.uniform(10, 45, 60),
    'http_req_rate': np.random.uniform(30, 70, 60), 'response_ms': np.random.uniform(200, 600, 60),
    'pod_restarts': np.zeros(60), 'label': np.ones(60)
})

# 4. Pod restarts / crash (40 samples)
anomalies.append({
    'cpu_percent': np.random.uniform(0, 10, 40), 'mem_percent': np.random.uniform(5, 20, 40),
    'net_tx': np.random.uniform(0, 30, 40), 'net_rx': np.random.uniform(0, 35, 40),
    'disk_read': np.random.uniform(0, 10, 40), 'disk_write': np.random.uniform(0, 8, 40),
    'http_req_rate': np.random.uniform(0, 20, 40), 'response_ms': np.random.uniform(500, 2000, 40),
    'pod_restarts': np.random.randint(1, 5, 40), 'label': np.ones(40)
})

# 5. Disk I/O saturation (40 samples)
anomalies.append({
    'cpu_percent': np.random.uniform(40, 70, 40), 'mem_percent': np.random.uniform(35, 55, 40),
    'net_tx': np.random.uniform(100, 180, 40), 'net_rx': np.random.uniform(110, 190, 40),
    'disk_read': np.random.uniform(500, 2000, 40), 'disk_write': np.random.uniform(400, 1500, 40),
    'http_req_rate': np.random.uniform(40, 90, 40), 'response_ms': np.random.uniform(150, 400, 40),
    'pod_restarts': np.zeros(40), 'label': np.ones(40)
})

# Combine normal + anomalies
all_data = {
    'cpu_percent': cpu,
    'mem_percent': mem,
    'net_tx': net_tx,
    'net_rx': net_rx,
    'disk_read': disk_read,
    'disk_write': disk_write,
    'http_req_rate': http_req_rate,
    'response_ms': response_ms,
    'pod_restarts': pod_restarts,
    'label': label
}

for anom in anomalies:
    for k in all_data:
        all_data[k] = np.concatenate([all_data[k], anom[k]])

# Shuffle
idx = np.arange(len(all_data['label']))
np.random.shuffle(idx)
for k in all_data:
    all_data[k] = all_data[k][idx]

df = pd.DataFrame(all_data)

out = Path(__file__).resolve().parents[1] / 'data' / 'metrics.csv'
df.to_csv(out, index=False)
print(f'Generated {len(df)} samples')
print(f'Normal: {(df.label==0).sum()}, Anomalies: {(df.label==1).sum()}')
print(f'Wrote: {out}')
