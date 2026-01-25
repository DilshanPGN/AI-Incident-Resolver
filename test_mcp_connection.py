"""
Test script to verify MCP server is receiving data from OTEL collector.
Tests the data flow: OTEL Collector -> Files -> MCP Server
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# Add mcp-server to path
sys.path.insert(0, str(Path(__file__).parent / "mcp-server"))

from telemetry_store import TelemetryStore
from file_watcher import TelemetryWatcher

def test_telemetry_files():
    """Check if telemetry files exist and have data."""
    telemetry_dir = Path(__file__).parent / "telemetry"
    
    print("=" * 60)
    print("Testing Telemetry Files")
    print("=" * 60)
    print(f"Telemetry directory: {telemetry_dir}")
    print(f"Directory exists: {telemetry_dir.exists()}")
    
    if not telemetry_dir.exists():
        print("❌ Telemetry directory does not exist!")
        return False
    
    # Check for telemetry files
    files = {
        "traces": list(telemetry_dir.glob("traces*.json*")),
        "logs": list(telemetry_dir.glob("logs*.json*")),
        "metrics": list(telemetry_dir.glob("metrics*.json*"))
    }
    
    print(f"\nFiles found:")
    for file_type, file_list in files.items():
        print(f"  {file_type}: {len(file_list)} files")
        for f in file_list:
            size = f.stat().st_size if f.exists() else 0
            print(f"    - {f.name} ({size} bytes)")
    
    # Check file contents
    has_data = False
    for file_type, file_list in files.items():
        for f in file_list:
            if f.exists() and f.stat().st_size > 0:
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        content = file.read()
                        lines = [l for l in content.strip().split('\n') if l.strip()]
                        print(f"\n  {f.name}: {len(lines)} lines")
                        if lines:
                            try:
                                sample = json.loads(lines[0])
                                print(f"    Sample keys: {list(sample.keys())}")
                                has_data = True
                            except json.JSONDecodeError:
                                print(f"    ⚠️  Invalid JSON in first line")
                except Exception as e:
                    print(f"    ❌ Error reading {f.name}: {e}")
    
    return has_data


def test_mcp_store():
    """Test the MCP server's telemetry store directly."""
    print("\n" + "=" * 60)
    print("Testing MCP Server Store")
    print("=" * 60)
    
    store = TelemetryStore()
    telemetry_dir = Path(__file__).parent / "telemetry"
    
    # Create watcher and load data
    watcher = TelemetryWatcher(store, telemetry_dir)
    watcher.start()
    
    # Wait a moment for file processing
    import time
    time.sleep(2)
    
    # Check store stats
    stats = store.get_stats()
    print(f"\nStore Statistics:")
    print(f"  Total spans: {stats['total_spans']}")
    print(f"  Total logs: {stats['total_logs']}")
    print(f"  Total metrics: {stats['total_metrics']}")
    print(f"  Services: {stats['services']}")
    
    # Test queries
    print(f"\nQuery Tests:")
    spans = store.get_recent_spans(limit=5)
    print(f"  Recent spans: {len(spans)}")
    if spans:
        print(f"    Sample: {spans[0].name} from {spans[0].service_name}")
    
    logs = store.get_recent_logs(limit=5)
    print(f"  Recent logs: {len(logs)}")
    if logs:
        print(f"    Sample: {logs[0].severity} from {logs[0].service_name}")
    
    metrics = store.get_recent_metrics(limit=5)
    print(f"  Recent metrics: {len(metrics)}")
    if metrics:
        print(f"    Sample: {metrics[0].name} = {metrics[0].value} from {metrics[0].service_name}")
    
    watcher.stop()
    
    return stats['total_spans'] > 0 or stats['total_logs'] > 0 or stats['total_metrics'] > 0


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("MCP Server - OTEL Collector Connection Test")
    print("=" * 60)
    print(f"Test time: {datetime.now().isoformat()}\n")
    
    # Test 1: Check telemetry files
    files_ok = test_telemetry_files()
    
    # Test 2: Test MCP store
    store_ok = test_mcp_store()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Telemetry files exist and have data: {'YES' if files_ok else 'NO'}")
    print(f"MCP store has data: {'YES' if store_ok else 'NO'}")
    
    if not files_ok:
        print("\nWARNING: No telemetry files found. Make sure:")
        print("  1. OTEL Collector is running (docker-compose up)")
        print("  2. Services are sending telemetry to collector")
        print("  3. Collector is configured to export to files")
    
    if not store_ok and files_ok:
        print("\nWARNING: Files exist but MCP store is empty. Check:")
        print("  1. File watcher is running")
        print("  2. File format matches expected OTEL JSON format")
        print("  3. Check debug logs for parsing errors")
    
    if files_ok and store_ok:
        print("\nSUCCESS: MCP server is successfully receiving data from OTEL collector!")
    
    return files_ok and store_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
