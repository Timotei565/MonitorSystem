# MonitorSystem

A small desktop application to monitor a Windows PC's health, detect threshold violations, log events, and show a simple multi-page GUI.

Why this exists
- I wanted to build a small and useful application that could help me monitor my Pc, Mostly to warn me when something goes bad such as no wifi, or high temps(Many times my Pc has Overheated because I didn't notice) I will Keep on adding more features as they come to me or that i think would be cool or useful.

Key features
- Continuous sampling of CPU, RAM and disk usage.
- Network latency checks and basic network status.
- process CPU and memory usage, with a Memory page listing all processes sorted by RAM.
- Simple rule based event detector with audible alerts.
- JSONL logging of snapshots and detected events.
- Modular code: separate monitors, detector, logger, alert manager and UI.

How it works
- Three background monitors run in threads:
  - `SystemMonitor` samples CPU, RAM and disk.
  - `NetworkMonitor` pings a target host and measures latency.
  - `ProcessMonitor` enumerates processes and reports CPU memory per process.
- The main UI runs a Tkinter mainloop and calls an `_update_loop()` every second to merge the latest snapshots, run the `EventDetector`, log the snapshot, and update the GUI.

Quick start
Install Python 3.8+ and pip.

Install dependencies
pip install -r requirements.txt

If you don't have `requirements.txt`, install `psutil` directly:

pip install psutil

Run the app:
python main.py

Logs
- By default logs are written to `system_health_logs.jsonl` in the app folder. The logger stores both raw snapshot data and detected events.

Extending the project
- Add more detectors in `detector.py` (e.g., I/O, temperature metrics).
- Replace the `Listbox` memory view with `ttk.Treeview` for columns and sorting.
- Add persistence, remote reporting, or a web dashboard for centralized monitoring.

Notes and limitations
- Designed as a local desktop utility not intended as an enterprise grade monitoring solution.
- CPU temperature and some process details may be platformdependent or require elevated privileges.
