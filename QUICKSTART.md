# Quick Start Guide

## Getting Started in 5 Minutes

This guide will help you deploy DIS to a local Kubernetes cluster.

### Prerequisites

- Docker Desktop with Kubernetes enabled, OR
- Minikube, OR
- Kind (Kubernetes in Docker)

### Step 1: Start Local Cluster

**Using Docker Desktop:**
- Enable Kubernetes in Docker Desktop settings
- Wait for Kubernetes to start

**Using Minikube:**
```bash
minikube start --cpus=4 --memory=8192
```

**Using Kind:**
```bash
kind create cluster --name dis-test
```

### Step 2: Build and Load Image

```bash
# Build the image
docker build -t dis-kubernetes:latest .

# For Minikube
minikube image load dis-kubernetes:latest

# For Kind
kind load docker-image dis-kubernetes:latest --name dis-test
```

### Step 3: Deploy DIS

```bash
# Deploy all components
kubectl apply -f k8s/manifests/

# Wait for pods to be ready
kubectl wait --for=condition=ready pod -l app=dis-agent -n dis-system --timeout=300s
```

### Step 4: Verify Installation

```bash
# Check pod status
kubectl get pods -n dis-system

# View logs (wait for "Training completed" message)
kubectl logs -n dis-system -l app=dis-agent --tail=50

# Check metrics
kubectl port-forward -n dis-system svc/dis-metrics 8000:8000
# Open http://localhost:8000/metrics in browser
```

### Step 5: Deploy Test Application

```bash
# Deploy test application
kubectl apply -f k8s/examples/test-app.yaml

# Verify deployment
kubectl get pods -l app=test-app
```

### Step 6: Observe DIS in Action

```bash
# Follow DIS logs
kubectl logs -n dis-system -l app=dis-agent -f

# In another terminal, generate some load
kubectl run stress --image=polinux/stress --rm -it --restart=Never -- \
  stress --cpu 4 --timeout 60s
```

### Cleanup

```bash
# Remove DIS
kubectl delete namespace dis-system

# Remove test app
kubectl delete -f k8s/examples/test-app.yaml
```

## Next Steps

- Review [Architecture Documentation](ARCHITECTURE.md)
- Try [Chaos Mesh Experiments](k8s/chaos-mesh/experiments.yaml)
- Customize [Configuration](config/dis-config.yaml)
- Run [Unit Tests](tests/)

## Common Issues

### "ImagePullBackOff" Error
- Make sure you built and loaded the image into your cluster
- Check image name matches in the DaemonSet manifest

### Pods Stuck in "Pending"
- Check node resources: `kubectl describe nodes`
- Verify RBAC permissions are applied

### No Metrics Appearing
- Wait for training phase to complete (~5 minutes by default)
- Check pod logs for errors
- Verify Prometheus port-forward is active

## Support

For issues and questions, please open a [GitHub Issue](https://github.com/theujwalthakare/DIS/issues).
