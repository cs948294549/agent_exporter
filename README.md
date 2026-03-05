# agent-exporter
分布式采集节点，对接http请求查询指标信息，使用Prometheus对接 Exporter获取监控指标


# 一、核心概念梳理
### Exporter：采集目标对象（服务器 / 应用 / 数据库）的监控指标，以 HTTP 接口（默认 /metrics）暴露给 Prometheus；
### Prometheus：通过配置文件指定 Exporter 地址，定期（scrape_interval）拉取指标并存储；
### 核心流程：Exporter 采集指标 → 暴露 HTTP 接口 → Prometheus 定时拉取 → 存储 / 查询 / 告警。