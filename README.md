# AI-Incident-Resolver
Build an AI-driven observability & incident-analysis agent that plugs into Java Spring Boot microservices and understands the system end-to-end, enabling automatic root-cause analysis and fix suggestions for complex production incidents.

## Services

| Service | Port | Description |
|---------|------|-------------|
| order-service | 8080 | Order management service |
| payment-service | 8081 | Payment processing service |

## Quick Start

### Prerequisites
- Java 17+
- Maven 3.6+
- Docker Desktop

### 1. Start OpenTelemetry Collector

```powershell
# PowerShell
.\start-collector.ps1

# Or using batch
start-collector.bat
```

Available commands:
- `start` - Start the collector (default)
- `stop` - Stop the collector
- `restart` - Restart the collector
- `logs` - Show collector logs
- `status` - Show collector status

### 2. Start Services with OpenTelemetry Instrumentation

```powershell
# PowerShell - Start all services
.\dev.ps1

# Start specific service
.\dev.ps1 order
.\dev.ps1 payment

# Or using batch
dev.bat
dev.bat order
dev.bat payment
```

## OpenTelemetry Configuration

### Collector Endpoints
| Endpoint | Port | Description |
|----------|------|-------------|
| OTLP gRPC | 4317 | Primary receiver for Java agent |
| OTLP HTTP | 4318 | HTTP receiver |
| Health Check | 13133 | Health status |
| Metrics | 8888 | Prometheus metrics |
| zPages | 55679 | Debug information |

### MCP Server Integration
The collector is configured to export telemetry to an MCP server at `localhost:4319`. Update the endpoint in `otel-collector/otel-collector-config.yaml` to point to your MCP server.

## Project Structure

```
├── order-service/           # Order management microservice
├── payment-service/         # Payment processing microservice
├── otel-collector/          # OpenTelemetry Collector config
│   └── otel-collector-config.yaml
├── docker-compose.yaml      # Docker Compose for OTEL Collector
├── opentelemetry-javaagent.jar
├── dev.ps1                  # PowerShell script to start services
├── dev.bat                  # Batch script to start services
├── start-collector.ps1      # PowerShell script for collector
└── start-collector.bat      # Batch script for collector
```
