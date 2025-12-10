import os
import sys
from snmp.client import SNMPClient
from monitor.device_monitor import DeviceMonitor
from storage.database import Database
from alerts.notifier import Notifier
from utils.config import load_config

def main():
    # Load configuration
    config = load_config()

    # Initialize SNMP client
    snmp_client = SNMPClient(config['snmp'])

    # Initialize database
    database = Database(config['database'])

    # Initialize notifier
    notifier = Notifier(config['alerts'])

    # Initialize device monitor
    device_monitor = DeviceMonitor(snmp_client, database, notifier)

    # Start monitoring
    device_monitor.start_monitoring()

if __name__ == "__main__":
    main()