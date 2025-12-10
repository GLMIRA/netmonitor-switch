from pysnmp.hlapi import *

class DeviceMonitor:
    def __init__(self, target, community):
        self.target = target
        self.community = community

    def get_device_info(self, oid):
        iterator = getCmd(SnmpEngine(),
                          CommunityData(self.community),
                          UdpTransportTarget((self.target, 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity(oid)))

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            print(f"Error: {errorIndication}")
            return None
        elif errorStatus:
            print(f"Error: {errorStatus.prettyPrint()}")
            return None
        else:
            for varBind in varBinds:
                return varBind.prettyPrint()

    def monitor_device(self):
        # Example OIDs for monitoring
        oids = {
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysDescr': '1.3.6.1.2.1.1.1.0'
        }

        device_info = {}
        for name, oid in oids.items():
            device_info[name] = self.get_device_info(oid)

        return device_info