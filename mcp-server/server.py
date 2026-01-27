"""
MCP Server for OpenTelemetry Incident Analysis.
Exposes OTEL traces, metrics, and logs to Cursor AI for incident analysis.
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta, timezone
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

try:
    from otlp_receiver import OTLPReceiver
except ImportError as e:
    print(f"ERROR: Failed to import OTLP receiver. Missing dependencies!", file=sys.stderr)
    print(f"ERROR: {e}", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"SOLUTION: Install dependencies using one of these methods:", file=sys.stderr)
    print(f"  1. From mcp-server directory: pip install -e .", file=sys.stderr)
    print(f"  2. Using requirements.txt: pip install -r mcp-server/requirements.txt", file=sys.stderr)
    print(f"  3. Direct install: pip install grpcio opentelemetry-proto protobuf", file=sys.stderr)
    print(f"", file=sys.stderr)
    print(f"Note: Make sure you're using the same Python interpreter that Cursor uses.", file=sys.stderr)
    raise


def load_instructions() -> Optional[str]:
    """Load server instructions from configuration file."""
    # Try to load from instructions.txt in the same directory as this script
    script_dir = Path(__file__).parent
    instructions_file = script_dir / "instructions.txt"
    
    if instructions_file.exists():
        try:
            with open(instructions_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                # Return the content as-is (markdown is fine for instructions)
                return content if content else None
        except Exception as e:
            print(f"WARNING: Failed to load instructions from {instructions_file}: {e}", file=sys.stderr)
    
    return None


# Load instructions from configuration file
server_instructions = load_instructions()

# Initialize the MCP server with instructions
server = Server("otel-incident-resolver", instructions=server_instructions)

# Global store and OTLP receiver
store = TelemetryStore(max_spans=10000, max_logs=10000, max_metrics=5000)
otlp_receiver: Optional[OTLPReceiver] = None


def format_span(span: Span) -> dict:
    """Format a span for JSON output."""
    result = {
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
    
    # Add code location information if available
    if span.has_code_info:
        code_info = {}
        if span.code_filepath:
            code_info["filepath"] = span.code_filepath
        if span.code_function:
            code_info["function"] = span.code_function
        if span.code_lineno:
            code_info["lineno"] = span.code_lineno
        if span.code_namespace:
            code_info["namespace"] = span.code_namespace
        if code_info:
            result["code_location"] = code_info
    
    return result


def format_log(log: LogRecord) -> dict:
    """Format a log record for JSON output."""
    result = {
        "timestamp": log.timestamp.isoformat(),
        "severity": log.severity,
        "body": log.body,
        "service": log.service_name,
        "trace_id": log.trace_id,
        "span_id": log.span_id,
        "is_error": log.is_error,
        "attributes": log.attributes,
    }
    
    # Add code location information if available
    if log.has_code_info:
        code_info = {}
        if log.code_filepath:
            code_info["filepath"] = log.code_filepath
        if log.code_function:
            code_info["function"] = log.code_function
        if log.code_lineno:
            code_info["lineno"] = log.code_lineno
        if log.code_namespace:
            code_info["namespace"] = log.code_namespace
        if code_info:
            result["code_location"] = code_info
    
    return result


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
        Tool(
            name="get_receiver_status",
            description="Get status of the OTLP receiver including whether it's running and listening for data.",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="get_code_locations",
            description="Get traces and logs filtered by code location (filepath, function, line number). Useful for finding all telemetry from a specific file or function.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filepath": {
                        "type": "string",
                        "description": "Filter by file path (partial match supported, e.g., 'OrderService.java')"
                    },
                    "function": {
                        "type": "string",
                        "description": "Filter by function/method name (partial match supported)"
                    },
                    "service": {
                        "type": "string",
                        "description": "Optional: Filter by service name"
                    },
                    "errors_only": {
                        "type": "boolean",
                        "description": "Only return errors (failed spans and error logs)",
                        "default": False
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 50)",
                        "default": 50
                    }
                }
            }
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    
    if name == "get_recent_traces":
        limit = arguments.get("limit", 20)
        service = arguments.get("service")
        errors_only = arguments.get("errors_only", False)
        
        spans = store.get_recent_spans(
            limit=limit,
            service=service,
            errors_only=errors_only
        )
        
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
        
        # Collect code locations from errors
        error_code_locations = {}
        for span in errors["error_spans"]:
            if span.has_code_info:
                loc_key = f"{span.code_filepath or 'unknown'}:{span.code_function or 'unknown'}"
                if span.code_lineno:
                    loc_key += f":{span.code_lineno}"
                error_code_locations[loc_key] = error_code_locations.get(loc_key, 0) + 1
        for log in errors["error_logs"]:
            if log.has_code_info:
                loc_key = f"{log.code_filepath or 'unknown'}:{log.code_function or 'unknown'}"
                if log.code_lineno:
                    loc_key += f":{log.code_lineno}"
                error_code_locations[loc_key] = error_code_locations.get(loc_key, 0) + 1
        
        result = {
            "summary": {
                **errors["summary"],
                "code_locations_with_errors": len(error_code_locations)
            },
            "error_code_locations": dict(sorted(
                error_code_locations.items(),
                key=lambda x: x[1],
                reverse=True
            )[:20]),
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
        
        # Collect code locations from errors
        error_code_locations = {}
        for span in errors["error_spans"]:
            if span.has_code_info:
                loc_key = f"{span.code_filepath or 'unknown'}:{span.code_function or 'unknown'}"
                if span.code_lineno:
                    loc_key += f":{span.code_lineno}"
                if loc_key not in error_code_locations:
                    error_code_locations[loc_key] = {
                        "filepath": span.code_filepath,
                        "function": span.code_function,
                        "lineno": span.code_lineno,
                        "namespace": span.code_namespace,
                        "error_count": 0
                    }
                error_code_locations[loc_key]["error_count"] += 1
        
        for log in errors["error_logs"]:
            if log.has_code_info:
                loc_key = f"{log.code_filepath or 'unknown'}:{log.code_function or 'unknown'}"
                if log.code_lineno:
                    loc_key += f":{log.code_lineno}"
                if loc_key not in error_code_locations:
                    error_code_locations[loc_key] = {
                        "filepath": log.code_filepath,
                        "function": log.code_function,
                        "lineno": log.code_lineno,
                        "namespace": log.code_namespace,
                        "error_count": 0
                    }
                error_code_locations[loc_key]["error_count"] += 1
        
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
                "affected_services": list(errors_by_service.keys()),
                "error_code_locations_count": len(error_code_locations)
            },
            "errors_by_service": errors_by_service,
            "error_code_locations": [
                {
                    "location": loc_key,
                    **loc_info
                }
                for loc_key, loc_info in sorted(
                    error_code_locations.items(),
                    key=lambda x: x[1]["error_count"],
                    reverse=True
                )[:20]
            ],
            "recent_errors": {
                "spans": [format_span(s) for s in errors["error_spans"][:10]],
                "logs": [format_log(l) for l in errors["error_logs"][:10]]
            },
            "slow_operations": [
                {
                    "name": s.name,
                    "service": s.service_name,
                    "duration_ms": s.duration_ms,
                    "trace_id": s.trace_id,
                    "code_location": {
                        "filepath": s.code_filepath,
                        "function": s.code_function,
                        "lineno": s.code_lineno
                    } if s.has_code_info else None
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
        if error_code_locations:
            top_error_loc = max(error_code_locations.items(), key=lambda x: x[1]["error_count"])
            report["recommendations"].append(
                f"Code location '{top_error_loc[0]}' has {top_error_loc[1]['error_count']} errors. Review this code location."
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
    
    elif name == "get_receiver_status":
        status = {
            "otlp_receiver": {
                "running": otlp_receiver.is_running if otlp_receiver else False,
                "port": int(os.environ.get("OTLP_RECEIVER_PORT", "4319")),
                "configured": otlp_receiver is not None
            },
            "store_stats": store.get_stats(),
            "services_discovered": store.get_services()
        }
        
        return [TextContent(type="text", text=json.dumps(status, indent=2))]
    
    elif name == "get_code_locations":
        filepath = arguments.get("filepath")
        function = arguments.get("function")
        service = arguments.get("service")
        errors_only = arguments.get("errors_only", False)
        limit = arguments.get("limit", 50)
        
        # Get spans and logs filtered by code location
        spans = store.get_recent_spans(
            limit=limit,
            service=service,
            errors_only=errors_only,
            code_filepath=filepath,
            code_function=function
        )
        
        logs = store.get_recent_logs(
            limit=limit,
            service=service,
            errors_only=errors_only,
            code_filepath=filepath,
            code_function=function
        )
        
        # Count unique code locations
        code_locations = set()
        for span in spans:
            if span.has_code_info:
                loc = f"{span.code_filepath or 'unknown'}:{span.code_function or 'unknown'}"
                if span.code_lineno:
                    loc += f":{span.code_lineno}"
                code_locations.add(loc)
        for log in logs:
            if log.has_code_info:
                loc = f"{log.code_filepath or 'unknown'}:{log.code_function or 'unknown'}"
                if log.code_lineno:
                    loc += f":{log.code_lineno}"
                code_locations.add(loc)
        
        result = {
            "filters": {
                "filepath": filepath,
                "function": function,
                "service": service,
                "errors_only": errors_only
            },
            "summary": {
                "spans_count": len(spans),
                "logs_count": len(logs),
                "unique_code_locations": len(code_locations)
            },
            "code_locations": sorted(code_locations),
            "spans": [format_span(s) for s in spans],
            "logs": [format_log(l) for l in logs]
        }
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    else:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]


# ============================================================================
# Main Entry Point
# ============================================================================

async def start_otlp_receiver():
    """Start the OTLP receiver as a background task."""
    global otlp_receiver
    
    otlp_port = int(os.environ.get("OTLP_RECEIVER_PORT", "4319"))
    
    try:
        otlp_receiver = OTLPReceiver(store, port=otlp_port)
        await otlp_receiver.start()
        print(f"OTLP receiver started on port {otlp_port}", file=sys.stderr)
        print(f"MCP server ready. Waiting for telemetry data...", file=sys.stderr)
    except Exception as e:
        print(f"ERROR: Failed to start OTLP receiver: {e}", file=sys.stderr)
        # Don't raise - allow MCP server to continue without receiver


async def main():
    """Run the MCP server."""
    # Start the OTLP receiver as a background task after MCP server is ready
    receiver_task = None
    
    try:
        # Run the MCP server over stdio
        # Start the OTLP receiver as a background task once stdio is connected
        async with stdio_server() as (read_stream, write_stream):
            # Start OTLP receiver in background after stdio connection is established
            receiver_task = asyncio.create_task(start_otlp_receiver())
            
            # Run the MCP server (this will handle initialization immediately)
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    finally:
        # Cancel receiver task if still running
        if receiver_task and not receiver_task.done():
            receiver_task.cancel()
            try:
                await receiver_task
            except asyncio.CancelledError:
                pass
        
        # Stop OTLP receiver if it was started
        if otlp_receiver:
            try:
                await otlp_receiver.stop()
            except Exception as e:
                print(f"ERROR: Failed to stop OTLP receiver: {e}", file=sys.stderr)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        raise
