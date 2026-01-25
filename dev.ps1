# PowerShell script to start services with OpenTelemetry Java Agent
# Usage: .\dev.ps1 [order|payment|all]

param(
    [string]$Service = "all"
)

$ErrorActionPreference = "Stop"

# Configuration
$OTEL_JAR = "opentelemetry-javaagent.jar"
$OTEL_COLLECTOR_ENDPOINT = "http://localhost:4317"

# Common OTEL environment variables
$env:OTEL_EXPORTER_OTLP_ENDPOINT = $OTEL_COLLECTOR_ENDPOINT
$env:OTEL_EXPORTER_OTLP_PROTOCOL = "grpc"
$env:OTEL_METRICS_EXPORTER = "otlp"
$env:OTEL_LOGS_EXPORTER = "otlp"
$env:OTEL_TRACES_EXPORTER = "otlp"

function Start-OrderService {
    Write-Host "Starting Order Service with OpenTelemetry..." -ForegroundColor Green
    
    $env:OTEL_SERVICE_NAME = "order-service"
    $env:OTEL_RESOURCE_ATTRIBUTES = "service.name=order-service,service.version=1.0.0,deployment.environment=development"
    
    Push-Location order-service
    try {
        # Build the service if target doesn't exist
        if (-not (Test-Path "target\*.jar")) {
            Write-Host "Building order-service..." -ForegroundColor Yellow
            mvn clean package -DskipTests
        }
        
        $jarFile = Get-ChildItem -Path "target" -Filter "*.jar" | Where-Object { $_.Name -notlike "*-sources*" } | Select-Object -First 1
        
        if ($null -eq $jarFile) {
            Write-Host "Error: No JAR file found. Please build the project first." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Running: java -javaagent:..\$OTEL_JAR -jar $($jarFile.FullName)" -ForegroundColor Cyan
        Start-Process -FilePath "java" -ArgumentList "-javaagent:..\$OTEL_JAR", "-jar", $jarFile.FullName -NoNewWindow
    }
    finally {
        Pop-Location
    }
}

function Start-PaymentService {
    Write-Host "Starting Payment Service with OpenTelemetry..." -ForegroundColor Green
    
    $env:OTEL_SERVICE_NAME = "payment-service"
    $env:OTEL_RESOURCE_ATTRIBUTES = "service.name=payment-service,service.version=1.0.0,deployment.environment=development"
    
    Push-Location payment-service
    try {
        # Build the service if target doesn't exist
        if (-not (Test-Path "target\*.jar")) {
            Write-Host "Building payment-service..." -ForegroundColor Yellow
            mvn clean package -DskipTests
        }
        
        $jarFile = Get-ChildItem -Path "target" -Filter "*.jar" | Where-Object { $_.Name -notlike "*-sources*" } | Select-Object -First 1
        
        if ($null -eq $jarFile) {
            Write-Host "Error: No JAR file found. Please build the project first." -ForegroundColor Red
            exit 1
        }
        
        Write-Host "Running: java -javaagent:..\$OTEL_JAR -jar $($jarFile.FullName)" -ForegroundColor Cyan
        Start-Process -FilePath "java" -ArgumentList "-javaagent:..\$OTEL_JAR", "-jar", $jarFile.FullName -NoNewWindow
    }
    finally {
        Pop-Location
    }
}

# Check if OTEL jar exists
if (-not (Test-Path $OTEL_JAR)) {
    Write-Host "Error: OpenTelemetry Java Agent not found at $OTEL_JAR" -ForegroundColor Red
    Write-Host "Download from: https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases" -ForegroundColor Yellow
    exit 1
}

Write-Host "========================================" -ForegroundColor Magenta
Write-Host "  OpenTelemetry Development Launcher   " -ForegroundColor Magenta
Write-Host "========================================" -ForegroundColor Magenta
Write-Host ""
Write-Host "OTEL Collector Endpoint: $OTEL_COLLECTOR_ENDPOINT" -ForegroundColor Cyan
Write-Host ""

switch ($Service.ToLower()) {
    "order" {
        Start-OrderService
    }
    "payment" {
        Start-PaymentService
    }
    "all" {
        Start-OrderService
        Start-Sleep -Seconds 2
        Start-PaymentService
    }
    default {
        Write-Host "Usage: .\dev.ps1 [order|payment|all]" -ForegroundColor Yellow
        Write-Host "  order   - Start only order-service" -ForegroundColor White
        Write-Host "  payment - Start only payment-service" -ForegroundColor White
        Write-Host "  all     - Start both services (default)" -ForegroundColor White
    }
}

Write-Host ""
Write-Host "Services started! Check the OpenTelemetry Collector for telemetry data." -ForegroundColor Green
