<#
.SYNOPSIS
  End-to-end experiment runner for the DIS scaffold (PowerShell).

.DESCRIPTION
  Builds the TensorFlow test image, trains models, deploys example workload
  and agent, runs the in-cluster simulator job, optionally applies Chaos
  experiments, collects results, and tears down resources.

  This script is designed for interactive use on Windows PowerShell. It
  performs simple checks for required tools and falls back to containerized
  trainers if a local venv is not available.

.NOTES
  - Run from the repository root.
  - Requires: Docker (or local image push), kubectl configured for cluster.
#>

param(
    [switch]$NoPrompts,
    [switch]$SkipBuild,
    [switch]$SkipTrain,
    [switch]$SkipDeploy,
    [switch]$SkipJob,
    [switch]$RunChaos,
    [switch]$CollectOnly,
    [switch]$Teardown
)

function Confirm-OrExit($msg){
    if($NoPrompts){ return }
    $r = Read-Host "$msg  (y/n)"
    if($r -ne 'y' -and $r -ne 'Y'){
        Write-Host "Aborted by user." -ForegroundColor Yellow; exit 1
    }
}

function Check-Tool($cmd, $name){
    $which = Get-Command $cmd -ErrorAction SilentlyContinue
    if(-not $which){ Write-Host "ERROR: Required tool '$name' not found in PATH." -ForegroundColor Red; exit 1 }
}

Push-Location $PSScriptRoot/.. | Out-Null

# Basic checks
Check-Tool -cmd docker -name docker
Check-Tool -cmd kubectl -name kubectl

if(-not $SkipBuild){
    Write-Host "Building TensorFlow test image (Dockerfile.tfbase)..."
    docker build -f Dockerfile.tfbase -t dis-autoencoder:tfbase .
}

if(-not $SkipTrain){
    # prefer venv python if present
    $venvPython = Join-Path -Path (Get-Location) -ChildPath ".venv\Scripts\python.exe"
    if(Test-Path $venvPython){
        Write-Host "Using venv python to run trainers..."
        & $venvPython ml/train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib
        & $venvPython ml/train_autoencoder_sklearn.py --input data/metrics.csv --out ml/models/ae_sklearn.joblib
    }
    else{
        Write-Host "venv Python not found; running trainers inside container (requires Docker)..."
        docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/ml/models:/app/ml/models" dis-autoencoder:tfbase python ml/train_isolation_forest.py --input data/metrics.csv --out ml/models/iforest.joblib
        docker run --rm -v "${PWD}/data:/app/data" -v "${PWD}/ml/models:/app/ml/models" dis-autoencoder:tfbase python ml/train_autoencoder.py --input data/metrics.csv --out ml/models/autoencoder
    }
}

if($CollectOnly){
    Write-Host "Collect-only requested. Skipping deploy/run steps."; goto :collect
}

if(-not $SkipDeploy){
    Write-Host "Applying example deployment and agent (cluster manifests)..."
    kubectl apply -f cluster/example-deployment.yaml
    kubectl apply -f cluster/agent-daemonset.yaml
}

if(-not $SkipJob){
    Write-Host "Applying RBAC and launching in-cluster simulator job..."
    kubectl apply -f cluster/simulate-rbac.yaml
    kubectl apply -f cluster/simulate-detection-job.yaml
    Write-Host "Waiting for job pods..."
    Start-Sleep -Seconds 5
    kubectl get pods -l job=simulate-detection
    Write-Host "Logs from simulator job:"
    kubectl logs -l job=simulate-detection --tail=200
}

if($RunChaos){
    Write-Host "Applying Chaos Mesh experiments (pod-kill, cpu-stress)..."
    kubectl apply -f chaos/pod-kill.yaml
    kubectl apply -f chaos/cpu-stress.yaml
    Write-Host "Chaos experiments applied. Monitor with events and pods."
}

:collect
Write-Host "Collecting artifacts into results/ ..."
New-Item -ItemType Directory -Force -Path results | Out-Null
kubectl get events -o yaml > results/events.yaml
kubectl get pods -o wide > results/pods.txt
kubectl logs -l app=example-app --tail=200 > results/example-app.logs 2>$null
if(Test-Path ml/models){ Copy-Item -Path ml/models/* -Destination results/ -Recurse -Force -ErrorAction SilentlyContinue }

if($Teardown){
    Write-Host "Tearing down cluster resources..."
    kubectl delete -f cluster/simulate-detection-job.yaml --ignore-not-found
    kubectl delete -f cluster/simulate-rbac.yaml --ignore-not-found
    kubectl delete -f cluster/agent-daemonset.yaml --ignore-not-found
    kubectl delete -f cluster/example-deployment.yaml --ignore-not-found
    if($RunChaos){
        kubectl delete -f chaos/pod-kill.yaml --ignore-not-found
        kubectl delete -f chaos/cpu-stress.yaml --ignore-not-found
    }
}

Write-Host "Experiment run complete. Results are in: $(Resolve-Path results)"
Pop-Location | Out-Null
