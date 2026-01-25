# AI-Incident-Resolver

Build an AI-driven observability & incident-analysis agent that plugs into Java Spring Boot microservices and understands the system end-to-end, enabling automatic root-cause analysis and fix suggestions for complex production incidents.

## Architecture

```
Java Services (Spring Boot)
    ↓ (OTLP gRPC/HTTP)
OpenTelemetry Collector (Docker)
    ↓ (OTLP gRPC)
MCP Server (Python) :4319
    ↓ (stdio)
Cursor AI
```

The MCP server receives telemetry data directly from the OTEL collector over gRPC, enabling real-time data ingestion without file I/O.

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
- Python 3.10+ (for MCP server)

### 1. Install MCP Server Dependencies

```powershell
cd mcp-server
pip install -e .
# Or install dependencies directly:
pip install -r requirements.txt
```

### 2. Start OpenTelemetry Collector

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

The collector runs in Docker and exposes the following endpoints:
- **OTLP gRPC**: `localhost:4317` - Primary receiver for Java agent
- **OTLP HTTP**: `localhost:4318` - HTTP receiver
- **Health Check**: `localhost:13133` - Health status endpoint
- **Prometheus Metrics**: `localhost:8888/metrics` - Metrics endpoint
- **zPages**: `localhost:55679/debug/tracez` - Debug information
- **pprof**: `localhost:1777` - Performance profiler

### 3. Start Services with OpenTelemetry Instrumentation

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

The services are automatically instrumented with the OpenTelemetry Java agent (`opentelemetry-javaagent.jar`) and send telemetry to the collector.

### 4. Enable MCP in Cursor

The MCP server is automatically started by Cursor when configured. The configuration is in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "otel-incident-resolver": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "cwd": "<workspace-path>"
    }
  }
}
```

**Note:** Restart Cursor after configuring MCP to load the server.

## OpenTelemetry Configuration

### Collector Configuration

The collector is configured via `otel-collector/otel-collector-config.yaml`:
- Receives telemetry via OTLP (gRPC on 4317, HTTP on 4318)
- Processes data with batching, memory limiting, and resource attributes
- Exports to:
  - **Debug exporter** (console logs for development)
  - **OTLP exporter** to MCP server at `host.docker.internal:4319`

### Java Agent Configuration

Services are instrumented using the OpenTelemetry Java agent with the following environment variables:
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`
- `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`
- `OTEL_SERVICE_NAME` - Set per service (order-service, payment-service)
- `OTEL_RESOURCE_ATTRIBUTES` - Service metadata

## MCP Server Integration

The MCP (Model Context Protocol) server exposes OpenTelemetry data to Cursor AI for incident analysis.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_recent_traces` | Get recent traces, filter by service or errors |
| `get_recent_logs` | Get recent logs, filter by severity |
| `get_recent_metrics` | Get current metrics snapshot |
| `get_trace_by_id` | Get full trace details by trace ID |
| `get_errors` | Get recent errors for incident analysis |
| `analyze_incident` | Generate incident analysis report |
| `get_service_health` | Get health summary for a specific service |
| `get_receiver_status` | Get status of the OTLP receiver |

### Available MCP Resources

| Resource URI | Description |
|--------------|-------------|
| `otel://traces/recent` | Recent trace spans |
| `otel://logs/recent` | Recent log records |
| `otel://metrics/current` | Current metrics |
| `otel://services` | Discovered services |
| `otel://errors/recent` | Recent errors |
| `otel://stats` | Telemetry statistics |

### Using with Cursor AI

Once configured, you can ask Cursor AI questions like:
- "What errors are occurring in my services?"
- "Analyze the recent incidents"
- "Show me the health of order-service"
- "Get traces for the payment-service"
- "What is the status of the OTLP receiver?"

The AI will use the MCP tools to query your live telemetry data and provide insights.

## Project Structure

```
├── order-service/           # Order management microservice
├── payment-service/         # Payment processing microservice
├── otel-collector/          # OpenTelemetry Collector config
│   └── otel-collector-config.yaml
├── mcp-server/              # MCP server for Cursor AI integration
│   ├── pyproject.toml       # Python dependencies
│   ├── server.py            # MCP server implementation
│   ├── telemetry_store.py   # In-memory telemetry storage
│   └── otlp_receiver.py     # OTLP gRPC receiver (receives data from collector)
├── .cursor/mcp.json         # Cursor MCP configuration
├── docker-compose.yaml      # Docker Compose for OTEL Collector
├── opentelemetry-javaagent.jar
├── dev.ps1                  # PowerShell script to start services
├── dev.bat                  # Batch script to start services
├── start-collector.ps1      # PowerShell script for collector
└── start-collector.bat      # Batch script for collector
```
