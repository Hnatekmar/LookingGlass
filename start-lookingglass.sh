#!/bin/bash
export PATH="/usr/local/bin:/root/.local/bin:$PATH"
export HOME="/root"
cd /opt/lookingglass
exec /usr/local/bin/uv run uvicorn app:app --host 0.0.0.0 --port 8090
