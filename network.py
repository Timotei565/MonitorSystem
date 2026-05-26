import datetime
import platform
import re
import subprocess
import threading
import time


class NetworkMonitor:
    def __init__(self, target_host='8.8.8.8', interval_seconds=3.0, timeout_seconds=2.0):
        self.target_host = target_host
        self.interval_seconds = interval_seconds
        self.timeout_seconds = timeout_seconds
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
        timestamp = datetime.datetime.now().isoformat()
        latency = None
        packet_loss = False
        status = 'FAIL'

        ping_command = self._build_ping_command()
        try:
            result = subprocess.run(
                ping_command,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds + 1,
            )
            output = result.stdout + result.stderr
            latency = self._parse_latency(output)
            if result.returncode != 0 or latency is None:
                packet_loss = True

        except (subprocess.TimeoutExpired, OSError):
            packet_loss = True
            latency = None

        if packet_loss:
            status = 'FAIL'
        elif latency >= 120.0:
            status = 'FAIL'
        elif latency >= 50.0:
            status = 'SLOW'
        else:
            status = 'OK'

        snapshot = {
            'network_timestamp': timestamp,
            'network_target': self.target_host,
            'network_latency': round(latency, 1) if latency is not None else None,
            'network_packet_loss': packet_loss,
            'network_status': status,
        }
        with self._lock:
            self._snapshot = snapshot

    def _build_ping_command(self):
        if platform.system() == 'Windows':
            return ['ping', '-n', '1', '-w', str(int(self.timeout_seconds * 1000)), self.target_host]
        return ['ping', '-c', '1', '-W', str(int(self.timeout_seconds)), self.target_host]

    def _parse_latency(self, output):
        if not output:
            return None
        match = re.search(r'time[=<]\s*([0-9]+\.?[0-9]*)\s*ms', output)
        if match:
            return float(match.group(1))
        match = re.search(r'Average\s*=\s*([0-9]+)ms', output)
        if match:
            return float(match.group(1))
        return None
