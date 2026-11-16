# HAYBAT AL SULTAN PRO - Production Monolith Container
FROM node:20-alpine
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3001
ENV ELECTRON_SKIP_BINARY_DOWNLOAD=1

# Install production dependencies cleanly
COPY package*.json .npmrc ./
RUN npm install --omit=dev --no-audit --no-fund --legacy-peer-deps

# Copy application files (including pre-built dist)
COPY . .

# Ensure local data directory exists for embedded libSQL SQLite
RUN mkdir -p data

EXPOSE 3001

CMD ["node", "server_libsql.cjs"]
