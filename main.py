from monitor import SystemMonitor
from network import NetworkMonitor
from process_monitor import ProcessMonitor
from detector import EventDetector
from logger import AppLogger
from alert import AlertManager
from ui import SystemHealthUI


def main():
    monitor = SystemMonitor(interval_seconds=1.0)
    network_monitor = NetworkMonitor(target_host='8.8.8.8', interval_seconds=3.0)
    process_monitor = ProcessMonitor(interval_seconds=1.0)
    detector = EventDetector(sustained_seconds=10)
    logger = AppLogger(path='system_health_logs.jsonl')
    alerter = AlertManager()
    ui = SystemHealthUI(monitor, network_monitor, process_monitor, detector, logger, alerter, refresh_ms=1000)

    monitor.start()
    network_monitor.start()
    process_monitor.start()
    try:
        ui.start()
    finally:
        network_monitor.stop()
        process_monitor.stop()
        monitor.stop()


if __name__ == '__main__':
    main()
