# OTEL MCP Server

MCP (Model Context Protocol) server that exposes OpenTelemetry telemetry data to Cursor AI for incident analysis and debugging.

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
- Python 3.10+ (Python 3.14 recommended, see `.python-version` in project root)
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
- 10,000 spans (configurable via `max_spans`)
- 10,000 log records (configurable via `max_logs`)
- 5,000 metric data points (configurable via `max_metrics`)

Features:
- Automatic FIFO eviction when limits are reached
- Service discovery from telemetry data
- Code location extraction and tracking
- Error detection and grouping
- Performance metrics calculation

### `otlp_receiver.py`
OTLP gRPC receiver that accepts telemetry data directly from the OTEL collector over the network. Listens on port 4319 by default.

Features:
- Async gRPC server for high performance
- Automatic span, log, and metric parsing
- Code location extraction from resource attributes
- Error handling and connection management

### `server.py`
MCP server implementation that exposes tools and resources to Cursor AI. Manages the OTLP receiver lifecycle and provides the MCP protocol interface.

Features:
- 9 MCP tools for telemetry analysis
- 6 MCP resources for telemetry snapshots
- AI assistant instructions for better tool usage
- Code location tracking and filtering

## MCP Tools

The server exposes 9 powerful tools for telemetry analysis:

### 1. `get_recent_traces`
Get recent traces, optionally filtered by service or errors.

**Parameters:**
- `limit` (integer, default: 20) - Maximum number of traces to return
- `service` (string, optional) - Filter by service name (e.g., 'order-service')
- `errors_only` (boolean, default: false) - Only return failed/error traces

**Example:**
```
Get recent traces from order-service that have errors
```

**Returns:**
- List of spans with trace_id, span_id, name, service, duration, status, attributes, and code_location (if available)

### 2. `get_recent_logs`
Get recent logs, optionally filtered by severity.

**Parameters:**
- `limit` (integer, default: 30) - Maximum number of logs to return
- `service` (string, optional) - Filter by service name
- `severity` (string, optional) - Filter by severity (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)
- `errors_only` (boolean, default: false) - Only return ERROR and FATAL logs

**Example:**
```
Get all ERROR logs from payment-service in the last hour
```

**Returns:**
- List of log records with timestamp, severity, body, service, trace_id, span_id, attributes, and code_location (if available)

### 3. `get_recent_metrics`
Get current metrics snapshot for services.

**Parameters:**
- `limit` (integer, default: 50) - Maximum number of metrics to return
- `service` (string, optional) - Filter by service name
- `metric_name` (string, optional) - Filter by metric name

**Example:**
```
Get all metrics from order-service
```

**Returns:**
- List of metric data points with timestamp, name, value, unit, service, and attributes

### 4. `get_trace_by_id`
Get full trace details by trace ID. Useful for deep-diving into a particular request's journey across services.

**Parameters:**
- `trace_id` (string, required) - The trace ID to look up

**Example:**
```
Get all spans for trace ID abc123def456
```

**Returns:**
- All spans for the trace with full details including parent-child relationships

### 5. `get_errors`
Get recent errors including failed traces and error logs. This is the primary tool for incident analysis.

**Parameters:**
- `limit` (integer, default: 30) - Maximum number of errors to return
- `since_minutes` (integer, default: 60) - Look back this many minutes

**Example:**
```
Get all errors from the last 30 minutes
```

**Returns:**
- Summary with error counts by service
- Error code locations (filepath, function, line number) with error counts
- List of error spans and error logs

### 6. `analyze_incident`
Analyze recent telemetry data and provide a summary of potential issues. Returns a structured incident report.

**Parameters:**
- `since_minutes` (integer, default: 30) - Analyze data from the last N minutes

**Example:**
```
Analyze incidents from the last hour
```

**Returns:**
- Analysis window and summary statistics
- Error rate and slow operations count
- Errors grouped by service
- Error code locations with counts
- Recent errors (spans and logs)
- Slow operations (>1s) with code locations
- Recommendations for investigation

### 7. `get_service_health`
Get health summary for a specific service based on its recent telemetry.

**Parameters:**
- `service` (string, required) - The service name to analyze

**Example:**
```
Get health status for order-service
```

**Returns:**
- Service name and analysis window
- Span statistics (total, errors, error rate, average duration)
- Log statistics (total, errors, by severity)
- Metrics count
- Health status (healthy, warning, degraded, critical)

### 8. `get_receiver_status`
Get status of the OTLP receiver including whether it's running and listening for data.

**Parameters:** None

**Example:**
```
Check if the OTLP receiver is running
```

**Returns:**
- OTLP receiver status (running, port, configured)
- Store statistics (spans, logs, metrics counts)
- List of discovered services

### 9. `get_code_locations`
Get traces and logs filtered by code location (filepath, function, line number). Useful for finding all telemetry from a specific file or function.

**Parameters:**
- `filepath` (string, optional) - Filter by file path (partial match supported, e.g., 'OrderService.java')
- `function` (string, optional) - Filter by function/method name (partial match supported)
- `service` (string, optional) - Filter by service name
- `errors_only` (boolean, default: false) - Only return errors (failed spans and error logs)
- `limit` (integer, default: 50) - Maximum number of results to return

**Example:**
```
Find all telemetry from OrderService.java processOrder method
```

**Returns:**
- Filters applied
- Summary (spans count, logs count, unique code locations)
- List of unique code locations found
- Matching spans and logs with full details

## MCP Resources

The server exposes 6 resources for accessing telemetry snapshots:

### 1. `otel://traces/recent`
Recent trace spans (last 50 spans)

### 2. `otel://logs/recent`
Recent log records (last 50 records)

### 3. `otel://metrics/current`
Current metrics snapshot (last 100 metrics)

### 4. `otel://services`
List of discovered services

### 5. `otel://errors/recent`
Recent errors (last 50, within 60 minutes)

### 6. `otel://stats`
Telemetry statistics (counts, storage info)

## Code Location Information

The server automatically extracts and exposes code location information from telemetry data when available:
- **code.filepath** - Source file path
- **code.function** - Function/method name
- **code.lineno** - Line number
- **code.namespace** - Package/namespace

This information appears in the `code_location` field of spans and logs when instrumentation includes it. Use `get_code_locations` to filter telemetry by code location.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OTLP_RECEIVER_PORT` | Port for OTLP gRPC receiver | `4319` |

## Configuration

### Server Instructions

You can provide pre-defined instructions to guide the AI assistant on how to use this MCP server effectively. Edit `instructions.txt` to customize the instructions:

```text
# MCP Server Instructions

This file contains instructions that guide the AI assistant on how to use this MCP server effectively.

## Tool Usage Guidelines

1. For Incident Analysis:
   - Start with get_errors to identify recent failures
   - Use analyze_incident for a comprehensive summary
   - Use get_service_health to check specific service status
   - Use get_code_locations to find all telemetry from a specific file or function

2. For Debugging:
   - Use get_trace_by_id to follow a specific request
   - Use get_recent_traces with errors_only=true
   - Use get_recent_logs with errors_only=true
   - Use get_code_locations with filepath/function filters

3. For Performance Analysis:
   - Use get_recent_metrics to check system performance
   - Look for slow spans in trace analysis (duration_ms > 1000)
   - Check service health for average duration metrics
```

The instructions are automatically loaded when the server starts and are provided to the AI assistant to help it use the tools more effectively.

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

On Windows, if `host.docker.internal` doesn't work, use the WSL/Hyper-V adapter IP (usually `172.24.224.1`):

```yaml
exporters:
  otlp/mcp:
    endpoint: "172.24.224.1:4319"
    tls:
      insecure: true
```

## Usage Examples

### Incident Analysis Workflow

1. **Check receiver status:**
   ```
   What is the status of the OTLP receiver?
   ```

2. **Get recent errors:**
   ```
   What errors are occurring in my services?
   ```

3. **Analyze incident:**
   ```
   Analyze the recent incidents from the last hour
   ```

4. **Check specific service:**
   ```
   Show me the health of order-service
   ```

5. **Investigate code location:**
   ```
   Find all telemetry from OrderService.java processOrder method
   ```

### Debugging Workflow

1. **Find failed operations:**
   ```
   Get all failed traces from order-service
   ```

2. **Get error logs:**
   ```
   Show me all ERROR logs from payment-service
   ```

3. **Trace a specific request:**
   ```
   Get all spans for trace ID abc123def456
   ```

4. **Find code location issues:**
   ```
   Find all errors from PaymentController.java
   ```

### Performance Analysis

1. **Get service metrics:**
   ```
   Get all metrics from order-service
   ```

2. **Check service health:**
   ```
   Get health summary for payment-service
   ```

3. **Find slow operations:**
   ```
   Analyze incidents and show me slow operations
   ```

## Troubleshooting

### Import Errors

If you see import errors when starting the server:

1. Ensure all dependencies are installed:
   ```powershell
   pip install -r requirements.txt
   ```

2. Verify you're using the correct Python interpreter (the one Cursor uses)

3. Check that `grpcio`, `opentelemetry-proto`, and `protobuf` are installed:
   ```powershell
   pip install grpcio opentelemetry-proto protobuf
   ```

### Receiver Not Starting

If the OTLP receiver fails to start:

1. Check if port 4319 is already in use:
   ```powershell
   netstat -ano | findstr :4319
   ```

2. Verify the OTEL collector is configured to send data to `host.docker.internal:4319` (or the correct IP)

3. Check Cursor's error logs for detailed error messages

4. Try running the server manually to see error output:
   ```powershell
   python server.py
   ```

### No Telemetry Data

If no telemetry data is appearing:

1. Verify the OTEL collector is running: `.\start-collector.ps1 status`
2. Verify services are running and instrumented: `.\dev.ps1`
3. Check collector logs: `.\start-collector.ps1 logs`
4. Use `get_receiver_status` tool to verify the receiver is running
5. Check that services are sending data to the collector (check service logs for OTEL agent initialization)

### Port Already in Use

If port 4319 is already in use:

1. Find the process using the port:
   ```powershell
   netstat -ano | findstr :4319
   ```

2. Either stop that process or change the port:
   ```powershell
   $env:OTLP_RECEIVER_PORT="4320"
   python server.py
   ```

   Then update the collector config to use the new port.

## Best Practices

1. **Always check receiver status first** - Use `get_receiver_status` to ensure data is being collected

2. **Use appropriate limits** - Don't request too many results at once (defaults are usually fine)

3. **Filter by service** - When investigating specific services, always filter by service name

4. **Combine trace and log data** - For complete incident context, use both traces and logs

5. **Use code locations** - When errors occur, check the `error_code_locations` field to identify problematic code areas

6. **Start with errors** - For incident analysis, start with `get_errors` or `analyze_incident` before diving into specific traces

7. **Monitor service health** - Regularly check service health to catch issues early

## Storage Limits

The telemetry store has configurable limits to prevent memory issues:
- **Spans**: 10,000 (default)
- **Logs**: 10,000 (default)
- **Metrics**: 5,000 (default)

When limits are reached, oldest data is evicted (FIFO). Adjust these in `telemetry_store.py` if needed:

```python
store = TelemetryStore(max_spans=20000, max_logs=20000, max_metrics=10000)
```

## Performance Considerations

- The server uses async/await for all I/O operations
- Telemetry data is stored in-memory for fast access
- Code location extraction happens during ingestion (no performance impact on queries)
- Large result sets are limited by default to prevent overwhelming responses

## Security

- The OTLP receiver accepts connections from the collector only (configured via collector config)
- No authentication is required (assumes trusted network)
- For production, consider adding TLS and authentication
- Telemetry data is stored in-memory only (not persisted to disk)

## License

Internal Use Only
