"""
OTLP gRPC Receiver for OpenTelemetry data.
Receives traces, metrics, and logs from the OTEL collector over gRPC.
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

import grpc
from opentelemetry.proto.collector.trace.v1 import trace_service_pb2, trace_service_pb2_grpc
from opentelemetry.proto.collector.metrics.v1 import metrics_service_pb2, metrics_service_pb2_grpc
from opentelemetry.proto.collector.logs.v1 import logs_service_pb2, logs_service_pb2_grpc
from opentelemetry.proto.trace.v1 import trace_pb2
from opentelemetry.proto.metrics.v1 import metrics_pb2
from opentelemetry.proto.logs.v1 import logs_pb2
from opentelemetry.proto.common.v1 import common_pb2
from opentelemetry.proto.resource.v1 import resource_pb2

from telemetry_store import TelemetryStore, Span, LogRecord, MetricDataPoint, parse_otel_timestamp, extract_code_info

def extract_resource_attributes(resource: resource_pb2.Resource) -> dict:
    """Extract attributes from resource."""
    attrs = {}
    for attr in resource.attributes:
        key = attr.key
        value = ""
        if attr.value.HasField("string_value"):
            value = attr.value.string_value
        elif attr.value.HasField("int_value"):
            value = attr.value.int_value
        elif attr.value.HasField("double_value"):
            value = attr.value.double_value
        elif attr.value.HasField("bool_value"):
            value = attr.value.bool_value
        else:
            value = str(attr.value)
        attrs[key] = value
    return attrs


def extract_attributes(attrs: list[common_pb2.KeyValue]) -> dict:
    """Extract attributes from KeyValue list."""
    result = {}
    for attr in attrs:
        key = attr.key
        value = ""
        if attr.value.HasField("string_value"):
            value = attr.value.string_value
        elif attr.value.HasField("int_value"):
            value = attr.value.int_value
        elif attr.value.HasField("double_value"):
            value = attr.value.double_value
        elif attr.value.HasField("bool_value"):
            value = attr.value.bool_value
        else:
            value = str(attr.value)
        result[key] = value
    return result


def parse_span_from_proto(resource: resource_pb2.Resource, scope_span: trace_pb2.ScopeSpans) -> list[Span]:
    """Parse spans from protobuf format."""
    spans = []
    resource_attrs = extract_resource_attributes(resource)
    service_name = resource_attrs.get("service.name", "unknown")
    
    for span_pb in scope_span.spans:
        # Parse status
        status_code = "UNSET"
        if span_pb.status.code == trace_pb2.Status.StatusCode.STATUS_CODE_OK:
            status_code = "OK"
        elif span_pb.status.code == trace_pb2.Status.StatusCode.STATUS_CODE_ERROR:
            status_code = "ERROR"
        
        # Parse timestamps
        start_time = parse_otel_timestamp(span_pb.start_time_unix_nano)
        end_time = parse_otel_timestamp(span_pb.end_time_unix_nano)
        
        # Convert bytes to hex strings
        trace_id_hex = span_pb.trace_id.hex() if span_pb.trace_id else ""
        span_id_hex = span_pb.span_id.hex() if span_pb.span_id else ""
        parent_span_id_hex = span_pb.parent_span_id.hex() if span_pb.parent_span_id and len(span_pb.parent_span_id) > 0 else None
        
        # Extract attributes and code information
        attrs = extract_attributes(span_pb.attributes)
        filepath, function, lineno, namespace = extract_code_info(attrs)
        
        span = Span(
            trace_id=trace_id_hex,
            span_id=span_id_hex,
            parent_span_id=parent_span_id_hex,
            name=span_pb.name,
            service_name=service_name,
            start_time=start_time,
            end_time=end_time,
            status_code=status_code,
            attributes=attrs,
            events=[{"name": e.name, "time": e.time_unix_nano} for e in span_pb.events],
            code_filepath=filepath,
            code_function=function,
            code_lineno=lineno,
            code_namespace=namespace
        )
        spans.append(span)
    
    return spans


def parse_log_from_proto(resource: resource_pb2.Resource, scope_log: logs_pb2.ScopeLogs) -> list[LogRecord]:
    """Parse log records from protobuf format."""
    logs = []
    resource_attrs = extract_resource_attributes(resource)
    service_name = resource_attrs.get("service.name", "unknown")
    
    severity_map = {
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_TRACE: "TRACE",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_TRACE2: "TRACE",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_TRACE3: "TRACE",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_TRACE4: "TRACE",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_DEBUG: "DEBUG",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_DEBUG2: "DEBUG",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_DEBUG3: "DEBUG",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_DEBUG4: "DEBUG",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_INFO: "INFO",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_INFO2: "INFO",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_INFO3: "INFO",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_INFO4: "INFO",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_WARN: "WARN",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_WARN2: "WARN",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_WARN3: "WARN",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_WARN4: "WARN",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_ERROR: "ERROR",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_ERROR2: "ERROR",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_ERROR3: "ERROR",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_ERROR4: "ERROR",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_FATAL: "FATAL",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_FATAL2: "FATAL",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_FATAL3: "FATAL",
        logs_pb2.SeverityNumber.SEVERITY_NUMBER_FATAL4: "FATAL",
    }
    
    for log_pb in scope_log.log_records:
        severity = severity_map.get(log_pb.severity_number, "INFO")
        if log_pb.severity_text:
            severity = log_pb.severity_text
        
        # Parse body
        body = ""
        if log_pb.body.HasField("string_value"):
            body = log_pb.body.string_value
        else:
            body = str(log_pb.body)
        
        # Parse trace context
        trace_id = log_pb.trace_id.hex() if log_pb.trace_id and len(log_pb.trace_id) > 0 else None
        span_id = log_pb.span_id.hex() if log_pb.span_id and len(log_pb.span_id) > 0 else None
        
        # Extract attributes and code information
        attrs = extract_attributes(log_pb.attributes)
        filepath, function, lineno, namespace = extract_code_info(attrs)
        
        log = LogRecord(
            timestamp=parse_otel_timestamp(log_pb.time_unix_nano),
            severity=severity,
            body=body,
            service_name=service_name,
            trace_id=trace_id,
            span_id=span_id,
            attributes=attrs,
            code_filepath=filepath,
            code_function=function,
            code_lineno=lineno,
            code_namespace=namespace
        )
        logs.append(log)
    
    return logs


def parse_metric_from_proto(resource: resource_pb2.Resource, scope_metric: metrics_pb2.ScopeMetrics) -> list[MetricDataPoint]:
    """Parse metrics from protobuf format."""
    metrics = []
    resource_attrs = extract_resource_attributes(resource)
    service_name = resource_attrs.get("service.name", "unknown")
    
    for metric_pb in scope_metric.metrics:
        name = metric_pb.name
        unit = metric_pb.unit
        
        # Handle gauge
        if metric_pb.HasField("gauge"):
            for dp in metric_pb.gauge.data_points:
                value = dp.as_double if dp.HasField("as_double") else (dp.as_int if dp.HasField("as_int") else 0)
                metric = MetricDataPoint(
                    timestamp=parse_otel_timestamp(dp.time_unix_nano),
                    name=name,
                    value=float(value),
                    service_name=service_name,
                    unit=unit,
                    attributes=extract_attributes(dp.attributes)
                )
                metrics.append(metric)
        
        # Handle sum
        if metric_pb.HasField("sum"):
            for dp in metric_pb.sum.data_points:
                value = dp.as_double if dp.HasField("as_double") else (dp.as_int if dp.HasField("as_int") else 0)
                metric = MetricDataPoint(
                    timestamp=parse_otel_timestamp(dp.time_unix_nano),
                    name=name,
                    value=float(value),
                    service_name=service_name,
                    unit=unit,
                    attributes=extract_attributes(dp.attributes)
                )
                metrics.append(metric)
        
        # Handle histogram
        if metric_pb.HasField("histogram"):
            for dp in metric_pb.histogram.data_points:
                # Use count as the value for histogram
                metric = MetricDataPoint(
                    timestamp=parse_otel_timestamp(dp.time_unix_nano),
                    name=name,
                    value=float(dp.count),
                    service_name=service_name,
                    unit=unit,
                    attributes=extract_attributes(dp.attributes)
                )
                metrics.append(metric)
    
    return metrics


class TraceServiceServicer(trace_service_pb2_grpc.TraceServiceServicer):
    """gRPC servicer for trace service."""
    
    def __init__(self, store: TelemetryStore):
        self.store = store
    
    def Export(self, request: trace_service_pb2.ExportTraceServiceRequest, context):
        """Handle trace export requests."""
        for resource_span in request.resource_spans:
            resource = resource_span.resource
            for scope_span in resource_span.scope_spans:
                spans = parse_span_from_proto(resource, scope_span)
                for span in spans:
                    self.store.add_span(span)
        
        return trace_service_pb2.ExportTraceServiceResponse()


class MetricsServiceServicer(metrics_service_pb2_grpc.MetricsServiceServicer):
    """gRPC servicer for metrics service."""
    
    def __init__(self, store: TelemetryStore):
        self.store = store
    
    def Export(self, request: metrics_service_pb2.ExportMetricsServiceRequest, context):
        """Handle metrics export requests."""
        for resource_metric in request.resource_metrics:
            resource = resource_metric.resource
            for scope_metric in resource_metric.scope_metrics:
                metrics = parse_metric_from_proto(resource, scope_metric)
                for metric in metrics:
                    self.store.add_metric(metric)
        
        return metrics_service_pb2.ExportMetricsServiceResponse()


class LogsServiceServicer(logs_service_pb2_grpc.LogsServiceServicer):
    """gRPC servicer for logs service."""
    
    def __init__(self, store: TelemetryStore):
        self.store = store
    
    def Export(self, request: logs_service_pb2.ExportLogsServiceRequest, context):
        """Handle logs export requests."""
        for resource_log in request.resource_logs:
            resource = resource_log.resource
            for scope_log in resource_log.scope_logs:
                logs = parse_log_from_proto(resource, scope_log)
                for log in logs:
                    self.store.add_log(log)
        
        return logs_service_pb2.ExportLogsServiceResponse()


class OTLPReceiver:
    """OTLP gRPC receiver server."""
    
    def __init__(self, store: TelemetryStore, port: int = 4319):
        self.store = store
        self.port = port
        self.server: Optional[grpc.aio.Server] = None
        self._running = False
    
    async def start(self):
        """Start the gRPC server."""
        if self._running:
            return
        
        try:
            self.server = grpc.aio.server()
            
            # Add servicers
            trace_service_pb2_grpc.add_TraceServiceServicer_to_server(
                TraceServiceServicer(self.store), self.server
            )
            metrics_service_pb2_grpc.add_MetricsServiceServicer_to_server(
                MetricsServiceServicer(self.store), self.server
            )
            logs_service_pb2_grpc.add_LogsServiceServicer_to_server(
                LogsServiceServicer(self.store), self.server
            )
            
            # Listen on port - use 0.0.0.0 to bind to all IPv4 interfaces
            # This will accept connections from localhost (which the collector uses)
            # We use IPv4 only to avoid IPv6 binding issues on Windows
            listen_addr = f'0.0.0.0:{self.port}'
            self.server.add_insecure_port(listen_addr)
            
            # Start the server
            await self.server.start()
            self._running = True
            
            # Print to stderr so it's visible
            import sys
            print(f"OTLP receiver started on port {self.port}", file=sys.stderr)
            print(f"Listening on {listen_addr} (IPv4)", file=sys.stderr)
        except Exception as e:
            import sys
            print(f"ERROR: Failed to start OTLP receiver on port {self.port}: {e}", file=sys.stderr)
            raise
    
    async def stop(self):
        """Stop the gRPC server."""
        if self.server and self._running:
            await self.server.stop(grace=5)
            self._running = False
            import sys
            print("OTLP receiver stopped", file=sys.stderr)
    
    @property
    def is_running(self) -> bool:
        return self._running
