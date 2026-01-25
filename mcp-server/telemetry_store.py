"""
In-memory storage for OpenTelemetry traces, metrics, and logs.
Provides query methods for filtering by service, time range, and error status.
"""

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Optional, Union
import threading

@dataclass
class Span:
    """Represents a single span from a trace."""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    service_name: str
    start_time: datetime
    end_time: datetime
    status_code: str  # "OK", "ERROR", "UNSET"
    attributes: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    
    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time).total_seconds() * 1000
    
    @property
    def is_error(self) -> bool:
        return self.status_code == "ERROR"


@dataclass
class LogRecord:
    """Represents a log record."""
    timestamp: datetime
    severity: str  # TRACE, DEBUG, INFO, WARN, ERROR, FATAL
    body: str
    service_name: str
    trace_id: Optional[str] = None
    span_id: Optional[str] = None
    attributes: dict = field(default_factory=dict)
    
    @property
    def is_error(self) -> bool:
        return self.severity in ("ERROR", "FATAL")


@dataclass
class MetricDataPoint:
    """Represents a metric data point."""
    timestamp: datetime
    name: str
    value: float
    service_name: str
    unit: str = ""
    attributes: dict = field(default_factory=dict)


class TelemetryStore:
    """
    Thread-safe in-memory storage for telemetry data.
    Uses deques with max length for automatic retention.
    """
    
    def __init__(self, max_spans: int = 10000, max_logs: int = 10000, max_metrics: int = 5000):
        self._spans: deque[Span] = deque(maxlen=max_spans)
        self._logs: deque[LogRecord] = deque(maxlen=max_logs)
        self._metrics: deque[MetricDataPoint] = deque(maxlen=max_metrics)
        self._lock = threading.RLock()
        self._services: set[str] = set()
    
    def add_span(self, span: Span) -> None:
        """Add a span to the store."""
        with self._lock:
            self._spans.append(span)
            self._services.add(span.service_name)
    
    def add_log(self, log: LogRecord) -> None:
        """Add a log record to the store."""
        with self._lock:
            self._logs.append(log)
            self._services.add(log.service_name)
    
    def add_metric(self, metric: MetricDataPoint) -> None:
        """Add a metric data point to the store."""
        with self._lock:
            self._metrics.append(metric)
            self._services.add(metric.service_name)
    
    def get_services(self) -> list[str]:
        """Get list of all discovered services."""
        with self._lock:
            return sorted(self._services)
    
    def get_recent_spans(
        self,
        limit: int = 100,
        service: Optional[str] = None,
        errors_only: bool = False,
        since: Optional[datetime] = None
    ) -> list[Span]:
        """Get recent spans with optional filtering."""
        with self._lock:
            spans = list(self._spans)
        
        # Apply filters
        if service:
            spans = [s for s in spans if s.service_name == service]
        if errors_only:
            spans = [s for s in spans if s.is_error]
        if since:
            spans = [s for s in spans if s.start_time >= since]
        
        # Return most recent first
        spans.sort(key=lambda s: s.start_time, reverse=True)
        return spans[:limit]
    
    def get_recent_logs(
        self,
        limit: int = 100,
        service: Optional[str] = None,
        severity: Optional[str] = None,
        errors_only: bool = False,
        since: Optional[datetime] = None
    ) -> list[LogRecord]:
        """Get recent logs with optional filtering."""
        with self._lock:
            logs = list(self._logs)
        
        # Apply filters
        if service:
            logs = [l for l in logs if l.service_name == service]
        if severity:
            logs = [l for l in logs if l.severity == severity]
        if errors_only:
            logs = [l for l in logs if l.is_error]
        if since:
            logs = [l for l in logs if l.timestamp >= since]
        
        # Return most recent first
        logs.sort(key=lambda l: l.timestamp, reverse=True)
        return logs[:limit]
    
    def get_recent_metrics(
        self,
        limit: int = 100,
        service: Optional[str] = None,
        metric_name: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> list[MetricDataPoint]:
        """Get recent metrics with optional filtering."""
        with self._lock:
            metrics = list(self._metrics)
        
        # Apply filters
        if service:
            metrics = [m for m in metrics if m.service_name == service]
        if metric_name:
            metrics = [m for m in metrics if m.name == metric_name]
        if since:
            metrics = [m for m in metrics if m.timestamp >= since]
        
        # Return most recent first
        metrics.sort(key=lambda m: m.timestamp, reverse=True)
        return metrics[:limit]
    
    def get_trace(self, trace_id: str) -> list[Span]:
        """Get all spans for a specific trace ID."""
        with self._lock:
            spans = [s for s in self._spans if s.trace_id == trace_id]
        spans.sort(key=lambda s: s.start_time)
        return spans
    
    def get_errors(self, limit: int = 50, since_minutes: int = 60) -> dict:
        """
        Get recent errors (failed spans and error logs).
        Returns a summary useful for incident analysis.
        """
        since = datetime.utcnow() - timedelta(minutes=since_minutes)
        
        error_spans = self.get_recent_spans(limit=limit, errors_only=True, since=since)
        error_logs = self.get_recent_logs(limit=limit, errors_only=True, since=since)
        
        return {
            "error_spans": error_spans,
            "error_logs": error_logs,
            "summary": {
                "total_error_spans": len(error_spans),
                "total_error_logs": len(error_logs),
                "affected_services": list(set(
                    [s.service_name for s in error_spans] + 
                    [l.service_name for l in error_logs]
                )),
                "time_range": {
                    "since": since.isoformat(),
                    "until": datetime.utcnow().isoformat()
                }
            }
        }
    
    def get_stats(self) -> dict:
        """Get storage statistics."""
        with self._lock:
            return {
                "total_spans": len(self._spans),
                "total_logs": len(self._logs),
                "total_metrics": len(self._metrics),
                "services": list(self._services),
                "max_spans": self._spans.maxlen,
                "max_logs": self._logs.maxlen,
                "max_metrics": self._metrics.maxlen
            }
    
    def clear(self) -> None:
        """Clear all stored telemetry data."""
        with self._lock:
            self._spans.clear()
            self._logs.clear()
            self._metrics.clear()
            self._services.clear()


def parse_otel_timestamp(ts: Union[str, int, float]) -> datetime:
    """Parse OTEL timestamp (nanoseconds or ISO string) to datetime."""
    if isinstance(ts, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00").replace("+00:00", ""))
        except (ValueError, AttributeError):
            # If ISO parse fails, try parsing as nanosecond timestamp string
            try:
                ts_num = int(ts)
                return datetime.utcfromtimestamp(ts_num / 1e9)
            except (ValueError, TypeError):
                pass
    elif isinstance(ts, (int, float)):
        # Nanoseconds since epoch
        return datetime.utcfromtimestamp(ts / 1e9)
    return datetime.utcnow()


def parse_span_from_otel(data: dict) -> Optional[Span]:
    """Parse a span from OTEL JSON format."""
    try:
        resource_attrs = {}
        if "resource" in data and "attributes" in data["resource"]:
            for attr in data["resource"]["attributes"]:
                resource_attrs[attr.get("key", "")] = attr.get("value", {}).get("stringValue", "")
        
        service_name = resource_attrs.get("service.name", "unknown")
        
        # Handle different OTEL export formats
        scope_spans = data.get("scopeSpans", data.get("instrumentationLibrarySpans", []))
        
        spans = []
        for scope in scope_spans:
            for span_data in scope.get("spans", []):
                status = span_data.get("status", {})
                status_code = status.get("code", "UNSET")
                if isinstance(status_code, int):
                    status_code = ["UNSET", "OK", "ERROR"][min(status_code, 2)]
                
                span = Span(
                    trace_id=span_data.get("traceId", ""),
                    span_id=span_data.get("spanId", ""),
                    parent_span_id=span_data.get("parentSpanId"),
                    name=span_data.get("name", ""),
                    service_name=service_name,
                    start_time=parse_otel_timestamp(span_data.get("startTimeUnixNano", 0)),
                    end_time=parse_otel_timestamp(span_data.get("endTimeUnixNano", 0)),
                    status_code=status_code,
                    attributes={
                        attr.get("key", ""): attr.get("value", {}).get("stringValue", str(attr.get("value", "")))
                        for attr in span_data.get("attributes", [])
                    },
                    events=span_data.get("events", [])
                )
                spans.append(span)
        
        return spans if spans else None
    except Exception as e:
        print(f"Error parsing span: {e}")
        return None


def parse_log_from_otel(data: dict) -> Optional[list[LogRecord]]:
    """Parse log records from OTEL JSON format."""
    try:
        resource_attrs = {}
        if "resource" in data and "attributes" in data["resource"]:
            for attr in data["resource"]["attributes"]:
                resource_attrs[attr.get("key", "")] = attr.get("value", {}).get("stringValue", "")
        
        service_name = resource_attrs.get("service.name", "unknown")
        
        logs = []
        for scope in data.get("scopeLogs", []):
            for log_data in scope.get("logRecords", []):
                severity_map = {
                    1: "TRACE", 2: "TRACE", 3: "TRACE", 4: "TRACE",
                    5: "DEBUG", 6: "DEBUG", 7: "DEBUG", 8: "DEBUG",
                    9: "INFO", 10: "INFO", 11: "INFO", 12: "INFO",
                    13: "WARN", 14: "WARN", 15: "WARN", 16: "WARN",
                    17: "ERROR", 18: "ERROR", 19: "ERROR", 20: "ERROR",
                    21: "FATAL", 22: "FATAL", 23: "FATAL", 24: "FATAL"
                }
                severity_num = log_data.get("severityNumber", 9)
                severity = log_data.get("severityText", severity_map.get(severity_num, "INFO"))
                
                body = log_data.get("body", {})
                if isinstance(body, dict):
                    body = body.get("stringValue", str(body))
                
                log = LogRecord(
                    timestamp=parse_otel_timestamp(log_data.get("timeUnixNano", 0)),
                    severity=severity,
                    body=str(body),
                    service_name=service_name,
                    trace_id=log_data.get("traceId"),
                    span_id=log_data.get("spanId"),
                    attributes={
                        attr.get("key", ""): attr.get("value", {}).get("stringValue", str(attr.get("value", "")))
                        for attr in log_data.get("attributes", [])
                    }
                )
                logs.append(log)
        
        return logs if logs else None
    except Exception as e:
        print(f"Error parsing log: {e}")
        return None


def parse_metric_from_otel(data: dict) -> Optional[list[MetricDataPoint]]:
    """Parse metrics from OTEL JSON format."""
    try:
        resource_attrs = {}
        if "resource" in data and "attributes" in data["resource"]:
            for attr in data["resource"]["attributes"]:
                resource_attrs[attr.get("key", "")] = attr.get("value", {}).get("stringValue", "")
        
        service_name = resource_attrs.get("service.name", "unknown")
        
        metrics = []
        for scope in data.get("scopeMetrics", []):
            for metric_data in scope.get("metrics", []):
                name = metric_data.get("name", "")
                unit = metric_data.get("unit", "")
                
                # Handle different metric types
                for data_type in ["gauge", "sum", "histogram"]:
                    if data_type in metric_data:
                        for dp in metric_data[data_type].get("dataPoints", []):
                            value = dp.get("asDouble", dp.get("asInt", 0))
                            metric = MetricDataPoint(
                                timestamp=parse_otel_timestamp(dp.get("timeUnixNano", 0)),
                                name=name,
                                value=float(value),
                                service_name=service_name,
                                unit=unit,
                                attributes={
                                    attr.get("key", ""): attr.get("value", {}).get("stringValue", str(attr.get("value", "")))
                                    for attr in dp.get("attributes", [])
                                }
                            )
                            metrics.append(metric)
        
        return metrics if metrics else None
    except Exception as e:
        print(f"Error parsing metric: {e}")
        return None
