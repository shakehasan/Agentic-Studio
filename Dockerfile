FROM python:3.11-slim
WORKDIR /app
COPY pyproject.toml README.md LICENSE ./
COPY src ./src
COPY examples ./examples
RUN python -m pip install --no-cache-dir -e .
EXPOSE 8080
CMD ["uvicorn", "marketing_swarm.api.app:create_app", "--factory", "--host", "0.0.0.0", "--port", "8080"]
