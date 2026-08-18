FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Hostless build context is the repository root.
COPY apps/worker/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY apps/worker/app /app/app

# Make the application importable regardless of the runtime working directory.
ENV PYTHONPATH=/app

# Explicit app directory prevents Hostless working-directory overrides from breaking imports.
CMD ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "/app", "--host", "0.0.0.0", "--port", "8000"]
