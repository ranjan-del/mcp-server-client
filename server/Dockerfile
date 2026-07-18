# MCP server image.
# NOTE: not built/run in the current dev environment (no Docker available),
# but kept correct for anyone who wants to containerise the server.
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies first for better layer caching.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the server package into /app/server so `python -m server.server` resolves.
COPY . ./server/

# The server speaks MCP over stdio, so there is no port to expose. A host/client
# launches this image and attaches to its stdin/stdout.
CMD ["python", "-m", "server.server"]
