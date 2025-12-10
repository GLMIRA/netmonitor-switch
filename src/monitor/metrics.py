from datetime import datetime
import psutil

class Metrics:
    def __init__(self):
        self.cpu_usage = []
        self.memory_usage = []
        self.disk_usage = []

    def collect_cpu_usage(self):
        usage = psutil.cpu_percent(interval=1)
        self.cpu_usage.append((datetime.now(), usage))

    def collect_memory_usage(self):
        usage = psutil.virtual_memory().percent
        self.memory_usage.append((datetime.now(), usage))

    def collect_disk_usage(self):
        usage = psutil.disk_usage('/').percent
        self.disk_usage.append((datetime.now(), usage))

    def get_metrics(self):
        return {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'disk_usage': self.disk_usage
        }