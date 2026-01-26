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

## Troubleshooting

### Collector Connection Errors

If you see connection errors like `connection refused` when the collector tries to connect to the MCP server:

1. **Verify MCP Server is Running**: The MCP server must be running before the collector starts. Check Cursor's MCP server status or run the server manually:
   ```powershell
   cd mcp-server
   python server.py
   ```
   You should see: `OTLP receiver started on port 4319`

2. **Check Windows Firewall**: Windows Firewall may be blocking port 4319. To allow it:
   ```powershell
   # Run PowerShell as Administrator
   New-NetFirewallRule -DisplayName "OTLP Receiver" -Direction Inbound -LocalPort 4319 -Protocol TCP -Action Allow
   ```

3. **Verify Startup Order**: Start the MCP server first, then start the collector:
   ```powershell
   # 1. Start MCP server (via Cursor or manually)
   # 2. Then start collector
   .\start-collector.ps1
   ```

4. **Check Network Connectivity**: The collector uses `host.docker.internal:4319` to reach the host. Verify this works:
   ```powershell
   # From inside the container (if needed)
   docker exec otel-collector ping host.docker.internal
   ```

5. **Restart Collector**: After starting the MCP server, restart the collector:
   ```powershell
   .\start-collector.ps1 restart
   ```

6. **Check Collector Logs**: Review collector logs for detailed error messages:
   ```powershell
   .\start-collector.ps1 logs
   ```

7. **Windows Docker Desktop Issue**: If `host.docker.internal` doesn't work (connection refused errors), the collector config uses the WSL/Hyper-V adapter IP (`172.24.224.1`) instead. If your system has a different IP, update `otel-collector/otel-collector-config.yaml`:
   ```powershell
   # Find your WSL/Hyper-V adapter IP
   Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -like "*WSL*" -or $_.InterfaceAlias -like "*Hyper-V*" }
   
   # Then update the endpoint in otel-collector-config.yaml:
   # endpoint: "YOUR_IP:4319"
   ```

The collector is configured with retry logic and will automatically retry connections, so if the MCP server starts after the collector, it should connect once the server is ready.

### No Telemetry Data

If no telemetry data appears in the MCP server:

1. Verify services are running: `.\dev.ps1`
2. Check collector is receiving data: `.\start-collector.ps1 logs`
3. Verify MCP receiver status using the `get_receiver_status` tool in Cursor
4. Check that services are instrumented with the Java agent (check service logs)

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
