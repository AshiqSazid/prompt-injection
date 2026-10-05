# Build for the official filesystem server (modelcontextprotocol/servers, src/filesystem).
# Used only to answer tools/list during schema capture (capture_native_schemas.py).
#
# Why not the repo's own src/filesystem/Dockerfile: at the pinned commit it copies
# the package out of its npm workspace and runs `npm install` alone, which fails
# ("Cannot read properties of null (reading 'edgesOut')"). This builds the same
# package from the repository root with the root package-lock.json instead, so
# every dependency version comes from the commit's own lockfile.
FROM node:22-alpine
WORKDIR /repo
COPY . .
RUN npm ci --ignore-scripts --no-audit --no-fund --workspace=@modelcontextprotocol/server-filesystem \
 && npm run build --workspace=@modelcontextprotocol/server-filesystem
ENTRYPOINT ["node", "/repo/src/filesystem/dist/index.js"]
