# Examples

This directory contains example deployments and configurations for testing DIS.

## Test Application

The `test-app.yaml` deploys a simple Nginx-based application that can be used to test DIS functionality.

```bash
# Deploy test application
kubectl apply -f test-app.yaml

# Verify deployment
kubectl get pods -l app=test-app

# Generate some traffic
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl http://test-app-service
```

## Usage with DIS

Once DIS agents are deployed, they will automatically:

1. Monitor the test-app pods
2. Collect CPU, memory, and network metrics
3. Detect anomalies when chaos experiments are applied
4. Trigger adaptive responses (isolate/restart)

## Chaos Testing

Combine with Chaos Mesh experiments:

```bash
# Apply CPU stress to test-app
kubectl apply -f ../chaos-mesh/experiments.yaml

# Watch DIS logs
kubectl logs -n dis-system -l app=dis-agent -f

# Check metrics
kubectl port-forward -n dis-system svc/dis-metrics 8000:8000
# Visit http://localhost:8000/metrics
```

## Cleanup

```bash
kubectl delete -f test-app.yaml
```
