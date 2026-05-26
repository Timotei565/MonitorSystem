import tkinter as tk
from tkinter import ttk
from functools import partial


class SystemHealthUI:
    def __init__(self, monitor, network_monitor, process_monitor, detector, logger, alerter, refresh_ms=1000):
        self.monitor = monitor
        self.network_monitor = network_monitor
        self.process_monitor = process_monitor
        self.detector = detector
        self.logger = logger
        self.alerter = alerter
        self.refresh_ms = refresh_ms
        self._last_event_message = None

        self.root = tk.Tk()
        self.root.title('System Health Monitor')
        self.root.geometry('380x330')
        self.root.resizable(False, False)

        self.status_label = None
        self.status_detail_label = None
        self.cpu_value = None
        self.ram_value = None
        self.disk_value = None
        self.network_value = None
        self.network_status_label = None
        self.process_top_label = None
        self.process_top_list = None
        self.active_window_label = None
        self.event_message = None

        # build multi-frame interface
        self.frames = {}
        self._build_interface()
        self.show_frame('Dashboard')

    def _build_interface(self):
        container = ttk.Frame(self.root, padding=8)
        container.pack(expand=True, fill='both')

        # Navigation
        nav = ttk.Frame(container)
        nav.pack(fill='x', pady=(0,6))
        btn_dash = ttk.Button(nav, text='Dashboard', command=partial(self.show_frame, 'Dashboard'))
        btn_dash.pack(side='left', padx=4)
        btn_mem = ttk.Button(nav, text='Memory Usage', command=partial(self.show_frame, 'Memory'))
        btn_mem.pack(side='left', padx=4)

        # frame container
        self.main_area = ttk.Frame(container)
        self.main_area.pack(expand=True, fill='both')

        # Dashboard Frame
        dash = ttk.Frame(self.main_area)
        dash.pack(expand=True, fill='both')
        self.frames['Dashboard'] = dash

        self.status_label = ttk.Label(dash, text='Status: OK', font=('Segoe UI', 12, 'bold'))
        self.status_label.pack(fill='x', pady=(0, 6))

        self.status_detail_label = ttk.Label(dash, text='No issues detected.', font=('Segoe UI', 8), foreground='#333333', wraplength=340, justify='left')
        self.status_detail_label.pack(fill='x', pady=(0, 6))

        self.cpu_value = ttk.Label(dash, text='CPU: -- %', font=('Segoe UI', 10))
        self.cpu_value.pack(fill='x', pady=2)

        self.ram_value = ttk.Label(dash, text='RAM: -- %', font=('Segoe UI', 10))
        self.ram_value.pack(fill='x', pady=2)

        self.disk_value = ttk.Label(dash, text='Disk: -- %', font=('Segoe UI', 10))
        self.disk_value.pack(fill='x', pady=2)

        self.network_value = ttk.Label(dash, text='Ping: -- ms', font=('Segoe UI', 10))
        self.network_value.pack(fill='x', pady=2)

        self.network_status_label = ttk.Label(dash, text='Network: --', font=('Segoe UI', 10))
        self.network_status_label.pack(fill='x', pady=2)

        self.process_top_label = ttk.Label(dash, text='Top Process: --', font=('Segoe UI', 9, 'bold'))
        self.process_top_label.pack(fill='x', pady=(8, 2))

        self.process_top_list_label = ttk.Label(dash, text='Top 5 Processes:', font=('Segoe UI', 8, 'bold'))
        self.process_top_list_label.pack(fill='x', pady=(6, 0))

        self.process_top_list = ttk.Label(dash, text='No process data', font=('Segoe UI', 8), justify='left', wraplength=340)
        self.process_top_list.pack(fill='x', pady=2)

        self.active_window_label = ttk.Label(dash, text='Active window: --', font=('Segoe UI', 8))
        self.active_window_label.pack(fill='x', pady=2)

        separator = ttk.Separator(dash, orient='horizontal')
        separator.pack(fill='x', pady=8)

        self.event_message = ttk.Label(
            dash,
            text='No alerts yet.',
            font=('Segoe UI', 9),
            wraplength=340,
            background='#f5f5f5',
            anchor='w',
            justify='left',
            padding=6,
        )
        self.event_message.pack(fill='x')

        # Memory Frame
        mem = ttk.Frame(self.main_area)
        self.frames['Memory'] = mem

        self.mem_total_label = ttk.Label(mem, text='Total RAM: --', font=('Segoe UI', 11, 'bold'))
        self.mem_total_label.pack(fill='x', pady=(6,4))

        self.mem_list_label = ttk.Label(mem, text='Processes by memory (all):', font=('Segoe UI', 9, 'bold'))
        self.mem_list_label.pack(fill='x', pady=(6,0))

        # listbox with scrollbar to show all processes
        mem_list_frame = ttk.Frame(mem)
        mem_list_frame.pack(expand=True, fill='both', pady=6)

        self.mem_list = tk.Listbox(mem_list_frame, height=14, font=('Segoe UI', 9))
        self.mem_list.pack(side='left', expand=True, fill='both')

        self.mem_scroll = ttk.Scrollbar(mem_list_frame, orient='vertical', command=self.mem_list.yview)
        self.mem_scroll.pack(side='right', fill='y')
        self.mem_list.config(yscrollcommand=self.mem_scroll.set)

    def start(self):
        self.root.protocol('WM_DELETE_WINDOW', self.close)
        self._update_loop()
        self.root.mainloop()

    def close(self):
        self.root.quit()

    def _update_loop(self):
        snapshot = {**self.monitor.latest(), **self.network_monitor.latest(), **self.process_monitor.latest()}
        status, events, details = self.detector.evaluate(snapshot)
        self.logger.log(snapshot, events)

        self._render(snapshot, status, details, events)

        if events:
            latest_event = events[-1]
            self.alerter.notify(latest_event)

        self.root.after(self.refresh_ms, self._update_loop)

    def show_frame(self, name):
        # hide all
        for f in self.frames.values():
            f.pack_forget()
        # show requested
        frame = self.frames.get(name)
        if frame:
            frame.pack(expand=True, fill='both')

    def _render(self, snapshot, status, details, events):
        cpu = snapshot.get('cpu', '--')
        ram = snapshot.get('ram', '--')
        disk = snapshot.get('disk', '--')
        ping = snapshot.get('network_latency', '--')
        network_status = snapshot.get('network_status', '--')
        proc_top = snapshot.get('process_top')
        proc_list = snapshot.get('processes_top_cpu') or []
        active_win = snapshot.get('active_window')

        self.status_label.config(text=f'Status: {status}')
        self.status_detail_label.config(text=details)
        self.cpu_value.config(text=f'CPU: {cpu} %')
        self.ram_value.config(text=f'RAM: {ram} %')
        self.disk_value.config(text=f'Disk: {disk} %')
        self.network_value.config(text=f'Ping: {ping if ping is not None else "--"} ms')
        self.network_status_label.config(text=f'Network: {network_status}')
        if proc_top:
            name = proc_top.get('name') or 'unknown'
            cpu = proc_top.get('cpu')
            self.process_top_label.config(text=f'Top Process: {name} ({cpu}%)')
        else:
            self.process_top_label.config(text='Top Process: --')

        if proc_list:
            lines = []
            for p in proc_list:
                lines.append(f"{p.get('name')} (pid:{p.get('pid')}) CPU:{p.get('cpu')}% MEM:{p.get('memory')}%")
            self.process_top_list.config(text='\n'.join(lines))
        else:
            self.process_top_list.config(text='No process data')

        self.active_window_label.config(text=f'Active window: {active_win or "--"}')

        if status == 'CRITICAL':
            self.status_label.config(foreground='red')
            self.event_message.config(background='#ffe5e5')
        elif status == 'WARNING':
            self.status_label.config(foreground='orange')
            self.event_message.config(background='#fff5d4')
        else:
            self.status_label.config(foreground='green')
            self.event_message.config(background='#f5fff5')

        if network_status == 'OK':
            self.network_status_label.config(foreground='green')
        elif network_status == 'SLOW':
            self.network_status_label.config(foreground='orange')
        else:
            self.network_status_label.config(foreground='red')

        if events:
            latest_event = events[-1]
            message = f"{latest_event.severity}: {latest_event.message}"
            self.event_message.config(text=message)
            self._last_event_message = message
        else:
            self.event_message.config(text=details)

        # Update memory frame list when visible
        mem_snapshot = snapshot.get('system_memory') or {}
        total = mem_snapshot.get('total')
        if total:
            # convert to human readable
            gb = total / (1024 ** 3)
            self.mem_total_label.config(text=f"Total RAM: {gb:.1f} GB ({mem_snapshot.get('percent')}%)")
        else:
            self.mem_total_label.config(text='Total RAM: --')

        # update mem listbox with all processes sorted by memory usage
        procs = snapshot.get('processes') or []
        try:
            # sort by memory_bytes if present, otherwise by memory percent
            def _mem_key(x):
                b = x.get('memory_bytes')
                if b is None:
                    return x.get('memory', 0)
                return b

            procs_sorted = sorted(procs, key=_mem_key, reverse=True)

            self.mem_list.delete(0, tk.END)
            for p in procs_sorted:
                name = p.get('name')
                pid = p.get('pid')
                mem_bytes = p.get('memory_bytes')
                mem_pct = p.get('memory')
                if mem_bytes:
                    if mem_bytes > 1024 ** 3:
                        human = f"{mem_bytes / (1024 ** 3):.2f} GB"
                    else:
                        human = f"{mem_bytes / (1024 ** 2):.1f} MB"
                    line = f"{name} (pid:{pid}) — {human} ({mem_pct}%)"
                else:
                    line = f"{name} (pid:{pid}) — {mem_pct}%"
                self.mem_list.insert(tk.END, line)
        except Exception:
            pass
