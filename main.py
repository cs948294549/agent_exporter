# 导入核心组件
from core.app import create_app
from core.logger import setup_logger
from core.singleton_config import ConfigLoader
# 初始化日志系统
logger = setup_logger()

def main():
    """主函数"""
    # 创建Flask应用
    app = create_app()

    # 运行Flask应用
    try:
        logger.info(f"Flask服务器启动在端口 {ConfigLoader.get('server.port')}")
        app.run(host=ConfigLoader.get("server.host"), port=ConfigLoader.get("server.port"), threaded=True, debug=False)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")


if __name__ == "__main__":
    main()
    # nohup python3 -u main.py > lapi.log 2>&1 &
