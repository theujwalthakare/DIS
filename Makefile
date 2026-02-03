# Makefile for DIS

.PHONY: help install test lint clean build deploy

help:
	@echo "DIS - Digital Immune System for Kubernetes"
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run unit tests"
	@echo "  lint       - Run linters"
	@echo "  clean      - Clean build artifacts"
	@echo "  build      - Build Docker image"
	@echo "  deploy     - Deploy to Kubernetes"
	@echo "  undeploy   - Remove from Kubernetes"

install:
	pip install -r requirements.txt
	pip install -e .

test:
	pytest tests/unit/ -v

test-cov:
	pytest tests/unit/ --cov=dis_k8s --cov-report=html --cov-report=term

lint:
	@echo "Linting not configured yet"

clean:
	rm -rf build/ dist/ *.egg-info
	rm -rf .pytest_cache .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	docker build -t dis-kubernetes:latest .

deploy:
	kubectl apply -f k8s/manifests/

undeploy:
	kubectl delete namespace dis-system

logs:
	kubectl logs -n dis-system -l app=dis-agent -f

metrics:
	kubectl port-forward -n dis-system svc/dis-metrics 8000:8000
