# DIS Architecture & Immune Mapping

This document explains the high-level mapping between biological immune system
concepts and the repository components.

## 📌 System Architecture Diagram

> **Figure 1:** High-level Cognitive Overlay DIS architecture showing the three immune-inspired layers and their interaction with the Kubernetes cluster.

![Cognitive Overlay Architecture](diagrams/cognitive-overlay-architecture.md)

For the full interactive Mermaid diagram, see: [diagrams/cognitive-overlay-architecture.md](diagrams/cognitive-overlay-architecture.md)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COGNITIVE OVERLAY DIS                                │
├─────────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────────────┐    │
│  │  🟢 ADC Agent   │───▶│  🔵 T-Helper     │───▶│  🟠 B-Cell Layer    │    │
│  │  (Sensing)      │    │  (Detection)     │    │  (Response)         │    │
│  │                 │    │                  │    │                     │    │
│  │  • psutil       │    │  • IsolationForest│   │  • bcell_isolate() │    │
│  │  • Metrics:8000 │    │  • Autoencoder   │    │  • bcell_restart() │    │
│  │  • JSON API     │    │  • score()       │    │  • bcell_rollout() │    │
│  └────────┬────────┘    └────────┬─────────┘    └──────────┬──────────┘    │
│           │                      │                         │               │
│           ▼                      ▼                         │               │
│  ┌─────────────────┐    ┌──────────────────┐              │               │
│  │  📊 Prometheus  │    │  💾 ML Models    │              │               │
│  │  (Observability)│    │  (Immune Memory) │              │               │
│  └─────────────────┘    └──────────────────┘              │               │
├───────────────────────────────────────────────────────────┼───────────────┤
│                    KUBERNETES CLUSTER                      │ K8s API       │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐  │               │
│  │ 📦 Target Pods│  │ 📋 Deployments│  │ ⚡ Chaos Mesh │◀─┘               │
│  │ (example-app) │  │ (ReplicaSets) │  │ (Validation)  │                  │
│  └───────────────┘  └───────────────┘  └───────────────┘                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

- ADC (artificial Dendritic Cell): `agents/adc_agent.py` — runs on each node,
  collects local metrics (antigens) and exposes them for evaluation.
- T-Helper layer: `ml/` models (Isolation Forest, Autoencoder) + `controller/` —
  evaluates presented antigens to decide if behavior is anomalous.
- B-Cell layer: `controller/bcell_*` logic (in `controller/controller.py`) —
  triggers adaptive responses (isolate, restart, replace pods) and records
  memory (e.g., models or signatures) for future rapid responses.
- Chaos experiments: `chaos/` — controlled injections used during evaluation to
  validate detection and response efficacy.
- Observability: `cluster/prometheus/` — example Prometheus scrape config.

Design principles:

- Modularity: each layer is separated to allow independent experimentation.
- Reproducibility: scripts and manifests are intended to be parameterized for
  repeatable experiments.
- Explainability: simple, well-documented models are preferred for research.
