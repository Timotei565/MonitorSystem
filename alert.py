import platform

try:
    import winsound
except ImportError:
    winsound = None


class AlertManager:
    def __init__(self):
        self._last_alert = None

    def notify(self, event):
        if not event or self._last_alert == (event.severity, event.message):
            return
        self._last_alert = (event.severity, event.message)
        self._play_sound(event.severity)

    def _play_sound(self, severity):
        if platform.system() == 'Windows' and winsound:
            frequency = 1200 if severity == 'CRITICAL' else 750
            duration = 400 if severity == 'CRITICAL' else 200
            winsound.Beep(frequency, duration)
        else:
            print('\a', end='', flush=True)

    def reset(self):
        self._last_alert = None
