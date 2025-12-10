import unittest
from src.monitor.device_monitor import DeviceMonitor
from src.monitor.metrics import Metrics

class TestDeviceMonitor(unittest.TestCase):
    def setUp(self):
        self.device_monitor = DeviceMonitor()

    def test_monitor_device(self):
        result = self.device_monitor.monitor_device("192.168.1.1")
        self.assertTrue(result)

    def test_get_metrics(self):
        metrics = self.device_monitor.get_metrics()
        self.assertIsInstance(metrics, Metrics)

if __name__ == '__main__':
    unittest.main()