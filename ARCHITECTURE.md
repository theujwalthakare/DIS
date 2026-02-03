# Architecture Documentation

## System Design

The Digital Immune System (DIS) follows a three-layer architecture inspired by biological immune systems:

### Layer 1: Innate Immunity (aDC Agents)

**Purpose**: Rapid, non-specific threat detection through continuous monitoring

**Components**:
- Per-node DaemonSet deployment
- Metric collectors (CPU, memory, network, pod events)
- Local antigen buffering

**Key Design Decisions**:
- DaemonSet ensures one agent per node
- hostNetwork/hostPID for system-level metrics
- Privileged mode for psutil access
- 10-second collection interval balances timeliness vs overhead

### Layer 2: Adaptive Immunity (T-Helper)

**Purpose**: Learned threat detection via unsupervised ML

**Components**:
1. **Isolation Forest**
   - Fast, tree-based anomaly detection
   - O(log n) inference time
   - Effective for high-dimensional data
   - No assumptions about data distribution

2. **Autoencoder**
   - Neural network (input → bottleneck → output)
   - Learns normal behavior patterns
   - Anomalies have high reconstruction error
   - Adaptive threshold (95th percentile)

**Ensemble Strategy**:
- Majority voting for consensus
- Single detector flagging for aggressive mode
- Reduces false positives while maintaining sensitivity

### Layer 3: Memory Response (B-Cell)

**Purpose**: Adaptive responses with learning from past incidents

**Components**:
- Memory cells (threat signature → response mapping)
- Response executor (isolate, restart, none)
- Quarantine manager

**Response Actions**:
1. **Isolate** (High Severity)
   - Add `dis-quarantine=true` label
   - Create NetworkPolicy blocking all traffic
   - Pod remains running but isolated

2. **Restart** (Medium Severity)
   - Delete pod (gracePeriodSeconds=0)
   - Controller recreates pod
   - Fresh state, potentially resolves issue

3. **None** (Low Severity)
   - Log only
   - Memory recorded for future reference
   - Avoid unnecessary disruption

## Data Flow

```
1. aDC collects metrics
   ↓
2. Convert to feature vector [cpu, mem, net, pod_events]
   ↓
3. T-Helper analyzes features
   ↓
4. If anomaly detected:
   ↓
5. Compute threat signature (MD5 of features)
   ↓
6. B-Cell recalls memory
   ↓
7. Execute response (learned or severity-based)
   ↓
8. Store outcome in memory
   ↓
9. Update Prometheus metrics
```

## Machine Learning Models

### Isolation Forest

**Algorithm**:
1. Randomly select feature
2. Randomly select split value between min/max
3. Recursively partition data
4. Anomalies require fewer splits (isolated earlier)

**Parameters**:
- `contamination=0.1`: Expect 10% of data to be anomalous
- `n_estimators=100`: Use 100 trees (ensemble)
- `random_state=42`: Reproducibility

**Training**:
- Unsupervised (no labels needed)
- Fits StandardScaler + IsolationForest
- 5-minute baseline collection (~30 samples)

### Autoencoder

**Architecture**:
```
Input (4) → Dense(16, relu) → Dense(8, relu) 
          ↓
Dense(16, relu) ← Dense(8, relu) ← Encoded(8)
          ↓
Output (4, sigmoid)
```

**Loss**: Mean Squared Error (reconstruction)

**Anomaly Detection**:
- Calculate reconstruction error for input
- If error > threshold (95th percentile): anomaly
- Threshold computed on training data

**Training**:
- 50 epochs, batch size 32
- Adam optimizer
- 10% validation split

## Kubernetes Integration

### RBAC Permissions

DIS requires:
- **Read**: pods, nodes, events (monitoring)
- **Write**: pods (restart)
- **Create/Delete**: networkpolicies (isolation)

### Resource Limits

Per agent:
- **Requests**: 256MB RAM, 100m CPU
- **Limits**: 512MB RAM, 500m CPU

Typical cluster usage:
- 3-node cluster: ~768MB RAM, 300m CPU
- Metrics collection: ~1MB/min/node
- Model storage: ~10MB per node

### Deployment Strategy

**DaemonSet Benefits**:
- Automatic scaling with cluster
- Node-local monitoring (low latency)
- Fault isolation (one agent failure ≠ system failure)

**Alternatives Considered**:
- ❌ Single deployment: Single point of failure
- ❌ ReplicaSet: Doesn't guarantee per-node coverage
- ✅ DaemonSet: Optimal for per-node agents

## Prometheus Metrics

### Metric Types

1. **Counter** (monotonically increasing)
   - `dis_antigens_collected_total`
   - `dis_anomalies_detected_total`
   - `dis_responses_executed_total`

2. **Gauge** (can go up/down)
   - `dis_node_cpu_usage_percent`
   - `dis_node_memory_usage_percent`
   - `dis_quarantined_pods_current`

3. **Histogram** (distribution)
   - `dis_detection_latency_seconds`

### Alerting Rules (Example)

```yaml
groups:
- name: dis_alerts
  rules:
  - alert: HighAnomalyRate
    expr: rate(dis_anomalies_detected_total[5m]) > 0.1
    annotations:
      summary: "High anomaly detection rate"
  
  - alert: DISAgentDown
    expr: up{job="dis-agent"} == 0
    annotations:
      summary: "DIS agent is down"
```

## Chaos Mesh Integration

### Supported Experiments

1. **StressChaos**: CPU/memory stress
2. **PodChaos**: Pod kill/failure
3. **NetworkChaos**: Latency, partition, loss
4. **TimeChaos**: Clock skew
5. **IOChaos**: Disk I/O errors

### Testing Strategy

1. **Baseline**: Collect normal metrics (5 min)
2. **Inject**: Apply chaos experiment (2 min)
3. **Detect**: Verify DIS detects anomaly
4. **Respond**: Verify appropriate response
5. **Recover**: Verify system returns to normal
6. **Validate**: Check metrics and logs

## Security Considerations

### Threat Model

**In Scope**:
- Resource exhaustion attacks
- Malfunctioning pods
- Configuration errors causing anomalies
- Network-level anomalies

**Out of Scope**:
- Direct attacks on DIS components
- Kubernetes API server compromise
- Host OS kernel exploits
- Malicious DIS configuration

### Security Mechanisms

1. **RBAC**: Minimal required permissions
2. **Network Policies**: Isolate quarantined pods
3. **Pod Security**: Non-root user (TODO)
4. **Audit Logging**: All actions logged
5. **Metrics Authentication**: Prometheus mTLS (optional)

## Performance Optimization

### Memory Management

- Antigen buffer: Max 1000 samples per node
- Model size: ~5MB (Isolation Forest) + ~5MB (Autoencoder)
- Memory cells: Auto-expire after 24h

### CPU Optimization

- Metric collection: Non-blocking, threaded
- Model inference: Batched (every 30s)
- Network policies: Lazy creation

### Scalability

Tested configurations:
- ✅ 1-10 nodes: Excellent
- ✅ 10-50 nodes: Good (tested up to 20)
- ⚠️ 50-100 nodes: Requires tuning
- ❌ 100+ nodes: Consider centralized architecture

## Future Enhancements

1. **Multi-cluster support**: Federated learning across clusters
2. **Advanced ML models**: LSTMs for time-series, GANs for generation
3. **Explainable AI**: SHAP values for anomaly explanations
4. **Human-in-the-loop**: Manual approval for high-impact actions
5. **Cost optimization**: Evict low-priority pods before restarts
6. **Integration**: ServiceMesh (Istio), APM tools

## References

- Artificial Immune Systems: [de Castro & Timmis, 2002]
- Isolation Forest: [Liu et al., 2008]
- Autoencoders for Anomaly Detection: [Sakurada & Yairi, 2014]
- Chaos Engineering: [Principles of Chaos Engineering, 2017]
