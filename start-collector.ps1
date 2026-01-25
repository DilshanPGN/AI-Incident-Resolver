# PowerShell script to start OpenTelemetry Collector
# Usage: .\start-collector.ps1 [start|stop|restart|logs|status]

param(
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"

function Show-Status {
    Write-Host "Checking OpenTelemetry Collector status..." -ForegroundColor Cyan
    docker-compose ps otel-collector
}

function Start-Collector {
    Write-Host "Starting OpenTelemetry Collector..." -ForegroundColor Green
    
    # Create logs directory if it doesn't exist
    if (-not (Test-Path "otel-collector\logs")) {
        New-Item -ItemType Directory -Path "otel-collector\logs" -Force | Out-Null
    }
    
    docker-compose up -d otel-collector
    
    Write-Host ""
    Write-Host "OpenTelemetry Collector is starting..." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Endpoints:" -ForegroundColor Cyan
    Write-Host "  OTLP gRPC:     http://localhost:4317" -ForegroundColor White
    Write-Host "  OTLP HTTP:     http://localhost:4318" -ForegroundColor White
    Write-Host "  Health Check:  http://localhost:13133" -ForegroundColor White
    Write-Host "  Metrics:       http://localhost:8888/metrics" -ForegroundColor White
    Write-Host "  zPages:        http://localhost:55679/debug/tracez" -ForegroundColor White
    Write-Host ""
    
    # Wait for health check
    Write-Host "Waiting for collector to be healthy..." -ForegroundColor Yellow
    $maxAttempts = 30
    $attempt = 0
    
    while ($attempt -lt $maxAttempts) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:13133" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Host "OpenTelemetry Collector is healthy!" -ForegroundColor Green
                return
            }
        }
        catch {
            # Ignore errors and retry
        }
        $attempt++
        Start-Sleep -Seconds 1
        Write-Host "." -NoNewline -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "Warning: Health check timeout. Collector may still be starting..." -ForegroundColor Yellow
}

function Stop-Collector {
    Write-Host "Stopping OpenTelemetry Collector..." -ForegroundColor Yellow
    docker-compose down
    Write-Host "OpenTelemetry Collector stopped." -ForegroundColor Green
}

function Restart-Collector {
    Stop-Collector
    Start-Sleep -Seconds 2
    Start-Collector
}

function Show-Logs {
    Write-Host "Showing OpenTelemetry Collector logs (Ctrl+C to exit)..." -ForegroundColor Cyan
    docker-compose logs -f otel-collector
}

# Check if Docker is running
try {
    docker info | Out-Null
}
catch {
    Write-Host "Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if docker-compose.yaml exists
if (-not (Test-Path "docker-compose.yaml")) {
    Write-Host "Error: docker-compose.yaml not found in current directory." -ForegroundColor Red
    exit 1
}

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  OpenTelemetry Collector Manager      " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""

switch ($Action.ToLower()) {
    "start" {
        Start-Collector
    }
    "stop" {
        Stop-Collector
    }
    "restart" {
        Restart-Collector
    }
    "logs" {
        Show-Logs
    }
    "status" {
        Show-Status
    }
    default {
        Write-Host "Usage: .\start-collector.ps1 [start|stop|restart|logs|status]" -ForegroundColor Yellow
        Write-Host "  start   - Start the collector (default)" -ForegroundColor White
        Write-Host "  stop    - Stop the collector" -ForegroundColor White
        Write-Host "  restart - Restart the collector" -ForegroundColor White
        Write-Host "  logs    - Show collector logs" -ForegroundColor White
        Write-Host "  status  - Show collector status" -ForegroundColor White
    }
}
