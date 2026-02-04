"""
Simulate detection and invoke `controller` B-Cell responses.

Usage examples:
  # use existing iforest model and kubeconfig
  python scripts/simulate_detection.py --label app=example-app --iforest ml/models/iforest.joblib

The script will:
 - find a pod matching the label
 - load the last numeric row from `data/metrics.csv` as features
 - score using the Isolation Forest model if present
 - decide an action via `controller.DecisionEngine` and call `controller.bcell_apply`

This provides a minimal end-to-end exercise for the detection->response flow.
"""
import argparse
import csv
import os
import random
import sys

try:
    import joblib
except Exception:
    joblib = None

try:
    from kubernetes import client, config
except Exception:
    client = None
    config = None

from controller.controller import DecisionEngine, bcell_apply


def read_last_numeric_row(path):
    if not os.path.exists(path):
        return None
    with open(path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        if not rows:
            return None
        last = rows[-1]
        vals = []
        for k, v in last.items():
            try:
                vals.append(float(v))
            except Exception:
                continue
        return vals


def find_pod_by_label(label_selector, namespace='default'):
    if client is None or config is None:
        print('[simulate] Kubernetes client not available; returning placeholder pod')
        return 'example-pod'

    try:
        try:
            config.load_kube_config()
        except Exception:
            config.load_incluster_config()
    except Exception as e:
        print(f'[simulate] Could not load kube config: {e}')
        return None

    v1 = client.CoreV1Api()
    pods = v1.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
    items = pods.items or []
    if not items:
        print(f'[simulate] No pods found for label {label_selector} in {namespace}')
        return None
    # pick first pod
    return items[0].metadata.name


def main(args):
    features = read_last_numeric_row('data/metrics.csv')
    de = DecisionEngine(iforest_path=args.iforest if args.iforest else None)

    if features is not None and de.iforest is not None:
        import numpy as np
        arr = np.array(features)
        scores = de.score(arr)
        action = de.decide_response(scores)
        print('[simulate] Scores:', scores, '-> action:', action)
    else:
        # fallback: random small probability of isolation/restart for demo
        action = random.choice(['monitor', 'monitor', 'isolate', 'restart'])
        print('[simulate] Fallback action:', action)

    pod = find_pod_by_label(args.label, namespace=args.namespace)
    if pod is None:
        print('[simulate] No pod to apply action to; exiting')
        sys.exit(1)

    bcell_apply(action, pod, namespace=args.namespace)


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--label', default='app=example-app')
    p.add_argument('--namespace', default='default')
    p.add_argument('--iforest', default='ml/models/iforest.joblib')
    args = p.parse_args()
    main(args)
