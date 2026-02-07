# Cognitive Overlay DIS - System Architecture Diagram

```mermaid
%%{init: {'theme': 'base', 'themeVariables': { 'primaryColor': '#e8f5e9', 'secondaryColor': '#e3f2fd', 'tertiaryColor': '#fff3e0'}}}%%
flowchart TB
    subgraph external["🔬 External Zone"]
        direction LR
        researcher["👨‍🔬 Researcher"]
        training["📊 Training Pipeline<br/><i>generate_metrics.py</i>"]
    end

    subgraph cognitive["🧠 COGNITIVE OVERLAY LAYER"]
        direction TB
        
        subgraph sensing["🟢 SENSING LAYER<br/><i>(Artificial Dendritic Cells)</i>"]
            adc["🔭 ADC Agent<br/><b>DaemonSet</b><br/><i>agents/adc_agent.py</i>"]
            metrics_endpoint["📡 Metrics Endpoint<br/>:8000/metrics"]
        end
        
        subgraph detection["🔵 DETECTION LAYER<br/><i>(T-Helper Cells)</i>"]
            decision["🧮 DecisionEngine<br/><i>controller/controller.py</i>"]
            subgraph models["💾 Immune Memory<br/><i>(ML Models)</i>"]
                iforest["🌲 Isolation Forest<br/><i>iforest.joblib</i>"]
                autoenc["🔄 Autoencoder<br/><i>ae_sklearn.joblib</i>"]
            end
        end
        
        subgraph response["🟠 RESPONSE LAYER<br/><i>(B-Cell Effectors)</i>"]
            bcell_isolate["🔒 bcell_isolate()<br/><i>Quarantine pod</i>"]
            bcell_restart["🔄 bcell_restart()<br/><i>Delete & recreate</i>"]
            bcell_rollout["🚀 bcell_rollout()<br/><i>Rolling restart</i>"]
        end
    end

    subgraph observability["📈 OBSERVABILITY"]
        prometheus["📊 Prometheus<br/><i>Scrape metrics</i>"]
    end

    subgraph k8s["☸️ KUBERNETES CLUSTER"]
        direction TB
        
        subgraph workloads["📦 Target Workloads"]
            pods["🟦 Pods<br/><i>example-app</i>"]
            deployments["📋 Deployments<br/><i>ReplicaSets</i>"]
        end
        
        subgraph rbac["🔐 RBAC"]
            sa["👤 ServiceAccount<br/><i>adc-agent-sa</i>"]
            role["📜 Role<br/><i>simulate-role</i>"]
        end
        
        subgraph chaos["⚡ VALIDATION LAYER<br/><i>(Controlled Pathogens)</i>"]
            pod_kill["💀 PodChaos<br/><i>pod-kill.yaml</i>"]
            cpu_stress["🔥 StressChaos<br/><i>cpu-stress.yaml</i>"]
        end
    end

    %% Data Flows
    researcher -->|"Configure<br/>experiments"| training
    training -->|"Train models"| models
    
    adc -->|"Collect<br/>psutil metrics"| metrics_endpoint
    metrics_endpoint -->|"JSON metrics"| decision
    prometheus -.->|"Scrape"| metrics_endpoint
    
    decision -->|"Load"| models
    iforest -->|"Anomaly<br/>score"| decision
    autoenc -->|"Reconstruction<br/>error"| decision
    
    decision -->|"score < -0.5"| bcell_isolate
    decision -->|"score < -0.7"| bcell_restart
    decision -->|"score < -0.9"| bcell_rollout
    
    bcell_isolate -->|"PATCH labels"| pods
    bcell_restart -->|"DELETE pod"| pods
    bcell_rollout -->|"PATCH annotation"| deployments
    
    sa -->|"Authorize"| bcell_isolate
    sa -->|"Authorize"| bcell_restart
    sa -->|"Authorize"| bcell_rollout
    
    chaos -->|"Inject faults"| pods
    pod_kill -->|"Kill pods"| pods
    cpu_stress -->|"CPU stress"| pods

    %% Styling
    classDef sensing fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    classDef detection fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    classDef response fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    classDef chaos fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    classDef k8s fill:#e1f5fe,stroke:#0277bd,stroke-width:2px
    classDef observability fill:#fff9c4,stroke:#f9a825,stroke-width:2px
    
    class adc,metrics_endpoint sensing
    class decision,iforest,autoenc detection
    class bcell_isolate,bcell_restart,bcell_rollout response
    class pod_kill,cpu_stress chaos
    class pods,deployments,sa,role k8s
    class prometheus observability
```

## Layer Descriptions

| Layer | Biological Analog | Component | Function |
|-------|-------------------|-----------|----------|
| **Sensing** | Dendritic Cells | ADC Agent (DaemonSet) | Collects node metrics (CPU, memory, network, disk) as "antigens" |
| **Detection** | T-Helper Cells | DecisionEngine + ML Models | Evaluates antigens using Isolation Forest/Autoencoder to detect anomalies |
| **Response** | B-Cell Effectors | bcell_* functions | Executes adaptive responses via Kubernetes API |
| **Memory** | Immune Memory | Trained ML Models | Retains learned patterns for rapid future detection |
| **Validation** | Controlled Pathogens | Chaos Mesh | Injects faults to validate detection efficacy |

## Data Flow Summary

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  ADC Agent  │───▶│  Decision   │───▶│   B-Cell    │───▶│  K8s API    │
│  (Sensing)  │    │  Engine     │    │  Response   │    │  (Action)   │
│             │    │             │    │             │    │             │
│ psutil      │    │ IForest     │    │ isolate()   │    │ PATCH/DELETE│
│ :8000       │    │ Autoencoder │    │ restart()   │    │ pods/deploy │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
      │                  │                                      │
      │                  │                                      │
      ▼                  ▼                                      ▼
┌─────────────┐    ┌─────────────┐                        ┌─────────────┐
│ Prometheus  │    │ ML Models   │                        │ Target Pods │
│ (Observe)   │    │ (Memory)    │                        │ (Workloads) │
└─────────────┘    └─────────────┘                        └─────────────┘
```
