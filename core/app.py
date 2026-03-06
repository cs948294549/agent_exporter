from flask import Flask, request

# 导入任务相关蓝图
from api.snmp_routes import snmp_bp
from api.agent_routes import agent_bp
from api.ssh_routes import ssh_bp


def create_app():
    """
    创建并配置Flask应用
    Returns:
        Flask应用实例
    """
    
    # 创建Flask应用实例
    app = Flask(__name__)
    
    # 配置应用
    app.config.update(
        JSON_SORT_KEYS=False,  # 保持JSON响应中键的顺序
        JSONIFY_MIMETYPE='application/json',
        DEBUG=False  # 生产环境应关闭调试模式
    )

    # 注册任务相关蓝图（示例：展示如何扩展新的API端点）
    app.register_blueprint(snmp_bp)
    app.register_blueprint(agent_bp)
    app.register_blueprint(ssh_bp)


    @app.before_request
    def auth():
        print(request.path)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,session_id,sessionid')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS,HEAD')
        # 这里不能使用add方法，否则会出现 The 'Access-Control-Allow-Origin' header contains multiple values 的问题
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    # 向中心注册自身
    # 修改成中心主动探测proxy，实现监控一体化
    # task_manager.register_task(
    #     task_instance_id="heartbeat",
    #     task_class_id="heartbeat",
    #     config={"interval": 10},
    #     schedule_type="interval",
    #     schedule_config={"seconds": 10}
    # )
    
    return app


# 导出应用创建函数
__all__ = ['create_app']