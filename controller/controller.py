"""
T-Helper decision logic and B-Cell response engine skeleton.

This module demonstrates how a T-Helper layer might load unsupervised models
and make decisions; when an anomaly is confirmed the B-Cell response engine
translates decisions into Kubernetes actions (isolate/restart/replace pod).

In a real experiment, replace print() calls with Kubernetes client operations
and integrate with the aDC agent via an API or message bus.
"""
import joblib
import os
import numpy as np
import time
from datetime import datetime

try:
    from kubernetes import client, config
except Exception:
    client = None
    config = None

class DecisionEngine:
    def __init__(self, iforest_path=None, ae_path=None):
        self.iforest = joblib.load(iforest_path) if iforest_path and os.path.exists(iforest_path) else None
        self.ae_path = ae_path

    def score(self, features: np.ndarray):
        scores = {}
        if self.iforest:
            scores['iforest'] = self.iforest.score_samples(features.reshape(1, -1))[0]
        # Add autoencoder reconstruction error scoring here if available
        return scores

    def decide_response(self, scores):
        # Simple threshold logic for demonstration; research should replace with
        # statistically-justified combination logic and uncertainty handling.
        if 'iforest' in scores and scores['iforest'] < -0.5:
            return 'isolate'
        return 'monitor'

def bcell_apply(action, pod_name, namespace='default'):
    # Map immune response to Kubernetes commands. When running inside a
    # cluster or with a kubeconfig available, the kubernetes python client is
    # used; otherwise we fallback to printing (useful for local testing).
    if client is None or config is None:
        print(f"[B-Cell] (no k8s client) {action} -> {pod_name} in {namespace}")
        return

    core_v1, apps_v1 = init_k8s_client()

    try:
        if action == 'isolate':
            bcell_isolate(core_v1, pod_name, namespace)
        elif action == 'restart':
            bcell_restart(core_v1, pod_name, namespace)
        elif action == 'replace':
            # For replace we attempt a rollout restart of the owning deployment.
            deployment = get_owner_deployment(core_v1, apps_v1, pod_name, namespace)
            if deployment:
                bcell_rollout_restart(apps_v1, deployment, namespace)
            else:
                # fallback to restart pod
                bcell_restart(core_v1, pod_name, namespace)
        else:
            print(f"[B-Cell] Unknown action {action} for {pod_name}")
    except Exception as e:
        print(f"[B-Cell] Error applying {action} to {pod_name}: {e}")


def init_k8s_client():
    """Initialize and return (CoreV1Api, AppsV1Api).

    Tries in-cluster config then falls back to kubeconfig.
    """
    try:
        config.load_incluster_config()
    except Exception:
        try:
            config.load_kube_config()
        except Exception:
            raise RuntimeError('Could not load Kubernetes configuration')

    return client.CoreV1Api(), client.AppsV1Api()


def bcell_isolate(core_v1, pod_name, namespace='default'):
    """Patch the pod to add an isolation label (research hook).

    Network-level isolation should be implemented separately (NetworkPolicy),
    but labeling a pod provides a clear artifact for experiments and policies.
    """
    body = {"metadata": {"labels": {"dis/isolated": "true"}}}
    core_v1.patch_namespaced_pod(name=pod_name, namespace=namespace, body=body)
    print(f"[B-Cell] Patched pod {pod_name} with dis/isolated=true")


def bcell_restart(core_v1, pod_name, namespace='default'):
    """Delete the pod to trigger a restart by its controller (Deployment/ReplicaSet).
    """
    core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace, body=client.V1DeleteOptions(grace_period_seconds=5))
    print(f"[B-Cell] Deleted pod {pod_name} to trigger restart")


def get_owner_deployment(core_v1, apps_v1, pod_name, namespace='default'):
    """Return the deployment name owning the pod if available.

    We look up the pod's ownerReferences and then search for a Deployment.
    """
    pod = core_v1.read_namespaced_pod(name=pod_name, namespace=namespace)
    owners = pod.metadata.owner_references or []
    for owner in owners:
        # ReplicaSet owner typically points to a ReplicaSet; check its owner
        if owner.kind == 'ReplicaSet':
            rs = apps_v1.read_namespaced_replica_set(name=owner.name, namespace=namespace)
            rs_owners = rs.metadata.owner_references or []
            for ro in rs_owners:
                if ro.kind == 'Deployment':
                    return ro.name
        if owner.kind == 'Deployment':
            return owner.name
    return None


def bcell_rollout_restart(apps_v1, deployment_name, namespace='default'):
    """Trigger a rollout restart by patching the deployment template annotation.
    """
    timestamp = datetime.utcnow().isoformat() + 'Z'
    body = {
        "spec": {
            "template": {
                "metadata": {
                    "annotations": {
                        "dis/restartedAt": timestamp
                    }
                }
            }
        }
    }
    apps_v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=body)
    print(f"[B-Cell] Triggered rollout restart for deployment {deployment_name}")

if __name__ == '__main__':
    de = DecisionEngine(iforest_path='ml/models/iforest.joblib')
    # Example usage
    sample = np.array([0.1, 0.2, 0.3])
    scores = de.score(sample)
    action = de.decide_response(scores)
    bcell_apply(action, 'example-pod')
