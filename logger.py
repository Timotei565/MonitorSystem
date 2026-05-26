import datetime
import json
import os


class AppLogger:
    def __init__(self, path='system_health_logs.jsonl'):
        self.path = path
        self._ensure_log_file()

    def _ensure_log_file(self):
        folder = os.path.dirname(self.path)
        if folder and not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
        if not os.path.exists(self.path):
            with open(self.path, 'w', encoding='utf-8'):
                pass

    def log(self, snapshot, events=None):
        if not snapshot:
            return
        entry = {
            'timestamp': snapshot.get('timestamp', datetime.datetime.now().isoformat()),
            'cpu': snapshot.get('cpu'),
            'cpu_temp': snapshot.get('cpu_temp'),
            'ram': snapshot.get('ram'),
            'disk': snapshot.get('disk'),
            'process_top': snapshot.get('process_top'),
            'processes_top_cpu': snapshot.get('processes_top_cpu'),
            'processes_top_mem': snapshot.get('processes_top_mem'),
            'network_latency': snapshot.get('network_latency'),
            'network_status': snapshot.get('network_status'),
            'network_packet_loss': snapshot.get('network_packet_loss'),
            'events': [event.to_dict() for event in events] if events else [],
        }
        with open(self.path, 'a', encoding='utf-8') as handle:
            handle.write(json.dumps(entry) + '\n')
