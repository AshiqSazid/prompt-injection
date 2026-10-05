# Throwaway local CalDAV server. caldav-mcp refuses to start unless it can reach
# one, but its tool schemas are static, so this server's contents cannot change
# what is captured. No real account, no internet at capture time.
FROM python:3.12-slim
RUN pip install --no-cache-dir radicale
COPY radicale.config /etc/radicale/config
EXPOSE 5232
ENTRYPOINT ["python", "-m", "radicale", "--config", "/etc/radicale/config"]
