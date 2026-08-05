# 基础镜像：Python 3.9（兼容大多数项目）
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（如需编译依赖，如 pymysql，可加）
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     gcc \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# 复制依赖文件并安装
COPY requirements.txt .

# 清理缓存减少镜像体积
RUN pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ && pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/

# 复制项目代码（含默认配置）
COPY . .

# 仅声明 /app/logs 为卷目录（无实际绑定）
# 注意：configs 不声明为 VOLUME，避免覆盖镜像内的配置文件
# 如需修改配置，运行时通过 -v 挂载：-v /path/to/configs:/app/configs
VOLUME ["/app/logs", "/app/configs"]



# 暴露端口（与默认配置一致）
EXPOSE 5000

# 启动命令：执行启动脚本
# 启动命令（生产环境推荐用gunicorn，开发环境用python app.py）
# 开发环境：
CMD ["python", "-u", "main.py"]
# 生产环境：
#CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]