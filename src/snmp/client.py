from pysnmp.hlapi import *

class SNMPClient:
    def __init__(self, host, community, version=2):
        self.host = host
        self.community = community
        self.version = version

    def get(self, oid):
        iterator = getCmd(SnmpEngine(),
                          CommunityData(self.community, mpModel=self.version - 1),
                          UdpTransportTarget((self.host, 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity(oid)))

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            raise Exception(f"Error: {errorIndication}")
        elif errorStatus:
            raise Exception(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")
        
        return varBinds

    def walk(self, oid):
        iterator = nextCmd(SnmpEngine(),
                           CommunityData(self.community, mpModel=self.version - 1),
                           UdpTransportTarget((self.host, 161)),
                           ContextData(),
                           ObjectType(ObjectIdentity(oid)),
                           lexicographicMode=False)

        results = []
        for errorIndication, errorStatus, errorIndex, varBinds in iterator:
            if errorIndication:
                raise Exception(f"Error: {errorIndication}")
            elif errorStatus:
                raise Exception(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")
            else:
                results.append(varBinds)

        return results
