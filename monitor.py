import datetime
import threading
import time

try:
    import psutil
except ImportError as exc:
    raise ImportError(
        "psutil is required for SystemMonitor. Install it with 'pip install psutil'."
    ) from exc


class SystemMonitor:
    def __init__(self, interval_seconds=1.0):
        self.interval_seconds = interval_seconds
        self._snapshot = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def latest(self):
        with self._lock:
            return dict(self._snapshot)

    def _run(self):
        self._take_snapshot()
        while not self._stop_event.wait(self.interval_seconds):
            self._take_snapshot()

    def _take_snapshot(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        ram_usage = psutil.virtual_memory().percent
        disk_usage = psutil.disk_usage('/').percent

        cpu_temp = None
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Prefer entries that mention CPU or core data
                    found = None
                    for key, entries in temps.items():
                        for entry in entries:
                            label = getattr(entry, 'label', '') or ''
                            key_name = key.lower() if isinstance(key, str) else ''
                            label_name = label.lower() if isinstance(label, str) else ''
                            if 'cpu' in key_name or 'core' in key_name or 'cpu' in label_name or 'core' in label_name:
                                found = entry
                                break
                        if found:
                            break
                    if found and getattr(found, 'current', None) is not None:
                        cpu_temp = float(found.current)
                    else:
                        for entries in temps.values():
                            for entry in entries:
                                if getattr(entry, 'current', None) is not None:
                                    cpu_temp = float(entry.current)
                                    break
                            if cpu_temp is not None:
                                break
        except Exception:
            cpu_temp = None

        snapshot = {
            'timestamp': datetime.datetime.now().isoformat(),
            'cpu': round(cpu_usage, 1),
            'ram': round(ram_usage, 1),
            'disk': round(disk_usage, 1),
            'cpu_temp': round(cpu_temp, 1) if cpu_temp is not None else None,
        }
        with self._lock:
            self._snapshot = snapshot
