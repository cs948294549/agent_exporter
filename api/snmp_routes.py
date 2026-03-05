from flask import Blueprint, request, Config
from api.api_response import APIResponse

# 创建SNMP相关的蓝图，前缀设置为/snmp
snmp_bp = Blueprint('snmp', __name__, url_prefix='/snmp')

# 导入SNMP相关模块
from function_snmp.snmp_collector import snmp_get, snmp_walk
from collectors.device_info_collector import global_collector
import logging

from core.singleton_config import ConfigLoader

COMMON_COMMUNITY = ConfigLoader.get("snmp.community")

logger = logging.getLogger(__name__)


@snmp_bp.route('/snmpget', methods=['POST'])
def snmp_agent_get():
    """
    SNMP GET基础调用接口
    """
    try:
        data = request.json
        ip = data.get('ip')
        community = data.get('community', COMMON_COMMUNITY)
        oid = data.get('oid')
        coding = data.get('coding', 'utf-8')
        
        if not ip or not oid:
            return APIResponse.param_error(message='ip和oid参数不能为空')
        
        result = snmp_get(ip, community, oid)


        return APIResponse.success(data={
            'result': result,
            'ip': ip,
            'oid': oid
        })
    except Exception as e:
        logger.error("snmp_agent_get==={}".format(str(e)))
        return APIResponse.server_error(message=str(e))

@snmp_bp.route('/snmpwalk', methods=['POST'])
def snmp_agent_walk():
    """
    SNMP WALK基础调用接口
    """
    try:
        data = request.json
        ip = data.get('ip')
        community = data.get('community', COMMON_COMMUNITY)
        oid = data.get('oid')
        bulk_size = data.get('bulk_size', 10)
        coding = data.get('coding', 'utf-8')
        
        if not ip or not oid:
            return APIResponse.param_error(message='ip和oid参数不能为空')

        result = snmp_walk(ip, community, oid)

        return APIResponse.success(data={
            'result': result,
            'ip': ip,
            'oid': oid
        })

    except Exception as e:
        return APIResponse.server_error(message=str(e))

@snmp_bp.route('/device-info', methods=['POST'])
def snmp_collector_device_info():
    """
    设备信息采集接口
    """
    try:
        data = request.json
        ip = data.get('ip')
        community = data.get('community', COMMON_COMMUNITY)
        if not ip:
            return APIResponse.param_error(message='ip参数不能为空')
        
        # 使用全局设备信息采集器
        device_info = global_collector.collect_data(ip, community)

        return APIResponse.success(data=device_info)
    except Exception as e:
        return APIResponse.server_error(message=str(e))

# 导出蓝图
__all__ = ['snmp_bp']