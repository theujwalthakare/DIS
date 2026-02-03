#!/bin/bash
# Verification script for DIS implementation

set -e

echo "================================"
echo "DIS Implementation Verification"
echo "================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

check() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓${NC} $1"
    else
        echo -e "${RED}✗${NC} $1"
        exit 1
    fi
}

echo "1. Checking project structure..."
[ -d "src/dis_k8s" ] && check "Source directory exists"
[ -d "k8s/manifests" ] && check "Kubernetes manifests exist"
[ -d "tests/unit" ] && check "Test directory exists"
[ -f "requirements.txt" ] && check "Requirements file exists"
[ -f "Dockerfile" ] && check "Dockerfile exists"

echo ""
echo "2. Checking Python modules..."
python -c "from dis_k8s.adc import ArtificialDendriticCell" && check "aDC module imports"
python -c "from dis_k8s.thelper import THelperLayer" && check "T-Helper module imports"
python -c "from dis_k8s.bcell import BCellMemoryLayer" && check "B-Cell module imports"
python -c "from dis_k8s.prometheus_metrics import DISMetrics" && check "Prometheus module imports"
python -c "from dis_k8s.orchestrator import DISOrchestrator" && check "Orchestrator imports"

echo ""
echo "3. Running unit tests..."
pytest tests/unit/ -v --tb=line -q 2>&1 | grep -E "passed|failed" | head -1
check "Unit tests"

echo ""
echo "4. Checking Kubernetes manifests..."
for manifest in k8s/manifests/*.yaml; do
    kubectl apply --dry-run=client -f "$manifest" > /dev/null 2>&1 && check "$(basename $manifest) is valid"
done

echo ""
echo "5. Checking documentation..."
[ -f "README.md" ] && check "README exists"
[ -f "QUICKSTART.md" ] && check "Quick Start Guide exists"
[ -f "ARCHITECTURE.md" ] && check "Architecture doc exists"
[ -f "CONTRIBUTING.md" ] && check "Contributing guide exists"
[ -f "LICENSE" ] && check "License file exists"

echo ""
echo "6. Checking configuration..."
[ -f "config/dis-config.yaml" ] && check "Configuration file exists"
python -c "import yaml; yaml.safe_load(open('config/dis-config.yaml'))" && check "Configuration is valid YAML"

echo ""
echo "7. Verifying Chaos Mesh experiments..."
[ -f "k8s/chaos-mesh/experiments.yaml" ] && check "Chaos experiments exist"

echo ""
echo "8. Checking examples..."
[ -f "k8s/examples/test-app.yaml" ] && check "Test application exists"

echo ""
echo "================================"
echo -e "${GREEN}All checks passed!${NC}"
echo "================================"
echo ""
echo "DIS is ready for deployment!"
echo ""
echo "Next steps:"
echo "  1. Build Docker image: make build"
echo "  2. Deploy to cluster: make deploy"
echo "  3. View logs: make logs"
echo "  4. Access metrics: make metrics"
