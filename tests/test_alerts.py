import unittest
from network_monitor.alerts.notifier import Notifier

class TestAlerts(unittest.TestCase):

    def setUp(self):
        self.notifier = Notifier()

    def test_send_alert(self):
        result = self.notifier.send_alert("Test Alert", "This is a test alert.")
        self.assertTrue(result)

    def test_alert_format(self):
        alert = self.notifier.format_alert("Test Alert", "This is a test alert.")
        self.assertIn("Test Alert", alert)
        self.assertIn("This is a test alert.", alert)

if __name__ == '__main__':
    unittest.main()