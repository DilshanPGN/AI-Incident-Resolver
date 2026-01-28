@echo off
REM Batch script to start services with OpenTelemetry Java Agent
REM Usage: dev-new.bat [order|product|all]

setlocal enabledelayedexpansion

set SERVICE=%1
if "%SERVICE%"=="" set SERVICE=all

REM Configuration
set OTEL_JAR=opentelemetry-javaagent.jar
REM Use HTTP endpoint (4318) - gRPC (4317) requires explicit protocol setting
set OTEL_COLLECTOR_ENDPOINT=http://localhost:4318

REM Common OTEL environment variables
set OTEL_EXPORTER_OTLP_ENDPOINT=%OTEL_COLLECTOR_ENDPOINT%
set OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf
set OTEL_METRICS_EXPORTER=otlp
set OTEL_LOGS_EXPORTER=otlp
set OTEL_TRACES_EXPORTER=otlp

REM Check if OTEL jar exists
if not exist "%OTEL_JAR%" (
    echo Error: OpenTelemetry Java Agent not found at %OTEL_JAR%
    echo Download from: https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases
    exit /b 1
)

echo ========================================
echo   OpenTelemetry Development Launcher
echo ========================================
echo.
echo OTEL Collector Endpoint: %OTEL_COLLECTOR_ENDPOINT%
echo.

if /i "%SERVICE%"=="order" (
    call :start_order
    goto :done
)
if /i "%SERVICE%"=="product" (
    call :start_product
    goto :done
)
if /i "%SERVICE%"=="all" goto :start_all
goto :usage

:start_order
echo Starting Order Service on port 8081 with OpenTelemetry...
set OTEL_SERVICE_NAME=order-service
set OTEL_RESOURCE_ATTRIBUTES=service.name=order-service,service.version=1.0.0,deployment.environment=development

cd ..\order-service
echo Running order-service on port 8081 with OpenTelemetry agent...
start "order-service-8081" cmd /k "set OTEL_SERVICE_NAME=order-service&& set OTEL_RESOURCE_ATTRIBUTES=service.name=order-service,service.version=1.0.0,deployment.environment=development&& set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318&& set OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf&& set OTEL_METRICS_EXPORTER=otlp&& set OTEL_LOGS_EXPORTER=otlp&& set OTEL_TRACES_EXPORTER=otlp&& mvn spring-boot:run -Dspring-boot.run.jvmArguments=-javaagent:..\AI-Incident-Resolver\opentelemetry-javaagent.jar -Dspring-boot.run.arguments=--server.port=8081"
cd ..\AI-Incident-Resolver
goto :eof

:start_product
echo Starting Product Service on port 8083 with OpenTelemetry...
set OTEL_SERVICE_NAME=product-service
set OTEL_RESOURCE_ATTRIBUTES=service.name=product-service,service.version=1.0.0,deployment.environment=development

cd ..\product-service
echo Running product-service on port 8083 with OpenTelemetry agent...
start "product-service-8083" cmd /k "set OTEL_SERVICE_NAME=product-service&& set OTEL_RESOURCE_ATTRIBUTES=service.name=product-service,service.version=1.0.0,deployment.environment=development&& set OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318&& set OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf&& set OTEL_METRICS_EXPORTER=otlp&& set OTEL_LOGS_EXPORTER=otlp&& set OTEL_TRACES_EXPORTER=otlp&& mvn spring-boot:run -Dspring-boot.run.jvmArguments=-javaagent:..\AI-Incident-Resolver\opentelemetry-javaagent.jar -Dspring-boot.run.arguments=--server.port=8083"
cd ..\AI-Incident-Resolver
goto :eof

:start_all
call :start_order
timeout /t 2 /nobreak >nul
call :start_product
goto :done

:usage
echo Usage: dev-new.bat [order^|product^|all]
echo   order   - Start only order-service on port 8081
echo   product - Start only product-service on port 8083
echo   all     - Start both services (default)
exit /b 0

:done
echo.
echo Services started! Check the OpenTelemetry Collector for telemetry data.
echo Order Service: http://localhost:8081
echo Product Service: http://localhost:8083
endlocal
