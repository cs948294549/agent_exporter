docker run -d -p 8000:5000 \
  -e PYTHONUNBUFFERED=1 \
  -v /root/docker_apps/agent_exporter/logs:/app/logs \
  -v /root/docker_apps/agent_exporter/configs:/app/configs \
  --name exporter agent-exporter:v1