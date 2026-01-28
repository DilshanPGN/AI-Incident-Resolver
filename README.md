# AI-Incident-Resolver

Build an AI-driven observability & incident-analysis agent that plugs into Java Spring Boot microservices and understands the system end-to-end, enabling automatic root-cause analysis and fix suggestions for complex production incidents.

## Overview

This project provides a comprehensive AI-powered incident analysis system that integrates OpenTelemetry telemetry data with AI assistants (via MCP - Model Context Protocol) to enable real-time observability, automatic incident detection, and intelligent root-cause analysis.

## Architecture

```
Java Services (Spring Boot)
    ↓ (OTLP gRPC/HTTP)
OpenTelemetry Collector (Docker)
    ↓ (OTLP gRPC)
MCP Server (Python) :4319
    ↓ (stdio)
Cursor AI / Other MCP Clients
```

The MCP server receives telemetry data directly from the OTEL collector over gRPC, enabling real-time data ingestion without file I/O. This architecture supports cloud deployments where services are distributed across containers/pods.

## Project Structure

This project contains three main MCP servers with different purposes:

### 1. Telemetry MCP Server (`mcp-server/`)
Receives and stores OpenTelemetry data from microservices for observability and incident analysis.

**Features:**
- Real-time telemetry ingestion via OTLP gRPC (port 4319)
- Trace, metric, and log storage (in-memory, configurable limits)
- AI-powered incident analysis with code location tracking
- 9 MCP tools for querying telemetry data
- 6 MCP resources for accessing telemetry snapshots

**Documentation:** See [`mcp-server/README.md`](mcp-server/README.md)

### 2. Base MCP Server (`base-mcp-server/`)
Provides access to entitlement/institution APIs, database queries, and product/order service operations.

**Features:**
- API integration (OAuth token management)
- MySQL database query capabilities (read-only, secure)
- Product service integration (create/retrieve products)
- Order service integration (full CRUD operations)
- 12 MCP tools for business operations

**Documentation:** See [`base-mcp-server/README.md`](base-mcp-server/README.md)

### 3. GitHub MCP Server (`github-mcp-server/`)
GitHub integration for repository management, issues, pull requests, and more.

**Features:**
- Repository browsing and code search
- Issue and PR management
- GitHub Actions workflow monitoring
- Code security and Dependabot alerts
- Comprehensive GitHub API coverage

**Documentation:** See [`github-mcp-server/README.md`](github-mcp-server/README.md)

## Services

| Service | Port | Description |
|---------|------|-------------|
| order-service | 8080 | Order management service |
| payment-service | 8081 | Payment processing service |
| product-service | 8083 | Product catalog service |

## Quick Start

### Prerequisites

- **Java 17+** - For Spring Boot microservices
- **Maven 3.6+** - For building Java services
- **Docker Desktop** - For OpenTelemetry Collector
- **Python 3.10+** - For MCP servers (Python 3.14 recommended, see `.python-version`)
- **Cursor IDE** - Or another MCP-compatible client

### 1. Install MCP Server Dependencies

```powershell
# For Telemetry MCP Server (OpenTelemetry observability)
cd mcp-server
pip install -e .
# Or install dependencies directly:
pip install -r requirements.txt

# For Base MCP Server (entitlement, database, product service)
cd base-mcp-server
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

The MCP servers are automatically started by Cursor when configured. The configuration is in `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "otel-incident-resolver": {
      "command": "python",
      "args": ["mcp-server/server.py"],
      "cwd": "<workspace-path>"
    },
    "base-mcp-server": {
      "command": "python",
      "args": ["base-mcp-server/entitlement-stdio.py"],
      "cwd": "<workspace-path>",
      "env": {
        "WILEY_TOKEN_URL": "https://your-oauth-endpoint/token",
        "WILEY_CLIENT_ID": "your_client_id",
        "WILEY_CLIENT_SECRET": "your_client_secret",
        "WILEY_ALM_BASE_URL": "https://your-api-base-url",
        "PRODUCT_SERVICE_URL": "http://localhost:8083",
        "ORDER_SERVICE_URL": "http://localhost:8081"
      }
    }
  }
}
```

**Note:** 
- Replace `<workspace-path>` with the absolute path to your project root
- Restart Cursor after configuring MCP to load the servers

## OpenTelemetry Configuration

### Collector Configuration

The collector is configured via `otel-collector/otel-collector-config.yaml`:
- Receives telemetry via OTLP (gRPC on 4317, HTTP on 4318)
- Processes data with batching, memory limiting, and resource attributes
- Exports to:
  - **Debug exporter** (console logs for development)
  - **OTLP exporter** to MCP server at `host.docker.internal:4319` (or WSL/Hyper-V adapter IP)

### Java Agent Configuration

Services are instrumented using the OpenTelemetry Java agent with the following environment variables:
- `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317`
- `OTEL_EXPORTER_OTLP_PROTOCOL=grpc`
- `OTEL_SERVICE_NAME` - Set per service (order-service, payment-service)
- `OTEL_RESOURCE_ATTRIBUTES` - Service metadata

## MCP Server Integration

The MCP (Model Context Protocol) servers expose data to Cursor AI for analysis and operations.

### Telemetry MCP Server Tools

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
| `get_code_locations` | Filter telemetry by code location (filepath, function) |

### Telemetry MCP Server Resources

| Resource URI | Description |
|--------------|-------------|
| `otel://traces/recent` | Recent trace spans |
| `otel://logs/recent` | Recent log records |
| `otel://metrics/current` | Current metrics |
| `otel://services` | Discovered services |
| `otel://errors/recent` | Recent errors |
| `otel://stats` | Telemetry statistics |

### Base MCP Server Tools

| Tool | Description |
|------|-------------|
| `search_license_entitlements` | Search license entitlements |
| `search_institutions` | Search institutions |
| `query_database` | Execute SQL SELECT queries |
| `list_database_tables` | List all database tables |
| `describe_table` | Get table schema and sample data |
| `create_product` | Create a new product |
| `get_product` | Retrieve a product by ID |
| `create_order` | Create a new order |
| `get_all_orders` | Retrieve all orders |
| `get_order_by_id` | Retrieve an order by ID |
| `update_order` | Update an existing order |
| `delete_order` | Delete an order |

### Using with Cursor AI

Once configured, you can ask Cursor AI questions like:

**Telemetry Analysis:**
- "What errors are occurring in my services?"
- "Analyze the recent incidents"
- "Show me the health of order-service"
- "Get traces for the payment-service"
- "What is the status of the OTLP receiver?"
- "Find all telemetry from OrderService.java"

**Business Operations:**
- "How many PHYSICAL products are in the database?"
- "Create a new digital product called 'Test eBook' with ID 'EBOOK-001'"
- "Get the details of product PROD-020"
- "Show me all orders"
- "Create an order for product 'Laptop' with quantity 2 and price 1000"

The AI will use the MCP tools to query your live telemetry data and perform operations.

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
5. Verify Java agent JAR file exists: `opentelemetry-javaagent.jar`

### Import Errors in MCP Server

If you see import errors when starting the MCP server:

1. Ensure all dependencies are installed:
   ```powershell
   cd mcp-server
   pip install -r requirements.txt
   ```

2. Verify you're using the correct Python interpreter (the one Cursor uses)

3. Check that `grpcio`, `opentelemetry-proto`, and `protobuf` are installed:
   ```powershell
   pip install grpcio opentelemetry-proto protobuf
   ```

### Database Connection Issues

If the Base MCP server cannot connect to the database:

1. Verify VPN/network access to the database host
2. Check credentials in `.env` file or `mcp.json` environment variables
3. Ensure MySQL port 3306 is accessible
4. Test connection manually:
   ```powershell
   mysql -h your-database-host -u your_user -p order_management
   ```

## Project Structure

```
├── order-service/           # Order management microservice
├── payment-service/         # Payment processing microservice
├── product-service/          # Product catalog microservice
├── otel-collector/          # OpenTelemetry Collector config
│   └── otel-collector-config.yaml
├── mcp-server/              # MCP server for telemetry/observability
│   ├── pyproject.toml       # Python dependencies
│   ├── server.py            # MCP server implementation
│   ├── telemetry_store.py   # In-memory telemetry storage
│   ├── otlp_receiver.py     # OTLP gRPC receiver (receives data from collector)
│   └── instructions.txt     # AI assistant instructions
├── base-mcp-server/         # MCP server for APIs, database, product/order services
│   ├── entitlement-stdio.py # Main MCP server (stdio transport)
│   ├── entitlement-sse.py   # Alternative MCP server (SSE transport)
│   ├── pyproject.toml       # Python dependencies
│   ├── requirements.txt    # Python dependencies
│   ├── env.example          # Environment variable template
│   └── SETUP.md             # Setup guide
├── github-mcp-server/       # GitHub MCP server (submodule or included)
├── .cursor/mcp.json         # Cursor MCP configuration
├── docker-compose.yaml      # Docker Compose for OTEL Collector
├── opentelemetry-javaagent.jar  # OpenTelemetry Java agent
├── dev.ps1                  # PowerShell script to start services
├── dev.bat                  # Batch script to start services
├── start-collector.ps1      # PowerShell script for collector
└── start-collector.bat      # Batch script for collector
```

## Features

### Telemetry Analysis
- **Real-time Data Ingestion**: Direct gRPC connection from collector to MCP server
- **Code Location Tracking**: Automatically extracts and tracks code locations from telemetry
- **Incident Analysis**: AI-powered analysis with error grouping and recommendations
- **Service Health Monitoring**: Per-service health summaries with error rates and performance metrics
- **Trace Analysis**: Full trace visualization with span relationships

### Business Operations
- **Database Queries**: Secure read-only SQL queries with automatic validation
- **Product Management**: Create and retrieve products from product service
- **Order Management**: Full CRUD operations for orders
- **API Integration**: OAuth token management for entitlement/institution APIs

### Security
- **Read-only Database Access**: Only SELECT queries allowed
- **Query Validation**: Blocks dangerous SQL keywords (DROP, DELETE, UPDATE, etc.)
- **Result Limiting**: Prevents large data dumps (max 1000 rows)
- **OAuth Token Caching**: Secure API authentication with automatic refresh
- **Environment Variable Isolation**: Credentials stored in `.env` or `mcp.json`

## Development

### Adding New Services

To add a new microservice:

1. Add service configuration to `dev.ps1` or `dev.bat`
2. Set `OTEL_SERVICE_NAME` environment variable
3. Configure OpenTelemetry Java agent
4. Service will automatically appear in telemetry data

### Extending MCP Servers

To add new tools to MCP servers:

1. **Telemetry MCP Server**: Add tool definition in `mcp-server/server.py`
2. **Base MCP Server**: Add tool using `@mcp.tool()` decorator in `base-mcp-server/entitlement-stdio.py`

### Testing

```powershell
# Test telemetry data flow
.\test_mcp_data_flow.ps1

# Test product service integration
cd base-mcp-server
python test_product_tools.py
```

## License

Internal Use Only

## Support

For questions or issues:
- Check the troubleshooting section above
- Review individual MCP server README files
- Contact the development team
