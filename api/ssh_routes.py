from flask import Blueprint, request
from api.api_response import APIResponse

# 创建SNMP相关的蓝图，前缀设置为/snmp
ssh_bp = Blueprint('ssh', __name__, url_prefix='/ssh')

# 导入SNMP相关模块
from function_ssh.sshClient import run_ssh_command


@ssh_bp.route('/run_cmd', methods=['POST'])
def ssh_agent_run_cmd():
    """
    ssh 执行命令的借口
    """
    try:
        data = request.json
        ip = data.get('ip')
        cmds = data.get('cmds', [])
        vendor = data.get('vendor', "")
        if not ip:
            return APIResponse.param_error(message='ip参数不能为空')

        # 接口登陆交换机权限
        # identify = data.get('identify', None)
        # if not identify:
        #     return APIResponse.auth_error(message="ssh权限不足")

        result = run_ssh_command(host=ip, vendor=vendor, commands=cmds)
        if result and result["status"]=="success":
            return APIResponse.success(data={
                "ip": ip,
                "cmds": cmds,
                "vendor": vendor,
                "result": result,
            })
        else:
            return APIResponse.error(message="执行失败")
    except Exception as e:
        return APIResponse.server_error(message=str(e))


# 导出蓝图
__all__ = ['ssh_bp']