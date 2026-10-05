# Minimal build for a Node MCP server that ships no Dockerfile of its own.
# Used only to answer tools/list during schema capture (capture_native_schemas.py).
# --ignore-scripts: do not run the package's install hooks (e.g. git-hook setup);
# the build step is run explicitly instead.
FROM node:22-alpine
WORKDIR /app
COPY . .
RUN npm ci --ignore-scripts --no-audit --no-fund && npm run build
ENTRYPOINT ["node", "dist/index.js"]
