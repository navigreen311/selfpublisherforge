# =============================================================================
# Frontend Dockerfile — Multi-stage production build (Next.js standalone)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: Dependencies — install node_modules
# ---------------------------------------------------------------------------
FROM node:20-alpine AS deps

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --ignore-scripts

# ---------------------------------------------------------------------------
# Stage 2: Build — compile Next.js application
# ---------------------------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Set standalone output for optimized production build
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# ---------------------------------------------------------------------------
# Stage 3: Runtime — minimal image with standalone output
# ---------------------------------------------------------------------------
FROM node:20-alpine AS runtime

# `node server.js` is the whole runtime; npm is only here because the base
# image ships it, and every Node finding the image scanner reports (tar,
# pacote, sigstore, cross-spawn, glob, minimatch, brace-expansion, ip-address)
# lives in npm's own bundled node_modules, not in anything this app imports.
# The apk upgrade picks up the openssl patches Alpine has released since the
# base image was cut.
RUN apk --no-cache upgrade && \
    rm -rf /usr/local/lib/node_modules/npm \
           /usr/local/bin/npm /usr/local/bin/npx \
           /usr/local/bin/corepack /usr/local/bin/yarn /usr/local/bin/yarnpkg \
           /opt/yarn-*

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

# Copy only the standalone output and static assets
COPY --from=builder /app/public ./public
COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static

USER appuser

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    # 127.0.0.1, not localhost: busybox wget resolves localhost to ::1 first and
    # the Next server listens on 0.0.0.0, so the probe never connected and the
    # container reported unhealthy forever.
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3000/ || exit 1

CMD ["node", "server.js"]
