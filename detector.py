import datetime


class Event:
    def __init__(self, severity, message, metric, value, event_type=None, timestamp=None):
        self.severity = severity
        self.message = message
        self.metric = metric
        self.value = value
        self.event_type = event_type
        self.timestamp = timestamp or datetime.datetime.now().isoformat()

    def to_dict(self):
        return {
            'timestamp': self.timestamp,
            'severity': self.severity,
            'event_type': self.event_type,
            'message': self.message,
            'metric': self.metric,
            'value': self.value,
        }


class EventDetector:
    WARNING_THRESHOLDS = {'cpu': 85.0, 'ram': 85.0}
    CRITICAL_THRESHOLDS = {'cpu': 95.0, 'ram': 95.0}

    def __init__(self, sustained_seconds=10):
        self.sustained_seconds = sustained_seconds
        self._cpu_high_count = 0
        self._ram_high_count = 0
        self._network_bad_count = 0
        self._process_high_counts = {}

    def evaluate(self, snapshot):
        events = []
        if not snapshot:
            return 'OK', events

        cpu = snapshot.get('cpu', 0.0)
        ram = snapshot.get('ram', 0.0)
        latency = snapshot.get('network_latency')
        network_status = snapshot.get('network_status')

        cpu_severity = self._metric_severity(cpu, 'cpu')
        ram_severity = self._metric_severity(ram, 'ram')
        network_severity = self._network_severity(latency, network_status)

        if cpu_severity in ('WARNING', 'CRITICAL'):
            self._cpu_high_count += 1
        else:
            self._cpu_high_count = 0

        if ram_severity in ('WARNING', 'CRITICAL'):
            self._ram_high_count += 1
        else:
            self._ram_high_count = 0

        if network_severity in ('WARNING', 'CRITICAL'):
            self._network_bad_count += 1
        else:
            self._network_bad_count = 0

        status = self._combine_severity(cpu_severity, ram_severity, network_severity)
        reasons = []

        if cpu_severity == 'CRITICAL':
            events.append(
                Event('CRITICAL', f'CPU critical at {cpu}%', 'cpu', cpu, event_type='CPU_CRITICAL')
            )
            reasons.append(f'CPU critical: {cpu}%')
        elif cpu_severity == 'WARNING':
            if self._cpu_high_count >= self.sustained_seconds:
                events.append(
                    Event(
                        'CRITICAL',
                        f'Sustained high CPU for {self._cpu_high_count}s at {cpu}%',
                        'cpu',
                        cpu,
                        event_type='CPU_CRITICAL',
                    )
                )
                reasons.append(f'Sustained CPU high: {cpu}% for {self._cpu_high_count}s')
            else:
                events.append(
                    Event('WARNING', f'CPU high at {cpu}%', 'cpu', cpu, event_type='CPU_WARNING')
                )
                reasons.append(f'CPU high: {cpu}%')

        if ram_severity == 'CRITICAL':
            events.append(
                Event('CRITICAL', f'RAM critical at {ram}%', 'ram', ram, event_type='RAM_CRITICAL')
            )
            reasons.append(f'RAM critical: {ram}%')
        elif ram_severity == 'WARNING':
            if self._ram_high_count >= self.sustained_seconds:
                events.append(
                    Event(
                        'CRITICAL',
                        f'Sustained high RAM for {self._ram_high_count}s at {ram}%',
                        'ram',
                        ram,
                        event_type='RAM_CRITICAL',
                    )
                )
                reasons.append(f'Sustained RAM high: {ram}% for {self._ram_high_count}s')
            else:
                events.append(
                    Event('WARNING', f'RAM high at {ram}%', 'ram', ram, event_type='RAM_WARNING')
                )
                reasons.append(f'RAM high: {ram}%')

        if network_status is not None:
            if network_status == 'FAIL':
                events.append(
                    Event(
                        'CRITICAL',
                        f'Network down at {latency if latency is not None else "?"}ms',
                        'network',
                        latency,
                        event_type='NETWORK_DOWN_EVENT',
                    )
                )
                reasons.append('Network down')
            elif latency is not None and latency > 120.0:
                if self._network_bad_count >= 3:
                    events.append(
                        Event(
                            'CRITICAL',
                            f'Sustained unstable network for {self._network_bad_count}s at {latency}ms',
                            'network',
                            latency,
                            event_type='NETWORK_UNSTABLE_EVENT',
                        )
                    )
                    reasons.append(f'Sustained unstable network: {latency}ms')
                else:
                    events.append(
                        Event(
                            'CRITICAL',
                            f'Network unstable at {latency}ms',
                            'network',
                            latency,
                            event_type='NETWORK_UNSTABLE_EVENT',
                        )
                    )
                    reasons.append(f'Network unstable: {latency}ms')
            elif latency is not None and latency >= 50.0:
                events.append(
                    Event(
                        'WARNING',
                        f'Network slow at {latency}ms',
                        'network',
                        latency,
                        event_type='NETWORK_SLOW_EVENT',
                    )
                )
                reasons.append(f'Network slow: {latency}ms')

        # Process-level checks: look for processes consuming too much CPU
        processes = snapshot.get('processes_top_cpu') or []
        for p in processes:
            pid = p.get('pid')
            cpu_val = p.get('cpu', 0)
            key = f'pid_{pid}'
            proc_name = p.get('name') or 'unknown'
            if cpu_val >= 95.0:
                events.append(
                    Event('CRITICAL', f'Process {proc_name}({pid}) critical CPU {cpu_val}%', 'process', cpu_val, event_type='PROCESS_CRITICAL')
                )
                reasons.append(f'Process {proc_name} critical CPU: {cpu_val}%')
            elif cpu_val >= 80.0:
                self._process_high_counts[key] = self._process_high_counts.get(key, 0) + 1
                if self._process_high_counts[key] >= 10:
                    events.append(
                        Event('CRITICAL', f'Sustained high CPU by {proc_name}({pid}) {cpu_val}%', 'process', cpu_val, event_type='PROCESS_CRITICAL')
                    )
                    reasons.append(f'Sustained high process CPU: {proc_name} {cpu_val}%')
                else:
                    events.append(
                        Event('WARNING', f'Process {proc_name}({pid}) high CPU {cpu_val}%', 'process', cpu_val, event_type='PROCESS_HIGH_CPU')
                    )
                    reasons.append(f'Process {proc_name} high CPU: {cpu_val}%')
            else:
                if key in self._process_high_counts:
                    self._process_high_counts.pop(key, None)

        status_detail = '; '.join(reasons) if reasons else 'All measured metrics are within normal ranges.'
        return status, events, status_detail

    def _metric_severity(self, value, metric):
        if value >= self.CRITICAL_THRESHOLDS[metric]:
            return 'CRITICAL'
        if value >= self.WARNING_THRESHOLDS[metric]:
            return 'WARNING'
        return 'OK'

    def _network_severity(self, latency, network_status):
        if network_status == 'FAIL' or latency is None:
            return 'CRITICAL'
        if latency >= 120.0:
            return 'CRITICAL'
        if latency >= 50.0:
            return 'WARNING'
        return 'OK'

    def _combine_severity(self, cpu_severity, ram_severity, network_severity):
        if 'CRITICAL' in (cpu_severity, ram_severity, network_severity):
            return 'CRITICAL'
        if 'WARNING' in (cpu_severity, ram_severity, network_severity):
            return 'WARNING'
        return 'OK'
