from pysnmp.hlapi import *

class SNMPParser:
    def __init__(self, target, community):
        self.target = target
        self.community = community

    def get_oid(self, oid):
        iterator = getCmd(SnmpEngine(),
                          CommunityData(self.community),
                          UdpTransportTarget((self.target, 161)),
                          ContextData(),
                          ObjectType(ObjectIdentity(oid)))

        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)

        if errorIndication:
            raise Exception(f"Error: {errorIndication}")
        elif errorStatus:
            raise Exception(f"Error: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")

        return varBinds

    def parse_response(self, varBinds):
        parsed_data = {}
        for varBind in varBinds:
            parsed_data[str(varBind[0])] = str(varBind[1])
        return parsed_data