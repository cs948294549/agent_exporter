from flask import Blueprint, request
import platform
import socket
import time
import psutil
import os
from api.api_response import APIResponse
import logging

logger = logging.getLogger(__name__)


# 创建Agent相关的蓝图，前缀设置为/agent
agent_bp = Blueprint('agent', __name__, url_prefix='/agent')

@agent_bp.route('/heartbeat', methods=['GET'])
def heartbeat():
    """
    Agent心跳检测端点
    控制中心通过此端点检查Agent是否正常运行
    """
    logger.info('Heartbeat received')
    return APIResponse.success(data={
        'status': 'alive',
        'timestamp': time.time(),
        'message': 'Agent is running normally'
    })

@agent_bp.route('/info', methods=['GET'])
def get_agent_info():
    """
    获取Agent基础信息
    返回Agent运行环境、系统信息等
    """
    try:
        # 获取系统信息
        system_info = {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'hostname': socket.gethostname(),
            'python_version': platform.python_version()
        }
        
        # 获取资源使用情况
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        resource_info = {
            'cpu_percent': cpu_percent,
            'memory_total': memory_info.total,
            'memory_available': memory_info.available,
            'memory_used': memory_info.used,
            'memory_percent': memory_info.percent,
            'disk_total': disk_info.total,
            'disk_used': disk_info.used,
            'disk_free': disk_info.free,
            'disk_percent': disk_info.percent
        }
        
        # 获取Agent进程信息
        process_info = {
            'pid': os.getpid(),
            'start_time': psutil.Process(os.getpid()).create_time()
        }
        
        return APIResponse.success(data={
            'agent_info': {
                'version': '1.0.0',  # Agent版本号
                'system': system_info,
                'resources': resource_info,
                'process': process_info,
                'timestamp': time.time()
            }
        })
    except Exception as e:
        logger.error(f'Error getting agent info: {str(e)}')
        return APIResponse.server_error(message=str(e))

@agent_bp.route('/probe', methods=['POST'])
def agent_probe():
    """
    Agent探测端点
    控制中心可以通过此端点发起对目标设备的探测请求
    """
    try:
        data = request.json
        target_ip = data.get('target_ip')
        probe_type = data.get('probe_type', 'ping')
        timeout = data.get('timeout', 3)
        
        if not target_ip:
            logger.warning('Probe request missing target_ip')
            return APIResponse.param_error(message='target_ip参数不能为空')
        
        # 根据探测类型执行不同的探测逻辑
        if probe_type == 'ping':
            # 简单的ping测试
            result = ping_probe(target_ip, timeout)
        elif probe_type == 'tcp':
            # TCP端口探测
            port = data.get('port', 80)
            result = tcp_probe(target_ip, port, timeout)
        else:
            logger.warning(f'Unsupported probe type: {probe_type}')
        return APIResponse.param_error(message=f'不支持的探测类型: {probe_type}')
        
        logger.info(f'Probe completed successfully for {target_ip}')
        return APIResponse.success(data={
            'probe_result': result
        })
    except Exception as e:
        logger.error(f'Error during probe: {str(e)}')
        return APIResponse.server_error(message=str(e))

def ping_probe(ip, timeout):
    """
    执行ping探测
    """
    try:
        # 构建ping命令（根据操作系统不同）
        param = '-n 1' if platform.system().lower() == 'windows' else '-c 1'
        
        # 执行ping命令
        response = os.system(f'ping {param} -W {timeout} {ip} > /dev/null 2>&1')
        
        return {
            'ip': ip,
            'success': response == 0,
            'type': 'ping',
            'timeout': timeout,
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'ip': ip,
            'success': False,
            'type': 'ping',
            'timeout': timeout,
            'error': str(e),
            'timestamp': time.time()
        }

def tcp_probe(ip, port, timeout):
    """
    执行TCP端口探测
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        
        return {
            'ip': ip,
            'port': port,
            'success': result == 0,
            'type': 'tcp',
            'timeout': timeout,
            'timestamp': time.time()
        }
    except Exception as e:
        return {
            'ip': ip,
            'port': port,
            'success': False,
            'type': 'tcp',
            'timeout': timeout,
            'error': str(e),
            'timestamp': time.time()
        }

# 导出蓝图
__all__ = ['agent_bp']

