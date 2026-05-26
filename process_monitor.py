import threading
import time
import datetime

try:
    import psutil
except ImportError as exc:
    raise ImportError("psutil is required for ProcessMonitor. Install with 'pip install psutil'.") from exc

import platform

# Optional: get active window title on Windows
if platform.system() == 'Windows':
    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        def _get_active_window_title():
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value

    except Exception:
        def _get_active_window_title():
            return None
else:
    def _get_active_window_title():
        return None


class ProcessMonitor:
    def __init__(self, interval_seconds=1.0):
        self.interval_seconds = interval_seconds
        self._snapshot = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        # Prime cpu_percent sampling for existing processes
        for p in psutil.process_iter(attrs=['pid']):
            try:
                p.cpu_percent(interval=None)
            except Exception:
                pass
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
        now = datetime.datetime.now().isoformat()
        procs = []
        cpu_count = psutil.cpu_count(logical=True) or 1
        # system memory snapshot
        try:
            vmem = psutil.virtual_memory()
            system_mem = {
                'total': getattr(vmem, 'total', None),
                'available': getattr(vmem, 'available', None),
                'used': getattr(vmem, 'used', None),
                'percent': getattr(vmem, 'percent', None),
            }
        except Exception:
            system_mem = {'total': None, 'available': None, 'used': None, 'percent': None}
        try:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    info = proc.info
                    name = (info.get('name') or '').strip()
                    # Ignore system idle processes from rankings
                    if name and 'idle' in name.lower():
                        continue
                    raw_cpu = proc.cpu_percent(interval=None)
                    cpu = raw_cpu / cpu_count
                    mem_pct = proc.memory_percent()
                    mem_bytes = None
                    try:
                        mem_info = proc.memory_info()
                        mem_bytes = getattr(mem_info, 'rss', None)
                    except Exception:
                        mem_bytes = None
                    procs.append({
                        'pid': info.get('pid'),
                        'name': name or 'unknown',
                        'cpu': round(cpu, 1),
                        'memory': round(mem_pct, 1),
                        'memory_bytes': mem_bytes,
                    })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception:
            procs = []

        procs_sorted_by_cpu = sorted(procs, key=lambda x: x.get('cpu', 0), reverse=True)
        procs_sorted_by_mem = sorted(procs, key=lambda x: x.get('memory', 0), reverse=True)

        top_cpu = procs_sorted_by_cpu[:5]
        top_mem = procs_sorted_by_mem[:5]
        top_process = top_cpu[0] if top_cpu else None

        active_window = _get_active_window_title()

        snapshot = {
            'processes': procs,
            'processes_top_cpu': top_cpu,
            'processes_top_mem': top_mem,
            'process_top': top_process,
            'system_memory': system_mem,
            'active_window': active_window,
            'process_timestamp': now,
        }
        with self._lock:
            self._snapshot = snapshot
