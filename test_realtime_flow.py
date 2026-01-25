"""Test real-time data flow: API calls -> Collector -> Files -> MCP Server"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "mcp-server"))

from telemetry_store import TelemetryStore
from file_watcher import TelemetryWatcher

def test_realtime_flow():
    """Test that MCP server receives data when APIs are called."""
    print("=" * 60)
    print("Testing Real-time Data Flow")
    print("=" * 60)
    
    store = TelemetryStore()
    telemetry_dir = Path(__file__).parent / "telemetry"
    
    # Get initial stats
    watcher = TelemetryWatcher(store, telemetry_dir)
    watcher.start()
    time.sleep(2)
    
    initial_stats = store.get_stats()
    initial_spans = initial_stats['total_spans']
    initial_logs = initial_stats['total_logs']
    initial_metrics = initial_stats['total_metrics']
    
    print(f"\nInitial state:")
    print(f"  Spans: {initial_spans}")
    print(f"  Logs: {initial_logs}")
    print(f"  Metrics: {initial_metrics}")
    print(f"  Services: {initial_stats['services']}")
    
    print(f"\nPlease call the APIs now:")
    print(f"  - GET http://localhost:8080/orders")
    print(f"  - GET http://localhost:8081/api/payments")
    print(f"\nWaiting 10 seconds for data to flow...")
    
    time.sleep(10)
    
    # Check new stats
    final_stats = store.get_stats()
    final_spans = final_stats['total_spans']
    final_logs = final_stats['total_logs']
    final_metrics = final_stats['total_metrics']
    
    print(f"\nFinal state:")
    print(f"  Spans: {final_spans} (+{final_spans - initial_spans})")
    print(f"  Logs: {final_logs} (+{final_logs - initial_logs})")
    print(f"  Metrics: {final_metrics} (+{final_metrics - initial_metrics})")
    print(f"  Services: {final_stats['services']}")
    
    # Get recent spans
    recent_spans = store.get_recent_spans(limit=10)
    print(f"\nRecent spans ({len(recent_spans)}):")
    for span in recent_spans[:5]:
        print(f"  - {span.name} from {span.service_name} (trace: {span.trace_id[:16]}...)")
    
    watcher.stop()
    
    # Verify data flow
    spans_increased = final_spans > initial_spans
    logs_increased = final_logs > initial_logs
    metrics_increased = final_metrics > initial_metrics
    
    print(f"\n" + "=" * 60)
    print("Test Results")
    print("=" * 60)
    print(f"Spans increased: {'YES' if spans_increased else 'NO'}")
    print(f"Logs increased: {'YES' if logs_increased else 'NO'}")
    print(f"Metrics increased: {'YES' if metrics_increased else 'NO'}")
    
    success = spans_increased or logs_increased or metrics_increased
    if success:
        print(f"\nSUCCESS: MCP server is receiving data in real-time!")
    else:
        print(f"\n⚠️  No new data detected. Make sure:")
        print(f"  1. Services are running")
        print(f"  2. OTEL Collector is running")
        print(f"  3. APIs were called during the wait period")
    
    return success

if __name__ == "__main__":
    success = test_realtime_flow()
    sys.exit(0 if success else 1)
