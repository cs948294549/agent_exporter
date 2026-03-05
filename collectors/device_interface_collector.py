"""
设备接口属性采集模块

负责通过SNMP协议采集网络设备的接口相关属性信息，分为三个独立的采集内容：
1. 接口基础信息
2. 接口指标信息
3. 接口状态信息
"""
import logging
import time
from typing import Dict, List, Any, Optional
from function_snmp.snmp_collector import snmp_get, snmp_walk
from collectors.collector_cache_manager import get_cache_manager

logger = logging.getLogger(__name__)

# 获取缓存管理器实例，用于存储每个设备每个接口的上一次采集值和时间戳
CACHE_MANAGER = get_cache_manager()

# 定义常用的SNMP OID前缀
INTERFACE_OIDS = {
    # 基础信息相关OID
    'ifName': '1.3.6.1.2.1.2.2.1.2',           # 接口描述
    'ifMtu': '1.3.6.1.2.1.2.2.1.4',             # 接口MTU
    'ifPhysAddress': '1.3.6.1.2.1.2.2.1.6',     # 物理地址(MAC)
    'ifAdminStatus': '1.3.6.1.2.1.2.2.1.7',     # 管理状态
    'ifOperStatus': '1.3.6.1.2.1.2.2.1.8',      # 操作状态(物理状态)
    'ifAlias': '1.3.6.1.2.1.31.1.1.1.18',       # 接口别名
    'ifHighSpeed': '1.3.6.1.2.1.31.1.1.1.15',   # 接口高速率

    # 指标信息相关OID
    'ifHCInOctets': '1.3.6.1.2.1.31.1.1.1.6',        # 64位入站字节数
    'ifHCOutOctets': '1.3.6.1.2.1.31.1.1.1.10',      # 64位出站字节数
    'ifHCInUcastPkts': '1.3.6.1.2.1.31.1.1.1.7',     # 64位入站单播包数
    'ifHCOutUcastPkts': '1.3.6.1.2.1.31.1.1.1.11',   # 64位出站单播包数
    'ifHCInBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.9',  # 64位入站广播包数
    'ifHCInMulticastPkts': '1.3.6.1.2.1.31.1.1.1.8',  # 64位入站多播包数
    'ifHCOutBroadcastPkts': '1.3.6.1.2.1.31.1.1.1.13', # 64位出站广播包数
    'ifHCOutMulticastPkts': '1.3.6.1.2.1.31.1.1.1.12', # 64位出站多播包数
    'ifInErrors': '1.3.6.1.2.1.2.2.1.14',            # 入站错误包数
    'ifOutErrors': '1.3.6.1.2.1.2.2.1.20',           # 出站错误包数
    'ifInDiscards': '1.3.6.1.2.1.2.2.1.13',          # 入站丢弃包数
    'ifOutDiscards': '1.3.6.1.2.1.2.2.1.19',         # 出站丢弃包数
}

# ====================== 接口基础信息采集 ======================
def collect_interface_basic_info(ip: str, community: str="public") -> Dict[str, Any]:
    """
    采集设备接口基础信息
    
    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        
    Returns:
        List[Dict[str, Any]]: 接口基础信息列表，每个接口包含：
            - id: 接口索引
            - name: 接口名称
            - description: 接口描述
            - bandwidth: 接口带宽
            - mtu: 接口MTU值
            - mac_address: 接口MAC地址
            - admin_status: 管理状态
            - oper_status: 物理状态
    """
    try:
        logger.info(f"开始采集设备 {ip} 的接口基础信息")

        # 采集必要的基础信息
        results = {
            'ifName': snmp_walk(ip, community, INTERFACE_OIDS['ifName'], ttl=300),
            'speed': snmp_walk(ip, community, INTERFACE_OIDS['ifHighSpeed'], ttl=300),
            'mtu': snmp_walk(ip, community, INTERFACE_OIDS['ifMtu'], ttl=300),
            'mac_address': snmp_walk(ip, community, INTERFACE_OIDS['ifPhysAddress'], ttl=300),
            'admin_status': snmp_walk(ip, community, INTERFACE_OIDS['ifAdminStatus'], ttl=30),
            'oper_status': snmp_walk(ip, community, INTERFACE_OIDS['ifOperStatus'], ttl=30),
            "alias": snmp_walk(ip, community, INTERFACE_OIDS['ifAlias'], ttl=300),
        }

        # 获取接口索引列表
        if not results['ifName']:
            logger.warning(f"未获取到设备 {ip} 的接口信息")
            return []

        interfaces_dict = {}
        for item in results['ifName']:
            interface_id = item["index"]
            interfaces_dict[interface_id] = {
                "id": interface_id,
                "ifName": item["value"],
                "speed": "",
                "mtu": "",
                "mac_address": "",
                "admin_status": "",
                "oper_status": "",
                "alias": ""
            }

        # 填充其他信息
        for key in results.keys():
            if key == "ifName":
                continue
            
            for item in results[key]:
                interface_id = item["index"]
                if interface_id in interfaces_dict:
                    interfaces_dict[interface_id][key] = item["value"]
        interfaces = list(interfaces_dict.values())
        logger.info(f"成功采集设备 {ip} 的 {len(interfaces)} 个接口基础信息")
        return {
            "ip": ip,
            "metric_name": "interface_base",
            "status": "ok",
            "message": "采集成功",
            "timestamp": time.time(),
            "data":interfaces
        }
    except Exception as e:
        logger.error(f"采集设备 {ip} 接口基础信息时出错: {str(e)}", exc_info=True)
        return {
            "ip": ip,
            "metric_name": "interface_base",
            "status": "error",
            "message": str(e),
            "timestamp": time.time(),
            "data": []
        }


# ====================== 接口状态信息采集 ======================
def collect_interface_status(ip: str, community: str="public") -> Dict[str, Any]:
    """
    采集设备接口状态信息

    Args:
        ip: 设备IP地址
        community: SNMP团体字符串

    Returns:
        List[Dict[str, Any]]: 接口状态信息列表
    """
    try:
        logger.info(f"开始采集设备 {ip} 的接口状态信息")
        # 采集接口状态相关信息
        admin_status_result = snmp_walk(ip, community, INTERFACE_OIDS['ifAdminStatus'], ttl=30)
        oper_status_result = snmp_walk(ip, community, INTERFACE_OIDS['ifOperStatus'], ttl=30)

        # 创建接口ID到状态信息的映射
        admin_status_map = {}
        for item in admin_status_result:
            admin_status_map[item['index']] = item['value']

        oper_status_map = {}
        for item in oper_status_result:
            oper_status_map[item['index']] = item['value']

        # 获取所有接口ID
        all_interface_ids = set(admin_status_map.keys())
        all_interface_ids.update(oper_status_map.keys())

        # 构建状态信息列表
        status_list = []
        for interface_id in all_interface_ids:
            status_info = {
                'id': interface_id,
                'admin_status': admin_status_map.get(interface_id, 2),  # 默认down
                'oper_status': oper_status_map.get(interface_id, 2)  # 默认down
            }
            status_list.append(status_info)

        logger.info(f"成功采集设备 {ip} 的 {len(status_list)} 个接口状态信息")
        return {
            "ip": ip,
            "metric_name": "interface_status",
            "status": "ok",
            "message": "采集成功",
            "timestamp": int(time.time()),
            "data": status_list
        }
    except Exception as e:
        logger.error(f"采集设备 {ip} 接口状态信息时出错: {str(e)}", exc_info=True)
        return {
            "ip": ip,
            "metric_name": "interface_status",
            "status": "error",
            "message": str(e),
            "timestamp": int(time.time()),
            "data": []
        }

# ====================== 接口指标信息采集 ======================
# 使用策略模式实现接口指标采集

# 定义采集策略的抽象基类
class InterfaceMetricStrategy:
    """
    接口指标采集策略的抽象基类
    """
    def __init__(self, metric_name: str, in_oid: str, out_oid: str, bit_width: int = 64):
        self.metric_name = metric_name
        self.in_oid = in_oid
        self.out_oid = out_oid
        # 验证bit_width参数
        if bit_width not in [32, 64]:
            raise ValueError("bit_width must be either 32 or 64")
        self.bit_width = bit_width
        self.max_value = 2 ** bit_width
    
    def collect_raw_data(self, ip: str, community: str) -> List[Dict[str, Any]]:
        """
        采集原始的指标数据
        
        Args:
            ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            List[Dict[str, Any]]: 原始指标数据，格式为 [{id: interface_id, in: in_value, out: out_value}]
        """
        try:
            # 获取入站和出站指标数据
            in_result = snmp_walk(ip, community, self.in_oid, ttl=0)
            out_result = snmp_walk(ip, community, self.out_oid, ttl=0)
            
            # 构建映射
            in_map = {}
            for item in in_result:
                if isinstance(item, dict) and 'index' in item and 'value' in item:
                    in_map[str(item['index'])] = item['value']
            
            out_map = {}
            for item in out_result:
                if isinstance(item, dict) and 'index' in item and 'value' in item:
                    out_map[str(item['index'])] = item['value']
            
            # 获取所有接口ID
            all_interface_ids = set(in_map.keys())
            all_interface_ids.update(out_map.keys())
            
            # 转换为[{id, in, out}]格式
            result = []
            for interface_id in all_interface_ids:
                result.append({
                    'id': interface_id,
                    'in': in_map.get(interface_id, 0),
                    'out': out_map.get(interface_id, 0)
                })
            return result
        except Exception as e:
            logger.error(f"采集{self.metric_name}原始数据时出错: {str(e)}")
            return []
    
    def calculate_rates(self, device_ip: str, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        计算指标速率
        
        Args:
            device_ip: 设备IP地址
            raw_data: 原始指标数据，格式为 [{id: interface_id, in: in_value, out: out_value}]
            bit_width: 指标位宽，32或64用于计算超出位数时的速率
        Returns:
            List[Dict[str, Any]]: 计算后的速率数据
        """
        current_time = time.time()
        try:
            result = []
            cache_data = []  # 用于缓存的数据
            
            # 获取上一次的缓存数据
            cache_key = f"{self.metric_name}_data"
            previous_data = CACHE_MANAGER.get_from_cache(device_ip, 'interface_metrics', cache_key)
            previous_data_map = {item['id']: item for item in previous_data} if previous_data else {}
            if previous_data:
                # 为当前数据计算速率并更新缓存
                for interface_data in raw_data:
                    interface_id = interface_data['id']
                    in_value = interface_data.get('in', 0)
                    out_value = interface_data.get('out', 0)

                    # 准备接口数据（用于缓存），加入时间戳
                    cache_item = {
                        'id': interface_id,
                        'in': in_value,
                        'out': out_value,
                        'timestamp': current_time  # 添加时间戳
                    }
                    cache_data.append(cache_item)

                    # 计算入站速率
                    in_rate = 0.0
                    if interface_id in previous_data_map:
                        # 兼容处理time和timestamp字段
                        prev_time = previous_data_map[interface_id].get('timestamp', previous_data_map[interface_id].get('time', current_time))
                        prev_in_value = previous_data_map[interface_id].get('in', 0)
                        time_diff = int(current_time - prev_time)

                        if time_diff > 0:
                            # 处理计数器回绕
                            if in_value >= prev_in_value:
                                value_diff = int(in_value - prev_in_value)
                            else:
                                value_diff = int((self.max_value - prev_in_value) + in_value)

                            in_rate = (value_diff / time_diff)

                    # 计算出站速率
                    out_rate = 0.0
                    if interface_id in previous_data_map:
                        # 兼容处理time和timestamp字段
                        prev_time = previous_data_map[interface_id].get('timestamp', previous_data_map[interface_id].get('time', current_time))
                        prev_out_value = previous_data_map[interface_id].get('out', 0)
                        time_diff = int(current_time - prev_time)

                        if time_diff > 0:
                            # 处理计数器回绕
                            if out_value >= prev_out_value:
                                value_diff = int(out_value - prev_out_value)
                            else:
                                value_diff = int((self.max_value - prev_out_value) + out_value)

                            out_rate = (value_diff / time_diff)

                    # 添加到结果
                    result.append({
                        'id': interface_id,
                        'in_rate': round(in_rate, 1),
                        'out_rate': round(out_rate, 1)
                    })
            else:
                for interface_data in raw_data:
                    interface_id = interface_data['id']
                    in_value = interface_data.get('in', 0)
                    out_value = interface_data.get('out', 0)

                    # 准备接口数据（用于缓存），加入时间戳
                    cache_item = {
                        'id': interface_id,
                        'in': in_value,
                        'out': out_value,
                        'timestamp': current_time  # 添加时间戳
                    }
                    cache_data.append(cache_item)

            # 更新缓存，保存当前时间戳和原始值
            CACHE_MANAGER.set_to_cache(device_ip, 'interface_metrics', cache_key, cache_data, ttl=300)
            return {
                "ip": device_ip,
                "metric_name": self.metric_name,
                "status": "ok",
                "message": "采集成功",
                "timestamp": int(current_time),
                "data": result,
            }
        except Exception as e:
            logger.error(f"计算{self.metric_name}速率时出错: {str(e)}")
            return {
                "ip": device_ip,
                "metric_name": self.metric_name,
                "status": "error",
                "message": str(e),
                "timestamp": int(current_time),
                "data": [],
            }
    
    def collect(self, device_ip: str, community: str) -> Dict[str, Any]:
        """
        执行完整的采集流程
        
        Args:
            device_ip: 设备IP地址
            community: SNMP团体字符串
            
        Returns:
            List[Dict[str, Any]]: 采集的指标数据
        """
        raw_data = self.collect_raw_data(device_ip, community)
        return self.calculate_rates(device_ip, raw_data)

# 实现具体的指标采集策略
class BytesMetricStrategy(InterfaceMetricStrategy):
    """字节数指标采集策略"""
    def __init__(self, bit_width: int = 64):
        super().__init__(
            metric_name='bytes',
            in_oid=INTERFACE_OIDS['ifHCInOctets'],
            out_oid=INTERFACE_OIDS['ifHCOutOctets'],
            bit_width=bit_width
        )

class BitsPerSecondMetricStrategy(InterfaceMetricStrategy):
    """比特率指标采集策略"""
    def __init__(self, bit_width: int = 64):
        super().__init__(
            metric_name='bps',
            in_oid=INTERFACE_OIDS['ifHCInOctets'],
            out_oid=INTERFACE_OIDS['ifHCOutOctets'],
            bit_width=bit_width
        )
    
    def calculate_rates(self, device_ip: str, raw_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """计算比特率，将字节转换为比特"""
        # 获取基础计算结果
        result = super().calculate_rates(device_ip, raw_data)
        
        # 将字节率转换为比特率（乘以8）
        for item in result["data"]:
            if 'in_rate' in item:
                item['in_rate'] = item['in_rate'] * 8
            if 'out_rate' in item:
                item['out_rate'] = item['out_rate'] * 8
        
        return result

class PacketsPerSecondMetricStrategy(InterfaceMetricStrategy):
    """包速率指标采集策略"""
    def __init__(self, bit_width: int = 64):
        super().__init__(
            metric_name='pps',
            in_oid=INTERFACE_OIDS['ifHCInUcastPkts'],
            out_oid=INTERFACE_OIDS['ifHCOutUcastPkts'],
            bit_width=bit_width
        )

class MulticastPacketsMetricStrategy(InterfaceMetricStrategy):
    """组播包指标采集策略"""
    def __init__(self, bit_width: int = 64):
        super().__init__(
            metric_name='multicast_pps',
            in_oid=INTERFACE_OIDS['ifHCInMulticastPkts'],
            out_oid=INTERFACE_OIDS['ifHCOutMulticastPkts'],
            bit_width=bit_width
        )

class BroadcastPacketsMetricStrategy(InterfaceMetricStrategy):
    """广播包指标采集策略"""
    def __init__(self, bit_width: int = 64):
        super().__init__(
            metric_name='broadcast_pps',
            in_oid=INTERFACE_OIDS['ifHCInBroadcastPkts'],
            out_oid=INTERFACE_OIDS['ifHCOutBroadcastPkts'],
            bit_width=bit_width
        )

class ErrorPacketsMetricStrategy(InterfaceMetricStrategy):
    """错误包指标采集策略"""
    def __init__(self, bit_width: int = 32):
        super().__init__(
            metric_name='error_pps',
            in_oid=INTERFACE_OIDS['ifInErrors'],
            out_oid=INTERFACE_OIDS['ifOutErrors'],
            bit_width=bit_width
        )

class DiscardPacketsMetricStrategy(InterfaceMetricStrategy):
    """丢包指标采集策略"""
    def __init__(self, bit_width: int = 32):
        super().__init__(
            metric_name='discard_pps',
            in_oid=INTERFACE_OIDS['ifInDiscards'],
            out_oid=INTERFACE_OIDS['ifOutDiscards'],
            bit_width=bit_width
        )

# 创建指标策略工厂
class MetricStrategyFactory:
    """
    指标策略工厂类，用于创建各种指标采集策略
    """
    _strategies = {
        'interface_bytes': BytesMetricStrategy,
        'interface_bps': BitsPerSecondMetricStrategy,
        'interface_pps': PacketsPerSecondMetricStrategy,
        'interface_multicast_pps': MulticastPacketsMetricStrategy,
        'interface_broadcast_pps': BroadcastPacketsMetricStrategy,
        'interface_error_pps': ErrorPacketsMetricStrategy,
        'interface_discard_pps': DiscardPacketsMetricStrategy
    }
    
    @classmethod
    def get_strategy(cls, metric_type: str, bit_width: int = 64) -> Optional[InterfaceMetricStrategy]:
        """
        获取指定类型的指标采集策略
        
        Args:
            metric_type: 指标类型
            bit_width: 计数器位宽，可以是32或64，默认64
            
        Returns:
            InterfaceMetricStrategy: 指标采集策略实例，不存在则返回None
        """
        strategy_class = cls._strategies.get(metric_type)
        if strategy_class:
            return strategy_class(bit_width=bit_width)
        return None
    
    @classmethod
    def get_all_strategies(cls, bit_width: int = 64) -> Dict[str, InterfaceMetricStrategy]:
        """
        获取所有可用的指标采集策略
        
        Args:
            bit_width: 计数器位宽，可以是32或64，默认64
            
        Returns:
            Dict[str, InterfaceMetricStrategy]: 所有策略实例，键为指标类型
        """
        return {metric_type: strategy_class(bit_width=bit_width) for metric_type, strategy_class in cls._strategies.items()}

# 创建指标采集管理器
class InterfaceMetricCollector:
    """
    接口指标采集管理器，协调各种指标策略的执行
    """
    def __init__(self):
        self.factory = MetricStrategyFactory()
    
    def collect_metric(self, device_ip: str, community: str, metric_type: str, bit_width: int = 64) -> Dict[str, Any]:
        """
        采集单个类型的指标
        
        Args:
            device_ip: 设备IP地址
            community: SNMP团体字符串
            metric_type: 指标类型
            bit_width: 计数器位宽，可以是32或64，默认64
            
        Returns:
            List[Dict[str, Any]]: 采集的指标数据
        """
        strategy = self.factory.get_strategy(metric_type, bit_width=bit_width)
        if not strategy:
            logger.error(f"不支持的指标类型: {metric_type}")
            return {
                "ip": device_ip,
                "metric_name": metric_type,
                "timestamp": int(time.time()),
                "data": [],
            }
        
        return strategy.collect(device_ip, community)

# 创建全局的指标采集管理器实例
metric_collector = InterfaceMetricCollector()


def collect_interface_metric(ip: str, community: str = "public", metric_type: str = "") -> Dict[str, Any]:
    """
    采集单个设备的基础信息（向后兼容接口）

    Args:
        ip: 设备IP地址
        community: SNMP团体字符串
        metric_type: 指标类型

    Returns:
        Dict[str, Any]: 设备接口指标信息
    """
    return metric_collector.collect_metric(ip, community, metric_type=metric_type)

# ====================== 示例使用 ======================
'''
所有指标项目
interface_base
interface_status
'interface_bytes': BytesMetricStrategy,
'interface_bps': BitsPerSecondMetricStrategy,
'interface_pps': PacketsPerSecondMetricStrategy,
'interface_multicast_pps': MulticastPacketsMetricStrategy,
'interface_broadcast_pps': BroadcastPacketsMetricStrategy,
'interface_error_pps': ErrorPacketsMetricStrategy,
'interface_discard_pps': DiscardPacketsMetricStrategy

basic_info = collect_interface_basic_info(test_ip, test_community)
print(json.dumps(basic_info, indent=4))

port_status = collect_interface_status(test_ip, test_community)
print(port_status)

metrics = metric_collector.collect_metric(test_ip, test_community, metric_type='interface_bps', bit_width=64)
print(json.dumps(metrics, indent=4))
'''


if __name__ == "__main__":
    import json
    # 示例使用
    test_ip = "192.168.1.1"
    test_community = "public"
    
    # 采集接口基础信息
    basic_info = collect_interface_basic_info(test_ip, test_community)
    print(json.dumps(basic_info, indent=4))
    
    # 采集接口指标信息
    metrics = metric_collector.collect_metric(test_ip, test_community, metric_type='bps', bit_width=64)
    print(metrics)
    metrics1 =metric_collector.collect_metric(test_ip, test_community, metric_type='pps', bit_width=64)
    print(metrics1)



    time.sleep(10)
    metrics = metric_collector.collect_metric(test_ip, test_community, metric_type='bps', bit_width=64)
    print(json.dumps(metrics, indent=4))
    metrics1 = metric_collector.collect_metric(test_ip, test_community, metric_type='pps', bit_width=64)
    print(json.dumps(metrics1, indent=4))



    sd = collect_interface_status(test_ip, test_community)
    print(sd)

    metrics2 = metric_collector.collect_metric(test_ip, test_community, metric_type='ppss', bit_width=64)
    print(json.dumps(metrics2, indent=4))
