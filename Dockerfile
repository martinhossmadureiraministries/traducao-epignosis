FROM python:3.12-slim

WORKDIR /app
COPY bee ./bee
COPY worker/src ./worker/src
RUN pip install --no-cache-dir "mistralai-workflows[mistralai]>=3.10"
ENV PYTHONPATH=/app:/app/worker/src
CMD ["python", "-m", "worker.entrypoints.worker"]
