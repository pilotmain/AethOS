# AethOS production API image
FROM python:3.11-slim AS base

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    DEPLOYMENT_MODE=team \
    WORKER_MODE=embedded

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY aethos_core ./aethos_core
COPY aethos_sdk ./aethos_sdk
# §5 — ship operator skill playbooks and provider skill docs so the Skills panel
# and skill_recall resolve them in the deployed image (repo_root()/skills).
COPY skills ./skills
COPY provider_skills ./provider_skills

# Include the `browser` extra so the Playwright Python package is present in the
# deployed runtime (it lives in pyproject's optional `browser` group, not `dev`).
RUN pip install --no-cache-dir -e ".[dev,browser]"

# Browser automation runtime: install the Chromium binary AND its OS libraries so the
# Playwright launch probe passes in the image (System Health → browser executor). Without
# this the runtime reports `playwright_package_missing` / "Execution ready: No".
RUN python -m playwright install --with-deps chromium

RUN mkdir -p data/agent_artifacts data/credentials data/browser_artifacts data/research_artifacts

EXPOSE 8010

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD curl -f http://127.0.0.1:8010/api/v1/health || exit 1

CMD ["uvicorn", "aethos_core.api.main:app", "--host", "0.0.0.0", "--port", "8010"]
