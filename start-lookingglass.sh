#!/bin/bash
export PATH="/root/.local/bin:$PATH"
export HOME="/root"
cd /opt/lookingglass
exec /root/.local/bin/uv run uvicorn app:app --host 0.0.0.0 --port 8000
