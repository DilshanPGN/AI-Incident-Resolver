# OTEL MCP Server

MCP (Model Context Protocol) server that exposes OpenTelemetry telemetry data to Cursor AI for incident analysis.

## Architecture

```
Java Services (order-service:8080, payment-service:8081)
        ↓ (OTLP gRPC/HTTP)
OTEL Collector (Docker) :4317, :4318
        ↓ (OTLP gRPC)
MCP Server (Python) :4319
        ↓ (stdio)
   Cursor AI
```

The MCP server receives telemetry data directly from the OTEL collector over gRPC, enabling real-time data ingestion without file I/O. This architecture supports cloud deployments where services are distributed across containers/pods.

## Installation

### Prerequisites
- Python 3.10+
- pip

### Install Dependencies

```powershell
# From the mcp-server directory - recommended
cd mcp-server
pip install -e .

# Or install dependencies directly
pip install -r requirements.txt

# Or install individual packages
pip install mcp>=1.0.0 grpcio>=1.60.0 opentelemetry-proto>=1.20.0 protobuf>=4.25.0
```

**Note:** Make sure you're using the same Python interpreter that Cursor uses.

## Usage

### Automatic Startup (Recommended)

The MCP server is automatically started by Cursor when configured in `.cursor/mcp.json`. Restart Cursor after configuration to load the server.

### Manual Testing

To run manually for testing:

```powershell
python server.py
```

The server will:
1. Start the OTLP gRPC receiver on port 4319 (configurable via `OTLP_RECEIVER_PORT`)
2. Wait for telemetry data from the OTEL collector
3. Expose MCP tools and resources via stdio to Cursor

## Components

### `telemetry_store.py`
In-memory storage for traces, metrics, and logs with query methods for filtering. Stores up to:
- 10,000 spans
- 10,000 log records
- 5,000 metric data points

### `otlp_receiver.py`
OTLP gRPC receiver that accepts telemetry data directly from the OTEL collector over the network. Listens on port 4319 by default.

### `server.py`
MCP server implementation that exposes tools and resources to Cursor AI. Manages the OTLP receiver lifecycle and provides the MCP protocol interface.

## MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `get_recent_traces` | Get recent traces, optionally filtered by service or errors | `limit`, `service`, `errors_only` |
| `get_recent_logs` | Get recent logs, optionally filtered by severity | `limit`, `service`, `severity`, `errors_only` |
| `get_recent_metrics` | Get current metrics for services | `limit`, `service`, `metric_name` |
| `get_trace_by_id` | Get full trace details by trace ID | `trace_id` (required) |
| `get_errors` | Get recent errors (ERROR/FATAL logs + failed traces) | `limit`, `since_minutes` |
| `analyze_incident` | AI-friendly summary of recent anomalies | `since_minutes` |
| `get_service_health` | Get health summary for a specific service | `service` (required) |
| `get_receiver_status` | Get status of the OTLP receiver | None |

## MCP Resources

| URI | Description |
|-----|-------------|
| `otel://traces/recent` | Recent traces summary (last 50 spans) |
| `otel://logs/recent` | Recent logs (last 50 records) |
| `otel://metrics/current` | Current metrics snapshot (last 100 metrics) |
| `otel://services` | List of discovered services |
| `otel://errors/recent` | Recent errors (last 50, within 60 minutes) |
| `otel://stats` | Telemetry statistics (counts, storage info) |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTLP_RECEIVER_PORT` | Port for OTLP gRPC receiver | `4319` |

## Configuration

### Cursor MCP Configuration

The Cursor MCP configuration is in `.cursor/mcp.json`:

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

**Note:** Replace `<workspace-path>` with the absolute path to your project root.

### OTEL Collector Configuration

The OTEL collector must be configured to forward telemetry to the MCP server. In `otel-collector/otel-collector-config.yaml`, the exporter is configured as:

```yaml
exporters:
  otlp/mcp:
    endpoint: "host.docker.internal:4319"
    tls:
      insecure: true
```

This allows the Docker-based collector to reach the MCP server running on the host machine.

## Troubleshooting

### Import Errors

If you see import errors when starting the server:

1. Ensure all dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```

2. Verify you're using the correct Python interpreter (the one Cursor uses)

3. Check that `grpcio`, `opentelemetry-proto`, and `protobuf` are installed

### Receiver Not Starting

If the OTLP receiver fails to start:

1. Check if port 4319 is already in use
2. Verify the OTEL collector is configured to send data to `host.docker.internal:4319`
3. Check Cursor's error logs for detailed error messages

### No Telemetry Data

If no telemetry data is appearing:

1. Verify the OTEL collector is running: `.\start-collector.ps1 status`
2. Verify services are running and instrumented: `.\dev.ps1`
3. Check collector logs: `.\start-collector.ps1 logs`
4. Use `get_receiver_status` tool to verify the receiver is running
