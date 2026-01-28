@echo off
REM Batch script to start OpenTelemetry Collector
REM Usage: start-collector.bat [start|stop|restart|logs|status]

setlocal

set ACTION=%1
if "%ACTION%"=="" set ACTION=start

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Check if docker-compose.yaml exists
if not exist "docker-compose.yaml" (
    echo Error: docker-compose.yaml not found in current directory.
    exit /b 1
)

echo ========================================
echo   OpenTelemetry Collector Manager
echo ========================================
echo.

if /i "%ACTION%"=="start" goto :start_collector
if /i "%ACTION%"=="stop" goto :stop_collector
if /i "%ACTION%"=="restart" goto :restart_collector
if /i "%ACTION%"=="logs" goto :show_logs
if /i "%ACTION%"=="status" goto :show_status
goto :usage

:start_collector
echo Starting OpenTelemetry Collector...

REM Create logs directory if it doesn't exist
if not exist "otel-collector\logs" mkdir "otel-collector\logs"

docker-compose up -d otel-collector

echo.
echo OpenTelemetry Collector is starting...
echo.
echo Endpoints:
echo   OTLP gRPC:     http://localhost:4317
echo   OTLP HTTP:     http://localhost:4318
echo   Health Check:  http://localhost:13133
echo   Metrics:       http://localhost:8888/metrics
echo   zPages:        http://localhost:55679/debug/tracez
echo.
echo Waiting for collector to be healthy...

REM Simple health check loop
set attempts=0
:health_loop
if %attempts% geq 30 goto :health_timeout
timeout /t 1 /nobreak >nul
curl.exe -s -f http://localhost:13133 >nul 2>&1
if errorlevel 1 (
    set /a attempts+=1
    echo|set /p="."
    goto :health_loop
)

echo.
echo OpenTelemetry Collector is healthy!
goto :end

:health_timeout
echo.
echo Warning: Health check timeout. Collector may still be starting...
goto :end

:stop_collector
echo Stopping OpenTelemetry Collector...
docker-compose down
echo OpenTelemetry Collector stopped.
goto :end

:restart_collector
call :stop_collector
timeout /t 2 /nobreak >nul
call :start_collector
goto :end

:show_logs
echo Showing OpenTelemetry Collector logs (Ctrl+C to exit)...
docker-compose logs -f otel-collector
goto :end

:show_status
echo Checking OpenTelemetry Collector status...
docker-compose ps otel-collector
goto :end

:usage
echo Usage: start-collector.bat [start^|stop^|restart^|logs^|status]
echo   start   - Start the collector (default)
echo   stop    - Stop the collector
echo   restart - Restart the collector
echo   logs    - Show collector logs
echo   status  - Show collector status
goto :end

:end
endlocal
