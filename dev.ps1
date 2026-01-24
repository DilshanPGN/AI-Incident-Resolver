# Development script to start Order and Payment services with OpenTelemetry
# Usage: .\dev.ps1

$ErrorActionPreference = "Stop"

# Configuration
$OTEL_AGENT = "opentelemetry-javaagent.jar"
$OTEL_ENDPOINT = "http://localhost:4317"

# Service configurations
$services = @(
    @{
        Name = "order-service"
        Jar = "order-service\target\order-service-1.0.0.jar"
    },
    @{
        Name = "payment-service"
        Jar = "payment-service\target\payment-service-1.0.0.jar"
    }
)

Write-Host "Starting services with OpenTelemetry instrumentation..." -ForegroundColor Cyan
Write-Host "OTEL Endpoint: $OTEL_ENDPOINT" -ForegroundColor Gray
Write-Host ""

# Check if OTEL agent exists
if (-not (Test-Path $OTEL_AGENT)) {
    Write-Host "ERROR: OpenTelemetry agent not found: $OTEL_AGENT" -ForegroundColor Red
    exit 1
}

# Start each service in a new window
foreach ($service in $services) {
    $serviceName = $service.Name
    $jarPath = $service.Jar

    if (-not (Test-Path $jarPath)) {
        Write-Host "WARNING: JAR not found for $serviceName at $jarPath" -ForegroundColor Yellow
        Write-Host "  Run 'mvn package -DskipTests' in $serviceName folder first" -ForegroundColor Yellow
        continue
    }

    Write-Host "Starting $serviceName..." -ForegroundColor Green
    
    $javaArgs = @(
        "-javaagent:$OTEL_AGENT",
        "-Dotel.service.name=$serviceName",
        "-Dotel.exporter.otlp.endpoint=$OTEL_ENDPOINT",
        "-jar",
        $jarPath
    )

    Start-Process -FilePath "java" -ArgumentList $javaArgs -WindowStyle Normal
    
    Write-Host "  $serviceName started" -ForegroundColor Green
}

Write-Host ""
Write-Host "All services started. Press Ctrl+C in each window to stop." -ForegroundColor Cyan
