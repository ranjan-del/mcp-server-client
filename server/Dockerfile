# MCP server image (skeleton).
# TODO: pin a specific base image digest before production use.
FROM python:3.12-slim

WORKDIR /app

# TODO: install dependencies (build step, not run during scaffolding).
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# TODO: copy the server package.
COPY . ./

# TODO: adjust entrypoint/transport as needed (see server/server.py).
CMD ["python", "-m", "server.server"]
