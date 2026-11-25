FROM python:3.12-slim-bookworm@sha256:44cf1793efa7c7a476bb0f2cff81443f4a072c90c1cb127e2924933daa3e8c64
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY workbench/ workbench/
COPY examples/ examples/
COPY rules/ rules/
USER 65532:65532
ENTRYPOINT ["python", "-m", "workbench"]
