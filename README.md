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

### MCP Server Integration (Cursor AI)

The project includes an MCP (Model Context Protocol) server that exposes OpenTelemetry data to Cursor AI for incident analysis.

**Architecture:** The MCP server receives telemetry data directly from the OTEL collector via gRPC (OTLP protocol) on port 4319, enabling real-time data ingestion without file I/O.

#### Setup MCP Server

1. **Install Python dependencies:**

```powershell
cd mcp-server
pip install -e .
# Or install dependencies directly:
pip install mcp grpcio opentelemetry-proto protobuf
```

2. **Start the OTEL Collector**:

```powershell
.\start-collector.ps1
```

The collector will forward telemetry data to the MCP server via gRPC (port 4319).

3. **Enable MCP in Cursor:**
   - The MCP configuration is already set up in `.cursor/mcp.json`
   - Restart Cursor to load the MCP server
   - The MCP server will automatically start when Cursor launches

#### Available MCP Tools

| Tool | Description |
|------|-------------|
| `get_recent_traces` | Get recent traces, filter by service or errors |
| `get_recent_logs` | Get recent logs, filter by severity |
| `get_recent_metrics` | Get current metrics snapshot |
| `get_trace_by_id` | Get full trace details by trace ID |
| `get_errors` | Get recent errors for incident analysis |
| `analyze_incident` | Generate incident analysis report |
| `get_service_health` | Get health summary for a specific service |

#### Available MCP Resources

| Resource | Description |
|----------|-------------|
| `otel://traces/recent` | Recent trace spans |
| `otel://logs/recent` | Recent log records |
| `otel://metrics/current` | Current metrics |
| `otel://services` | Discovered services |
| `otel://errors/recent` | Recent errors |
| `otel://stats` | Telemetry statistics |

#### Using with Cursor AI

Once configured, you can ask Cursor AI questions like:
- "What errors are occurring in my services?"
- "Analyze the recent incidents"
- "Show me the health of order-service"
- "Get traces for the payment-service"

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
