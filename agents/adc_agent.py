"""
Artificial Dendritic Cell (aDC) agent skeleton.

Purpose: run on each node (DaemonSet) to collect local metrics and expose a
Prometheus scrape endpoint. In immune terms: the aDC gathers 'antigens' (local
observations) and presents them to the T-Helper decision layer.

This file is a clear, well-commented starting point for research — extend it
to collect metrics from cgroups, kubelet, or Prometheus exporters.
"""
import time
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import psutil

PORT = 8000

state = {
    "node": None,
    "metrics": {}
}

def collect_metrics():
    """Collect simple local metrics and update `state`.

    Extend this to collect pod-level CPU/memory, network counters, and events.
    """
    while True:
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory().percent
        state['metrics'] = {
            'cpu_percent': cpu,
            'mem_percent': mem,
            'timestamp': time.time()
        }
        time.sleep(5)

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics' or self.path == '/':
            payload = json.dumps(state['metrics']).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
        else:
            self.send_response(404)
            self.end_headers()

def run_server():
    server = HTTPServer(('0.0.0.0', PORT), MetricsHandler)
    server.serve_forever()

if __name__ == '__main__':
    collector = threading.Thread(target=collect_metrics, daemon=True)
    collector.start()
    print(f"aDC agent serving metrics on :{PORT}")
    run_server()
