from puresnmp import get, bulkwalk

def snmpget0(ip, community, oid, coding="utf-8"):
    try:
        res = get(ip, community, oid)
        if type(res) == bytes or type(res) == int or type(res) == str:
            if type(res) == bytes:
                if coding == "utf-8":
                    ret = res.decode("utf-8", "ignore")
                else:
                    ret = res
            else:
                ret = res
        else:
            ret = repr(str(res))
        return ret
    except Exception as e:
        print("snmpget exception=", ip, oid, e)
        return None

def snmpwalk0(ip, community, oids, bulk_size=10, coding="utf-8"):
    try:
        res = bulkwalk(ip, community, oids=oids, bulk_size=bulk_size)
        values = {}
        for i in res:
            if type(i[1]) == bytes or type(i[1]) == int or type(i[1]) == str:
                if type(i[1]) == bytes:
                    if coding == "utf-8":
                        values[str(i[0])] = i[1].decode("utf-8", "ignore")
                    else:
                        values[str(i[0])] = i[1]
                else:
                    values[str(i[0])] = i[1]
            else:
                values[str(i[0])] = str(repr(str(i[1])))

        return values
    except Exception as e:
        print("snmpwalk exception=", ip, oids, e)
        return None


from function_snmp.snmpAgent_Test import snmpget, snmpwalk


if __name__ == '__main__':
    aa = snmpget0("192.168.57.10", "Mrtg.Netease", "1.3.6.1.2.1.1.5.0", "utf-8")
    print(aa)