import json
import time
from function_snmp.snmpData import oid_test_database

def snmpget(ip, community, oid, coding="utf-8"):
    try:
        # time.sleep(1)
        if oid in oid_test_database["get"].keys():
            return oid_test_database["get"][oid]
        else:
            print("OID {} not found".format(oid))
    except Exception as e:
        print("snmpget exception=", ip, oid, e)
        return None

def snmpwalk(ip, community, oids, bulk_size=10, coding="utf-8"):
    try:
        # time.sleep(2)
        if oids in oid_test_database["walk"].keys():
            result = {}
            for key, value in oid_test_database["walk"][oids].items():
                if value == "timeadd":
                    result["{}{}".format(oids, key)] = int(time.time())
                else:
                    result["{}{}".format(oids, key)] = value
            return result
        else:
            print("OID {} not found".format(oids))
            return None
    except Exception as e:
        print("snmpwalk exception=", ip, oids, e)
        return None


if __name__ == '__main__':
    aa = snmpwalk("10.162.0.14", "Mrtg.Netease","1.3.6.1.2.1.2.2.1.2")
    print(aa)