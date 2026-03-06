docker run -d -p 8000:5000 \
  -v /root/apps/agent-exporter/logs:/app/logs \
  -v /root/apps/agent-exporter/configs:/app/configs \
  --name exporter agent-exporter:v1