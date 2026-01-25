# OTEL MCP Server

MCP (Model Context Protocol) server that exposes OpenTelemetry telemetry data to Cursor AI for incident analysis.

## Architecture

```
Java Services (order, payment)
        ↓ (OTLP)
OTEL Collector (4317)
        ↓ (JSON files)
    telemetry/
        ↓ (file watcher)
MCP Server (Python)
        ↓ (stdio)
   Cursor AI
```

## Installation

```powershell
# Install with pip
pip install -e .

# Or install dependencies directly
pip install mcp watchdog pydantic
```

## Usage

The MCP server is automatically started by Cursor when configured. To run manually for testing:

```powershell
python server.py
```

## Components

### `telemetry_store.py`
In-memory storage for traces, metrics, and logs with query methods for filtering.

### `file_watcher.py`
Watches the `telemetry/` directory for OTEL JSON exports and parses them into the store.

### `server.py`
MCP server implementation that exposes tools and resources to Cursor AI.

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
| `OTEL_TELEMETRY_PATH` | Path to telemetry directory | `../telemetry` |

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
