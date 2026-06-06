# 导入核心组件
from core.app import create_app
from core.logger import setup_logger
from core.singleton_config import ConfigLoader
from core.scheduler import scheduler
from services.task_main import start_task_pull_service

# 初始化日志系统
logger = setup_logger()

def main():
    """主函数"""
    # 创建Flask应用
    app = create_app()

    # 启动调度器
    scheduler.start()
    logger.info("调度器已启动")

    # 启动任务拉取服务
    pull_interval = ConfigLoader.get("center.pull_interval", 60)
    start_task_pull_service(interval=pull_interval)

    # 运行Flask应用
    try:
        logger.info(f"Flask服务器启动在端口 {ConfigLoader.get('server.port')}")
        app.run(host=ConfigLoader.get("server.host"), port=ConfigLoader.get("server.port"), threaded=True, debug=False)
    except KeyboardInterrupt:
        logger.info("收到停止信号，正在关闭...")
    finally:
        scheduler.shutdown(wait=False)
        logger.info("调度器已关闭")


if __name__ == "__main__":
    main()
    # nohup python3 -u main.py > lapi.log 2>&1 &
