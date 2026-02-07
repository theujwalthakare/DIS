"""
Detection Latency Measurement for DIS Publication.

Measures time-to-detect from anomaly onset, simulating real-world detection
scenarios. Computes:
- Per-sample detection latency (inference time)
- Time to first detection in anomaly sequences
- Detection delay statistics (mean, median, 95th percentile)

Usage:
  python analysis/measure_latency.py

Output:
  - results/latency_metrics.csv
  - results/figures/latency_distribution.png
  - Console output with latency statistics
"""
import time
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
DATA_CSV = ROOT / 'data' / 'metrics.csv'
RESULTS = ROOT / 'results'
FIG_DIR = RESULTS / 'figures'
FIG_DIR.mkdir(parents=True, exist_ok=True)


def load_data():
    """Load metrics CSV with ground truth labels."""
    if not DATA_CSV.exists():
        raise FileNotFoundError(f"Missing data file: {DATA_CSV}")
    return pd.read_csv(DATA_CSV)


def load_models():
    """Load trained models."""
    models = {}
    
    iforest_paths = [RESULTS / 'iforest.joblib', ROOT / 'ml' / 'models' / 'iforest.joblib']
    for p in iforest_paths:
        if p.exists():
            models['iforest'] = joblib.load(p)
            break
    
    ae_paths = [RESULTS / 'ae_sklearn.joblib', ROOT / 'ml' / 'models' / 'ae_sklearn.joblib']
    for p in ae_paths:
        if p.exists():
            models['ae_sklearn'] = joblib.load(p)
            break
    
    return models


def identify_anomaly_sequences(labels):
    """
    Identify contiguous sequences of anomalies.
    Returns list of (start_idx, end_idx) tuples.
    """
    sequences = []
    in_sequence = False
    start_idx = 0
    
    for i, label in enumerate(labels):
        if label == 1 and not in_sequence:
            # Start of new anomaly sequence
            in_sequence = True
            start_idx = i
        elif label == 0 and in_sequence:
            # End of anomaly sequence
            in_sequence = False
            sequences.append((start_idx, i - 1))
    
    # Handle sequence that extends to end
    if in_sequence:
        sequences.append((start_idx, len(labels) - 1))
    
    return sequences


def measure_inference_latency(models, X, n_iterations=100):
    """
    Measure single-sample inference latency for each model.
    Returns latency statistics in milliseconds.
    """
    results = {}
    
    # Test on a subset of samples
    sample_indices = np.random.choice(len(X), min(n_iterations, len(X)), replace=False)
    
    for model_name, model in models.items():
        latencies = []
        
        for idx in sample_indices:
            sample = X[idx:idx+1]  # Single sample
            
            start_time = time.perf_counter()
            
            if model_name == 'iforest':
                _ = model.score_samples(sample)
            elif model_name == 'ae_sklearn':
                ae = model
                model_obj = ae.get('model') if isinstance(ae, dict) else ae
                scaler = ae.get('scaler') if isinstance(ae, dict) else None
                Xs = scaler.transform(sample) if scaler is not None else sample
                recon = model_obj.predict(Xs)
                _ = np.mean((Xs - recon) ** 2)
            
            end_time = time.perf_counter()
            latencies.append((end_time - start_time) * 1000)  # Convert to ms
        
        results[model_name] = {
            'latencies': np.array(latencies),
            'mean_ms': np.mean(latencies),
            'median_ms': np.median(latencies),
            'std_ms': np.std(latencies),
            'p95_ms': np.percentile(latencies, 95),
            'p99_ms': np.percentile(latencies, 99),
            'min_ms': np.min(latencies),
            'max_ms': np.max(latencies)
        }
    
    # Ensemble latency (sum of individual models)
    if len(models) >= 2:
        total_latencies = np.zeros(len(sample_indices))
        for model_results in results.values():
            total_latencies += model_results['latencies']
        
        results['ensemble'] = {
            'latencies': total_latencies,
            'mean_ms': np.mean(total_latencies),
            'median_ms': np.median(total_latencies),
            'std_ms': np.std(total_latencies),
            'p95_ms': np.percentile(total_latencies, 95),
            'p99_ms': np.percentile(total_latencies, 99),
            'min_ms': np.min(total_latencies),
            'max_ms': np.max(total_latencies)
        }
    
    return results


def measure_detection_delay(models, X, labels, threshold_percentile=90):
    """
    Measure detection delay: samples from anomaly onset to detection.
    Uses threshold at given percentile of normal data scores.
    """
    # Compute scores on all data
    scores = {}
    
    if 'iforest' in models:
        scores['iforest'] = -models['iforest'].score_samples(X)
    
    if 'ae_sklearn' in models:
        ae = models['ae_sklearn']
        model = ae.get('model') if isinstance(ae, dict) else ae
        scaler = ae.get('scaler') if isinstance(ae, dict) else None
        Xs = scaler.transform(X) if scaler is not None else X
        recon = model.predict(Xs)
        scores['ae_sklearn'] = np.mean((Xs - recon) ** 2, axis=1)
    
    # Ensemble score (normalized average)
    if len(scores) >= 2:
        normalized = []
        for s in scores.values():
            s_norm = (s - s.min()) / (s.max() - s.min() + 1e-10)
            normalized.append(s_norm)
        scores['ensemble'] = np.mean(normalized, axis=0)
    
    # Determine thresholds from normal data
    normal_mask = labels == 0
    thresholds = {}
    for name, s in scores.items():
        thresholds[name] = np.percentile(s[normal_mask], threshold_percentile)
    
    # Find anomaly sequences
    sequences = identify_anomaly_sequences(labels)
    
    # Measure delay for each sequence
    delay_results = {name: [] for name in scores.keys()}
    
    for start_idx, end_idx in sequences:
        for name, s in scores.items():
            threshold = thresholds[name]
            detected = False
            for offset, idx in enumerate(range(start_idx, end_idx + 1)):
                if s[idx] >= threshold:
                    delay_results[name].append(offset)
                    detected = True
                    break
            if not detected:
                # Anomaly sequence not detected, record as sequence length (max delay)
                delay_results[name].append(end_idx - start_idx + 1)
    
    # Compute statistics
    stats = {}
    for name, delays in delay_results.items():
        if delays:
            delays = np.array(delays)
            stats[name] = {
                'delays': delays,
                'mean_samples': np.mean(delays),
                'median_samples': np.median(delays),
                'max_samples': np.max(delays),
                'detection_rate': np.mean(delays < (end_idx - start_idx + 1)) if sequences else 0,
                'n_sequences': len(sequences)
            }
    
    return stats, sequences


def plot_latency_distribution(latency_results):
    """Plot inference latency distributions."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    colors = ['#2563eb', '#dc2626', '#16a34a']
    positions = []
    labels = []
    
    for i, (name, data) in enumerate(latency_results.items()):
        bp = ax.boxplot(data['latencies'], positions=[i], widths=0.6, 
                       patch_artist=True)
        bp['boxes'][0].set_facecolor(colors[i % len(colors)])
        bp['boxes'][0].set_alpha(0.7)
        positions.append(i)
        labels.append(name.replace('_', ' ').title())
    
    ax.set_xticks(positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel('Inference Latency (ms)')
    ax.set_title('Single-Sample Detection Latency Distribution')
    ax.grid(True, axis='y', alpha=0.3)
    
    # Add statistics annotation
    for i, (name, data) in enumerate(latency_results.items()):
        ax.annotate(f"μ={data['mean_ms']:.3f}ms\np95={data['p95_ms']:.3f}ms",
                   xy=(i, data['p95_ms']), xytext=(i + 0.3, data['p95_ms'] * 1.1),
                   fontsize=9, ha='left')
    
    fig.tight_layout()
    out_path = FIG_DIR / 'latency_distribution.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved latency distribution to {out_path}")
    plt.close(fig)


def plot_detection_delay(delay_stats):
    """Plot detection delay histogram."""
    fig, ax = plt.subplots(figsize=(10, 5))
    
    colors = ['#2563eb', '#dc2626', '#16a34a']
    
    for i, (name, data) in enumerate(delay_stats.items()):
        ax.hist(data['delays'], bins=15, alpha=0.6, 
               label=f"{name.replace('_', ' ').title()} (μ={data['mean_samples']:.1f})",
               color=colors[i % len(colors)])
    
    ax.set_xlabel('Detection Delay (samples from anomaly onset)')
    ax.set_ylabel('Frequency')
    ax.set_title('Time-to-Detection After Anomaly Onset')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    fig.tight_layout()
    out_path = FIG_DIR / 'detection_delay.png'
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    print(f"✓ Saved detection delay plot to {out_path}")
    plt.close(fig)


def save_latency_csv(latency_results, delay_stats):
    """Save latency metrics to CSV."""
    rows = []
    
    for name, data in latency_results.items():
        rows.append({
            'Model': name.replace('_', ' ').title(),
            'Metric_Type': 'Inference_Latency',
            'Mean_ms': data['mean_ms'],
            'Median_ms': data['median_ms'],
            'Std_ms': data['std_ms'],
            'P95_ms': data['p95_ms'],
            'P99_ms': data['p99_ms'],
            'Min_ms': data['min_ms'],
            'Max_ms': data['max_ms']
        })
    
    for name, data in delay_stats.items():
        rows.append({
            'Model': name.replace('_', ' ').title(),
            'Metric_Type': 'Detection_Delay',
            'Mean_samples': data['mean_samples'],
            'Median_samples': data['median_samples'],
            'Max_samples': data['max_samples'],
            'Detection_Rate': data['detection_rate'],
            'N_Sequences': data['n_sequences']
        })
    
    df = pd.DataFrame(rows)
    out_path = RESULTS / 'latency_metrics.csv'
    df.to_csv(out_path, index=False)
    print(f"✓ Saved latency metrics to {out_path}")
    return df


def print_latency_summary(latency_results, delay_stats):
    """Print formatted latency summary."""
    print("\n" + "="*70)
    print("DIS DETECTION LATENCY - PUBLICATION SUMMARY")
    print("="*70)
    
    print("\n1. INFERENCE LATENCY (single-sample detection time)")
    print("-"*70)
    print(f"{'Model':<20} {'Mean':>10} {'Median':>10} {'P95':>10} {'P99':>10}")
    print("-"*70)
    
    for name, data in latency_results.items():
        print(f"{name:<20} {data['mean_ms']:>9.3f}ms {data['median_ms']:>9.3f}ms "
              f"{data['p95_ms']:>9.3f}ms {data['p99_ms']:>9.3f}ms")
    
    print("-"*70)
    
    print("\n2. DETECTION DELAY (samples from anomaly onset to detection)")
    print("-"*70)
    print(f"{'Model':<20} {'Mean':>12} {'Median':>12} {'Max':>10} {'Det.Rate':>10}")
    print("-"*70)
    
    for name, data in delay_stats.items():
        print(f"{name:<20} {data['mean_samples']:>10.1f}s {data['median_samples']:>10.1f}s "
              f"{data['max_samples']:>8.0f}s {data['detection_rate']*100:>9.1f}%")
    
    print("-"*70)
    print("="*70)


def main():
    print("="*70)
    print("DIS Detection Latency Measurement")
    print("="*70 + "\n")
    
    # Load data
    df = load_data()
    labels = df['label'].values.astype(int)
    feature_cols = [c for c in df.columns if c != 'label']
    X = df[feature_cols].select_dtypes(include=['number']).fillna(0).values
    
    print(f"Loaded {len(labels)} samples ({np.sum(labels)} anomalies)")
    
    # Load models
    print("\nLoading models...")
    models = load_models()
    
    if not models:
        raise RuntimeError("No models found. Run training scripts first.")
    
    for name in models:
        print(f"  ✓ {name}")
    
    # Measure inference latency
    print("\nMeasuring inference latency (100 iterations)...")
    latency_results = measure_inference_latency(models, X, n_iterations=100)
    
    # Measure detection delay
    print("Measuring detection delay...")
    delay_stats, sequences = measure_detection_delay(models, X, labels)
    print(f"  Found {len(sequences)} anomaly sequences")
    
    # Generate visualizations
    print("\nGenerating visualizations...")
    plot_latency_distribution(latency_results)
    plot_detection_delay(delay_stats)
    
    # Save metrics
    save_latency_csv(latency_results, delay_stats)
    
    # Print summary
    print_latency_summary(latency_results, delay_stats)


if __name__ == '__main__':
    main()
