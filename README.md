# agent-exporter
分布式采集节点，对接http请求查询指标信息，使用Prometheus对接 Exporter获取监控指标


# 一、核心概念梳理
### Exporter：采集目标对象（服务器 / 应用 / 数据库）的监控指标，以 HTTP 接口（默认 /metrics）暴露给 Prometheus；
### Prometheus：通过配置文件指定 Exporter 地址，定期（scrape_interval）拉取指标并存储；
### 核心流程：Exporter 采集指标 → 暴露 HTTP 接口 → Prometheus 定时拉取 → 存储 / 查询 / 告警。

---

# 二、快速开始

## 2.1 环境要求
- Docker 20.10+
- Python 3.9+（非 Docker 部署）

## 2.2 Docker 部署（推荐）

### 构建镜像
```bash
# 默认构建 v1 版本
./docker/app_build.sh

# 指定版本标签
./docker/app_build.sh v2
```

### 启动容器
```bash
# 使用默认配置启动（端口 8000）
./docker/app_start.sh

# 指定版本和端口
./docker/app_start.sh v1 8080
```

**数据目录说明**：
- 默认使用当前目录作为数据目录
- 自动创建 `logs/` 和 `configs/` 目录
- 可通过环境变量自定义：
  ```bash
  export AGENT_EXPORTER_DATA_DIR=/path/to/data
  ./docker/app_start.sh
  ```

### 查看日志
```bash
# 查看容器日志
docker logs -f agent_exporter

# 查看应用日志
ls -lh logs/
```

### 容器管理
```bash
# 停止容器
docker stop agent_exporter

# 重启容器
docker restart agent_exporter

# 进入容器
docker exec -it agent_exporter bash

# 删除容器
docker rm -f agent_exporter
```

## 2.3 本地运行

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置文件
编辑 `configs/config.py` 配置数据库连接等参数

### 启动服务
```bash
python main.py
```

---

# 三、API 接口

## 3.1 Agent 管理接口

### 心跳检测
```bash
GET /agent/heartbeat
curl http://localhost:8000/agent/heartbeat
```

### 获取 Agent 信息
```bash
GET /agent/info
curl http://localhost:8000/agent/info
```
返回系统信息、资源使用情况、进程信息等。

### 探测目标设备
```bash
POST /agent/probe
curl -X POST http://localhost:8000/agent/probe \
  -H "Content-Type: application/json" \
  -d '{
    "target_ip": "192.168.1.1",
    "probe_type": "ping",
    "timeout": 3
  }'
```
**参数**：
- `target_ip`：目标 IP（必填）
- `probe_type`：探测类型，支持 `ping`、`tcp`（默认 `ping`）
- `timeout`：超时时间（秒，默认 3）
- `port`：TCP 端口（仅 tcp 类型需要）

## 3.2 SNMP 接口

### SNMP GET
```bash
POST /snmp/snmpget
curl -X POST http://localhost:8000/snmp/snmpget \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "community": "public",
    "oid": "1.3.6.1.2.1.1.1.0",
    "coding": "utf-8",
    "flag": false
  }'
```
**参数**：
- `ip`：设备 IP（必填）
- `oid`：OID（必填）
- `community`：SNMP 团体名（默认使用配置文件）
- `coding`：编码格式（默认 utf-8）
- `flag`：是否返回原始数据（默认 false）

### SNMP WALK
```bash
POST /snmp/snmpwalk
curl -X POST http://localhost:8000/snmp/snmpwalk \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "community": "public",
    "oid": "1.3.6.1.2.1.1",
    "coding": "utf-8",
    "flag": false,
    "bulk_size": 10
  }'
```
**参数**：
- `ip`：设备 IP（必填）
- `oid`：OID（必填）
- `community`：SNMP 团体名（默认使用配置文件）
- `coding`：编码格式（默认 utf-8）
- `flag`：是否返回原始数据（默认 false）
- `bulk_size`：批量大小（默认 10）

### 设备信息采集
```bash
POST /snmp/device-info
curl -X POST http://localhost:8000/snmp/device-info \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "community": "public"
  }'
```
**参数**：
- `ip`：设备 IP（必填）
- `community`：SNMP 团体名（默认使用配置文件）

## 3.3 SSH 接口

### 执行 SSH 命令
```bash
POST /ssh/run_cmd
curl -X POST http://localhost:8000/ssh/run_cmd \
  -H "Content-Type: application/json" \
  -d '{
    "ip": "192.168.1.1",
    "cmds": ["show version", "show ip interface brief"],
    "vendor": "cisco"
  }'
```
**参数**：
- `ip`：设备 IP（必填）
- `cmds`：命令列表（默认 []）
- `vendor`：设备厂商（可选，如：cisco、huawei、h3c 等）

---

# 四、Prometheus 配置

在 Prometheus 配置文件中添加：

```yaml
scrape_configs:
  - job_name: 'agent_exporter'
    static_configs:
      - targets: ['localhost:8000']
    scrape_interval: 30s
    scrape_timeout: 10s
```

---

# 五、目录结构

```
agent_exporter/
├── main.py              # 主程序入口
├── requirements.txt     # Python依赖
├── configs/            # 配置文件目录
├── logs/               # 日志文件目录（运行时生成）
└── docker/             # Docker相关脚本
    ├── Dockerfile      # 镜像构建文件
    ├── app_build.sh    # 镜像构建脚本
    └── app_start.sh    # 容器启动脚本
```

---

# 六、常见问题

## Q1: 端口被占用
**解决方法**：启动时指定其他端口
```bash
./docker/app_start.sh v1 8001
```

## Q2: 配置文件修改后不生效
**解决方法**：重启容器
```bash
docker restart agent_exporter
```

## Q3: 查看详细错误日志
```bash
docker logs agent_exporter 2>&1 | grep -i error
```

---

# 七、开发说明

## 时区设置
容器已配置为东八区（UTC+8），所有日志时间与本地时间一致。

## 健康检查
容器内置健康检查，每60秒检查一次主进程状态。

## 自动重启
容器配置了 `--restart unless-stopped`，异常退出会自动重启。