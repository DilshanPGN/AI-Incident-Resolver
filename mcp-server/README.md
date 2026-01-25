# OTEL MCP Server

MCP (Model Context Protocol) server that exposes OpenTelemetry telemetry data to Cursor AI for incident analysis.

## Architecture

```
Java Services (order, payment)
        ↓ (OTLP)
OTEL Collector (4317)
        ↓ (OTLP gRPC)
MCP Server (Python) :4319
        ↓ (stdio)
   Cursor AI
```

The MCP server receives telemetry data directly from the OTEL collector over gRPC, enabling cloud deployments where services are distributed across containers/pods.

## Installation

```powershell
# Install with pip
pip install -e .

# Or install dependencies directly
pip install mcp grpcio opentelemetry-proto protobuf
```

## Usage

The MCP server is automatically started by Cursor when configured. To run manually for testing:

```powershell
python server.py
```

## Components

### `telemetry_store.py`
In-memory storage for traces, metrics, and logs with query methods for filtering.

### `otlp_receiver.py`
OTLP gRPC receiver that accepts telemetry data directly from the OTEL collector over the network.

### `server.py`
MCP server implementation that exposes tools and resources to Cursor AI. Manages the OTLP receiver.

## MCP Tools

| Tool | Description |
|------|-------------|
| `get_recent_traces` | Get recent traces, optionally filtered by service |
| `get_recent_logs` | Get recent logs, optionally filtered by severity |
| `get_recent_metrics` | Get current metrics for services |
| `get_trace_by_id` | Get full trace details by trace ID |
| `get_errors` | Get recent errors (ERROR/FATAL logs + failed traces) |
| `analyze_incident` | AI-friendly summary of recent anomalies |
| `get_service_health` | Get health summary for a specific service |

## MCP Resources

| URI | Description |
|-----|-------------|
| `otel://traces/recent` | Recent traces summary |
| `otel://logs/recent` | Recent logs |
| `otel://metrics/current` | Current metrics snapshot |
| `otel://services` | List of discovered services |
| `otel://errors/recent` | Recent errors |
| `otel://stats` | Telemetry statistics |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTLP_RECEIVER_PORT` | Port for OTLP gRPC receiver | `4319` |

## Configuration

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
