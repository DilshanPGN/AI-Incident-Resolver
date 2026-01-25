"""
MCP Server for OpenTelemetry Incident Analysis.
Exposes OTEL traces, metrics, and logs to Cursor AI for incident analysis.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    EmbeddedResource,
)

from telemetry_store import TelemetryStore, Span, LogRecord, MetricDataPoint
from file_watcher import TelemetryWatcher

# #region agent log
DEBUG_LOG_PATH = Path(__file__).parent.parent / ".cursor" / "debug.log"
def _debug_log(location: str, message: str, data: dict):
    try:
        with open(DEBUG_LOG_PATH, 'a', encoding='utf-8') as f:
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "sessionId": "debug-session",
                "runId": "run1",
                "location": location,
                "message": message,
                "data": data
            }
            f.write(json.dumps(log_entry) + "\n")
    except Exception:
        pass
# #endregion


# Initialize the MCP server
server = Server("otel-incident-resolver")

# Global store and watcher
store = TelemetryStore(max_spans=10000, max_logs=10000, max_metrics=5000)
watcher: Optional[TelemetryWatcher] = None


def get_telemetry_path() -> Path:
    """Get the path to the telemetry directory."""
    # Look for telemetry directory relative to workspace
    workspace = os.environ.get("OTEL_TELEMETRY_PATH", "")
    if workspace:
        return Path(workspace)
    
    # Default: look in parent directory's telemetry folder
    script_dir = Path(__file__).parent.parent
    return script_dir / "telemetry"


def format_span(span: Span) -> dict:
    """Format a span for JSON output."""
    return {
        "trace_id": span.trace_id,
        "span_id": span.span_id,
        "parent_span_id": span.parent_span_id,
        "name": span.name,
        "service": span.service_name,
        "start_time": span.start_time.isoformat(),
        "end_time": span.end_time.isoformat(),
        "duration_ms": span.duration_ms,
        "status": span.status_code,
        "is_error": span.is_error,
        "attributes": span.attributes,
    }


def format_log(log: LogRecord) -> dict:
    """Format a log record for JSON output."""
    return {
        "timestamp": log.timestamp.isoformat(),
        "severity": log.severity,
        "body": log.body,
        "service": log.service_name,
        "trace_id": log.trace_id,
        "span_id": log.span_id,
        "is_error": log.is_error,
        "attributes": log.attributes,
    }


def format_metric(metric: MetricDataPoint) -> dict:
    """Format a metric for JSON output."""
    return {
        "timestamp": metric.timestamp.isoformat(),
        "name": metric.name,
        "value": metric.value,
        "unit": metric.unit,
        "service": metric.service_name,
        "attributes": metric.attributes,
    }


# ============================================================================
# MCP Resources
# ============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available telemetry resources."""
    return [
        Resource(
            uri="otel://traces/recent",
            name="Recent Traces",
            description="Recent trace spans from all services",
            mimeType="application/json",
        ),
        Resource(
            uri="otel://logs/recent",
            name="Recent Logs",
            description="Recent log records from all services",
            mimeType="application/json",
        ),
        Resource(
            uri="otel://metrics/current",
            name="Current Metrics",
            description="Current metrics snapshot from all services",
            mimeType="application/json",
        ),
        Resource(
            uri="otel://services",
            name="Discovered Services",
            description="List of all discovered services with telemetry",
            mimeType="application/json",
        ),
        Resource(
            uri="otel://errors/recent",
            name="Recent Errors",
            description="Recent errors and failed traces for incident analysis",
            mimeType="application/json",
        ),
        Resource(
            uri="otel://stats",
            name="Telemetry Statistics",
            description="Statistics about stored telemetry data",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a telemetry resource."""
    
    if uri == "otel://traces/recent":
        spans = store.get_recent_spans(limit=50)
        return json.dumps({
            "count": len(spans),
            "traces": [format_span(s) for s in spans]
        }, indent=2)
    
    elif uri == "otel://logs/recent":
        logs = store.get_recent_logs(limit=50)
        return json.dumps({
            "count": len(logs),
            "logs": [format_log(l) for l in logs]
        }, indent=2)
    
    elif uri == "otel://metrics/current":
        metrics = store.get_recent_metrics(limit=100)
        return json.dumps({
            "count": len(metrics),
            "metrics": [format_metric(m) for m in metrics]
        }, indent=2)
    
    elif uri == "otel://services":
        services = store.get_services()
        return json.dumps({
            "count": len(services),
            "services": services
        }, indent=2)
    
    elif uri == "otel://errors/recent":
        errors = store.get_errors(limit=50, since_minutes=60)
        return json.dumps({
            "summary": errors["summary"],
            "error_spans": [format_span(s) for s in errors["error_spans"]],
            "error_logs": [format_log(l) for l in errors["error_logs"]]
        }, indent=2)
    
    elif uri == "otel://stats":
        return json.dumps(store.get_stats(), indent=2)
    
    else:
        return json.dumps({"error": f"Unknown resource: {uri}"})


# ============================================================================
# MCP Tools
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available telemetry analysis tools."""
    return [
        Tool(
            name="get_recent_traces",
            description="Get recent traces from the OTEL collector. Useful for understanding request flow and identifying slow or failed operations.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of traces to return (default: 20)",
                        "default": 20
                    },
                    "service": {
                        "type": "string",
                        "description": "Filter by service name (e.g., 'order-service')"
                    },
                    "errors_only": {
                        "type": "boolean",
                        "description": "Only return failed/error traces",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="get_recent_logs",
            description="Get recent logs from the OTEL collector. Useful for debugging and understanding application behavior.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of logs to return (default: 30)",
                        "default": 30
                    },
                    "service": {
                        "type": "string",
                        "description": "Filter by service name"
                    },
                    "severity": {
                        "type": "string",
                        "description": "Filter by severity (TRACE, DEBUG, INFO, WARN, ERROR, FATAL)"
                    },
                    "errors_only": {
                        "type": "boolean",
                        "description": "Only return ERROR and FATAL logs",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="get_recent_metrics",
            description="Get recent metrics from the OTEL collector. Useful for understanding system health and performance.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of metrics to return (default: 50)",
                        "default": 50
                    },
                    "service": {
                        "type": "string",
                        "description": "Filter by service name"
                    },
                    "metric_name": {
                        "type": "string",
                        "description": "Filter by metric name"
                    }
                }
            }
        ),
        Tool(
            name="get_trace_by_id",
            description="Get all spans for a specific trace ID. Useful for deep-diving into a particular request's journey across services.",
            inputSchema={
                "type": "object",
                "properties": {
                    "trace_id": {
                        "type": "string",
                        "description": "The trace ID to look up"
                    }
                },
                "required": ["trace_id"]
            }
        ),
        Tool(
            name="get_errors",
            description="Get recent errors including failed traces and error logs. This is the primary tool for incident analysis.",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of errors to return (default: 30)",
                        "default": 30
                    },
                    "since_minutes": {
                        "type": "integer",
                        "description": "Look back this many minutes (default: 60)",
                        "default": 60
                    }
                }
            }
        ),
        Tool(
            name="analyze_incident",
            description="Analyze recent telemetry data and provide a summary of potential issues. Returns a structured incident report.",
            inputSchema={
                "type": "object",
                "properties": {
                    "since_minutes": {
                        "type": "integer",
                        "description": "Analyze data from the last N minutes (default: 30)",
                        "default": 30
                    }
                }
            }
        ),
        Tool(
            name="get_service_health",
            description="Get health summary for a specific service based on its recent telemetry.",
            inputSchema={
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The service name to analyze"
                    }
                },
                "required": ["service"]
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    # #region agent log
    _debug_log("server.py:call_tool", "Tool called", {"tool_name": name, "arguments": arguments})
    # #endregion
    
    if name == "get_recent_traces":
        limit = arguments.get("limit", 20)
        service = arguments.get("service")
        errors_only = arguments.get("errors_only", False)
        
        # #region agent log
        _debug_log("server.py:call_tool:get_recent_traces", "Querying traces", {"limit": limit, "service": service, "errors_only": errors_only})
        # #endregion
        
        spans = store.get_recent_spans(
            limit=limit,
            service=service,
            errors_only=errors_only
        )
        
        # #region agent log
        _debug_log("server.py:call_tool:get_recent_traces", "Traces retrieved", {"count": len(spans), "store_stats": store.get_stats()})
        # #endregion
        
        result = {
            "count": len(spans),
            "filters": {"service": service, "errors_only": errors_only},
            "traces": [format_span(s) for s in spans]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_recent_logs":
        limit = arguments.get("limit", 30)
        service = arguments.get("service")
        severity = arguments.get("severity")
        errors_only = arguments.get("errors_only", False)
        
        logs = store.get_recent_logs(
            limit=limit,
            service=service,
            severity=severity,
            errors_only=errors_only
        )
        
        result = {
            "count": len(logs),
            "filters": {"service": service, "severity": severity, "errors_only": errors_only},
            "logs": [format_log(l) for l in logs]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_recent_metrics":
        limit = arguments.get("limit", 50)
        service = arguments.get("service")
        metric_name = arguments.get("metric_name")
        
        metrics = store.get_recent_metrics(
            limit=limit,
            service=service,
            metric_name=metric_name
        )
        
        result = {
            "count": len(metrics),
            "filters": {"service": service, "metric_name": metric_name},
            "metrics": [format_metric(m) for m in metrics]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_trace_by_id":
        trace_id = arguments.get("trace_id", "")
        spans = store.get_trace(trace_id)
        
        result = {
            "trace_id": trace_id,
            "span_count": len(spans),
            "spans": [format_span(s) for s in spans]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "get_errors":
        limit = arguments.get("limit", 30)
        since_minutes = arguments.get("since_minutes", 60)
        
        errors = store.get_errors(limit=limit, since_minutes=since_minutes)
        
        result = {
            "summary": errors["summary"],
            "error_spans": [format_span(s) for s in errors["error_spans"]],
            "error_logs": [format_log(l) for l in errors["error_logs"]]
        }
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    elif name == "analyze_incident":
        since_minutes = arguments.get("since_minutes", 30)
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        
        # Gather data for analysis
        errors = store.get_errors(limit=100, since_minutes=since_minutes)
        all_spans = store.get_recent_spans(limit=200, since=since)
        all_logs = store.get_recent_logs(limit=200, since=since)
        
        # Calculate statistics
        error_rate = (
            len(errors["error_spans"]) / len(all_spans) * 100
            if all_spans else 0
        )
        
        # Find slow spans (> 1 second)
        slow_spans = [s for s in all_spans if s.duration_ms > 1000]
        
        # Group errors by service
        errors_by_service = {}
        for span in errors["error_spans"]:
            svc = span.service_name
            errors_by_service[svc] = errors_by_service.get(svc, 0) + 1
        for log in errors["error_logs"]:
            svc = log.service_name
            errors_by_service[svc] = errors_by_service.get(svc, 0) + 1
        
        report = {
            "analysis_window": {
                "since": since.isoformat(),
                "until": datetime.utcnow().isoformat(),
                "minutes": since_minutes
            },
            "summary": {
                "total_spans": len(all_spans),
                "total_logs": len(all_logs),
                "error_spans": len(errors["error_spans"]),
                "error_logs": len(errors["error_logs"]),
                "error_rate_percent": round(error_rate, 2),
                "slow_spans_count": len(slow_spans),
                "affected_services": list(errors_by_service.keys())
            },
            "errors_by_service": errors_by_service,
            "recent_errors": {
                "spans": [format_span(s) for s in errors["error_spans"][:10]],
                "logs": [format_log(l) for l in errors["error_logs"][:10]]
            },
            "slow_operations": [
                {
                    "name": s.name,
                    "service": s.service_name,
                    "duration_ms": s.duration_ms,
                    "trace_id": s.trace_id
                }
                for s in sorted(slow_spans, key=lambda x: x.duration_ms, reverse=True)[:10]
            ],
            "recommendations": []
        }
        
        # Generate recommendations
        if error_rate > 10:
            report["recommendations"].append(
                f"High error rate ({error_rate:.1f}%) detected. Investigate failing services."
            )
        if slow_spans:
            report["recommendations"].append(
                f"Found {len(slow_spans)} slow operations (>1s). Consider performance optimization."
            )
        if errors_by_service:
            top_error_svc = max(errors_by_service, key=errors_by_service.get)
            report["recommendations"].append(
                f"Service '{top_error_svc}' has the most errors ({errors_by_service[top_error_svc]}). Prioritize investigation."
            )
        
        return [TextContent(type="text", text=json.dumps(report, indent=2))]
    
    elif name == "get_service_health":
        service = arguments.get("service", "")
        since = datetime.utcnow() - timedelta(minutes=30)
        
        spans = store.get_recent_spans(limit=500, service=service, since=since)
        logs = store.get_recent_logs(limit=200, service=service, since=since)
        metrics = store.get_recent_metrics(limit=100, service=service, since=since)
        
        error_spans = [s for s in spans if s.is_error]
        error_logs = [l for l in logs if l.is_error]
        
        avg_duration = (
            sum(s.duration_ms for s in spans) / len(spans)
            if spans else 0
        )
        
        health = {
            "service": service,
            "analysis_window_minutes": 30,
            "spans": {
                "total": len(spans),
                "errors": len(error_spans),
                "error_rate_percent": round(len(error_spans) / len(spans) * 100, 2) if spans else 0,
                "avg_duration_ms": round(avg_duration, 2)
            },
            "logs": {
                "total": len(logs),
                "errors": len(error_logs),
                "by_severity": {}
            },
            "metrics_count": len(metrics),
            "status": "healthy"
        }
        
        # Count logs by severity
        for log in logs:
            sev = log.severity
            health["logs"]["by_severity"][sev] = health["logs"]["by_severity"].get(sev, 0) + 1
        
        # Determine health status
        if health["spans"]["error_rate_percent"] > 20:
            health["status"] = "critical"
        elif health["spans"]["error_rate_percent"] > 5:
            health["status"] = "degraded"
        elif error_logs:
            health["status"] = "warning"
        
        return [TextContent(type="text", text=json.dumps(health, indent=2))]
    
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ============================================================================
# Main Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    global watcher
    
    # #region agent log
    _debug_log("server.py:main", "MCP server starting", {"store_stats": store.get_stats()})
    # #endregion
    
    # Start the telemetry watcher
    telemetry_path = get_telemetry_path()
    print(f"Watching telemetry directory: {telemetry_path}", file=sys.stderr)
    
    # #region agent log
    _debug_log("server.py:main", "Initializing watcher", {"telemetry_path": str(telemetry_path), "path_exists": telemetry_path.exists()})
    # #endregion
    
    watcher = TelemetryWatcher(store, telemetry_path)
    watcher.start()
    
    # #region agent log
    _debug_log("server.py:main", "Watcher started", {"is_running": watcher.is_running, "store_stats_after_start": store.get_stats()})
    # #endregion
    
    try:
        # Run the MCP server over stdio
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        if watcher:
            watcher.stop()


if __name__ == "__main__":
    asyncio.run(main())
