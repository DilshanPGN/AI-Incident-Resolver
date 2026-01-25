"""
File watcher for OpenTelemetry JSON exports.
Watches the telemetry directory and parses new data into the TelemetryStore.
"""

import json
import os
import threading
import time
from pathlib import Path
from typing import Callable, Optional, Union
from datetime import datetime

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileModifiedEvent, FileCreatedEvent

from telemetry_store import (
    TelemetryStore,
    parse_span_from_otel,
    parse_log_from_otel,
    parse_metric_from_otel,
)

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


class TelemetryFileHandler(FileSystemEventHandler):
    """Handles file events for telemetry JSON files."""
    
    def __init__(self, store: TelemetryStore):
        super().__init__()
        self.store = store
        self._file_positions: dict[str, int] = {}
        self._lock = threading.Lock()
    
    def on_created(self, event):
        # #region agent log
        _debug_log("file_watcher.py:on_created", "File created event", {"path": event.src_path, "is_directory": event.is_directory})
        # #endregion
        if event.is_directory:
            return
        self._process_file(event.src_path)
    
    def on_modified(self, event):
        # #region agent log
        _debug_log("file_watcher.py:on_modified", "File modified event", {"path": event.src_path, "is_directory": event.is_directory})
        # #endregion
        if event.is_directory:
            return
        self._process_file(event.src_path)
    
    def _process_file(self, file_path: str):
        """Process a telemetry file, reading only new content."""
        path = Path(file_path)
        
        # #region agent log
        _debug_log("file_watcher.py:_process_file", "Processing file", {"path": str(path), "suffix": path.suffix, "exists": path.exists()})
        # #endregion
        
        # Only process .json or .jsonl files
        if path.suffix not in ('.json', '.jsonl'):
            # #region agent log
            _debug_log("file_watcher.py:_process_file", "Skipping file - wrong suffix", {"path": str(path), "suffix": path.suffix})
            # #endregion
            return
        
        try:
            with self._lock:
                # Get last read position
                last_pos = self._file_positions.get(file_path, 0)
                
                # #region agent log
                _debug_log("file_watcher.py:_process_file", "Reading file", {"path": str(path), "last_pos": last_pos, "file_size": path.stat().st_size if path.exists() else 0})
                # #endregion
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    # Seek to last position
                    f.seek(last_pos)
                    
                    # Read new content
                    new_content = f.read()
                    
                    # Update position
                    self._file_positions[file_path] = f.tell()
                
                # #region agent log
                _debug_log("file_watcher.py:_process_file", "Read content", {"path": str(path), "content_length": len(new_content), "new_position": self._file_positions[file_path]})
                # #endregion
                
                if not new_content.strip():
                    # #region agent log
                    _debug_log("file_watcher.py:_process_file", "No new content", {"path": str(path)})
                    # #endregion
                    return
                
                # Determine file type from name
                file_name = path.stem.lower()
                
                # #region agent log
                _debug_log("file_watcher.py:_process_file", "Parsing content", {"path": str(path), "file_name": file_name, "line_count": len(new_content.strip().split('\n'))})
                # #endregion
                
                # Process each line (JSONL format)
                lines_processed = 0
                for line in new_content.strip().split('\n'):
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        lines_processed += 1
                        self._parse_and_store(data, file_name)
                    except json.JSONDecodeError:
                        # Try to parse as complete JSON object
                        try:
                            data = json.loads(new_content)
                            lines_processed += 1
                            self._parse_and_store(data, file_name)
                            break  # Entire content was one JSON object
                        except json.JSONDecodeError:
                            # #region agent log
                            _debug_log("file_watcher.py:_process_file", "JSON parse error", {"path": str(path), "line_preview": line[:100]})
                            # #endregion
                            pass
                
                # #region agent log
                _debug_log("file_watcher.py:_process_file", "File processing complete", {"path": str(path), "lines_processed": lines_processed})
                # #endregion
                            
        except Exception as e:
            # #region agent log
            _debug_log("file_watcher.py:_process_file", "Error processing file", {"path": str(path), "error": str(e)})
            # #endregion
            print(f"Error processing file {file_path}: {e}")
    
    def _parse_and_store(self, data: dict, file_type_hint: str):
        """Parse OTEL data and store in appropriate collection."""
        # #region agent log
        _debug_log("file_watcher.py:_parse_and_store", "Parsing data", {"file_type_hint": file_type_hint, "data_keys": list(data.keys())})
        # #endregion
        
        spans_added = 0
        logs_added = 0
        metrics_added = 0
        
        # Try to determine data type from content or file name
        if 'resourceSpans' in data:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Found resourceSpans", {"count": len(data.get('resourceSpans', []))})
            # #endregion
            for resource_span in data.get('resourceSpans', []):
                spans = parse_span_from_otel(resource_span)
                if spans:
                    for span in spans:
                        self.store.add_span(span)
                        spans_added += 1
        
        elif 'resourceLogs' in data:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Found resourceLogs", {"count": len(data.get('resourceLogs', []))})
            # #endregion
            for resource_log in data.get('resourceLogs', []):
                logs = parse_log_from_otel(resource_log)
                if logs:
                    for log in logs:
                        self.store.add_log(log)
                        logs_added += 1
        
        elif 'resourceMetrics' in data:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Found resourceMetrics", {"count": len(data.get('resourceMetrics', []))})
            # #endregion
            for resource_metric in data.get('resourceMetrics', []):
                metrics = parse_metric_from_otel(resource_metric)
                if metrics:
                    for metric in metrics:
                        self.store.add_metric(metric)
                        metrics_added += 1
        
        # Also try based on file name hint
        elif 'trace' in file_type_hint or 'span' in file_type_hint:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Trying trace parsing from file hint", {})
            # #endregion
            spans = parse_span_from_otel(data)
            if spans:
                for span in spans:
                    self.store.add_span(span)
                    spans_added += 1
        
        elif 'log' in file_type_hint:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Trying log parsing from file hint", {})
            # #endregion
            logs = parse_log_from_otel(data)
            if logs:
                for log in logs:
                    self.store.add_log(log)
                    logs_added += 1
        
        elif 'metric' in file_type_hint:
            # #region agent log
            _debug_log("file_watcher.py:_parse_and_store", "Trying metric parsing from file hint", {})
            # #endregion
            metrics = parse_metric_from_otel(data)
            if metrics:
                for metric in metrics:
                    self.store.add_metric(metric)
                    metrics_added += 1
        
        # #region agent log
        _debug_log("file_watcher.py:_parse_and_store", "Parse and store complete", {"spans_added": spans_added, "logs_added": logs_added, "metrics_added": metrics_added})
        # #endregion


class TelemetryWatcher:
    """
    Watches a directory for OTEL telemetry files and loads them into the store.
    """
    
    def __init__(self, store: TelemetryStore, watch_path: Union[str, Path]):
        self.store = store
        self.watch_path = Path(watch_path)
        self._observer: Optional[Observer] = None
        self._handler: Optional[TelemetryFileHandler] = None
        self._running = False
    
    def start(self):
        """Start watching the telemetry directory."""
        if self._running:
            return
        
        # #region agent log
        _debug_log("file_watcher.py:start", "Starting watcher", {"watch_path": str(self.watch_path), "path_exists": self.watch_path.exists()})
        # #endregion
        
        # Create directory if it doesn't exist
        self.watch_path.mkdir(parents=True, exist_ok=True)
        
        # #region agent log
        _debug_log("file_watcher.py:start", "Directory created/verified", {"watch_path": str(self.watch_path), "path_exists": self.watch_path.exists()})
        # #endregion
        
        # Load existing files first
        self._load_existing_files()
        
        # Set up file watcher
        self._handler = TelemetryFileHandler(self.store)
        self._observer = Observer()
        self._observer.schedule(self._handler, str(self.watch_path), recursive=False)
        self._observer.start()
        self._running = True
        
        # #region agent log
        _debug_log("file_watcher.py:start", "Watcher started", {"watch_path": str(self.watch_path), "is_running": self._running})
        # #endregion
        
        print(f"Started watching telemetry directory: {self.watch_path}")
    
    def stop(self):
        """Stop watching the telemetry directory."""
        if self._observer:
            self._observer.stop()
            self._observer.join()
            self._observer = None
        self._running = False
        print("Stopped telemetry watcher")
    
    def _load_existing_files(self):
        """Load any existing telemetry files on startup."""
        # #region agent log
        _debug_log("file_watcher.py:_load_existing_files", "Loading existing files", {"watch_path": str(self.watch_path), "exists": self.watch_path.exists()})
        # #endregion
        
        if not self.watch_path.exists():
            # #region agent log
            _debug_log("file_watcher.py:_load_existing_files", "Watch path does not exist", {"watch_path": str(self.watch_path)})
            # #endregion
            return
        
        files_found = list(self.watch_path.glob('*.json*'))
        # #region agent log
        _debug_log("file_watcher.py:_load_existing_files", "Found files", {"count": len(files_found), "files": [str(f) for f in files_found]})
        # #endregion
        
        for file_path in files_found:
            try:
                # #region agent log
                _debug_log("file_watcher.py:_load_existing_files", "Loading file", {"file_path": str(file_path), "size": file_path.stat().st_size})
                # #endregion
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                file_name = file_path.stem.lower()
                lines_loaded = 0
                
                for line in content.strip().split('\n'):
                    if not line.strip():
                        continue
                    try:
                        data = json.loads(line)
                        lines_loaded += 1
                        self._parse_and_store_data(data, file_name)
                    except json.JSONDecodeError:
                        # #region agent log
                        _debug_log("file_watcher.py:_load_existing_files", "JSON parse error in line", {"file_path": str(file_path), "line_preview": line[:100]})
                        # #endregion
                        pass
                
                # #region agent log
                _debug_log("file_watcher.py:_load_existing_files", "File loaded", {"file_path": str(file_path), "lines_loaded": lines_loaded, "content_length": len(content)})
                # #endregion
                
                # Update file position for handler
                if self._handler:
                    self._handler._file_positions[str(file_path)] = len(content)
                    
            except Exception as e:
                # #region agent log
                _debug_log("file_watcher.py:_load_existing_files", "Error loading file", {"file_path": str(file_path), "error": str(e)})
                # #endregion
                print(f"Error loading existing file {file_path}: {e}")
    
    def _parse_and_store_data(self, data: dict, file_type_hint: str):
        """Parse and store data (reuses handler logic)."""
        if self._handler:
            self._handler._parse_and_store(data, file_type_hint)
        else:
            # Fallback if handler not yet created
            handler = TelemetryFileHandler(self.store)
            handler._parse_and_store(data, file_type_hint)
    
    @property
    def is_running(self) -> bool:
        return self._running


if __name__ == "__main__":
    # Quick test
    store = TelemetryStore()
    watcher = TelemetryWatcher(store, "./telemetry")
    
    try:
        watcher.start()
        print("Watcher running. Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
            stats = store.get_stats()
            print(f"Stats: {stats}")
    except KeyboardInterrupt:
        watcher.stop()
