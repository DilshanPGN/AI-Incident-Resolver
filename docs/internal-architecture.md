# AI Incident Resolver — Internal Architecture

Mermaid diagrams of components, protocols, data stores, and data flow.

---

## 1. Component & protocol overview

```mermaid
flowchart TB
    subgraph clients["MCP Clients"]
        Cursor["Cursor AI / MCP Client"]
    end

    subgraph mcp_servers["MCP Servers"]
        direction TB
        
        subgraph telemetry_mcp["Telemetry MCP Server (Python)"]
            ServerPy["server.py\nMCP protocol + tools"]
            OtlpRx["otlp_receiver.py\nOTLP gRPC server :4319"]
            TelemetryStore["telemetry_store.py\nIn-memory store"]
            ServerPy --> OtlpRx
            ServerPy --> TelemetryStore
        end

        subgraph base_mcp["Base MCP Server (Python)"]
            EntitlementStdio["entitlement-stdio.py\nor entitlement-sse.py"]
            EntitlementStdio --> OAuth["OAuth client\nToken cache"]
            EntitlementStdio --> HttpApi["HTTP client\n(httpx)"]
            EntitlementStdio --> DbClient["MySQL connector"]
        end

        subgraph github_mcp["GitHub MCP Server (Go)"]
            GhServer["github-mcp-server\nstdio or HTTP"]
        end
    end

    subgraph telemetry_data["Telemetry Data Store"]
        StoreDetail["In-memory (TelemetryStore)\n• Spans: 10,000 max\n• Logs: 10,000 max\n• Metrics: 5,000 max\n• FIFO eviction\n• Thread-safe deques"]
    end

    subgraph otel["OpenTelemetry Collector (Docker)"]
        Collector["otel-collector-contrib"]
        OtelRecv["Receivers:\n• OTLP gRPC :4317\n• OTLP HTTP :4318"]
        OtelProc["Processors:\n• batch\n• memory_limiter\n• resource"]
        OtelExport["Exporters:\n• debug (console)\n• otlp/mcp → :4319"]
        Collector --> OtelRecv
        OtelRecv --> OtelProc
        OtelProc --> OtelExport
    end

    subgraph java_services["Java Microservices (Spring Boot)"]
        OrderSvc["order-service\n:8080"]
        PaymentSvc["payment-service\n:8081"]
        ProductSvc["product-service\n:8083"]
        JavaAgent["OpenTelemetry\nJava Agent"]
        OrderSvc --> JavaAgent
        PaymentSvc --> JavaAgent
        ProductSvc --> JavaAgent
    end

    subgraph external_apis["External APIs & Data Stores"]
        WileyOAuth["Wiley OAuth\n(WILEY_TOKEN_URL)\nclient_credentials"]
        WileyAlm["Wiley ALM API\n(WILEY_ALM_BASE_URL)\n/v1/institutions\n/v1/institutions/entitlements"]
        MySQL["MySQL\norder_management\n(DB_HOST:3306)\n• query_database\n• list_database_tables\n• describe_table"]
        ProductApi["Product Service API\n:8083\n/api/products"]
        OrderApi["Order Service API\n:8081\n/orders"]
        GitHubApi["GitHub API\n(HTTPS)\nRepos, Issues, PRs,\nActions, etc."]
    end

    Cursor <-.->|"MCP stdio"| ServerPy
    Cursor <-.->|"MCP stdio"| EntitlementStdio
    Cursor <-.->|"MCP stdio\nor HTTP"| GhServer
    JavaAgent -->|"OTLP gRPC / OTLP HTTP"| OtelRecv
    OtelExport -->|"OTLP gRPC\n(endpoint :4319)"| OtlpRx
    OtlpRx --> TelemetryStore
    OAuth -->|"HTTPS POST\nx-www-form-urlencoded"| WileyOAuth
    HttpApi -->|"HTTPS GET\nBearer token"| WileyAlm
    HttpApi -->|"HTTP"| ProductApi
    HttpApi -->|"HTTP"| OrderApi
    DbClient -->|"TCP 3306\nMySQL protocol"| MySQL
    GhServer -->|"HTTPS\nREST / GraphQL"| GitHubApi
    TelemetryStore -.->|"reads/writes"| StoreDetail
```

---

## 2. Protocols & ports

| Protocol | Port / Transport | Role |
|----------|-------------------|------|
| **OTLP gRPC** | 4317 (collector in), 4319 (MCP server in) | Java → Collector; Collector → Telemetry MCP |
| **OTLP HTTP** | 4318 (collector in) | Alternative Java → Collector |
| **MCP stdio** | stdin/stdout | Cursor ↔ all MCP servers |
| **MCP SSE** | 8000 (optional) | Base MCP HTTP/SSE transport |
| **MCP HTTP** | HTTPS | GitHub MCP remote (e.g. api.githubcopilot.com) |
| **HTTP/REST** | 8080, 8081, 8083 | order / payment / product services; Wiley ALM APIs |
| **MySQL** | 3306 | Base MCP → order_management DB |
| **HTTPS** | — | Wiley OAuth, Wiley ALM, GitHub API |

```mermaid
flowchart LR
    subgraph protocols["Protocols & Ports"]
        P1["OTLP gRPC\n4317 (collector in)\n4319 (MCP in)"]
        P2["OTLP HTTP\n4318 (collector in)"]
        P3["MCP stdio\nCursor ↔ all MCP servers"]
        P4["MCP SSE\n:8000 (base-mcp optional)"]
        P5["HTTP/HTTPS\nREST: 8080,8081,8083\nWiley OAuth + ALM API\nGitHub API"]
        P6["MySQL\n3306 (order_management)"]
    end
```

---

## 3. Data stores

| Store | Location | Contents | Access |
|-------|----------|----------|--------|
| **TelemetryStore** | In-process (mcp-server) | Spans (max 10k), logs (max 10k), metrics (max 5k); FIFO, thread-safe | Telemetry MCP tools/resources |
| **MySQL order_management** | External (DB_HOST:3306) | products, orders, etc. | Base MCP: query_database, list_database_tables, describe_table (read-only SELECT) |
| **Token cache** | In-process (base-mcp) | OAuth access token, expiry with 5min buffer | Base MCP for Wiley ALM API calls |

```mermaid
flowchart TB
    subgraph stores["Data Stores"]
        DS1["TelemetryStore\n(in-process, mcp-server)\n• Spans: deque, max 10k\n• Logs: deque, max 10k\n• Metrics: deque, max 5k\n• FIFO eviction, thread-safe"]
        DS2["MySQL order_management\n(external)\n• Tables: products, orders, etc.\n• Access: Base MCP, read-only SELECT\n• Port 3306"]
        DS3["Token cache\n(in-process, base-mcp)\n• OAuth access token\n• In-memory, 5min buffer before expiry"]
    end

    subgraph consumers["Consumers"]
        Tc["Telemetry MCP\ntools/resources"]
        Bc["Base MCP\nquery_database, list_database_tables,\ndescribe_table"]
        Tc --> DS1
        Bc --> DS2
        Bc --> DS3
    end
```

---

## 4. End-to-end telemetry pipeline

```mermaid
sequenceDiagram
    participant Java as Java Services + OTEL Agent
    participant Collector as OTEL Collector (Docker)
    participant MCP as Telemetry MCP (otlp_receiver :4319)
    participant Store as TelemetryStore
    participant Cursor as Cursor AI

    Java->>+Collector: OTLP gRPC/HTTP (4317/4318) — traces, metrics, logs
    Collector->>Collector: batch, memory_limiter, resource
    Collector->>+MCP: OTLP gRPC (4319)
    MCP->>Store: add_span / add_log / add_metric
    MCP-->>-Collector: ack
    Collector-->>-Java: ack
    Cursor->>+MCP: MCP stdio: get_errors, analyze_incident, etc.
    MCP->>Store: get_recent_* / get_trace_by_id / ...
    Store-->>MCP: spans, logs, metrics
    MCP-->>-Cursor: JSON results
```

---

## Collector pipelines (otel-collector-config.yaml)

- **Receivers:** `otlp` — gRPC `0.0.0.0:4317`, HTTP `0.0.0.0:4318`
- **Processors:** `memory_limiter` → `batch` → `resource`
- **Exporters:** `debug` (console), `otlp/mcp` (MCP server at host:4319)
- **Pipelines:** traces, metrics, logs — each: receiver → processors → exporters
- **Extensions:** health_check (:13133), pprof (:1777), zpages (:55679); Prometheus metrics :8888

---

## File layout (architecture-related)

| Path | Role |
|------|------|
| `mcp-server/server.py` | Telemetry MCP entry; MCP tools/resources, wires OTLP receiver and store |
| `mcp-server/otlp_receiver.py` | OTLP gRPC server on :4319, pushes into TelemetryStore |
| `mcp-server/telemetry_store.py` | In-memory TelemetryStore (spans, logs, metrics) |
| `base-mcp-server/entitlement-stdio.py` | Base MCP over stdio; OAuth, MySQL, product/order HTTP |
| `base-mcp-server/entitlement-sse.py` | Base MCP over SSE on :8000 |
| `otel-collector/otel-collector-config.yaml` | Collector config (receivers, processors, exporters, pipelines) |
| `docker-compose.yaml` | Runs OTEL Collector container |
| `github-mcp-server/` | Go GitHub MCP server (stdio or HTTP) |
