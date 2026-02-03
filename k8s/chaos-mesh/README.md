# Chaos Mesh Experiments

This directory contains Chaos Mesh experiment definitions for testing DIS.

## Prerequisites

Install Chaos Mesh (after reviewing the script):

```bash
# Download and review the installation script
curl -sSL https://mirrors.chaos-mesh.org/v2.5.0/install.sh -o install.sh
cat install.sh  # Review the script
bash install.sh
```

Verify installation:

```bash
kubectl get pods -n chaos-mesh
```

## Experiments

### CPU Stress Test

Stresses CPU to trigger DIS anomaly detection:

```bash
kubectl apply -f experiments.yaml
# Look for: cpu-stress-test
```

### Memory Stress Test

Causes memory pressure:

```bash
kubectl apply -f experiments.yaml
# Look for: memory-stress-test
```

### Network Latency

Introduces network delays:

```bash
kubectl apply -f experiments.yaml
# Look for: network-latency-test
```

### Pod Kill

Randomly kills pods:

```bash
kubectl apply -f experiments.yaml
# Look for: pod-kill-test
```

### Network Partition

Simulates network splits:

```bash
kubectl apply -f experiments.yaml
# Look for: network-partition-test
```

## Monitoring DIS Response

Watch DIS detect and respond to chaos:

```bash
# Terminal 1: Watch DIS logs
kubectl logs -n dis-system -l app=dis-agent -f

# Terminal 2: Watch test app pods
watch kubectl get pods -l app=test-app

# Terminal 3: Monitor metrics
kubectl port-forward -n dis-system svc/dis-metrics 8000:8000
# Open http://localhost:8000/metrics
```

## Expected Behavior

1. **Detection**: DIS should detect anomalies within 30-60 seconds
2. **Response**: Based on severity:
   - High (>90% resource usage): Pod isolation
   - Medium (>75% resource usage): Pod restart
   - Low: Log only
3. **Recovery**: System should stabilize after chaos ends

## Cleanup

```bash
# Remove all experiments
kubectl delete -f experiments.yaml

# Remove Chaos Mesh
kubectl delete ns chaos-mesh
```

## Customization

Edit `experiments.yaml` to modify:
- `duration`: How long chaos lasts
- `scheduler.cron`: Frequency of recurring experiments
- `selector`: Which pods to target
- Chaos-specific parameters (load, latency, etc.)
