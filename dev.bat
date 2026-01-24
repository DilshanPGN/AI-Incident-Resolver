@echo off
REM Development script to start Order and Payment services with OpenTelemetry
REM Usage: dev.bat

set OTEL_AGENT=opentelemetry-javaagent.jar
set OTEL_ENDPOINT=http://localhost:4317

echo Starting services with OpenTelemetry instrumentation...
echo OTEL Endpoint: %OTEL_ENDPOINT%
echo.

REM Check if OTEL agent exists
if not exist "%OTEL_AGENT%" (
    echo ERROR: OpenTelemetry agent not found: %OTEL_AGENT%
    pause
    exit /b 1
)

REM Start Order Service
echo Starting order-service...
start "order-service" java -javaagent:%OTEL_AGENT% -Dotel.service.name=order-service -Dotel.exporter.otlp.endpoint=%OTEL_ENDPOINT% -jar order-service\target\order-service-1.0.0.jar

REM Start Payment Service
echo Starting payment-service...
start "payment-service" java -javaagent:%OTEL_AGENT% -Dotel.service.name=payment-service -Dotel.exporter.otlp.endpoint=%OTEL_ENDPOINT% -jar payment-service\target\payment-service-1.0.0.jar

echo.
echo All services started. Close each window to stop the service.
pause
