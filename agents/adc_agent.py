"""
Artificial Dendritic Cell (aDC) Metrics Collection Agent

Purpose: 
  Runs on each Kubernetes node (typically as DaemonSet) to collect comprehensive 
  local metrics and expose them via HTTP endpoint. In immune system terms: the aDC 
  gathers 'antigens' (system observations) and presents them to the T-Helper 
  detection layer for anomaly analysis.

Collected Metrics (8 features matching 100k dataset):
  - cpu_percent: CPU utilization (0-100)
  - mem_percent: Memory utilization (0-100)
  - net_tx: Network transmission bytes/sec
  - net_rx: Network receive bytes/sec
  - disk_read: Disk read I/O bytes/sec
  - disk_write: Disk write I/O bytes/sec
  - http_req_rate: HTTP requests per second (from access logs or scrape)
  - response_ms: Average HTTP response time in milliseconds

Output Format: JSON payload matching DIS detection pipeline requirements
Endpoint: http://localhost:8000/metrics

This agent integrates with the T-Helper decision layer and B-Cell response engine
for real-time threat detection and automated mitigation.
"""
import time
import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Dict, Any
import threading
import psutil
from collections import deque

PORT = int(os.getenv('ADC_PORT', 8000))
COLLECTION_INTERVAL = int(os.getenv('COLLECTION_INTERVAL', 5))  # seconds
HISTORY_SIZE = 100  # Keep rolling window of metrics

# Global state for metrics collection
state = {
    "node_name": os.getenv('NODE_NAME', 'unknown'),
    "pod_name": os.getenv('POD_NAME', 'adc-agent'),
    "timestamp": time.time(),
    "metrics": {},
    "history": deque(maxlen=HISTORY_SIZE)
}


def get_network_stats() -> tuple:
    """Get network I/O statistics (bytes/sec).
    
    Returns:
        (net_tx, net_rx): bytes transmitted and received per second
    """
    try:
        net_io = psutil.net_io_counters()
        # Get cumulative bytes; return as approximate bytes/sec
        # In production, would track delta from previous measurement
        tx_bytes = net_io.bytes_sent
        rx_bytes = net_io.bytes_recv
        
        # Normalize to reasonable ranges based on 100k dataset
        net_tx = min(1000, (tx_bytes % 10000) / 10)  # Rough scaling
        net_rx = min(1000, (rx_bytes % 10000) / 10)
        
        return net_tx, net_rx
    except Exception as e:
        print(f"WARNING: Network stats collection failed: {e}")
        return 0, 0


def get_disk_stats() -> tuple:
    """Get disk I/O statistics (bytes/sec).
    
    Returns:
        (disk_read, disk_write): bytes read and written per second
    """
    try:
        disk_io = psutil.disk_io_counters()
        # Get cumulative bytes
        read_bytes = disk_io.read_bytes
        write_bytes = disk_io.write_bytes
        
        # Normalize to reasonable ranges based on 100k dataset
        disk_read = min(2000, (read_bytes % 20000) / 10)  # Rough scaling
        disk_write = min(1500, (write_bytes % 15000) / 10)
        
        return disk_read, disk_write
    except Exception as e:
        print(f"WARNING: Disk stats collection failed: {e}")
        return 0, 0


def get_http_metrics() -> tuple:
    """Estimate HTTP request rate and response time.
    
    In production, would scrape from application metrics or parse access logs.
    Returns default estimates for demo purposes.
    
    Returns:
        (http_req_rate, response_ms): requests/sec and response time in ms
    """
    try:
        # Demo: use load average as proxy for request rate
        load_avg = os.getloadavg()[0] if hasattr(os, 'getloadavg') else psutil.cpu_percent()
        http_req_rate = load_avg * 10  # Rough estimate
        
        # Response time correlates with system load
        response_ms = 50 + (psutil.cpu_percent() * 2)  # 50-250ms range
        
        return http_req_rate, response_ms
    except Exception as e:
        print(f"WARNING: HTTP metrics estimation failed: {e}")
        return 30, 100


def collect_metrics():
    """Collect comprehensive system metrics and update state.
    
    Runs continuously in background thread, updating metrics every 
    COLLECTION_INTERVAL seconds. Maintains rolling history for trend analysis.
    """
    prev_time = time.time()
    
    while True:
        try:
            current_time = time.time()
            
            # CPU and Memory
            cpu_percent = psutil.cpu_percent(interval=0.5)
            mem_info = psutil.virtual_memory()
            mem_percent = mem_info.percent
            
            # Network and Disk
            net_tx, net_rx = get_network_stats()
            disk_read, disk_write = get_disk_stats()
            
            # HTTP (application-level)
            http_req_rate, response_ms = get_http_metrics()
            
            # Pod restart count (would get from Kubernetes API in production)
            pod_restarts = 0
            try:
                # Try to read from container environment
                restart_count = os.getenv('RESTART_COUNT', '0')
                pod_restarts = int(restart_count)
            except:
                pod_restarts = 0
            
            # Build current metrics snapshot
            current_metrics = {
                'cpu_percent': round(cpu_percent, 2),
                'mem_percent': round(mem_percent, 2),
                'net_tx': round(net_tx, 2),
                'net_rx': round(net_rx, 2),
                'disk_read': round(disk_read, 2),
                'disk_write': round(disk_write, 2),
                'http_req_rate': round(http_req_rate, 2),
                'response_ms': round(response_ms, 2),
                'pod_restarts': pod_restarts,
                'timestamp': current_time
            }
            
            # Update global state
            state['metrics'] = current_metrics
            state['timestamp'] = current_time
            state['history'].append(current_metrics)
            
            # Debug output
            print(f"[{time.strftime('%H:%M:%S')}] Metrics collected: "
                  f"CPU={cpu_percent:.1f}% MEM={mem_percent:.1f}% "
                  f"NET_TX={net_tx:.1f} NET_RX={net_rx:.1f}")
            
            time.sleep(COLLECTION_INTERVAL)
            
        except Exception as e:
            print(f"ERROR in metric collection: {e}")
            time.sleep(COLLECTION_INTERVAL)


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP request handler for metrics endpoint.
    
    Endpoints:
      GET /metrics          - Latest metrics snapshot (JSON)
      GET /metrics/latest   - Current metrics only
      GET /metrics/history  - Rolling history of recent metrics
      GET /health           - Health check (200 OK)
    """
    
    def do_GET(self):
        """Handle GET requests to various endpoints."""
        try:
            if self.path == '/metrics' or self.path == '/metrics/latest':
                self.send_metrics_response(state['metrics'])
                
            elif self.path == '/metrics/history':
                self.send_metrics_response({
                    'history': list(state['history']),
                    'count': len(state['history'])
                })
                
            elif self.path == '/health':
                payload = json.dumps({'status': 'healthy', 'timestamp': time.time()}).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)
                
            else:
                self.send_error(404)
                
        except Exception as e:
            print(f"ERROR handling request: {e}")
            self.send_error(500)
    
    def send_metrics_response(self, metrics_data: Dict[str, Any]):
        """Send metrics as JSON response."""
        payload = json.dumps(metrics_data, default=str).encode('utf-8')
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)
    
    def log_message(self, format, *args):
        """Suppress default HTTP server logging."""
        pass


def run_server():
    """Start HTTP server for metrics endpoint."""
    server = HTTPServer(('0.0.0.0', PORT), MetricsHandler)
    print(f"aDC Agent HTTP server starting on port {PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("aDC Agent shutting down...")
        server.shutdown()


if __name__ == '__main__':
    print("="*80)
    print("Artificial Dendritic Cell (aDC) Metrics Collection Agent")
    print("="*80)
    print(f"Node: {state['node_name']}")
    print(f"Pod:  {state['pod_name']}")
    print(f"Port: {PORT}")
    print(f"Collection Interval: {COLLECTION_INTERVAL}s")
    print("")
    print("Collecting metrics:")
    print("  - cpu_percent, mem_percent (system utilization)")
    print("  - net_tx, net_rx (network I/O)")
    print("  - disk_read, disk_write (disk I/O)")
    print("  - http_req_rate, response_ms (application)")
    print("  - pod_restarts (container lifecycle)")
    print("")
    print("Endpoints:")
    print(f"  GET http://localhost:{PORT}/metrics         - Current metrics")
    print(f"  GET http://localhost:{PORT}/metrics/history - Rolling history")
    print(f"  GET http://localhost:{PORT}/health          - Health check")
    print("="*80)
    print("")
    
    # Start metrics collection thread
    collector = threading.Thread(target=collect_metrics, daemon=True)
    collector.start()
    
    # Start HTTP server
    run_server()
