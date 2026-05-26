# MonitorSystem — System Health Monitor (Python)

A small desktop application to monitor a Windows PC's health (CPU, RAM, disk, network, processes), detect threshold violations, log events, and show a simple multi-page GUI.

Why this exists
- Quick local tool to observe system resource usage and get lightweight alerts when resources become constrained.
- Built as a small, extensible Python project to experiment with monitoring, detection rules, and a responsive Tkinter UI.

Key features
- Continuous sampling of CPU, RAM and disk usage.
- Network latency checks (ping) and basic network status.
- Per-process CPU and memory usage, with a Memory page listing all processes sorted by RAM.
- Simple rule-based event detector (WARNING / CRITICAL) with audible alerts.
- JSONL logging of snapshots and detected events.
- Modular code: separate monitors, detector, logger, alert manager and UI.

How it works (high level)
- Three background monitors run in threads:
  - `SystemMonitor` samples CPU, RAM and disk.
  - `NetworkMonitor` pings a target host and measures latency.
  - `ProcessMonitor` enumerates processes and reports CPU/memory per-process.
- The main UI (`SystemHealthUI`) runs a Tkinter mainloop and calls an `_update_loop()` every second to merge the latest snapshots, run the `EventDetector`, log the snapshot, and update the GUI.

Quick start
1. Install Python 3.8+ and pip.
2. Install dependencies:

```powershell
pip install -r requirements.txt
```

If you don't have `requirements.txt`, install `psutil` directly:

```powershell
pip install psutil
```

3. Run the app:

```powershell
python main.py
```

Project layout (important files)
- `main.py` — application entrypoint (starts monitors and UI).
- `monitor.py` — system-level monitor (CPU/RAM/Disk).
- `network.py` — network ping monitor.
- `process_monitor.py` — per-process metrics and system memory snapshot.
- `detector.py` — rule-based event detection and status aggregation.
- `logger.py` — JSONL logging of snapshots and events.
- `alert.py` — audible alert manager.
- `ui.py` — Tkinter multi-page UI (Dashboard + Memory page).

Logs
- By default logs are written to `system_health_logs.jsonl` in the app folder (one JSON object per line). The logger stores both raw snapshot data and detected events.

Extending the project
- Add more detectors in `detector.py` (e.g., I/O, temperature metrics).
- Replace the `Listbox` memory view with `ttk.Treeview` for columns and sorting.
- Add persistence, remote reporting, or a web dashboard for centralized monitoring.

Notes and limitations
- Designed as a local desktop utility; not intended as an enterprise-grade monitoring solution.
- CPU temperature and some process details may be platform-dependent or require elevated privileges.

License & author
- This repository is a personal/project prototype. Check the repo for license details or add one if you intend to publish.
