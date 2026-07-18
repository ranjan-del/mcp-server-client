# Full-demo image: contains both the server and client packages.
#
# Why one image? This project uses the MCP *stdio* transport, where the client
# launches the server as a subprocess and talks to it over stdin/stdout. There is
# no long-running network server to connect to, so the natural container runs the
# client demo, which spawns the server itself and prints the full round trip.
#
# NOTE: not built/run in the current dev environment (no Docker available), but
# kept correct for anyone who wants to containerise the demo.
FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching.
COPY server/requirements.txt ./server-requirements.txt
RUN pip install --no-cache-dir -r server-requirements.txt

# Copy the whole project (server, client, config, data, README).
COPY . ./

# Run the client demo; it launches `python -m server.server` under the hood.
CMD ["python", "-m", "client.client"]
